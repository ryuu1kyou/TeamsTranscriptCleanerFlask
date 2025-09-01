"""
Corrections blueprint for handling transcript correction jobs.
"""
from flask import Blueprint

bp = Blueprint('corrections', __name__)

from app.corrections import routes