# Site2MD - Website to Markdown Converter

![Site2MD Logo](https://img.shields.io/badge/Site2MD-Website%20to%20Markdown-blue?style=for-the-badge)

[![CI/CD Pipeline](https://github.com/yourusername/site2md/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/site2md/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade Python application that converts websites to high-quality Markdown files with real-time progress tracking. Features both CLI and web interfaces with support for JavaScript-heavy sites, authentication, and incremental crawling.

## ✨ Features

- 🚀 **Fast Async Crawling** - HTTP/2 support with concurrent processing
- 🌐 **JavaScript Support** - Optional Playwright rendering for dynamic content
- 🔐 **Authentication** - Cookie/header support + interactive browser login
- 📊 **Real-time Progress** - WebSocket-powered progress tracking
- 🔄 **Incremental Crawling** - Smart updates using ETags and content hashes
- 🤖 **Robots.txt Compliant** - Respects crawling guidelines
- 🎯 **High-Quality Output** - Advanced content extraction and formatting
- 🐳 **Production Ready** - Docker support with health checks
- ☁️ **Deploy Anywhere** - One-click deploys to Railway, Render, Heroku

## 🚀 Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template=https://github.com/yourusername/site2md)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/site2md)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/site2md)

## 🖥️ Web Interface

Simple, modern interface with collapsible advanced options:

- **URL Input** - Just paste any website URL
- **Advanced Options** - JavaScript rendering, custom delays, depth limits
- **Real-time Progress** - Watch crawling progress with live updates
- **Download Results** - Get ZIP file with all Markdown files

## 📦 Installation

### Using Docker (Recommended)

```bash
# Quick start
docker run -p 8000:8000 yourusername/site2md:latest

# With Docker Compose
git clone https://github.com/yourusername/site2md.git
cd site2md
docker-compose up
```

### Using pip

```bash
# Install from PyPI (coming soon)
pip install site2md

# Or install from source
git clone https://github.com/yourusername/site2md.git
cd site2md
pip install -e ".[web]"
```

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev,web]"

# Run tests
pytest

# Start web server
python -m site2md.web.main
```

## 🎯 Usage

### Web Interface

1. Start the server: `python -m site2md.web.main`
2. Open http://localhost:8000
3. Enter website URL and configure options
4. Watch real-time progress and download results

### Command Line

```bash
# Basic usage
site2md https://example.com

# With JavaScript rendering
site2md https://spa-site.com --javascript

# Custom authentication
site2md https://private-site.com --cookies cookies.json --headers headers.json

# Incremental crawling
site2md https://news-site.com --incremental

# Advanced options
site2md https://large-site.com \
    --max-depth 3 \
    --max-pages 100 \
    --delay 1.0 \
    --output ./export/
```

### Authentication Examples

**Cookies (JSON format):**
```json
{
  "domain.com": {
    "session_id": "abc123",
    "auth_token": "xyz789"
  }
}
```

**Headers (JSON format):**
```json
{
  "User-Agent": "Custom Bot 1.0",
  "Authorization": "Bearer token123",
  "X-API-Key": "secret-key"
}
```

## ⚙️ Configuration

### Environment Variables

- `PORT` - Web server port (default: 8000)
- `PYTHONUNBUFFERED` - Disable output buffering (recommended: 1)

### Advanced Options

- **Max Depth** - Control crawling depth (1-10)
- **Max Pages** - Limit total pages crawled
- **Request Delay** - Delay between requests (seconds)
- **JavaScript** - Enable browser rendering for SPAs
- **User Agent** - Custom user agent string
- **Output Format** - Markdown formatting options

## 🏗️ Architecture

```
src/site2md/
├── cli/           # Command line interface
├── crawl/         # Web crawling engine
├── process/       # Content processing
├── storage/       # File management
├── auth/          # Authentication handling
└── web/           # Web interface & API
```

### Key Components

- **Crawler Engine** - Async HTTP client with smart queuing
- **Content Extractor** - trafilatura + custom processing
- **Markdown Converter** - High-quality HTML to Markdown
- **Progress Tracker** - Real-time WebSocket updates
- **Authentication** - Cookie/header injection + Playwright
- **Storage Manager** - Organized output with manifests

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/site2md --cov-report=html

# Run specific test category
pytest tests/test_crawler.py -v

# Test web interface
pytest tests/test_web.py -v
```

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Supported Platforms

- **Railway** - Easy deployment with persistent storage
- **Render** - Auto-deploy from GitHub with SSL
- **Heroku** - Classic PaaS with extensive addons
- **Vercel** - Serverless functions for API endpoints
- **Docker** - Self-hosted on any platform

## 📊 Performance

### Benchmarks

- **Speed**: 50-100 pages/minute (depending on site complexity)
- **Memory**: ~50MB base + 2-5MB per concurrent request
- **Storage**: ~10KB per page (Markdown + metadata)
- **CPU**: Optimized async processing with connection pooling

### Optimization Tips

- Use `--max-pages` for large sites
- Enable `--javascript` only when necessary
- Adjust `--delay` based on server capacity
- Use incremental mode for regular updates

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev,web]"

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [trafilatura](https://github.com/adbar/trafilatura) - Content extraction
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Playwright](https://playwright.dev/) - Browser automation
- [httpx](https://www.python-httpx.org/) - Async HTTP client

## 📞 Support

- 📖 [Documentation](https://github.com/yourusername/site2md/wiki)
- 🐛 [Bug Reports](https://github.com/yourusername/site2md/issues)
- 💬 [Discussions](https://github.com/yourusername/site2md/discussions)
- 📧 Email: support@site2md.com

---

Made with ❤️ for the web scraping community