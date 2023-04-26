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
            
            cnt = 0
            success = 1
            while success:
                success, image = video.read()
                if success:
                    output_file_name = os.path.join(framePath, f"{fileName[:-4]}_frame_{cnt}.jpg")
                    #self.log.dev_log(f"output_file_name: {output_file_name} status: {success}")
                    cv2.imwrite(output_file_name, image)
                    cnt += 1
        except Exception as e:
            self.log.dev_log(f"extract_frames_from_video file: {filePath}\{fileName}. Error: {e}")
            raise e
