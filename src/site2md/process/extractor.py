"""Content extraction from HTML using trafilatura."""

from typing import Any, Dict, Optional

import trafilatura
from bs4 import BeautifulSoup

from ..utils.exceptions import ProcessingError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ContentExtractor:
    """Extracts main content from HTML using trafilatura."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def extract(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract main content and metadata from HTML."""
        try:
            # Use trafilatura for main content extraction
            extracted_content = trafilatura.extract(
                html_content,
                favor_precision=True,
                include_comments=False,
                include_tables=True,
                include_formatting=True,
                include_links=True,
                url=url,
            )

            if not extracted_content:
                logger.warning(f"No content extracted from {url}")
                extracted_content = ""

            # Extract metadata
            metadata = trafilatura.extract_metadata(html_content)

            # Parse HTML for additional elements we need
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract title
            title = self._extract_title(soup, metadata)

            # Extract description
            description = self._extract_description(soup, metadata)

            # Extract canonical URL
            canonical_url = self._extract_canonical(soup, url)

            # Extract language
            language = self._extract_language(soup, metadata)

            return {
                "content": extracted_content,
                "title": title,
                "description": description,
                "canonical_url": canonical_url,
                "language": language,
                "metadata": metadata,
                "raw_html": html_content if self.config.get("debug", False) else None,
            }

        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            raise ProcessingError(
                f"Failed to extract content from {url}: {e}") from e

    def _extract_title(self, soup: BeautifulSoup, metadata: Optional[Any]) -> str:
        """Extract page title."""
        # Try metadata first
        if metadata and hasattr(metadata, 'title') and metadata.title:
            return metadata.title.strip()

        # Try HTML title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Try first h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        # Try og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        return "Untitled"

    def _extract_description(self, soup: BeautifulSoup, metadata: Optional[Any]) -> str:
        """Extract page description."""
        # Try metadata first
        if metadata and hasattr(metadata, 'description') and metadata.description:
            return metadata.description.strip()

        # Try meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            return desc_tag['content'].strip()

        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()

        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            if len(text) > 20:  # Must be substantial
                return text[:200] + ('...' if len(text) > 200 else '')

        return ""

    def _extract_canonical(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Extract canonical URL."""
        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag and canonical_tag.get('href'):
            from urllib.parse import urljoin
            return urljoin(current_url, canonical_tag['href'])

        return None

    def _extract_language(self, soup: BeautifulSoup, metadata: Optional[Any]) -> Optional[str]:
        """Extract page language."""
        # Try html lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']

        # Try meta language
        lang_tag = soup.find('meta', attrs={'name': 'language'})
        if lang_tag and lang_tag.get('content'):
            return lang_tag['content']

        # Try http-equiv
        lang_tag = soup.find('meta', {'http-equiv': 'content-language'})
        if lang_tag and lang_tag.get('content'):
            return lang_tag['content']

        return None
