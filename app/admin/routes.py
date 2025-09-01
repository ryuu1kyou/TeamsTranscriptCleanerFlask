"""
Admin routes for Flask application.
"""
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.admin import bp
from app.models import User, TranscriptDocument, CorrectionJob, WordList, Role
from app import db
from datetime import datetime
from functools import wraps


def admin_required(f):
    """Decorator to require admin permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        if not current_user.can_manage_users():
            return jsonify({'success': False, 'error': 'Admin permissions required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def role_admin_required(f):
    """Decorator to require role management permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        if not current_user.can_manage_roles():
            return jsonify({'success': False, 'error': 'Role management permissions required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
def dashboard():
    """Admin dashboard."""
    # Check permissions using new role system
    if not current_user.can_manage_users():
        flash('管理者権限が必要です。', 'error')
        return redirect(url_for('main.index'))
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_transcripts': TranscriptDocument.query.count(),
        'total_jobs': CorrectionJob.query.count(),
        'total_wordlists': WordList.query.count(),
        'total_roles': Role.query.count(),
        'recent_users': User.query.order_by(User.created_at.desc()).limit(5).all(),
        'recent_jobs': CorrectionJob.query.order_by(CorrectionJob.created_at.desc()).limit(10).all()
    }
    
    return render_template('admin/dashboard.html', stats=stats, title='管理ダッシュボード')


# User Management API Endpoints

@bp.route('/api/users', methods=['GET'])
@admin_required
def list_users():
    """Get list of users."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in users.items:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role_name,
                'role_id': user.role_id,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None,
                'created_at': user.created_at.strftime('%Y-%m-%d'),
                'total_api_cost': float(user.total_api_cost),
                'api_usage_limit': float(user.api_usage_limit)
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role_id=data.get('role_id'),
            is_active=data.get('is_active', True),
            is_verified=data.get('is_verified', False)
        )
        user.set_password(data['password'])
        
        # Assign default role if none provided
        if not user.role_id:
            user.assign_default_role()
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role_name,
                'is_active': user.is_active
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get specific user details."""
    try:
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'role': user.role_name,
                'role_id': user.role_id,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None,
                'created_at': user.created_at.strftime('%Y-%m-%d'),
                'total_api_cost': float(user.total_api_cost),
                'api_usage_limit': float(user.api_usage_limit)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Prevent self-deactivation
        if user_id == current_user.id and 'is_active' in data and not data['is_active']:
            return jsonify({'success': False, 'error': 'Cannot deactivate your own account'}), 400
        
        # Update fields
        if 'username' in data:
            if data['username'] != user.username:
                if User.query.filter_by(username=data['username']).first():
                    return jsonify({'success': False, 'error': 'Username already exists'}), 400
                user.username = data['username']
        
        if 'email' in data:
            if data['email'] != user.email:
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({'success': False, 'error': 'Email already exists'}), 400
                user.email = data['email']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'role_id' in data:
            user.role_id = data['role_id']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_verified' in data:
            user.is_verified = data['is_verified']
        if 'api_usage_limit' in data:
            user.api_usage_limit = data['api_usage_limit']
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role_name,
                'is_active': user.is_active
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user."""
    try:
        # Prevent self-deletion
        if user_id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        user = User.query.get_or_404(user_id)
        
        # Store username for response
        username = user.username
        
        # Delete user (cascading deletes will handle related records)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} has been deleted'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# Role Management API Endpoints

@bp.route('/api/roles', methods=['GET'])
@role_admin_required
def list_roles():
    """Get list of roles."""
    try:
        roles = Role.query.order_by(Role.name).all()
        
        roles_data = []
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': role.user_count(),
                'permissions': {
                    'can_manage_users': role.can_manage_users,
                    'can_manage_roles': role.can_manage_roles,
                    'can_view_all_transcripts': role.can_view_all_transcripts,
                    'can_manage_wordlists': role.can_manage_wordlists,
                    'can_use_api': role.can_use_api
                },
                'created_at': role.created_at.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'roles': roles_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/roles', methods=['POST'])
@role_admin_required
def create_role():
    """Create a new role."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Role name is required'}), 400
        
        # Check if role name already exists
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'success': False, 'error': 'Role name already exists'}), 400
        
        # Create new role
        role = Role(
            name=data['name'],
            description=data.get('description', ''),
            can_manage_users=data.get('can_manage_users', False),
            can_manage_roles=data.get('can_manage_roles', False),
            can_view_all_transcripts=data.get('can_view_all_transcripts', False),
            can_manage_wordlists=data.get('can_manage_wordlists', False),
            can_use_api=data.get('can_use_api', True)
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': 0
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/roles/<int:role_id>', methods=['GET'])
@role_admin_required
def get_role(role_id):
    """Get specific role details."""
    try:
        role = Role.query.get_or_404(role_id)
        
        return jsonify({
            'success': True,
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': role.user_count(),
                'permissions': {
                    'can_manage_users': role.can_manage_users,
                    'can_manage_roles': role.can_manage_roles,
                    'can_view_all_transcripts': role.can_view_all_transcripts,
                    'can_manage_wordlists': role.can_manage_wordlists,
                    'can_use_api': role.can_use_api
                },
                'created_at': role.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/roles/<int:role_id>', methods=['PUT'])
@role_admin_required
def update_role(role_id):
    """Update role details."""
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            if data['name'] != role.name:
                if Role.query.filter_by(name=data['name']).first():
                    return jsonify({'success': False, 'error': 'Role name already exists'}), 400
                role.name = data['name']
        
        if 'description' in data:
            role.description = data['description']
        
        # Update permissions
        if 'can_manage_users' in data:
            role.can_manage_users = data['can_manage_users']
        if 'can_manage_roles' in data:
            role.can_manage_roles = data['can_manage_roles']
        if 'can_view_all_transcripts' in data:
            role.can_view_all_transcripts = data['can_view_all_transcripts']
        if 'can_manage_wordlists' in data:
            role.can_manage_wordlists = data['can_manage_wordlists']
        if 'can_use_api' in data:
            role.can_use_api = data['can_use_api']
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'role': {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': role.user_count()
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/roles/<int:role_id>', methods=['DELETE'])
@role_admin_required
def delete_role(role_id):
    """Delete a role."""
    try:
        role = Role.query.get_or_404(role_id)
        
        # Prevent deletion of roles that have users assigned
        if role.user_count() > 0:
            return jsonify({'success': False, 'error': 'Cannot delete role with assigned users'}), 400
        
        # Prevent deletion of essential roles
        if role.name in ['Admin', 'User']:
            return jsonify({'success': False, 'error': 'Cannot delete essential system roles'}), 400
        
        # Store role name for response
        role_name = role.name
        
        # Delete role
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Role {role_name} has been deleted'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500