"""Custom exceptions for Site2MD."""


class Site2MDError(Exception):
    """Base exception class for Site2MD errors."""
    pass


class ConfigError(Site2MDError):
    """Configuration-related errors."""
    pass


class CrawlError(Site2MDError):
    """Crawling-related errors."""
    pass


class FetchError(Site2MDError):
    """HTTP fetching errors."""
    pass


class AuthError(Site2MDError):
    """Authentication-related errors."""
    pass


class RenderError(Site2MDError):
    """JavaScript rendering errors."""
    pass


class ProcessingError(Site2MDError):
    """Content processing errors."""
    pass


class StorageError(Site2MDError):
    """Storage and file system errors."""
    pass


class ValidationError(Site2MDError):
    """Data validation errors."""
    pass


class RobotsError(Site2MDError):
    """Robots.txt related errors."""
    pass