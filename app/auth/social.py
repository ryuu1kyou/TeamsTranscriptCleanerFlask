"""
Social login routes using Flask-Dance.
"""
import os
from flask import Blueprint, url_for, redirect, flash, current_app, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_login import login_user, current_user
from app import db
from app.models import User, TemporaryUser

# Create social login blueprint
social_bp = Blueprint('social', __name__)

# Configure OAuth to allow HTTP for development
import os
if os.getenv('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# Google OAuth setup
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="social.google_authorized",
    offline=True
)

# Facebook OAuth setup (optional)
facebook_bp = make_facebook_blueprint(
    client_id=os.getenv("FACEBOOK_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET"),
    scope=["email"],
    redirect_to="social.facebook_authorized"
)

def create_or_get_user(provider, user_info):
    """
    Create temporary user or get existing DB user from social login.
    
    Args:
        provider: Social provider name ('google', 'facebook', etc.)
        user_info: Dictionary containing user information from provider
    
    Returns:
        User object (either TemporaryUser or regular User)
    """
    # Check if user already exists in DB with this email
    db_user = User.query.filter_by(email=user_info['email']).first()
    
    if db_user:
        # Return existing DB user (likely an admin or specially registered user)
        if not db_user.social_id:
            db_user.social_id = user_info['id']
            db_user.social_provider = provider
            db.session.commit()
        return db_user
    
    # Create temporary user (not stored in DB)
    temp_user = TemporaryUser(user_info, provider)
    
    # Store temporary user data in session
    session['temp_user_data'] = {
        'id': temp_user.id,
        'provider': provider,
        'info': user_info
    }
    
    return temp_user

@social_bp.route("/login/google")
def google_login():
    """Initiate Google login."""
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("google.login"))

@social_bp.route("/login/google/authorized")
def google_authorized():
    """Google OAuth callback."""
    if not google.authorized:
        flash('Google login failed', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            flash('Failed to retrieve Google user information', 'error')
            return redirect(url_for('auth.login'))
        
        user_info = resp.json()
        user = create_or_get_user('google', user_info)
        
        if user.is_active:
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        current_app.logger.error(f"Google login error: {str(e)}")
        flash('An error occurred during Google login', 'error')
        return redirect(url_for('auth.login'))

@social_bp.route("/login/facebook")
def facebook_login():
    """Initiate Facebook login."""
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))
    return redirect(url_for("facebook.login"))

@social_bp.route("/login/facebook/authorized")
def facebook_authorized():
    """Facebook OAuth callback."""
    if not facebook.authorized:
        flash('Facebook login failed', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        resp = facebook.get("/me?fields=id,email,name,first_name,last_name")
        if not resp.ok:
            flash('Failed to retrieve Facebook user information', 'error')
            return redirect(url_for('auth.login'))
        
        user_info = resp.json()
        user_info['given_name'] = user_info.get('first_name', '')
        user_info['family_name'] = user_info.get('last_name', '')
        
        user = create_or_get_user('facebook', user_info)
        
        if user.is_active:
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        current_app.logger.error(f"Facebook login error: {str(e)}")
        flash('An error occurred during Facebook login', 'error')
        return redirect(url_for('auth.login'))

@social_bp.route("/unlink/<provider>")
def unlink_social_account(provider):
    """Unlink social account from user."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if current_user.social_provider == provider:
        current_user.social_id = None
        current_user.social_provider = None
        current_user.social_data = None
        db.session.commit()
        flash(f'{provider.title()} account unlinked', 'success')
    
    return redirect(url_for('auth.profile'))
