"""Message processing widget for Discord data exports.

This widget provides a UI for:
- Selecting Discord data export directory
- Selecting output directory for message export
- Excluding specific channels
- Processing messages with progress feedback
- Displaying results summary
"""

from typing import Optional
import threading
import os

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QProgressBar, QFileDialog, QTextEdit, QScrollArea
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QMessageBox, QLineEdit,
        QProgressBar, QFileDialog, QTextEdit, QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont

from src.services.message_service import MessageService
from src.models.message_data import MessageExport


class MessageWidget(QWidget):
    """Widget for Discord message processing and export.
    
    Provides a modern interface for:
    - Selecting messages directory from Discord data export
    - Selecting output directory for processed messages
    - Excluding specific channels from processing
    - Processing messages with real-time progress updates
    - Displaying results summary
    
    Signals:
        processing_started: Emitted when message processing begins
        processing_completed: Emitted when processing completes (MessageExport)
        processing_failed: Emitted when processing fails (str: error_message)
    """
    
    processing_started = Signal()
    processing_completed = Signal(object)  # MessageExport
    processing_failed = Signal(str)
    
    def __init__(self, message_service: MessageService, parent: Optional[QWidget] = None):
        """Initialize the message processing widget.
        
        Args:
            message_service: MessageService instance for processing
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.message_service = message_service
        self._processing_thread: Optional[threading.Thread] = None
        self._current_export: Optional[MessageExport] = None
        self._output_file_path: Optional[str] = None
        
        self._init_ui()
    
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
        header_label = QLabel("Message Processing")
        header_label.setProperty("heading", True)
        layout.addWidget(header_label)
        
        # Input section card
        input_card = self._create_input_section()
        layout.addWidget(input_card)
        
        # Progress section card
        progress_card = self._create_progress_section()
        layout.addWidget(progress_card)
        
        # Results section card
        results_card = self._create_results_section()
        layout.addWidget(results_card)
        
        layout.addStretch()
    
    def _create_input_section(self) -> QFrame:
        """Create the input section with directory selection and options.
        
        Returns:
            QFrame: Frame containing input controls
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Messages Directory
        messages_label = QLabel("Messages Directory")
        messages_label.setProperty("secondary", False)
        layout.addWidget(messages_label)
        
        messages_layout = QHBoxLayout()
        messages_layout.setSpacing(8)
        
        self.messages_dir_input = QLineEdit()
        self.messages_dir_input.setPlaceholderText("Select Discord data export messages directory...")
        messages_layout.addWidget(self.messages_dir_input)
        
        self.messages_browse_button = QPushButton("Browse")
        self.messages_browse_button.setProperty("secondary", True)
        self.messages_browse_button.clicked.connect(self._on_messages_browse_clicked)
        messages_layout.addWidget(self.messages_browse_button)
        
        layout.addLayout(messages_layout)
        
        # Save Directory
        save_label = QLabel("Save Directory")
        save_label.setProperty("secondary", False)
        layout.addWidget(save_label)
        
        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)
        
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText("Select directory to save processed messages...")
        save_layout.addWidget(self.save_dir_input)
        
        self.save_browse_button = QPushButton("Browse")
        self.save_browse_button.setProperty("secondary", True)
        self.save_browse_button.clicked.connect(self._on_save_browse_clicked)
        save_layout.addWidget(self.save_browse_button)
        
        layout.addLayout(save_layout)
        
        # Excluded Channels
        excluded_label = QLabel("Exclude Channels (comma-separated)")
        excluded_label.setProperty("secondary", False)
        layout.addWidget(excluded_label)
        
        self.excluded_channels_input = QLineEdit()
        self.excluded_channels_input.setPlaceholderText("e.g., 123456789, 987654321")
        layout.addWidget(self.excluded_channels_input)
        
        # Process Button
        self.process_button = QPushButton("Process Messages")
        self.process_button.clicked.connect(self._on_process_clicked)
        layout.addWidget(self.process_button)
        
        return frame
    
    def _create_progress_section(self) -> QFrame:
        """Create the progress section with progress bar and status.
        
        Returns:
            QFrame: Frame containing progress controls
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_label = QLabel("Ready to process messages")
        self.status_label.setProperty("secondary", True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Message count
        self.message_count_label = QLabel("")
        self.message_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_count_label)
        
        # Hide progress section initially
        frame.hide()
        self.progress_frame = frame
        
        return frame
    
    def _create_results_section(self) -> QFrame:
        """Create the results section with summary display.
        
        Returns:
            QFrame: Frame containing results display
        """
        frame = QFrame()
        frame.setProperty("card", True)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Results header
        results_header = QLabel("Results Summary")
        results_header.setProperty("heading", False)
        results_font = QFont()
        results_font.setPointSize(14)
        results_font.setBold(True)
        results_header.setFont(results_font)
        layout.addWidget(results_header)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        layout.addWidget(self.results_text)
        
        # Open file button
        self.open_file_button = QPushButton("Open Output File")
        self.open_file_button.setProperty("secondary", True)
        self.open_file_button.clicked.connect(self._on_open_file_clicked)
        layout.addWidget(self.open_file_button)
        
        # Hide results section initially
        frame.hide()
        self.results_frame = frame
        
        return frame
    
    def _on_messages_browse_clicked(self) -> None:
        """Handle messages directory browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Discord Messages Directory",
            self.messages_dir_input.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.messages_dir_input.setText(directory)
    
    def _on_save_browse_clicked(self) -> None:
        """Handle save directory browse button click."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            self.save_dir_input.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.save_dir_input.setText(directory)
    
    def _on_process_clicked(self) -> None:
        """Handle process button click."""
        # Validate inputs
        messages_dir = self.messages_dir_input.text().strip()
        save_dir = self.save_dir_input.text().strip()
        
        if not messages_dir:
            QMessageBox.warning(
                self,
                "Missing Input",
                "Please select a messages directory."
            )
            return
        
        if not save_dir:
            QMessageBox.warning(
                self,
                "Missing Input",
                "Please select a save directory."
            )
            return
        
        # Validate messages directory
        if not self.message_service.validate_directory(messages_dir):
            QMessageBox.critical(
                self,
                "Invalid Directory",
                "The selected messages directory does not contain valid Discord message data.\n\n"
                "Please ensure you've selected the 'messages' folder from your Discord data export."
            )
            return
        
        # Parse excluded channels
        excluded_text = self.excluded_channels_input.text().strip()
        excluded_channels = []
        if excluded_text:
            excluded_channels = [ch.strip() for ch in excluded_text.split(",") if ch.strip()]
        
        # Disable inputs during processing
        self._set_inputs_enabled(False)
        
        # Show progress section
        self.progress_frame.show()
        self.results_frame.hide()
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting scan...")
        self.message_count_label.setText("")
        
        # Emit signal
        self.processing_started.emit()
        
        # Start processing in background thread
        self._processing_thread = threading.Thread(
            target=self._process_messages_thread,
            args=(messages_dir, save_dir, excluded_channels),
            daemon=True
        )
        self._processing_thread.start()
    
    def _process_messages_thread(
        self,
        messages_dir: str,
        save_dir: str,
        excluded_channels: list
    ) -> None:
        """Process messages in a background thread.
        
        Args:
            messages_dir: Path to messages directory
            save_dir: Path to save directory
            excluded_channels: List of channel IDs to exclude
        """
        try:
            # Scan messages with progress callback
            export = self.message_service.scan_messages(
                directory=messages_dir,
                excluded_channels=excluded_channels,
                progress_callback=self._on_progress_update
            )
            
            # Save the export
            output_path = os.path.join(save_dir, "discord_messages.txt")
            saved_path = self.message_service.save_message_export(export, output_path)
            
            # Update UI from main thread
            QTimer.singleShot(0, lambda: self._on_processing_success(export, saved_path))
            
        except Exception as e:
            # Update UI from main thread
            QTimer.singleShot(0, lambda: self._on_processing_error(str(e)))
    
    def _on_progress_update(
        self,
        status_text: str,
        current_channel: int,
        total_channels: int,
        message_count: int
    ) -> None:
        """Handle progress update from message service.
        
        Args:
            status_text: Current status description
            current_channel: Number of channels processed
            total_channels: Total number of channels
            message_count: Total messages found so far
        """
        # Calculate percentage
        if total_channels > 0:
            percentage = int((current_channel / total_channels) * 100)
        else:
            percentage = 0
        
        # Update UI from main thread
        QTimer.singleShot(0, lambda: self._update_progress_ui(
            status_text, percentage, current_channel, total_channels, message_count
        ))
    
    def _update_progress_ui(
        self,
        status_text: str,
        percentage: int,
        current_channel: int,
        total_channels: int,
        message_count: int
    ) -> None:
        """Update progress UI elements.
        
        Args:
            status_text: Status text to display
            percentage: Progress percentage (0-100)
            current_channel: Current channel number
            total_channels: Total channels
            message_count: Total messages found
        """
        self.progress_bar.setValue(percentage)
        self.status_label.setText(f"{status_text} ({current_channel}/{total_channels})")
        self.message_count_label.setText(f"Found {message_count:,} messages")
    
    def _on_processing_success(self, export: MessageExport, output_path: str) -> None:
        """Handle successful message processing.
        
        Args:
            export: MessageExport object with results
            output_path: Path to saved output file
        """
        # Store results
        self._current_export = export
        self._output_file_path = output_path
        
        # Re-enable inputs
        self._set_inputs_enabled(True)
        
        # Update progress to 100%
        self.progress_bar.setValue(100)
        self.status_label.setText("Processing complete!")
        
        # Show results
        self._display_results(export, output_path)
        
        # Emit signal
        self.processing_completed.emit(export)
        
        # Show success message
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {export.total_messages:,} messages from {export.total_channels} channels.\n\n"
            f"Output saved to:\n{output_path}"
        )
    
    def _on_processing_error(self, error_message: str) -> None:
        """Handle processing error.
        
        Args:
            error_message: Error message to display
        """
        # Re-enable inputs
        self._set_inputs_enabled(True)
        
        # Update status
        self.status_label.setText("Processing failed")
        
        # Emit signal
        self.processing_failed.emit(error_message)
        
        # Show error message
        QMessageBox.critical(
            self,
            "Processing Failed",
            f"An error occurred while processing messages:\n\n{error_message}"
        )
    
    def _display_results(self, export: MessageExport, output_path: str) -> None:
        """Display processing results.
        
        Args:
            export: MessageExport object with results
            output_path: Path to saved output file
        """
        # Show results frame
        self.results_frame.show()
        
        # Format results text
        results_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif;">
            <p><strong>Total Messages:</strong> {export.total_messages:,}</p>
            <p><strong>Total Channels:</strong> {export.total_channels}</p>
            <p><strong>Export Date:</strong> {export.export_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Output File:</strong><br/><code>{output_path}</code></p>
        </div>
        """
        
        self.results_text.setHtml(results_html)
    
    def _on_open_file_clicked(self) -> None:
        """Handle open file button click."""
        if self._output_file_path and os.path.exists(self._output_file_path):
            # Open file in default application
            import platform
            import subprocess
            
            try:
                if platform.system() == 'Windows':
                    os.startfile(self._output_file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', self._output_file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', self._output_file_path])
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Cannot Open File",
                    f"Could not open the file:\n{str(e)}"
                )
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                "The output file could not be found."
            )
    
    def _set_inputs_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.messages_dir_input.setEnabled(enabled)
        self.messages_browse_button.setEnabled(enabled)
        self.save_dir_input.setEnabled(enabled)
        self.save_browse_button.setEnabled(enabled)
        self.excluded_channels_input.setEnabled(enabled)
        self.process_button.setEnabled(enabled)
    
    def set_messages_directory(self, directory: str) -> None:
        """Set the messages directory path.
        
        Args:
            directory: Path to messages directory
        """
        self.messages_dir_input.setText(directory)
    
    def set_save_directory(self, directory: str) -> None:
        """Set the save directory path.
        
        Args:
            directory: Path to save directory
        """
        self.save_dir_input.setText(directory)
    
    def set_excluded_channels(self, channels: list) -> None:
        """Set the excluded channels list.
        
        Args:
            channels: List of channel IDs to exclude
        """
        self.excluded_channels_input.setText(", ".join(channels))
    
    def get_current_export(self) -> Optional[MessageExport]:
        """Get the current message export result.
        
        Returns:
            MessageExport object if processing completed, None otherwise
        """
        return self._current_export
