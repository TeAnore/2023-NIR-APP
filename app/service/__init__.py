from flask import Blueprint

bp = Blueprint('service', __name__)

from app.service import logic, transcript_service, video_service, data_frame_logic, yolo_logic