"""
Flask application factory.
"""
import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_babel import Babel
# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
babel = Babel()


def create_app(config_name=None):
    """Application factory pattern."""
    # Set correct template and static folder paths
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'ログインが必要です。'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.auth.social import social_bp, google_bp, facebook_bp
    app.register_blueprint(social_bp, url_prefix='/auth')
    app.register_blueprint(google_bp, url_prefix='/login')
    app.register_blueprint(facebook_bp, url_prefix='/login')
    
    from app.transcripts import bp as transcripts_bp
    app.register_blueprint(transcripts_bp, url_prefix='/transcripts')
    
    from app.corrections import bp as corrections_bp
    app.register_blueprint(corrections_bp, url_prefix='/corrections')
    
    from app.wordlists import bp as wordlists_bp
    app.register_blueprint(wordlists_bp, url_prefix='/wordlists')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Main routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        from flask import flash, redirect, url_for
        flash('ファイルサイズが大きすぎます。10MB以下のファイルをアップロードしてください。', 'error')
        return redirect(url_for('main.index'))
    
    # Babel locale selector
    def get_locale():
        # Check if user has manually set a language preference
        from flask import session
        if 'language' in session:
            return session['language']
        
        # Fall back to browser's preferred language
        return request.accept_languages.best_match(app.config['LANGUAGES'])
    
    # Initialize Babel with locale selector
    babel.init_app(app, locale_selector=get_locale)
    
    # Shell context processor
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, TranscriptDocument, CorrectionJob, WordList
        return {
            'db': db,
            'User': User,
            'TranscriptDocument': TranscriptDocument,
            'CorrectionJob': CorrectionJob,
            'WordList': WordList
        }
    
    return app
