"""Configuration service for managing application settings."""

import json
import os
from typing import Optional
from dotenv import load_dotenv

from src.models.config import EnvConfig, AppConfig, EmailConfig
from src.utils.crypto import encrypt_password, decrypt_password


class ConfigService:
    """Service for loading and saving application configuration.
    
    Handles both environment variables (.env file) and application
    configuration (config.json file) with encryption for sensitive data.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the configuration service.
        
        Args:
            config_file: Path to the application configuration file
        """
        self.config_file = config_file
    
    def load_env_config(self) -> EnvConfig:
        """Load environment configuration from .env file.
        
        Returns:
            EnvConfig: Environment configuration object
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Load .env file
        load_dotenv()
        
        # Get required environment variables
        client_id = os.getenv('DISCORD_CLIENT_ID')
        client_secret = os.getenv('DISCORD_CLIENT_SECRET')
        redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
        scope = os.getenv('DISCORD_SCOPE')
        
        # Validate required fields
        if not client_id:
            raise ValueError("DISCORD_CLIENT_ID is required in .env file")
        if not client_secret:
            raise ValueError("DISCORD_CLIENT_SECRET is required in .env file")
        if not redirect_uri:
            raise ValueError("DISCORD_REDIRECT_URI is required in .env file")
        if not scope:
            raise ValueError("DISCORD_SCOPE is required in .env file")
        
        return EnvConfig(
            discord_client_id=client_id,
            discord_client_secret=client_secret,
            discord_redirect_uri=redirect_uri,
            discord_scope=scope
        )
    
    def load_app_config(self) -> AppConfig:
        """Load application configuration from config.json.
        
        If the file doesn't exist, returns default configuration.
        Decrypts sensitive fields (email password) if present.
        
        Returns:
            AppConfig: Application configuration object
        """
        if not os.path.exists(self.config_file):
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Parse email config if present
            email_config = None
            if data.get('email_config'):
                email_data = data['email_config']
                
                # Decrypt password if present
                password = email_data.get('password', '')
                if password:
                    try:
                        password = decrypt_password(password)
                    except Exception:
                        # If decryption fails, treat as empty
                        password = ''
                
                email_config = EmailConfig(
                    smtp_server=email_data.get('smtp_server', ''),
                    smtp_port=email_data.get('smtp_port', 587),
                    email_address=email_data.get('email_address', ''),
                    password=password,
                    use_tls=email_data.get('use_tls', True)
                )
            
            return AppConfig(
                last_messages_directory=data.get('last_messages_directory'),
                last_save_directory=data.get('last_save_directory'),
                excluded_channels=data.get('excluded_channels', []),
                email_config=email_config,
                theme=data.get('theme', 'dark')
            )
        except (json.JSONDecodeError, KeyError) as e:
            # If file is corrupted, return default config
            return self._get_default_config()
    
    def save_app_config(self, config: AppConfig) -> None:
        """Save application configuration to config.json.
        
        Encrypts sensitive fields (email password) before saving.
        Validates configuration before saving.
        
        Args:
            config: Application configuration to save
            
        Raises:
            ValueError: If configuration validation fails
        """
        # Validate configuration
        self._validate_config(config)
        
        # Prepare data for serialization
        data = {
            'last_messages_directory': config.last_messages_directory,
            'last_save_directory': config.last_save_directory,
            'excluded_channels': config.excluded_channels,
            'theme': config.theme
        }
        
        # Add email config if present
        if config.email_config:
            email_data = {
                'smtp_server': config.email_config.smtp_server,
                'smtp_port': config.email_config.smtp_port,
                'email_address': config.email_config.email_address,
                'use_tls': config.email_config.use_tls
            }
            
            # Encrypt password if present
            if config.email_config.password:
                email_data['password'] = encrypt_password(config.email_config.password)
            else:
                email_data['password'] = ''
            
            data['email_config'] = email_data
        else:
            data['email_config'] = None
        
        # Write to file
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_default_config(self) -> AppConfig:
        """Generate default application configuration.
        
        Returns:
            AppConfig: Default configuration object
        """
        return AppConfig(
            last_messages_directory=None,
            last_save_directory=None,
            excluded_channels=[],
            email_config=None,
            theme='dark'
        )
    
    def _validate_config(self, config: AppConfig) -> None:
        """Validate application configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate theme
        valid_themes = ['dark', 'light']
        if config.theme not in valid_themes:
            raise ValueError(f"Invalid theme: {config.theme}. Must be one of {valid_themes}")
        
        # Validate excluded channels (must be list of strings)
        if not isinstance(config.excluded_channels, list):
            raise ValueError("excluded_channels must be a list")
        
        for channel_id in config.excluded_channels:
            if not isinstance(channel_id, str):
                raise ValueError("All channel IDs must be strings")
        
        # Validate email config if present
        if config.email_config:
            self._validate_email_config(config.email_config)
    
    def _validate_email_config(self, email_config: EmailConfig) -> None:
        """Validate email configuration.
        
        Args:
            email_config: Email configuration to validate
            
        Raises:
            ValueError: If email configuration is invalid
        """
        # Validate SMTP server
        if not email_config.smtp_server or not email_config.smtp_server.strip():
            raise ValueError("SMTP server cannot be empty")
        
        # Validate SMTP port
        if not isinstance(email_config.smtp_port, int):
            raise ValueError("SMTP port must be an integer")
        
        if email_config.smtp_port < 1 or email_config.smtp_port > 65535:
            raise ValueError("SMTP port must be between 1 and 65535")
        
        # Validate email address
        if not email_config.email_address or not email_config.email_address.strip():
            raise ValueError("Email address cannot be empty")
        
        # Basic email validation
        if '@' not in email_config.email_address:
            raise ValueError("Invalid email address format")
        
        # Validate password
        if not email_config.password or not email_config.password.strip():
            raise ValueError("Email password cannot be empty")
        
        # Validate use_tls
        if not isinstance(email_config.use_tls, bool):
            raise ValueError("use_tls must be a boolean")
