from app import db
from app.models import Transcript
from app.logger import Logger

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptService():
    def __init__(self):
        self.log = Logger()

    def get_transcript_info(self,video_key):
        cnt_ti = Transcript.query.filter_by(video_key=video_key).count()
        if cnt_ti == 1:
            transcript = Transcript.to_dict(Transcript.query.filter_by(video_key=video_key).first())
            self.log.msg_log(f"Transcript Info: Found id: {transcript['id']}")
        else:
            transcript = {}
            self.log.msg_log(f"Transcript Info: Not Found")
        return transcript
    

    def create_transcript_info(self, task):
        try:
            self.log.status_log(f"Transcript info task id: {task['id']} key: {task['video_key']}")
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(task['video_key'])
                
                for transcript in transcript_list:
                    #self.log.dev_log(f"Transcript list key: {transcript}")

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
                    '''
                    self.log.dev_log(f"transcript.language {language}")
                    self.log.dev_log(f"transcript.language_code {language_code}")
                    self.log.dev_log(f"transcript.is_generated {is_generated}")
                    self.log.dev_log(f"transcript.is_translatable {is_translatable}")
                    '''

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
