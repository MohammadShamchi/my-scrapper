"""Unit tests for URL validation utilities."""

import pytest

from site2md.utils.validation import (
    normalize_url,
    get_domain_info,
    is_same_domain,
    is_valid_content_url,
    matches_pattern,
    should_crawl_url,
    sanitize_filename,
    url_to_filepath,
)
from site2md.utils.exceptions import ValidationError


class TestURLNormalization:
    """Test URL normalization functionality."""
    
    def test_normalize_basic_url(self):
        """Test basic URL normalization."""
        url = "https://Example.Com/Path/"
        expected = "https://example.com/Path/"
        assert normalize_url(url) == expected
    
    def test_normalize_remove_fragment(self):
        """Test fragment removal."""
        url = "https://example.com/page#section"
        expected = "https://example.com/page"
        assert normalize_url(url) == expected
    
    def test_normalize_preserve_query(self):
        """Test query string preservation."""
        url = "https://example.com/page?param=value"
        expected = "https://example.com/page?param=value"
        assert normalize_url(url) == expected
    
    def test_normalize_default_port_removal(self):
        """Test default port removal."""
        url = "https://example.com:443/page"
        expected = "https://example.com/page"
        assert normalize_url(url) == expected
        
        url = "http://example.com:80/page"
        expected = "http://example.com/page"
        assert normalize_url(url) == expected
    
    def test_normalize_add_trailing_slash(self):
        """Test adding trailing slash to root."""
        url = "https://example.com"
        expected = "https://example.com/"
        assert normalize_url(url) == expected
    
    def test_normalize_invalid_url(self):
        """Test invalid URL handling."""
        with pytest.raises(ValidationError):
            normalize_url("not-a-url")
        
        with pytest.raises(ValidationError):
            normalize_url("ftp://example.com")  # Unsupported scheme


class TestDomainInfo:
    """Test domain information extraction."""
    
    def test_get_domain_info_basic(self):
        """Test basic domain extraction."""
        url = "https://www.example.com/path"
        full, registrable, subdomain = get_domain_info(url)
        
        assert full == "www.example.com"
        assert registrable == "example.com"
        assert subdomain == "www"
    
    def test_get_domain_info_no_subdomain(self):
        """Test domain extraction without subdomain."""
        url = "https://example.com/path"
        full, registrable, subdomain = get_domain_info(url)
        
        assert full == "example.com"
        assert registrable == "example.com"
        assert subdomain == ""
    
    def test_get_domain_info_multiple_subdomains(self):
        """Test domain extraction with multiple subdomains."""
        url = "https://api.v1.example.com/path"
        full, registrable, subdomain = get_domain_info(url)
        
        assert full == "api.v1.example.com"
        assert registrable == "example.com"
        assert subdomain == "api.v1"


class TestSameDomain:
    """Test same domain checking."""
    
    def test_is_same_domain_exact_match(self):
        """Test exact domain match."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert is_same_domain(url1, url2, allow_subdomains=False)
    
    def test_is_same_domain_subdomain_disallowed(self):
        """Test subdomain mismatch when not allowed."""
        url1 = "https://example.com/page1"
        url2 = "https://www.example.com/page2"
        assert not is_same_domain(url1, url2, allow_subdomains=False)
    
    def test_is_same_domain_subdomain_allowed(self):
        """Test subdomain match when allowed."""
        url1 = "https://example.com/page1"
        url2 = "https://www.example.com/page2"
        assert is_same_domain(url1, url2, allow_subdomains=True)
    
    def test_is_same_domain_different_domains(self):
        """Test different domains."""
        url1 = "https://example.com/page1"
        url2 = "https://other.com/page2"
        assert not is_same_domain(url1, url2, allow_subdomains=True)


class TestValidContentURL:
    """Test valid content URL checking."""
    
    def test_is_valid_content_url_html(self):
        """Test HTML URLs are valid."""
        assert is_valid_content_url("https://example.com/page")
        assert is_valid_content_url("https://example.com/page.html")
        assert is_valid_content_url("https://example.com/")
    
    def test_is_valid_content_url_binary_files(self):
        """Test binary files are invalid."""
        assert not is_valid_content_url("https://example.com/image.jpg")
        assert not is_valid_content_url("https://example.com/document.pdf")
        assert not is_valid_content_url("https://example.com/archive.zip")
        assert not is_valid_content_url("https://example.com/styles.css")
        assert not is_valid_content_url("https://example.com/script.js")


class TestPatternMatching:
    """Test regex pattern matching."""
    
    def test_matches_pattern_simple(self):
        """Test simple pattern matching."""
        url = "https://example.com/docs/guide"
        patterns = [r"docs", r"api"]
        assert matches_pattern(url, patterns)
    
    def test_matches_pattern_no_match(self):
        """Test pattern non-matching."""
        url = "https://example.com/blog/post"
        patterns = [r"docs", r"api"]
        assert not matches_pattern(url, patterns)
    
    def test_matches_pattern_empty_patterns(self):
        """Test empty patterns list."""
        url = "https://example.com/page"
        patterns = []
        assert matches_pattern(url, patterns, is_include=True)
        assert not matches_pattern(url, patterns, is_include=False)


class TestFilenameHandling:
    """Test filename sanitization and path conversion."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        filename = "valid_filename.txt"
        assert sanitize_filename(filename) == "valid_filename.txt"
    
    def test_sanitize_filename_invalid_chars(self):
        """Test invalid character removal."""
        filename = 'file<name>with:invalid"chars'
        expected = "file_name_with_invalid_chars"
        assert sanitize_filename(filename) == expected
    
    def test_sanitize_filename_too_long(self):
        """Test long filename truncation."""
        filename = "a" * 300
        result = sanitize_filename(filename)
        assert len(result) <= 255
    
    def test_sanitize_filename_empty(self):
        """Test empty filename handling."""
        filename = ""
        assert sanitize_filename(filename) == "index"
    
    def test_url_to_filepath_basic(self):
        """Test basic URL to filepath conversion."""
        url = "https://example.com/docs/guide"
        base_url = "https://example.com"
        expected = "example.com/docs/guide.md"
        assert url_to_filepath(url, base_url) == expected
    
    def test_url_to_filepath_root(self):
        """Test root URL conversion."""
        url = "https://example.com/"
        base_url = "https://example.com"
        expected = "example.com/index.md"
        assert url_to_filepath(url, base_url) == expected


class TestShouldCrawlURL:
    """Test comprehensive URL crawling decision logic."""
    
    def test_should_crawl_url_same_domain(self):
        """Test same domain crawling."""
        url = "https://example.com/page"
        base_url = "https://example.com"
        assert should_crawl_url(url, base_url)
    
    def test_should_crawl_url_different_domain(self):
        """Test different domain rejection."""
        url = "https://other.com/page"
        base_url = "https://example.com"
        assert not should_crawl_url(url, base_url)
    
    def test_should_crawl_url_binary_file(self):
        """Test binary file rejection."""
        url = "https://example.com/image.jpg"
        base_url = "https://example.com"
        assert not should_crawl_url(url, base_url)
    
    def test_should_crawl_url_exclude_pattern(self):
        """Test exclude pattern rejection."""
        url = "https://example.com/admin/page"
        base_url = "https://example.com"
        exclude_patterns = [r"admin"]
        assert not should_crawl_url(
            url, base_url, exclude_patterns=exclude_patterns
        )
    
    def test_should_crawl_url_include_pattern(self):
        """Test include pattern requirement."""
        url = "https://example.com/docs/page"
        base_url = "https://example.com"
        include_patterns = [r"docs"]
        assert should_crawl_url(
            url, base_url, include_patterns=include_patterns
        )
        
        # Non-matching URL should be rejected
        url = "https://example.com/blog/page"
        assert not should_crawl_url(
            url, base_url, include_patterns=include_patterns
        )