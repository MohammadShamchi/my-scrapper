"""CLI command implementations for Site2MD."""

import asyncio
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..crawl.crawler import Crawler
from ..fetch.playwright_client import PlaywrightClient
from ..utils.exceptions import Site2MDError
from ..utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def crawl_command(config: Dict[str, Any]) -> None:
    """Execute the crawl command with given configuration."""
    logger.info(f"Starting crawl of {config['start_urls'][0]}")
    
    # Initialize crawler
    crawler = Crawler(config)
    
    try:
        if config.get('dry_run', False):
            # Preview crawl plan
            urls = await crawler.preview_urls()
            console.print(f"\n[bold]Crawl Preview[/bold]")
            console.print(f"Starting URL: {config['start_urls'][0]}")
            console.print(f"Estimated pages: {len(urls)}")
            console.print(f"Output directory: {config['output']['directory']}")
            
            # Show first 10 URLs as example
            if urls:
                console.print("\n[bold]Sample URLs (first 10):[/bold]")
                for url in urls[:10]:
                    console.print(f"  • {url}")
                if len(urls) > 10:
                    console.print(f"  ... and {len(urls) - 10} more")
            return
        
        # Run actual crawl
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Crawling website...", total=None)
            
            stats = await crawler.crawl()
            
            progress.update(task, description="Crawl completed!")
        
        # Display results
        _display_crawl_stats(stats, config)
        
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        raise Site2MDError(f"Crawl failed: {e}") from e
    finally:
        await crawler.cleanup()


async def login_command(
    url: str, 
    context_dir: Path, 
    timeout: int, 
    headless: bool
) -> None:
    """Execute interactive login using Playwright."""
    logger.info(f"Starting interactive login for {url}")
    
    # Ensure Playwright is available
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise Site2MDError(
            "Playwright is required for interactive login. "
            "Install with: pip install site2md[playwright]"
        )
    
    context_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        try:
            # Create persistent context
            context = await browser.new_context(
                user_data_dir=str(context_dir),
                viewport={"width": 1280, "height": 720},
            )
            
            page = await context.new_page()
            
            console.print(f"\n[bold blue]Opening login page: {url}[/bold blue]")
            console.print("Please complete the login process in the browser window.")
            console.print("Press Ctrl+C when finished to save the session.\n")
            
            await page.goto(url)
            
            # Wait for user to complete login
            try:
                await asyncio.sleep(timeout)
                console.print("[yellow]Login timeout reached[/yellow]")
            except KeyboardInterrupt:
                console.print("\n[green]Saving authentication context...[/green]")
            
            await context.close()
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise Site2MDError(f"Login failed: {e}") from e
        finally:
            await browser.close()


def _display_crawl_stats(stats: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Display crawl statistics in a formatted table."""
    from rich.table import Table
    
    table = Table(title="Crawl Results", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", justify="right", style="green")
    
    # Add stats rows
    table.add_row("Pages Crawled", str(stats.get('pages_crawled', 0)))
    table.add_row("Pages Cached", str(stats.get('pages_cached', 0)))
    table.add_row("Pages Failed", str(stats.get('pages_failed', 0)))
    table.add_row("Assets Downloaded", str(stats.get('assets_downloaded', 0)))
    table.add_row("Total Size", _format_bytes(stats.get('total_bytes', 0)))
    table.add_row("Duration", _format_duration(stats.get('duration_seconds', 0)))
    
    console.print("\n")
    console.print(table)
    console.print(f"\n[bold]Output directory:[/bold] {config['output']['directory']}")


def _format_bytes(bytes_count: int) -> str:
    """Format byte count in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"


def _format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"