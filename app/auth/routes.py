"""
Authentication routes for Flask application.
"""
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.auth.forms import (
    LoginForm, RegistrationForm, ChangePasswordForm, EditProfileForm,
    RequestPasswordResetForm, ResetPasswordForm
)
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('ユーザー名またはパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('アカウントが無効化されています。管理者にお問い合わせください。', 'error')
            return redirect(url_for('auth.login'))
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        
        flash(f'ようこそ、{user.full_name}さん！', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='ログイン', form=form)


@bp.route('/logout')
def logout():
    """User logout."""
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            organization=form.organization.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='新規登録', form=form)


@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    # Get user statistics
    total_transcripts = current_user.transcripts.count()
    total_jobs = current_user.correction_jobs.count()
    successful_jobs = current_user.correction_jobs.filter_by(status='completed').count()
    
    return render_template('auth/profile.html', title='プロフィール',
                         total_transcripts=total_transcripts,
                         total_jobs=total_jobs,
                         successful_jobs=successful_jobs)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    form = EditProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.organization = form.organization.data
        
        db.session.commit()
        flash('プロフィールが更新されました。', 'success')
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.organization.data = current_user.organization
    
    return render_template('auth/edit_profile.html', title='プロフィール編集', form=form)


@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('現在のパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('パスワードが変更されました。', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', title='パスワード変更', form=form)


@bp.route('/api_usage')
@login_required
def api_usage():
    """Display API usage statistics."""
    from datetime import datetime, timedelta
    from app.models import CorrectionJob
    
    # Calculate monthly usage
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    jobs = current_user.correction_jobs.order_by(CorrectionJob.created_at.desc()).limit(10)
    monthly_jobs = current_user.correction_jobs.filter(
        CorrectionJob.created_at >= current_month_start
    )
    monthly_cost = sum(job.cost for job in monthly_jobs if job.cost)
    
    return render_template('auth/api_usage.html', title='API使用状況',
                         monthly_cost=monthly_cost,
                         recent_jobs=jobs)


@bp.route('/reset_api_cost', methods=['POST'])
@login_required
def reset_api_cost():
    """Reset user's API cost."""
    current_user.reset_api_cost()
    flash('API使用コストがリセットされました。', 'success')
    return redirect(url_for('auth.api_usage'))


@bp.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # In a real application, you would send an email here
            flash('パスワードリセットの手順をメールで送信しました。', 'info')
        else:
            flash('そのメールアドレスは登録されていません。', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_password_reset.html', 
                         title='パスワードリセット要求', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # In a real application, you would verify the token here
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # For demo purposes, we'll just redirect to login
        flash('パスワードがリセットされました。新しいパスワードでログインしてください。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', 
                         title='パスワードリセット', form=form)