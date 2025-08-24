"""Convert extracted content to high-quality Markdown."""

import re
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import markdownify
import yaml

from ..utils.exceptions import ProcessingError
from ..utils.logging import get_logger
from ..utils.validation import normalize_url, url_to_filepath

logger = get_logger(__name__)


class MarkdownConverter:
    """Converts HTML content to high-quality Markdown."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Configure markdownify
        self.md_converter = markdownify.MarkdownConverter(
            heading_style=markdownify.ATX,  # Use # style headings
            bullets="-",  # Use - for bullet points
            strong_em_style=markdownify.ASTERISK,  # Use * for bold/italic
            strip=['script', 'style']  # Strip these tags only
        )

    async def convert(
        self,
        extracted_data: Dict[str, Any],
        source_url: str,
        headers: Dict[str, str]
    ) -> str:
        """Convert extracted content to Markdown with front matter."""
        try:
            # Extract content and metadata
            content = extracted_data.get("content", "")
            title = extracted_data.get("title", "Untitled")
            description = extracted_data.get("description", "")
            canonical_url = extracted_data.get("canonical_url") or source_url
            language = extracted_data.get("language")

            # Convert content to Markdown
            if content:
                markdown_content = self._convert_html_to_markdown(
                    content, source_url)
            else:
                markdown_content = "*No content extracted*"

            # Generate front matter
            front_matter = self._generate_front_matter(
                source_url=source_url,
                canonical_url=canonical_url,
                title=title,
                description=description,
                language=language,
                headers=headers
            )

            # Add table of contents if enabled
            if self.config.get("markdown", {}).get("add_toc", False):
                toc = self._generate_toc(markdown_content)
                if toc:
                    markdown_content = f"{toc}\n\n{markdown_content}"

            # Combine front matter and content
            full_markdown = f"{front_matter}\n\n{markdown_content}"

            # Clean up the Markdown
            full_markdown = self._clean_markdown(full_markdown)

            return full_markdown

        except Exception as e:
            logger.error(f"Markdown conversion failed for {source_url}: {e}")
            raise ProcessingError(
                f"Failed to convert to Markdown: {source_url}") from e

    def _convert_html_to_markdown(self, html_content: str, base_url: str) -> str:
        """Convert HTML to Markdown with link rewriting."""
        try:
            # First pass: convert to Markdown
            markdown = self.md_converter.convert(html_content)

            # Post-process: fix links
            markdown = self._rewrite_links(markdown, base_url)

            # Post-process: improve code blocks
            markdown = self._improve_code_blocks(markdown)

            # Post-process: clean up tables
            markdown = self._clean_tables(markdown)

            return markdown

        except Exception as e:
            logger.warning(f"HTML to Markdown conversion failed: {e}")
            # Fallback: return cleaned HTML
            return self._fallback_conversion(html_content)

    def _rewrite_links(self, markdown: str, base_url: str) -> str:
        """Rewrite links in Markdown to use relative paths for internal links."""
        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)

            try:
                # Convert relative to absolute
                absolute_url = urljoin(base_url, link_url)
                normalized_url = normalize_url(absolute_url)

                # Check if it's an internal link
                base_domain = urlparse(base_url).netloc
                link_domain = urlparse(normalized_url).netloc

                if base_domain == link_domain:
                    # Internal link - convert to relative .md path
                    relative_path = url_to_filepath(
                        normalized_url, base_url, '.md')
                    return f"[{link_text}]({relative_path})"
                else:
                    # External link - keep absolute
                    return f"[{link_text}]({normalized_url})"

            except Exception as e:
                logger.debug(f"Failed to rewrite link {link_url}: {e}")
                return match.group(0)  # Return original

        # Match Markdown links: [text](url)
        link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(link_pattern, replace_link, markdown)

    def _improve_code_blocks(self, markdown: str) -> str:
        """Improve code block formatting."""
        # Convert inline code blocks to fenced blocks when appropriate
        # This is a simple heuristic - look for code blocks with newlines
        def replace_code(match):
            code = match.group(1)
            if '\n' in code and len(code.strip()) > 50:
                # Multi-line code should be fenced
                language = self._detect_language(code)
                return f"\n```{language}\n{code.strip()}\n```\n"
            else:
                return match.group(0)  # Keep inline

        # Match inline code: `code`
        code_pattern = r'`([^`]+)`'
        return re.sub(code_pattern, replace_code, markdown)

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code snippet."""
        code_lower = code.lower()

        # Simple language detection heuristics
        if any(keyword in code_lower for keyword in ['function', 'var ', 'let ', 'const ']):
            return 'javascript'
        elif any(keyword in code_lower for keyword in ['def ', 'import ', 'from ']):
            return 'python'
        elif any(keyword in code_lower for keyword in ['class ', 'public ', 'private ']):
            return 'java'
        elif '<?php' in code_lower or '<?=' in code_lower:
            return 'php'
        elif any(keyword in code_lower for keyword in ['<div', '<span', '<html']):
            return 'html'
        elif any(keyword in code_lower for keyword in ['select ', 'from ', 'where ']):
            return 'sql'

        return ''  # No language detected

    def _clean_tables(self, markdown: str) -> str:
        """Clean up table formatting."""
        # This is a placeholder - markdownify usually handles tables well
        # Could add more sophisticated table cleaning here
        return markdown

    def _generate_front_matter(
        self,
        source_url: str,
        canonical_url: str,
        title: str,
        description: str,
        language: Optional[str],
        headers: Dict[str, str]
    ) -> str:
        """Generate YAML front matter."""
        if not self.config.get("markdown", {}).get("front_matter", True):
            return ""

        front_matter_data = {
            "source_url": canonical_url,
            "title": title,
            "fetched_at": datetime.now().isoformat(),
        }

        if description:
            front_matter_data["description"] = description

        if language:
            front_matter_data["language"] = language

        # Add useful headers
        if "last-modified" in headers:
            front_matter_data["last_modified"] = headers["last-modified"]

        if "etag" in headers:
            front_matter_data["etag"] = headers["etag"]

        # Add empty tags array for user customization
        front_matter_data["tags"] = []

        try:
            yaml_content = yaml.dump(
                front_matter_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
            return f"---\n{yaml_content.strip()}\n---"
        except Exception as e:
            logger.warning(f"Failed to generate YAML front matter: {e}")
            return ""

    def _generate_toc(self, markdown_content: str) -> str:
        """Generate table of contents from headings."""
        headings = []

        # Extract headings
        for line in markdown_content.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                # Count heading level
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break

                if 1 <= level <= 6:
                    heading_text = line[level:].strip()
                    if heading_text:
                        # Create anchor
                        anchor = re.sub(r'[^\w\s-]', '', heading_text.lower())
                        anchor = re.sub(r'[\s_-]+', '-', anchor)
                        headings.append((level, heading_text, anchor))

        if not headings:
            return ""

        # Generate TOC
        toc_lines = ["## Table of Contents", ""]

        for level, text, anchor in headings:
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{text}](#{anchor})")

        return "\n".join(toc_lines)

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown formatting issues."""
        # Remove excessive blank lines
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)

        # Ensure proper spacing around headings
        markdown = re.sub(r'\n(#{1,6}[^#])', r'\n\n\1', markdown)
        markdown = re.sub(r'(#{1,6}[^\n]*)\n([^#\n])', r'\1\n\n\2', markdown)

        # Clean up list formatting
        markdown = re.sub(r'\n(\s*[-*+])', r'\n\n\1', markdown)

        # Remove trailing whitespace
        lines = markdown.split('\n')
        lines = [line.rstrip() for line in lines]

        return '\n'.join(lines).strip()

    def _fallback_conversion(self, html_content: str) -> str:
        """Fallback conversion when markdownify fails."""
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip()
                      for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception:
            return "*Failed to convert content*"
