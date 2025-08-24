"""HTTP client for fetching web content."""

import asyncio
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from ..utils.exceptions import AuthError, FetchError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """Async HTTP client with authentication and retry logic."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.headers: Dict[str, str] = {}
        self.cookies: Dict[str, str] = {}
        
        # Initialize auth
        self._load_auth_config()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.client is None:
            # Client configuration
            timeout = httpx.Timeout(
                timeout=self.config["fetch"]["timeout"],
                connect=10.0,
            )
            
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            )
            
            # Proxy configuration
            proxies = self.config["fetch"].get("proxies")
            
            self.client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                http2=True,
                proxies=proxies,
                headers=self._get_default_headers(),
                cookies=self.cookies,
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch content from URL with retry logic."""
        if not self.client:
            raise FetchError("HTTP client not initialized")
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Add jitter to prevent thundering herd
                if attempt > 0:
                    jitter = random.uniform(0.1, 0.5)
                    delay = base_delay * (2 ** attempt) + jitter
                    await asyncio.sleep(delay)
                
                logger.debug(f"Fetching {url} (attempt {attempt + 1})")
                
                response = await self.client.get(url, headers=self.headers)
                
                # Handle different status codes
                if response.status_code == 200:
                    return await self._process_response(response, url)
                elif response.status_code == 429:  # Rate limited
                    retry_after = response.headers.get("retry-after")
                    if retry_after and attempt < max_retries - 1:
                        delay = min(float(retry_after), 60.0)  # Cap at 60 seconds
                        logger.warning(f"Rate limited for {url}, waiting {delay}s")
                        await asyncio.sleep(delay)
                        continue
                elif response.status_code in (301, 302, 303, 307, 308):
                    # Redirects are handled automatically by httpx
                    return await self._process_response(response, url)
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < max_retries - 1:
                        logger.warning(f"Server error {response.status_code} for {url}, retrying")
                        continue
                else:
                    # Client error - don't retry
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    return {
                        "status_code": response.status_code,
                        "content": "",
                        "headers": dict(response.headers),
                        "url": str(response.url),
                    }
                
            except httpx.TimeoutException:
                logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise FetchError(f"Timeout after {max_retries} attempts: {url}")
                
            except httpx.RequestError as e:
                logger.warning(f"Request error for {url}: {e}")
                if attempt == max_retries - 1:
                    raise FetchError(f"Request failed after {max_retries} attempts: {url}") from e
                
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                raise FetchError(f"Fetch failed: {url}") from e
        
        raise FetchError(f"Failed to fetch after {max_retries} attempts: {url}")
    
    async def _process_response(self, response: httpx.Response, original_url: str) -> Dict[str, Any]:
        """Process HTTP response and extract content."""
        try:
            # Determine content type
            content_type = response.headers.get("content-type", "").lower()
            
            if "text/html" in content_type or "application/xhtml" in content_type:
                # HTML content
                content = response.text
                encoding = response.encoding or "utf-8"
                
                return {
                    "status_code": response.status_code,
                    "content": content,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "encoding": encoding,
                    "content_type": content_type,
                }
            
            elif "application/xml" in content_type or "text/xml" in content_type:
                # XML content (sitemaps, RSS)
                return {
                    "status_code": response.status_code,
                    "content": response.text,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "content_type": content_type,
                }
            
            else:
                # Non-HTML content
                logger.debug(f"Non-HTML content type for {original_url}: {content_type}")
                return {
                    "status_code": response.status_code,
                    "content": "",
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "content_type": content_type,
                }
        
        except Exception as e:
            logger.error(f"Error processing response for {original_url}: {e}")
            raise FetchError(f"Failed to process response: {original_url}") from e
    
    def _load_auth_config(self) -> None:
        """Load authentication configuration."""
        auth_config = self.config.get("auth", {})
        
        # Load cookies from file
        cookies_file = auth_config.get("cookies_file")
        if cookies_file:
            self._load_cookies_file(cookies_file)
        
        # Load headers from file
        headers_file = auth_config.get("headers_file")
        if headers_file:
            self._load_headers_file(headers_file)
    
    def _load_cookies_file(self, cookies_file: str) -> None:
        """Load cookies from file (Netscape or JSON format)."""
        try:
            cookies_path = Path(cookies_file)
            if not cookies_path.exists():
                raise AuthError(f"Cookies file not found: {cookies_file}")
            
            content = cookies_path.read_text(encoding='utf-8')
            
            # Try JSON format first
            if content.strip().startswith('{'):
                cookies_data = json.loads(content)
                if isinstance(cookies_data, dict):
                    self.cookies.update(cookies_data)
                else:
                    # Handle list format from browser exports
                    for cookie in cookies_data:
                        if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                            self.cookies[cookie['name']] = cookie['value']
            
            else:
                # Try Netscape format
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        # Netscape format: domain, flag, path, secure, expiration, name, value
                        name, value = parts[5], parts[6]
                        self.cookies[name] = value
            
            logger.info(f"Loaded {len(self.cookies)} cookies from {cookies_file}")
            
        except Exception as e:
            raise AuthError(f"Failed to load cookies file {cookies_file}: {e}") from e
    
    def _load_headers_file(self, headers_file: str) -> None:
        """Load headers from JSON file."""
        try:
            headers_path = Path(headers_file)
            if not headers_path.exists():
                raise AuthError(f"Headers file not found: {headers_file}")
            
            with open(headers_path, 'r', encoding='utf-8') as f:
                headers_data = json.load(f)
            
            if not isinstance(headers_data, dict):
                raise AuthError(f"Headers file must contain a JSON object: {headers_file}")
            
            self.headers.update(headers_data)
            logger.info(f"Loaded {len(headers_data)} headers from {headers_file}")
            
        except Exception as e:
            raise AuthError(f"Failed to load headers file {headers_file}: {e}") from e
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        headers = {
            "User-Agent": self.config["fetch"]["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Add custom headers
        headers.update(self.headers)
        
        return headers