import os 
from ultralytics import YOLO

from app import db
from app.models import User, Task, Video, Transcript
from app.logger import Logger
from app.service import video_service, transcript_service
from flask import current_app

class YOLOService():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()

    def try_yolo(self):
        try:
            pass

        except Exception as e:
            self.log.dev_log(f"Error YOLO: {e}")
            raise e