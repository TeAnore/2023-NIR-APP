import os
import yaml
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):

    def get_flask_config(file_name: str) -> dict:
        with open(file_name) as f:
            temporary = yaml.safe_load(f)
        
        return temporary['flask_config']
    
    def get_db_config(file_name: str) -> dict:
        with open(file_name) as f:
            temporary = yaml.safe_load(f)
    
        return temporary['db_config']

    FILE_CONFIG = os.path.join(basedir, 'config', 'config.yaml')

    flask_config = get_flask_config(FILE_CONFIG)
    db_config = get_db_config(FILE_CONFIG)


    SECRET_KEY = os.environ.get('SECRET_KEY') or flask_config['secret_key']

    # Use to LocalHost Developing
    SERVER = 'localhost'
    DB_USER = os.environ.get('DB_USER') or db_config['db_user']
    DB_PASS = os.environ.get('DB_PASS') or db_config['db_pass']
    DB_SERVER = SERVER
    DB_PORT = '5432'
    DB_NAME = 'postgres'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_SERVER}:{DB_PORT}/{DB_NAME}" 

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or SERVER
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en', 'ru']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    TASKS_PER_PAGE = 100
    
    FILE_CONFIG = os.path.join(basedir, 'config', 'config.yaml')
    PATH_DOWNLOAD = os.path.join(basedir, 'downloads', 'youtube')
    PATH_DUMPS = os.path.join(basedir, 'dumps')
    PATH_YOLO =  os.path.join(basedir, 'YOLO')
    PATH_MODELS = os.path.join(basedir, 'models')