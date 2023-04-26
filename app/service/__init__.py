from flask import Blueprint

bp = Blueprint('service', __name__)

from app.service import logic, data_frame_service, transcript_service, video_service, yolo_service, file_service