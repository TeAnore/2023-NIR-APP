import os
import pandas as pd

from app import db
from app.models import User, Task, Video, Transcript
from app.logger import Logger
from app.service import video_service, transcript_service
from flask import current_app

class DFService():
    def __init__(self):
        self.log = Logger()
        self.vs = video_service.VideoService()
        self.ts = transcript_service.TranscriptService()

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