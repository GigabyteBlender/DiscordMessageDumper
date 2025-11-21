"""Message processing service for Discord data exports."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from src.models.message_data import ChannelMessages, MessageExport
from src.utils.validators import validate_directory_path, sanitize_path


logger = logging.getLogger(__name__)


class MessageService:
    """Service for processing Discord message data exports.
    
    This service handles:
    - Validation of Discord data export directories
    - Scanning and extracting message IDs from channel JSON files
    - Filtering channels based on exclusion lists
    - Generating formatted message export files
    - Error handling for corrupted or invalid data
    """
    
    def __init__(self):
        """Initialize the MessageService."""
        pass
    
    def validate_directory(self, path: str) -> bool:
        """Validate that a directory contains valid Discord message data.
        
        A valid Discord message directory should:
        - Exist and be readable
        - Contain at least one subdirectory (channel folder)
        - Have at least one messages.json file in a channel subdirectory
        
        Args:
            path: Path to the messages directory to validate
            
        Returns:
            True if directory is valid, False otherwise
        """
        # First check basic directory validity
        is_valid, error_msg = validate_directory_path(path)
        if not is_valid:
            logger.warning(f"Directory validation failed: {error_msg}")
            return False
        
        try:
            path_obj = Path(path)
            
            # Look for channel subdirectories with messages.json files
            found_valid_channel = False
            
            for item in path_obj.iterdir():
                if item.is_dir():
                    # Check if this directory contains a messages.json file
                    messages_file = item / "messages.json"
                    if messages_file.exists() and messages_file.is_file():
                        found_valid_channel = True
                        break
            
            if not found_valid_channel:
                logger.warning(f"No valid channel directories with messages.json found in {path}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating directory {path}: {str(e)}")
            return False
    
    def scan_messages(
        self,
        directory: str,
        excluded_channels: List[str],
        progress_callback: Optional[Callable[[str, int, int, int], None]] = None
    ) -> MessageExport:
        """Scan a Discord data export directory and extract message IDs.
        
        Args:
            directory: Path to the messages directory
            excluded_channels: List of channel IDs to exclude from processing
            progress_callback: Optional callback function for progress updates.
                              Called with (status_text, current_channel, total_channels, message_count)
        
        Returns:
            MessageExport object containing all extracted message data
            
        Raises:
            ValueError: If directory is invalid
            OSError: If directory cannot be accessed
        """
        # Validate directory first
        if not self.validate_directory(directory):
            raise ValueError(f"Invalid Discord message directory: {directory}")
        
        path_obj = Path(directory)
        channels_data: List[ChannelMessages] = []
        total_messages = 0
        
        # Get list of all channel directories
        channel_dirs = [d for d in path_obj.iterdir() if d.is_dir()]
        total_channels = len(channel_dirs)
        processed_channels = 0
        
        logger.info(f"Starting message scan of {total_channels} channels in {directory}")
        
        # Report initial progress
        if progress_callback:
            progress_callback("Starting scan...", 0, total_channels, 0)
        
        for channel_dir in channel_dirs:
            channel_id = channel_dir.name
            processed_channels += 1
            
            # Skip excluded channels
            if channel_id in excluded_channels:
                logger.info(f"Skipping excluded channel: {channel_id}")
                if progress_callback:
                    progress_callback(
                        f"Skipped channel {channel_id} (excluded)",
                        processed_channels,
                        total_channels,
                        total_messages
                    )
                continue
            
            # Look for messages.json file
            messages_file = channel_dir / "messages.json"
            
            if not messages_file.exists():
                logger.warning(f"No messages.json found in channel {channel_id}")
                if progress_callback:
                    progress_callback(
                        f"No messages.json in channel {channel_id}",
                        processed_channels,
                        total_channels,
                        total_messages
                    )
                continue
            
            # Process the messages file
            try:
                message_ids = self._extract_message_ids(messages_file)
                
                if message_ids:
                    channel_messages = ChannelMessages(
                        channel_id=channel_id,
                        message_ids=message_ids,
                        message_count=len(message_ids)
                    )
                    channels_data.append(channel_messages)
                    total_messages += len(message_ids)
                    
                    logger.info(f"Processed channel {channel_id}: {len(message_ids)} messages")
                    
                    if progress_callback:
                        progress_callback(
                            f"Processed channel {channel_id}",
                            processed_channels,
                            total_channels,
                            total_messages
                        )
                else:
                    logger.info(f"Channel {channel_id} has no messages")
                    if progress_callback:
                        progress_callback(
                            f"Channel {channel_id} has no messages",
                            processed_channels,
                            total_channels,
                            total_messages
                        )
            
            except json.JSONDecodeError as e:
                # Handle corrupted JSON files - log error and continue
                logger.error(f"Corrupted JSON in channel {channel_id}: {str(e)}")
                if progress_callback:
                    progress_callback(
                        f"Error in channel {channel_id} (corrupted JSON)",
                        processed_channels,
                        total_channels,
                        total_messages
                    )
                continue
            
            except Exception as e:
                # Handle other errors - log and continue
                logger.error(f"Error processing channel {channel_id}: {str(e)}")
                if progress_callback:
                    progress_callback(
                        f"Error in channel {channel_id}",
                        processed_channels,
                        total_channels,
                        total_messages
                    )
                continue
        
        # Create the export object
        export = MessageExport(
            channels=channels_data,
            total_messages=total_messages,
            total_channels=len(channels_data),
            export_date=datetime.now()
        )
        
        logger.info(f"Scan complete: {total_messages} messages from {len(channels_data)} channels")
        
        if progress_callback:
            progress_callback(
                "Scan complete",
                total_channels,
                total_channels,
                total_messages
            )
        
        return export
    
    def _extract_message_ids(self, messages_file: Path) -> List[str]:
        """Extract message IDs from a messages.json file.
        
        Args:
            messages_file: Path to the messages.json file
            
        Returns:
            List of message IDs (as strings)
            
        Raises:
            json.JSONDecodeError: If the JSON file is corrupted
            OSError: If the file cannot be read
        """
        with open(messages_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        message_ids = []
        
        # Discord message exports can have different structures
        # Handle both array of messages and object with messages array
        if isinstance(data, list):
            # Array of message objects
            for message in data:
                if isinstance(message, dict) and 'id' in message:
                    message_ids.append(str(message['id']))
        elif isinstance(data, dict):
            # Object that might contain a messages array
            if 'messages' in data:
                messages = data['messages']
                if isinstance(messages, list):
                    for message in messages:
                        if isinstance(message, dict) and 'id' in message:
                            message_ids.append(str(message['id']))
        
        return message_ids
    
    def save_message_export(self, export: MessageExport, output_path: str) -> str:
        """Save a message export to a formatted text file.
        
        The output format is:
        Channel ID: <channel_id>
        <message_id_1>
        <message_id_2>
        ...
        
        Channel ID: <channel_id_2>
        ...
        
        Args:
            export: MessageExport object to save
            output_path: Path where the output file should be saved
            
        Returns:
            The full path to the saved file
            
        Raises:
            OSError: If the file cannot be written
            ValueError: If the output path is invalid
        """
        # Sanitize the output path
        is_safe, error_msg = sanitize_path(output_path)
        if not is_safe:
            raise ValueError(f"Invalid output path: {error_msg}")
        
        try:
            output_file = Path(output_path)
            
            # Create parent directories if they don't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"Discord Message Export\n")
                f.write(f"Generated: {export.export_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Messages: {export.total_messages}\n")
                f.write(f"Total Channels: {export.total_channels}\n")
                f.write(f"\n{'='*60}\n\n")
                
                # Write each channel's messages
                for channel in export.channels:
                    f.write(f"Channel ID: {channel.channel_id}\n")
                    f.write(f"Message Count: {channel.message_count}\n")
                    f.write(f"\n")
                    
                    for message_id in channel.message_ids:
                        f.write(f"{message_id}\n")
                    
                    f.write(f"\n{'-'*60}\n\n")
            
            logger.info(f"Message export saved to {output_file}")
            return str(output_file.absolute())
        
        except Exception as e:
            logger.error(f"Error saving message export to {output_path}: {str(e)}")
            raise OSError(f"Failed to save message export: {str(e)}")
