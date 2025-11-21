"""User data model for Discord authentication."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Represents an authenticated Discord user.
    
    Attributes:
        id: Discord user ID
        username: Discord username
        email: User's email address
        verified: Whether the email is verified
        access_token: OAuth access token (optional, encrypted when stored)
    """
    id: str
    username: str
    email: str
    verified: bool
    access_token: Optional[str] = None
