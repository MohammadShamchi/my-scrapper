"""SQLite-based manifest for tracking crawl state and incremental updates."""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from ..utils.exceptions import StorageError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CrawlManifest:
    """Manages crawl state using SQLite database."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.db_path = self.output_dir / ".site2md_manifest.db"
        self.db: Optional[aiosqlite.Connection] = None
    
    async def initialize(self) -> None:
        """Initialize the manifest database."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            self.db = await aiosqlite.connect(self.db_path)
            
            # Enable WAL mode for better concurrency
            await self.db.execute("PRAGMA journal_mode=WAL")
            await self.db.execute("PRAGMA synchronous=NORMAL")
            await self.db.execute("PRAGMA cache_size=10000")
            
            # Create tables
            await self._create_tables()
            
            logger.debug(f"Initialized manifest database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize manifest: {e}")
            raise StorageError(f"Failed to initialize manifest: {e}") from e
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()
            self.db = None
    
    async def _create_tables(self) -> None:
        """Create database tables."""
        # Pages table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                normalized_url TEXT NOT NULL,
                canonical_url TEXT,
                title TEXT,
                content_hash TEXT,
                etag TEXT,
                last_modified TEXT,
                fetch_timestamp TEXT NOT NULL,
                file_path TEXT,
                status TEXT NOT NULL DEFAULT 'success',
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Assets table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                content_hash TEXT,
                size_bytes INTEGER,
                content_type TEXT,
                fetch_timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crawl sessions table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS crawl_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                config_hash TEXT,
                pages_crawled INTEGER DEFAULT 0,
                pages_failed INTEGER DEFAULT 0,
                assets_downloaded INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_pages_normalized_url ON pages(normalized_url)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON pages(content_hash)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_assets_url ON assets(url)")
        
        await self.db.commit()
    
    async def update_page(
        self,
        url: str,
        filepath: Path,
        content_hash: int,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        title: Optional[str] = None,
        canonical_url: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> None:
        """Update page information in manifest."""
        try:
            content_hash_str = str(content_hash) if content_hash else None
            fetch_timestamp = datetime.now().isoformat()
            
            await self.db.execute("""
                INSERT OR REPLACE INTO pages (
                    url, normalized_url, canonical_url, title, content_hash,
                    etag, last_modified, fetch_timestamp, file_path, status, error_message,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                url,  # normalized_url (same for now)
                canonical_url,
                title,
                content_hash_str,
                etag,
                last_modified,
                fetch_timestamp,
                str(filepath),
                status,
                error_message,
                datetime.now().isoformat()
            ))
            
            await self.db.commit()
            
            logger.debug(f"Updated page manifest: {url}")
            
        except Exception as e:
            logger.error(f"Failed to update page manifest for {url}: {e}")
            raise StorageError(f"Failed to update page manifest: {e}") from e
    
    async def update_asset(
        self,
        url: str,
        filepath: Path,
        content_hash: str,
        size_bytes: int,
        content_type: str = ""
    ) -> None:
        """Update asset information in manifest."""
        try:
            fetch_timestamp = datetime.now().isoformat()
            
            await self.db.execute("""
                INSERT OR REPLACE INTO assets (
                    url, file_path, content_hash, size_bytes, content_type, fetch_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (url, str(filepath), content_hash, size_bytes, content_type, fetch_timestamp))
            
            await self.db.commit()
            
            logger.debug(f"Updated asset manifest: {url}")
            
        except Exception as e:
            logger.error(f"Failed to update asset manifest for {url}: {e}")
    
    async def is_up_to_date(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        content_hash: Optional[int] = None
    ) -> bool:
        """Check if a page is up to date (for incremental crawling)."""
        try:
            cursor = await self.db.execute("""
                SELECT etag, last_modified, content_hash, status FROM pages 
                WHERE url = ? OR normalized_url = ?
            """, (url, url))
            
            row = await cursor.fetchone()
            if not row:
                return False  # Page not in manifest
            
            db_etag, db_last_modified, db_content_hash, status = row
            
            # Skip if previous crawl failed
            if status != "success":
                return False
            
            # Check ETag first (most reliable)
            if etag and db_etag:
                return etag == db_etag
            
            # Check Last-Modified
            if last_modified and db_last_modified:
                return last_modified == db_last_modified
            
            # Check content hash if available
            if content_hash and db_content_hash:
                return str(content_hash) == db_content_hash
            
            # If no comparison method available, consider stale
            return False
            
        except Exception as e:
            logger.debug(f"Error checking if {url} is up to date: {e}")
            return False  # On error, re-crawl to be safe
    
    async def get_page_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get page information from manifest."""
        try:
            cursor = await self.db.execute("""
                SELECT * FROM pages WHERE url = ? OR normalized_url = ?
            """, (url, url))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
            
        except Exception as e:
            logger.debug(f"Error getting page info for {url}: {e}")
            return None
    
    async def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawl statistics from manifest."""
        try:
            # Page stats
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_pages,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_pages,
                    SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as failed_pages
                FROM pages
            """)
            page_stats = await cursor.fetchone()
            
            # Asset stats
            cursor = await self.db.execute("""
                SELECT COUNT(*) as total_assets, SUM(size_bytes) as total_asset_bytes
                FROM assets
            """)
            asset_stats = await cursor.fetchone()
            
            return {
                "total_pages": page_stats[0] or 0,
                "successful_pages": page_stats[1] or 0,
                "failed_pages": page_stats[2] or 0,
                "total_assets": asset_stats[0] or 0,
                "total_asset_bytes": asset_stats[1] or 0,
            }
            
        except Exception as e:
            logger.error(f"Error getting crawl stats: {e}")
            return {}
    
    async def cleanup_old_entries(self, days: int = 30) -> None:
        """Clean up old manifest entries."""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            await self.db.execute("""
                DELETE FROM pages WHERE updated_at < ?
            """, (cutoff_iso,))
            
            await self.db.execute("""
                DELETE FROM assets WHERE fetch_timestamp < ?
            """, (cutoff_iso,))
            
            await self.db.commit()
            
            logger.info(f"Cleaned up manifest entries older than {days} days")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup old manifest entries: {e}")
    
    async def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        try:
            await self.db.execute("VACUUM")
            logger.debug("Vacuumed manifest database")
        except Exception as e:
            logger.warning(f"Failed to vacuum manifest database: {e}")
    
    def __aenter__(self):
        return self.initialize()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()