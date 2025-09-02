# Confluence 内联附件功能使用指南

## 功能概述

这个新功能解决了 Confluence 文档中附件作为列表返回而丢失原文图文布局的问题。现在附件可以以内联方式显示在内容中，保持原始文档的布局和阅读体验。

## 开启功能的方法

### 方法一：环境变量配置（推荐）

在你的环境中设置以下环境变量：

```bash
export CONFLUENCE_PRESERVE_INLINE_ATTACHMENTS=true
```

**支持的值**：
- `true`, `1`, `yes`, `on` - 开启功能
- `false`, `0`, `no`, `off` - 关闭功能（默认）

### 方法二：编程配置

如果你需要更细粒度的控制，可以在代码中直接配置：

```python
from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor

# 创建预处理器时开启功能
preprocessor = ConfluencePreprocessor(
    base_url="https://your-company.atlassian.net",
    preserve_inline_attachments=True
)
```

## 功能效果

### 转换示例

**图片宏转换**：
```html
<!-- 转换前 -->
<ac:image>
    <ri:attachment ri:filename="architecture.png"/>
</ac:image>

<!-- 转换后 -->
<img src="https://your-company.atlassian.net/download/attachments/12345/architecture.png" alt="architecture.png">
```

**附件链接转换**：
```html
<!-- 转换前 -->
<ac:link>
    <ri:attachment ri:filename="requirements.pdf"/>
    <ac:link-body>项目需求文档</ac:link-body>
</ac:link>

<!-- 转换后 -->
<a href="https://your-company.atlassian.net/download/attachments/12345/requirements.pdf">项目需求文档</a>
```

**纯附件引用转换**：
```html
<!-- 转换前 -->
<ri:attachment ri:filename="data.csv"/>

<!-- 转换后 -->
<a href="https://your-company.atlassian.net/download/attachments/12345/data.csv">data.csv</a>
```

## 支持的附件类型

1. **图片附件** (`<ac:image>`)
   - 转换为 `<img>` 标签
   - 支持 alt 文本和标题参数
   - 保持图片在文档流中的位置

2. **文档链接** (`<ac:link>` + `<ri:attachment>`)
   - 转换为 `<a>` 链接标签
   - 保持原始链接文本
   - 支持点击下载

3. **纯附件引用** (`<ri:attachment>`)
   - 转换为 `<a>` 链接标签
   - 使用文件名作为链接文本

## 配置选项

### 全局配置（环境变量）

```bash
# 开启内联附件功能
export CONFLUENCE_PRESERVE_INLINE_ATTACHMENTS=true

# 其他 Confluence 配置
export CONFLUENCE_URL=https://your-company.atlassian.net
export CONFLUENCE_USERNAME=your-email@company.com
export CONFLUENCE_API_TOKEN=your-api-token
```

### 实例级配置

```python
from mcp_atlassian.confluence import ConfluenceClient

# 方法1：通过环境变量
client = ConfluenceClient()  # 会自动读取环境变量

# 方法2：编程配置
from mcp_atlassian.confluence.config import ConfluenceConfig

config = ConfluenceConfig(
    url="https://your-company.atlassian.net",
    username="your-email@company.com",
    api_token="your-api-token",
    preserve_inline_attachments=True  # 开启功能
)

client = ConfluenceClient(config=config)
```

## 使用场景

### 场景1：获取页面内容

```python
from mcp_atlassian.confluence import ConfluenceClient

client = ConfluenceClient()

# 获取页面内容，附件将以内联方式显示
page = client.get_page_content("12345")
print(page.content)  # HTML 内容中包含内联的图片和链接
```

### 场景2：搜索结果

```python
# 搜索结果中的附件也会以内联方式显示
results = client.search("project documentation")
for page in results:
    print(page.content)  # 包含内联附件的 HTML
```

### 场景3：评论内容

```python
# 评论中的附件也会被处理
comments = client.get_page_comments("12345")
for comment in comments:
    print(comment.content)  # 包含内联附件的评论内容
```

## 向后兼容性

- **默认行为**：功能默认关闭，不影响现有代码
- **渐进 adoption**：可以逐步在不同环境中开启
- **回滚支持**：随时可以通过环境变量关闭

## 故障排除

### 功能没有生效

1. 检查环境变量是否正确设置：
   ```bash
   echo $CONFLUENCE_PRESERVE_INLINE_ATTACHMENTS
   ```

2. 确认配置已生效：
   ```python
   from mcp_atlassian.confluence import ConfluenceClient
   client = ConfluenceClient()
   print(client.preprocessor.preserve_inline_attachments)  # 应该输出 True
   ```

### 图片不显示

1. 检查图片 URL 是否可访问
2. 确认用户有查看附件的权限
3. 检查网络连接和防火墙设置

### 性能问题

- 内联附件功能对性能影响很小
- 只在 HTML 解析阶段增加少量处理时间
- 可以随时关闭以恢复原始性能

## 演示

运行演示脚本来查看功能效果：

```bash
python demo_inline_attachments.py
```

这个脚本会展示功能开启前后的差异，并提供详细的使用示例。

## 技术细节

- **URL 构造**：使用标准的 Confluence 下载路径格式
- **编码处理**：自动对文件名进行 URL 编码
- **错误处理**：解析失败时显示友好的占位符
- **类型安全**：完整的类型提示支持

## 版本兼容性

- 支持 Confluence Cloud 和 Server/Data Center
- 兼容所有现有的认证方式（Basic Auth、PAT、OAuth）
- 不影响其他功能模块

---

## 快速开始

1. **设置环境变量**：
   ```bash
   export CONFLUENCE_PRESERVE_INLINE_ATTACHMENTS=true
   ```

2. **运行你的应用**：
   ```python
   from mcp_atlassian.confluence import ConfluenceClient

   client = ConfluenceClient()
   page = client.get_page_content("your-page-id")

   # 现在 page.content 包含内联的图片和附件链接！
   ```

3. **享受更好的文档布局** 🎉
