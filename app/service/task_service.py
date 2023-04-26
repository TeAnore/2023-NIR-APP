from app import db
from app.models import Task
from app.logger import Logger

class Task():
    def __init__(self):
        self.log = Logger()