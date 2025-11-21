# Discord Message Delete Helper

Discord Message Delete Helper is a modern Python application with a Qt6-based GUI designed to assist users in generating a list of Discord message IDs and automatically sending deletion requests to Discord Support. The application features secure authentication, automated email generation, and a polished user interface.

## Why was this made?

Discord's approach to message deletion has been a source of frustration for many users. The platform currently does not provide an official method for bulk deleting messages, which has led to the development of this tool.

### Reasons Behind This Decision

- **Preserving Context:** Discord claims that retaining messages is necessary to maintain context in conversations, especially for collaborative projects or communities that rely on historical information.
- **Technical Limitations:** Mass deletion of messages can put a significant strain on Discord's database, which led to the removal of bulk deletion features in the past.
- **Privacy and Security Concerns:** Discord's privacy policy prevents them from reviewing message content without cause, which complicates the process of verifying requests for mass deletion.
- **Compliance with Regulations:** Discord must balance user requests with legal requirements like GDPR's Right to Erasure, which has led to changes in how they handle deletion requests.

### Discord's Measures

To address these issues while still providing some level of control to users, Discord has implemented the following measures:
- Allowing users to request their data package and submit message IDs for deletion.
- Deleting messages on both sides in private DMs but retaining placeholders in server or group chats.
- Gradually adapting their approach to GDPR compliance has affected how deletion requests are processed.

These measures, however, are often seen as inadequate by users who desire more control over their message history. The lack of an official bulk deletion feature has led to the creation of unofficial tools.

In response to this demand, some users have developed methods to generate lists of message IDs from the data provided by Discord, which can then be submitted for deletion. This approach aims to provide users with more control over their message history.

## Features

- **Modern Qt6 Interface:** Clean, intuitive GUI with sidebar navigation and card-based layouts
- **Discord OAuth2 Authentication:** Securely connect to your Discord account with visual status indicators
- **Message ID List Generation:** Compile a comprehensive list of message IDs from Discord data exports
- **Real-time Progress Tracking:** Visual progress bars and status updates during message processing
- **Automated Email Generation:** Generate formatted deletion request emails with user information
- **SMTP Email Sending:** Send deletion requests directly to Discord Support with attachments
- **Email Provider Presets:** Pre-configured settings for Gmail, Outlook, Yahoo, and custom SMTP servers
- **Secure Configuration:** Encrypted storage of sensitive data (passwords, tokens) using industry-standard encryption
- **Customizable Processing:** 
  - Select specific message directories
  - Exclude specific channel IDs
  - Configure default directories and preferences
- **Error Resilience:** Graceful handling of corrupted files with detailed error logging

## Prerequisites

- Python 3.8 or higher
- Discord Developer Account (for OAuth2 credentials)
- Email account with SMTP access (Gmail, Outlook, Yahoo, or custom SMTP server)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/discord-message-helper.git
cd discord-message-helper
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `PySide6` - Qt6 GUI framework
- `requests` - HTTP requests for Discord API
- `cryptography` - Encryption for sensitive data
- `python-dotenv` - Environment variable management
- `hypothesis` - Property-based testing (development)
- `pytest` - Unit testing framework (development)

### 3. Discord Application Configuration

1. Visit [Discord Developer Portal](https://discord.com/developers/applications/)
2. Create a new application
3. Navigate to the **OAuth2** section
4. Add `http://localhost:8000/callback` to your **Redirect URIs**
5. Copy your **Client ID** and **Client Secret**

### 4. Environment Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit the `.env` file with your Discord credentials:

```bash
# Discord OAuth Configuration
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/callback
DISCORD_SCOPE=identify email
```

**Important:** Never commit your `.env` file to version control. It contains sensitive credentials.

## Usage

### Running the Application

```bash
python src/main.py
```

Or use the provided run script:

```bash
python run_app.py
```

### Step-by-Step Guide

#### 1. Discord Authentication

1. Click the **🔐 Auth** tab in the sidebar
2. Click **Connect to Discord**
3. Your browser will open to Discord's authorization page
4. Click **Authorize** to grant the application access
5. The application will display your username, email, and user ID
6. Your authentication is saved securely for future sessions

#### 2. Process Messages

1. Click the **📁 Messages** tab in the sidebar
2. **Select Messages Directory:**
   - Click **Browse** next to "Messages Directory"
   - Navigate to your Discord data export's `messages` folder
   - The application will validate the directory structure
3. **Select Save Directory:**
   - Click **Browse** next to "Save Directory"
   - Choose where to save the message ID list
4. **Exclude Channels (Optional):**
   - Enter channel IDs to exclude, separated by commas
   - Example: `123456789012345678, 987654321098765432`
5. Click **Process Messages**
6. Watch the progress bar as channels are scanned
7. When complete, a `messages.txt` file will be saved to your chosen directory

#### 3. Configure Email (First Time)

1. Click the **✉️ Email** tab in the sidebar
2. Expand the **SMTP Configuration** section
3. **Select Email Provider:**
   - Choose from **Gmail**, **Outlook**, **Yahoo**, or **Custom**
   - Server and port are pre-filled for common providers
4. **Enter Email Credentials:**
   - Email address
   - Password (stored encrypted)
   
   **Note for Gmail users:** You must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.
5. Click **Test Connection** to verify settings
6. Your configuration is saved securely for future use

#### 4. Send Deletion Request Email

1. Review the email preview showing:
   - Your Discord username and user ID
   - Total messages and channels to be deleted
2. Ensure the message ID list file is attached
3. Click **Send Email**
4. Confirm the action in the dialog
5. Wait for confirmation that the email was sent successfully

#### 5. Settings and Preferences

1. Click the **⚙️ Settings** tab in the sidebar
2. Configure:
   - Default directories for messages and saves
   - Email provider presets
   - Application preferences
3. Use **Clear Data** to reset authentication and configuration (with confirmation)

## Email Configuration Guide

### Gmail Setup

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Select "2-Step Verification"
   - Scroll to "App passwords"
   - Generate a new app password for "Mail"
3. **In the Application:**
   - Provider: Gmail
   - Email: your.email@gmail.com
   - Password: Use the 16-character app password (no spaces)
   - Server: smtp.gmail.com (pre-filled)
   - Port: 587 (pre-filled)

### Outlook/Hotmail Setup

1. **In the Application:**
   - Provider: Outlook
   - Email: your.email@outlook.com (or @hotmail.com)
   - Password: Your regular Outlook password
   - Server: smtp-mail.outlook.com (pre-filled)
   - Port: 587 (pre-filled)

**Note:** If you have 2FA enabled, you may need to generate an app password.

### Yahoo Setup

1. **Generate an App Password:**
   - Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
   - Enable 2-Step Verification if not already enabled
   - Generate an app password
2. **In the Application:**
   - Provider: Yahoo
   - Email: your.email@yahoo.com
   - Password: Use the app password
   - Server: smtp.mail.yahoo.com (pre-filled)
   - Port: 587 (pre-filled)

### Custom SMTP Server

For other email providers:
1. Find your provider's SMTP settings (usually in their help documentation)
2. Select "Custom" as the provider
3. Enter the SMTP server address and port
4. Enter your email and password
5. Enable TLS if required (usually yes for port 587)

## Troubleshooting

### Authentication Issues

**Problem:** "OAuth flow failed" or "Could not connect to Discord"
- **Solution:** 
  - Verify your `.env` file has correct `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET`
  - Ensure `http://localhost:8000/callback` is added to your Discord app's Redirect URIs
  - Check that no other application is using port 8000
  - Try disconnecting and reconnecting

**Problem:** "User not authenticated" when trying to process messages
- **Solution:** 
  - Click the Auth tab and connect to Discord first
  - If already connected, try logging out and back in

### Message Processing Issues

**Problem:** "Invalid directory" error
- **Solution:** 
  - Ensure you're selecting the `messages` folder from your Discord data export
  - The folder should contain subdirectories with channel IDs
  - Each channel folder should have a `messages.json` file

**Problem:** "No messages found" or very few messages
- **Solution:** 
  - Verify you've downloaded your complete Discord data package
  - Check that you're not excluding channels unintentionally
  - Some channels may be empty or have no messages from you

**Problem:** Processing stops or freezes
- **Solution:** 
  - Check the `logs/app.log` file for detailed error messages
  - Some JSON files may be corrupted - the app will skip them and continue
  - Try processing a smaller subset of channels first

### Email Issues

**Problem:** "SMTP authentication failed"
- **Solution:** 
  - **Gmail:** Use an App Password, not your regular password
  - **Outlook/Yahoo:** Enable app passwords if 2FA is enabled
  - Verify your email and password are correct
  - Use the "Test Connection" button to diagnose issues

**Problem:** "Connection timeout" or "Could not connect to SMTP server"
- **Solution:** 
  - Check your internet connection
  - Verify the SMTP server address and port
  - Some networks block SMTP ports - try a different network
  - Check if your email provider requires specific security settings

**Problem:** "Attachment too large"
- **Solution:** 
  - Discord Support typically accepts attachments up to 25MB
  - If your message list is larger, consider splitting it into multiple requests
  - Compress the file before attaching

### Configuration Issues

**Problem:** "Could not load configuration" on startup
- **Solution:** 
  - Ensure `.env` file exists in the project root
  - Check that `.env` file has all required variables
  - Verify file permissions allow reading
  - Try copying from `.env.example` and filling in your values

**Problem:** Settings not saving
- **Solution:** 
  - Check file permissions in the project directory
  - Ensure `config.json` is not read-only
  - Check `logs/app.log` for permission errors

### General Issues

**Problem:** Application won't start
- **Solution:** 
  - Verify Python 3.8+ is installed: `python --version`
  - Reinstall dependencies: `pip install -r requirements.txt`
  - Check for error messages in the terminal
  - Try running with: `python -u src/main.py` for unbuffered output

**Problem:** "Module not found" errors
- **Solution:** 
  - Ensure you're in the project root directory
  - Reinstall dependencies: `pip install -r requirements.txt`
  - Check that you're using the correct Python environment

**Problem:** UI looks broken or has rendering issues
- **Solution:** 
  - Update PySide6: `pip install --upgrade PySide6`
  - Try a different Qt style (modify in Settings)
  - Check graphics drivers are up to date

### Getting Help

If you encounter issues not covered here:

1. **Check the logs:** Look in `logs/app.log` for detailed error messages
2. **Search existing issues:** Check the GitHub issues page
3. **Create a new issue:** Include:
   - Operating system and Python version
   - Error messages from logs
   - Steps to reproduce the problem
   - Screenshots if relevant (redact sensitive information)

## Project Structure

```
discord-message-helper/
├── src/
│   ├── main.py                    # Application entry point
│   ├── models/                    # Data models
│   │   ├── user.py
│   │   ├── message_data.py
│   │   └── config.py
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   ├── message_service.py
│   │   ├── email_service.py
│   │   └── config_service.py
│   ├── ui/                        # User interface
│   │   ├── main_window.py
│   │   ├── widgets/
│   │   └── styles/
│   └── utils/                     # Utilities
│       ├── crypto.py
│       ├── validators.py
│       └── migration.py
├── tests/                         # Test suite
├── logs/                          # Application logs
├── .env                           # Environment variables (not in git)
├── .env.example                   # Environment template
├── config.json                    # User configuration (encrypted)
├── requirements.txt               # Python dependencies
└── README.md
```

## Security and Privacy

- **Encrypted Storage:** Email passwords and OAuth tokens are encrypted using Fernet symmetric encryption
- **Local Processing:** All message processing happens locally on your machine
- **No Data Collection:** The application does not send your data anywhere except to Discord (for auth) and your email server
- **Secure Logging:** Sensitive information (passwords, tokens) is automatically redacted from log files
- **Environment Variables:** Secrets are stored in `.env` file which is excluded from version control

## Migration from Old Version

If you're upgrading from the old version (using `gui.py`, `server.py`, `config.py`):

1. **Backup your data:**
   ```bash
   cp data.txt data.txt.backup
   cp config.py config.py.backup
   ```

2. **Run the migration:**
   - The application will automatically detect old configuration files
   - On first run, it will migrate `config.py` to `.env`
   - User data from `data.txt` will be migrated to encrypted `config.json`
   - Backups are created automatically

3. **Verify migration:**
   - Check that `.env` file was created with your Discord credentials
   - Verify you can authenticate successfully
   - Old files will be renamed with `.backup` extension

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest tests/`
4. Run property-based tests: `pytest tests/ -k property`

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for public methods
- Add tests for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) for the modern Qt6 interface
- Uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing
- Encryption provided by [cryptography](https://cryptography.io/)

## Disclaimer

This tool is provided as-is for educational purposes. Use at your own risk. Always ensure you comply with Discord's Terms of Service and applicable laws when requesting data deletion.