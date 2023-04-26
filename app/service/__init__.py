from flask import Blueprint

bp = Blueprint('service', __name__)

from app.service import data_frame_service, logic, transcript_service, video_service, yolo_service