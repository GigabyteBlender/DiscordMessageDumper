"""Email service for generating and sending deletion request emails."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Callable, Optional
import os

from src.models.user import User
from src.models.message_data import MessageExport
from src.models.config import EmailConfig

logger = logging.getLogger(__name__)


# Email provider presets
EMAIL_PRESETS = {
    'Gmail': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'note': 'Requires app-specific password'
    },
    'Outlook': {
        'smtp_server': 'smtp-mail.outlook.com',
        'smtp_port': 587,
        'use_tls': True,
    },
    'Yahoo': {
        'smtp_server': 'smtp.mail.yahoo.com',
        'smtp_port': 587,
        'use_tls': True,
    },
    'Custom': {
        'smtp_server': '',
        'smtp_port': 587,
        'use_tls': True,
    }
}


class EmailService:
    """Service for generating and sending deletion request emails.
    
    This service handles:
    - Email template generation with user and message export data
    - SMTP configuration validation
    - Email sending with attachment support
    - Support for common email providers (Gmail, Outlook, Yahoo, custom)
    - Error handling for email operations
    """
    
    def __init__(self):
        """Initialize the email service."""
        self.logger = logging.getLogger(__name__)
    
    def generate_email_template(self, user: User, export: MessageExport) -> str:
        """Generate a formatted email template for Discord deletion request.
        
        Args:
            user: Authenticated Discord user
            export: Message export data containing channel and message information
            
        Returns:
            Formatted email body as a string
            
        Validates: Requirements 5.1, 5.2, 5.3
        """
        template = f"""Subject: Request for Deletion of Discord Messages

Dear Discord Support Team,

I am writing to formally request the deletion of my Discord messages from your servers. Below are my account details:

- Discord Username: {user.username}
- User ID: {user.id}
- Email: {user.email}

I have attached a file containing {export.total_messages} message IDs across {export.total_channels} channels that I would like to be deleted from your servers. These messages are organized by channel ID for your convenience.

I understand that this process may take some time, and I appreciate your assistance in this matter.

Thank you for your attention to this request.

Best regards,
{user.username}
"""
        return template
    
    def validate_smtp_config(self, config: EmailConfig) -> bool:
        """Validate SMTP configuration.
        
        Args:
            config: Email configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
            
        Validates: Requirements 5.4
        """
        # Check that all required fields are non-empty
        if not config.smtp_server or not config.smtp_server.strip():
            self.logger.error("SMTP server is empty")
            return False
        
        if not config.email_address or not config.email_address.strip():
            self.logger.error("Email address is empty")
            return False
        
        if not config.password or not config.password.strip():
            self.logger.error("Password is empty")
            return False
        
        # Validate port is a valid number in reasonable range
        if not isinstance(config.smtp_port, int):
            self.logger.error(f"SMTP port must be an integer, got {type(config.smtp_port)}")
            return False
        
        if config.smtp_port < 1 or config.smtp_port > 65535:
            self.logger.error(f"SMTP port {config.smtp_port} is out of valid range (1-65535)")
            return False
        
        return True
    
    def send_deletion_request(
        self,
        config: EmailConfig,
        user: User,
        attachment_path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Send deletion request email to Discord Support.
        
        Args:
            config: Email SMTP configuration
            user: Authenticated Discord user
            attachment_path: Path to the message export file to attach
            progress_callback: Optional callback for progress updates (message, percentage)
            
        Returns:
            True if email was sent successfully, False otherwise
            
        Raises:
            ValueError: If configuration is invalid or attachment doesn't exist
            smtplib.SMTPException: If email sending fails
            
        Validates: Requirements 5.5, 5.8
        """
        # Validate configuration
        if not self.validate_smtp_config(config):
            raise ValueError("Invalid SMTP configuration")
        
        # Check attachment exists
        if not os.path.exists(attachment_path):
            raise ValueError(f"Attachment file not found: {attachment_path}")
        
        if progress_callback:
            progress_callback("Preparing email...", 10)
        
        try:
            # Load message export to get statistics
            # We need to parse the attachment to get message counts
            # For now, we'll create a simple export object
            # In a real scenario, this would be passed in or loaded
            from datetime import datetime
            from src.models.message_data import MessageExport, ChannelMessages
            
            # Parse the attachment file to get message counts
            total_messages = 0
            total_channels = 0
            
            try:
                with open(attachment_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Count channels (lines starting with "Channel ID:")
                    for line in content.split('\n'):
                        if line.startswith('Channel ID:'):
                            total_channels += 1
                        elif line.strip() and not line.startswith('Channel ID:') and not line.startswith('---'):
                            # Count message IDs (non-empty lines that aren't headers)
                            total_messages += 1
            except Exception as e:
                self.logger.warning(f"Could not parse attachment for statistics: {e}")
                # Use default values if parsing fails
                total_messages = 0
                total_channels = 0
            
            export = MessageExport(
                channels=[],
                total_messages=total_messages,
                total_channels=total_channels,
                export_date=datetime.now()
            )
            
            # Generate email template
            email_body = self.generate_email_template(user, export)
            
            if progress_callback:
                progress_callback("Creating email message...", 20)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config.email_address
            msg['To'] = 'support@discord.com'
            msg['Subject'] = 'Request for Deletion of Discord Messages'
            
            # Attach body
            msg.attach(MIMEText(email_body, 'plain'))
            
            if progress_callback:
                progress_callback("Attaching file...", 40)
            
            # Attach file
            attachment_filename = os.path.basename(attachment_path)
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_filename}'
                )
                msg.attach(part)
            
            if progress_callback:
                progress_callback("Connecting to SMTP server...", 60)
            
            # Connect to SMTP server and send
            if config.use_tls:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port)
            
            if progress_callback:
                progress_callback("Authenticating...", 70)
            
            server.login(config.email_address, config.password)
            
            if progress_callback:
                progress_callback("Sending email...", 80)
            
            text = msg.as_string()
            server.sendmail(config.email_address, 'support@discord.com', text)
            server.quit()
            
            if progress_callback:
                progress_callback("Email sent successfully!", 100)
            
            self.logger.info(f"Deletion request email sent successfully to support@discord.com")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            raise smtplib.SMTPException(f"Authentication failed. Please check your email and password.") from e
        
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"Could not connect to SMTP server: {e}")
            raise smtplib.SMTPException(f"Could not connect to {config.smtp_server}:{config.smtp_port}. Please check your server settings.") from e
        
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error occurred: {e}")
            raise
        
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            raise smtplib.SMTPException(f"Failed to send email: {str(e)}") from e
    
    @staticmethod
    def get_provider_preset(provider_name: str) -> dict:
        """Get SMTP configuration preset for a common email provider.
        
        Args:
            provider_name: Name of the email provider (Gmail, Outlook, Yahoo, Custom)
            
        Returns:
            Dictionary containing SMTP configuration preset
            
        Raises:
            ValueError: If provider name is not recognized
        """
        if provider_name not in EMAIL_PRESETS:
            raise ValueError(f"Unknown email provider: {provider_name}. Available: {', '.join(EMAIL_PRESETS.keys())}")
        
        return EMAIL_PRESETS[provider_name].copy()
