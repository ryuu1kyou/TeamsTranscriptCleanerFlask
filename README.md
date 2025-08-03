# Teams Transcript Cleaner

A Flask-based web application for cleaning and processing Microsoft Teams meeting transcripts.

## Features

- **Transcript Upload**: Upload Teams transcript files (.docx)
- **AI-Powered Cleaning**: Uses OpenAI GPT to clean and format transcripts
- **Word List Management**: Create and manage custom word lists for corrections
- **Social Login**: Google, GitHub, and Microsoft OAuth integration
- **Admin Dashboard**: Manage users and system settings
- **Responsive Design**: Works on desktop and mobile devices
- **Multi-language Support**: Japanese and English with browser-based auto-detection

## Quick Start

### ⚠️ Virtual Environment Required

**重要: このプロジェクトは仮想環境での開発が必須です。**

システムのPython環境を汚染しないため、必ず仮想環境を作成してから作業を開始してください。以下の手順に従ってください：

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/ryuu1kyou/TeamsTranscriptCleanerFlask.git
cd TeamsTranscriptCleanerFlask

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost/teams_transcript_cleaner
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Social Login (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### 3. Database Setup

```bash
# Initialize database
./venv/bin/python -m flask db upgrade

# Create admin user (optional)
./venv/bin/python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin@example.com / admin123')
"
```

### 4. Run Application

```bash
# Development server
./venv/bin/python -m flask run

# Or use the main app
./venv/bin/python app.py
```

Access at: http://localhost:5000

## Multi-language Support

The application automatically detects browser language settings and supports:
- **Japanese (日本語)**
- **English**

### Manual Language Switching
Users can manually switch languages using the language dropdown in the navigation bar.

### Adding New Languages
1. Extract translatable strings:
   ```bash
   pybabel extract -F babel.cfg -o messages.pot .
   ```
2. Initialize new language:
   ```bash
   pybabel init -i messages.pot -d app/translations -l [language-code]
   ```
3. Edit translation files in `app/translations/[language-code]/LC_MESSAGES/messages.po`
4. Compile translations:
   ```bash
   pybabel compile -d app/translations
   ```

## Social Login Setup

### Google OAuth Setup 

#### Prerequisites

- Google Cloud Console にログインしていること
- OAuth 2.0 を設定したい Google Cloud プロジェクト (teams-transcript-cleaner-flask) が選択されていること

#### Step 1: OAuth Consent Screen Setup

1. Navigate to **"APIs & Services" > "OAuth consent screen"**
2. Select **"External"** for user type (for public apps)
3. Click **"Create"**
4. Fill in app information:
   - **App name**: Teams Transcript Cleaner
   - **User support email**: Your Gmail address
   - **Developer contact email**: Your Gmail address
5. Click **"Save and Continue"**

#### Step 2: Add Scopes

1. Click **"Add or remove scopes"**
2. Add these scopes:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `openid`
3. Click **"Update"**
4. Click **"Save and Continue"**

#### Step 3: Add Test Users

1. In **"Test users"** section, click **"Add users"**
2. Add your Gmail address
3. Click **"Add"**
4. Click **"Save and Continue"**

#### Step 4: Create OAuth Client ID

1. Navigate to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials" > "OAuth client ID"**
3. Select **"Web application"**
4. Name: `teams-transcript-cleaner-local`
5. Add authorized redirect URI:
   ```
   http://localhost:5000/auth/login/google/callback
   ```
6. Click **"Create"**

#### Step 5: Copy Credentials

Copy the displayed **Client ID** and **Client Secret** to your `.env` file.

### GitHub OAuth Setup

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click **"New OAuth App"**
3. Fill in:
   - **Application name**: Teams Transcript Cleaner
   - **Homepage URL**: http://localhost:5000
   - **Authorization callback URL**: http://localhost:5000/auth/login/github/callback
4. Copy **Client ID** and **Client Secret**

### Microsoft OAuth Setup

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click **"New registration"**
3. Fill in:
   - **Name**: Teams Transcript Cleaner
   - **Redirect URI**: http://localhost:5000/auth/login/microsoft/callback
4. Copy **Application (client) ID** and create **Client Secret**

## Usage

### Upload Transcripts

1. Register/login to the application
2. Click **"Upload Transcript"**
3. Select your Teams transcript file (.docx)
4. Choose processing options
5. Submit for processing

### Manage Word Lists

1. Go to **"Word Lists"** in navigation
2. Create new word lists for specific corrections
3. Upload CSV files with word mappings
4. Apply word lists during transcript processing

### View Results

1. Go to **"My Transcripts"**
2. Click on processed transcripts to view
3. Download cleaned versions
4. Make manual corrections if needed

## Development

### Project Structure

```
TeamsTranscriptCleanerFlask/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes.py            # Main routes
│   ├── auth/                # Authentication
│   ├── transcripts/         # Transcript handling
│   ├── corrections/         # Correction management
│   ├── wordlists/           # Word list management
│   └── admin/               # Admin functionality
├── migrations/              # Database migrations
├── static/                  # CSS, JS, images
├── templates/               # HTML templates
├── processing/              # AI processing logic
├── translations/            # Multi-language support
└── uploads/                 # Uploaded files
```

### Database Migrations

```bash
# Create new migration
./venv/bin/python -m flask db migrate -m "description"

# Apply migrations
./venv/bin/python -m flask db upgrade

# Downgrade migration
./venv/bin/python -m flask db downgrade
```

### Translation Management

```bash
# Extract new translatable strings
pybabel extract -F babel.cfg -o messages.pot .

# Update existing translations
pybabel update -i messages.pot -d app/translations

# Compile translations
pybabel compile -d app/translations
```

### Testing

```bash
# Run tests
./venv/bin/python -m pytest tests/

# Run with coverage
./venv/bin/python -m pytest tests/ --cov=app
```

## Troubleshooting

### Database Issues

```bash
# Reset database
rm instance/app.db
./venv/bin/python -m flask db upgrade

# Check migration status
./venv/bin/python -m flask db current
./venv/bin/python -m flask db history
```

### OAuth Issues

- **redirect_uri_mismatch**: Check redirect URI in OAuth settings
- **invalid_client**: Verify client ID and secret in .env
- **access_denied**: Ensure test user is added in OAuth console

### Common Errors

- **ImportError: Can't find Python file migrations/env.py**: Reinitialize migrations
- **Database connection errors**: Check DATABASE_URL in .env
- **OpenAI API errors**: Verify OPENAI_API_KEY is set

## Docker Support

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t teams-transcript-cleaner .
docker run -p 5000:5000 teams-transcript-cleaner
```

## License

MIT License - see LICENSE file for details

## Social Login Usage Notes

### Important Considerations for Social Account Login

#### Account Linking Behavior

- **Email Matching**: When you log in with a social account (Google/Facebook), the system automatically links to an existing account if the email address matches
- **Username Generation**: If no existing account is found, a new account is created with a username derived from your email (e.g., "user" from "user@example.com")
- **Username Conflicts**: If the generated username already exists, a number is appended (e.g., "user1", "user2")

#### Security Features

- **Automatic Verification**: Social login accounts are automatically marked as email-verified
- **No Password Required**: Social login accounts don't require a password for the application
- **Session Management**: Sessions are managed by the social provider's OAuth tokens

#### Data Privacy

- **Minimal Data Collection**: Only essential information (email, name, profile ID) is retrieved from social providers
- **No Password Storage**: Your social media passwords are never stored or accessed
- **Revocable Access**: You can revoke application access anytime through your social account settings

#### Account Management

- **Unlinking Social Accounts**: You can unlink your social account from your profile page
- **Multiple Social Accounts**: Currently supports linking one social provider per account
- **Fallback Login**: After unlinking, you can still log in with email/password if set up

#### Provider-Specific Notes

##### Google Login

- **Scopes**: Requests access to your basic profile and email address
- **Offline Access**: Enabled for potential future calendar integration
- **Test Mode**: Requires adding test users in Google Cloud Console during development

##### Facebook Login

- **Scopes**: Requests access to your public profile and email address
- **App Review**: Facebook apps require review for production use
- **Test Users**: Use Facebook's test user feature for development

#### Development Tips

- **Local Testing**: Use localhost:5000 for redirect URIs during development
- **HTTPS Requirement**: Social providers require HTTPS in production (except for localhost)
- **Environment Variables**: Ensure all OAuth credentials are properly set in .env file

#### Migration from Email/Password to Social Login

- **Existing Accounts**: If you have an existing email/password account with the same email, social login will automatically link to it
- **Password Retention**: Your original password remains available as a fallback login method
- **Profile Sync**: Basic profile information (name) may be updated from social provider data

#### Production Deployment

- **HTTPS Required**: All social providers require HTTPS in production environments
- **Domain Verification**: Ensure your production domain is properly configured in OAuth settings
- **Rate Limits**: Be aware of API rate limits for social login providers
