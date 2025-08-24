"""Pytest configuration and shared fixtures."""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import httpx
from httpx_mock import HTTPXMock

from site2md.cli.config import DEFAULT_CONFIG


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = DEFAULT_CONFIG.copy()
    config["start_urls"] = ["https://example.com"]
    config["output"]["directory"] = temp_dir / "export"
    config["limits"]["max_pages"] = 10
    config["fetch"]["concurrency"] = 2
    return config


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="This is a sample page description.">
        <title>Sample Page Title</title>
        <link rel="canonical" href="https://example.com/sample">
    </head>
    <body>
        <nav>
            <a href="/home">Home</a>
            <a href="/about">About</a>
        </nav>
        
        <main>
            <h1>Main Heading</h1>
            <p>This is the main content of the page.</p>
            
            <h2>Subheading</h2>
            <p>More content here with <strong>bold text</strong> and <em>italic text</em>.</p>
            
            <ul>
                <li>First item</li>
                <li>Second item</li>
                <li>Third item</li>
            </ul>
            
            <table>
                <thead>
                    <tr>
                        <th>Column 1</th>
                        <th>Column 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Data 1</td>
                        <td>Data 2</td>
                    </tr>
                </tbody>
            </table>
            
            <pre><code class="language-python">
def hello_world():
    print("Hello, world!")
            </code></pre>
        </main>
        
        <footer>
            <p>Footer content</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_sitemap():
    """Sample sitemap XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
            <lastmod>2023-01-01</lastmod>
            <priority>1.0</priority>
        </url>
        <url>
            <loc>https://example.com/about</loc>
            <lastmod>2023-01-02</lastmod>
            <priority>0.8</priority>
        </url>
        <url>
            <loc>https://example.com/contact</loc>
            <lastmod>2023-01-03</lastmod>
            <priority>0.6</priority>
        </url>
    </urlset>"""


@pytest.fixture
def sample_robots_txt():
    """Sample robots.txt for testing."""
    return """User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
Crawl-delay: 1"""


@pytest.fixture
def mock_cookies_file(temp_dir):
    """Create a mock cookies file."""
    cookies_data = {
        "session_id": "abc123",
        "csrf_token": "xyz789",
        "user_pref": "dark_mode"
    }
    
    cookies_file = temp_dir / "cookies.json"
    with open(cookies_file, 'w') as f:
        json.dump(cookies_data, f)
    
    return cookies_file


@pytest.fixture
def mock_headers_file(temp_dir):
    """Create a mock headers file."""
    headers_data = {
        "Authorization": "Bearer fake-token",
        "X-API-Key": "fake-api-key"
    }
    
    headers_file = temp_dir / "headers.json"
    with open(headers_file, 'w') as f:
        json.dump(headers_data, f)
    
    return headers_file


@pytest.fixture
def httpx_mock():
    """HTTP mock for testing."""
    with HTTPXMock() as mock:
        yield mock


@pytest.fixture
def mock_successful_response(sample_html):
    """Create a mock successful HTTP response."""
    return {
        "status_code": 200,
        "content": sample_html,
        "headers": {
            "content-type": "text/html; charset=utf-8",
            "etag": '"abc123"',
            "last-modified": "Wed, 01 Jan 2023 00:00:00 GMT"
        },
        "url": "https://example.com/",
    }


class MockCrawlResponse:
    """Mock response for crawl testing."""
    
    def __init__(self, url: str, status_code: int = 200, content: str = ""):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": "text/html"}


@pytest.fixture
def mock_responses():
    """Factory for creating mock responses."""
    def _create_response(url: str, status_code: int = 200, content: str = None):
        if content is None:
            content = f"<html><body><h1>Page: {url}</h1></body></html>"
        return MockCrawlResponse(url, status_code, content)
    
    return _create_response