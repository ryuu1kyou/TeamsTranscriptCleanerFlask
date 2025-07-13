"""
Routes for correction job management.
"""
from flask import render_template, flash, redirect, url_for, request, make_response
from flask_login import login_required, current_user
from app import db
from app.corrections import bp
from app.models import CorrectionJob, TranscriptDocument


@bp.route('/')
@login_required
def list():
    """List all correction jobs for the current user."""
    page = request.args.get('page', 1, type=int)
    jobs = current_user.correction_jobs.order_by(CorrectionJob.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('corrections/list.html', jobs=jobs, title='修正ジョブ一覧')


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Display correction job details."""
    job = CorrectionJob.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('corrections/detail.html', job=job, title=f'修正ジョブ #{job.id}')


@bp.route('/<int:id>/download')
@login_required
def download(id):
    """Download corrected text as a file."""
    job = CorrectionJob.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if not job.is_successful or not job.corrected_content:
        flash('ダウンロード可能な結果がありません。', 'error')
        return redirect(url_for('corrections.detail', id=job.id))
    
    response = make_response(job.corrected_content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    filename = f"corrected_{job.transcript.title}_{job.id}.txt"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@bp.route('/<int:id>/retry', methods=['POST'])
@login_required
def retry(id):
    """Retry a failed correction job."""
    job = CorrectionJob.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if job.status not in ['failed', 'cancelled']:
        flash('このジョブは再試行できません。', 'error')
        return redirect(url_for('corrections.detail', id=job.id))
    
    # Create a new job with the same parameters
    new_job = CorrectionJob(
        user_id=current_user.id,
        transcript_id=job.transcript_id,
        wordlist_id=job.wordlist_id,
        processing_mode=job.processing_mode,
        custom_prompt=job.custom_prompt,
        model_used=job.model_used
    )
    
    db.session.add(new_job)
    db.session.commit()
    
    flash('ジョブが再作成されました。処理実行ページから実行してください。', 'info')
    return redirect(url_for('corrections.detail', id=new_job.id))