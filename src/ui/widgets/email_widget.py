"""Email widget for generating and sending deletion request emails.

This widget provides a UI for:
- Previewing the email template
- Configuring SMTP settings with provider presets
- Testing SMTP connection
- Sending deletion request emails with attachments
"""

from typing import Optional
import threading
import smtplib

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QTextEdit, QComboBox, QCheckBox, QSpinBox,
        QGroupBox, QScrollArea
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QTextEdit, QComboBox, QCheckBox, QSpinBox,
        QGroupBox, QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont

from src.services.email_service import EmailService, EMAIL_PRESETS
from src.services.config_service import ConfigService
from src.models.user import User
from src.models.message_data import MessageExport
from src.models.config import EmailConfig


class EmailWidget(QWidget):
    """Widget for email generation and sending.
    
    Provides a modern interface for:
    - Previewing deletion request email template
    - Configuring SMTP settings with provider presets
    - Testing SMTP connection
    - Sending emails with message export attachments
    
    Signals:
        email_sent: Emitted when email is sent successfully
        email_failed: Emitted when email sending fails (str: error_message)
    """
    
    email_sent = Signal()
    email_failed = Signal(str)
    
    def __init__(
        self,
        email_service: EmailService,
        config_service: ConfigService,
        parent: Optional[QWidget] = None
    ):
        """Initialize the email widget.
        
        Args:
            email_service: EmailService instance for email operations
            config_service: ConfigService instance for loading/saving config
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.email_service = email_service
        self.config_service = config_service
        self._sending_thread: Optional[threading.Thread] = None
        self._current_user: Optional[User] = None
        self._current_export: Optional[MessageExport] = None
        self._attachment_path: Optional[str] = None
        
        self._init_ui()
        self._load_saved_config()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_layout.addWidget(scroll)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        # Content layout
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_label = QLabel("Email Deletion Request")
        header_label.setProperty("heading", True)
        layout.addWidget(header_label)
        
        # Email preview section
        preview_card = self._create_preview_section()
        layout.addWidget(preview_card)
        
        # SMTP configuration section
        smtp_card = self._create_smtp_section()
        layout.addWidget(smtp_card)
        
        # Attachment status section
        attachment_card = self._create_attachment_section()
        layout.addWidget(attachment_card)
        
        # Action buttons section
        buttons_layout = self._create_action_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_preview_section(self) -> QFrame:
        """Create the email preview section.
        
        Returns:
            QFrame: Frame containing email preview
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section label
        preview_label = QLabel("Email Preview")
        preview_font = QFont()
        preview_font.setPointSize(14)
        preview_font.setBold(True)
        preview_label.setFont(preview_font)
        layout.addWidget(preview_label)
        
        # Email preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(250)
        self.preview_text.setPlaceholderText(
            "Email preview will appear here once you authenticate and process messages..."
        )
        layout.addWidget(self.preview_text)
        
        return frame
    
    def _create_smtp_section(self) -> QFrame:
        """Create the SMTP configuration section.
        
        Returns:
            QFrame: Frame containing SMTP configuration
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section header with expand/collapse
        section_label = QLabel("SMTP Configuration")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_label.setFont(section_font)
        layout.addWidget(section_label)
        
        # Collapsible group box for SMTP settings
        self.smtp_group = QGroupBox()
        self.smtp_group.setCheckable(True)
        self.smtp_group.setChecked(False)  # Collapsed by default
        self.smtp_group.setTitle("")  # No title since we have label above
        
        smtp_layout = QVBoxLayout()
        smtp_layout.setSpacing(12)
        
        # Provider preset dropdown
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Email Provider:")
        provider_label.setMinimumWidth(120)
        provider_layout.addWidget(provider_label)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(EMAIL_PRESETS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        
        smtp_layout.addLayout(provider_layout)
        
        # SMTP Server
        server_layout = QHBoxLayout()
        server_label = QLabel("SMTP Server:")
        server_label.setMinimumWidth(120)
        server_layout.addWidget(server_label)
        
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.gmail.com")
        server_layout.addWidget(self.smtp_server_input)
        
        smtp_layout.addLayout(server_layout)
        
        # SMTP Port
        port_layout = QHBoxLayout()
        port_label = QLabel("SMTP Port:")
        port_label.setMinimumWidth(120)
        port_layout.addWidget(port_label)
        
        self.smtp_port_input = QSpinBox()
        self.smtp_port_input.setMinimum(1)
        self.smtp_port_input.setMaximum(65535)
        self.smtp_port_input.setValue(587)
        port_layout.addWidget(self.smtp_port_input)
        
        smtp_layout.addLayout(port_layout)
        
        # Email Address
        email_layout = QHBoxLayout()
        email_label = QLabel("Email Address:")
        email_label.setMinimumWidth(120)
        email_layout.addWidget(email_label)
        
        self.email_address_input = QLineEdit()
        self.email_address_input.setPlaceholderText("your.email@gmail.com")
        email_layout.addWidget(self.email_address_input)
        
        smtp_layout.addLayout(email_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setMinimumWidth(120)
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("App-specific password")
        password_layout.addWidget(self.password_input)
        
        smtp_layout.addLayout(password_layout)
        
        # Use TLS checkbox
        self.use_tls_checkbox = QCheckBox("Use TLS Encryption")
        self.use_tls_checkbox.setChecked(True)
        smtp_layout.addWidget(self.use_tls_checkbox)
        
        # Provider note
        self.provider_note_label = QLabel("")
        self.provider_note_label.setProperty("secondary", True)
        self.provider_note_label.setWordWrap(True)
        smtp_layout.addWidget(self.provider_note_label)
        
        self.smtp_group.setLayout(smtp_layout)
        layout.addWidget(self.smtp_group)
        
        return frame
    
    def _create_attachment_section(self) -> QFrame:
        """Create the attachment status section.
        
        Returns:
            QFrame: Frame containing attachment status
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Attachment label
        attachment_label = QLabel("Attachment")
        attachment_font = QFont()
        attachment_font.setPointSize(14)
        attachment_font.setBold(True)
        attachment_label.setFont(attachment_font)
        layout.addWidget(attachment_label)
        
        # Attachment status
        self.attachment_status_label = QLabel("No attachment selected")
        self.attachment_status_label.setProperty("secondary", True)
        layout.addWidget(self.attachment_status_label)
        
        return frame
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons layout.
        
        Returns:
            QHBoxLayout: Layout containing action buttons
        """
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Test Connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.setProperty("secondary", True)
        self.test_button.clicked.connect(self._on_test_connection_clicked)
        layout.addWidget(self.test_button)
        
        # Spacer
        layout.addStretch()
        
        # Send Email button
        self.send_button = QPushButton("Send Email")
        self.send_button.setProperty("success", True)
        self.send_button.clicked.connect(self._on_send_email_clicked)
        layout.addWidget(self.send_button)
        
        return layout
    
    def _load_saved_config(self) -> None:
        """Load saved email configuration from config service."""
        try:
            app_config = self.config_service.load_app_config()
            if app_config.email_config:
                email_config = app_config.email_config
                
                # Set SMTP settings
                self.smtp_server_input.setText(email_config.smtp_server)
                self.smtp_port_input.setValue(email_config.smtp_port)
                self.email_address_input.setText(email_config.email_address)
                self.use_tls_checkbox.setChecked(email_config.use_tls)
                
                # Decrypt and set password
                try:
                    decrypted_password = self.config_service.decrypt_password(email_config.password)
                    self.password_input.setText(decrypted_password)
                except Exception:
                    # If decryption fails, leave password empty
                    pass
                
                # Try to detect provider
                self._detect_provider(email_config.smtp_server)
        except Exception as e:
            # If loading fails, just use defaults
            pass
    
    def _detect_provider(self, smtp_server: str) -> None:
        """Detect and set provider based on SMTP server.
        
        Args:
            smtp_server: SMTP server hostname
        """
        for provider_name, preset in EMAIL_PRESETS.items():
            if preset['smtp_server'] == smtp_server:
                self.provider_combo.setCurrentText(provider_name)
                return
        
        # If no match, set to Custom
        self.provider_combo.setCurrentText('Custom')
    
    def _on_provider_changed(self, provider_name: str) -> None:
        """Handle provider selection change.
        
        Args:
            provider_name: Selected provider name
        """
        try:
            preset = EMAIL_PRESETS[provider_name]
            
            # Update SMTP settings from preset
            if preset['smtp_server']:
                self.smtp_server_input.setText(preset['smtp_server'])
            
            self.smtp_port_input.setValue(preset['smtp_port'])
            self.use_tls_checkbox.setChecked(preset['use_tls'])
            
            # Show provider note if available
            if 'note' in preset:
                self.provider_note_label.setText(f"Note: {preset['note']}")
                self.provider_note_label.show()
            else:
                self.provider_note_label.hide()
        except KeyError:
            pass
    
    def _get_email_config(self) -> EmailConfig:
        """Get current email configuration from UI inputs.
        
        Returns:
            EmailConfig: Current email configuration
        """
        return EmailConfig(
            smtp_server=self.smtp_server_input.text().strip(),
            smtp_port=self.smtp_port_input.value(),
            email_address=self.email_address_input.text().strip(),
            password=self.password_input.text(),
            use_tls=self.use_tls_checkbox.isChecked()
        )
    
    def _save_email_config(self) -> None:
        """Save current email configuration to config service."""
        try:
            email_config = self._get_email_config()
            
            # Encrypt password before saving
            encrypted_password = self.config_service.encrypt_password(email_config.password)
            email_config.password = encrypted_password
            
            # Load current app config and update email config
            app_config = self.config_service.load_app_config()
            app_config.email_config = email_config
            self.config_service.save_app_config(app_config)
        except Exception as e:
            # Log error but don't block operation
            pass
    
    def _on_test_connection_clicked(self) -> None:
        """Handle test connection button click."""
        # Get email config
        email_config = self._get_email_config()
        
        # Validate configuration
        if not self.email_service.validate_smtp_config(email_config):
            QMessageBox.warning(
                self,
                "Invalid Configuration",
                "Please fill in all SMTP configuration fields:\n"
                "- SMTP Server\n"
                "- SMTP Port\n"
                "- Email Address\n"
                "- Password"
            )
            return
        
        # Disable button during test
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing...")
        
        # Test connection in background thread
        test_thread = threading.Thread(
            target=self._test_connection_thread,
            args=(email_config,),
            daemon=True
        )
        test_thread.start()
    
    def _test_connection_thread(self, config: EmailConfig) -> None:
        """Test SMTP connection in background thread.
        
        Args:
            config: Email configuration to test
        """
        try:
            # Try to connect and authenticate
            if config.use_tls:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=10)
            
            server.login(config.email_address, config.password)
            server.quit()
            
            # Success - update UI from main thread
            QTimer.singleShot(0, self._on_test_connection_success)
            
        except smtplib.SMTPAuthenticationError:
            QTimer.singleShot(0, lambda: self._on_test_connection_error(
                "Authentication failed. Please check your email address and password.\n\n"
                "For Gmail, you may need to use an app-specific password."
            ))
        except smtplib.SMTPConnectError:
            QTimer.singleShot(0, lambda: self._on_test_connection_error(
                f"Could not connect to {config.smtp_server}:{config.smtp_port}.\n\n"
                "Please check your server settings and internet connection."
            ))
        except Exception as e:
            QTimer.singleShot(0, lambda: self._on_test_connection_error(
                f"Connection test failed:\n{str(e)}"
            ))
    
    def _on_test_connection_success(self) -> None:
        """Handle successful connection test."""
        # Re-enable button
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")
        
        # Save configuration
        self._save_email_config()
        
        # Show success message
        QMessageBox.information(
            self,
            "Connection Successful",
            "SMTP connection test successful!\n\n"
            "Your email configuration has been saved."
        )
    
    def _on_test_connection_error(self, error_message: str) -> None:
        """Handle connection test error.
        
        Args:
            error_message: Error message to display
        """
        # Re-enable button
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")
        
        # Show error message
        QMessageBox.critical(
            self,
            "Connection Failed",
            error_message
        )
    
    def _on_send_email_clicked(self) -> None:
        """Handle send email button click."""
        # Validate prerequisites
        if not self._current_user:
            QMessageBox.warning(
                self,
                "Authentication Required",
                "Please authenticate with Discord before sending email."
            )
            return
        
        if not self._current_export:
            QMessageBox.warning(
                self,
                "No Messages Processed",
                "Please process messages before sending email."
            )
            return
        
        if not self._attachment_path:
            QMessageBox.warning(
                self,
                "No Attachment",
                "No message export file found. Please process messages first."
            )
            return
        
        # Get email config
        email_config = self._get_email_config()
        
        # Validate configuration
        if not self.email_service.validate_smtp_config(email_config):
            QMessageBox.warning(
                self,
                "Invalid Configuration",
                "Please configure SMTP settings before sending email."
            )
            # Expand SMTP section to show settings
            self.smtp_group.setChecked(True)
            return
        
        # Confirm send
        reply = QMessageBox.question(
            self,
            "Confirm Send",
            f"Send deletion request email to Discord Support?\n\n"
            f"From: {email_config.email_address}\n"
            f"To: support@discord.com\n"
            f"Attachment: {self._attachment_path}\n\n"
            f"Messages: {self._current_export.total_messages:,}\n"
            f"Channels: {self._current_export.total_channels}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable buttons during send
        self._set_buttons_enabled(False)
        self.send_button.setText("Sending...")
        
        # Send email in background thread
        self._sending_thread = threading.Thread(
            target=self._send_email_thread,
            args=(email_config,),
            daemon=True
        )
        self._sending_thread.start()
    
    def _send_email_thread(self, config: EmailConfig) -> None:
        """Send email in background thread.
        
        Args:
            config: Email configuration
        """
        try:
            # Send email with progress callback
            success = self.email_service.send_deletion_request(
                config=config,
                user=self._current_user,
                attachment_path=self._attachment_path,
                progress_callback=self._on_send_progress
            )
            
            if success:
                # Update UI from main thread
                QTimer.singleShot(0, self._on_send_success)
            else:
                QTimer.singleShot(0, lambda: self._on_send_error(
                    "Email sending failed for unknown reason."
                ))
        
        except ValueError as e:
            QTimer.singleShot(0, lambda: self._on_send_error(str(e)))
        
        except smtplib.SMTPException as e:
            QTimer.singleShot(0, lambda: self._on_send_error(str(e)))
        
        except Exception as e:
            QTimer.singleShot(0, lambda: self._on_send_error(
                f"Unexpected error: {str(e)}"
            ))
    
    def _on_send_progress(self, message: str, percentage: int) -> None:
        """Handle send progress update.
        
        Args:
            message: Progress message
            percentage: Progress percentage (0-100)
        """
        # Update button text from main thread
        QTimer.singleShot(0, lambda: self.send_button.setText(
            f"Sending... {percentage}%"
        ))
    
    def _on_send_success(self) -> None:
        """Handle successful email send."""
        # Re-enable buttons
        self._set_buttons_enabled(True)
        self.send_button.setText("Send Email")
        
        # Save configuration
        self._save_email_config()
        
        # Emit signal
        self.email_sent.emit()
        
        # Show success message
        QMessageBox.information(
            self,
            "Email Sent",
            "Deletion request email sent successfully to Discord Support!\n\n"
            "You should receive a response within a few business days."
        )
    
    def _on_send_error(self, error_message: str) -> None:
        """Handle email send error.
        
        Args:
            error_message: Error message to display
        """
        # Re-enable buttons
        self._set_buttons_enabled(True)
        self.send_button.setText("Send Email")
        
        # Emit signal
        self.email_failed.emit(error_message)
        
        # Show error message
        QMessageBox.critical(
            self,
            "Email Failed",
            f"Failed to send email:\n\n{error_message}"
        )
    
    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable action buttons.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.test_button.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
    
    def set_user(self, user: Optional[User]) -> None:
        """Set the current authenticated user.
        
        Args:
            user: Authenticated user or None
        """
        self._current_user = user
        self._update_preview()
    
    def set_message_export(self, export: Optional[MessageExport], attachment_path: Optional[str] = None) -> None:
        """Set the current message export data.
        
        Args:
            export: Message export data or None
            attachment_path: Path to attachment file or None
        """
        self._current_export = export
        self._attachment_path = attachment_path
        
        # Update attachment status
        if attachment_path:
            import os
            filename = os.path.basename(attachment_path)
            try:
                size_bytes = os.path.getsize(attachment_path)
                size_kb = size_bytes / 1024
                self.attachment_status_label.setText(f"{filename} ({size_kb:.1f} KB)")
            except Exception:
                self.attachment_status_label.setText(filename)
        else:
            self.attachment_status_label.setText("No attachment selected")
        
        # Update preview
        self._update_preview()
    
    def _update_preview(self) -> None:
        """Update the email preview based on current user and export data."""
        if self._current_user and self._current_export:
            # Generate email template
            email_body = self.email_service.generate_email_template(
                self._current_user,
                self._current_export
            )
            self.preview_text.setPlainText(email_body)
        else:
            # Show placeholder
            if not self._current_user:
                self.preview_text.setPlaceholderText(
                    "Please authenticate with Discord to generate email preview..."
                )
            elif not self._current_export:
                self.preview_text.setPlaceholderText(
                    "Please process messages to generate email preview..."
                )
            self.preview_text.clear()
    
    def get_email_config(self) -> Optional[EmailConfig]:
        """Get the current email configuration.
        
        Returns:
            EmailConfig if valid, None otherwise
        """
        config = self._get_email_config()
        if self.email_service.validate_smtp_config(config):
            return config
        return None
