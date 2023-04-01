from flask import Blueprint

bp = Blueprint('service', __name__)

from app.service import logic