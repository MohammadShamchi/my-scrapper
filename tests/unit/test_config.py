"""Unit tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from site2md.cli.config import load_config, DEFAULT_CONFIG
from site2md.utils.exceptions import ConfigError


class TestConfigLoading:
    """Test configuration loading functionality."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_config(url="https://example.com", out=Path("./test"))
        
        assert config["start_urls"] == ["https://example.com"]
        assert config["output"]["directory"] == Path("./test")
        assert config["limits"]["max_pages"] == DEFAULT_CONFIG["limits"]["max_pages"]
    
    def test_load_config_from_file(self, temp_dir):
        """Test loading configuration from file."""
        config_data = {
            "limits": {"max_pages": 500, "max_depth": 3},
            "fetch": {"concurrency": 4, "timeout": 30},
        }
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(
            config_file=config_file,
            url="https://example.com",
            out=Path("./test")
        )
        
        assert config["limits"]["max_pages"] == 500
        assert config["limits"]["max_depth"] == 3
        assert config["fetch"]["concurrency"] == 4
        assert config["fetch"]["timeout"] == 30
    
    def test_cli_overrides_config_file(self, temp_dir):
        """Test CLI arguments override config file."""
        config_data = {
            "limits": {"max_pages": 500},
            "fetch": {"concurrency": 4},
        }
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(
            config_file=config_file,
            url="https://example.com",
            out=Path("./test"),
            max_pages=100,  # CLI override
            concurrency=8   # CLI override
        )
        
        assert config["limits"]["max_pages"] == 100  # CLI wins
        assert config["fetch"]["concurrency"] == 8   # CLI wins
    
    def test_invalid_yaml_config(self, temp_dir):
        """Test invalid YAML configuration handling."""
        config_file = temp_dir / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(config_file=config_file, url="https://example.com")
    
    def test_missing_start_urls(self):
        """Test missing start URLs validation."""
        with pytest.raises(ConfigError, match="At least one start URL"):
            load_config()
    
    def test_invalid_url_validation(self):
        """Test invalid URL validation."""
        with pytest.raises(ConfigError, match="Invalid URL"):
            load_config(url="not-a-valid-url")
    
    def test_negative_limits_validation(self):
        """Test negative limits validation."""
        with pytest.raises(ConfigError, match="max_pages must be positive"):
            load_config(url="https://example.com", max_pages=-1)
        
        with pytest.raises(ConfigError, match="concurrency must be positive"):
            load_config(url="https://example.com", concurrency=0)
    
    def test_auth_file_validation(self, temp_dir):
        """Test authentication file validation."""
        # Non-existent cookies file
        with pytest.raises(ConfigError, match="Auth file not found"):
            load_config(
                url="https://example.com", 
                cookies="/non/existent/cookies.txt"
            )
        
        # Non-existent headers file
        with pytest.raises(ConfigError, match="Auth file not found"):
            load_config(
                url="https://example.com",
                headers="/non/existent/headers.json"
            )


class TestConfigMerging:
    """Test configuration merging logic."""
    
    def test_deep_merge_nested_dicts(self, temp_dir):
        """Test deep merging of nested dictionaries."""
        config_data = {
            "limits": {
                "max_pages": 500,
                # max_depth should come from default
            },
            "fetch": {
                "concurrency": 4,
                "timeout": 30,
                # other fetch settings should come from default
            }
        }
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(
            config_file=config_file,
            url="https://example.com"
        )
        
        # Custom values
        assert config["limits"]["max_pages"] == 500
        assert config["fetch"]["concurrency"] == 4
        assert config["fetch"]["timeout"] == 30
        
        # Default values should still be present
        assert config["limits"]["max_depth"] == DEFAULT_CONFIG["limits"]["max_depth"]
        assert config["fetch"]["respect_robots"] == DEFAULT_CONFIG["fetch"]["respect_robots"]
    
    def test_list_handling(self, temp_dir):
        """Test list value handling in configuration."""
        config_data = {
            "scope": {
                "include": [r"docs", r"api"],
                "exclude": [r"admin", r"private"],
            }
        }
        
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(
            config_file=config_file,
            url="https://example.com",
            include=[r"guides"],  # CLI override
            exclude=[r"temp"]     # CLI override
        )
        
        # CLI should override file values for lists
        assert config["scope"]["include"] == [r"guides"]
        assert config["scope"]["exclude"] == [r"temp"]


class TestConfigNormalization:
    """Test configuration normalization and type conversion."""
    
    def test_path_normalization(self):
        """Test Path object normalization."""
        config = load_config(
            url="https://example.com",
            out="./test/output"  # String path
        )
        
        assert isinstance(config["output"]["directory"], Path)
        assert config["output"]["directory"] == Path("./test/output")
    
    def test_start_urls_list_conversion(self):
        """Test start URLs list conversion."""
        config = load_config(url="https://example.com")
        
        assert isinstance(config["start_urls"], list)
        assert config["start_urls"] == ["https://example.com"]
    
    def test_boolean_values(self):
        """Test boolean value handling."""
        config = load_config(
            url="https://example.com",
            render=True,
            download_assets=False,
            respect_robots=True
        )
        
        assert config["render"]["enabled"] is True
        assert config["assets"]["download"] is False
        assert config["fetch"]["respect_robots"] is True