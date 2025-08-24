"""Main crawler orchestrator for Site2MD."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from rich.progress import Progress, TaskID

from ..fetch.http_client import HTTPClient
from ..fetch.playwright_client import PlaywrightClient
from ..process.converter import MarkdownConverter
from ..process.extractor import ContentExtractor
from ..storage.filesystem import FileSystemManager
from ..storage.manifest import CrawlManifest
from ..utils.exceptions import CrawlError
from ..utils.logging import CrawlStatsLogger, get_logger
from ..utils.validation import normalize_url, should_crawl_url
from .discovery import URLDiscovery
from .robots import RobotsChecker
from .url_manager import URLManager

logger = get_logger(__name__)


class Crawler:
    """Main crawler that orchestrates the crawling process."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stats_logger = CrawlStatsLogger(logger)
        
        # Initialize components
        self.url_manager = URLManager(config)
        self.url_discovery = URLDiscovery(config)
        self.robots_checker = RobotsChecker(config)
        self.http_client = HTTPClient(config)
        self.playwright_client = None
        self.content_extractor = ContentExtractor(config)
        self.markdown_converter = MarkdownConverter(config)
        self.filesystem = FileSystemManager(config)
        self.manifest = CrawlManifest(config["output"]["directory"])
        
        # State
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.http_client.__aenter__()
        if self.config["render"]["enabled"]:
            self.playwright_client = PlaywrightClient(self.config)
            await self.playwright_client.__aenter__()
        await self.manifest.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self.http_client, 'close'):
            await self.http_client.close()
        if self.playwright_client:
            await self.playwright_client.__aexit__(None, None, None)
    
    async def preview_urls(self) -> List[str]:
        """Preview URLs that would be crawled without actually crawling."""
        logger.info("Generating crawl preview")
        
        # Initialize discovery
        start_urls = [normalize_url(url) for url in self.config["start_urls"]]
        
        # Discover URLs
        discovered_urls = await self.url_discovery.discover_urls(start_urls)
        
        # Filter URLs based on scope rules
        filtered_urls = []
        for url in discovered_urls:
            if should_crawl_url(
                url,
                start_urls[0],  # Use first URL as base
                self.config["scope"]["allow_subdomains"],
                self.config["scope"]["include"],
                self.config["scope"]["exclude"],
            ):
                filtered_urls.append(url)
        
        # Apply limits
        max_pages = self.config["limits"]["max_pages"]
        if max_pages and len(filtered_urls) > max_pages:
            filtered_urls = filtered_urls[:max_pages]
        
        return filtered_urls
    
    async def crawl(self) -> Dict[str, Any]:
        """Execute the full crawl process."""
        logger.info("Starting crawl process")
        self.stats_logger.stats["start_time"] = datetime.now()
        
        try:
            # Initialize
            async with self:
                start_urls = [normalize_url(url) for url in self.config["start_urls"]]
                
                # Discover URLs
                logger.info("Discovering URLs")
                discovered_urls = await self.url_discovery.discover_urls(start_urls)
                
                # Add to URL manager
                await self.url_manager.add_urls(discovered_urls)
                
                # Create semaphore for concurrency control
                concurrency = self.config["fetch"]["concurrency"]
                semaphore = asyncio.Semaphore(concurrency)
                
                # Process URLs
                tasks = []
                processed_count = 0
                max_pages = self.config["limits"]["max_pages"]
                
                async for url, priority in self.url_manager.get_next_batch():
                    if max_pages and processed_count >= max_pages:
                        break
                    
                    task = asyncio.create_task(
                        self._crawl_url(url, semaphore)
                    )
                    tasks.append(task)
                    processed_count += 1
                    
                    # Process in batches to avoid overwhelming the system
                    if len(tasks) >= concurrency * 2:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        tasks = []
                
                # Wait for remaining tasks
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Generate site-level README
                await self._generate_site_readme()
                
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            raise CrawlError(f"Crawl failed: {e}") from e
        
        finally:
            self.stats_logger.stats["end_time"] = datetime.now()
        
        return self.stats_logger.get_stats()
    
    async def _crawl_url(self, url: str, semaphore: asyncio.Semaphore) -> None:
        """Crawl a single URL."""
        async with semaphore:
            try:
                # Check robots.txt
                if not await self.robots_checker.can_fetch(url):
                    logger.debug(f"Robots.txt disallows: {url}")
                    return
                
                # Check if already processed
                if url in self.crawled_urls:
                    self.stats_logger.log_page_cached(url)
                    return
                
                # Check incremental mode
                if self.config.get("incremental", {}).get("enabled", False):
                    if await self.manifest.is_up_to_date(url):
                        self.stats_logger.log_page_cached(url)
                        return
                
                # Fetch content
                response = await self._fetch_content(url)
                if not response:
                    self.stats_logger.log_page_failed(url, "Failed to fetch")
                    return
                
                # Process content
                await self._process_content(url, response)
                
                self.crawled_urls.add(url)
                self.stats_logger.log_page_crawled(url, len(response.get("content", "")))
                
                # Add delay to be polite
                delay = self.config["fetch"].get("delay_seconds", 0)
                if delay > 0:
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                self.failed_urls.add(url)
                self.stats_logger.log_page_failed(url, str(e))
    
    async def _fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch content from URL using appropriate method."""
        try:
            # Try Playwright first if rendering is enabled
            if self.config["render"]["enabled"] and self.playwright_client:
                try:
                    return await self.playwright_client.fetch_rendered(url)
                except Exception as e:
                    logger.warning(f"Playwright failed for {url}, falling back to HTTP: {e}")
            
            # Use HTTP client
            return await self.http_client.fetch(url)
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    async def _process_content(self, url: str, response: Dict[str, Any]) -> None:
        """Process fetched content and save as Markdown."""
        try:
            content = response.get("content", "")
            if not content:
                return
            
            # Extract main content
            extracted = await self.content_extractor.extract(content, url)
            
            # Convert to Markdown
            markdown = await self.markdown_converter.convert(
                extracted, url, response.get("headers", {})
            )
            
            # Save to filesystem
            filepath = await self.filesystem.save_page(url, markdown)
            
            # Update manifest
            await self.manifest.update_page(
                url=url,
                filepath=filepath,
                content_hash=hash(markdown),
                etag=response.get("headers", {}).get("etag"),
                last_modified=response.get("headers", {}).get("last-modified"),
            )
            
            logger.debug(f"Processed and saved: {url} -> {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to process content for {url}: {e}")
            raise
    
    async def _generate_site_readme(self) -> None:
        """Generate a site-level README with crawl results."""
        try:
            stats = self.stats_logger.get_stats()
            
            readme_content = f"""# Site Export Results

Generated by Site2MD on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics

- **Pages Crawled**: {stats['pages_crawled']}
- **Pages Cached**: {stats['pages_cached']}
- **Pages Failed**: {stats['pages_failed']}
- **Assets Downloaded**: {stats['assets_downloaded']}
- **Total Size**: {stats['total_bytes']:,} bytes
- **Duration**: {stats.get('duration_seconds', 0):.1f} seconds

## Configuration

- **Start URLs**: {', '.join(self.config['start_urls'])}
- **Max Pages**: {self.config['limits']['max_pages']}
- **Max Depth**: {self.config['limits']['max_depth']}
- **Concurrency**: {self.config['fetch']['concurrency']}
- **Respect Robots**: {self.config['fetch']['respect_robots']}

## Files Generated

All pages have been exported as Markdown files with the following structure:

```
{self.config['output']['directory']}/
├── README.md (this file)
└── [domain]/[path].md (exported pages)
```

Each exported page includes YAML front matter with metadata like source URL, title, and fetch timestamp.
"""
            
            readme_path = self.config["output"]["directory"] / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info(f"Generated site README: {readme_path}")
            
        except Exception as e:
            logger.warning(f"Failed to generate site README: {e}")