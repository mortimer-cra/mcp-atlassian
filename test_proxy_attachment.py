#!/usr/bin/env python3
"""Test script to verify proxy attachment URL replacement."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor

def test_proxy_attachment_url():
    """Test that attachment URLs are replaced with proxy URLs."""

    # Test HTML content with attachment
    html_content = """
    <p>This is a test page with an attachment.</p>
    <ac:image>
        <ri:attachment ri:filename="test.png"/>
    </ac:image>
    <p>Another attachment link:</p>
    <ac:link>
        <ri:attachment ri:filename="document.pdf"/>
        <ac:link-body>Download PDF</ac:link-body>
    </ac:link>
    """

    # Create preprocessor with proxy configuration
    preprocessor = ConfluencePreprocessor(
        base_url="https://spms.migu.cn:8090",
        preserve_inline_attachments=True,
        proxy_host="0.0.0.0",
        proxy_port=8002,
        proxy_base_path="/proxy"
    )

    # Mock confluence client
    class MockConfluenceClient:
        def get_user_details_by_accountid(self, account_id):
            return {"displayName": "Test User"}

    # Process the content
    processed_html, processed_markdown = preprocessor.process_html_content(
        html_content,
        space_key="TEST",
        confluence_client=MockConfluenceClient(),
        page_id="12345",
        preserve_inline_attachments=True
    )

    print("Original HTML:")
    print(html_content)
    print("\nProcessed HTML:")
    print(processed_html)
    print("\nProcessed Markdown:")
    print(processed_markdown)

    # Check if proxy URLs are used
    expected_proxy_url_png = "http://0.0.0.0:8002/proxy/confluence/attachment/12345/test.png"
    expected_proxy_url_pdf = "http://0.0.0.0:8002/proxy/confluence/attachment/12345/document.pdf"

    if expected_proxy_url_png in processed_html and expected_proxy_url_pdf in processed_html:
        print("\n✅ SUCCESS: Proxy URLs are correctly used!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected PNG URL: {expected_proxy_url_png}")
        print(f"Expected PDF URL: {expected_proxy_url_pdf}")
        print(f"Processed HTML contains PNG URL: {expected_proxy_url_png in processed_html}")
        print(f"Processed HTML contains PDF URL: {expected_proxy_url_pdf in processed_html}")
        return False

def test_external_links():
    """Test that external links are NOT replaced (only attachments should be)."""

    # Test HTML content with external links
    html_content = """
    <p>This is a test page with external links.</p>
    <p>Link to external site: <a href="https://example.com/page">Example</a></p>
    <p>Link to Confluence (should not be proxied): <a href="https://spms.migu.cn:8090/pages/viewpage.action?pageId=12345">Internal</a></p>
    """

    # Create preprocessor with proxy configuration
    preprocessor = ConfluencePreprocessor(
        base_url="https://spms.migu.cn:8090",
        preserve_inline_attachments=True,
        proxy_host="0.0.0.0",
        proxy_port=8002,
        proxy_base_path="/proxy"
    )

    # Mock confluence client
    class MockConfluenceClient:
        def get_user_details_by_accountid(self, account_id):
            return {"displayName": "Test User"}

    # Process the content
    processed_html, processed_markdown = preprocessor.process_html_content(
        html_content,
        space_key="TEST",
        confluence_client=MockConfluenceClient(),
        page_id="12345",
        preserve_inline_attachments=True
    )

    print("\nExternal links test - Processed HTML:")
    print(processed_html)

    # Check that external links are NOT changed
    original_external_url = "https://example.com/page"
    internal_url = "https://spms.migu.cn:8090/pages/viewpage.action?pageId=12345"

    if original_external_url in processed_html and internal_url in processed_html:
        print("\n✅ SUCCESS: External links are NOT proxied, only attachments should be!")
        return True
    else:
        print(f"\n❌ FAILURE: External links should remain unchanged")
        print(f"Original external URL: {original_external_url}")
        print(f"Internal URL: {internal_url}")
        return False

def test_without_proxy():
    """Test that proxy URLs are still used even when no proxy is configured (using defaults)."""

    # Test HTML content with attachment
    html_content = """
    <p>This is a test page with an attachment.</p>
    <ac:image>
        <ri:attachment ri:filename="test.png"/>
    </ac:image>
    """

    # Create preprocessor without proxy configuration
    preprocessor = ConfluencePreprocessor(
        base_url="https://spms.migu.cn:8090",
        preserve_inline_attachments=True
    )

    # Mock confluence client
    class MockConfluenceClient:
        def get_user_details_by_accountid(self, account_id):
            return {"displayName": "Test User"}

    # Process the content
    processed_html, processed_markdown = preprocessor.process_html_content(
        html_content,
        space_key="TEST",
        confluence_client=MockConfluenceClient(),
        page_id="12345",
        preserve_inline_attachments=True
    )

    print("\nWithout explicit proxy config - Processed HTML:")
    print(processed_html)

    # Check if default proxy URLs are used
    expected_proxy_url = "http://localhost:8002/proxy/confluence/attachment/12345/test.png"

    if expected_proxy_url in processed_html:
        print("\n✅ SUCCESS: Default proxy URLs are correctly used!")
        return True
    else:
        print(f"\n❌ FAILURE: Expected proxy URL: {expected_proxy_url}")
        print(f"Processed HTML contains proxy URL: {expected_proxy_url in processed_html}")
        return False

def test_get_page_simulation():
    """Test simulating the get_page MCP tool functionality."""

    # Simulate HTML content from a Confluence page with attachments
    html_content = """
    <p>This is a test page with attachments.</p>
    <p>Here is an image:</p>
    <ac:image>
        <ri:attachment ri:filename="test.png"/>
    </ac:image>
    <p>And a document link:</p>
    <ac:link>
        <ri:attachment ri:filename="document.pdf"/>
        <ac:link-body>Download PDF</ac:link-body>
    </ac:link>
    <p>Some external link (should not be changed):</p>
    <a href="https://example.com">External Link</a>
    """

    # Create preprocessor with proxy configuration
    preprocessor = ConfluencePreprocessor(
        base_url="https://spms.migu.cn:8090",
        preserve_inline_attachments=True,
        proxy_host="localhost",
        proxy_port=8002,
        proxy_base_path="/proxy"
    )

    # Mock confluence client
    class MockConfluenceClient:
        def get_user_details_by_accountid(self, account_id):
            return {"displayName": "Test User"}

    # Process the content (simulating get_page)
    processed_html, processed_markdown = preprocessor.process_html_content(
        html_content,
        space_key="TEST",
        confluence_client=MockConfluenceClient(),
        page_id="463693554",  # The page ID the user mentioned
        preserve_inline_attachments=True
    )

    print("=== SIMULATING get_page TOOL RESPONSE ===")
    print("Page ID: 463693554")
    print("Processed HTML:")
    print(processed_html)
    print("\nProcessed Markdown:")
    print(processed_markdown)

    # Check if attachment URLs are replaced
    expected_attachment_url_png = "http://localhost:8002/proxy/confluence/attachment/463693554/test.png"
    expected_attachment_url_pdf = "http://localhost:8002/proxy/confluence/attachment/463693554/document.pdf"
    external_link_should_remain = "https://example.com"

    attachment_urls_replaced = (
        expected_attachment_url_png in processed_html and
        expected_attachment_url_pdf in processed_html
    )
    external_link_unchanged = external_link_should_remain in processed_html

    if attachment_urls_replaced and external_link_unchanged:
        print("\n✅ SUCCESS: get_page simulation shows correct behavior!")
        print("   - Attachment URLs are replaced with proxy URLs")
        print("   - External links remain unchanged")
        return True
    else:
        print("\n❌ FAILURE: get_page simulation failed")
        print(f"   - Attachment URLs replaced: {attachment_urls_replaced}")
        print(f"   - External links unchanged: {external_link_unchanged}")
        return False

if __name__ == "__main__":
    print("Testing proxy attachment URL replacement...")

    success1 = test_proxy_attachment_url()
    success2 = test_external_links()
    success3 = test_without_proxy()
    success4 = test_get_page_simulation()

    if success1 and success2 and success3 and success4:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
