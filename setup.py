from setuptools import find_packages, setup

setup(
    name="site2md",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.6",
        "websockets>=12.0",
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "pyyaml>=6.0.0",
        "httpx[http2]>=0.25.0",
        "anyio>=3.7.0,<4.0.0",
        "brotli>=1.0.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "trafilatura>=1.6.0",
        "readability-lxml>=0.8.0",
        "markdownify>=0.11.0",
        "tldextract>=5.0.0",
        "urllib3>=2.0.0",
        "requests>=2.28.0",
        "aiosqlite>=0.19.0",
        "python-dateutil>=2.8.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "site2md=site2md.cli.main:app",
            "site2md-web=site2md.web.main:main",
        ],
    },
    python_requires=">=3.11",
)
