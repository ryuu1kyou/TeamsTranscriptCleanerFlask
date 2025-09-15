"""
Database models for Flask application.
"""
from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io

from app import db


class TemporaryUser:
    """Temporary user object for social login sessions (not stored in DB)."""
    
    def __init__(self, user_info, provider):
        self.id = f"temp_{provider}_{user_info['id']}"
        self.username = user_info['email'].split('@')[0]
        self.email = user_info['email']
        self.first_name = user_info.get('given_name', '')
        self.last_name = user_info.get('family_name', '')
        self.social_provider = provider
        self.social_id = user_info['id']
        self.is_active = True
        self.is_verified = True
        self.role_id = None
        self.role = None
        
        # Set default API limits for temporary users
        self.api_usage_limit = 5.0  # Lower limit for temporary users
        self.total_api_cost = 0.0
    
    @property
    def full_name(self):
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def role_name(self):
        """Get role name."""
        return 'Temporary User'
    
    def has_permission(self, permission):
        """Check if user has specific permission. Temporary users have limited permissions."""
        # Temporary users only have basic API access
        if permission == 'can_use_api':
            return True
        return False
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return False
    
    def can_manage_roles(self):
        """Check if user can manage roles."""
        return False
    
    def can_view_all_transcripts(self):
        """Check if user can view all transcripts."""
        return False
    
    def can_manage_wordlists(self):
        """Check if user can manage wordlists."""
        return False
    
    def is_admin(self):
        """Check if user is admin."""
        return False
    
    def is_authenticated(self):
        """Check if user is authenticated."""
        return True
    
    def is_anonymous(self):
        """Check if user is anonymous."""
        return False
    
    def get_id(self):
        """Get user ID for Flask-Login."""
        return self.id
    
    @property
    def remaining_api_budget(self):
        """Calculate remaining API budget."""
        return self.api_usage_limit - self.total_api_cost
    
    @property
    def api_budget_percentage_used(self):
        """Calculate percentage of API budget used."""
        if self.api_usage_limit == 0:
            return 100
        return (self.total_api_cost / self.api_usage_limit) * 100
    
    def can_use_api(self, estimated_cost=0.01):
        """Check if user can use API with estimated cost."""
        return (self.total_api_cost + estimated_cost) <= self.api_usage_limit
    
    def add_api_cost(self, cost):
        """Add API cost to user's total (stored in session)."""
        from flask import session
        self.total_api_cost += cost
        # Update session data
        temp_user_data = session.get('temp_user_data', {})
        temp_user_data['api_cost'] = self.total_api_cost
        session['temp_user_data'] = temp_user_data
    
    def reset_api_cost(self):
        """Reset user's API cost to zero."""
        from flask import session
        self.total_api_cost = 0.0
        # Update session data
        temp_user_data = session.get('temp_user_data', {})
        temp_user_data['api_cost'] = 0.0
        session['temp_user_data'] = temp_user_data


class Role(db.Model):
    """Role model for user permissions management."""
    
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Permissions
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_roles = db.Column(db.Boolean, default=False)
    can_view_all_transcripts = db.Column(db.Boolean, default=False)
    can_manage_wordlists = db.Column(db.Boolean, default=False)
    can_use_api = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    @classmethod
    def get_default_role(cls):
        """Get the default role for new users."""
        return cls.query.filter_by(name='User').first()
    
    @classmethod
    def get_admin_role(cls):
        """Get the admin role."""
        return cls.query.filter_by(name='Admin').first()
    
    def user_count(self):
        """Get number of users with this role."""
        return self.users.count()
    
    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Allow NULL for social login users
    
    # Profile information
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    organization = db.Column(db.String(100))
    
    # API usage management
    api_usage_limit = db.Column(db.Numeric(10, 2), default=Decimal('10.00'), nullable=False)
    total_api_cost = db.Column(db.Numeric(10, 4), default=Decimal('0.0000'), nullable=False)
    
    # Account status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Role assignment
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    
    # Social login fields
    social_provider = db.Column(db.String(50), nullable=True)
    social_id = db.Column(db.String(255), nullable=True)
    social_data = db.Column(db.JSON(), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    transcripts = db.relationship('TranscriptDocument', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    correction_jobs = db.relationship('CorrectionJob', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    wordlists = db.relationship('WordList', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def remaining_api_budget(self):
        """Calculate remaining API budget."""
        return self.api_usage_limit - self.total_api_cost
    
    @property
    def api_budget_percentage_used(self):
        """Calculate percentage of API budget used."""
        if self.api_usage_limit == 0:
            return 100
        return float((self.total_api_cost / self.api_usage_limit) * 100)
    
    def can_use_api(self, estimated_cost=Decimal('0.01')):
        """Check if user can use API with estimated cost."""
        return (self.total_api_cost + estimated_cost) <= self.api_usage_limit
    
    def add_api_cost(self, cost):
        """Add API cost to user's total."""
        self.total_api_cost += Decimal(str(cost))
        db.session.commit()
    
    def reset_api_cost(self):
        """Reset user's API cost to zero."""
        self.total_api_cost = Decimal('0.0000')
        db.session.commit()
    
    @property
    def full_name(self):
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def role_name(self):
        """Get role name."""
        return self.role.name if self.role else 'No Role'
    
    def has_permission(self, permission):
        """Check if user has specific permission."""
        if not self.role:
            return False
        return getattr(self.role, permission, False)
    
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.has_permission('can_manage_users')
    
    def can_manage_roles(self):
        """Check if user can manage roles."""
        return self.has_permission('can_manage_roles')
    
    def can_view_all_transcripts(self):
        """Check if user can view all transcripts."""
        return self.has_permission('can_view_all_transcripts')
    
    def can_manage_wordlists(self):
        """Check if user can manage wordlists."""
        return self.has_permission('can_manage_wordlists')
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role and self.role.name == 'Admin'
    
    def assign_default_role(self):
        """Assign default role to user."""
        if not self.role_id:
            default_role = Role.get_default_role()
            if default_role:
                self.role_id = default_role.id
    
    def __repr__(self):
        return f'<User {self.username}>'


class TranscriptDocument(db.Model):
    """Model for storing transcript documents."""
    
    __tablename__ = 'transcript_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # File metadata
    file_size = db.Column(db.Integer, nullable=False)
    character_count = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    
    # Processing status
    is_processed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    correction_jobs = db.relationship('CorrectionJob', backref='transcript', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.content:
            self.character_count = len(self.content)
            self.word_count = len(self.content.split())
    
    @property
    def estimated_tokens(self):
        """Estimate number of tokens (rough approximation)."""
        return max(int(self.character_count / 4), self.word_count)
    
    def get_file_extension(self):
        """Get file extension."""
        import os
        return os.path.splitext(self.original_filename)[1].lower()
    
    def __repr__(self):
        return f'<TranscriptDocument {self.title}>'


class TranscriptRevision(db.Model):
    """Stores finalized (or intermediate) corrected versions of a transcript for history."""
    __tablename__ = 'transcript_revisions'

    id = db.Column(db.Integer, primary_key=True)
    transcript_id = db.Column(db.Integer, db.ForeignKey('transcript_documents.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_final = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    transcript = db.relationship('TranscriptDocument', backref=db.backref('revisions', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):  # pragma: no cover
        return f'<TranscriptRevision t={self.transcript_id} id={self.id} final={self.is_final}>'


class WordList(db.Model):
    """Model for storing word correction lists with history tracking."""
    
    __tablename__ = 'wordlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    csv_content = db.Column(db.Text, nullable=False)
    
    # Version management for history
    version = db.Column(db.Integer, default=1, nullable=False)
    parent_wordlist_id = db.Column(db.Integer, db.ForeignKey('wordlists.id'), nullable=True)
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    # Metadata
    word_count = db.Column(db.Integer, default=0)
    is_shared = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    correction_jobs = db.relationship('CorrectionJob', backref='wordlist', lazy='dynamic')
    shared_access = db.relationship('SharedWordList', backref='wordlist', lazy='dynamic', cascade='all, delete-orphan')
    history_versions = db.relationship('WordList', backref=db.backref('parent_wordlist', remote_side=[id]), lazy='dynamic')
    
    # Unique constraint for active wordlists only
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_wordlist_name_uc'),)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.csv_content:
            self.word_count = self.get_word_count()
    
    def get_word_count(self):
        """Count the number of word pairs in the CSV content."""
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            # Skip header row
            next(csv_reader, None)
            count = sum(1 for row in csv_reader if len(row) >= 2)
            return count
        except Exception:
            return 0
    
    def get_word_pairs(self):
        """Parse CSV content and return list of word pairs."""
        word_pairs = []
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            # Skip header row
            next(csv_reader, None)
            for row in csv_reader:
                if len(row) >= 2:
                    word_pairs.append({
                        'incorrect': row[0].strip(),
                        'correct': row[1].strip()
                    })
        except Exception:
            pass
        return word_pairs
    
    def validate_csv_format(self):
        """Validate CSV format and return any errors."""
        errors = []
        try:
            csv_reader = csv.reader(io.StringIO(self.csv_content))
            header = next(csv_reader, None)
            
            if not header or len(header) < 2:
                errors.append("CSV must have at least 2 columns")
            
            row_count = 0
            for row_num, row in enumerate(csv_reader, start=2):
                if len(row) < 2:
                    errors.append(f"Row {row_num}: Must have at least 2 columns")
                elif not row[0].strip() or not row[1].strip():
                    errors.append(f"Row {row_num}: Both columns must have values")
                row_count += 1
            
            if row_count == 0:
                errors.append("CSV must contain at least one data row")
                
        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")
        
        return errors
    
    def create_version(self, new_csv_content, description=None):
        """Create a new version of this wordlist."""
        new_version = WordList(
            user_id=self.user_id,
            name=self.name,
            description=description or self.description,
            csv_content=new_csv_content,
            version=self.version + 1,
            parent_wordlist_id=self.id,
            is_shared=self.is_shared,
            is_active=True,
            is_template=self.is_template
        )
        
        # Deactivate current version
        self.is_active = False
        
        db.session.add(new_version)
        db.session.commit()
        return new_version
    
    def get_history(self):
        """Get version history of this wordlist."""
        if self.parent_wordlist_id:
            # If this is a version, get all versions of the parent
            parent = WordList.query.get(self.parent_wordlist_id)
            return parent.history_versions.order_by(WordList.version.desc()).all()
        else:
            # If this is the original, get all its versions
            return self.history_versions.order_by(WordList.version.desc()).all()
    
    def mark_as_used(self):
        """Mark wordlist as used and increment usage count."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_user_wordlists_with_history(cls, user_id):
        """Get all active wordlists for a user with their usage history."""
        from sqlalchemy import case
        return cls.query.filter_by(user_id=user_id, is_active=True).order_by(
            case((cls.last_used_at == None, 1), else_=0),
            cls.last_used_at.desc(),
            cls.created_at.desc()
        ).all()
    
    def __repr__(self):
        return f'<WordList {self.name}>'


class CorrectionJob(db.Model):
    """Model for correction processing jobs."""
    
    __tablename__ = 'correction_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transcript_id = db.Column(db.Integer, db.ForeignKey('transcript_documents.id'), nullable=False)
    wordlist_id = db.Column(db.Integer, db.ForeignKey('wordlists.id'), nullable=True)
    
    # Job configuration
    processing_mode = db.Column(db.String(20), default='proofreading', nullable=False)
    custom_prompt = db.Column(db.Text)
    model_used = db.Column(db.String(50), default='gpt-4o', nullable=False)
    
    # Job status and results
    status = db.Column(db.String(20), default='pending', nullable=False)
    corrected_content = db.Column(db.Text)
    
    # Processing metadata
    cost = db.Column(db.Numeric(10, 4), default=Decimal('0.0000'))
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    processing_time = db.Column(db.Interval)
    
    # Error handling
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constants for choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PROCESSING_MODE_CHOICES = [
        ('proofreading', 'Proofreading (Typo Correction)'),
        ('grammar', 'Grammar Correction'),
        ('summary', 'Summary Generation'),
        ('custom', 'Custom Processing'),
    ]
    
    MODEL_CHOICES = [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ]
    
    @property
    def is_completed(self):
        """Check if job is completed (successfully or with error)."""
        return self.status in ['completed', 'failed', 'cancelled']
    
    @property
    def is_successful(self):
        """Check if job completed successfully."""
        return self.status == 'completed'
    
    @property
    def total_tokens(self):
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens
    
    def mark_as_processing(self):
        """Mark job as processing."""
        self.status = 'processing'
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_completed(self, corrected_content, cost=0, input_tokens=0, output_tokens=0):
        """Mark job as completed successfully."""
        self.status = 'completed'
        self.corrected_content = corrected_content
        self.cost = Decimal(str(cost))
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        db.session.commit()
        
        # Add cost to user's total
        self.user.add_api_cost(cost)
    
    def mark_as_failed(self, error_message):
        """Mark job as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        db.session.commit()
    
    def __repr__(self):
        return f'<CorrectionJob {self.id}: {self.processing_mode} - {self.status}>'


class SharedWordList(db.Model):
    """Model for tracking shared word lists access."""
    
    __tablename__ = 'shared_wordlists'
    
    id = db.Column(db.Integer, primary_key=True)
    wordlist_id = db.Column(db.Integer, db.ForeignKey('wordlists.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    can_edit = db.Column(db.Boolean, default=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('wordlist_id', 'user_id', name='_wordlist_user_uc'),)
    
    # Relationships
    user = db.relationship('User', backref='shared_wordlist_access')
    
    def __repr__(self):
        return f'<SharedWordList {self.wordlist.name} shared with {self.user.username}>'
