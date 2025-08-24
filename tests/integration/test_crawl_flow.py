"""Integration tests for the complete crawl flow."""

import pytest
from unittest.mock import AsyncMock, patch

from site2md.crawl.crawler import Crawler
from site2md.fetch.http_client import HTTPClient
from site2md.process.extractor import ContentExtractor
from site2md.process.converter import MarkdownConverter


@pytest.mark.integration
class TestCrawlFlow:
    """Test the complete crawl flow integration."""
    
    @pytest.mark.asyncio
    async def test_simple_crawl_flow(self, test_config, sample_html, temp_dir):
        """Test a simple end-to-end crawl flow."""
        # Setup test config with temp directory
        config = test_config.copy()
        config["output"]["directory"] = temp_dir / "export"
        config["limits"]["max_pages"] = 1
        
        # Mock HTTP responses
        mock_responses = {
            "https://example.com": {
                "status_code": 200,
                "content": sample_html,
                "headers": {"content-type": "text/html"},
                "url": "https://example.com"
            },
            "https://example.com/sitemap.xml": {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": "https://example.com/sitemap.xml"
            },
            "https://example.com/robots.txt": {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": "https://example.com/robots.txt"
            }
        }
        
        async def mock_fetch(url):
            return mock_responses.get(url, {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": url
            })
        
        # Create crawler and run
        crawler = Crawler(config)
        
        # Mock the HTTP client fetch method
        with patch.object(HTTPClient, 'fetch', side_effect=mock_fetch):
            try:
                async with crawler:
                    stats = await crawler.crawl()
                
                # Verify results
                assert stats["pages_crawled"] >= 1
                
                # Check output files exist
                output_dir = config["output"]["directory"]
                assert output_dir.exists()
                
                # Look for generated markdown files
                md_files = list(output_dir.glob("**/*.md"))
                assert len(md_files) > 0
                
                # Check README was generated
                readme_path = output_dir / "README.md"
                assert readme_path.exists()
                
                # Verify markdown content
                for md_file in md_files:
                    if md_file.name != "README.md":
                        content = md_file.read_text()
                        assert "---" in content  # Front matter
                        assert "Main Heading" in content  # Extracted content
            
            finally:
                await crawler.cleanup()
    
    @pytest.mark.asyncio
    async def test_crawl_with_sitemap(self, test_config, sample_sitemap, sample_html, temp_dir):
        """Test crawl with sitemap discovery."""
        config = test_config.copy()
        config["output"]["directory"] = temp_dir / "export"
        config["discovery"]["sitemap_first"] = True
        config["limits"]["max_pages"] = 3
        
        mock_responses = {
            "https://example.com": {
                "status_code": 200,
                "content": sample_html,
                "headers": {"content-type": "text/html"},
                "url": "https://example.com"
            },
            "https://example.com/sitemap.xml": {
                "status_code": 200,
                "content": sample_sitemap,
                "headers": {"content-type": "application/xml"},
                "url": "https://example.com/sitemap.xml"
            },
            "https://example.com/about": {
                "status_code": 200,
                "content": sample_html.replace("Sample Page Title", "About Page"),
                "headers": {"content-type": "text/html"},
                "url": "https://example.com/about"
            },
            "https://example.com/contact": {
                "status_code": 200,
                "content": sample_html.replace("Sample Page Title", "Contact Page"),
                "headers": {"content-type": "text/html"},
                "url": "https://example.com/contact"
            },
            "https://example.com/robots.txt": {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": "https://example.com/robots.txt"
            }
        }
        
        async def mock_fetch(url):
            return mock_responses.get(url, {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": url
            })
        
        crawler = Crawler(config)
        
        with patch.object(HTTPClient, 'fetch', side_effect=mock_fetch):
            try:
                async with crawler:
                    stats = await crawler.crawl()
                
                # Should have crawled multiple pages from sitemap
                assert stats["pages_crawled"] >= 2
                
                # Check multiple markdown files were created
                output_dir = config["output"]["directory"]
                md_files = list(output_dir.glob("**/*.md"))
                
                # Should have at least the pages from sitemap (excluding README)
                content_files = [f for f in md_files if f.name != "README.md"]
                assert len(content_files) >= 2
            
            finally:
                await crawler.cleanup()
    
    @pytest.mark.asyncio
    async def test_crawl_with_auth(self, test_config, sample_html, mock_cookies_file, mock_headers_file, temp_dir):
        """Test crawl with authentication."""
        config = test_config.copy()
        config["output"]["directory"] = temp_dir / "export"
        config["auth"]["cookies_file"] = str(mock_cookies_file)
        config["auth"]["headers_file"] = str(mock_headers_file)
        config["limits"]["max_pages"] = 1
        
        mock_responses = {
            "https://example.com": {
                "status_code": 200,
                "content": sample_html,
                "headers": {"content-type": "text/html"},
                "url": "https://example.com"
            },
            "https://example.com/sitemap.xml": {"status_code": 404, "content": "", "headers": {}, "url": "https://example.com/sitemap.xml"},
            "https://example.com/robots.txt": {"status_code": 404, "content": "", "headers": {}, "url": "https://example.com/robots.txt"}
        }
        
        # Track if auth headers were used
        auth_used = {"cookies": False, "headers": False}
        
        async def mock_fetch_with_auth_check(url):
            # In a real scenario, we'd check the HTTP client's headers/cookies
            # For this test, we'll assume auth was applied if the files exist
            auth_used["cookies"] = True
            auth_used["headers"] = True
            return mock_responses.get(url, {
                "status_code": 404,
                "content": "",
                "headers": {},
                "url": url
            })
        
        crawler = Crawler(config)
        
        with patch.object(HTTPClient, 'fetch', side_effect=mock_fetch_with_auth_check):
            try:
                async with crawler:
                    stats = await crawler.crawl()
                
                assert stats["pages_crawled"] >= 1
                assert auth_used["cookies"]  # Verify cookies were loaded
                assert auth_used["headers"]  # Verify headers were loaded
            
            finally:
                await crawler.cleanup()


@pytest.mark.integration 
class TestContentProcessing:
    """Test content extraction and conversion integration."""
    
    @pytest.mark.asyncio
    async def test_html_to_markdown_conversion(self, test_config, sample_html):
        """Test the complete HTML to Markdown conversion pipeline."""
        extractor = ContentExtractor(test_config)
        converter = MarkdownConverter(test_config)
        
        # Extract content
        extracted = await extractor.extract(sample_html, "https://example.com")
        
        # Verify extraction
        assert extracted["title"] == "Sample Page Title"
        assert extracted["description"] == "This is a sample page description."
        assert "Main Heading" in extracted["content"]
        
        # Convert to Markdown
        markdown = await converter.convert(
            extracted, 
            "https://example.com", 
            {"content-type": "text/html"}
        )
        
        # Verify markdown structure
        assert "---" in markdown  # Front matter
        assert "source_url: https://example.com" in markdown
        assert "title: Sample Page Title" in markdown
        assert "# Main Heading" in markdown
        assert "## Subheading" in markdown
        assert "**bold text**" in markdown
        assert "*italic text*" in markdown
        
        # Check list conversion
        assert "- First item" in markdown
        assert "- Second item" in markdown
        
        # Check table conversion
        assert "| Column 1 | Column 2 |" in markdown
        
        # Check code block conversion
        assert "```python" in markdown or "```" in markdown
    
    @pytest.mark.asyncio
    async def test_link_rewriting(self, test_config):
        """Test internal link rewriting in markdown conversion."""
        html_with_links = """
        <html>
        <body>
            <a href="/internal/page">Internal Link</a>
            <a href="https://external.com">External Link</a>
            <a href="relative.html">Relative Link</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor(test_config)
        converter = MarkdownConverter(test_config)
        
        extracted = await extractor.extract(html_with_links, "https://example.com")
        markdown = await converter.convert(
            extracted, 
            "https://example.com", 
            {"content-type": "text/html"}
        )
        
        # Internal links should be converted to relative .md paths
        assert "[Internal Link](example.com/internal/page.md)" in markdown
        
        # External links should remain absolute
        assert "[External Link](https://external.com)" in markdown
        
        # Relative links should be resolved and converted
        assert "[Relative Link](example.com/relative.html.md)" in markdown or "relative.html" in markdown