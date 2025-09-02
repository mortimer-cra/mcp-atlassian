#!/usr/bin/env python3
"""
Demo script showing the inline attachment functionality for Confluence content.

This script demonstrates how the new preserve_inline_attachments feature works
by processing Confluence HTML content with various attachment macros.
"""

from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor


def demo_inline_attachments():
    """Demonstrate inline attachment processing functionality."""

    # Sample Confluence HTML content with various attachment types
    html_content = """
<h1>Project Documentation</h1>

<p>This document contains various types of attachments:</p>

<h2>Images</h2>
<p>Here is a diagram showing the architecture:</p>
<ac:image>
    <ri:attachment ri:filename="architecture-diagram.png"/>
</ac:image>

<p>And here is a screenshot with alt text:</p>
<ac:image>
    <ri:attachment ri:filename="screenshot.png"/>
    <ac:parameter ac:name="alt">User Interface Screenshot</ac:parameter>
    <ac:parameter ac:name="title">Main Dashboard</ac:parameter>
</ac:image>

<h2>Document Links</h2>
<p>Please refer to the following documents:</p>
<ul>
    <li><ac:link>
        <ri:attachment ri:filename="requirements.pdf"/>
        <ac:link-body>Project Requirements Document</ac:link-body>
    </ac:link></li>
    <li><ac:link>
        <ri:attachment ri:filename="design-spec.docx"/>
        <ac:link-body>Design Specifications</ac:link-body>
    </ac:link></li>
</ul>

<h2>Plain Attachments</h2>
<p>Additional files:</p>
<ri:attachment ri:filename="data-export.csv"/>
<ri:attachment ri:filename="source-code.zip"/>

<p>That's all for now!</p>
"""

    print("=== INLINE ATTACHMENTS DEMO ===\n")

    # Test with preserve_inline_attachments=False (default behavior)
    print("1. DEFAULT BEHAVIOR (preserve_inline_attachments=False)")
    print("-" * 60)

    preprocessor_default = ConfluencePreprocessor(
        base_url="https://company.atlassian.net",
        preserve_inline_attachments=False
    )

    processed_html_default, processed_markdown_default = preprocessor_default.process_html_content(
        html_content,
        confluence_client=None,  # No client needed for this demo
        page_id="12345"
    )

    print("Original macros are preserved:")
    print("- ac:image macros remain unchanged")
    print("- ri:attachment references remain unchanged")
    print("- ac:link macros remain unchanged")
    print()

    # Test with preserve_inline_attachments=True (new behavior)
    print("2. NEW BEHAVIOR (preserve_inline_attachments=True)")
    print("-" * 60)

    preprocessor_inline = ConfluencePreprocessor(
        base_url="https://company.atlassian.net",
        preserve_inline_attachments=True
    )

    processed_html_inline, processed_markdown_inline = preprocessor_inline.process_html_content(
        html_content,
        confluence_client=None,  # Mock client for demo
        page_id="12345"
    )

    print("HTML Output:")
    print("- ac:image macros converted to <img> tags")
    print("- ri:attachment references converted to <a> tags")
    print("- ac:link macros converted to <a> tags")
    print()

    # Show specific examples
    print("EXAMPLES:")
    print("-" * 60)

    # Image conversion
    if '<img src="https://company.atlassian.net/download/attachments/12345/architecture-diagram.png"' in processed_html_inline:
        print("✅ Image macro converted:")
        print('   <ac:image><ri:attachment ri:filename="architecture-diagram.png"/></ac:image>')
        print('   → <img src="https://company.atlassian.net/download/attachments/12345/architecture-diagram.png" alt="architecture-diagram.png">')
        print()

    # Link conversion
    if '<a href="https://company.atlassian.net/download/attachments/12345/requirements.pdf">Project Requirements Document</a>' in processed_html_inline:
        print("✅ Link macro converted:")
        print('   <ac:link><ri:attachment ri:filename="requirements.pdf"/><ac:link-body>Project Requirements Document</ac:link-body></ac:link>')
        print('   → <a href="https://company.atlassian.net/download/attachments/12345/requirements.pdf">Project Requirements Document</a>')
        print()

    # Plain attachment conversion
    if '<a href="https://company.atlassian.net/download/attachments/12345/data-export.csv">data-export.csv</a>' in processed_html_inline:
        print("✅ Plain attachment converted:")
        print('   <ri:attachment ri:filename="data-export.csv"/>')
        print('   → <a href="https://company.atlassian.net/download/attachments/12345/data-export.csv">data-export.csv</a>')
        print()

    print("3. CONFIGURATION")
    print("-" * 60)
    print("To enable this feature, set the environment variable:")
    print("   CONFLUENCE_PRESERVE_INLINE_ATTACHMENTS=true")
    print()
    print("Or configure it programmatically:")
    print("   preprocessor = ConfluencePreprocessor(")
    print("       base_url='https://company.atlassian.net',")
    print("       preserve_inline_attachments=True")
    print("   )")
    print()

    print("4. BENEFITS")
    print("-" * 60)
    print("✅ Preserves original document layout and flow")
    print("✅ Images appear inline instead of as separate attachments")
    print("✅ Documents remain clickable links in context")
    print("✅ Maintains backward compatibility")
    print("✅ Configurable per instance or globally")
    print()

    print("=== DEMO COMPLETE ===")


if __name__ == "__main__":
    demo_inline_attachments()
