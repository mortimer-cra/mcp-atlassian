"""Base preprocessing module."""

import logging
import re
import warnings
from typing import Any, Protocol

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

logger = logging.getLogger("mcp-atlassian")


class ConfluenceClient(Protocol):
    """Protocol for Confluence client."""

    def get_user_details_by_accountid(self, account_id: str) -> dict[str, Any]:
        """Get user details by account ID."""
        ...

    def get_user_details_by_username(self, username: str) -> dict[str, Any]:
        """Get user details by username (for Server/DC compatibility)."""
        ...


class BasePreprocessor:
    """Base class for text preprocessing operations."""

    def __init__(self, base_url: str = "") -> None:
        """
        Initialize the base text preprocessor.

        Args:
            base_url: Base URL for API server
        """
        self.base_url = base_url.rstrip("/") if base_url else ""

    def process_html_content(
        self,
        html_content: str,
        space_key: str = "",
        confluence_client: ConfluenceClient | None = None,
        page_id: str | None = None,
        preserve_inline_attachments: bool = False,
    ) -> tuple[str, str]:
        """
        Process HTML content to replace user refs and page links.

        Args:
            html_content: The HTML content to process
            space_key: Optional space key for context
            confluence_client: Optional Confluence client for user lookups
            page_id: Optional page ID for attachment URL construction
            preserve_inline_attachments: Whether to inline attachments in content (default: False)

        Returns:
            Tuple of (processed_html, processed_markdown)
        """
        try:
            # Parse the HTML content
            soup = BeautifulSoup(html_content, "html.parser")

            # Process user mentions
            self._process_user_mentions_in_soup(soup, confluence_client)
            self._process_user_profile_macros_in_soup(soup, confluence_client)

            # Process inline attachments if enabled
            if preserve_inline_attachments and confluence_client and page_id:
                self._process_inline_attachments_in_soup(
                    soup, confluence_client, page_id, self.base_url
                )

            # Convert to string and markdown
            processed_html = str(soup)
            processed_markdown = md(processed_html)

            return processed_html, processed_markdown

        except Exception as e:
            logger.error(f"Error in process_html_content: {str(e)}")
            raise

    def _process_user_mentions_in_soup(
        self, soup: BeautifulSoup, confluence_client: ConfluenceClient | None = None
    ) -> None:
        """
        Process user mentions in BeautifulSoup object.

        Args:
            soup: BeautifulSoup object containing HTML
            confluence_client: Optional Confluence client for user lookups
        """
        # Find all ac:link elements that might contain user mentions
        user_mentions = soup.find_all("ac:link")

        for user_element in user_mentions:
            user_ref = user_element.find("ri:user")
            if user_ref and user_ref.get("ri:account-id"):
                # Case 1: Direct user reference without link-body
                account_id = user_ref.get("ri:account-id")
                if isinstance(account_id, str):
                    self._replace_user_mention(
                        user_element, account_id, confluence_client
                    )
                    continue

            # Case 2: User reference with link-body containing @
            link_body = user_element.find("ac:link-body")
            if link_body and "@" in link_body.get_text(strip=True):
                user_ref = user_element.find("ri:user")
                if user_ref and user_ref.get("ri:account-id"):
                    account_id = user_ref.get("ri:account-id")
                    if isinstance(account_id, str):
                        self._replace_user_mention(
                            user_element, account_id, confluence_client
                        )

    def _process_user_profile_macros_in_soup(
        self, soup: BeautifulSoup, confluence_client: ConfluenceClient | None = None
    ) -> None:
        """
        Process Confluence User Profile macros in BeautifulSoup object.
        Replaces <ac:structured-macro ac:name="profile">...</ac:structured-macro>
        with the user's display name, typically formatted as @DisplayName.

        Args:
            soup: BeautifulSoup object containing HTML
            confluence_client: Optional Confluence client for user lookups
        """
        profile_macros = soup.find_all(
            "ac:structured-macro", attrs={"ac:name": "profile"}
        )

        for macro_element in profile_macros:
            user_param = macro_element.find("ac:parameter", attrs={"ac:name": "user"})
            if not user_param:
                logger.debug(
                    "User profile macro found without a 'user' parameter. Replacing with placeholder."
                )
                macro_element.replace_with("[User Profile Macro (Malformed)]")
                continue

            user_ref = user_param.find("ri:user")
            if not user_ref:
                logger.debug(
                    "User profile macro's 'user' parameter found without 'ri:user' tag. Replacing with placeholder."
                )
                macro_element.replace_with("[User Profile Macro (Malformed)]")
                continue

            account_id = user_ref.get("ri:account-id")
            userkey = user_ref.get("ri:userkey")  # Fallback for Confluence Server/DC

            user_identifier_for_log = account_id or userkey
            display_name = None

            if confluence_client and user_identifier_for_log:
                try:
                    if account_id and isinstance(account_id, str):
                        user_details = confluence_client.get_user_details_by_accountid(
                            account_id
                        )
                        display_name = user_details.get("displayName")
                    elif userkey and isinstance(userkey, str):
                        # For Confluence Server/DC, userkey might be the username
                        user_details = confluence_client.get_user_details_by_username(
                            userkey
                        )
                        display_name = user_details.get("displayName")
                except Exception as e:
                    logger.warning(
                        f"Error fetching user details for profile macro (user: {user_identifier_for_log}): {e}"
                    )
            elif not confluence_client:
                logger.warning(
                    "Confluence client not available for User Profile Macro processing."
                )

            if display_name:
                replacement_text = f"@{display_name}"
                macro_element.replace_with(replacement_text)
            else:
                fallback_identifier = (
                    user_identifier_for_log
                    if user_identifier_for_log
                    else "unknown_user"
                )
                fallback_text = f"[User Profile: {fallback_identifier}]"
                macro_element.replace_with(fallback_text)
                logger.debug(f"Using fallback for user profile macro: {fallback_text}")

    def _replace_user_mention(
        self,
        user_element: Tag,
        account_id: str,
        confluence_client: ConfluenceClient | None = None,
    ) -> None:
        """
        Replace a user mention with the user's display name.

        Args:
            user_element: The HTML element containing the user mention
            account_id: The user's account ID
            confluence_client: Optional Confluence client for user lookups
        """
        try:
            # Only attempt to get user details if we have a valid confluence client
            if confluence_client is not None:
                user_details = confluence_client.get_user_details_by_accountid(
                    account_id
                )
                display_name = user_details.get("displayName", "")
                if display_name:
                    new_text = f"@{display_name}"
                    user_element.replace_with(new_text)
                    return
            # If we don't have a confluence client or couldn't get user details,
            # use fallback
            self._use_fallback_user_mention(user_element, account_id)
        except Exception as e:
            logger.warning(f"Error processing user mention: {str(e)}")
            self._use_fallback_user_mention(user_element, account_id)

    def _use_fallback_user_mention(self, user_element: Tag, account_id: str) -> None:
        """
        Replace user mention with a fallback when the API call fails.

        Args:
            user_element: The HTML element containing the user mention
            account_id: The user's account ID
        """
        # Fallback: just use the account ID
        new_text = f"@user_{account_id}"
        user_element.replace_with(new_text)

    def _process_inline_attachments_in_soup(
        self,
        soup: BeautifulSoup,
        confluence_client: ConfluenceClient,
        page_id: str,
        base_url: str,
    ) -> None:
        """
        Process inline attachments in BeautifulSoup object.
        Replaces attachment macros with inline content preserving layout.

        Args:
            soup: BeautifulSoup object containing HTML
            confluence_client: Confluence client for attachment lookups
            page_id: Page ID for attachment URL construction
            base_url: Base URL for attachment download URLs
        """
        # Process ac:image macros (images)
        self._process_ac_image_macros(soup, confluence_client, page_id, base_url)

        # Process ri:attachment references (links)
        self._process_ri_attachment_macros(soup, confluence_client, page_id, base_url)

        # Process ac:link with ri:attachment (attachment links)
        self._process_ac_link_attachment_macros(soup, confluence_client, page_id, base_url)

    def _process_ac_image_macros(
        self,
        soup: BeautifulSoup,
        confluence_client: ConfluenceClient,
        page_id: str,
        base_url: str,
    ) -> None:
        """Process ac:image macros for inline images."""
        image_macros = soup.find_all("ac:image")

        for image_macro in image_macros:
            try:
                # Extract attachment reference
                attachment_ref = image_macro.find("ri:attachment")
                if not attachment_ref:
                    continue

                filename = attachment_ref.get("ri:filename")
                if not filename:
                    continue

                # Get alt text from parameters
                alt_text = ""
                ac_params = image_macro.find_all("ac:parameter")
                for param in ac_params:
                    if param.get("ac:name") in ["alt", "title", "caption"]:
                        alt_text = param.get_text(strip=True)
                        break

                # Construct download URL
                download_url = self._construct_attachment_download_url(
                    base_url, page_id, filename
                )

                # Create inline image element
                if alt_text:
                    img_tag = soup.new_tag("img", src=download_url, alt=alt_text)
                else:
                    img_tag = soup.new_tag("img", src=download_url, alt=filename)

                # Replace the macro with the image
                image_macro.replace_with(img_tag)

            except Exception as e:
                logger.warning(f"Error processing ac:image macro: {str(e)}")
                # Replace with placeholder on error
                image_macro.replace_with("[Image attachment]")

    def _process_ri_attachment_macros(
        self,
        soup: BeautifulSoup,
        confluence_client: ConfluenceClient,
        page_id: str,
        base_url: str,
    ) -> None:
        """Process ri:attachment references for inline attachments."""
        attachment_refs = soup.find_all("ri:attachment")

        for attachment_ref in attachment_refs:
            try:
                filename = attachment_ref.get("ri:filename")
                if not filename:
                    continue

                # Skip if this is inside an ac:image (already processed)
                if attachment_ref.find_parent("ac:image"):
                    continue

                # Skip if this is inside an ac:link (will be processed separately)
                if attachment_ref.find_parent("ac:link"):
                    continue

                # Construct download URL
                download_url = self._construct_attachment_download_url(
                    base_url, page_id, filename
                )

                # Create link element
                link_tag = soup.new_tag("a", href=download_url)
                link_tag.string = filename

                # Replace the reference with the link
                attachment_ref.replace_with(link_tag)

            except Exception as e:
                logger.warning(f"Error processing ri:attachment: {str(e)}")
                # Replace with placeholder on error
                attachment_ref.replace_with("[Attachment]")

    def _process_ac_link_attachment_macros(
        self,
        soup: BeautifulSoup,
        confluence_client: ConfluenceClient,
        page_id: str,
        base_url: str,
    ) -> None:
        """Process ac:link elements containing ri:attachment."""
        link_macros = soup.find_all("ac:link")

        for link_macro in link_macros:
            try:
                attachment_ref = link_macro.find("ri:attachment")
                if not attachment_ref:
                    continue

                filename = attachment_ref.get("ri:filename")
                if not filename:
                    continue

                # Get link text from ac:link-body
                link_body = link_macro.find("ac:link-body")
                link_text = link_body.get_text(strip=True) if link_body else filename

                # Construct download URL
                download_url = self._construct_attachment_download_url(
                    base_url, page_id, filename
                )

                # Create link element
                link_tag = soup.new_tag("a", href=download_url)
                link_tag.string = link_text

                # Replace the macro with the link
                link_macro.replace_with(link_tag)

            except Exception as e:
                logger.warning(f"Error processing ac:link with ri:attachment: {str(e)}")
                # Replace with placeholder on error
                link_macro.replace_with("[Attachment link]")

    def _construct_attachment_download_url(
        self, base_url: str, page_id: str, filename: str
    ) -> str:
        """
        Construct attachment download URL.

        Args:
            base_url: Base URL of Confluence instance
            page_id: Page ID containing the attachment
            filename: Attachment filename

        Returns:
            Download URL for the attachment
        """
        # URL encode the filename
        from urllib.parse import quote
        encoded_filename = quote(filename)

        # Construct download URL
        # Format: {base_url}/download/attachments/{pageId}/{filename}
        download_url = f"{base_url}/download/attachments/{page_id}/{encoded_filename}"

        return download_url

    def _convert_html_to_markdown(self, text: str) -> str:
        """Convert HTML content to markdown if needed."""
        if re.search(r"<[^>]+>", text):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    soup = BeautifulSoup(f"<div>{text}</div>", "html.parser")
                    html = str(soup.div.decode_contents()) if soup.div else text
                    text = md(html)
            except Exception as e:
                logger.warning(f"Error converting HTML to markdown: {str(e)}")
        return text
