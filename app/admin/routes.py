"""
Admin routes for Flask application.
"""
from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.admin import bp
from app.models import User, TranscriptDocument, CorrectionJob, WordList


@bp.route('/')
@login_required
def dashboard():
    """Admin dashboard."""
    # Simple admin check - in production, use proper role-based access
    if not current_user.email.endswith('@admin.com') and current_user.username != 'admin':
        flash('管理者権限が必要です。', 'error')
        return redirect(url_for('main.index'))
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_transcripts': TranscriptDocument.query.count(),
        'total_jobs': CorrectionJob.query.count(),
        'total_wordlists': WordList.query.count(),
        'recent_users': User.query.order_by(User.created_at.desc()).limit(5).all(),
        'recent_jobs': CorrectionJob.query.order_by(CorrectionJob.created_at.desc()).limit(10).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats, title='管理ダッシュボード')