from flask import Blueprint
bp = Blueprint('wordlists', __name__)
from app.wordlists import routes