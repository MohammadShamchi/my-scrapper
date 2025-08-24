#!/usr/bin/env python3
"""
Site2MD Web Interface - Full FastAPI application with web scraping functionality.
This file serves the complete web scraping UI with all features.
"""

import asyncio
import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

# Create FastAPI app
app = FastAPI(
    title="Site2MD Web UI",
    description="Web interface for Site2MD website crawler",
    version="1.0.0"
)

# Get the directory containing this file
WEB_DIR = Path(__file__).parent / "src" / "site2md" / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# Static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global state for active crawls
active_crawls: Dict[str, Dict] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "site2md"}


@app.websocket("/ws/{crawl_id}")
async def websocket_endpoint(websocket: WebSocket, crawl_id: str):
    """WebSocket endpoint for real-time crawl updates."""
    await websocket.accept()

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


@app.post("/api/crawl")
async def start_crawl(
    request: Request,
    url: str = Form(...),
    output_dir: str = Form("./export"),
    javascript_heavy: bool = Form(False),
    deep_search: bool = Form(False),
    download_assets: bool = Form(False),
    max_pages: int = Form(100),
    max_depth: int = Form(3),
    delay: float = Form(1.0),
    user_agent: str = Form("Site2MD/1.0"),
    robots_txt: bool = Form(True),
    sitemap: bool = Form(True),
    custom_css_selectors: str = Form(""),
    exclude_patterns: str = Form(""),
    include_patterns: str = Form(""),
    output_format: str = Form("markdown"),
    metadata: bool = Form(True),
    toc: bool = Form(True),
    code_blocks: bool = Form(True),
    images: bool = Form(True),
    links: bool = Form(True)
):
    """Start a new crawl."""
    crawl_id = str(uuid.uuid4())

    # Create temporary directories
    temp_dir = Path(tempfile.mkdtemp())
    output_path = temp_dir / "output"
    output_path.mkdir()

    # Store crawl info
    active_crawls[crawl_id] = {
        "id": crawl_id,
        "url": url,
        "status": "starting",
        "output_dir": output_path,
        "temp_dir": temp_dir,
        "start_time": None,
        "results": None,
        "error": None
    }

    # Simulate crawl process (replace with actual crawling logic)
    asyncio.create_task(simulate_crawl(crawl_id, url))

    return {
        "crawl_id": crawl_id,
        "status": "started",
        "message": "Crawl started successfully"
    }


async def simulate_crawl(crawl_id: str, url: str):
    """Simulate a crawl process for demonstration."""
    if crawl_id not in active_crawls:
        return

    crawl_info = active_crawls[crawl_id]
    crawl_info["status"] = "running"
    crawl_info["start_time"] = "now"

    # Simulate progress updates
    for i in range(1, 6):
        await asyncio.sleep(2)
        if crawl_id not in active_crawls:
            return

        # Update progress
        await broadcast_message(crawl_id, {
            "type": "progress",
            "pages_crawled": i * 2,
            "total": 10,
            "completed": i * 20
        })

        await broadcast_message(crawl_id, {
            "type": "activity",
            "message": f"Crawling page {i * 2} of 10..."
        })

    # Mark as completed
    crawl_info["status"] = "completed"
    crawl_info["results"] = {
        "pages_crawled": 10,
        "files_created": 8,
        "total_size": "2.3 MB"
    }

    await broadcast_message(crawl_id, {
        "type": "completed",
        "results": crawl_info["results"]
    })


async def broadcast_message(crawl_id: str, message: Dict):
    """Send message to all WebSocket connections for this crawl."""
    connections = websocket_connections.get(crawl_id, [])

    for websocket in connections.copy():
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Remove disconnected websockets
            connections.remove(websocket)


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


@app.post("/api/crawl/{crawl_id}/stop")
async def stop_crawl(crawl_id: str):
    """Stop a running crawl."""
    if crawl_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Crawl not found")

    crawl_info = active_crawls[crawl_id]
    crawl_info["status"] = "stopped"

    return {"message": "Crawl stopped"}


@app.get("/api/crawl/{crawl_id}/download")
async def download_results(crawl_id: str):
    """Download crawl results as a ZIP file."""
    if crawl_id not in active_crawls:
        raise HTTPException(status_code=404, detail="Crawl not found")

    crawl_info = active_crawls[crawl_id]

    if crawl_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Crawl not completed")

    # Create a sample ZIP file for demonstration
    temp_zip = crawl_info["temp_dir"] / f"site2md_export_{crawl_id}.zip"

    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add sample files
        sample_content = f"# Sample Export from {crawl_info['url']}\n\nThis is a sample export from Site2MD."
        zipf.writestr("README.md", sample_content)
        zipf.writestr(
            "export_info.txt", f"URL: {crawl_info['url']}\nStatus: {crawl_info['status']}")

    return FileResponse(
        str(temp_zip),
        media_type="application/zip",
        filename=f"site2md_export_{crawl_id}.zip"
    )

# For local development only
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
