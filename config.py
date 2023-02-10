import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

    # DB PostgreSQL
    DB_USER = "example"
    DB_PASS = "example"
    DB_NAME = "example"
    SQLALCHEMY_DATABASE_URI = "postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}"