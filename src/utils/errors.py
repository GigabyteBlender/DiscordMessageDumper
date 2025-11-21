"""
Error handling utilities for Discord Message Delete Helper.

This module provides custom exception classes, error message formatting,
and logging configuration with sensitive data filtering.
"""

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# ============================================================================
# Custom Exception Classes
# ============================================================================

class AppError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def format_message(self) -> str:
        """Format error message for user display."""
        if self.details:
            return f"{self.message}\n\nDetails: {self.details}"
        return self.message


class AuthenticationError(AppError):
    """Exception raised for authentication-related errors."""
    
    def __init__(self, message: str, error_type: str = "general", details: Optional[str] = None):
        """
        Initialize authentication error.
        
        Args:
            message: User-friendly error message
            error_type: Type of auth error (oauth_flow, invalid_token, expired_token, network)
            details: Additional technical details
        """
        self.error_type = error_type
        super().__init__(message, details)


class FileSystemError(AppError):
    """Exception raised for file system operation errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, details: Optional[str] = None):
        """
        Initialize file system error.
        
        Args:
            message: User-friendly error message
            file_path: Path to the file that caused the error
            details: Additional technical details
        """
        self.file_path = file_path
        # Ensure file path is included in the message (Property 14)
        if file_path:
            message = f"{message} (File: {file_path})"
        super().__init__(message, details)


class EmailError(AppError):
    """Exception raised for email-related errors."""
    
    def __init__(self, message: str, error_type: str = "general", details: Optional[str] = None):
        """
        Initialize email error.
        
        Args:
            message: User-friendly error message
            error_type: Type of email error (smtp_config, auth_failure, network_timeout, attachment)
            details: Additional technical details
        """
        self.error_type = error_type
        super().__init__(message, details)


class ValidationError(AppError):
    """Exception raised for input validation errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[str] = None):
        """
        Initialize validation error.
        
        Args:
            message: User-friendly error message
            field_name: Name of the field that failed validation
            details: Additional guidance for correction
        """
        self.field_name = field_name
        super().__init__(message, details)


class NetworkError(AppError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, error_category: str = "connection", details: Optional[str] = None):
        """
        Initialize network error.
        
        Args:
            message: User-friendly error message
            error_category: Category of network error (connection, authentication, server)
            details: Additional technical details
        """
        # Validate error category (Property 15)
        valid_categories = ["connection", "authentication", "server"]
        if error_category not in valid_categories:
            error_category = "connection"
        
        self.error_category = error_category
        super().__init__(message, details)


# ============================================================================
# Sensitive Data Filter for Logging
# ============================================================================

class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that redacts sensitive information from log messages.
    
    This filter prevents passwords, tokens, and other credentials from
    appearing in plain text in log files (Property 19).
    """
    
    # Patterns to redact
    SENSITIVE_PATTERNS = [
        # OAuth tokens and access tokens
        (r'token["\']?\s*[:=]\s*["\']?[\w\-\.]+', 'token=***REDACTED***'),
        (r'access_token["\']?\s*[:=]\s*["\']?[\w\-\.]+', 'access_token=***REDACTED***'),
        (r'bearer\s+[\w\-\.]+', 'bearer ***REDACTED***'),
        
        # Passwords
        (r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', 'password=***REDACTED***'),
        (r'passwd["\']?\s*[:=]\s*["\']?[^\s"\']+', 'passwd=***REDACTED***'),
        (r'pwd["\']?\s*[:=]\s*["\']?[^\s"\']+', 'pwd=***REDACTED***'),
        
        # API keys and secrets (including common prefixes like sk_, pk_, etc.)
        (r'api[_\-]?key["\']?\s*[:=]\s*["\']?[\w\-]+', 'api_key=***REDACTED***'),
        (r'["\']?[sp]k_[a-zA-Z0-9_]+', '***REDACTED***'),  # Stripe-style keys
        (r'secret["\']?\s*[:=]\s*["\']?[\w\-]+', 'secret=***REDACTED***'),
        (r'client[_\-]?secret["\']?\s*[:=]\s*["\']?[\w\-]+', 'client_secret=***REDACTED***'),
        
        # Email credentials in SMTP context
        (r'smtp.*password["\']?\s*[:=]\s*["\']?[^\s"\']+', 'smtp_password=***REDACTED***'),
        
        # Authorization headers
        (r'Authorization:\s*[\w\s]+[\w\-\.]+', 'Authorization: ***REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to redact sensitive information.
        
        Args:
            record: Log record to filter
            
        Returns:
            True to allow the record to be logged
        """
        # Redact sensitive data from message
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        
        # Redact sensitive data from args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact_value(v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact_value(arg) for arg in record.args)
        
        return True
    
    def _redact_value(self, value):
        """Redact sensitive values in log arguments."""
        if isinstance(value, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        return value


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(
    log_file: str = "app.log",
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure application logging with file rotation and sensitive data filtering.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10 MB)
        backup_count: Number of backup log files to keep (default: 5)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("discord_message_helper")
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(SensitiveDataFilter())
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(simple_formatter)
    console_handler.addFilter(SensitiveDataFilter())
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (default: uses root application logger)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"discord_message_helper.{name}")
    return logging.getLogger("discord_message_helper")


# ============================================================================
# Error Message Formatting
# ============================================================================

def format_error_message(
    error: Exception,
    user_friendly: bool = True,
    include_traceback: bool = False
) -> str:
    """
    Format error message for display or logging.
    
    Args:
        error: Exception to format
        user_friendly: If True, return user-friendly message; if False, include technical details
        include_traceback: If True, include full traceback (for logging)
        
    Returns:
        Formatted error message
    """
    if isinstance(error, AppError):
        if user_friendly:
            return error.format_message()
        else:
            msg = f"{error.__class__.__name__}: {error.message}"
            if error.details:
                msg += f"\nDetails: {error.details}"
            return msg
    else:
        if user_friendly:
            return f"An unexpected error occurred: {str(error)}"
        else:
            return f"{error.__class__.__name__}: {str(error)}"


def categorize_network_error(error: Exception) -> str:
    """
    Categorize network errors into connection, authentication, or server errors.
    
    This function implements Property 15: Network error categorization.
    
    Args:
        error: Network-related exception
        
    Returns:
        Error category: "connection", "authentication", or "server"
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Authentication errors
    auth_keywords = ['auth', 'unauthorized', '401', '403', 'forbidden', 'credentials']
    if any(keyword in error_str or keyword in error_type for keyword in auth_keywords):
        return "authentication"
    
    # Server errors
    server_keywords = ['500', '502', '503', '504', 'server error', 'internal server', 'bad gateway']
    if any(keyword in error_str or keyword in error_type for keyword in server_keywords):
        return "server"
    
    # Connection errors (default)
    return "connection"


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[str] = None,
    extra_data: Optional[dict] = None
) -> None:
    """
    Log an error with context and ensure it's persisted to the log file.
    
    This function implements Property 16: Error logging persistence.
    
    Args:
        logger: Logger instance to use
        error: Exception to log
        context: Additional context about where/when the error occurred
        extra_data: Additional data to include in the log
    """
    # Build log message
    message_parts = []
    
    if context:
        message_parts.append(f"Context: {context}")
    
    message_parts.append(f"Error: {format_error_message(error, user_friendly=False)}")
    
    if extra_data:
        message_parts.append(f"Extra data: {extra_data}")
    
    log_message = " | ".join(message_parts)
    
    # Log with appropriate level
    if isinstance(error, ValidationError):
        logger.warning(log_message, exc_info=False)
    else:
        logger.error(log_message, exc_info=True)
    
    # Ensure the log is flushed to disk
    for handler in logger.handlers:
        handler.flush()
