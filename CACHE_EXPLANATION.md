# 代理服务代码思路和缓存机制详解

## 🧠 代码设计思路

### 1. 核心问题解决
**原始问题**: Confluence 附件链接需要登录才能访问
**解决方案**: 创建一个代理服务，使用配置的认证信息代为访问，然后返回内容给用户

### 2. 架构设计
- **FastAPI 框架**: 提供高性能的 REST API 服务
- **aiohttp 客户端**: 异步 HTTP 客户端，高效处理并发请求
- **缓存机制**: 减少重复请求，提高性能
- **错误处理**: 完善的异常处理和日志记录

## 💾 缓存机制详解

### 1. 缓存位置
```python
from cachetools import TTLCache

# 内存缓存，最大1000个项目，每个项目存活3600秒（1小时）
cache = TTLCache(maxsize=1000, ttl=3600)
```

**缓存位置**: **内存中** (in-memory cache)
- 存储在应用程序进程的内存中
- 重启服务后缓存会清空
- 每个容器实例有自己的独立缓存

### 2. 缓存键设计
```python
cache_key = f"confluence_attachment_{page_id}_{filename}"
```

缓存键包含:
- `confluence_attachment_` - 前缀标识类型
- `{page_id}` - 页面ID
- `{filename}` - 文件名

这样可以确保不同页面、不同文件的缓存不会冲突。

### 3. 缓存内容
每个缓存项存储:
```python
{
    "content": bytes,           # 附件的二进制内容
    "content_type": str,        # 内容类型 (如 image/png)
    "headers": dict            # 响应头信息
}
```

### 4. 缓存流程
1. 收到请求时，先检查缓存中是否有该附件
2. 如果缓存命中，直接返回缓存内容
3. 如果缓存未命中，从 Confluence 下载附件
4. 下载成功后，存入缓存，然后返回内容

## 🔐 认证机制

### 1. 认证方式
```python
auth = aiohttp.BasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
```

使用 **Basic Authentication** 认证，每次请求 Confluence 时都会在请求头中包含认证信息。

### 2. 认证复用
```python
async with aiohttp.ClientSession(auth=auth) as session:
    async with session.get(attachment_url) as response:
        # 处理响应
```

**关键点**: 
- **不是每次用户请求都需要登录**
- 代理服务使用配置的固定认证信息
- 用户访问代理服务时**不需要提供任何认证**
- 代理服务在后台使用配置的认证信息访问 Confluence

### 3. 会话管理
- 使用 `aiohttp.ClientSession` 管理 HTTP 会话
- 会话会自动处理认证、连接池、cookie 等
- 每个请求复用相同的会话，提高性能

## ⚡ 性能优化

### 1. 缓存优势
- **减少网络请求**: 相同附件一小时內只下载一次
- **降低延迟**: 内存访问比网络请求快得多
- **减轻负载**: 减少对 Confluence 服务器的压力

### 2. 异步处理
- 使用 `async/await` 异步编程
- 支持高并发请求
- 不会阻塞其他请求的处理

### 3. 连接复用
- HTTP 连接池管理
- 复用 TCP 连接，减少握手开销

## 🔧 配置说明

### 环境变量
```bash
CONFLUENCE_URL=https://spms.migu.cn:8090      # Confluence 地址
CONFLUENCE_USERNAME=your_username             # 用户名
CONFLUENCE_API_TOKEN=your_api_token           # API令牌
PROXY_PORT=8080                               # 代理服务端口
PROXY_BASE_PATH=/proxy                        # API基础路径
```

### 缓存配置
- **最大缓存数**: 1000 个项目
- **缓存时间**: 3600 秒 (1小时)
- 可根据需要调整这些参数

## 🛡️ 安全考虑

### 1. 认证安全
- API token 通过环境变量配置，不在代码中硬编码
- 使用 Basic Auth，token 不会暴露给终端用户

### 2. 访问控制
- 代理服务本身没有访问控制
- 实际的访问控制由 Confluence 的认证机制处理

### 3. 数据安全
- 附件内容在传输过程中保持加密 (HTTPS)
- 缓存内容只在内存中，重启后消失

## 📊 性能指标

假设场景:
- 附件平均大小: 1MB
- 并发用户: 100人
- 缓存命中率: 80%

**无缓存时**:
- 需要100个并发请求到 Confluence
- 总带宽: 100MB

**有缓存时**:
- 只有20个请求需要访问 Confluence
- 80个请求直接从内存返回
- 总带宽: 20MB
- 响应时间大幅减少

这个设计确保了高性能和高可用性，同时保持了代码的简洁性和可维护性。
