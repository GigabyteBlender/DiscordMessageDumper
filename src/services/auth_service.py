"""Authentication service for Discord OAuth flow."""

import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional, Callable
import requests
import threading
import logging

from src.models.user import User
from src.models.config import EnvConfig
from src.utils.crypto import encrypt_password, decrypt_password


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""
    
    auth_code: Optional[str] = None
    error: Optional[str] = None
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        # Parse the query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # Check for authorization code
        if 'code' in query_params:
            OAuthCallbackHandler.auth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #5865F2;">Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
            """)
        elif 'error' in query_params:
            OAuthCallbackHandler.error = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #ED4245;">Authentication Failed</h1>
                    <p>Error: {query_params['error'][0]}</p>
                    <p>You can close this window and try again.</p>
                </body>
                </html>
            """.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Invalid Request</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #ED4245;">Invalid Request</h1>
                    <p>No authorization code received.</p>
                </body>
                </html>
            """)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class AuthService:
    """Service for handling Discord OAuth authentication.
    
    Manages the OAuth flow, token exchange, user data fetching,
    and authentication state persistence.
    """
    
    DISCORD_API_BASE = "https://discord.com/api/v10"
    DISCORD_OAUTH_BASE = "https://discord.com/api/oauth2"
    
    def __init__(self, env_config: EnvConfig, auth_file: str = "auth.json"):
        """Initialize the authentication service.
        
        Args:
            env_config: Environment configuration with OAuth credentials
            auth_file: Path to the authentication state file
        """
        self.env_config = env_config
        self.auth_file = auth_file
        self._current_user: Optional[User] = None
        self._load_auth_state()
    
    def start_oauth_flow(self) -> str:
        """Initialize OAuth flow and return authorization URL.
        
        Opens the Discord OAuth authorization page in the default browser.
        
        Returns:
            str: The OAuth authorization URL
        """
        # Build authorization URL
        params = {
            'client_id': self.env_config.discord_client_id,
            'redirect_uri': self.env_config.discord_redirect_uri,
            'response_type': 'code',
            'scope': self.env_config.discord_scope
        }
        
        auth_url = f"{self.DISCORD_OAUTH_BASE}/authorize?{urlencode(params)}"
        
        # Open in browser
        webbrowser.open(auth_url)
        
        return auth_url
    
    def handle_oauth_callback(self, code: str) -> User:
        """Handle OAuth callback and exchange code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            User: Authenticated user object with user data
            
        Raises:
            ValueError: If code is empty or invalid
            requests.RequestException: If token exchange or user fetch fails
        """
        if not code or not code.strip():
            raise ValueError("Authorization code cannot be empty")
        
        # Exchange code for access token
        token_data = self._exchange_code_for_token(code)
        access_token = token_data['access_token']
        
        # Fetch user data
        user_data = self._fetch_user_data(access_token)
        
        # Create User object
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email', ''),
            verified=user_data.get('verified', False),
            access_token=access_token
        )
        
        # Store user and persist
        self._current_user = user
        self._save_auth_state()
        
        return user
    
    def wait_for_oauth_callback(self, timeout: int = 300) -> User:
        """Start local server and wait for OAuth callback.
        
        This method starts a local HTTP server to receive the OAuth callback,
        waits for the authorization code, and then exchanges it for user data.
        
        Args:
            timeout: Maximum time to wait for callback in seconds (default: 300)
            
        Returns:
            User: Authenticated user object
            
        Raises:
            TimeoutError: If no callback received within timeout
            ValueError: If OAuth error occurred
            requests.RequestException: If token exchange fails
        """
        import time
        logger = logging.getLogger(__name__)
        
        # Parse redirect URI to get host and port
        parsed_uri = urlparse(self.env_config.discord_redirect_uri)
        host = parsed_uri.hostname or 'localhost'
        port = parsed_uri.port or 8000
        
        logger.info(f"Starting OAuth callback server on {host}:{port}")
        
        # Reset callback handler state
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None
        
        # Start HTTP server
        server = HTTPServer((host, port), OAuthCallbackHandler)
        server.timeout = 1  # Set timeout for each request to 1 second
        
        # Function to run server and handle multiple requests
        def run_server():
            while OAuthCallbackHandler.auth_code is None and OAuthCallbackHandler.error is None:
                server.handle_request()
        
        # Run server in a separate thread
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info("OAuth callback server started, waiting for callback...")
        
        # Wait for callback with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if OAuthCallbackHandler.auth_code or OAuthCallbackHandler.error:
                logger.info("OAuth callback received!")
                break
            time.sleep(0.1)  # Check every 100ms
        
        # Shutdown server - do this in a separate thread to avoid deadlock
        logger.info("Shutting down OAuth callback server...")
        def shutdown_server():
            try:
                server.shutdown()
                server.server_close()
                logger.info("OAuth callback server shut down successfully")
            except Exception as e:
                logger.warning(f"Error shutting down server: {e}")
        
        shutdown_thread = threading.Thread(target=shutdown_server)
        shutdown_thread.daemon = True
        shutdown_thread.start()
        
        # Give it a moment to shutdown, but don't wait too long
        shutdown_thread.join(timeout=2)
        
        # Check if we got a response
        if OAuthCallbackHandler.error:
            logger.error(f"OAuth error: {OAuthCallbackHandler.error}")
            raise ValueError(f"OAuth error: {OAuthCallbackHandler.error}")
        
        if not OAuthCallbackHandler.auth_code:
            logger.error("OAuth callback timeout")
            raise TimeoutError("No OAuth callback received within timeout period")
        
        # Exchange code for user data
        logger.info("Exchanging authorization code for access token...")
        user = self.handle_oauth_callback(OAuthCallbackHandler.auth_code)
        logger.info(f"Successfully authenticated user: {user.username}")
        return user
    
    def get_current_user(self) -> Optional[User]:
        """Get the currently authenticated user.
        
        Returns:
            Optional[User]: Current user if authenticated, None otherwise
        """
        return self._current_user
    
    def logout(self) -> None:
        """Logout the current user and clear authentication data.
        
        Clears the current user and removes the authentication state file.
        """
        self._current_user = None
        
        # Remove auth file if it exists
        if os.path.exists(self.auth_file):
            os.remove(self.auth_file)
    
    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated.
        
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return self._current_user is not None
    
    def _exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            dict: Token response data including access_token
            
        Raises:
            requests.RequestException: If token exchange fails
        """
        token_url = f"{self.DISCORD_OAUTH_BASE}/token"
        
        data = {
            'client_id': self.env_config.discord_client_id,
            'client_secret': self.env_config.discord_client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.env_config.discord_redirect_uri
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def _fetch_user_data(self, access_token: str) -> dict:
        """Fetch user data from Discord API.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            dict: User data from Discord API
            
        Raises:
            requests.RequestException: If user data fetch fails
        """
        user_url = f"{self.DISCORD_API_BASE}/users/@me"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(user_url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def _save_auth_state(self) -> None:
        """Save authentication state to file.
        
        Encrypts the access token before saving.
        """
        if not self._current_user:
            return
        
        # Prepare data for serialization
        data = {
            'id': self._current_user.id,
            'username': self._current_user.username,
            'email': self._current_user.email,
            'verified': self._current_user.verified
        }
        
        # Encrypt and store access token if present
        if self._current_user.access_token:
            data['access_token'] = encrypt_password(self._current_user.access_token)
        
        # Write to file
        with open(self.auth_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_auth_state(self) -> None:
        """Load authentication state from file.
        
        Decrypts the access token after loading.
        """
        if not os.path.exists(self.auth_file):
            self._current_user = None
            return
        
        try:
            with open(self.auth_file, 'r') as f:
                data = json.load(f)
            
            # Decrypt access token if present
            access_token = None
            if data.get('access_token'):
                try:
                    access_token = decrypt_password(data['access_token'])
                except Exception:
                    # If decryption fails, treat as no token
                    access_token = None
            
            # Create User object
            self._current_user = User(
                id=data['id'],
                username=data['username'],
                email=data.get('email', ''),
                verified=data.get('verified', False),
                access_token=access_token
            )
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # If file is corrupted or missing, treat as not authenticated
            self._current_user = None
