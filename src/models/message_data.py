"""Data models for message processing and export."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ChannelMessages:
    """Represents messages from a single Discord channel.
    
    Attributes:
        channel_id: Discord channel ID
        message_ids: List of message IDs in this channel
        message_count: Total number of messages
    """
    channel_id: str
    message_ids: List[str]
    message_count: int


@dataclass
class MessageExport:
    """Represents a complete message export from Discord data.
    
    Attributes:
        channels: List of channel message data
        total_messages: Total number of messages across all channels
        total_channels: Total number of channels processed
        export_date: Timestamp when the export was created
    """
    channels: List[ChannelMessages]
    total_messages: int
    total_channels: int
    export_date: datetime
