#!/usr/bin/env python
"""
Flask version setup script for Teams Transcript Cleaner.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_prerequisites():
    """Check if required software is installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} found")
    
    # Check if MySQL is available (optional check)
    try:
        subprocess.run("mysql --version", shell=True, check=True, capture_output=True)
        print("✅ MySQL found")
    except subprocess.CalledProcessError:
        print("⚠️  MySQL not found - please ensure MySQL is installed and running")
    
    return True

def setup_virtual_environment():
    """Create and activate virtual environment."""
    if not os.path.exists('venv'):
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activation_script = "venv\\Scripts\\activate"
        pip_command = "venv\\Scripts\\pip"
    else:  # Unix-like
        activation_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
    
    print(f"📝 To activate virtual environment manually, run: {activation_script}")
    return pip_command

def install_dependencies(pip_command):
    """Install Python dependencies."""
    return run_command(f"{pip_command} install -r requirements.txt", "Installing Python dependencies")

def setup_environment_file():
    """Create .env file from template."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command("cp .env.example .env", "Creating .env file from template")
            print("\n📝 環境設定について:")
            print("   - DB_PASSWORD: MySQL パスワードを .env に設定")
            print("   - SECRET_KEY: 安全な秘密鍵を .env に設定")
            print("\n🔒 セキュリティ重要:")
            print("   - OpenAI APIキーはシステム環境変数で設定することを強く推奨:")
            print("     export OPENAI_API_KEY='your-api-key-here'")
            print("   - .env ファイルはgitignoreに含まれています")
        else:
            print("⚠️  .env.example not found")
    else:
        print("✅ .env file already exists")

def initialize_database(pip_command):
    """Initialize the database."""
    print("\n🗄️  Database setup...")
    print("📝 Please ensure:")
    print("   1. MySQL is running")
    print("   2. Database 'transcript_cleaner_flask' is created")
    print("   3. Database credentials are set in .env file")
    
    response = input("\nProceed with database initialization? (y/n): ")
    if response.lower() != 'y':
        print("⏭️  Skipping database initialization")
        return True
    
    # Set Flask app environment variable
    os.environ['FLASK_APP'] = 'app.py'
    
    if os.name == 'nt':  # Windows
        flask_command = "venv\\Scripts\\flask"
    else:  # Unix-like
        flask_command = "venv/bin/flask"
    
    success = True
    success &= run_command(f"{flask_command} init-db", "Initializing database")
    success &= run_command(f"{flask_command} create-test-data", "Creating test data")
    
    if success:
        print("\n🎉 Database initialized successfully!")
        print("Test accounts created:")
        print("  Admin: admin@example.com / admin123")
        print("  User:  test@example.com / test123")
    
    return success

def run_development_server():
    """Ask user if they want to start the development server."""
    response = input("\nStart development server? (y/n): ")
    if response.lower() == 'y':
        print("\n🚀 Starting Flask development server...")
        print("   Server will be available at: http://127.0.0.1:5000")
        print("   Press Ctrl+C to stop the server")
        
        try:
            if os.name == 'nt':  # Windows
                subprocess.run("venv\\Scripts\\python app.py", shell=True)
            else:  # Unix-like
                subprocess.run("venv/bin/python app.py", shell=True)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

def main():
    """Main setup function."""
    print("🎯 Teams Transcript Cleaner - Flask Version Setup")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup virtual environment
    pip_command = setup_virtual_environment()
    if not pip_command:
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(pip_command):
        sys.exit(1)
    
    # Setup environment file
    setup_environment_file()
    
    # Initialize database
    if not initialize_database(pip_command):
        print("⚠️  Database initialization failed. You can run it manually later:")
        print("   flask init-db")
        print("   flask create-test-data")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your credentials")
    print("2. Ensure MySQL database is created")
    print("3. Run: python app.py (or flask run)")
    print("4. Open: http://127.0.0.1:5000")
    
    # Optionally start development server
    run_development_server()

if __name__ == '__main__':
    main()