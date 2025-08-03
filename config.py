"""
Flask application configuration.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    DB_NAME = os.getenv('DB_NAME', 'transcript_cleaner')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'csv'}
    
    # OpenAI API settings - Prioritize system environment variables
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    
    # Cost management
    DEFAULT_USER_COST_LIMIT = 10.00  # USD
    
    # Mail settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Pagination
    POSTS_PER_PAGE = 20
    
    # Language settings
    LANGUAGES = ['en', 'ja']
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    @classmethod
    def validate_config(cls):
        """Validate production configuration."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if not all([Config.DB_USER, Config.DB_PASSWORD, Config.DB_NAME]):
            raise ValueError("Database configuration is incomplete")


class TestingConfig(Config):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
