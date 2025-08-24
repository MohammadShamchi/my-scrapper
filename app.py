#!/usr/bin/env python3
"""
Simple FastAPI app for Site2MD web interface.
This file can run directly without package import issues.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Create FastAPI app
app = FastAPI(
    title="Site2MD Web UI",
    description="Web interface for Site2MD website crawler",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve a simple welcome page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Site2MD - Web Scraper</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Site2MD Web Interface</h1>
            <div class="status">
                <h2>✅ Deployment Successful!</h2>
                <p>Your Site2MD web scraper is now running on Heroku.</p>
                <p><strong>Status:</strong> Running</p>
                <p><strong>Version:</strong> 1.0.0</p>
            </div>
            <h3>Features:</h3>
            <ul>
                <li>Web scraping and crawling</li>
                <li>Markdown export</li>
                <li>FastAPI backend</li>
                <li>Heroku deployment</li>
            </ul>
            <p><em>This is a basic deployment. The full web interface will be available in future updates.</em></p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "site2md"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
