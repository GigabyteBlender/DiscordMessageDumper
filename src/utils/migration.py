"""Migration utilities for upgrading from old application structure to new architecture.

This module provides functions to migrate configuration and user data from the old
application format (config.py, data.txt) to the new format (.env, config.json).

The migration process:
1. Detects old configuration files (config.py, data.txt)
2. Creates timestamped backups of old files
3. Migrates data to new format (.env, user_data.json)
4. Renames old files with .migrated extension
5. Logs all migration activities

Migration is automatically triggered on application startup via check_and_run_migrations().
If migrations fail, the application continues to start (migrations are not critical).

Example usage:
    # Automatic migration on startup (already integrated in main.py)
    from src.utils.migration import check_and_run_migrations
    check_and_run_migrations()
    
    # Manual migration
    from src.utils.migration import migrate_config_to_env, migrate_user_data
    success, message = migrate_config_to_env()
    success, message = migrate_user_data()
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional, Tuple

from src.models.user import User
from src.models.config import AppConfig


def create_backup(file_path: str) -> Optional[str]:
    """Create a backup of a file before migration.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file if successful, None otherwise
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Warning: Failed to create backup of {file_path}: {e}")
        return None


def migrate_config_to_env() -> Tuple[bool, str]:
    """Migrate from config.py to .env file.
    
    This function attempts to import the old config.py file and extract
    Discord OAuth credentials, then writes them to a .env file.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if config.py exists
    if not os.path.exists('config.py'):
        return False, "No config.py file found - migration not needed"
    
    # Check if .env already exists
    if os.path.exists('.env'):
        return False, ".env file already exists - skipping config migration"
    
    try:
        # Create backup of config.py
        create_backup('config.py')
        
        # Import the old config module
        import importlib.util
        spec = importlib.util.spec_from_file_location("old_config", "config.py")
        old_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old_config)
        
        # Extract configuration values
        client_id = getattr(old_config, 'CLIENT_ID', '')
        client_secret = getattr(old_config, 'CLIENT_SECRET', '')
        redirect_uri = getattr(old_config, 'REDIRECT_URI', 'http://localhost:8000/callback')
        scope = getattr(old_config, 'SCOPE', 'identify email')
        
        # Validate required fields
        if not client_id or not client_secret:
            return False, "config.py is missing required fields (CLIENT_ID or CLIENT_SECRET)"
        
        # Create .env file
        env_content = f"""# Discord OAuth Configuration
# Migrated from config.py on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

DISCORD_CLIENT_ID={client_id}
DISCORD_CLIENT_SECRET={client_secret}
DISCORD_REDIRECT_URI={redirect_uri}
DISCORD_SCOPE={scope}
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        # Rename old config.py to indicate it's been migrated
        os.rename('config.py', 'config.py.migrated')
        
        return True, "Successfully migrated config.py to .env"
        
    except Exception as e:
        return False, f"Failed to migrate config.py: {e}"


def migrate_user_data() -> Tuple[bool, str]:
    """Migrate from data.txt to new user data storage format.
    
    This function reads user data from the old data.txt file and stores it
    in the new config.json format using the ConfigService.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if data.txt exists
    if not os.path.exists('data.txt'):
        return False, "No data.txt file found - migration not needed"
    
    try:
        # Create backup of data.txt
        create_backup('data.txt')
        
        # Read user data from data.txt
        with open('data.txt', 'r') as f:
            lines = f.readlines()
        
        # Validate data format
        if len(lines) < 3:
            return False, "data.txt has invalid format (missing required fields)"
        
        # Parse user data
        user_id = lines[0].strip()
        user_email = lines[1].strip()
        user_username = lines[2].strip()
        user_verified = lines[3].strip().lower() == 'true' if len(lines) > 3 else False
        
        # Validate required fields
        if not user_id or not user_email or not user_username:
            return False, "data.txt contains empty required fields"
        
        # Create User object
        user = User(
            id=user_id,
            username=user_username,
            email=user_email,
            verified=user_verified,
            access_token=None  # Token will need to be re-authenticated
        )
        
        # Import here to avoid circular import
        from src.services.config_service import ConfigService
        
        # Load or create app config
        config_service = ConfigService()
        try:
            app_config = config_service.load_app_config()
        except Exception:
            # If loading fails, use default config
            app_config = config_service._get_default_config()
        
        # Save the config (this ensures config.json exists)
        config_service.save_app_config(app_config)
        
        # Store user data in a separate user_data.json file
        # (The new architecture doesn't store user data in config.json,
        # but we'll preserve it for reference)
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'verified': user.verified,
            'migrated_from': 'data.txt',
            'migration_date': datetime.now().isoformat()
        }
        
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        
        # Rename old data.txt to indicate it's been migrated
        os.rename('data.txt', 'data.txt.migrated')
        
        return True, f"Successfully migrated user data for {user_username} to user_data.json"
        
    except Exception as e:
        return False, f"Failed to migrate user data: {e}"


def check_and_run_migrations() -> None:
    """Check for old data files and run migrations if needed.
    
    This function should be called on application startup to automatically
    detect and migrate old configuration and user data files.
    """
    print("Checking for data migrations...")
    
    migrations_run = []
    
    # Try to migrate config.py to .env
    success, message = migrate_config_to_env()
    if success:
        migrations_run.append("config.py → .env")
        print(f"✓ {message}")
    elif "not needed" not in message and "already exists" not in message:
        print(f"✗ {message}")
    
    # Try to migrate data.txt to new format
    success, message = migrate_user_data()
    if success:
        migrations_run.append("data.txt → user_data.json")
        print(f"✓ {message}")
    elif "not needed" not in message:
        print(f"✗ {message}")
    
    # Summary
    if migrations_run:
        print(f"\nMigrations completed: {', '.join(migrations_run)}")
        print("Old files have been renamed with .migrated extension")
        print("Backup files have been created with timestamps")
    else:
        print("No migrations needed - application is up to date")


def rollback_migration(backup_file: str) -> Tuple[bool, str]:
    """Rollback a migration by restoring from backup.
    
    Args:
        backup_file: Path to the backup file to restore
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not os.path.exists(backup_file):
        return False, f"Backup file not found: {backup_file}"
    
    try:
        # Extract original filename from backup
        if '.backup_' in backup_file:
            original_file = backup_file.split('.backup_')[0]
        else:
            return False, "Invalid backup file format"
        
        # Restore the backup
        shutil.copy2(backup_file, original_file)
        
        return True, f"Successfully restored {original_file} from backup"
        
    except Exception as e:
        return False, f"Failed to rollback migration: {e}"
