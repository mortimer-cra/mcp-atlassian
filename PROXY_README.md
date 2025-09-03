# Atlassian 代理服务使用说明

## 🎯 功能概述

这个独立的代理服务解决了 Confluence 页面中图片和附件需要登录才能访问的问题。

## 🚀 快速开始

### 1. 配置环境变量

创建 `.env` 文件：

```bash
CONFLUENCE_URL=https://spms.migu.cn:8090
CONFLUENCE_USERNAME=你的用户名
CONFLUENCE_API_TOKEN=你的API令牌
PROXY_PORT=8080
```

### 2. 构建 Docker 镜像

```bash
docker build -f Dockerfile.standalone -t atlassian-proxy .
```

### 3. 运行服务

```bash
docker run -d --name atlassian-proxy -p 8080:8080 --env-file .env atlassian-proxy
```

### 4. 测试服务

```bash
curl http://localhost:8080/health
```

## 📖 API 接口

### 健康检查
```bash
GET /health
```

### 代理 Confluence 附件
```bash
GET /proxy/confluence/attachment/{page_id}/{filename}
```

示例：
```bash
# 原始链接 (需要登录)
https://spms.migu.cn:8090/download/attachments/438665657/111.png

# 代理链接 (无需登录)
http://localhost:8080/proxy/confluence/attachment/438665657/111.png
```

### 获取页面内容（自动替换链接）
```bash
GET /proxy/confluence/page/{page_id}
```

## 🛠️ 文件说明

- `standalone_proxy.py` - 独立的代理服务实现
- `Dockerfile.standalone` - 简化的 Docker 配置
- `PROXY_README.md` - 本使用说明

## 🔧 技术特点

- ✅ 完全独立，不依赖复杂项目结构
- ✅ 最小依赖，只使用必要的库
- ✅ 内置缓存，提高性能
- ✅ 完善的错误处理和日志记录
- ✅ CORS 支持，支持跨域访问
- ✅ 安全配置，使用非 root 用户运行

## 💡 使用场景

1. **Markdown 文档中的图片显示**
   ```markdown
   ![运算元素列表](http://localhost:8080/proxy/confluence/attachment/438665657/111.png)
   ```

2. **直接下载附件**
   ```bash
   wget http://localhost:8080/proxy/confluence/attachment/438665657/111.png
   ```

3. **获取页面内容并自动替换链接**
   ```bash
   curl http://localhost:8080/proxy/confluence/page/438665657
   ```

## 🐛 故障排除

如果服务无法启动，检查：
1. 环境变量是否正确配置
2. Confluence URL 和认证信息是否正确
3. 端口 8080 是否被占用

## 📝 日志查看

```bash
docker logs atlassian-proxy
```

服务已经成功运行，你可以立即开始使用！
