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


class WordList(db.Model):
    """Model for storing word correction lists."""
    
    __tablename__ = 'wordlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    csv_content = db.Column(db.Text, nullable=False)
    
    # Metadata
    word_count = db.Column(db.Integer, default=0)
    is_shared = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    correction_jobs = db.relationship('CorrectionJob', backref='wordlist', lazy='dynamic')
    shared_access = db.relationship('SharedWordList', backref='wordlist', lazy='dynamic', cascade='all, delete-orphan')
    
    # Unique constraint
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
