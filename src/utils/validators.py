"""Input validation utilities for user inputs and configuration."""

import os
import re
from pathlib import Path
from typing import Tuple


def validate_directory_path(path: str) -> Tuple[bool, str]:
    """Validate that a directory path exists and is accessible.
    
    Args:
        path: Directory path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if directory is valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not path:
        return False, "Directory path cannot be empty"
    
    if not isinstance(path, str):
        return False, "Directory path must be a string"
    
    # Check for path traversal attempts
    is_safe, error = sanitize_path(path)
    if not is_safe:
        return False, error
    
    try:
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, f"Directory does not exist: {path}"
        
        if not path_obj.is_dir():
            return False, f"Path is not a directory: {path}"
        
        # Check if directory is readable
        if not os.access(path, os.R_OK):
            return False, f"Directory is not readable: {path}"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid directory path: {str(e)}"


def validate_email_address(email: str) -> Tuple[bool, str]:
    """Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if email is valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not email:
        return False, "Email address cannot be empty"
    
    if not isinstance(email, str):
        return False, "Email address must be a string"
    
    # Basic email regex pattern
    # Matches: user@domain.com, user.name@domain.co.uk, etc.
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email address format"
    
    # Additional checks
    if len(email) > 254:  # RFC 5321
        return False, "Email address is too long (max 254 characters)"
    
    local_part, domain = email.rsplit('@', 1)
    
    if len(local_part) > 64:  # RFC 5321
        return False, "Email local part is too long (max 64 characters)"
    
    if len(domain) > 253:
        return False, "Email domain is too long (max 253 characters)"
    
    return True, ""


def sanitize_path(path: str) -> Tuple[bool, str]:
    """Sanitize a file path to prevent directory traversal attacks.
    
    Args:
        path: File path to sanitize
        
    Returns:
        Tuple of (is_safe, error_message)
        - is_safe: True if path is safe, False if it contains traversal patterns
        - error_message: Empty string if safe, error description if unsafe
    """
    if not path:
        return False, "Path cannot be empty"
    
    if not isinstance(path, str):
        return False, "Path must be a string"
    
    # Normalize the path to resolve any .. or . components
    try:
        normalized = os.path.normpath(path)
        
        # Check for directory traversal patterns
        dangerous_patterns = [
            '..',      # Parent directory
            '/../',    # Unix-style traversal
            '\\..\\',  # Windows-style traversal
            '../',     # Unix-style relative
            '..\\',    # Windows-style relative
        ]
        
        for pattern in dangerous_patterns:
            if pattern in path or pattern in normalized:
                return False, f"Path contains directory traversal pattern: {pattern}"
        
        # Additional check: ensure normalized path doesn't go up from current directory
        # when it's a relative path
        if not os.path.isabs(path):
            # For relative paths, check if normpath introduces ..
            if normalized.startswith('..'):
                return False, "Path attempts to traverse above current directory"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def validate_smtp_port(port: int) -> Tuple[bool, str]:
    """Validate an SMTP port number.
    
    Args:
        port: Port number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if port is valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not isinstance(port, int):
        return False, "Port must be an integer"
    
    # Valid port range: 1-65535
    if port < 1 or port > 65535:
        return False, f"Port must be between 1 and 65535, got {port}"
    
    # Common SMTP ports for reference (not enforced, just informational)
    common_smtp_ports = [25, 465, 587, 2525]
    
    # Warn about privileged ports (< 1024) but don't reject
    if port < 1024 and port not in common_smtp_ports:
        # Still valid, but might require elevated privileges
        pass
    
    return True, ""
