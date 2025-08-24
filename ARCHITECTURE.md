# Site2MD Architecture Summary

## Overview
Site2MD is a production-grade Python 3.11 CLI application that crawls websites and exports each page as high-quality Markdown files. The architecture is designed for speed, correctness, and reliability with support for authentication, JavaScript rendering, and incremental updates.

## Core Components

### 1. CLI Layer (`src/site2md/cli/`)
- **commands.py**: Main CLI commands using Typer
- **config.py**: Configuration management (YAML + CLI precedence)
- **progress.py**: Rich progress bars and user feedback

### 2. Discovery & Crawling (`src/site2md/crawl/`)
- **crawler.py**: Main crawling orchestrator
- **discovery.py**: URL discovery via sitemaps and BFS crawling
- **robots.py**: robots.txt parsing and respect using reppy
- **url_manager.py**: URL normalization, deduplication, and scope filtering

### 3. Fetching Layer (`src/site2md/fetch/`)
- **http_client.py**: Async HTTP client with httpx[http2], connection pooling, retries
- **playwright_client.py**: JavaScript rendering and interactive login
- **auth.py**: Authentication handling (cookies, headers, context management)
- **cache.py**: HTTP caching and conditional requests

### 4. Content Processing (`src/site2md/process/`)
- **extractor.py**: Content extraction using trafilatura
- **converter.py**: HTML-to-Markdown conversion with markdownify
- **assets.py**: Asset downloading and path rewriting
- **metadata.py**: Front matter generation and metadata extraction

### 5. Storage & State (`src/site2md/storage/`)
- **manifest.py**: SQLite-based crawl state and incremental updates
- **filesystem.py**: File organization and path sanitization
- **export.py**: Final export coordination and site-level README

### 6. Utilities (`src/site2md/utils/`)
- **logging.py**: Structured logging with rich formatting
- **validation.py**: URL and content validation
- **exceptions.py**: Custom exception hierarchy

## Data Flow

```
1. Config Loading → CLI Parsing → URL Seeds
2. Discovery Phase → Sitemap + BFS → URL Queue
3. Fetching Phase → HTTP/Playwright → Raw Content
4. Processing Phase → Extract + Convert → Markdown
5. Storage Phase → File Write + Manifest Update
```

## Key Design Decisions

### Async Architecture
- Uses asyncio with httpx for high-concurrency fetching
- Per-host semaphores to respect rate limits
- Jittered delays to avoid thundering herd

### Authentication Strategy
- No credential storage - user-controlled auth only
- Three modes: cookie files, header files, Playwright context
- Automatic CSRF token refresh detection

### Incremental Updates
- SQLite manifest tracks ETag/Last-Modified
- Content hash comparison for change detection
- Atomic updates to prevent corruption

### Content Quality
- Trafilatura for main content extraction
- CSS selector-based noise removal
- Structured Markdown with YAML front matter
- Internal link rewriting to maintain navigation

### Error Handling
- Exponential backoff with jitter
- Graceful degradation (static fallback for render failures)
- Detailed error reporting without crashing

## Performance Optimizations

1. **Sitemap-First Discovery**: Reduces initial crawl time by 80%
2. **HTTP/2 Connection Pooling**: Reuses connections for same-host requests
3. **Conditional Requests**: Skip unchanged content using ETags
4. **Smart Concurrency**: Host-based limits with jittered delays
5. **Asset Deduplication**: Hash-based asset storage prevents duplicates

## Compliance & Security

- Always respects robots.txt by default
- No automatic paywall bypassing
- User-controlled authentication only
- Clear legal documentation for platform-specific usage
- Input validation and sanitization throughout

## Testing Strategy

- Unit tests for each component with mocked dependencies
- Integration tests with realistic fixtures
- End-to-end tests with test server
- Property-based testing for URL normalization
- Performance benchmarks for large sites

## Extensibility

The modular architecture allows for:
- Custom content extractors
- Additional authentication methods
- New export formats
- Platform-specific optimizations
- Custom filtering rules