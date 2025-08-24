# Product Requirements Document (PRD)

## Universal Website → Markdown Exporter

### Version 1.0.0

### Date: August 2025

### Status: Draft

---

## 1. Executive Summary

### 1.1 Product Vision

Build a production-grade Python CLI application that enables users to export any website's content as high-quality Markdown files while respecting legal boundaries, supporting authentication, and optimizing for speed and accuracy.

### 1.2 Problem Statement

Organizations and individuals need to:

- Archive website content for offline access
- Migrate content between platforms
- Create documentation repositories from existing web resources
- Backup internal knowledge bases
- Convert web content to portable, version-controllable formats

Current solutions lack:

- Proper authentication handling without storing credentials
- High-fidelity content preservation
- Incremental update capabilities
- Legal compliance features
- Production-grade performance

### 1.3 Solution Overview

A Python 3.11+ CLI tool that:

- Crawls websites with configurable scope and depth
- Supports multiple authentication methods (cookies, headers, interactive login)
- Converts HTML to clean, structured Markdown
- Handles JavaScript-rendered content
- Respects robots.txt and rate limits
- Enables incremental updates
- Provides enterprise-grade logging and monitoring

---

## 2. Objectives & Success Metrics

### 2.1 Primary Objectives

1. **Accuracy**: 95%+ content fidelity in Markdown conversion
2. **Performance**: Process 1000+ pages/hour on standard hardware
3. **Compliance**: 100% robots.txt compliance by default
4. **Usability**: < 5 minute setup for basic usage
5. **Reliability**: < 0.1% failure rate with proper retry mechanisms

### 2.2 Key Performance Indicators (KPIs)

- Average pages processed per second
- Content extraction accuracy score
- Memory usage per 1000 pages
- Cache hit rate in incremental mode
- User authentication success rate
- Error recovery rate

### 2.3 Success Criteria

- Successfully export 10+ different website types (docs, blogs, wikis, forums)
- Support authentication for 5+ major platforms
- Handle sites with 10,000+ pages efficiently
- Maintain < 500MB memory footprint for typical usage
- Achieve 90%+ user satisfaction in usability testing

---

## 3. User Personas & Use Cases

### 3.1 Primary Personas

#### Technical Documentation Manager

- **Needs**: Archive product documentation, maintain offline copies
- **Pain Points**: Manual copy-paste, formatting inconsistencies
- **Success**: Complete documentation mirror with preserved structure

#### Content Migration Specialist

- **Needs**: Move content between CMS platforms
- **Pain Points**: Format conversion, authentication barriers
- **Success**: Automated migration with minimal manual cleanup

#### Compliance Officer

- **Needs**: Create auditable content archives
- **Pain Points**: Legal compliance, access controls
- **Success**: Compliant archival with full audit trail

#### Developer/DevOps Engineer

- **Needs**: Backup internal wikis, create portable documentation
- **Pain Points**: Authentication complexity, incremental updates
- **Success**: Automated, scheduled exports with version control

### 3.2 Core Use Cases

1. **Public Documentation Export**

   - User exports public technical documentation
   - No authentication required
   - Focus on speed and completeness

2. **Authenticated Internal Wiki Export**

   - User exports company internal wiki
   - Requires SSO/cookie authentication
   - Emphasis on security and compliance

3. **Personal Content Backup**

   - User backs up their own content from platforms
   - Interactive login flow
   - Legal compliance for personal use

4. **Incremental Documentation Sync**
   - User maintains up-to-date local mirror
   - Only fetches changed content
   - Scheduled/automated execution

---

## 4. Functional Requirements

### 4.1 Core Functionality

#### 4.1.1 Discovery & Crawling

- **Sitemap Processing**

  - Parse sitemap.xml with nested sitemap support
  - Honor lastmod timestamps
  - Support sitemap index files

- **Link Discovery**

  - BFS crawl from seed URLs
  - Configurable depth limits
  - Domain scope enforcement

- **URL Management**
  - Normalization (lowercase, resolve relatives, canonicalization)
  - Deduplication by URL and content hash
  - Fragment handling (#anchors)

#### 4.1.2 Authentication System

- **Cookie-based Auth**

  - Import Netscape/Mozilla format cookies
  - JSON cookie format support
  - Session persistence

- **Header-based Auth**

  - Custom header injection
  - Bearer token support
  - API key authentication

- **Interactive Login**
  - Playwright-based browser automation
  - Context persistence
  - Cookie/storage extraction

#### 4.1.3 Content Processing

- **Extraction**

  - Main content identification (trafilatura/readability)
  - Noise removal (ads, navigation, footers)
  - Structure preservation

- **Conversion**

  - HTML to Markdown transformation
  - Table formatting
  - Code block detection with language hints
  - Image handling

- **Enhancement**
  - YAML frontmatter generation
  - Internal link rewriting
  - Asset localization

#### 4.1.4 Performance Features

- **Concurrency Control**

  - Per-host connection limiting
  - Global concurrency cap
  - Request queuing

- **Caching**

  - HTTP cache with ETag/Last-Modified
  - Content hash deduplication
  - SQLite manifest database

- **Optimization**
  - HTTP/2 support
  - Connection pooling
  - Compression (gzip/brotli)

### 4.2 Non-Functional Requirements

#### 4.2.1 Performance

- Process 100 pages/minute minimum
- < 100ms per page parsing overhead
- < 500MB RAM for 10,000 page crawl
- Support 10+ concurrent connections

#### 4.2.2 Scalability

- Handle websites with 100,000+ pages
- Linear performance scaling with resources
- Resumable crawls after interruption

#### 4.2.3 Reliability

- Automatic retry with exponential backoff
- Graceful degradation on errors
- Transaction-safe state management
- Data corruption prevention

#### 4.2.4 Security

- No credential storage in plaintext
- Secure cookie handling
- XSS prevention in output
- Path traversal protection

#### 4.2.5 Usability

- Single command basic usage
- Progressive disclosure of features
- Helpful error messages
- Interactive setup wizard option

---

## 5. Technical Architecture

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────┐
│                   CLI Interface                  │
│                     (Typer)                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Command Orchestrator                │
│         (Config, Validation, Routing)            │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┬─────────────┐
        │                   │             │
┌───────▼──────┐  ┌─────────▼──────┐  ┌──▼──────┐
│   Crawler    │  │  Authenticator  │  │ Renderer│
│   Engine     │  │    Manager      │  │ Engine  │
└───────┬──────┘  └─────────┬──────┘  └──┬──────┘
        │                   │             │
┌───────▼──────────────────▼─────────────▼───────┐
│              Content Processor                  │
│     (Extraction, Conversion, Enhancement)       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Storage Manager                     │
│        (File System, SQLite, Cache)              │
└──────────────────────────────────────────────────┘
```

### 5.2 Component Design

#### 5.2.1 Crawler Engine

- URL frontier management
- Robot.txt compliance
- Rate limiting
- Concurrency control

#### 5.2.2 Authentication Manager

- Cookie jar management
- Header injection
- Browser context handling
- Token refresh logic

#### 5.2.3 Content Processor

- HTML parsing pipeline
- Content extraction algorithms
- Markdown generation
- Link rewriting engine

#### 5.2.4 Storage Manager

- File system operations
- Database transactions
- Cache invalidation
- Asset management

### 5.3 Data Models

```python
# Core entities
class Page:
    url: str
    normalized_url: str
    content_hash: str
    etag: Optional[str]
    last_modified: Optional[datetime]
    status_code: int
    file_path: str
    metadata: dict

class CrawlSession:
    id: str
    start_time: datetime
    config: dict
    stats: CrawlStats
    manifest: List[Page]

class AuthContext:
    type: AuthType
    cookies: Optional[dict]
    headers: Optional[dict]
    playwright_context: Optional[Path]
```

---

## 6. User Interface Specifications

### 6.1 Command Line Interface

```bash
# Main commands
site2md crawl [OPTIONS]
site2md login [OPTIONS]
site2md config [OPTIONS]
site2md validate [OPTIONS]

# Key options
--url URL                 Starting URL(s)
--out PATH               Output directory
--config PATH            Config file path
--max-pages INT          Maximum pages to crawl
--max-depth INT          Maximum crawl depth
--concurrency INT        Concurrent requests
--cookies PATH           Cookie file path
--headers PATH           Headers file path
--render                 Enable JS rendering
--incremental           Enable incremental mode
--dry-run               Preview without fetching
--verbose              Verbose output
--debug                Debug logging
```

### 6.2 Configuration File

```yaml
# config.yaml structure
version: '1.0'
crawl:
  start_urls: []
  scope: {}
  limits: {}

fetch:
  concurrency: 8
  timeout: 30
  user_agent: ''

auth:
  method: null
  config: {}

output:
  format: 'markdown'
  layout: 'mirror'
  assets: {}

processing:
  extractors: []
  filters: []
  enhancements: []
```

### 6.3 Output Structure

```
output_dir/
├── README.md              # Site overview
├── manifest.db           # SQLite database
├── assets/              # Downloaded assets
│   └── [hash].[ext]
└── [domain]/            # Content tree
    ├── index.md
    └── [path]/
        └── page.md
```

---

## 7. Implementation Roadmap

### 7.1 Development Phases

#### Phase 1: Foundation (Weeks 1-2)

- [ ] Project setup and dependencies
- [ ] Basic CLI structure
- [ ] URL normalization and management
- [ ] Simple HTML fetching

#### Phase 2: Core Crawling (Weeks 3-4)

- [ ] Sitemap parsing
- [ ] BFS crawler implementation
- [ ] Robots.txt compliance
- [ ] Concurrency control

#### Phase 3: Content Processing (Weeks 5-6)

- [ ] Content extraction pipeline
- [ ] HTML to Markdown conversion
- [ ] Link rewriting
- [ ] Asset handling

#### Phase 4: Authentication (Weeks 7-8)

- [ ] Cookie import
- [ ] Header management
- [ ] Playwright integration
- [ ] Session persistence

#### Phase 5: Optimization (Weeks 9-10)

- [ ] Incremental mode
- [ ] Caching layer
- [ ] Performance tuning
- [ ] Error recovery

#### Phase 6: Polish (Weeks 11-12)

- [ ] Documentation
- [ ] Testing suite
- [ ] CLI improvements
- [ ] Release preparation

### 7.2 Testing Strategy

#### Unit Tests

- URL normalization logic
- Content extraction algorithms
- Markdown conversion rules
- Authentication flows

#### Integration Tests

- End-to-end crawl scenarios
- Authentication workflows
- Incremental update logic
- Error recovery paths

#### Performance Tests

- Large site crawling
- Memory usage profiling
- Concurrency stress testing
- Cache effectiveness

#### Acceptance Tests

- Real website exports
- Authentication scenarios
- Output quality validation
- User workflow testing

---

## 8. Risk Assessment & Mitigation

### 8.1 Technical Risks

| Risk                             | Impact | Probability | Mitigation                           |
| -------------------------------- | ------ | ----------- | ------------------------------------ |
| Rate limiting by targets         | High   | High        | Adaptive delays, exponential backoff |
| Memory exhaustion on large sites | High   | Medium      | Streaming processing, pagination     |
| JavaScript rendering failures    | Medium | High        | Fallback to static extraction        |
| Authentication complexity        | High   | Medium      | Multiple auth methods, clear docs    |
| Content extraction inaccuracy    | Medium | Medium      | Multiple extractors, fallbacks       |

### 8.2 Legal Risks

| Risk                | Impact | Probability | Mitigation                                      |
| ------------------- | ------ | ----------- | ----------------------------------------------- |
| ToS violations      | High   | Medium      | Robots.txt compliance, user responsibility docs |
| Copyright concerns  | High   | Low         | Personal use emphasis, no redistribution        |
| Data privacy issues | High   | Low         | No credential storage, secure handling          |

### 8.3 Operational Risks

| Risk                  | Impact | Probability | Mitigation                          |
| --------------------- | ------ | ----------- | ----------------------------------- |
| User misconfiguration | Medium | High        | Validation, defaults, examples      |
| Incomplete exports    | Medium | Medium      | Resumable crawls, progress tracking |
| Platform changes      | Medium | Medium      | Modular design, quick updates       |

---

## 9. Dependencies & Constraints

### 9.1 Technical Dependencies

- Python 3.11+ (system requirement)
- Playwright (optional, for rendering)
- SQLite (included in Python)
- Network connectivity
- Sufficient disk space for exports

### 9.2 External Dependencies

- Target website availability
- robots.txt compliance
- Rate limit adherence
- Authentication token validity

### 9.3 Constraints

- Cannot bypass paywalls or DRM
- Must respect robots.txt by default
- No password storage
- Limited to publicly accessible content (with auth)

---

## 10. Documentation Requirements

### 10.1 User Documentation

- Installation guide
- Quick start tutorial
- Authentication setup guides
- Configuration reference
- Troubleshooting guide
- FAQ

### 10.2 Developer Documentation

- Architecture overview
- API reference
- Plugin development guide
- Contributing guidelines
- Testing guide

### 10.3 Legal Documentation

- Terms of use
- Disclaimer
- MIT License
- Third-party licenses

---

## 11. Support & Maintenance

### 11.1 Support Channels

- GitHub Issues (primary)
- Documentation site
- Community Discord/Slack
- Stack Overflow tag

### 11.2 Maintenance Plan

- Security updates: As needed
- Feature releases: Quarterly
- Bug fixes: Bi-weekly
- Documentation updates: Continuous

### 11.3 Deprecation Policy

- 6-month deprecation notices
- Migration guides provided
- Backward compatibility for 2 major versions

---

## 12. Appendices

### A. Glossary

- **BFS**: Breadth-First Search crawling strategy
- **ETag**: HTTP entity tag for caching
- **Registrable Domain**: Base domain for scope control
- **YAML Frontmatter**: Metadata header in Markdown files

### B. References

- [HTTP/2 Specification](https://http2.github.io/)
- [robots.txt Specification](https://www.robotstxt.org/)
- [CommonMark Specification](https://commonmark.org/)
- [Sitemap Protocol](https://www.sitemaps.org/)

### C. Competitive Analysis

- wget/curl: Lower-level, no Markdown conversion
- HTTrack: Full site mirror, no Markdown
- Scrapy: Framework, requires coding
- SingleFile: Browser extension, single pages only

---

## Approval & Sign-off

| Role           | Name | Date | Signature |
| -------------- | ---- | ---- | --------- |
| Product Owner  |      |      |           |
| Technical Lead |      |      |           |
| Legal Counsel  |      |      |           |
| QA Lead        |      |      |           |

---

_This PRD is a living document and will be updated as requirements evolve._
