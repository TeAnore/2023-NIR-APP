import re
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

from app import db
from app.models import User, Task, Video, Transcript
from app.logger import Logger
from flask import current_app

class Service():
    def __init__(self):
        self.log = Logger()

    def check_availability(self, task, info):
        result = True
        try:
            status = info['status']
            if status != 'OK':
                reason = info['reason']
                self.log.msg_log(f"Check availability task_id: {task['id']} status: {status} - reason: {reason}")
            else:
                self.log.msg_log(f"Check availability task_id: {task['id']} status: {status}")

            if status == 'UNPLAYABLE':
                if reason == 'Join this channel to get access to members-only content like this video, and other exclusive perks.':
                    result = False
                elif reason == 'This live stream recording is not available.':
                    result = False
                else:
                    result = False
            elif status == 'LOGIN_REQUIRED':
                if reason == 'This is a private video. Please sign in to verify that you may see it.':
                    result = False
                elif reason == 'This video may be inappropriate for some users.':
                    result = False
                else:
                    result = False
            elif status == 'ERROR':
                if reason == 'Video unavailable':
                    result = False
                else:
                    result = False
            elif status == 'LIVE_STREAM':
                result = False
            else:
                result = True
        except Exception as e:
            self.log.error_log(f"Error check availability task_id: {task['id']}. Error: {e}")
            result = False
            pass
        
        return result

    def check_platform(self, platform, url):
        if platform.lower() == 'youtube':
            pattern_web = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(watch){1}\?v{1}\={1}(\w|\d|\S){11}$")
            pattern_mobile = re.compile("^(https){1}\:(\/){2}(youtu){1}\.(be){1}\/(\w|\d|\S){11}$")
            pattern_shorts = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(shorts){1}\/(\w|\d|\S){11}$")
            pattern_live = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(live){1}\/(\w|\d|\S){11}$")
        if pattern_web.match(url.lower()) \
        or pattern_mobile.match(url.lower())\
        or pattern_shorts.match(url.lower())\
        or pattern_live.match(url.lower()): 
            return True
        else:
            self.log.dev_log(f"Original URL: {url}")
            return False

    def get_platform_type(self, platform, url):
        if platform.lower() == 'youtube':
            pattern_web = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(watch){1}\?v{1}\={1}(\w|\d|\S){11}$")
            pattern_mobile = re.compile("^(https){1}\:(\/){2}(youtu){1}\.(be){1}\/(\w|\d|\S){11}$")
            pattern_shorts = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(shorts){1}\/(\w|\d|\S){11}$")
            pattern_live = re.compile("^(https){1}\:(\/){2}w{3}\.(" + platform.lower() + "){1}\.(com){1}\/(live){1}\/(\w|\d|\S){11}$")
            if pattern_web.match(url.lower()):
                return 'web'
            elif pattern_mobile.match(url.lower()):
                return 'mobile'
            elif pattern_shorts.match(url.lower()):
                return 'shorts'
            elif pattern_live.match(url.lower()):
                return 'live'
            else:
                return "unknown youtube"
        else:
            return f"unknown {platform.lower()}"

    def get_video_from_youtube(self, tasks):
        try:
            needDownload = True

            for task in tasks['items']:
                self.log.status_log(f"Process task: {task}")
                task_entity=Task.query.get(task['id'])

                if self.check_platform(task['platform'], task['url']):
                    self.log.msg_log(f"Check task: {task['id']} platform: True")
                    try:
                        video = YouTube(task['url'])
                    except Exception as e:
                        task_entity.from_dict({"status":1})
                        db.session.commit()
                        self.log.error_log(f"Error process task id: {task['id']}. Error: {e}")
                        pass
                    
                    if self.check_availability(task, video.vid_info['playabilityStatus']):
                        self.log.msg_log(f"Check task: {task['id']} playability status: True")
                        cnt_vi = Video.query.filter_by(video_key=task['video_key']).count()

                        if cnt_vi == 0:
                            self.log.msg_log(f"Video info task: {task['id']} count {cnt_vi}")

                            try:
                                self.log.msg_log(f"Get video info task: {task['id']} start")

                                ## DEVELOP FLAG
                                needDownload = False
                                self.log.dev_log(f"DEV Need Download: {task['id']} flag: {needDownload}")

                                try:
                                    self.create_video_info(task, video)
                                    task_entity.from_dict({"status":2})
                                    db.session.commit()

                                except Exception as e:
                                    self.log.error_log(f"Error Video Info: {e}")
                                    raise e
                                
                                try:
                                    self.create_transcript_info(task)
                                    task_entity.from_dict({"status":3})
                                    db.session.commit()

                                except Exception as e:
                                    self.log.error_log(f"Error Transcript Info: {e}")
                                    raise e

                                if needDownload:
                                    self.log.msg_log(f"Download video task: {task['id']} start")

                                    try:
                                        video.streams.filter(progressive="True").get_highest_resolution().download(output_path=current_app.config['PATH_DOWNLOAD'])
                                    except Exception as e:
                                        task_entity.from_dict({"status":4})
                                        db.session.commit() 
                                        self.log.error_log(f"Downlod video: {task['id']}. Error: {e}")
                                        raise e
                                else:
                                    self.log.msg_log(f"Download video task: {task['id']} not needed")


                                self.log.msg_log(f"Get video info task: {task['id']} comlite")

                            except Exception as e:
                                self.log.error_log(f"Get video info task: {task['id']}. Error: {e}")
                                pass
                        else:
                            task_entity.from_dict({"status":2})
                            db.session.commit() 
                            self.log.msg_log(f"Video info task: {task['id']} exist")
                            pass

                    else:
                        task_entity.from_dict({"status":1})
                        db.session.commit()
                        self.log.error_log(f"Check task: {task['id']} playability status: False")

                else:
                    task_entity.from_dict({"status":1})
                    db.session.commit()
                    self.log.error_log(f"Check task: {task['id']} platform: False")

        except Exception as e:
            self.log.error_log(f"get_video_from_youtube: {e}")

    def create_video_info(self, task, vi):
        self.log.status_log(f"Create Video Info task id: {task['id']} key: {task['video_key']}")
        try:
            video = Video()
            try:
                self.log.dev_log(f"Try parse vid_info")
                #for key in vi.vid_info: self.log.dev_log(f"vid_info key: {key}")
                '''
                vid_info key: responseContext
                vid_info key: playabilityStatus
                vid_info key: streamingData
                vid_info key: playbackTracking
                vid_info key: captions
                vid_info key: videoDetails
                vid_info key: playerConfig
                vid_info key: storyboards
                vid_info key: trackingParams
                vid_info key: attestation
                vid_info key: adBreakParams
                vid_info key: playerSettingsMenuData
                '''
                #for key in details: self.log.dev_log(f"details key: {key}")
                '''
                details key: videoId
                details key: title
                details key: lengthSeconds
                details key: channelId
                details key: isOwnerViewing
                details key: shortDescription
                details key: isCrawlable
                details key: thumbnail
                details key: allowRatings
                details key: viewCount
                details key: author
                details key: isPrivate
                details key: isUnpluggedCorpus
                details key: isLiveContent
                '''

                details = vi.vid_info.get('videoDetails', {})
                title = details.get('title', '')
                views = details.get('viewCount', 0)
                author = details.get('author', '')
                keywords = str(details.get('keywords', []))
                
                shortDescription = details.get('shortDescription', '')
                lengthSeconds = details.get('lengthSeconds', '')
                
                captions = vi.vid_info.get('captions', {})
                playerCaptionsTracklistRenderer = captions.get('playerCaptionsTracklistRenderer', {})
                captionTracks = playerCaptionsTracklistRenderer.get('captionTracks', {})

                if len(captionTracks) > 0:
                    language_code = captionTracks[0].get('languageCode', '')
                    is_translatable = captionTracks[0].get('isTranslatable', False)
                else:
                    language_code = ''
                    is_translatable = False

                streamingData = vi.vid_info.get('streamingData', {})
                progressive_formats = str(streamingData.get('formats', {}))
                adaptive_formats = str(streamingData.get('adaptiveFormats', {}))

            except Exception as e:
                self.log.dev_log(f"Error parse vid_info: {e}")
                raise e

            video.video_key = task['video_key']
            video.system = task['system']
            video.platform = task['platform']
            video.platform_type =  task['platform_type']
            video.title = title
            video.url =  task['url']
            video.views = views
            video.author = author
            video.keywords = keywords
            video.short_description = shortDescription
            video.length_seconds = lengthSeconds
            video.language_code = language_code
            video.progressive_formats = progressive_formats
            video.adaptive_formats = adaptive_formats
            video.is_translatable = is_translatable
            video.video_info = str(vi.vid_info)
            
            db.session.add(video)
            db.session.commit()
            self.log.status_log(f"Created Video Info: task_id {task['id']} video_key: {task['video_key']}")

        except Exception as e:
            self.log.error_log(f"Error create video info task id: {task['id']} key: {task['video_key']}. Error: {e}")
            raise e

    def create_transcript_info(self, task):
        try:
            self.log.status_log(f"Transcript info task id: {task['id']} key: {task['video_key']}")
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(task['video_key'])
                
                for transcript in transcript_list:
                    self.log.dev_log(f"Transcript list key: {transcript}")

                    language = transcript.language
                    language_code = str(transcript.language_code)
                    is_generated = transcript.is_generated
                    is_translatable = transcript.is_translatable
                    auto_subtitles = ''
                    manual_subtitles = ''

                    if is_translatable:

                        if not is_generated:
                            if transcript_list.find_manually_created_transcript([language_code]):
                                manual_subtitles = str(YouTubeTranscriptApi.get_transcript(task['video_key'], languages=[language_code]))
                        else:
                            if transcript_list.find_transcript([language_code]):
                                auto_subtitles = str(YouTubeTranscriptApi.get_transcript(task['video_key'], languages=[language_code]))

                    self.log.dev_log(f"transcript.language {language}")
                    self.log.dev_log(f"transcript.language_code {language_code}")
                    self.log.dev_log(f"transcript.is_generated {is_generated}")
                    self.log.dev_log(f"transcript.is_translatable {is_translatable}")
                    
                    t = Transcript()
                    t.video_key = task['video_key']
                    
                    t.language = language
                    t.language_code = language_code
                    t.is_generated = is_generated
                    t.is_translatable = is_translatable
                    t.translation_languages = ''
                    t.auto_subtitles = auto_subtitles
                    t.manual_subtitles = manual_subtitles

                    t.transcript_info = str(transcript_list)

                    db.session.add(t)
                    db.session.commit()

                message = f"Created Transcript Info: task_id {task['id']} video_key: {task['video_key']}"

            except Exception as e:
                err = str(e)
                if 'Subtitles are disabled for this video' in err or 'TranscriptsDisabled' in err:
                    message = f"Subtitles are disabled for this video {task['video_key']} task id: {task['id']}."
                    pass
                else:
                    self.log.error_log(f"Transcript list. task id: {task['id']} key: {task['video_key']}. Error: {e}")
                    raise e
            
            self.log.status_log(message)

        except Exception as e:
            self.log.error_log(f"Transcript info task id: {task['id']} key: {task['video_key']}. Error: {e}")
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