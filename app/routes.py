"""
Main application routes.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from flask_login import current_user, login_required
from app.models import TranscriptDocument, CorrectionJob
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Redirect to processing screen when logged in; otherwise login page via Flask-Login."""
    return redirect(url_for('transcripts.index'))


@bp.route('/set_language/<lang>')
def set_language(lang):
    """Set language preference."""
    if lang in ['en', 'ja']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': str(db.session.execute('SELECT NOW()').scalar())})
