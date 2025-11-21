"""Main window for Discord Message Delete Helper application.

This module provides the main application window with:
- Sidebar navigation with icons
- Stacked widget for content area switching
- Integration of all widget components
- Status bar for global messages
- Modern styling and responsive behavior
"""

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QStackedWidget, QPushButton, QLabel, QFrame,
        QStatusBar, QSizePolicy
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QFont, QIcon
except ImportError:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QStackedWidget, QPushButton, QLabel, QFrame,
        QStatusBar, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QFont, QIcon

from src.ui.widgets.auth_widget import AuthWidget
from src.ui.widgets.message_widget import MessageWidget
from src.ui.widgets.email_widget import EmailWidget
from src.ui.widgets.settings_widget import SettingsWidget
from src.services.auth_service import AuthService
from src.services.message_service import MessageService
from src.services.email_service import EmailService
from src.services.config_service import ConfigService


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and content area.
    
    Provides a modern interface with:
    - Sidebar navigation with icon buttons for each section
    - Stacked widget for switching between different views
    - Status bar for displaying global messages
    - Integration of all widget components (Auth, Message, Email, Settings)
    - Responsive layout that adapts to window size
    """
    
    def __init__(
        self,
        auth_service: AuthService,
        message_service: MessageService,
        email_service: EmailService,
        config_service: ConfigService,
        parent: Optional[QWidget] = None
    ):
        """Initialize the main window.
        
        Args:
            auth_service: AuthService instance for authentication
            message_service: MessageService instance for message processing
            email_service: EmailService instance for email operations
            config_service: ConfigService instance for configuration
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Store services
        self.auth_service = auth_service
        self.message_service = message_service
        self.email_service = email_service
        self.config_service = config_service
        
        # Initialize widgets
        self.auth_widget: Optional[AuthWidget] = None
        self.message_widget: Optional[MessageWidget] = None
        self.email_widget: Optional[EmailWidget] = None
        self.settings_widget: Optional[SettingsWidget] = None
        
        # Navigation buttons
        self.nav_buttons: list = []
        
        # Initialize UI
        self._init_ui()
        self._connect_signals()
        self._load_default_settings()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Discord Message Delete Helper")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (horizontal: sidebar + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Create content area
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_stack)
        
        # Add widgets to content stack
        self._create_content_widgets()
        
        # Create status bar
        self._create_status_bar()
        
        # Set initial page
        self._switch_to_page(0)
    
    def _create_sidebar(self) -> QFrame:
        """Create the sidebar navigation panel.
        
        Returns:
            QFrame: Sidebar frame with navigation buttons
        """
        sidebar = QFrame()
        sidebar.setProperty("surface", True)
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(180)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)
        
        # App title/logo
        title_label = QLabel("Discord Message\nDelete Helper")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Spacer
        layout.addSpacing(20)
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Auth button
        auth_button = self._create_nav_button("Authentication")
        auth_button.clicked.connect(lambda: self._switch_to_page(0))
        layout.addWidget(auth_button)
        self.nav_buttons.append(auth_button)
        
        # Messages button
        messages_button = self._create_nav_button("Messages")
        messages_button.clicked.connect(lambda: self._switch_to_page(1))
        layout.addWidget(messages_button)
        self.nav_buttons.append(messages_button)
        
        # Email button
        email_button = self._create_nav_button("Email")
        email_button.clicked.connect(lambda: self._switch_to_page(2))
        layout.addWidget(email_button)
        self.nav_buttons.append(email_button)
        
        # Settings button
        settings_button = self._create_nav_button("Settings")
        settings_button.clicked.connect(lambda: self._switch_to_page(3))
        layout.addWidget(settings_button)
        self.nav_buttons.append(settings_button)
        
        # Spacer to push buttons to top
        layout.addStretch()
        
        return sidebar
    
    def _create_nav_button(self, text: str) -> QPushButton:
        """Create a navigation button with text.
        
        Args:
            text: Button text label
            
        Returns:
            QPushButton: Configured navigation button
        """
        button = QPushButton(text)
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setMinimumHeight(40)
        button.setProperty("nav", True)
        
        return button
    
    def _create_content_widgets(self) -> None:
        """Create and add all content widgets to the stacked widget."""
        # Authentication widget
        self.auth_widget = AuthWidget(self.auth_service)
        self.content_stack.addWidget(self.auth_widget)
        
        # Message processing widget
        self.message_widget = MessageWidget(self.message_service)
        self.content_stack.addWidget(self.message_widget)
        
        # Email widget
        self.email_widget = EmailWidget(self.email_service, self.config_service)
        self.content_stack.addWidget(self.email_widget)
        
        # Settings widget
        self.settings_widget = SettingsWidget(self.config_service)
        self.content_stack.addWidget(self.settings_widget)
    
    def _create_status_bar(self) -> None:
        """Create and configure the status bar."""
        status_bar = QStatusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: #2F3136;
                color: #B9BBBE;
                border-top: 1px solid #202225;
                padding: 4px 8px;
            }}
        """)
        self.setStatusBar(status_bar)
        self.show_status_message("Ready")
    
    def _switch_to_page(self, index: int) -> None:
        """Switch to a different page in the content stack.
        
        Args:
            index: Index of the page to switch to
        """
        # Update button states
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        
        # Switch content
        self.content_stack.setCurrentIndex(index)
        
        # Update status bar based on page
        page_names = ["Authentication", "Message Processing", "Email", "Settings"]
        if 0 <= index < len(page_names):
            self.show_status_message(f"Viewing: {page_names[index]}")
    
    def _connect_signals(self) -> None:
        """Connect signals between widgets and services."""
        # Auth widget signals
        if self.auth_widget:
            self.auth_widget.auth_state_changed.connect(self._on_auth_state_changed)
        
        # Message widget signals
        if self.message_widget:
            self.message_widget.processing_started.connect(
                lambda: self.show_status_message("Processing messages...")
            )
            self.message_widget.processing_completed.connect(self._on_messages_processed)
            self.message_widget.processing_failed.connect(
                lambda msg: self.show_status_message(f"Processing failed: {msg}", error=True)
            )
        
        # Email widget signals
        if self.email_widget:
            self.email_widget.email_sent.connect(
                lambda: self.show_status_message("Email sent successfully!", success=True)
            )
            self.email_widget.email_failed.connect(
                lambda msg: self.show_status_message(f"Email failed: {msg}", error=True)
            )
        
        # Settings widget signals
        if self.settings_widget:
            self.settings_widget.settings_saved.connect(self._on_settings_saved)
            self.settings_widget.data_cleared.connect(self._on_data_cleared)
            self.settings_widget.theme_changed.connect(self._on_theme_changed)
    
    def _load_default_settings(self) -> None:
        """Load default settings and apply them to widgets."""
        try:
            config = self.config_service.load_app_config()
            
            # Apply default directories to message widget
            if self.message_widget:
                if config.last_messages_directory:
                    self.message_widget.set_messages_directory(config.last_messages_directory)
                if config.last_save_directory:
                    self.message_widget.set_save_directory(config.last_save_directory)
                if config.excluded_channels:
                    self.message_widget.set_excluded_channels(config.excluded_channels)
        
        except Exception as e:
            # If loading fails, just use defaults
            pass
    
    def _on_auth_state_changed(self, is_authenticated: bool) -> None:
        """Handle authentication state change.
        
        Args:
            is_authenticated: True if user is authenticated, False otherwise
        """
        if is_authenticated:
            self.show_status_message("Successfully authenticated with Discord", success=True)
            
            # Update email widget with user info
            if self.email_widget and self.auth_widget:
                user = self.auth_service.get_current_user()
                if user:
                    self.email_widget.set_user(user)
        else:
            self.show_status_message("Disconnected from Discord")
            
            # Clear user from email widget
            if self.email_widget:
                self.email_widget.set_user(None)
    
    def _on_messages_processed(self, export) -> None:
        """Handle successful message processing.
        
        Args:
            export: MessageExport object with processing results
        """
        self.show_status_message(
            f"Processed {export.total_messages:,} messages from {export.total_channels} channels",
            success=True
        )
        
        # Update email widget with export data
        if self.email_widget and self.message_widget:
            attachment_path = self.message_widget._output_file_path
            self.email_widget.set_message_export(export, attachment_path)
    
    def _on_data_cleared(self) -> None:
        """Handle data cleared event."""
        self.show_status_message("All application data cleared", success=True)
        
        # Refresh all widgets
        if self.auth_widget:
            self.auth_widget.refresh()
        if self.email_widget:
            self.email_widget.set_user(None)
            self.email_widget.set_message_export(None, None)
        if self.settings_widget:
            self.settings_widget.refresh()
    
    def show_status_message(self, message: str, success: bool = False, error: bool = False) -> None:
        """Show a message in the status bar.
        
        Args:
            message: Message to display
            success: True to show as success message (green)
            error: True to show as error message (red)
        """
        status_bar = self.statusBar()
        if status_bar:
            # Set color based on message type
            if success:
                color = "#3BA55D"  # Green
            elif error:
                color = "#ED4245"  # Red
            else:
                color = "#B9BBBE"  # Default gray
            
            status_bar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: #2F3136;
                    color: {color};
                    border-top: 1px solid #202225;
                    padding: 4px 8px;
                }}
            """)
            status_bar.showMessage(message)
    
    def _on_settings_saved(self) -> None:
        """Handle settings saved event."""
        self.show_status_message("Settings saved successfully!", success=True)
    
    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change event.
        
        Args:
            theme: New theme name ('dark' or 'light')
        """
        try:
            from src.ui.styles.theme import apply_theme
            
            # Get the QApplication instance
            try:
                from PySide6.QtWidgets import QApplication
            except ImportError:
                from PyQt6.QtWidgets import QApplication
            
            app = QApplication.instance()
            
            # Apply the new theme
            if app:
                apply_theme(app, theme)
                self.show_status_message(f"Theme changed to {theme}", success=True)
            else:
                self.show_status_message("Could not get application instance", error=True)
        except Exception as e:
            self.show_status_message(f"Failed to apply theme: {str(e)}", error=True)
    
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event
        """
        # Save current settings before closing
        try:
            if self.message_widget:
                # Get current directories from message widget
                messages_dir = self.message_widget.messages_dir_input.text().strip() or None
                save_dir = self.message_widget.save_dir_input.text().strip() or None
                
                # Get excluded channels
                excluded_text = self.message_widget.excluded_channels_input.text().strip()
                excluded_channels = []
                if excluded_text:
                    excluded_channels = [ch.strip() for ch in excluded_text.split(",") if ch.strip()]
                
                # Load current config and update
                config = self.config_service.load_app_config()
                config.last_messages_directory = messages_dir
                config.last_save_directory = save_dir
                config.excluded_channels = excluded_channels
                
                # Save updated config
                self.config_service.save_app_config(config)
        
        except Exception:
            # If saving fails, just continue closing
            pass
        
        # Accept the close event
        event.accept()
