"""Playwright client for JavaScript rendering and interactive login."""

from typing import Any, Dict, Optional

from ..utils.exceptions import RenderError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PlaywrightClient:
    """Playwright client for JavaScript rendering."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        """Initialize Playwright browser."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RenderError(
                "Playwright is required for rendering. "
                "Install with: pip install site2md[playwright]"
            )
        
        self.playwright = async_playwright()
        await self.playwright.__aenter__()
        
        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create context
        context_dir = self.config.get("auth", {}).get("playwright_context_dir")
        if context_dir:
            self.context = await self.browser.new_context(
                user_data_dir=str(context_dir),
                viewport={"width": 1280, "height": 720},
            )
        else:
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up Playwright resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch_rendered(self, url: str) -> Dict[str, Any]:
        """Fetch URL with JavaScript rendering."""
        if not self.context:
            raise RenderError("Playwright context not initialized")
        
        try:
            page = await self.context.new_page()
            
            # Set up page
            await page.set_extra_http_headers({
                "User-Agent": self.config["fetch"]["user_agent"]
            })
            
            # Navigate to page
            response = await page.goto(
                url, 
                wait_until=self.config["render"].get("wait_for", "networkidle"),
                timeout=self.config["render"].get("timeout", 15000)
            )
            
            if not response:
                raise RenderError(f"No response received for {url}")
            
            # Wait for page to be ready
            await page.wait_for_load_state("networkidle")
            
            # Get content
            content = await page.content()
            
            # Clean up
            await page.close()
            
            return {
                "status_code": response.status,
                "content": content,
                "headers": response.headers,
                "url": response.url,
                "content_type": response.headers.get("content-type", ""),
            }
            
        except Exception as e:
            logger.error(f"Playwright rendering failed for {url}: {e}")
            raise RenderError(f"Failed to render {url}: {e}") from e