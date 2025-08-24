"""Logging configuration for Site2MD."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

_loggers: Dict[str, logging.Logger] = {}
_console = Console(stderr=True)


def setup_logging(
    verbose: bool = False,
    debug: bool = False,
    log_file: Optional[Path] = None,
    json_format: bool = False,
) -> None:
    """Setup logging configuration for Site2MD."""
    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Setup console handler with Rich
    console_handler = RichHandler(
        console=_console,
        show_path=debug,
        show_time=True,
        rich_tracebacks=True,
        markup=True,
    )
    console_handler.setLevel(level)
    
    if json_format:
        console_formatter = JSONFormatter()
    else:
        console_formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]",
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if requested
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always debug for file
        
        file_formatter = JSONFormatter() if json_format else logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    root_logger.setLevel(logging.DEBUG)
    
    # Configure third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("trafilatura").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance."""
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName",
                "process", "getMessage", "exc_info", "exc_text", "stack_info"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class CrawlStatsLogger:
    """Logger for crawl statistics and progress."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stats = {
            "pages_crawled": 0,
            "pages_cached": 0,
            "pages_failed": 0,
            "assets_downloaded": 0,
            "total_bytes": 0,
            "start_time": None,
            "end_time": None,
        }
    
    def log_page_crawled(self, url: str, bytes_count: int = 0) -> None:
        """Log a successfully crawled page."""
        self.stats["pages_crawled"] += 1
        self.stats["total_bytes"] += bytes_count
        self.logger.debug(f"Crawled: {url} ({bytes_count} bytes)")
    
    def log_page_cached(self, url: str) -> None:
        """Log a cached page (skipped)."""
        self.stats["pages_cached"] += 1
        self.logger.debug(f"Cached: {url}")
    
    def log_page_failed(self, url: str, error: str) -> None:
        """Log a failed page."""
        self.stats["pages_failed"] += 1
        self.logger.warning(f"Failed: {url} - {error}")
    
    def log_asset_downloaded(self, url: str, bytes_count: int = 0) -> None:
        """Log a downloaded asset."""
        self.stats["assets_downloaded"] += 1
        self.stats["total_bytes"] += bytes_count
        self.logger.debug(f"Downloaded asset: {url} ({bytes_count} bytes)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats = self.stats.copy()
        if self.stats["start_time"] and self.stats["end_time"]:
            stats["duration_seconds"] = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()
        return stats