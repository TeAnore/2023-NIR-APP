import os
import cv2

from app.logger import Logger

class FileService:
    def __init__(self):
        self.log = Logger()
    
    def get_files_from_path(self, path):
        try:
            files = []
            with os.scandir(path) as it:
                for entry in it:
                    if not entry.name.startswith('.') and entry.is_file():
                        files.append(entry.name)
            return files
        except Exception as e:
            raise e
        
    def check_exist_file(self, filePath, fileName):
        result = False

        files = self.get_files_from_path(filePath)

        for fn in files:
            if fn == fileName:
                result = True
            self.log.dev_log(f"Check exist result {result} for File Name: {fileName} in Path: {filePath}")

        return result
    
    def extract_frames_from_video(self, filePath, fileName, framePath):
        try:
            input_file_name = os.path.join(filePath, fileName)
            video = cv2.VideoCapture(input_file_name)
            
            total_frame_cnt = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(video.get(cv2.CAP_PROP_FPS))
            
            duration = total_frame_cnt / fps

            minutes = duration / 60
            hours = duration / 3600

            if hours > 1:
                k = fps * 100
            elif hours <= 0 and  minutes > 3:
                k = fps * 10
            else:
                k = fps


            self.log.dev_log(f"total_frame_cnt: {total_frame_cnt}")
            self.log.dev_log(f"fps: {fps}")
            self.log.dev_log(f"duration: {duration}")

            self.log.dev_log(f"hours: {hours}")
            self.log.dev_log(f"minutes: {minutes}")
            self.log.dev_log(f"k: {k}")

            cnt = 0
            success = 1
            while success:
                video.set(cv2.CAP_PROP_POS_FRAMES, cnt * k)
                success, image = video.read()
                if success:
                    output_file_name = os.path.join(framePath, f"{fileName[:-4]}_frame_{cnt}.jpg")
                    self.log.dev_log(f"output_file_name: {output_file_name} status: {success}")
                    cv2.imwrite(output_file_name, image)
                    cnt += 1

            video.release()
            #cv2.destroyAllWindows()

        except Exception as e:
            if video.isOpened(): 
                video.release()
            self.log.error_log(f"extract_frames_from_video file: {filePath}\{fileName}. Error: {e}")

            raise e
    
    def clear_frames(self, framePath):
        try:
            files = self.get_files_from_path(framePath)

            for f in files:
                os.remove(os.path.join(framePath, f))

        except Exception as e:
            self.log.error_log(f"clear_frames. Error: {e}")
            raise e
