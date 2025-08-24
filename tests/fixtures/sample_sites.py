"""Sample site fixtures for testing."""

# Complex HTML document for comprehensive testing
COMPLEX_HTML_DOCUMENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="A comprehensive test page with various HTML elements and structures.">
    <meta name="keywords" content="test, html, markdown, conversion">
    <title>Comprehensive Test Page</title>
    <link rel="canonical" href="https://example.com/comprehensive-test">
    <style>
        .hidden { display: none; }
        .highlight { background: yellow; }
    </style>
</head>
<body>
    <!-- Navigation should be preserved -->
    <nav aria-label="Main navigation">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/docs">Documentation</a></li>
            <li><a href="/api">API Reference</a></li>
            <li><a href="https://github.com/example/repo">GitHub</a></li>
        </ul>
    </nav>
    
    <!-- Main content -->
    <main>
        <header>
            <h1>Comprehensive Test Page</h1>
            <p class="lead">This page contains various HTML elements to test content extraction and markdown conversion.</p>
        </header>
        
        <section id="text-formatting">
            <h2>Text Formatting</h2>
            <p>This paragraph contains <strong>bold text</strong>, <em>italic text</em>, 
               <u>underlined text</u>, <del>strikethrough text</del>, and <ins>inserted text</ins>.</p>
            
            <p>We also have <code>inline code</code> and <mark>highlighted text</mark>.</p>
            
            <blockquote>
                <p>This is a blockquote with multiple paragraphs.</p>
                <p>It demonstrates how quoted content should be handled.</p>
                <cite>— Test Author</cite>
            </blockquote>
        </section>
        
        <section id="lists">
            <h2>Lists</h2>
            
            <h3>Unordered List</h3>
            <ul>
                <li>First item</li>
                <li>Second item with <strong>nested formatting</strong></li>
                <li>Third item
                    <ul>
                        <li>Nested item 1</li>
                        <li>Nested item 2</li>
                    </ul>
                </li>
                <li>Fourth item</li>
            </ul>
            
            <h3>Ordered List</h3>
            <ol>
                <li>First step</li>
                <li>Second step</li>
                <li>Third step with sub-steps:
                    <ol type="a">
                        <li>Sub-step A</li>
                        <li>Sub-step B</li>
                    </ol>
                </li>
                <li>Final step</li>
            </ol>
            
            <h3>Definition List</h3>
            <dl>
                <dt>Term 1</dt>
                <dd>Definition of term 1</dd>
                <dt>Term 2</dt>
                <dd>Definition of term 2 with more detail</dd>
            </dl>
        </section>
        
        <section id="code-examples">
            <h2>Code Examples</h2>
            
            <h3>Python Code</h3>
            <pre><code class="language-python">
def hello_world():
    """Print a greeting message."""
    message = "Hello, world!"
    print(message)
    return message

if __name__ == "__main__":
    hello_world()
            </code></pre>
            
            <h3>JavaScript Code</h3>
            <pre><code class="language-javascript">
function calculateSum(a, b) {
    // Add two numbers and return the result
    const result = a + b;
    console.log(`The sum of ${a} and ${b} is ${result}`);
    return result;
}

const sum = calculateSum(5, 3);
            </code></pre>
            
            <h3>HTML Code</h3>
            <pre><code class="language-html">
&lt;div class="container"&gt;
    &lt;h1&gt;Page Title&lt;/h1&gt;
    &lt;p&gt;This is a paragraph.&lt;/p&gt;
&lt;/div&gt;
            </code></pre>
        </section>
        
        <section id="tables">
            <h2>Tables</h2>
            
            <h3>Simple Table</h3>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Age</th>
                        <th>City</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Alice</td>
                        <td>30</td>
                        <td>New York</td>
                    </tr>
                    <tr>
                        <td>Bob</td>
                        <td>25</td>
                        <td>London</td>
                    </tr>
                    <tr>
                        <td>Charlie</td>
                        <td>35</td>
                        <td>Tokyo</td>
                    </tr>
                </tbody>
            </table>
            
            <h3>Complex Table with Spans</h3>
            <table>
                <thead>
                    <tr>
                        <th rowspan="2">Category</th>
                        <th colspan="2">Metrics</th>
                    </tr>
                    <tr>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Type A</td>
                        <td>150</td>
                        <td>75%</td>
                    </tr>
                    <tr>
                        <td>Type B</td>
                        <td>50</td>
                        <td>25%</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section id="media">
            <h2>Media Elements</h2>
            
            <h3>Images</h3>
            <figure>
                <img src="/images/sample.jpg" alt="Sample image" width="300" height="200">
                <figcaption>This is a sample image with a caption.</figcaption>
            </figure>
            
            <p>Inline image: <img src="/images/icon.png" alt="Icon" width="16" height="16"> with text.</p>
            
            <h3>Links</h3>
            <p>Visit our <a href="/documentation" title="Complete documentation">documentation</a> 
               or check out our <a href="https://github.com/example/repo" target="_blank" rel="noopener">GitHub repository</a>.</p>
        </section>
        
        <section id="special-elements">
            <h2>Special Elements</h2>
            
            <h3>Abbreviations and Acronyms</h3>
            <p>The <abbr title="HyperText Markup Language">HTML</abbr> specification is maintained by the 
               <acronym title="World Wide Web Consortium">W3C</acronym>.</p>
            
            <h3>Time and Data</h3>
            <p>Published on <time datetime="2023-01-15T14:30:00Z">January 15, 2023 at 2:30 PM</time>.</p>
            
            <h3>Keyboard and Code Elements</h3>
            <p>To save the file, press <kbd>Ctrl+S</kbd> or use the <code>save()</code> function.</p>
            
            <h3>Mathematical Expressions</h3>
            <p>The formula is: E = mc<sup>2</sup></p>
            <p>Water molecule: H<sub>2</sub>O</p>
        </section>
    </main>
    
    <!-- Sidebar content (should be filtered out by trafilatura) -->
    <aside>
        <h3>Related Articles</h3>
        <ul>
            <li><a href="/article1">Article 1</a></li>
            <li><a href="/article2">Article 2</a></li>
        </ul>
        
        <div class="advertisement">
            <p>Advertisement content that should be filtered out.</p>
        </div>
    </aside>
    
    <!-- Footer (should be filtered out) -->
    <footer>
        <p>&copy; 2023 Example Company. All rights reserved.</p>
        <nav>
            <a href="/privacy">Privacy Policy</a>
            <a href="/terms">Terms of Service</a>
        </nav>
    </footer>
    
    <!-- Script tags should be stripped -->
    <script>
        console.log("This script should be removed");
        function trackAnalytics() {
            // Analytics code
        }
    </script>
</body>
</html>
"""

# Sample sitemap index (points to multiple sitemaps)
SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://example.com/sitemap-main.xml</loc>
        <lastmod>2023-01-01T00:00:00Z</lastmod>
    </sitemap>
    <sitemap>
        <loc>https://example.com/sitemap-blog.xml</loc>
        <lastmod>2023-01-02T00:00:00Z</lastmod>
    </sitemap>
    <sitemap>
        <loc>https://example.com/sitemap-docs.xml</loc>
        <lastmod>2023-01-03T00:00:00Z</lastmod>
    </sitemap>
</sitemapindex>"""

# Main pages sitemap
SITEMAP_MAIN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2023-01-01T00:00:00Z</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/about</loc>
        <lastmod>2023-01-01T00:00:00Z</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/contact</loc>
        <lastmod>2023-01-01T00:00:00Z</lastmod>
        <changefreq>yearly</changefreq>
        <priority>0.6</priority>
    </url>
</urlset>"""

# Documentation sitemap
SITEMAP_DOCS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/docs</loc>
        <lastmod>2023-01-03T00:00:00Z</lastmod>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://example.com/docs/getting-started</loc>
        <lastmod>2023-01-03T00:00:00Z</lastmod>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/docs/api-reference</loc>
        <lastmod>2023-01-03T00:00:00Z</lastmod>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/docs/examples</loc>
        <lastmod>2023-01-03T00:00:00Z</lastmod>
        <priority>0.7</priority>
    </url>
</urlset>"""

# Comprehensive robots.txt
ROBOTS_TXT = """# Robots.txt for testing
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /private/
Disallow: *.pdf$
Crawl-delay: 2

User-agent: site2md
Allow: /
Crawl-delay: 1

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-index.xml
"""

# Sample error page
ERROR_404_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found</title>
</head>
<body>
    <h1>Page Not Found</h1>
    <p>The requested page could not be found.</p>
    <a href="/">Return to home page</a>
</body>
</html>
"""

# Sample JavaScript-heavy page
JS_HEAVY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dynamic Content Page</title>
</head>
<body>
    <div id="loading">Loading...</div>
    <div id="content" style="display: none;">
        <h1>Dynamic Content</h1>
        <p>This content is loaded by JavaScript.</p>
        <div id="data-container"></div>
    </div>
    
    <script>
        // Simulate dynamic content loading
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';
            
            // Add dynamic data
            const container = document.getElementById('data-container');
            const data = ['Item 1', 'Item 2', 'Item 3'];
            const list = document.createElement('ul');
            
            data.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                list.appendChild(li);
            });
            
            container.appendChild(list);
        }, 1000);
    </script>
</body>
</html>
"""