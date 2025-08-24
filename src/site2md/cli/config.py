"""Configuration management for Site2MD."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..utils.exceptions import ConfigError
from ..utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG = {
    "start_urls": [],
    "scope": {
        "allow_subdomains": False,
        "include": [],
        "exclude": [],
    },
    "limits": {
        "max_pages": 1000,
        "max_depth": 5,
    },
    "fetch": {
        "concurrency": 8,
        "timeout": 20,
        "respect_robots": True,
        "user_agent": "site2md/1.0 (+https://github.com/yourorg/site2md)",
        "proxies": None,
        "delay_seconds": 0,
    },
    "auth": {
        "cookies_file": None,
        "headers_file": None,
        "playwright_context_dir": None,
    },
    "render": {
        "enabled": False,
        "wait_for": "networkidle",
        "timeout": 15000,
    },
    "markdown": {
        "add_toc": True,
        "front_matter": True,
    },
    "assets": {
        "download": False,
        "min_bytes": 1024,
        "folder": "assets",
    },
    "output": {
        "directory": "./export",
    },
    "discovery": {
        "sitemap_first": True,
    },
    "incremental": {
        "enabled": False,
    },
}


def load_config(
    config_file: Optional[Path] = None,
    **cli_overrides: Any
) -> Dict[str, Any]:
    """Load configuration from file and CLI arguments."""
    config = DEFAULT_CONFIG.copy()
    
    # Load from file if provided
    if config_file and config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
            config = _merge_config(config, file_config)
            logger.debug(f"Loaded configuration from {config_file}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file {config_file}: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading config file {config_file}: {e}")
    
    # Apply CLI overrides
    config = _apply_cli_overrides(config, cli_overrides)
    
    # Validate and normalize
    config = _validate_config(config)
    
    return config


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def _apply_cli_overrides(config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Apply CLI argument overrides to configuration."""
    # Remove None values from overrides
    overrides = {k: v for k, v in overrides.items() if v is not None}
    
    # Map CLI arguments to config structure
    cli_mapping = {
        "url": ("start_urls", lambda x: [x]),
        "out": ("output.directory", str),
        "max_pages": ("limits.max_pages", int),
        "max_depth": ("limits.max_depth", int),
        "concurrency": ("fetch.concurrency", int),
        "cookies": ("auth.cookies_file", str),
        "headers": ("auth.headers_file", str),
        "playwright_context": ("auth.playwright_context_dir", str),
        "render": ("render.enabled", bool),
        "download_assets": ("assets.download", bool),
        "allow_subdomains": ("scope.allow_subdomains", bool),
        "sitemap_first": ("discovery.sitemap_first", bool),
        "respect_robots": ("fetch.respect_robots", bool),
        "incremental": ("incremental.enabled", bool),
        "include": ("scope.include", list),
        "exclude": ("scope.exclude", list),
    }
    
    for cli_key, (config_path, converter) in cli_mapping.items():
        if cli_key in overrides:
            value = overrides[cli_key]
            if converter:
                value = converter(value)
            _set_nested_config(config, config_path, value)
    
    # Handle special cases
    if "dry_run" in overrides:
        config["dry_run"] = overrides["dry_run"]
    
    return config


def _set_nested_config(config: Dict[str, Any], path: str, value: Any) -> None:
    """Set a nested configuration value using dot notation."""
    keys = path.split('.')
    current = config
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize configuration."""
    # Ensure start_urls is a list
    if not config.get("start_urls"):
        raise ConfigError("At least one start URL must be provided")
    
    if isinstance(config["start_urls"], str):
        config["start_urls"] = [config["start_urls"]]
    
    # Validate URLs
    for url in config["start_urls"]:
        if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
            raise ConfigError(f"Invalid URL: {url}")
    
    # Ensure output directory is Path
    output_dir = config["output"]["directory"]
    if isinstance(output_dir, str):
        config["output"]["directory"] = Path(output_dir)
    
    # Validate numeric limits
    limits = config["limits"]
    if limits["max_pages"] <= 0:
        raise ConfigError("max_pages must be positive")
    if limits["max_depth"] <= 0:
        raise ConfigError("max_depth must be positive")
    
    fetch = config["fetch"]
    if fetch["concurrency"] <= 0:
        raise ConfigError("concurrency must be positive")
    if fetch["timeout"] <= 0:
        raise ConfigError("timeout must be positive")
    
    # Validate auth files exist if specified
    auth = config["auth"]
    for file_key in ["cookies_file", "headers_file"]:
        if auth[file_key] and not Path(auth[file_key]).exists():
            raise ConfigError(f"Auth file not found: {auth[file_key]}")
    
    if auth["playwright_context_dir"]:
        ctx_dir = Path(auth["playwright_context_dir"])
        if not ctx_dir.exists():
            logger.warning(f"Playwright context directory not found: {ctx_dir}")
    
    return config


def save_example_config(path: Path) -> None:
    """Save example configuration file."""
    example_config = {
        "start_urls": ["https://example.com"],
        "scope": {
            "allow_subdomains": False,
            "include": [],
            "exclude": [],
        },
        "limits": {
            "max_pages": 1000,
            "max_depth": 5,
        },
        "fetch": {
            "concurrency": 8,
            "timeout": 20,
            "respect_robots": True,
            "user_agent": "site2md/1.0 (+https://yourdomain.example)",
            "proxies": None,
            "delay_seconds": 0,
        },
        "auth": {
            "cookies_file": None,
            "headers_file": None,
            "playwright_context_dir": None,
        },
        "render": {
            "enabled": False,
            "wait_for": "networkidle",
            "timeout": 15000,
        },
        "markdown": {
            "add_toc": True,
            "front_matter": True,
        },
        "assets": {
            "download": False,
            "min_bytes": 1024,
            "folder": "assets",
        },
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(example_config, f, default_flow_style=False, indent=2)