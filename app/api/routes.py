"""
API routes for Flask application.
"""
import os
from datetime import datetime
from decimal import Decimal
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import User, TranscriptDocument, CorrectionJob, WordList
from processing.openai_service import correct_text
from processing.csv_parser import parse_csv_text


@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Flask API is running'})


@bp.route('/user')
@login_required
def user_info():
    """Get current user information."""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'organization': current_user.organization,
        'api_usage': {
            'total_cost': float(current_user.total_api_cost),
            'limit': float(current_user.api_usage_limit),
            'remaining': float(current_user.remaining_api_budget),
            'percentage_used': current_user.api_budget_percentage_used
        },
        'stats': {
            'transcripts': current_user.transcripts.count(),
            'jobs': current_user.correction_jobs.count(),
            'wordlists': current_user.wordlists.count()
        }
    })


@bp.route('/transcripts')
@login_required
def transcripts():
    """Get user's transcripts."""
    transcripts = current_user.transcripts.order_by(TranscriptDocument.created_at.desc()).all()
    return jsonify({
        'transcripts': [{
            'id': t.id,
            'title': t.title,
            'character_count': t.character_count,
            'word_count': t.word_count,
            'is_processed': t.is_processed,
            'created_at': t.created_at.isoformat()
        } for t in transcripts]
    })


@bp.route('/jobs')
@login_required
def jobs():
    """Get user's correction jobs."""
    jobs = current_user.correction_jobs.order_by(CorrectionJob.created_at.desc()).all()
    return jsonify({
        'jobs': [{
            'id': j.id,
            'transcript_title': j.transcript.title,
            'processing_mode': j.processing_mode,
            'status': j.status,
            'model_used': j.model_used,
            'cost': float(j.cost) if j.cost else 0,
            'created_at': j.created_at.isoformat(),
            'completed_at': j.completed_at.isoformat() if j.completed_at else None
        } for j in jobs]
    })


@bp.route('/process', methods=['POST'])
@login_required
def process_transcript():
    """Process transcript with AI correction."""
    try:
        data = request.get_json()
        
        # バリデーション
        required_fields = ['content', 'processing_mode', 'model_used']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        content = data['content']
        processing_mode = data['processing_mode']
        model_used = data['model_used']
        custom_prompt = data.get('custom_prompt', '')
        csv_text = data.get('csv_text', '')
        title = data.get('title', f'処理_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        # CSV解析（誤字脱字修正モードの場合）
        correction_words = []
        wordlist_id = None
        if processing_mode == 'proofreading' and csv_text:
            correction_words = parse_csv_text(csv_text)
            if not correction_words:
                return jsonify({'error': 'CSVデータが無効です'}), 400
        
        # トランスクリプト文書を作成
        transcript = TranscriptDocument(
            user_id=current_user.id,
            title=title,
            original_filename=f'{title}.txt',
            content=content,
            file_size=len(content.encode('utf-8')),
            character_count=len(content),
            word_count=len(content.split())
        )
        db.session.add(transcript)
        db.session.flush()  # IDを取得するため
        
        # 修正ジョブを作成
        job = CorrectionJob(
            user_id=current_user.id,
            transcript_id=transcript.id,
            wordlist_id=wordlist_id,
            processing_mode=processing_mode,
            model_used=model_used,
            custom_prompt=custom_prompt,
            status='processing'
        )
        db.session.add(job)
        db.session.commit()
        
        # OpenAI API呼び出し
        try:
            corrected_content, cost, prompt_tokens, completion_tokens = correct_text(
                processing_mode=processing_mode,
                user_custom_prompt=custom_prompt,
                input_text=content,
                correction_words=correction_words,
                model=model_used
            )
            
            # ジョブを更新
            job.status = 'completed'
            job.corrected_content = corrected_content
            job.cost = Decimal(str(cost))
            job.prompt_tokens = prompt_tokens
            job.completion_tokens = completion_tokens
            job.completed_at = datetime.utcnow()
            
            # ユーザーのAPI使用コストを更新
            current_user.total_api_cost += Decimal(str(cost))
            
            # トランスクリプトを処理済みに
            transcript.is_processed = True
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'job_id': job.id,
                'transcript_id': transcript.id,
                'corrected_content': corrected_content,
                'cost': float(cost),
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'message': '処理が完了しました'
            })
            
        except Exception as api_error:
            # API呼び出しエラー
            job.status = 'failed'
            job.error_message = str(api_error)
            db.session.commit()
            
            return jsonify({
                'error': f'AI処理エラー: {str(api_error)}',
                'job_id': job.id
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'処理エラー: {str(e)}'}), 500


@bp.route('/job/<int:job_id>/status')
@login_required
def job_status(job_id):
    """Get job status."""
    job = CorrectionJob.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'id': job.id,
        'status': job.status,
        'corrected_content': job.corrected_content,
        'cost': float(job.cost) if job.cost else 0,
        'error_message': job.error_message,
        'created_at': job.created_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None
    })