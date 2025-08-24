"""URL queue management and prioritization."""

import asyncio
import heapq
from typing import Any, AsyncIterator, Dict, List, Set, Tuple
from urllib.parse import urlparse

from ..utils.logging import get_logger
from ..utils.validation import normalize_url

logger = get_logger(__name__)


class URLManager:
    """Manages URL queue with prioritization and deduplication."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url_queue: List[Tuple[int, str]] = []  # (priority, url)
        self.processed_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.url_priorities: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def add_urls(self, urls: List[str]) -> None:
        """Add URLs to the queue with appropriate priority."""
        async with self._lock:
            for url in urls:
                try:
                    normalized_url = normalize_url(url)
                    
                    if normalized_url in self.processed_urls or normalized_url in self.failed_urls:
                        continue
                    
                    # Skip if already queued
                    if normalized_url in self.url_priorities:
                        continue
                    
                    priority = self._calculate_priority(normalized_url)
                    self.url_priorities[normalized_url] = priority
                    heapq.heappush(self.url_queue, (priority, normalized_url))
                    
                except Exception as e:
                    logger.debug(f"Failed to add URL {url}: {e}")
    
    async def add_url(self, url: str, priority: int = 100) -> None:
        """Add a single URL with specified priority."""
        await self.add_urls([url])
    
    async def get_next_batch(self, batch_size: int = None) -> AsyncIterator[Tuple[str, int]]:
        """Get next batch of URLs to process."""
        if batch_size is None:
            batch_size = self.config["fetch"]["concurrency"]
        
        while True:
            batch = []
            
            async with self._lock:
                # Get up to batch_size URLs
                for _ in range(min(batch_size, len(self.url_queue))):
                    if not self.url_queue:
                        break
                    
                    priority, url = heapq.heappop(self.url_queue)
                    
                    # Skip if already processed
                    if url in self.processed_urls or url in self.failed_urls:
                        continue
                    
                    batch.append((url, priority))
                    self.processed_urls.add(url)
            
            if not batch:
                break
            
            for url, priority in batch:
                yield url, priority
    
    async def mark_failed(self, url: str) -> None:
        """Mark URL as failed."""
        async with self._lock:
            self.failed_urls.add(url)
            self.processed_urls.discard(url)
    
    async def mark_success(self, url: str) -> None:
        """Mark URL as successfully processed."""
        # URL is already in processed_urls from get_next_batch
        pass
    
    async def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        async with self._lock:
            return {
                "queued": len(self.url_queue),
                "processed": len(self.processed_urls),
                "failed": len(self.failed_urls),
                "total": len(self.url_queue) + len(self.processed_urls) + len(self.failed_urls),
            }
    
    def _calculate_priority(self, url: str) -> int:
        """Calculate priority for URL (lower number = higher priority)."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Higher priority (lower number) for important pages
        priority = 100  # Default priority
        
        # Root pages get highest priority
        if path == '/' or path == '':
            priority = 10
        
        # Documentation, guides, help pages
        elif any(term in path for term in ['doc', 'guide', 'help', 'tutorial', 'getting-started']):
            priority = 20
        
        # API documentation
        elif 'api' in path:
            priority = 30
        
        # Blog/news pages (usually less important for documentation)
        elif any(term in path for term in ['blog', 'news', 'press']):
            priority = 80
        
        # Asset/media pages (lowest priority)
        elif any(ext in path for ext in ['.css', '.js', '.png', '.jpg', '.pdf']):
            priority = 200
        
        # Adjust based on depth (deeper = lower priority)
        path_depth = path.count('/')
        if path_depth > 0:
            priority += min(path_depth * 5, 50)  # Cap depth penalty
        
        # Adjust based on query parameters (usually less important)
        if parsed.query:
            priority += 10
        
        return priority
    
    async def clear(self) -> None:
        """Clear all URLs from queue."""
        async with self._lock:
            self.url_queue.clear()
            self.processed_urls.clear()
            self.failed_urls.clear()
            self.url_priorities.clear()
    
    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        async with self._lock:
            return len(self.url_queue) == 0