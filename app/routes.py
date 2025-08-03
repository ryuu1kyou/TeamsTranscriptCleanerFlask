"""
Main application routes.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from flask_login import current_user
from app.models import TranscriptDocument, CorrectionJob
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        # Get user's recent transcripts
        recent_transcripts = TranscriptDocument.query.filter_by(
            user_id=current_user.id
        ).order_by(
            TranscriptDocument.created_at.desc()
        ).limit(5).all()
        
        # Get user's recent correction jobs
        recent_corrections = CorrectionJob.query.filter_by(
            user_id=current_user.id
        ).order_by(
            CorrectionJob.created_at.desc()
        ).limit(5).all()
        
        return render_template('index.html',
                             recent_transcripts=recent_transcripts,
                             recent_corrections=recent_corrections)
    
    return render_template('index.html')

@bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@bp.route('/help')
def help():
    """Help page."""
    return render_template('help.html')

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
