from flask import Blueprint
bp = Blueprint('corrections', __name__)
from app.corrections import routes