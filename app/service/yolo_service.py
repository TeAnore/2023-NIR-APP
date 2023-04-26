import os 
import tensorflow as tf
from ultralytics import YOLO

from app import db
from app.models import User, Task, Video, Transcript
from app.logger import Logger
from app.service import task_service, video_service, transcript_service, file_service
from flask import current_app

class YOLOService():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()
        self.tk = task_service.TaskService()
        self.fs = file_service.FileService()

    def try_yolo(self, modelPath, framePath):
        try:
            model_file = os.path.join(modelPath, 'yolov8n.pt')

            self.log.dev_log(f"modelFile {model_file}")

            model = YOLO(model_file)

            frames = self.fs.get_files_from_path(framePath)
            
            #objects = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}
            classes = {}
            base_confidence = 0.2

            for frame in frames:
                frame_file = os.path.join(framePath, frame)
                self.log.dev_log(f"frame_file {frame_file}")
                results = model(frame_file)
                #self.log.dev_log(f"try_yolo results{results}")

                r = results[0]
                if len(r.boxes) > 0:
                    if len(r.boxes[0].data) > 0:
                        data = r.boxes[0].data[0]
                        self.log.dev_log(f"try_yolo data {data}")
                        names = r.names
                        self.log.dev_log(f"try_yolo names {names}")
                        confidence = tf.Variable(data[4], tf.float64).numpy()
                        self.log.dev_log(f"try_yolo confidence {confidence}")
                        class_value = names[int(data[5])]
                        self.log.dev_log(f"try_yolo class_value {class_value}")

                        #print(f"boxes: {t} object {class_value}")
                        #print(f"confidence: {confidence} > 0.3 {(confidence > base_confidence)}")
                        if class_value not in classes and confidence > base_confidence:
                            classes[class_value] = {'confidence':confidence, 'cnt': 1}
                        elif class_value in classes and confidence > base_confidence:
                            classes[class_value]['cnt'] += 1

                '''
                for r in results:
                    boxes = r.boxes  # Boxes object for bbox outputs WARNING  'Boxes.boxes' is deprecated. Use 'Boxes.data' instead.
                    names = r.names

                    masks = r.masks  # Masks object for segment masks outputs
                    probs = r.probs  # Class probabilities for classification outputs
                    keypoints = r.keypoints

                    for t in boxes.data:

                        confidence = tf.Variable(t[4], tf.float64).numpy()
                        class_value = names[int(t[5])]

                        #print(f"boxes: {t} object {class_value}")
                        #print(f"confidence: {confidence} > 0.3 {(confidence > base_confidence)}")
                        if class_value not in classes and confidence > base_confidence:
                            classes[class_value] = {'confidence':confidence, 'cnt': 1}
                        elif class_value in classes and confidence > base_confidence:
                            classes[class_value]['cnt'] += 1
                        else:
                            continue
                '''
            self.log.dev_log(f"try_yolo classes{classes}")
                
        except Exception as e:
            self.log.dev_log(f"try_yolo error: {e}")
            raise e
