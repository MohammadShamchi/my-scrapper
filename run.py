#!/usr/bin/env python3
"""
Simple entry point for running the Site2MD web server.
This avoids relative import issues when running directly.
"""

from site2md.web.main import main
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


if __name__ == "__main__":
    main()
