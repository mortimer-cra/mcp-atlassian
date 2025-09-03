"""Confluence-specific text preprocessing module."""

import logging
import shutil
import tempfile
from pathlib import Path

from md2conf.converter import (
    ConfluenceConverterOptions,
    ConfluenceStorageFormatConverter,
    elements_from_string,
    elements_to_string,
    markdown_to_html,
)

from .base import BasePreprocessor, ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class ConfluencePreprocessor(BasePreprocessor):
    """Handles text preprocessing for Confluence content."""

    def __init__(
        self,
        base_url: str,
        preserve_inline_attachments: bool = False,
        proxy_host: str | None = None,
        proxy_port: int | None = None,
        proxy_base_path: str | None = None,
    ) -> None:
        """
        Initialize the Confluence text preprocessor.

        Args:
            base_url: Base URL for Confluence API
            preserve_inline_attachments: Whether to inline attachments in content (default: False)
            proxy_host: Proxy host for attachment URLs
            proxy_port: Proxy port for attachment URLs
            proxy_base_path: Proxy base path for attachment URLs
        """
        super().__init__(base_url=base_url)
        self.preserve_inline_attachments = preserve_inline_attachments
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_base_path = proxy_base_path

    def markdown_to_confluence_storage(
        self, markdown_content: str, *, enable_heading_anchors: bool = False
    ) -> str:
        """
        Convert Markdown content to Confluence storage format (XHTML)

        Args:
            markdown_content: Markdown text to convert
            enable_heading_anchors: Whether to enable automatic heading anchor generation (default: False)

        Returns:
            Confluence storage format (XHTML) string
        """
        try:
            # First convert markdown to HTML
            html_content = markdown_to_html(markdown_content)

            # Create a temporary directory for any potential attachments
            temp_dir = tempfile.mkdtemp()

            try:
                # Parse the HTML into an element tree
                root = elements_from_string(html_content)

                # Create converter options
                options = ConfluenceConverterOptions(
                    ignore_invalid_url=True,
                    heading_anchors=enable_heading_anchors,
                    render_mermaid=False,
                )

                # Create a converter
                converter = ConfluenceStorageFormatConverter(
                    options=options,
                    path=Path(temp_dir) / "temp.md",
                    root_dir=Path(temp_dir),
                    page_metadata={},
                )

                # Transform the HTML to Confluence storage format
                converter.visit(root)

                # Convert the element tree back to a string
                storage_format = elements_to_string(root)

                return str(storage_format)
            finally:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Error converting markdown to Confluence storage format: {e}")
            logger.exception(e)

            # Fall back to a simpler method if the conversion fails
            html_content = markdown_to_html(markdown_content)

            # Use a different approach that doesn't rely on the HTML macro
            # This creates a proper Confluence storage format document
            storage_format = f"""<p>{html_content}</p>"""

            return str(storage_format)

    def process_html_content(
        self,
        html_content: str,
        space_key: str = "",
        confluence_client: ConfluenceClient | None = None,
        page_id: str | None = None,
        preserve_inline_attachments: bool | None = None,
    ) -> tuple[str, str]:
        """
        Process HTML content to replace user refs and page links.

        Args:
            html_content: The HTML content to process
            space_key: Optional space key for context
            confluence_client: Optional Confluence client for user lookups
            page_id: Optional page ID for attachment URL construction
            preserve_inline_attachments: Whether to inline attachments in content.
                                      If None, uses the instance setting.

        Returns:
            Tuple of (processed_html, processed_markdown)
        """
        # Use instance setting if not explicitly provided
        if preserve_inline_attachments is None:
            preserve_inline_attachments = self.preserve_inline_attachments

        # Call parent method with the preserve_inline_attachments parameter
        processed_html, processed_markdown = super().process_html_content(
            html_content=html_content,
            space_key=space_key,
            confluence_client=confluence_client,
            page_id=page_id,
            preserve_inline_attachments=preserve_inline_attachments,
        )

        # Only process attachments, no external links

        return processed_html, processed_markdown

    # Confluence-specific methods can be added here
