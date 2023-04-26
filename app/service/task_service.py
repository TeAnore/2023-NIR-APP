from app import db
from app.models import Task
from app.logger import Logger

class TaskService():
    def __init__(self):
        self.log = Logger()