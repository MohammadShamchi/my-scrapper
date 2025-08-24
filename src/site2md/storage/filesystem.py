"""File system management for Site2MD."""

import hashlib
from pathlib import Path
from typing import Any, Dict

from ..utils.exceptions import StorageError
from ..utils.logging import get_logger
from ..utils.validation import sanitize_filename, url_to_filepath

logger = get_logger(__name__)


class FileSystemManager:
    """Manages file system operations for Site2MD."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config["output"]["directory"])
        self.assets_dir = self.output_dir / config.get("assets", {}).get("folder", "assets")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if config.get("assets", {}).get("download", False):
            self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_page(self, url: str, markdown_content: str) -> Path:
        """Save page content as Markdown file."""
        try:
            # Generate file path
            relative_path = url_to_filepath(url, self.config["start_urls"][0])
            file_path = self.output_dir / relative_path
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle naming conflicts
            file_path = self._resolve_path_conflict(file_path)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.debug(f"Saved page: {url} -> {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save page {url}: {e}")
            raise StorageError(f"Failed to save page {url}: {e}") from e
    
    async def save_asset(self, asset_url: str, asset_data: bytes, content_type: str = "") -> Path:
        """Save asset file and return its path."""
        try:
            # Generate filename from URL and content hash
            url_hash = hashlib.md5(asset_url.encode()).hexdigest()[:8]
            content_hash = hashlib.md5(asset_data).hexdigest()[:8]
            
            # Determine file extension
            extension = self._get_extension_from_url_or_type(asset_url, content_type)
            
            filename = f"{url_hash}_{content_hash}{extension}"
            file_path = self.assets_dir / filename
            
            # Skip if file already exists (same content)
            if file_path.exists():
                existing_size = file_path.stat().st_size
                if existing_size == len(asset_data):
                    logger.debug(f"Asset already exists: {file_path}")
                    return file_path
            
            # Write asset data
            with open(file_path, 'wb') as f:
                f.write(asset_data)
            
            logger.debug(f"Saved asset: {asset_url} -> {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save asset {asset_url}: {e}")
            raise StorageError(f"Failed to save asset {asset_url}: {e}") from e
    
    def _resolve_path_conflict(self, original_path: Path) -> Path:
        """Resolve path conflicts by adding suffixes."""
        if not original_path.exists():
            return original_path
        
        # Try adding numeric suffixes
        counter = 1
        stem = original_path.stem
        suffix = original_path.suffix
        parent = original_path.parent
        
        while counter < 1000:  # Safety limit
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
        
        # If we can't resolve, use timestamp
        import time
        timestamp = int(time.time())
        new_name = f"{stem}_{timestamp}{suffix}"
        return parent / new_name
    
    def _get_extension_from_url_or_type(self, url: str, content_type: str) -> str:
        """Determine file extension from URL or content type."""
        from urllib.parse import urlparse
        
        # First try URL extension
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if path and '.' in path:
            extension = path.split('.')[-1].lower()
            if len(extension) <= 5:  # Reasonable extension length
                return f".{extension}"
        
        # Fall back to content type
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'text/css': '.css',
            'application/javascript': '.js',
            'text/javascript': '.js',
            'application/pdf': '.pdf',
            'application/zip': '.zip',
        }
        
        return content_type_map.get(content_type.lower(), '')
    
    async def create_directory_structure(self) -> None:
        """Create the basic directory structure."""
        try:
            # Main output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Assets directory (if needed)
            if self.config.get("assets", {}).get("download", False):
                self.assets_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created directory structure at {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create directory structure: {e}")
            raise StorageError(f"Failed to create directory structure: {e}") from e
    
    async def clean_output_directory(self, force: bool = False) -> None:
        """Clean the output directory."""
        if not force:
            logger.warning("Use force=True to actually clean the output directory")
            return
        
        try:
            import shutil
            
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                logger.info(f"Cleaned output directory: {self.output_dir}")
            
            # Recreate directory structure
            await self.create_directory_structure()
            
        except Exception as e:
            logger.error(f"Failed to clean output directory: {e}")
            raise StorageError(f"Failed to clean output directory: {e}") from e
    
    def get_relative_path(self, file_path: Path) -> str:
        """Get relative path from output directory."""
        try:
            return str(file_path.relative_to(self.output_dir))
        except ValueError:
            return str(file_path)