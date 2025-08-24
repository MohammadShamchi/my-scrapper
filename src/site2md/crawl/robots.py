"""Robots.txt parsing and compliance checking."""

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from ..fetch.http_client import HTTPClient
from ..utils.exceptions import RobotsError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """Handles robots.txt parsing and URL checking."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.http_client = HTTPClient(config)
        self.robots_cache: Dict[str, Optional[RobotFileParser]] = {}
        self.user_agent = config["fetch"]["user_agent"]
        self.respect_robots = config["fetch"]["respect_robots"]

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.respect_robots:
            return True

        try:
            parsed_url = urlparse(url)
            domain_key = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Get robots.txt for this domain
            robots = await self._get_robots(domain_key)

            if robots is None:
                # No robots.txt found, allow crawling
                return True

            # Check if URL is allowed
            return robots.can_fetch(self.user_agent, url)

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # On error, be conservative and allow (unless strict mode)
            return not self.config.get("fetch", {}).get("strict_robots", False)

    async def get_crawl_delay(self, url: str) -> float:
        """Get crawl delay for URL from robots.txt."""
        if not self.respect_robots:
            return 0.0

        try:
            parsed_url = urlparse(url)
            domain_key = f"{parsed_url.scheme}://{parsed_url.netloc}"

            robots = await self._get_robots(domain_key)

            if robots is None:
                return 0.0

            # Get crawl delay for our user agent
            delay = robots.crawl_delay(self.user_agent)
            return float(delay) if delay else 0.0

        except Exception as e:
            logger.debug(f"Error getting crawl delay for {url}: {e}")
            return 0.0

    async def _get_robots(self, domain_key: str) -> Optional[RobotFileParser]:
        """Get robots.txt for domain, with caching."""
        if domain_key in self.robots_cache:
            return self.robots_cache[domain_key]

        try:
            robots_url = urljoin(domain_key, '/robots.txt')
            logger.debug(f"Fetching robots.txt: {robots_url}")

            async with self.http_client:
                response = await self.http_client.fetch(robots_url)

                if not response or response.get("status_code", 0) >= 400:
                    # No robots.txt found
                    self.robots_cache[domain_key] = None
                    return None

                content = response.get("content", "")
                if not content:
                    self.robots_cache[domain_key] = None
                    return None

                # Parse robots.txt content
                robots = RobotFileParser()
                robots.set_url(robots_url)
                robots.read(content.splitlines())
                self.robots_cache[domain_key] = robots

                logger.debug(f"Parsed robots.txt for {domain_key}")
                return robots

        except Exception as e:
            logger.warning(
                f"Failed to fetch/parse robots.txt for {domain_key}: {e}")
            # Cache the failure to avoid repeated attempts
            self.robots_cache[domain_key] = None
            return None
