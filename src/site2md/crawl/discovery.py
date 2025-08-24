"""URL discovery via sitemaps and BFS crawling."""

import asyncio
import re
from typing import Any, Dict, List, Set
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

from ..fetch.http_client import HTTPClient
from ..utils.exceptions import CrawlError
from ..utils.logging import get_logger
from ..utils.validation import normalize_url, should_crawl_url

logger = get_logger(__name__)


class URLDiscovery:
    """Discovers URLs via sitemaps and breadth-first search."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.http_client = HTTPClient(config)
        self.discovered_urls: Set[str] = set()
        
    async def discover_urls(self, start_urls: List[str]) -> List[str]:
        """Discover all URLs to crawl."""
        logger.info(f"Starting URL discovery from {len(start_urls)} seeds")
        
        # Initialize with start URLs
        for url in start_urls:
            self.discovered_urls.add(url)
        
        # Discover via sitemaps first if enabled
        if self.config.get("discovery", {}).get("sitemap_first", True):
            await self._discover_from_sitemaps(start_urls)
        
        # Discover via BFS crawling
        await self._discover_via_bfs(start_urls)
        
        # Convert to sorted list (helps with consistency)
        urls = sorted(list(self.discovered_urls))
        logger.info(f"Discovered {len(urls)} total URLs")
        
        return urls
    
    async def _discover_from_sitemaps(self, start_urls: List[str]) -> None:
        """Discover URLs from XML sitemaps."""
        logger.info("Discovering URLs from sitemaps")
        
        for start_url in start_urls:
            try:
                # Common sitemap locations
                sitemap_urls = [
                    urljoin(start_url, '/sitemap.xml'),
                    urljoin(start_url, '/sitemap_index.xml'),
                    urljoin(start_url, '/robots.txt'),  # Check for sitemap references
                ]
                
                # Check each potential sitemap
                for sitemap_url in sitemap_urls:
                    await self._parse_sitemap(sitemap_url, start_url)
                
            except Exception as e:
                logger.warning(f"Sitemap discovery failed for {start_url}: {e}")
    
    async def _parse_sitemap(self, sitemap_url: str, base_url: str) -> None:
        """Parse a sitemap XML file."""
        try:
            async with self.http_client:
                response = await self.http_client.fetch(sitemap_url)
                
                if not response or response.get("status_code", 0) >= 400:
                    return
                
                content = response.get("content", "")
                if not content:
                    return
                
                # Handle robots.txt case - extract sitemap references
                if sitemap_url.endswith("robots.txt"):
                    await self._parse_robots_sitemaps(content, base_url)
                    return
                
                # Parse XML sitemap
                await self._parse_xml_sitemap(content, base_url)
                
        except Exception as e:
            logger.debug(f"Failed to parse sitemap {sitemap_url}: {e}")
    
    async def _parse_robots_sitemaps(self, robots_content: str, base_url: str) -> None:
        """Extract sitemap URLs from robots.txt."""
        sitemap_pattern = r'^Sitemap:\s*(.+)$'
        
        for line in robots_content.split('\n'):
            match = re.match(sitemap_pattern, line.strip(), re.IGNORECASE)
            if match:
                sitemap_url = match.group(1).strip()
                sitemap_url = urljoin(base_url, sitemap_url)
                await self._parse_sitemap(sitemap_url, base_url)
    
    async def _parse_xml_sitemap(self, xml_content: str, base_url: str) -> None:
        """Parse XML sitemap content."""
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespace
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }
            
            # Check if this is a sitemap index
            sitemaps = root.findall('.//sm:sitemap', namespaces)
            if sitemaps:
                # This is a sitemap index - parse child sitemaps
                for sitemap in sitemaps:
                    loc_elem = sitemap.find('sm:loc', namespaces)
                    if loc_elem is not None and loc_elem.text:
                        child_url = normalize_url(loc_elem.text.strip())
                        await self._parse_sitemap(child_url, base_url)
                return
            
            # This is a regular sitemap - extract URLs
            urls = root.findall('.//sm:url', namespaces)
            for url_elem in urls:
                loc_elem = url_elem.find('sm:loc', namespaces)
                if loc_elem is not None and loc_elem.text:
                    url = loc_elem.text.strip()
                    try:
                        normalized_url = normalize_url(url)
                        if should_crawl_url(
                            normalized_url,
                            base_url,
                            self.config["scope"]["allow_subdomains"],
                            self.config["scope"]["include"],
                            self.config["scope"]["exclude"],
                        ):
                            self.discovered_urls.add(normalized_url)
                    except Exception as e:
                        logger.debug(f"Invalid URL in sitemap {url}: {e}")
            
            logger.debug(f"Found {len(urls)} URLs in sitemap")
            
        except ET.ParseError as e:
            logger.debug(f"Failed to parse XML sitemap: {e}")
        except Exception as e:
            logger.warning(f"Error processing sitemap: {e}")
    
    async def _discover_via_bfs(self, start_urls: List[str]) -> None:
        """Discover URLs via breadth-first search crawling."""
        if not self.config.get("discovery", {}).get("bfs_enabled", True):
            return
        
        logger.info("Discovering URLs via BFS crawling")
        
        queue = list(start_urls)
        visited = set(start_urls)
        current_depth = 0
        max_depth = self.config["limits"]["max_depth"]
        max_pages = self.config["limits"]["max_pages"]
        
        while queue and current_depth < max_depth and len(self.discovered_urls) < max_pages:
            next_queue = []
            batch_size = min(len(queue), self.config["fetch"]["concurrency"])
            
            # Process current level in batches
            for i in range(0, len(queue), batch_size):
                batch = queue[i:i + batch_size]
                tasks = [self._extract_links_from_page(url, start_urls[0]) for url in batch]
                
                try:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, Exception):
                            continue
                        if isinstance(result, list):
                            for url in result:
                                if url not in visited and len(self.discovered_urls) < max_pages:
                                    visited.add(url)
                                    next_queue.append(url)
                                    self.discovered_urls.add(url)
                
                except Exception as e:
                    logger.warning(f"BFS batch failed at depth {current_depth}: {e}")
            
            queue = next_queue
            current_depth += 1
            
            logger.debug(f"BFS depth {current_depth}: found {len(next_queue)} new URLs")
    
    async def _extract_links_from_page(self, url: str, base_url: str) -> List[str]:
        """Extract links from a single page."""
        try:
            async with self.http_client:
                response = await self.http_client.fetch(url)
                
                if not response or response.get("status_code", 0) >= 400:
                    return []
                
                content = response.get("content", "")
                if not content:
                    return []
                
                return self._extract_links_from_html(content, url, base_url)
                
        except Exception as e:
            logger.debug(f"Failed to extract links from {url}: {e}")
            return []
    
    def _extract_links_from_html(self, html_content: str, current_url: str, base_url: str) -> List[str]:
        """Extract links from HTML content."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Extract href attributes from anchor tags
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                # Skip empty, javascript, mailto, tel links
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                
                try:
                    # Convert to absolute URL
                    absolute_url = urljoin(current_url, href)
                    normalized_url = normalize_url(absolute_url)
                    
                    # Check if should crawl
                    if should_crawl_url(
                        normalized_url,
                        base_url,
                        self.config["scope"]["allow_subdomains"],
                        self.config["scope"]["include"],
                        self.config["scope"]["exclude"],
                    ):
                        links.append(normalized_url)
                
                except Exception as e:
                    logger.debug(f"Invalid link {href} on {current_url}: {e}")
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.debug(f"Failed to parse HTML for links: {e}")
            return []