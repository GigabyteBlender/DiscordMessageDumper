"""Authentication widget for Discord OAuth flow.

This widget provides a card-based UI for Discord authentication,
displaying connection status and user information.
"""

from typing import Optional, Callable
import threading
import logging

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont

from src.services.auth_service import AuthService
from src.models.user import User


class AuthWidget(QWidget):
    """Widget for Discord authentication and user information display.
    
    Provides a modern card-based interface for:
    - Initiating Discord OAuth flow
    - Displaying authenticated user information
    - Showing connection status
    - Logging out
    
    Signals:
        auth_state_changed: Emitted when authentication state changes (bool: is_authenticated)
        _oauth_success_signal: Internal signal for OAuth success (User)
        _oauth_error_signal: Internal signal for OAuth error (str)
    """
    
    auth_state_changed = Signal(bool)
    _oauth_success_signal = Signal(object)  # User object
    _oauth_error_signal = Signal(str)  # Error message
    
    def __init__(self, auth_service: AuthService, parent: Optional[QWidget] = None):
        """Initialize the authentication widget.
        
        Args:
            auth_service: AuthService instance for handling OAuth
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.auth_service = auth_service
        self._oauth_thread: Optional[threading.Thread] = None
        
        self._init_ui()
        self._update_ui_state()
        
        # Connect internal signals
        self._oauth_success_signal.connect(self._on_oauth_success)
        self._oauth_error_signal.connect(self._handle_oauth_error)
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header_label = QLabel("Discord Authentication")
        header_label.setProperty("heading", True)
        layout.addWidget(header_label)
        
        # Card frame for user info or connect button
        self.card_frame = QFrame()
        self.card_frame.setProperty("card", True)
        self.card_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.card_layout = QVBoxLayout(self.card_frame)
        self.card_layout.setContentsMargins(16, 16, 16, 16)
        self.card_layout.setSpacing(12)
        
        # User info section (shown when authenticated)
        self.user_info_widget = self._create_user_info_widget()
        self.card_layout.addWidget(self.user_info_widget)
        
        # Connect button section (shown when not authenticated)
        self.connect_widget = self._create_connect_widget()
        self.card_layout.addWidget(self.connect_widget)
        
        layout.addWidget(self.card_frame)
        layout.addStretch()
    
    def _create_user_info_widget(self) -> QWidget:
        """Create the user information display widget.
        
        Returns:
            QWidget: Widget containing user information display
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Avatar placeholder (using emoji for now)
        avatar_label = QLabel("👤")
        avatar_font = QFont()
        avatar_font.setPointSize(48)
        avatar_label.setFont(avatar_font)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar_label)
        
        # Username
        self.username_label = QLabel("Username#0000")
        self.username_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        username_font = QFont()
        username_font.setPointSize(16)
        username_font.setBold(True)
        self.username_label.setFont(username_font)
        layout.addWidget(self.username_label)
        
        # Email
        self.email_label = QLabel("user@email.com")
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.email_label.setProperty("secondary", True)
        layout.addWidget(self.email_label)
        
        # User ID
        self.user_id_label = QLabel("ID: 000000000000000000")
        self.user_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_id_label.setProperty("secondary", True)
        id_font = QFont()
        id_font.setPointSize(10)
        self.user_id_label.setFont(id_font)
        layout.addWidget(self.user_id_label)
        
        # Spacer
        layout.addSpacing(8)
        
        # Connection status
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #3BA55D;")  # Green
        status_font = QFont()
        status_font.setPointSize(12)
        self.status_indicator.setFont(status_font)
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Connected")
        self.status_label.setStyleSheet("color: #3BA55D;")  # Green
        status_layout.addWidget(self.status_label)
        
        layout.addLayout(status_layout)
        
        # Spacer
        layout.addSpacing(8)
        
        # Disconnect button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setProperty("danger", True)
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        layout.addWidget(self.disconnect_button)
        
        return widget
    
    def _create_connect_widget(self) -> QWidget:
        """Create the connect button widget.
        
        Returns:
            QWidget: Widget containing connect button
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Info text
        info_label = QLabel(
            "Connect your Discord account to authenticate\n"
            "and verify your identity for message deletion requests."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setProperty("secondary", True)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Spacer
        layout.addSpacing(8)
        
        # Connect button
        self.connect_button = QPushButton("Connect to Discord")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_button)
        
        # Status label for OAuth flow
        self.oauth_status_label = QLabel("")
        self.oauth_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.oauth_status_label.setProperty("secondary", True)
        self.oauth_status_label.setWordWrap(True)
        self.oauth_status_label.hide()
        layout.addWidget(self.oauth_status_label)
        
        return widget
    
    def _update_ui_state(self) -> None:
        """Update UI based on authentication state."""
        is_authenticated = self.auth_service.is_authenticated()
        
        # Show/hide appropriate widgets
        if is_authenticated:
            self.user_info_widget.show()
            self.connect_widget.hide()
        else:
            self.user_info_widget.hide()
            self.connect_widget.show()
        
        # Update user info if authenticated
        if is_authenticated:
            user = self.auth_service.get_current_user()
            if user:
                self._display_user_info(user)
    
    def _display_user_info(self, user: User) -> None:
        """Display user information in the UI.
        
        Args:
            user: User object with authentication data
        """
        self.username_label.setText(user.username)
        self.email_label.setText(user.email)
        self.user_id_label.setText(f"ID: {user.id}")
        
        # Update verification status if needed
        if not user.verified:
            self.email_label.setText(f"{user.email} (unverified)")
    
    def _on_connect_clicked(self) -> None:
        """Handle connect button click."""
        # Disable button during OAuth flow
        self.connect_button.setEnabled(False)
        self.oauth_status_label.setText("Opening browser for authentication...")
        self.oauth_status_label.show()
        
        try:
            # Start OAuth flow
            self.auth_service.start_oauth_flow()
            
            # Update status
            self.oauth_status_label.setText(
                "Waiting for authorization...\n"
                "Please complete the authentication in your browser."
            )
            
            # Wait for callback in a separate thread
            self._oauth_thread = threading.Thread(
                target=self._wait_for_oauth_callback,
                daemon=True
            )
            self._oauth_thread.start()
            
        except Exception as e:
            self._handle_oauth_error(f"Failed to start OAuth flow: {str(e)}")
    
    def _wait_for_oauth_callback(self) -> None:
        """Wait for OAuth callback in a separate thread."""
        logger = logging.getLogger(__name__)
        try:
            logger.info("Waiting for OAuth callback...")
            # Wait for callback with 5 minute timeout
            user = self.auth_service.wait_for_oauth_callback(timeout=300)
            
            logger.info(f"OAuth callback received for user: {user.username}")
            # Emit signal to update UI from main thread
            self._oauth_success_signal.emit(user)
            
        except TimeoutError:
            logger.error("OAuth callback timed out")
            self._oauth_error_signal.emit("Authentication timed out. Please try again.")
        except ValueError as e:
            logger.error(f"OAuth callback error: {e}")
            self._oauth_error_signal.emit(str(e))
        except Exception as e:
            logger.error(f"OAuth callback exception: {e}", exc_info=True)
            self._oauth_error_signal.emit(f"Authentication failed: {str(e)}")
    
    def _on_oauth_success(self, user: User) -> None:
        """Handle successful OAuth authentication.
        
        Args:
            user: Authenticated user object
        """
        logger = logging.getLogger(__name__)
        logger.info(f"_on_oauth_success called for user: {user.username}")
        
        # Re-enable button
        self.connect_button.setEnabled(True)
        self.oauth_status_label.hide()
        
        # Update UI
        self._update_ui_state()
        
        # Emit signal
        self.auth_state_changed.emit(True)
        
        logger.info("Showing success message box")
        # Show success message
        QMessageBox.information(
            self,
            "Authentication Successful",
            f"Successfully authenticated as {user.username}!"
        )
    
    def _handle_oauth_error(self, error_message: str) -> None:
        """Handle OAuth authentication error.
        
        Args:
            error_message: Error message to display
        """
        # Re-enable button
        self.connect_button.setEnabled(True)
        self.oauth_status_label.hide()
        
        # Show error message
        QMessageBox.critical(
            self,
            "Authentication Failed",
            error_message
        )
    
    def _on_disconnect_clicked(self) -> None:
        """Handle disconnect button click."""
        # Confirm logout
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to disconnect your Discord account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Logout
            self.auth_service.logout()
            
            # Update UI
            self._update_ui_state()
            
            # Emit signal
            self.auth_state_changed.emit(False)
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Disconnected",
                "Successfully disconnected from Discord."
            )
    
    def refresh(self) -> None:
        """Refresh the widget to reflect current authentication state."""
        self._update_ui_state()
