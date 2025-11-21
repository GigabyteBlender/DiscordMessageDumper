"""Main entry point for Discord Message Delete Helper application.

This module initializes the Qt application, loads configuration,
initializes all services, and creates the main window.
"""

import sys
import logging
import traceback
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt

from src.services.config_service import ConfigService
from src.services.auth_service import AuthService
from src.services.message_service import MessageService
from src.services.email_service import EmailService
from src.ui.main_window import MainWindow
from src.ui.styles.theme import apply_theme
from src.utils.migration import check_and_run_migrations


def setup_logging():
    """Configure application logging.
    
    Sets up logging to both file and console with appropriate formatting
    and log levels. Sensitive data is filtered from logs.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Set up file handler with rotation
    log_file = log_dir / "app.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add sensitive data filter
    class SensitiveDataFilter(logging.Filter):
        """Filter to redact sensitive information from logs."""
        
        def filter(self, record):
            """Filter log record to remove sensitive data.
            
            Args:
                record: LogRecord to filter
                
            Returns:
                True to allow the record, False to block it
            """
            import re
            
            # Convert message to string
            msg = str(record.msg)
            
            # Redact patterns that look like tokens or passwords
            patterns = [
                (r'token["\']?\s*[:=]\s*["\']?[\w\-\.]+', 'token=***REDACTED***'),
                (r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', 'password=***REDACTED***'),
                (r'access_token["\']?\s*[:=]\s*["\']?[\w\-\.]+', 'access_token=***REDACTED***'),
                (r'client_secret["\']?\s*[:=]\s*["\']?[\w\-\.]+', 'client_secret=***REDACTED***'),
                (r'Bearer\s+[\w\-\.]+', 'Bearer ***REDACTED***'),
            ]
            
            for pattern, replacement in patterns:
                msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
            
            record.msg = msg
            return True
    
    # Add filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(SensitiveDataFilter())
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for uncaught exceptions.
    
    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    # Don't handle KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the exception
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Show error dialog to user
    error_msg = f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}"
    
    try:
        # Try to show Qt message box if possible
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Application Error")
        msg_box.setText("An unexpected error occurred.")
        msg_box.setInformativeText(error_msg)
        msg_box.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        msg_box.exec()
    except:
        # If Qt is not available, print to console
        print(error_msg, file=sys.stderr)
        traceback.print_exception(exc_type, exc_value, exc_traceback)


def initialize_services():
    """Initialize all application services.
    
    Returns:
        tuple: (config_service, auth_service, message_service, email_service)
        
    Raises:
        ValueError: If environment configuration is missing or invalid
        Exception: If service initialization fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration service
        logger.info("Initializing configuration service...")
        config_service = ConfigService()
        
        # Load environment configuration
        logger.info("Loading environment configuration...")
        env_config = config_service.load_env_config()
        logger.info("Environment configuration loaded successfully")
        
        # Initialize authentication service
        logger.info("Initializing authentication service...")
        auth_service = AuthService(env_config)
        logger.info("Authentication service initialized")
        
        # Initialize message service
        logger.info("Initializing message service...")
        message_service = MessageService()
        logger.info("Message service initialized")
        
        # Initialize email service
        logger.info("Initializing email service...")
        email_service = EmailService()
        logger.info("Email service initialized")
        
        return config_service, auth_service, message_service, email_service
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


def main():
    """Main application entry point.
    
    Initializes Qt application, loads configuration, creates services,
    and shows the main window.
    
    Returns:
        int: Application exit code
    """
    # Set up logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Discord Message Delete Helper - Starting")
    logger.info("="*60)
    
    # Check for and run any necessary migrations
    logger.info("Checking for data migrations...")
    try:
        check_and_run_migrations()
    except Exception as e:
        logger.warning(f"Migration check failed: {e}")
        # Continue anyway - migrations are not critical for startup
    
    # Install global exception handler
    sys.excepthook = handle_exception
    
    try:
        # Create Qt application
        logger.info("Creating Qt application...")
        app = QApplication(sys.argv)
        app.setApplicationName("Discord Message Delete Helper")
        app.setOrganizationName("Discord Message Helper")
        
        # Initialize config service first to load theme preference
        logger.info("Initializing configuration service...")
        config_service = ConfigService()
        
        # Load theme preference
        try:
            app_config = config_service.load_app_config()
            theme = app_config.theme
            logger.info(f"Loading theme: {theme}")
        except Exception as e:
            logger.warning(f"Could not load theme preference: {e}, using default")
            theme = 'dark'
        
        # Apply theme
        logger.info("Applying application theme...")
        apply_theme(app, theme)
        
        # Initialize remaining services
        logger.info("Initializing services...")
        
        # Load environment configuration
        logger.info("Loading environment configuration...")
        env_config = config_service.load_env_config()
        logger.info("Environment configuration loaded successfully")
        
        # Initialize authentication service
        logger.info("Initializing authentication service...")
        auth_service = AuthService(env_config)
        logger.info("Authentication service initialized")
        
        # Initialize message service
        logger.info("Initializing message service...")
        message_service = MessageService()
        logger.info("Message service initialized")
        
        # Initialize email service
        logger.info("Initializing email service...")
        email_service = EmailService()
        logger.info("Email service initialized")
        
        # Create main window
        logger.info("Creating main window...")
        main_window = MainWindow(
            auth_service=auth_service,
            message_service=message_service,
            email_service=email_service,
            config_service=config_service
        )
        
        # Show main window
        logger.info("Showing main window...")
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run application event loop
        exit_code = app.exec()
        
        logger.info(f"Application exiting with code {exit_code}")
        return exit_code
    
    except ValueError as e:
        # Configuration error - show user-friendly message
        logger.error(f"Configuration error: {e}")
        
        error_msg = (
            "Configuration Error\n\n"
            f"{str(e)}\n\n"
            "Please ensure you have:\n"
            "1. Created a .env file (copy from .env.example)\n"
            "2. Added your Discord OAuth credentials\n"
            "3. Configured the redirect URI in Discord Developer Portal"
        )
        
        # Try to show error dialog
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Configuration Error")
            msg_box.setText("Failed to load configuration")
            msg_box.setInformativeText(error_msg)
            msg_box.exec()
        except:
            print(error_msg, file=sys.stderr)
        
        return 1
    
    except Exception as e:
        # Unexpected error
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        
        error_msg = (
            f"Fatal Error\n\n"
            f"An unexpected error occurred during startup:\n\n"
            f"{type(e).__name__}: {str(e)}\n\n"
            f"Please check the log file for details."
        )
        
        # Try to show error dialog
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Fatal Error")
            msg_box.setText("Application failed to start")
            msg_box.setInformativeText(error_msg)
            msg_box.exec()
        except:
            print(error_msg, file=sys.stderr)
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
