"""Settings widget for application configuration.

This widget provides a UI for:
- Theme selection
- Default directories configuration
- Email provider presets management
- Clearing application data
"""

from typing import Optional
import os

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QComboBox, QFileDialog, QGroupBox, QScrollArea
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QComboBox, QFileDialog, QGroupBox, QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal
    from PyQt6.QtGui import QFont

from src.services.config_service import ConfigService
from src.services.email_service import EMAIL_PRESETS
from src.models.config import AppConfig


class SettingsWidget(QWidget):
    """Widget for application settings and configuration.
    
    Provides a modern interface for:
    - Selecting UI theme
    - Configuring default directories for messages and saves
    - Managing email provider presets
    - Clearing application data with confirmation
    
    Signals:
        settings_saved: Emitted when settings are saved successfully
        data_cleared: Emitted when application data is cleared
    """
    
    settings_saved = Signal()
    data_cleared = Signal()
    theme_changed = Signal(str)  # Emits the new theme name
    
    def __init__(self, config_service: ConfigService, parent: Optional[QWidget] = None):
        """Initialize the settings widget.
        
        Args:
            config_service: ConfigService instance for loading/saving settings
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.config_service = config_service
        
        self._init_ui()
        self._load_current_settings()
    
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
        header_label = QLabel("Settings")
        header_label.setProperty("heading", True)
        layout.addWidget(header_label)
        
        # Theme settings section
        theme_card = self._create_theme_section()
        layout.addWidget(theme_card)
        
        # Default directories section
        directories_card = self._create_directories_section()
        layout.addWidget(directories_card)
        
        # Email provider presets section
        email_presets_card = self._create_email_presets_section()
        layout.addWidget(email_presets_card)
        
        # Data management section
        data_card = self._create_data_management_section()
        layout.addWidget(data_card)
        
        # Action buttons
        buttons_layout = self._create_action_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_theme_section(self) -> QFrame:
        """Create the theme selection section.
        
        Returns:
            QFrame: Frame containing theme settings
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section header
        section_label = QLabel("Appearance")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_label.setFont(section_font)
        layout.addWidget(section_label)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(12)
        
        theme_label = QLabel("Theme:")
        theme_label.setMinimumWidth(150)
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['dark', 'light'])
        theme_layout.addWidget(self.theme_combo)
        
        layout.addLayout(theme_layout)
        
        # Theme note
        theme_note = QLabel("Theme changes will be applied immediately when you save settings.")
        theme_note.setProperty("secondary", True)
        theme_note.setWordWrap(True)
        layout.addWidget(theme_note)
        
        return frame
    
    def _create_directories_section(self) -> QFrame:
        """Create the default directories configuration section.
        
        Returns:
            QFrame: Frame containing directory settings
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section header
        section_label = QLabel("Default Directories")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_label.setFont(section_font)
        layout.addWidget(section_label)
        
        # Messages directory
        messages_label = QLabel("Default Messages Directory:")
        layout.addWidget(messages_label)
        
        messages_layout = QHBoxLayout()
        messages_layout.setSpacing(8)
        
        self.messages_dir_input = QLineEdit()
        self.messages_dir_input.setPlaceholderText("No default directory set")
        messages_layout.addWidget(self.messages_dir_input)
        
        messages_browse_button = QPushButton("Browse")
        messages_browse_button.setProperty("secondary", True)
        messages_browse_button.clicked.connect(self._on_messages_browse_clicked)
        messages_layout.addWidget(messages_browse_button)
        
        messages_clear_button = QPushButton("Clear")
        messages_clear_button.setProperty("secondary", True)
        messages_clear_button.clicked.connect(lambda: self.messages_dir_input.clear())
        messages_layout.addWidget(messages_clear_button)
        
        layout.addLayout(messages_layout)
        
        # Save directory
        save_label = QLabel("Default Save Directory:")
        layout.addWidget(save_label)
        
        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)
        
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText("No default directory set")
        save_layout.addWidget(self.save_dir_input)
        
        save_browse_button = QPushButton("Browse")
        save_browse_button.setProperty("secondary", True)
        save_browse_button.clicked.connect(self._on_save_browse_clicked)
        save_layout.addWidget(save_browse_button)
        
        save_clear_button = QPushButton("Clear")
        save_clear_button.setProperty("secondary", True)
        save_clear_button.clicked.connect(lambda: self.save_dir_input.clear())
        save_layout.addWidget(save_clear_button)
        
        layout.addLayout(save_layout)
        
        # Excluded channels
        excluded_label = QLabel("Default Excluded Channels:")
        layout.addWidget(excluded_label)
        
        self.excluded_channels_input = QLineEdit()
        self.excluded_channels_input.setPlaceholderText("Comma-separated channel IDs (e.g., 123456789, 987654321)")
        layout.addWidget(self.excluded_channels_input)
        
        return frame
    
    def _create_email_presets_section(self) -> QFrame:
        """Create the email provider presets section.
        
        Returns:
            QFrame: Frame containing email preset information
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section header
        section_label = QLabel("Email Provider Presets")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_label.setFont(section_font)
        layout.addWidget(section_label)
        
        # Info text
        info_label = QLabel(
            "The following email provider presets are available for quick SMTP configuration:"
        )
        info_label.setProperty("secondary", True)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # List of presets
        presets_text = []
        for provider_name, preset in EMAIL_PRESETS.items():
            if provider_name != 'Custom':
                preset_info = f"• {provider_name}: {preset['smtp_server']}:{preset['smtp_port']}"
                if 'note' in preset:
                    preset_info += f" ({preset['note']})"
                presets_text.append(preset_info)
        
        presets_label = QLabel("\n".join(presets_text))
        presets_label.setProperty("secondary", True)
        presets_label.setWordWrap(True)
        layout.addWidget(presets_label)
        
        # Note about configuration
        config_note = QLabel(
            "Configure email settings in the Email section to use these presets."
        )
        config_note.setProperty("secondary", True)
        config_note.setWordWrap(True)
        layout.addWidget(config_note)
        
        return frame
    
    def _create_data_management_section(self) -> QFrame:
        """Create the data management section.
        
        Returns:
            QFrame: Frame containing data management controls
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Section header
        section_label = QLabel("Data Management")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_label.setFont(section_font)
        layout.addWidget(section_label)
        
        # Warning text
        warning_label = QLabel(
            "Clear all application data including authentication tokens, "
            "saved settings, and email configuration. This action cannot be undone."
        )
        warning_label.setProperty("secondary", True)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Clear data button
        self.clear_data_button = QPushButton("Clear All Data")
        self.clear_data_button.setProperty("danger", True)
        self.clear_data_button.clicked.connect(self._on_clear_data_clicked)
        layout.addWidget(self.clear_data_button)
        
        return frame
    
    def _create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons layout.
        
        Returns:
            QHBoxLayout: Layout containing action buttons
        """
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Reset button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.setProperty("secondary", True)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        layout.addWidget(self.reset_button)
        
        # Spacer
        layout.addStretch()
        
        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_button)
        
        return layout
    
    def _load_current_settings(self) -> None:
        """Load current settings from config service."""
        try:
            config = self.config_service.load_app_config()
            
            # Set theme
            if config.theme:
                index = self.theme_combo.findText(config.theme)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)
            
            # Set directories
            if config.last_messages_directory:
                self.messages_dir_input.setText(config.last_messages_directory)
            
            if config.last_save_directory:
                self.save_dir_input.setText(config.last_save_directory)
            
            # Set excluded channels
            if config.excluded_channels:
                self.excluded_channels_input.setText(", ".join(config.excluded_channels))
        
        except Exception as e:
            # If loading fails, just use defaults
            pass
    
    def _on_messages_browse_clicked(self) -> None:
        """Handle messages directory browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Messages Directory",
            self.messages_dir_input.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.messages_dir_input.setText(directory)
    
    def _on_save_browse_clicked(self) -> None:
        """Handle save directory browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Directory",
            self.save_dir_input.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.save_dir_input.setText(directory)
    
    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            # Get current settings from UI
            theme = self.theme_combo.currentText()
            messages_dir = self.messages_dir_input.text().strip() or None
            save_dir = self.save_dir_input.text().strip() or None
            
            # Parse excluded channels
            excluded_text = self.excluded_channels_input.text().strip()
            excluded_channels = []
            if excluded_text:
                excluded_channels = [ch.strip() for ch in excluded_text.split(",") if ch.strip()]
            
            # Load current config to preserve email settings
            current_config = self.config_service.load_app_config()
            
            # Create updated config
            updated_config = AppConfig(
                last_messages_directory=messages_dir,
                last_save_directory=save_dir,
                excluded_channels=excluded_channels,
                email_config=current_config.email_config,  # Preserve email config
                theme=theme
            )
            
            # Check if theme changed
            theme_changed = theme != current_config.theme
            
            # Save configuration
            self.config_service.save_app_config(updated_config)
            
            # Emit signals
            self.settings_saved.emit()
            
            # If theme changed, emit theme_changed signal and apply immediately
            if theme_changed:
                self.theme_changed.emit(theme)
            
            # Show success message
            QMessageBox.information(
                self,
                "Settings Saved",
                "Your settings have been saved successfully!" +
                ("\n\nTheme has been applied immediately." if theme_changed else "")
            )
        
        except ValueError as e:
            # Validation error
            QMessageBox.warning(
                self,
                "Invalid Settings",
                f"Could not save settings:\n\n{str(e)}"
            )
        
        except Exception as e:
            # Other error
            QMessageBox.critical(
                self,
                "Save Failed",
                f"An error occurred while saving settings:\n\n{str(e)}"
            )
    
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        # Confirm reset
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Reset all settings to default values?\n\n"
            "This will clear default directories and excluded channels, "
            "but will not affect your email configuration or authentication.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to defaults
            self.theme_combo.setCurrentText('dark')
            self.messages_dir_input.clear()
            self.save_dir_input.clear()
            self.excluded_channels_input.clear()
            
            # Show confirmation
            QMessageBox.information(
                self,
                "Settings Reset",
                "Settings have been reset to defaults.\n\n"
                "Click 'Save Settings' to apply the changes."
            )
    
    def _on_clear_data_clicked(self) -> None:
        """Handle clear data button click."""
        # Confirm clear with strong warning
        reply = QMessageBox.warning(
            self,
            "Confirm Clear Data",
            "⚠️ WARNING: This will permanently delete ALL application data:\n\n"
            "• Authentication tokens and user data\n"
            "• All saved settings and preferences\n"
            "• Email configuration and passwords\n"
            "• Default directories and excluded channels\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Second confirmation
            reply2 = QMessageBox.question(
                self,
                "Final Confirmation",
                "This is your last chance to cancel.\n\n"
                "Clear all application data?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                try:
                    # Clear config file
                    if os.path.exists(self.config_service.config_file):
                        os.remove(self.config_service.config_file)
                    
                    # Clear any other data files
                    data_files = ['data.txt', 'user_data.json', 'auth_token.txt']
                    for data_file in data_files:
                        if os.path.exists(data_file):
                            os.remove(data_file)
                    
                    # Reset UI to defaults
                    self.theme_combo.setCurrentText('dark')
                    self.messages_dir_input.clear()
                    self.save_dir_input.clear()
                    self.excluded_channels_input.clear()
                    
                    # Emit signal
                    self.data_cleared.emit()
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Data Cleared",
                        "All application data has been cleared successfully.\n\n"
                        "The application will now restart with default settings."
                    )
                
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Clear Failed",
                        f"An error occurred while clearing data:\n\n{str(e)}"
                    )
    
    def refresh(self) -> None:
        """Refresh the widget to reflect current settings."""
        self._load_current_settings()
    
    def get_current_theme(self) -> str:
        """Get the currently selected theme.
        
        Returns:
            str: Current theme name
        """
        return self.theme_combo.currentText()
    
    def get_default_messages_directory(self) -> Optional[str]:
        """Get the default messages directory.
        
        Returns:
            str: Default messages directory path or None
        """
        text = self.messages_dir_input.text().strip()
        return text if text else None
    
    def get_default_save_directory(self) -> Optional[str]:
        """Get the default save directory.
        
        Returns:
            str: Default save directory path or None
        """
        text = self.save_dir_input.text().strip()
        return text if text else None
    
    def get_excluded_channels(self) -> list:
        """Get the list of excluded channels.
        
        Returns:
            list: List of channel IDs to exclude
        """
        text = self.excluded_channels_input.text().strip()
        if text:
            return [ch.strip() for ch in text.split(",") if ch.strip()]
        return []
