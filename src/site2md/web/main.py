"""FastAPI web server for Site2MD UI."""

import asyncio
import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from ..cli.config import load_config
from ..crawl.crawler import Crawler
from ..utils.exceptions import Site2MDError
from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

# Get the directory containing this file
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# FastAPI app
app = FastAPI(
    title="Site2MD Web UI",
    description="Web interface for Site2MD website crawler",
    version="1.0.0"
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global state for active crawls
active_crawls: Dict[str, Dict] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}


class CrawlProgressTracker:
    """Tracks crawl progress and sends updates via WebSocket."""
    
    def __init__(self, crawl_id: str):
        self.crawl_id = crawl_id
        self.stats = {
            "pages_crawled": 0,
            "pages_cached": 0,
            "pages_failed": 0,
            "assets_downloaded": 0,
            "total_bytes": 0,
            "total": 1,
            "completed": 0,
        }
    
    async def update_progress(self, **kwargs):
        """Update progress stats and notify WebSocket connections."""
        self.stats.update(kwargs)
        
        message = {
            "type": "progress",
            **self.stats
        }
        
        await self.broadcast_message(message)
    
    async def update_activity(self, message: str):
        """Update current activity and notify connections."""
        await self.broadcast_message({
            "type": "activity",
            "message": message
        })
    
    async def broadcast_completed(self, results: Dict):
        """Broadcast crawl completion."""
        await self.broadcast_message({
            "type": "completed",
            **results
        })
    
    async def broadcast_error(self, error_message: str):
        """Broadcast crawl error."""
        await self.broadcast_message({
            "type": "error",
            "message": error_message
        })
    
    async def broadcast_message(self, message: Dict):
        """Send message to all WebSocket connections for this crawl."""
        connections = websocket_connections.get(self.crawl_id, [])
        
        for websocket in connections.copy():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                # Remove disconnected websockets
                connections.remove(websocket)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/crawl")
async def start_crawl(
    request: Request,
    url: str = Form(...),
    output_dir: str = Form("./export"),
    javascript_heavy: bool = Form(False),
    deep_search: bool = Form(False),
    download_assets: bool = Form(False),
    max_pages: int = Form(1000),
    max_depth: int = Form(5),
    concurrency: int = Form(8),
    delay: float = Form(0),
    respect_robots: bool = Form(True),
    sitemap_first: bool = Form(True),
    add_toc: bool = Form(True),
    incremental: bool = Form(False),
    include_patterns: str = Form("[]"),
    exclude_patterns: str = Form("[]"),
    cookies_file: Optional[UploadFile] = File(None),
    headers_file: Optional[UploadFile] = File(None),
    dry_run: bool = Form(False)
):
    """Start a crawl job."""
    try:
        # Generate unique crawl ID
        crawl_id = str(uuid.uuid4())
        
        # Parse patterns
        include_list = json.loads(include_patterns) if include_patterns != "[]" else []
        exclude_list = json.loads(exclude_patterns) if exclude_patterns != "[]" else []
        
        # Create temporary directory for this crawl
        temp_dir = Path(tempfile.mkdtemp(prefix=f"site2md_{crawl_id}_"))
        actual_output_dir = temp_dir / "export"
        
        # Handle file uploads
        cookies_path = None
        headers_path = None
        
        if cookies_file and cookies_file.filename:
            cookies_path = temp_dir / cookies_file.filename
            with open(cookies_path, 'wb') as f:
                content = await cookies_file.read()
                f.write(content)
        
        if headers_file and headers_file.filename:
            headers_path = temp_dir / headers_file.filename
            with open(headers_path, 'wb') as f:
                content = await headers_file.read()
                f.write(content)
        
        # Build configuration
        config = load_config(
            url=url,
            out=actual_output_dir,
            render=javascript_heavy,
            allow_subdomains=deep_search,
            download_assets=download_assets,
            max_pages=max_pages,
            max_depth=max_depth,
            concurrency=concurrency,
            delay_seconds=delay,
            respect_robots=respect_robots,
            sitemap_first=sitemap_first,
            incremental=incremental,
            include=include_list,
            exclude=exclude_list,
            cookies=str(cookies_path) if cookies_path else None,
            headers=str(headers_path) if headers_path else None,
            dry_run=dry_run
        )
        
        # Override some config for web UI
        config["markdown"]["add_toc"] = add_toc
        
        # Store crawl info
        active_crawls[crawl_id] = {
            "config": config,
            "temp_dir": temp_dir,
            "output_dir": actual_output_dir,
            "status": "starting",
            "task": None
        }
        
        if dry_run:
            # Handle dry run
            crawler = Crawler(config)
            try:
                urls = await crawler.preview_urls()
                return {
                    "crawl_id": crawl_id,
                    "dry_run": True,
                    "start_url": url,
                    "estimated_pages": len(urls),
                    "sample_urls": urls[:20],  # First 20 for preview
                    "output_directory": str(actual_output_dir)
                }
            except Exception as e:
                logger.error(f"Dry run failed: {e}")
                raise HTTPException(status_code=400, detail=f"Dry run failed: {str(e)}")
            finally:
                await crawler.cleanup()
        
        else:
            # Start actual crawl in background
            task = asyncio.create_task(run_crawl(crawl_id))
            active_crawls[crawl_id]["task"] = task
            
            return {
                "crawl_id": crawl_id,
                "status": "started",
                "message": "Crawl started successfully"
            }
    
    except Exception as e:
        logger.error(f"Failed to start crawl: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def run_crawl(crawl_id: str):
    """Run the actual crawl in background."""
    crawl_info = active_crawls[crawl_id]
    progress_tracker = CrawlProgressTracker(crawl_id)
    
    try:
        await progress_tracker.update_activity("Initializing crawler...")
        
        crawler = Crawler(crawl_info["config"])
        
        # Update status
        active_crawls[crawl_id]["status"] = "running"
        
        # Run crawl with progress tracking
        async with crawler:
            await progress_tracker.update_activity("Discovering URLs...")
            
            # Mock progress updates for demo (in real implementation, 
            # you'd integrate with the actual crawler progress)
            stats = await crawler.crawl()
            
            # Update final progress
            await progress_tracker.update_progress(
                pages_crawled=stats.get("pages_crawled", 0),
                pages_cached=stats.get("pages_cached", 0),
                pages_failed=stats.get("pages_failed", 0),
                total_bytes=stats.get("total_bytes", 0),
                completed=stats.get("pages_crawled", 0),
                total=stats.get("pages_crawled", 0)
            )
        
        # Mark as completed
        active_crawls[crawl_id]["status"] = "completed"
        active_crawls[crawl_id]["results"] = stats
        
        await progress_tracker.broadcast_completed({
            "pages_crawled": stats.get("pages_crawled", 0),
            "pages_cached": stats.get("pages_cached", 0),
            "pages_failed": stats.get("pages_failed", 0),
            "total_bytes": stats.get("total_bytes", 0),
            "duration": f"{stats.get('duration_seconds', 0):.1f} seconds",
            "output_directory": str(crawl_info["output_dir"])
        })
        
        logger.info(f"Crawl {crawl_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Crawl {crawl_id} failed: {e}")
        active_crawls[crawl_id]["status"] = "failed"
        active_crawls[crawl_id]["error"] = str(e)
        
        await progress_tracker.broadcast_error(str(e))


@app.websocket("/ws/{crawl_id}")
async def websocket_endpoint(websocket: WebSocket, crawl_id: str):
    """WebSocket endpoint for real-time crawl updates."""
    await websocket.accept()
    
    # Add to connections
    if crawl_id not in websocket_connections:
        websocket_connections[crawl_id] = []
    websocket_connections[crawl_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Remove from connections
        if crawl_id in websocket_connections:
            websocket_connections[crawl_id].remove(websocket)


@app.post("/api/crawl/{crawl_id}/stop")
async def stop_crawl(crawl_id: str):
    """Stop a running crawl."""
    if crawl_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    crawl_info = active_crawls[crawl_id]
    task = crawl_info.get("task")
    
    if task and not task.done():
        task.cancel()
        active_crawls[crawl_id]["status"] = "stopped"
        return {"message": "Crawl stopped"}
    
    return {"message": "Crawl was not running"}


@app.get("/api/crawl/{crawl_id}/download")
async def download_results(crawl_id: str):
    """Download crawl results as a ZIP file."""
    if crawl_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    crawl_info = active_crawls[crawl_id]
    
    if crawl_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Crawl not completed")
    
    output_dir = crawl_info["output_dir"]
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
    
    # Create ZIP file
    temp_zip = crawl_info["temp_dir"] / f"site2md_export_{crawl_id}.zip"
    
    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in output_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(output_dir)
                zipf.write(file_path, arcname)
    
    return FileResponse(
        str(temp_zip),
        media_type="application/zip",
        filename=f"site2md_export_{crawl_id}.zip"
    )


@app.get("/api/crawl/{crawl_id}/status")
async def get_crawl_status(crawl_id: str):
    """Get crawl status."""
    if crawl_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    crawl_info = active_crawls[crawl_id]
    
    return {
        "crawl_id": crawl_id,
        "status": crawl_info["status"],
        "results": crawl_info.get("results"),
        "error": crawl_info.get("error")
    }


def main():
    """Main entry point for web server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Site2MD Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.debug, debug=args.debug)
    
    logger.info(f"Starting Site2MD Web UI at http://{args.host}:{args.port}")
    
    # Run server
    uvicorn.run(
        "site2md.web.main:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info"
    )


if __name__ == "__main__":
    main()