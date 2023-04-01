import re

from pytube import YouTube

from app import db
from app.models import Task
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
            else:
                reason = ''
        
            self.log.msg_log(f"Check availability task_id: {task['id']} status: {status} - reason: {reason}")

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
        if pattern_web.match(url.lower()) or pattern_mobile.match(url.lower()) or pattern_shorts.match(url.lower()): 
            return True
        else:
            return False

    def get_video_from_youtube(self, tasks):

        for task in tasks['items']:
            self.log.status_log(f"Process task: {task}")
            self.log.msg_log(f"Check platform: {self.check_platform(task['platform'], task['url'])}")
            if self.check_platform(task['platform'], task['url']):
                video = YouTube(task['url'])
                title = video.title
                views = video.views
                self.log.msg_log(f"Video: {title} views: {views}")
                task_entity=Task.query.get(task['id'])
                if self.check_availability(task, video.vid_info['playabilityStatus']):
                    
                    try:
                        self.log.msg_log(f"vid_info: {video.vid_info}")
                        self.log.msg_log(f"Available resolution: {video.streams.filter(progressive='True').get_highest_resolution()}")
                    
                        try:
                            video.streams.filter(progressive="True").get_highest_resolution().download(output_path=current_app.config['PATH_DOWNLOAD'])
                        except Exception as err:
                            task_entity.from_dict({"status":3})
                            db.session.commit() 
                            self.log.error_log(f"Error downlod video: {err}")
                            raise err
                        
                        task_entity.from_dict({"status":2})
                        db.session.commit() 

                        self.log.status_log(f"Comlite task: {task}")

                    except Exception as err:
                        self.log.error_log(f"Error process task: {task}")
                        self.log.error_log(f"Video Info: {video.vid_info}")
                        pass
                
                else:
                    task_entity.from_dict({"status":1})
                    db.session.commit()