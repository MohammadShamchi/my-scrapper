"""Main CLI interface for Site2MD."""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..utils.exceptions import Site2MDError
from ..utils.logging import setup_logging
from .commands import crawl_command, login_command
from .config import load_config

app = typer.Typer(
    name="site2md",
    help="Universal Website → Markdown Exporter",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


@app.command()
def crawl(
    url: str = typer.Argument(help="Starting URL to crawl"),
    out: Path = typer.Option(
        "./export", "--out", "-o", help="Output directory for exported files"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Configuration file path"
    ),
    max_pages: Optional[int] = typer.Option(
        None, "--max-pages", help="Maximum number of pages to crawl"
    ),
    max_depth: Optional[int] = typer.Option(
        None, "--max-depth", help="Maximum crawl depth"
    ),
    concurrency: Optional[int] = typer.Option(
        None, "--concurrency", help="Number of concurrent requests"
    ),
    cookies: Optional[Path] = typer.Option(
        None, "--cookies", help="Path to cookies file (Netscape/JSON format)"
    ),
    headers: Optional[Path] = typer.Option(
        None, "--headers", help="Path to headers JSON file"
    ),
    playwright_context: Optional[Path] = typer.Option(
        None, "--playwright-context", help="Path to Playwright context directory"
    ),
    render: bool = typer.Option(
        False, "--render", help="Use Playwright to render JavaScript"
    ),
    download_assets: bool = typer.Option(
        False, "--download-assets", help="Download and save page assets"
    ),
    allow_subdomains: bool = typer.Option(
        False, "--allow-subdomains", help="Allow crawling subdomains"
    ),
    sitemap_first: bool = typer.Option(
        True, "--sitemap-first/--no-sitemap-first", help="Prioritize sitemap discovery"
    ),
    respect_robots: bool = typer.Option(
        True, "--respect-robots/--no-respect-robots", help="Respect robots.txt"
    ),
    incremental: bool = typer.Option(
        False, "--incremental", help="Skip unchanged pages"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview crawl plan without fetching"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug logging"
    ),
    include: List[str] = typer.Option(
        [], "--include", help="Include URL patterns (regex)"
    ),
    exclude: List[str] = typer.Option(
        [], "--exclude", help="Exclude URL patterns (regex)"
    ),
):
    """Crawl a website and export pages as Markdown files."""
    try:
        # Setup logging
        setup_logging(verbose=verbose, debug=debug)
        
        # Load configuration
        cfg = load_config(
            config_file=config,
            url=url,
            out=out,
            max_pages=max_pages,
            max_depth=max_depth,
            concurrency=concurrency,
            cookies=cookies,
            headers=headers,
            playwright_context=playwright_context,
            render=render,
            download_assets=download_assets,
            allow_subdomains=allow_subdomains,
            sitemap_first=sitemap_first,
            respect_robots=respect_robots,
            incremental=incremental,
            dry_run=dry_run,
            include=include,
            exclude=exclude,
        )
        
        # Run crawl command
        asyncio.run(crawl_command(cfg))
        
    except Site2MDError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Crawl interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def login(
    url: str = typer.Argument(help="Login URL to open"),
    ctx: Path = typer.Option(
        "./.auth", "--ctx", help="Directory to save authentication context"
    ),
    timeout: int = typer.Option(
        300, "--timeout", help="Login timeout in seconds"
    ),
    headless: bool = typer.Option(
        False, "--headless", help="Run browser in headless mode"
    ),
):
    """Interactive login using Playwright browser."""
    try:
        setup_logging(verbose=False, debug=False)
        asyncio.run(login_command(url, ctx, timeout, headless))
        console.print(f"[green]Authentication context saved to {ctx}[/green]")
    except Site2MDError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Login cancelled by user[/yellow]")
        raise typer.Exit(130)


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode")
):
    """Launch the web UI for Site2MD."""
    try:
        from ..web.main import main as web_main
        import sys
        
        # Override sys.argv for the web server
        sys.argv = ["site2md-web", "--host", host, "--port", str(port)]
        if debug:
            sys.argv.append("--debug")
        
        console.print(f"[green]Starting Site2MD Web UI at http://{host}:{port}[/green]")
        console.print("Press Ctrl+C to stop the server")
        
        web_main()
        
    except ImportError:
        console.print("[red]Web dependencies not installed. Install with:[/red]")
        console.print("pip install site2md[web]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Web server stopped[/yellow]")
        raise typer.Exit(0)


@app.command()
def version():
    """Show version information."""
    from .. import __version__, __author__
    
    table = Table(show_header=False, box=None)
    table.add_column(style="bold cyan")
    table.add_column()
    
    table.add_row("Site2MD", f"v{__version__}")
    table.add_row("Author", __author__)
    table.add_row("Python", "3.11+")
    
    console.print(table)


if __name__ == "__main__":
    app()