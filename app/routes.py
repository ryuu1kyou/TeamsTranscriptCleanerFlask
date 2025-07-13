"""
Main routes for Flask application.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/index')
def index():
    """Home page."""
    # Get user statistics if logged in
    user_stats = {}
    if current_user.is_authenticated:
        user_stats = {
            'transcripts': current_user.transcripts.count(),
            'jobs': current_user.correction_jobs.count(),
            'wordlists': current_user.wordlists.count(),
            'api_cost': current_user.total_api_cost
        }
    
    return render_template('index.html', user_stats=user_stats)


@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html', title='について')


@bp.route('/help')
def help():
    """Help page."""
    return render_template('help.html', title='ヘルプ')


@bp.route('/dashboard')
def dashboard():
    """Dashboard - redirects to appropriate main page."""
    if current_user.is_authenticated:
        return redirect(url_for('transcripts.list'))
    return redirect(url_for('auth.login'))