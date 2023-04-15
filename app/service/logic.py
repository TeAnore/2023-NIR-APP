import os
import json
import re
import pandas as pd
from ultralytics import YOLO

from datetime import datetime
#from pytube import YouTube


from app import db
from app.models import User, Task, Video, Transcript
from app.logger import Logger
from app.service import video_service, transcript_service
from flask import current_app

class Service():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()

    def check_task_status(self, task):
        if task['status'] == 0:
            result = 'PROCESS'
        elif task['status'] == 1: 
            
            if task['error'].lower() == '':
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
        data["error"] = error

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
                        playability_status = video.vid_info.get('playabilityStatus', {})
                    except Exception as e:
                        error_msg = f"Video Info. YT-PT Error: {e}"
                        self.change_task_status(task, 1, error_msg)
                        error_info = f"{l} {error_msg}"
                        self.log.error_log(error_info)
                        return error_info

                    # Проверяем доступность информации о видео
                    # Проверяем возможность воспроизведения
                    result, status, reason = self.vs.check_availability(task, playability_status)
                    if result:
                        try:
                            video_info = self.vs.create_video_info(task, video)
                            
                            if str(type(video)) == "<class 'str'>":
                                raise Exception('Bad video type', video)

                        except Exception as e:
                            error_msg = f"Video Info. Create Error: {e}"
                            self.change_task_status(task, 1, error_msg)
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

                try:
                    files = []
                    with os.scandir(current_app.config['PATH_DOWNLOAD']) as it:
                        for entry in it:
                            if not entry.name.startswith('.') and entry.is_file():
                                files.append(entry.name)
                except Exception as e:
                    raise e

                # Скачиваем видео
                if not is_downloaded:
                    try:
                        if not video:
                            # Получаем объект с YouTube
                            try:
                                video = self.vs.get_youtube_object(task['url'])

                                if str(type(video)) == "<class 'str'>":
                                    raise Exception('Bad video type', video)

                            except Exception as e:
                                error_msg = f"Download YT-PT Error: {e}"
                                self.change_task_status(task, 1, error_msg)
                                error_info = f"{l} {error_msg}"
                                self.log.error_log(error_info)
                                return error_info

                        #video.streams.filter(progressive="True").get_highest_resolution().download(output_path=current_app.config['PATH_DOWNLOAD'])
                        stream_tag_id = video.streams.filter(progressive="True").get_highest_resolution().itag

                        stream = video.streams.get_by_itag(stream_tag_id)
                        
                        r = False
                        file_name = task['video_key'] + ".mp4"
                        self.log.dev_log(f"Task file_name: {file_name}")
                        for fn in files:
                            if fn == file_name:
                                r = True

                        self.log.dev_log(f"Check downloaded: {r}")
                        if not r:
                            stream.download(output_path=current_app.config['PATH_DOWNLOAD'], filename=task['video_key']+".mp4")

                        stream.mime_type
                        self.vs.mark_video_downloaded(task['video_key'], stream)

                        task['is_downloaded'] = True
                        task['error'] = None

                        self.update_task(task)
                        self.log.msg_log(f"{l} Download Complite")
                    except Exception as e:
                        self.log.error_log(f"Download Error: {e}")
                        raise e
                else:
                    self.log.dev_log(f"{l} Download not needed")
            
            self.change_task_status(task, 2)
            self.log.status_log(f"{l} Process Task: Complite")
        except Exception as e:
            self.log.error_log(f"{l} Process Task Error: {e}")
            raise e

    def generate_data_frame(self, type):
        try:
            df = pd.DataFrame()
            self.log.status_log(f"Generate Data Frame: Begin")
            if type == 'vi':
                '''
                Датафрейм с информацией о видео:
                user_id Идентификатор юзера
                liked Бинарный индикатор, понравилось ли видео (1, если понравилось, 0 в противном случае)
                video_key  Уникальный ключ Видео на YouTube
                platform  Платформа видео
                platform_type  Тип видео на платформе
                title  Заголовок
                views  количество просмотров
                author  автор видео
                keywords  ключевые слова
                short_description  короткое описание под видео
                language_code  исходный язык видео
                length_seconds  длинна видео в секундах
                '''
                columns_video_info = [
                    'id',
                    'user_id',
                    'liked',
                    'video_key',
                    'platform',
                    'platform_type',
                    'title',
                    'views',
                    'author',
                    'keywords',
                    'short_description',
                    'language_code',
                    'length_seconds'
                ]

                rows_video_info = []
                tasks = Task.to_collection_short_dict(Task.query.order_by('created').all())

                id = 0
                for row_idx in range(0, len(tasks['items']) -1 ):
                    id += 1

                    user_id = tasks['items'][row_idx]['user_id']

                    if tasks['items'][row_idx]['reaction'] == 100:
                        liked = 1
                    else:
                        liked = 0

                    video_key = tasks['items'][row_idx]['video_key']
                    platform = tasks['items'][row_idx]['platform']
                    platform_type = tasks['items'][row_idx]['platform_type']

                    video = Video()
                    video = Video.query.filter_by(video_key=video_key).first()

                    if not video:
                        pass
                    else:
                        title = video.title
                        views = video.views
                        author = video.author
                        keywords = video.keywords
                        short_description = video.short_description
                        language_code = video.language_code
                        length_seconds = video.length_seconds
                        
                        row = [ 
                            id,
                            user_id,
                            liked,
                            video_key,
                            platform,
                            platform_type,
                            title,
                            views,
                            author,
                            keywords,
                            short_description,
                            language_code,
                            length_seconds
                        ]

                        rows_video_info.append(row)
                
                df = pd.DataFrame(rows_video_info, columns=columns_video_info)

                self.log.status_log(f"Generate Data Frame {type}: End")
                
            elif type == 'ti':
                '''
                Датафрейм с субтитрами:
                video_key  Уникальный ключ Видео на YouTube
                language  Язык субтитров
                auto_subtitles  автоматически сгенерированные субтитры
                manual_subtitles  субтитры сгенерированныне автором в ручную
                '''
                columns_transcript_info = [
                    'id',
                    'video_key',
                    'language',
                    'auto_subtitles',
                    'manual_subtitles'
                ]

                rows_transcript_info = []
                transcripts = Transcript.to_collection_short_dict(Transcript.query.order_by('created').all())
                id = 0
                for row_idx in range(0, len(transcripts['items']) -1 ):
                    id += 1
                    video_key = transcripts['items'][row_idx]['video_key']
                    language = transcripts['items'][row_idx]['language']
                    auto_subtitles = transcripts['items'][row_idx]['auto_subtitles']
                    manual_subtitles = transcripts['items'][row_idx]['manual_subtitles']

                    row = [ 
                        id,
                        video_key,
                        language,
                        auto_subtitles,
                        manual_subtitles
                    ]

                    rows_transcript_info.append(row)

                df = pd.DataFrame(rows_transcript_info, columns=columns_transcript_info)
                self.log.status_log(f"Generate Data Frame {type}: End")
            else:
                df = pd.DataFrame()
                self.log.error_log(f"Generate Data Frame {type}: Not Supported")

            datetime_string = f'{datetime.now():%Y-%m-%d_%H-%M-%S%z}'
            filename = f"{current_app.config['PATH_DUMPS']}\\{datetime_string}_{type}.csv"
            df.to_csv(filename)

            return df.to_json(orient="records")
        
        except Exception as e:
            message = f"Generate Data Frame: {e}"
            self.log.error_log(message)
            return message
        
    def try_yolo(self):
        try:
            pass

        except Exception as e:
            self.log.dev_log(f"Error YOLO: {e}")
            raise e