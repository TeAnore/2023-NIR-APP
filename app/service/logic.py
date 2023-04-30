import os
import json
import re

from datetime import datetime

from app import db
from app.models import User, Task, Video, Transcript, Embedding
from app.logger import Logger
from app.service import video_service, transcript_service, file_service, yolo_service, embedding_service
from flask import current_app

class Service():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()
        self.fs = file_service.FileService()
        self.yolo = yolo_service.YOLOService()
        self.es = embedding_service.EmbeddingService()

    def check_task_status(self, task):
        if task['status'] == 0:
            result = 'PROCESS'
        elif task['status'] == 1: 
            
            mask_login_required = re.compile("^.*LOGIN_REQUIRED.*$")

            if str(task['error']).lower() != None and mask_login_required.match(str(task['error']).upper()):
                result = 'REPAIR'
            else:
                result = 'BAD'

        else:
            result = 'COMPLITED'

        return result

    def change_task_status(self, task, status, error=None):
        task = Task.query.get(task['id'])
        
        data = {}
        
        data["status"] = status
        if str(error) == 'None':
            data["error"] = error
        else:
            data["error"] = str(error)

        task.from_dict(data, new_task=False)
        db.session.commit()

    def update_task(self, task):
        data = task
        task = Task.query.get(task['id'])
        task.from_dict(data, new_task=False)
        db.session.commit()

    def get_video_from_youtube(self, task):
        try:
            l = f"USER_ID: {task['user_id']} TASK ID: {task['id']} VIDEO KEY: {task['video_key']}."
            self.log.status_log(f"{l} Process Task: Begin")
            # Проверяем состояние таски
            action = self.check_task_status(task)

            if action == 'COMPLITED':
                return action
            
            # Чиним если была поломана
            if action == 'REPAIR':
                self.change_task_status(task, 0)
                action = 'PROCESS'

            if action == 'PROCESS':

                # Проверяем доступные платформы
                if self.vs.check_platform('youtube', task['url']):
                    self.log.msg_log(f"{l} Check Platform: True")
                else:
                    error_msg = "Check Platform: False"
                    self.change_task_status(task, 1, error_msg)
                    error_info = f"{l} {error_msg}"
                    self.log.error_log(error_info)
                    return error_info

                # Получаем информацию о видео
                # Проверяем существование
                video = {}
                video_info = {}
                video_info = self.vs.get_video_info(task['video_key'])
                if not video_info:
                    # Получаем объект с YouTube
                    try:
                        video = self.vs.get_youtube_object(task['url'])

                        if str(type(video)) != 'YouTube':
                            raise Exception(video)

                    except Exception as e:
                        self.change_task_status(task, 1, str(e))
                        error_msg = f"Video Info. YT-PT Error: {e}"
                        error_info = f"{l} {error_msg}"
                        self.log.error_log(error_info)
                        return error_info

                    # Проверяем доступность информации о видео
                    # Проверяем возможность воспроизведения
                    result, status, reason = self.vs.check_availability(video.vid_info['playabilityStatus'])
                    if result:
                        try:
                            video_info = self.vs.create_video_info(task, video)
                            
                            if str(type(video)) == "<class 'str'>":
                                raise Exception(video)

                        except Exception as e:
                            self.change_task_status(task, 1, str(e))
                            error_msg = f"Video Info. Create Error: {e}"
                            error_info = f"{l} {error_msg}"
                            self.log.error_log(error_info)
                            return error_info
                    else:
                        error_msg = f"Video Info. Playability Status: False = status: {status} - reason: {reason}"
                        error_info = f"{l} {error_msg}"
                        self.change_task_status(task, 1, error_msg)
                        self.log.error_log(error_info)
                        return error_info
                else:
                    self.log.dev_log(f"{l} Video Info. Exist")

                if task['caption'] == 'Unknow':
                    try:
                        video = self.vs.get_youtube_object(task['url'])

                        if str(type(video)) == "<class 'str'>":
                            raise Exception(video)
                        
                        caption = self.vs.get_video_title(video)

                        task['caption'] = caption
                        self.update_task(task)
                        
                    except Exception as e:
                        self.change_task_status(task, 1, e)
                        error_msg = f"Video Info. Try UPD Caption YT-PT Error: {e}"
                        error_info = f"{l} {error_msg}"
                        self.log.error_log(error_info)
                        return error_info

                is_translatable = video_info['is_translatable']
                is_downloaded = video_info['is_downloaded']

                # Получаем информацию о субтитрах, если они есть
                if is_translatable:
                    transcript_info = {}
                    # Проверяем существование субтитров
                    transcript_info = self.ts.get_transcript_info(task['video_key'])

                    if not transcript_info:
                        try:
                            self.ts.create_transcript_info(task)
                        except Exception as e:
                            error_msg = f"Transcript Info. Create Error: {e}"
                            self.change_task_status(task, 1, error_msg)
                            error_info = f"{l} {error_msg}"
                            self.log.error_log(error_info)
                            return error_info
                    else:
                        self.log.dev_log(f"{l} Transcript Info. Exist")
                else:
                    self.log.warning_log(f"{l} Transcript Info. Reason: Subtitles or Transcripts are disabled for this video.")

                # Скачиваем видео
                r = self.fs.check_exist_file(current_app.config['PATH_DOWNLOAD'], task['video_key'] + ".mp4")

                if not is_downloaded and not r:
                    try:
                        if not video:
                            # Получаем объект с YouTube
                            try:
                                video = self.vs.get_youtube_object(task['url'])

                                if str(type(video)) == "<class 'str'>":
                                    raise Exception(video)

                            except Exception as e:
                                self.change_task_status(task, 1, e)
                                error_msg = f"Download YT-PT Error: {e}"
                                error_info = f"{l} {error_msg}"
                                self.log.error_log(error_info)
                                return error_info

                        #video.streams.filter(progressive="True").get_highest_resolution().download(output_path=current_app.config['PATH_DOWNLOAD'])
                        stream_tag_id = video.streams.filter(progressive="True").get_highest_resolution().itag

                        stream = video.streams.get_by_itag(stream_tag_id)
                        
                        stream.download(output_path=current_app.config['PATH_DOWNLOAD'], filename=task['video_key']+".mp4")

                        stream.mime_type
                        self.vs.mark_video_downloaded(task['video_key'], stream)

                        
                        task['is_downloaded'] = is_downloaded = True
                        task['error'] = None

                        self.update_task(task)
                        self.log.msg_log(f"{l} Download Complite")

                    except Exception as e:
                        self.log.error_log(f"Download Error: {e}")
                        raise e
                else:
                    self.log.dev_log(f"{l} Download not needed")
            
            # YOLO Logic Block
            r = self.fs.check_exist_file(current_app.config['PATH_DOWNLOAD'], task['video_key'] + ".mp4")
            if r:
                is_downloaded = True
            else:
                is_downloaded = False

            yolo_info = self.yolo.get_yolo_info(task['video_key'])

            if not yolo_info:
                needAnalysys = True
            else:
                needAnalysys = False

            if is_downloaded and needAnalysys:                

                self.fs.extract_frames_from_video(current_app.config['PATH_DOWNLOAD'], task['video_key'] + ".mp4", current_app.config['PATH_FRAMES'])
                self.yolo.try_yolo(task['video_key'], current_app.config['PATH_MODELS'], current_app.config['PATH_FRAMES'])
                self.fs.clear_frames(current_app.config['PATH_FRAMES'])

            else:
                self.log.dev_log(f"{l} YOLO Analysis. Exist")



            embedding_info = self.es.get_embedding_info(task['video_key'])

            if not embedding_info:
                needEmbedding = True
            else:
                needEmbedding = False

            if needEmbedding:
                self.es.create_embedding(task['video_key'])
            else:
                self.log.dev_log(f"{l} Embedding. Exist")


            self.change_task_status(task, 2)
            self.log.status_log(f"{l} Process Task: Complite")

        except Exception as e:
            self.log.error_log(f"{l} Process Task Error: {e}")
            raise e