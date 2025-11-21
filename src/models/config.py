"""Configuration data models for application settings."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmailConfig:
    """Email SMTP configuration.
    
    Attributes:
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        email_address: Sender email address
        password: Email password (stored encrypted)
        use_tls: Whether to use TLS encryption
    """
    smtp_server: str
    smtp_port: int
    email_address: str
    password: str  # Encrypted
    use_tls: bool


@dataclass
class AppConfig:
    """Application configuration settings.
    
    Attributes:
        last_messages_directory: Last used messages directory path
        last_save_directory: Last used save directory path
        excluded_channels: List of channel IDs to exclude from processing
        email_config: Email SMTP configuration (optional)
        theme: UI theme name
    """
    last_messages_directory: Optional[str]
    last_save_directory: Optional[str]
    excluded_channels: List[str]
    email_config: Optional[EmailConfig]
    theme: str


@dataclass
class EnvConfig:
    """Configuration loaded from .env file.
    
    Attributes:
        discord_client_id: Discord OAuth client ID
        discord_client_secret: Discord OAuth client secret
        discord_redirect_uri: OAuth redirect URI
        discord_scope: OAuth scope (e.g., "identify email")
    """
    discord_client_id: str
    discord_client_secret: str
    discord_redirect_uri: str
    discord_scope: str
