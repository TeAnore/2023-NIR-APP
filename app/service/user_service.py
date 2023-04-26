from app import db
from app.models import User
from app.logger import Logger

class UserService():
    def __init__(self):
        self.log = Logger()