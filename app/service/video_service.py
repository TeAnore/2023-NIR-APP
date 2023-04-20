import re

from app import db
from app.models import Video
from app.logger import Logger

from pytube import YouTube
from pytube import exceptions

class VideoService():
    def __init__(self):
        self.log = Logger()
        self.yt_pattern_web = re.compile("^(https){1}\:(\/){2}w{3}\.(youtube){1}\.(com){1}\/(watch){1}\?v{1}\={1}(\w|\d|\S){11}(.+|)$")
        self.yt_pattern_mobile = re.compile("^(https){1}\:(\/){2}(youtu){1}\.(be){1}\/(\w|\d|\S){11}$")
        self.yt_pattern_shorts = re.compile("^(https){1}\:(\/){2}w{3}\.(youtube){1}\.(com){1}\/(shorts){1}\/(\w|\d|\S){11}(.+|)$")
        self.yt_pattern_live = re.compile("^(https){1}\:(\/){2}w{3}\.(youtube){1}\.(com){1}\/(live){1}\/(\w|\d|\S){11}(.+|)$")
        self.yt_pattern_m = re.compile("^(https){1}\:(\/){2}(m){1}(\.){1}(youtube){1}(\.){1}(com){1}(\/){1}(watch){1}(\?){1}(v\=){1}(\w|\d|\S){11}(.+|)$")
        self.yt_pattern_share_shorts = re.compile("^(https){1}\:(\/){2}(youtube){1}\.(com){1}\/(shorts){1}\/(\w|\d|\S){11}(.+|)$")

    def get_video_info(self, video_key):
        cnt_vi = Video.query.filter_by(video_key=video_key).count()
        if cnt_vi == 1:
            video = Video.to_dict(Video.query.filter_by(video_key=video_key).first())
            self.log.msg_log(f"Video Info: Found id: {video['id']}")
        else:
            video = {}
            self.log.msg_log(f"Video Info: Not Found")

        return video
    
    def mark_video_downloaded(self, video_key, stream):
        video = Video.query.filter_by(video_key=video_key).first()
        mt = re.search(r'(?<=\/)\w+', stream.mime_type)
        exstention = mt.group(0)
#        self.log.dev_log(f"Format: {stream}")
#        self.log.dev_log(f"Exstention: {exstention}")
        
        data = {}
        data['current_format'] = str(stream)
        data['exstention'] = exstention
        data['is_downloaded'] = True

        video.from_dict(data, new_video=False)
        db.session.commit()

    def check_availability(self, task, info):
        result = True
        try:
            status = info['status']
            if status != 'OK':
                reason = info['reason']
                self.log.msg_log(f"Check availability task_id: {task['id']} status: {status} - reason: {reason}")
            else:
                reason = ''
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
        
        return result, status, reason

    def check_platform(self, platform, url):
        if platform.lower() == 'youtube' and\
        (  self.yt_pattern_web.match(url.lower()) \
        or self.yt_pattern_mobile.match(url.lower())\
        or self.yt_pattern_shorts.match(url.lower())\
        or self.yt_pattern_live.match(url.lower())\
        or self.yt_pattern_m.match(url.lower())\
        or self.yt_pattern_share_shorts.match(url.lower())\
        ):
            return True
        else:
            self.log.dev_log(f"Original URL: {url}")
            return False

    def get_platform_type(self, url):
        if self.yt_pattern_web.match(url.lower()) \
        or self.yt_pattern_mobile.match(url.lower())\
        or self.yt_pattern_shorts.match(url.lower())\
        or self.yt_pattern_live.match(url.lower())\
        or self.yt_pattern_m.match(url.lower())\
        or self.yt_pattern_share_shorts.match(url.lower())\
        :
            platform = 'youtube'
            if self.yt_pattern_web.match(url.lower()):
                patform_type = 'web'
            elif self.yt_pattern_mobile.match(url.lower()):
                patform_type = 'mobile'
            elif self.yt_pattern_m.match(url.lower()):
                patform_type = 'full_mobile'
            elif self.yt_pattern_shorts.match(url.lower()):
                patform_type = 'shorts'
            elif self.yt_pattern_share_shorts.match(url.lower()):
                patform_type = 'share_shorts'
            elif self.yt_pattern_live.match(url.lower()):
                patform_type = 'live'
            else:
                patform_type = f"unknown {platform.lower()}"
        else:
            patform_type = f"unknown {platform.lower()}"
        
        return platform, patform_type

    def get_youtube_object(self, url):
        result = ''
        try:
            for i in range(0,13):
                try: 
                    video = YouTube(url)
                    #self.log.dev_log(f"Type YouTube(url): {type(video)}")
                    title = video.title
                    stream_tag_id = video.streams.filter(progressive="True").get_highest_resolution().itag
                except exceptions.PytubeError as e:
                    self.log.dev_log(f"[{i}] get_youtube_object PytubeError: {e}")
                    result = e
                    continue
                except Exception as e:
                    self.log.dev_log(f"[{i}] get_youtube_object: {e}")
                    result = e
                    continue
                else:
                    return video

            return str(result)

        except Exception as e:
            raise e

    def create_video_info(self, task, vi):
        try:
            video = Video()
            try:
                #self.log.dev_log(f"Try parse vid_info")
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

            platform, platform_type = self.get_platform_type(task['url'])


            video.video_key = task['video_key']
            video.system = task['system']
            video.platform = platform
            video.platform_type =  platform_type
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
            return video.to_dict()
        except Exception as e:
            self.log.error_log(f"Error create video info task id: {task['id']} key: {task['video_key']}. Error: {e}")
            raise e
