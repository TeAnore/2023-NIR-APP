import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Use to LocalHost Developing
    SERVER = 'localhost'

    DB_USER = os.environ.get('DB_USER')
    DB_PASS = os.environ.get('DB_PASS')
    DB_SERVER = SERVER
    DB_PORT = '5432'
    DB_NAME = 'postgres'
    print(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_SERVER}:{DB_PORT}/{DB_NAME}")
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
    POSTS_PER_PAGE = 25

    ELASTICSEARCH_SERVER = os.environ.get('ELASTICSEARCH_SERVER') or SERVER
    ELASTICSEARCH_PORT = 9200
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or f"http://{ELASTICSEARCH_SERVER}:{ELASTICSEARCH_PORT}"