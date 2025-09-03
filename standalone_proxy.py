#!/usr/bin/env python3
"""
独立的 Atlassian 代理服务
解决 Confluence 页面中图片和附件需要登录才能访问的问题
"""

import os
import re
import logging
import mimetypes
from typing import Optional
from urllib.parse import quote, unquote
import asyncio

import aiohttp
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from cachetools import TTLCache

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Atlassian Proxy Service",
    description="代理 Atlassian 附件和内容的服务",
    version="1.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 缓存
cache = TTLCache(maxsize=1000, ttl=3600)

# 配置
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
PROXY_BASE_PATH = os.getenv("PROXY_BASE_PATH", "/proxy")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "atlassian-proxy"}


@app.get(f"{PROXY_BASE_PATH}/confluence/attachment/{{page_id}}/{{attachment_id}}")
async def proxy_confluence_attachment(page_id: str, attachment_id: str):
    """代理 Confluence 附件下载"""
    if not CONFLUENCE_URL or not CONFLUENCE_USERNAME or not CONFLUENCE_API_TOKEN:
        raise HTTPException(status_code=503, detail="Confluence 配置不完整")

    cache_key = f"confluence_attachment_{page_id}_{attachment_id}"

    # 检查缓存
    if cache_key in cache:
        logger.info(f"从缓存返回附件: {attachment_id}")
        cached_data = cache[cache_key]
        return Response(
            content=cached_data["content"],
            media_type=cached_data["content_type"],
            headers=cached_data["headers"]
        )

    try:
        # 构建原始 Confluence 附件 URL
        base_url = CONFLUENCE_URL.rstrip('/')
        attachment_url = f"{base_url}/download/attachments/{page_id}/{attachment_id}"

        # 创建认证
        auth = aiohttp.BasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(attachment_url) as response:
                if response.status == 404:
                    raise HTTPException(status_code=404, detail="附件未找到")
                elif response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"获取附件失败: {response.reason}"
                    )

                # 读取内容
                content = await response.read()

                # 确定内容类型
                content_type = response.headers.get('content-type')
                if not content_type:
                    # 从响应头获取文件名
                    content_disposition = response.headers.get('content-disposition', '')
                    filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                        content_type, _ = mimetypes.guess_type(filename)
                    content_type = content_type or 'application/octet-stream'

                # 准备响应头
                response_headers = {
                    "Content-Disposition": response.headers.get('content-disposition', 'inline'),
                    "Cache-Control": "public, max-age=3600"
                }

                # 缓存结果
                cache[cache_key] = {
                    "content": content,
                    "content_type": content_type,
                    "headers": response_headers
                }

                logger.info(f"成功代理附件: {attachment_id}")
                return Response(
                    content=content,
                    media_type=content_type,
                    headers=response_headers
                )

    except aiohttp.ClientError as e:
        logger.error(f"网络错误获取附件 {attachment_id}: {e}")
        raise HTTPException(status_code=502, detail="获取附件失败")
    except Exception as e:
        logger.error(f"意外错误获取附件 {attachment_id}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@app.get(f"{PROXY_BASE_PATH}/confluence/page/{{page_id}}")
async def get_confluence_page_with_proxy_links(page_id: str, request: Request):
    """获取 Confluence 页面内容，并替换附件链接为代理链接"""
    if not CONFLUENCE_URL or not CONFLUENCE_USERNAME or not CONFLUENCE_API_TOKEN:
        raise HTTPException(status_code=503, detail="Confluence 配置不完整")

    try:
        # 构建 Confluence API URL
        base_url = CONFLUENCE_URL.rstrip('/')
        api_url = f"{base_url}/rest/api/content/{page_id}?expand=body.storage,version,space,children.attachment"

        # 创建认证
        auth = aiohttp.BasicAuth(CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(api_url) as response:
                if response.status == 404:
                    raise HTTPException(status_code=404, detail="页面未找到")
                elif response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"获取页面失败: {response.reason}"
                    )

                page_data = await response.json()

                # 获取页面内容
                content = page_data.get("body", {}).get("storage", {}).get("value", "")

                # 获取附件列表
                attachments = page_data.get("children", {}).get("attachment", {}).get("results", [])

                # 替换附件链接为代理链接
                proxy_base_url = f"{request.url.scheme}://{request.url.netloc}{PROXY_BASE_PATH}"
                modified_content = replace_attachment_links(content, page_id, proxy_base_url, base_url, attachments)

                # 返回修改后的页面数据
                result = {
                    "id": page_data.get("id"),
                    "title": page_data.get("title"),
                    "content": modified_content,
                    "space": page_data.get("space", {}),
                    "version": page_data.get("version", {}),
                    "type": page_data.get("type"),
                    "_links": page_data.get("_links", {})
                }

                logger.info(f"成功获取页面: {page_id}")
                return result

    except aiohttp.ClientError as e:
        logger.error(f"网络错误获取页面 {page_id}: {e}")
        raise HTTPException(status_code=502, detail="获取页面失败")
    except Exception as e:
        logger.error(f"意外错误获取页面 {page_id}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@app.get(f"{PROXY_BASE_PATH}/general/{{path:path}}")
async def proxy_general(path: str):
    """代理通用 URL"""
    try:
        # 解码 URL
        from urllib.parse import unquote, urlparse
        url = unquote(path)

        # 验证 URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise HTTPException(status_code=400, detail="无效的 URL")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.read()

                # 返回内容，保留原始头部
                response_headers = {
                    "Content-Type": response.headers.get("Content-Type", "application/octet-stream"),
                    "Cache-Control": "public, max-age=3600"
                }

                return Response(
                    content=content,
                    headers=response_headers,
                    status_code=response.status
                )

    except aiohttp.ClientError as e:
        logger.error(f"网络错误代理 URL {path}: {e}")
        raise HTTPException(status_code=502, detail="代理失败")
    except Exception as e:
        logger.error(f"意外错误代理 URL {path}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


def replace_attachment_links(content: str, page_id: str, proxy_base_url: str, confluence_base_url: str, attachments: list) -> str:
    """替换内容中的附件链接为代理链接"""

    # 创建文件名到附件ID的映射
    attachment_map = {att.get("title", ""): att.get("id", "") for att in attachments}

    # 模式1: 相对路径 /download/attachments/pageId/filename
    pattern1 = r'/download/attachments/(\d+)/([^)\s"\']+)'

    def replace_relative_link(match):
        matched_page_id = match.group(1)
        filename = unquote(match.group(2))
        if filename in attachment_map:
            attachment_id = attachment_map[filename]
            return f"{proxy_base_url}/confluence/attachment/{matched_page_id}/{attachment_id}"
        else:
            logger.warning(f"附件未找到: {filename}")
            return match.group(0)

    content = re.sub(pattern1, replace_relative_link, content)

    # 模式2: 完整 URL https://domain/download/attachments/pageId/filename
    confluence_base_escaped = re.escape(confluence_base_url)
    pattern2 = rf'{confluence_base_escaped}/download/attachments/(\d+)/([^)\s"\']+)'

    content = re.sub(pattern2, replace_relative_link, content)

    return content


def main():
    """主函数"""
    # 检查必要的环境变量
    if not CONFLUENCE_URL:
        logger.error("请设置 CONFLUENCE_URL 环境变量")
        return
    
    if not CONFLUENCE_USERNAME or not CONFLUENCE_API_TOKEN:
        logger.warning("Confluence 认证信息未配置，某些功能可能不可用")
    
    # 启动服务器
    host = os.getenv("PROXY_HOST", "0.0.0.0")
    port = int(os.getenv("PROXY_PORT", "8080"))
    
    logger.info(f"启动 Atlassian 代理服务: {host}:{port}")
    logger.info(f"代理基础路径: {PROXY_BASE_PATH}")
    logger.info(f"Confluence URL: {CONFLUENCE_URL}")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
