import os 
import tensorflow as tf
from ultralytics import YOLO

from app import db
from app.models import User, Task, Video, Transcript, YoloResults
from app.logger import Logger
from app.service import task_service, video_service, transcript_service, file_service
from flask import current_app

class YOLOMOdel():
    def __init__(self, model_path, base_confidence) -> None:
        self.model_file = os.path.join(model_path, 'yolov8n.pt')
        self.model = YOLO(self.model_file)
        self.base_confidence = base_confidence

    def analysis(self, framePath, classes):
        
        results = self.model(framePath)

        r = results[0]
        if len(r.boxes) > 0:
            if len(r.boxes[0].data) > 0:
                data = r.boxes[0].data[0]
                names = r.names
                #names = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}
                confidence = tf.Variable(data[4], tf.float64).numpy()
                class_value = names[int(data[5])]

                if class_value not in classes and confidence > self.base_confidence:
                    classes[class_value] = {'confidence':confidence, 'cnt': 1}
                elif class_value in classes and confidence > self.base_confidence:
                    classes[class_value]['cnt'] += 1


class YOLOService():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()
        self.tk = task_service.TaskService()
        self.fs = file_service.FileService()

    def get_yolo_info(self, video_key):
        cnt_yre = YoloResults.query.filter_by(video_key=video_key).count()
        if cnt_yre == 1:
            yre = YoloResults.to_dict(YoloResults.query.filter_by(video_key=video_key).first())
            self.log.msg_log(f"YOLO Results Info. Found id: {yre['id']}")
        else:
            yre = {}
            self.log.msg_log(f"YOLO Results Info. Not Found")

        return yre

    def find_key(self, frame_name):
        name, ext = frame_name.split('.')
        number = name.split('_')[-1]
        return int(number)

    def sort_frames(self, frames):
        sorted_frames = x = sorted(frames, key=lambda k : self.find_key(k))
        return sorted_frames

    def try_yolo(self, video_key, modelPath, framesPath):
        try:
            model = YOLOMOdel(model_path=modelPath, base_confidence=0.2)
            frames = self.sort_frames(self.fs.get_files_from_path(framesPath))
            classes = {}
            frames_count = 0
            for frame in frames:
                frame_file = os.path.join(framesPath, frame)
                model.analysis(frame_file, classes)
                frames_count += 1

            if len(classes) == 0:
                classes['music'] = {'confidence': 0.99999999, 'cnt': frames_count}

            self.save_result(video_key, frames_count, classes)
            self.log.dev_log(f"try_yolo frames count {frames_count} classes{classes}")

        except Exception as e:
            self.log.dev_log(f"try_yolo error: {e}")
            raise e

    def save_result(self, video_key, frames_count, classes):
        yolo_results = YoloResults()

        yolo_results.video_key = video_key
        yolo_results.frames = frames_count
        yolo_results.classes = str(classes)

        db.session.add(yolo_results)
        db.session.commit()