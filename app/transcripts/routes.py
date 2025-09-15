"""
Routes for transcript management.
"""
import os
from flask import render_template, flash, redirect, url_for, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.transcripts import bp
from app.transcripts.forms import TranscriptUploadForm, TranscriptProcessForm, TranscriptEditForm
from app.models import TranscriptDocument, CorrectionJob, WordList, TranscriptRevision
from processing.openai_service import correct_text, estimate_cost
from processing.csv_parser import parse_csv_text


@bp.route('/')
@login_required
def index():
    """Main transcript processing page matching main.png design."""
    return render_template('transcripts/index.html', title='Teams Transcript Cleaner')


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload a new transcript."""
    form = TranscriptUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        title = form.title.data
        
        try:
            # Read file content
            content = file.read().decode('utf-8')
            
            # Create transcript document
            transcript = TranscriptDocument(
                user_id=current_user.id,
                title=title,
                original_filename=secure_filename(file.filename),
                content=content,
                file_size=len(content.encode('utf-8'))
            )
            
            db.session.add(transcript)
            db.session.commit()
            
            flash('トランスクリプトがアップロードされました。', 'success')
            return redirect(url_for('transcripts.detail', id=transcript.id))
            
        except UnicodeDecodeError:
            flash('ファイルの文字エンコーディングが正しくありません。UTF-8でエンコードされたファイルを使用してください。', 'error')
        except Exception as e:
            flash(f'アップロード中にエラーが発生しました: {str(e)}', 'error')
    
    return render_template('transcripts/upload.html', form=form, title='トランスクリプトアップロード')


@bp.route('/<int:id>')
@login_required
def detail(id):
    """Display transcript details."""
    transcript = TranscriptDocument.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    correction_jobs = transcript.correction_jobs.order_by(CorrectionJob.created_at.desc()).all()
    return render_template('transcripts/detail.html', transcript=transcript, 
                         correction_jobs=correction_jobs, title=transcript.title)


@bp.route('/api/finalize', methods=['POST'])
@login_required
def api_finalize_transcript():
    """Finalize current corrected content: create a TranscriptRevision and return success."""
    data = request.get_json() or {}
    transcript_id = data.get('transcript_id')
    content = data.get('content')
    if not transcript_id or content is None:
        return { 'success': False, 'error': 'transcript_id and content required' }, 400
    transcript = TranscriptDocument.query.filter_by(id=transcript_id, user_id=current_user.id).first()
    if not transcript:
        return { 'success': False, 'error': 'Transcript not found' }, 404
    try:
        revision = TranscriptRevision(
            transcript_id=transcript.id,
            user_id=current_user.id,
            content=content,
            is_final=True
        )
        db.session.add(revision)
        db.session.commit()
        return { 'success': True, 'revision_id': revision.id }
    except Exception as e:  # pragma: no cover
        db.session.rollback()
        return { 'success': False, 'error': str(e) }, 500


@bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload_transcript():
    """Create a transcript document (AJAX) and return its id. Expects JSON {title, filename?, content}."""
    data = request.get_json() or {}
    title = data.get('title') or 'Untitled'
    content = data.get('content')
    original_filename = data.get('filename') or f'{title}.txt'
    if not content:
        return {'success': False, 'error': 'content required'}, 400
    try:
        transcript = TranscriptDocument(
            user_id=current_user.id,
            title=title[:255],
            original_filename=original_filename[:255],
            content=content,
            file_size=len(content.encode('utf-8'))
        )
        db.session.add(transcript)
        db.session.commit()
        return {'success': True, 'transcript_id': transcript.id}
    except Exception as e:  # pragma: no cover
        db.session.rollback()
        return {'success': False, 'error': str(e)}, 500


@bp.route('/api/history')
@login_required
def api_transcript_history():
    """Return list of transcripts with their revision counts and latest finalize date."""
    transcripts = TranscriptDocument.query.filter_by(user_id=current_user.id).order_by(TranscriptDocument.created_at.desc()).all()
    result = []
    for t in transcripts:
        latest_rev = t.revisions.order_by(TranscriptRevision.created_at.desc()).first()
        result.append({
            'id': t.id,
            'title': t.title,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'revision_count': t.revisions.count(),
            'latest_finalized_at': latest_rev.created_at.isoformat() if latest_rev else None
        })
    return { 'success': True, 'transcripts': result }


@bp.route('/list')
@login_required
def list():
    """List all transcripts for the current user."""
    page = request.args.get('page', 1, type=int)
    transcripts = current_user.transcripts.order_by(TranscriptDocument.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('transcripts/list.html', transcripts=transcripts, title='トランスクリプト一覧')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a transcript."""
    transcript = TranscriptDocument.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = TranscriptEditForm()
    
    if form.validate_on_submit():
        transcript.title = form.title.data
        transcript.content = form.content.data
        transcript.character_count = len(form.content.data)
        transcript.word_count = len(form.content.data.split())
        
        db.session.commit()
        flash('トランスクリプトが更新されました。', 'success')
        return redirect(url_for('transcripts.detail', id=transcript.id))
    
    elif request.method == 'GET':
        form.title.data = transcript.title
        form.content.data = transcript.content
    
    return render_template('transcripts/edit.html', form=form, transcript=transcript, title='トランスクリプト編集')


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a transcript."""
    transcript = TranscriptDocument.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(transcript)
    db.session.commit()
    
    flash('トランスクリプトが削除されました。', 'success')
    return redirect(url_for('transcripts.list'))