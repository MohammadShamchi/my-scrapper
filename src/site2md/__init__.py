"""
Site2MD: Universal Website → Markdown Exporter

A production-grade Python CLI application that crawls any website 
and exports each page as high-quality Markdown files.
"""

__version__ = "1.0.0"
__author__ = "Site2MD Team"
__email__ = "hello@site2md.com"

from .cli.main import app

__all__ = ["app"]