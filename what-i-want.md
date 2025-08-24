Master Prompt: “Universal Website → Markdown Exporter (Auth, Fast, High-Quality)”

Role: You are a senior software engineer. Build a production‑grade Python 3.11 CLI app that crawls any website (respecting ToS/robots) and exports each page as high‑quality .md. It must support user‑provided auth (cookies/headers) and an interactive login flow (via Playwright) so the user can log in themselves before scraping. Optimize for speed, correctness, and re‑runs.

Deliverables (in this order): 1. Architecture summary 2. pyproject.toml (pinned deps) 3. src/ code (modular) 4. tests/ with realistic fixtures 5. README.md (setup, auth flows, examples, limitations) 6. config.example.yaml 7. LICENSE (MIT)

⸻

Core Capabilities

CLI

python -m site2md crawl --url https://example.com --out ./export --config ./config.yaml
Use typer for subcommands and options; config via YAML (CLI > config precedence).

Scope & Discovery
• Limit to same registrable domain by default (tldextract), with --allow-subdomains and fine‑grained --include/--exclude regex.
• Sources: sitemap.xml (with nested sitemaps) + BFS crawl from seeds.
• Dedup by normalized canonical URL + content hash; skip hash‑only fragments.
• Max controls: --max-pages, --max-depth, --concurrency, --timeout.

Fetching (Fast & Polite)
• httpx[http2] (async), connection pooling, gzip/brotli, retries w/ exponential backoff.
• Respect robots.txt (via reppy), Crawl-delay if present; default polite delay 1–2s unless overridden.
• Conditional requests with ETag / Last-Modified (incremental mode).
• Per‑host concurrency & jitter to reduce throttling; exponential backoff on 429/5xx.
• Optional proxy support and custom --user-agent.

Auth (User-controlled; no password storage)
• Mode A: Cookie file import — --cookies path/to/cookies.txt (Netscape/Mozilla format) or JSON export.
• Mode B: Headers file — --headers path/to/headers.json (e.g., {"Authorization": "Bearer …"})
• Mode C: Interactive Login (Playwright) — site2md login --url https://target.com/login --ctx ./auth opens a persistent Chromium profile so the user signs in. We save cookies + local/sessionStorage to ./auth.
• Then crawl reuses that context (--playwright-context ./auth) or exports cookies to httpx.
• Auto‑refresh CSRF tokens when detected (form meta or cookie).
• Never hardcode credentials; only use what the user supplies.

Rendering (JS-heavy pages)
• Default: HTML fetch via httpx.
• --render flag: use Playwright to snapshot the DOM post‑login/post‑render.
• Wait strategy: networkidle + selector heuristics; --render-timeout.
• Fall back to static fetch if rendering fails.

Content Extraction (High Quality)
• Use trafilatura (preferred) or readability-lxml to get main content.
• Preserve headings hierarchy, paragraphs, lists, tables, code blocks (language aware).
• Strip nav/footers/ads/cookie banners/newsletter modals via CSS selectors + heuristics.
• Keep internal anchor text; rewrite internal links to exported .md paths.
• Titles: <title> then first <h1>; description: <meta name="description">.
• Handle canonical tags, locales (/en/, /fr/), and hreflang.

Markdown Conversion
• High‑fidelity HTML→MD via tuned markdownify (or a robust custom converter):
• Headings #..######, fenced code blocks ```lang, tables as Markdown (fallback to HTML if too complex).
• Images: rewrite to local paths if assets downloaded.
• Prepend YAML front matter to every file:

---

source_url: <final-or-canonical>
title: <page title>
fetched_at: <ISO8601>
description: <meta description or first paragraph>
tags: []

---

    •	Optional per‑page ToC; configurable.

Assets
• --download-assets to fetch images (skip tiny/tracking). Store under /assets/<hash>.<ext>.
• Update Markdown image refs accordingly.
• Skip PDFs by default; --include-pdf-links to keep as links, --fetch-pdf to download.

Output Layout
• Mirror URL paths under --out:
https://docs.example.com/guides/setup → ./export/docs.example.com/guides/setup.md
• / becomes index.md.
• Generate a site‑level README.md with a tree of exported pages and counts.

Incremental & Caching
• SQLite manifest with URL, normalized URL, ETag/Last‑Modified, content hash, last fetch, status, and file path.
• Skip unchanged pages; add --force to bypass.
• Optional on‑disk HTTP cache.

Logging & DX
• rich progress bars; crawl stats summary (fetched, cached, skipped, errors).
• --dry-run previews URL plan without fetching.
• Verbose/debug modes with structured logs (JSON).

Security & Compliance
• Always respect robots.txt by default; allow --respect-robots=false only if the user explicitly chooses (document risks).
• Do not bypass paywalls or technical protection.
• LinkedIn/similar: scraping may violate ToS. Prefer their official data export. If the user provides cookies/login for their own account, support it technically but document legal considerations.

Edge Cases
• Canonical vs duplicate paths; prefer canonical target.
• Querystrings that control content; configurable keep/drop strategy.
• Hash‑only links: map to the same file + anchor (don’t create new files).
• Sitemap <lastmod> ordering; prioritize fresh pages.
• 3xx stabilization (avoid infinite redirect loops).
• Non‑HTML (JSON, XML, binary): skip or save as references depending on flags.

⸻

Tech Stack (Pin versions)
• typer, rich
• httpx[http2], anyio
• playwright (optional install behind extra)
• beautifulsoup4, lxml
• trafilatura (or readability-lxml)
• markdownify (custom config)
• tldextract, urllib3
• reppy (robots)
• sqlite3 stdlib manifest
• Optional: brotli, cchardet for speed

⸻

Implementation Must‑Haves
• URL normalization: lowercase host, strip fragments, resolve relatives, normalize trailing slashes, preserve meaningful query params (configurable allowlist/denylist).
• Internal/external detection via registrable domain.
• Link rewriting: internal → relative .md path (mirror tree). External → absolute URL.
• Filenames: sanitize; use -index.md for path collisions; dedupe long names.
• Code blocks: detect <pre><code class="language-xyz"> and emit fenced blocks with language.
• Tables: robust conversion; fallback to inline HTML when spanning/rowspan complex.
• Locale awareness: unify /en/ vs /en-US/ when canonical says so.
• Concurrency controls with per‑host semaphores; random jitter to avoid burstiness.

⸻

CLI Examples (document these)
• Static docs crawl (fastest):
site2md crawl --url https://docs.example.com --out ./export --sitemap-first true --max-depth 3 --concurrency 8 --download-assets
• Auth via cookie file (you log in in your browser, then export cookies):
site2md crawl --url https://intranet.example.com --cookies ./cookies.txt --out ./export --respect-robots true
• Interactive login with Playwright (you sign in, we reuse the session):

site2md login --url https://www.linkedin.com/login --ctx ./.auth/linkedin
site2md crawl --url https://www.linkedin.com/in/your-handle/ --playwright-context ./.auth/linkedin --render --max-pages 50

    •	Incremental re‑run:

site2md crawl --url https://docs.example.com --out ./export --max-pages 1000 --concurrency 6 --incremental

⸻

Tests (focus)
• URL normalization & mapping → filesystem paths
• Robots parsing & allow/deny
• Sitemap parsing (nested, index sitemaps)
• HTML→MD on tricky inputs (nested lists, complex tables, code blocks with language, figures/captions)
• Link rewriting (internal anchors, relative paths, locale switches)
• Incremental logic (ETag/Last‑Modified + hash)
• Playwright login context save/restore & cookie export to httpx

⸻

Config (config.example.yaml)

start_urls:

- https://example.com
  scope:
  allow_subdomains: false
  include: []
  exclude: []
  limits:
  max_pages: 1000
  max_depth: 5
  fetch:
  concurrency: 8
  timeout: 20
  respect_robots: true
  user_agent: "site2md/1.0 (+https://yourdomain.example)"
  proxies: null
  delay_seconds: 0
  auth:
  cookies_file: null
  headers_file: null
  playwright_context_dir: null
  render:
  enabled: false
  wait_for: "networkidle"
  timeout: 15000
  markdown:
  add_toc: true
  front_matter: true
  assets:
  download: false
  min_bytes: 1024
  folder: "assets"

⸻

Performance Tips (baked into code)
• Sitemap-first crawl drastically reduces fetches.
• Use HTTP/2 + pooled connections; enable brotli.
• Cap per‑host concurrency (e.g., 4–8) and add jitter to avoid rate‑limits.
• Incremental mode with ETag/Last‑Modified + content hash prevents re‑downloading unchanged pages.
• Render only when needed (--render); static fetch is 5–20× faster.
• Pre‑filter URLs via include/exclude regex before enqueueing.

⸻

Legal & Platform Notes
• Always follow robots.txt and site ToS.
• LinkedIn: automated scraping can violate ToS. Prefer the official Data Export under Settings. If you still proceed for your own account, use your own login via the interactive mode or cookie import—you’re responsible for compliance.
