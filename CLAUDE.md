# Teams Transcript Cleaner

A Flask-based web application for cleaning and processing Microsoft Teams meeting transcripts.

## Features

- **Transcript Upload**: Upload Teams transcript text files (.txt) and optional typo correction list (.csv)
- **AI-Powered Cleaning**: Uses OpenAI GPT to clean and format transcripts
- **Word List Management**: Create and manage custom word lists for corrections
- **Social Login**: Google OAuth integration
- **Admin Dashboard**: Manage users and system settings
- **Responsive Design**: Works on desktop and mobile devices
- **Multi-language (Japanese/English) interface via Flask-Babel**
- **Transcript revision history**: every finalized download stores a revision (TranscriptRevision) enabling per-user 議事録修正履歴 browsing
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
# Database (MySQL)
DB_NAME=transcript_cleaner_flask
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Social Login (Google only)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

### 3. Database Setup

```bash
# Initialize database (Alembic)
./venv/bin/python -m flask db init
./venv/bin/python -m flask db migrate -m "Initial"
./venv/bin/python -m flask db upgrade

# Or (development quick start)
./venv/bin/python -m flask init-db

# Create admin user (optional)
./venv/bin/python -m flask create-admin
```

### 4. Run Application

```bash
# Development server
./venv/bin/python -m flask run

# Or use the main app
./venv/bin/python app.py
```

Access at: <http://localhost:5000>

## Detailed MySQL + Flask Initialization Guide (From Fresh Machine)

The following end-to-end steps cover setting up MySQL, preparing the virtual environment, applying migrations, and creating initial data (admin + sample records) on a brand new development PC.

### 0. Prerequisites

- OS: Linux (Debian/Ubuntu family assumed)
- Python 3.12+ (matching your virtualenv)
- Git installed

### 1. Install & Start MySQL

```bash
sudo apt update
sudo apt install -y mysql-server mysql-client
sudo systemctl enable --now mysql
```
Optional hardening (prompts to set root password, remove anonymous users, etc.):
```bash
sudo mysql_secure_installation
```

### (Optional) Updating Translations After UI Changes

Whenever you add or modify translatable strings in Python or Jinja templates (wrapping them in `_(...)`), re-run the translation maintenance command to extract, update, and compile catalogs:

```bash
flask --app app:create_app compile-translations
```

Then edit the generated `app/translations/<locale>/LC_MESSAGES/messages.po` files to provide missing translations and re-run the command to compile updated `.mo` files. Strings embedded in JavaScript via Jinja (e.g. `document.getElementById('pricingInfo').textContent = "{{ _('料金') }}: " + value;`) are also picked up because the extractor scans templates.

### 2. (Recommended) Create Dedicated App User & Database

Log into MySQL (many distros allow socket login for root):

```bash
sudo mysql
```

Inside the MySQL shell:

```sql
CREATE DATABASE IF NOT EXISTS transcript_cleaner_flask
   CHARACTER SET utf8mb4
   COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'transcript_user'@'localhost' IDENTIFIED BY 'ChangeMe123!';
GRANT ALL PRIVILEGES ON transcript_cleaner_flask.* TO 'transcript_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

If you insist on using `root` with a password (and encounter plugin `auth_socket` issues), you can switch to native password:
```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YourRootPass!';
FLUSH PRIVILEGES;
```

### 3. Clone Repository & Virtual Environment

```bash
git clone https://github.com/ryuu1kyou/TeamsTranscriptCleanerFlask.git
cd TeamsTranscriptCleanerFlask
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` (minimal example):

```dotenv
FLASK_ENV=development
SECRET_KEY=dev-change-me
DB_NAME=transcript_cleaner_flask
DB_USER=transcript_user
DB_PASSWORD=ChangeMe123!
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=your-openai-key   # (optional now)
JWT_SECRET_KEY=dev-jwt-secret
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
```

### 5. Run Database Migrations (Alembic)

The project already contains a populated `migrations/` directory, so do NOT run `flask db init` again.

```bash
flask db migrate -m "sync"   # (Should detect no changes if in sync; optional)
flask db upgrade
```
If `flask db migrate` reports new tables on a clean DB, that's normal for first run.

### 6. (If Needed) Recreate Missing `migrations/versions/` Folder

If you ever see `FileNotFoundError` for a revision path, create the folder:

```bash
mkdir -p migrations/versions
flask db migrate -m "initial schema"
flask db upgrade
```

### 7. Register CLI Commands (App Factory Pattern)

This project uses an application factory (`create_app`). Custom CLI commands are registered inside `create_app` via `app/cli.py`.

Use the explicit factory reference to ensure the commands load:
```bash
flask --app app:create_app --help | grep create-admin
```

### 8. Create Admin User

```bash
flask --app app:create_app create-admin
# Output example: Admin user created: admin@example.com / admin123
```
Immediately change the password later via the UI or a script.

### 9. (Optional) Seed Test Data

```bash
flask --app app:create_app create-test-data
```

### 10. Verify Tables Manually (Optional)

```bash
mysql -u $DB_USER -p$DB_PASSWORD -e "USE $DB_NAME; SHOW TABLES;"
```
Expected tables: `alembic_version, roles, users, transcript_documents, wordlists, correction_jobs, shared_wordlists`.

### 11. Run the Development Server

```bash
flask --app app:create_app run
```
Access: <http://127.0.0.1:5000>

### 12. Common Issues & Resolutions

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Access denied for user 'root'@'localhost'` | `auth_socket` plugin vs password | Create dedicated user or alter root to native password |
| `No such command 'create-admin'` | App factory not referenced | Use `--app app:create_app` |
| `FileNotFoundError` for versions path` | Missing `migrations/versions` dir | `mkdir -p migrations/versions` then migrate |
| `No changes in schema detected` on first migrate | DB already matches models | Just run `flask db upgrade` |
| Google OAuth secret appears with spaces | Copy artifact / leaked secret | Regenerate in GCP console |

### 13. Quick Reset (Drop & Reapply)

```bash
mysql -u $DB_USER -p$DB_PASSWORD -e "DROP DATABASE IF EXISTS $DB_NAME; CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
flask db upgrade
flask --app app:create_app create-admin
```

### 14. SQLite (Temporary Alternative)

If MySQL is unavailable but you want to test UI fast:

```bash
export SQLALCHEMY_DATABASE_URI=sqlite:///dev.db
flask --app app:create_app db upgrade
flask --app app:create_app run
```

---
This section documents the exact working sequence validated on a clean environment (2025-09-01).

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

   ```bash
   # Redirect URI (copy line below without the comment)
   http://localhost:5000/login/google/authorized
   ```
6. Click **"Create"**

#### Step 5: Copy Credentials

Copy the displayed **Client ID** and **Client Secret** to your `.env` file.


## Usage

### Upload Transcripts

1. Register/login to the application
2. Click **"Upload Transcript"**
3. Select your Teams transcript file (.txt) and optional typo list (.csv)
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
# Reset database (MySQL)
mysql -u ${DB_USER:-root} -p -e "DROP DATABASE IF EXISTS ${DB_NAME:-transcript_cleaner_flask}; CREATE DATABASE ${DB_NAME:-transcript_cleaner_flask} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Re-run migrations
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

## License

MIT License - see LICENSE file for details

## Social Login Usage Notes

### Important Considerations for Social Account Login

#### Account Linking Behavior

- **Email Matching**: When you log in with a social account (Google), the system automatically links to an existing account if the email address matches
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
