"""
Transcripts blueprint for Flask application.
"""
from flask import Blueprint

bp = Blueprint('transcripts', __name__)

from app.transcripts import routes