"""URL and content validation utilities for Site2MD."""

import re
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import tldextract
from tldextract import TLDExtract

from .exceptions import ValidationError

# Initialize TLD extractor with cache
tld_extract = TLDExtract(cache_dir=None)


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normalize URL for consistent processing."""
    try:
        # Resolve relative URLs
        if base_url:
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        
        # Ensure scheme is present
        if not parsed.scheme:
            raise ValidationError(f"URL missing scheme: {url}")
        
        # Normalize scheme to lowercase
        scheme = parsed.scheme.lower()
        if scheme not in ('http', 'https'):
            raise ValidationError(f"Unsupported URL scheme: {scheme}")
        
        # Normalize hostname to lowercase
        hostname = parsed.hostname
        if not hostname:
            raise ValidationError(f"URL missing hostname: {url}")
        hostname = hostname.lower()
        
        # Normalize port (remove default ports)
        port = parsed.port
        if port:
            if (scheme == 'http' and port == 80) or (scheme == 'https' and port == 443):
                port = None
        
        # Reconstruct netloc
        netloc = hostname
        if parsed.username:
            auth = parsed.username
            if parsed.password:
                auth += f":{parsed.password}"
            netloc = f"{auth}@{netloc}"
        if port:
            netloc += f":{port}"
        
        # Normalize path
        path = parsed.path or '/'
        if not path.startswith('/'):
            path = '/' + path
        
        # Remove fragment (hash)
        fragment = ''
        
        # Keep query string (may be important for content)
        query = parsed.query
        
        # Reconstruct URL
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
        return normalized
        
    except Exception as e:
        raise ValidationError(f"Invalid URL '{url}': {e}") from e


def get_domain_info(url: str) -> Tuple[str, str, str]:
    """Extract domain information from URL."""
    try:
        result = tld_extract(url)
        domain = result.domain
        suffix = result.suffix
        subdomain = result.subdomain
        
        if not domain or not suffix:
            raise ValidationError(f"Invalid domain in URL: {url}")
        
        registrable_domain = f"{domain}.{suffix}"
        full_domain = f"{subdomain}.{registrable_domain}" if subdomain else registrable_domain
        
        return full_domain, registrable_domain, subdomain
        
    except Exception as e:
        raise ValidationError(f"Error extracting domain from '{url}': {e}") from e


def is_same_domain(url1: str, url2: str, allow_subdomains: bool = False) -> bool:
    """Check if two URLs belong to the same domain."""
    try:
        _, reg_domain1, subdomain1 = get_domain_info(url1)
        _, reg_domain2, subdomain2 = get_domain_info(url2)
        
        if allow_subdomains:
            return reg_domain1 == reg_domain2
        else:
            full1 = f"{subdomain1}.{reg_domain1}" if subdomain1 else reg_domain1
            full2 = f"{subdomain2}.{reg_domain2}" if subdomain2 else reg_domain2
            return full1 == full2
            
    except ValidationError:
        return False


def is_valid_content_url(url: str) -> bool:
    """Check if URL points to valid content (not binary files)."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Skip obvious binary files
    binary_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.exe', '.dmg', '.deb', '.rpm',
        '.css', '.js'  # Usually not main content
    }
    
    for ext in binary_extensions:
        if path.endswith(ext):
            return False
    
    return True


def matches_pattern(url: str, patterns: list, is_include: bool = True) -> bool:
    """Check if URL matches any of the given regex patterns."""
    if not patterns:
        return is_include  # Default behavior when no patterns
    
    for pattern in patterns:
        try:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        except re.error:
            continue  # Skip invalid patterns
    
    return False


def should_crawl_url(
    url: str, 
    base_url: str, 
    allow_subdomains: bool = False,
    include_patterns: Optional[list] = None,
    exclude_patterns: Optional[list] = None
) -> bool:
    """Determine if URL should be crawled based on scope rules."""
    # Must be same domain
    if not is_same_domain(url, base_url, allow_subdomains):
        return False
    
    # Must be valid content
    if not is_valid_content_url(url):
        return False
    
    # Check exclude patterns first
    if exclude_patterns and matches_pattern(url, exclude_patterns):
        return False
    
    # Check include patterns
    if include_patterns and not matches_pattern(url, include_patterns):
        return False
    
    return True


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for filesystem compatibility."""
    # Remove/replace invalid characters
    invalid_chars = r'<>:"/\\|?*\x00-\x1f'
    sanitized = re.sub(f'[{re.escape(invalid_chars)}]', '_', filename)
    
    # Replace multiple underscores with single
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim and ensure not empty
    sanitized = sanitized.strip('._')
    if not sanitized:
        sanitized = 'index'
    
    # Truncate if too long
    if len(sanitized) > max_length:
        # Keep extension if present
        name_parts = sanitized.rsplit('.', 1)
        if len(name_parts) == 2 and len(name_parts[1]) <= 10:
            name, ext = name_parts
            max_name_length = max_length - len(ext) - 1
            sanitized = name[:max_name_length] + '.' + ext
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def url_to_filepath(url: str, base_url: str, extension: str = '.md') -> str:
    """Convert URL to relative filepath."""
    parsed_base = urlparse(base_url)
    parsed_url = urlparse(url)
    
    # Start with hostname for organization
    domain_parts = [parsed_url.hostname or 'unknown']
    
    # Add path components
    path = parsed_url.path.strip('/')
    if path:
        path_parts = path.split('/')
        # Sanitize each part
        path_parts = [sanitize_filename(part) for part in path_parts if part]
        domain_parts.extend(path_parts)
    
    # Create filename
    if domain_parts[-1] == parsed_url.hostname or not domain_parts[-1]:
        domain_parts[-1] = 'index'
    
    # Ensure extension
    if not domain_parts[-1].endswith(extension):
        domain_parts[-1] += extension
    
    return '/'.join(domain_parts)


def extract_canonical_url(html_content: str, current_url: str) -> Optional[str]:
    """Extract canonical URL from HTML content."""
    import re
    
    # Look for canonical link tag
    canonical_pattern = r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']'
    match = re.search(canonical_pattern, html_content, re.IGNORECASE)
    
    if match:
        canonical_url = match.group(1)
        # Resolve relative URLs
        canonical_url = urljoin(current_url, canonical_url)
        try:
            return normalize_url(canonical_url)
        except ValidationError:
            pass
    
    return None