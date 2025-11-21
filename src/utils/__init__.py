"""Utility functions and helpers"""

from .crypto import encrypt_password, decrypt_password, get_encryption_key
from .validators import (
    validate_directory_path,
    validate_email_address,
    sanitize_path,
    validate_smtp_port
)
from .errors import (
    AppError,
    AuthenticationError,
    FileSystemError,
    EmailError,
    ValidationError,
    NetworkError,
    SensitiveDataFilter,
    setup_logging,
    get_logger,
    format_error_message,
    categorize_network_error,
    log_error,
)
from .migration import (
    migrate_config_to_env,
    migrate_user_data,
    check_and_run_migrations,
    create_backup,
    rollback_migration,
)

__all__ = [
    'encrypt_password',
    'decrypt_password',
    'get_encryption_key',
    'validate_directory_path',
    'validate_email_address',
    'sanitize_path',
    'validate_smtp_port',
    'AppError',
    'AuthenticationError',
    'FileSystemError',
    'EmailError',
    'ValidationError',
    'NetworkError',
    'SensitiveDataFilter',
    'setup_logging',
    'get_logger',
    'format_error_message',
    'categorize_network_error',
    'log_error',
    'migrate_config_to_env',
    'migrate_user_data',
    'check_and_run_migrations',
    'create_backup',
    'rollback_migration',
]
