"""
Routes for correction job management.
"""
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.corrections import bp
from app.models import CorrectionJob, TranscriptDocument
from processing.openai_service import correct_text, estimate_cost


@bp.route('/')
@login_required
def list():
    """Display correction jobs for current user."""
    jobs = CorrectionJob.query.filter_by(user_id=current_user.id)\
                             .order_by(CorrectionJob.created_at.desc())\
                             .all()
    return render_template('corrections/list.html', jobs=jobs)


@bp.route('/<int:job_id>')
@login_required
def detail(job_id):
    """Display detailed view of a correction job."""
    job = CorrectionJob.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    return render_template('corrections/detail.html', job=job)


@bp.route('/api/jobs')
@login_required
def api_list_jobs():
    """API endpoint to get correction jobs."""
    jobs = CorrectionJob.query.filter_by(user_id=current_user.id)\
                             .order_by(CorrectionJob.created_at.desc())\
                             .all()
    
    jobs_data = []
    for job in jobs:
        jobs_data.append({
            'id': job.id,
            'transcript_id': job.transcript_id,
            'transcript_title': job.transcript.title if job.transcript else 'N/A',
            'status': job.status,
            'processing_mode': job.processing_mode,
            'model_used': job.model_used,
            'cost': float(job.cost) if job.cost else 0.0,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        })
    
    return jsonify({'jobs': jobs_data})


@bp.route('/<int:job_id>/api/details')
@login_required
def api_job_details(job_id):
    """API endpoint to get detailed job information."""
    job = CorrectionJob.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    
    job_data = {
        'id': job.id,
        'transcript_id': job.transcript_id,
        'transcript_title': job.transcript.title if job.transcript else 'N/A',
        'status': job.status,
        'processing_mode': job.processing_mode,
        'model_used': job.model_used,
        'custom_prompt': job.custom_prompt,
        'original_content': job.original_content,
        'corrected_content': job.corrected_content,
        'cost': float(job.cost) if job.cost else 0.0,
        'prompt_tokens': job.prompt_tokens,
        'completion_tokens': job.completion_tokens,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message
    }
    
    return jsonify(job_data)


@bp.route('/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    """Delete a correction job."""
    job = CorrectionJob.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(job)
        db.session.commit()
        flash('修正ジョブが削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('修正ジョブの削除に失敗しました。', 'error')
    
    return redirect(url_for('corrections.list'))