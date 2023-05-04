import os
import re
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sentence_transformers import SentenceTransformer
from sklearn.neighbors import KNeighborsClassifier

from app import db
from app.models import User, Task, Video, Transcript, YoloResults, Embedding
from app.logger import Logger
from app.service import task_service, video_service, transcript_service, file_service, yolo_service
from flask import current_app

class EmbeddingService():
    def __init__(self) -> None:
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.yolo = yolo_service.YOLOService()

    def clear_text(self, imput_string):
        tmp_string = re.sub(r'(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)', '', imput_string.lower())
        return re.sub(r"[^a-z+а-я+ +,\-.():?!]", '', tmp_string).replace('\n', '').replace(' .', '.')

    def get_description(self, original_description):

        result = ''

        if len(str(original_description)) > 512:
            result = str(original_description)[:512]
        else:
            result = str(original_description)

        return result

    def get_yolo_keys(self, video_key):
        self.log.dev_log(f"get_yolo_keys - video_key: {video_key}")
        yolo_info = self.yolo.get_yolo_info(video_key)

        yolo_keys = []
        if yolo_info:
            frames = yolo_info['frames']
            classes = str(yolo_info['classes'])
            # 10% of Full Frames
            k = 0.1
            # 50% Confidence
            frames_k = int(frames * k)
            confidence = 0.3
            json_acceptable_string = classes.replace("'", "\"")
            yolo_classes = json.loads(json_acceptable_string)
            
            #self.log.dev_log(f"frames {frames}")
            #self.log.dev_log(f"frames_k {frames_k}")
            #self.log.dev_log(f"classes {classes}")

            for _class in yolo_classes:

                #self.log.dev_log(f"confidence {yolo_classes[_class]['confidence']}")
                #self.log.dev_log(f"cnt {yolo_classes[_class]['cnt']}")
                if frames_k < yolo_classes[_class]['confidence']:
                    if float(yolo_classes[_class]['cnt']) > confidence:
                        yolo_keys.append(_class)
        
        #self.log.dev_log(f"yolo_keys {yolo_keys}")

        return yolo_keys

    def extract_data(self, video_key):
        
        video_info = self.vs.get_video_info(video_key)

        template = 'Title: {}. Author: {}. Description: {}. Keywords: {}. YoloKeys: {}.'

        sentence = template.format(video_info['title'],
                                   video_info['author'],
                                   self.get_description(video_info['short_description']),
                                   video_info['keywords'],
                                   self.get_yolo_keys(video_key))
        
        sentence = self.clear_text(sentence)

        return sentence

    def create_embedding(self, video_key):

        sentence = self.extract_data(video_key)

        model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

        embedding_data = model.encode(sentence)

        embedding = Embedding()

        embedding.video_key = video_key
        embedding.embedding_data = str(embedding_data)
        db.session.add(embedding)
        db.session.commit()

    def get_embedding_info(self, video_key):
        cnt_ee = Embedding.query.filter_by(video_key=video_key).count()
        if cnt_ee == 1:
            ee = Embedding.to_dict(Embedding.query.filter_by(video_key=video_key).first())
            self.log.msg_log(f"Embedding Info. Found id: {ee['id']}")
        else:
            ee = {}
            self.log.msg_log(f"Embedding Info. Not Found")

        return ee