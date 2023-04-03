import jwt
from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return "<{0.__class__.__name__}(id={0.id!r})>".format(self)

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page=page, per_page=per_page, error_out=False)

        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

    @staticmethod
    def to_collection_short_dict(query):

        data = {'items': [item.to_dict() for item in query]}

        return data
    
class User(PaginatedAPIMixin, UserMixin, BaseModel):
    __tablename__ = 'user'

    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    external_user_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    username = db.Column(db.String(255), nullable=False, index=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), index=True, unique=True)
    password_hash =  db.Column(db.String(128))
    description = db.Column(db.String(255), nullable=True)

    tasks = db.relationship('Task', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'external_user_id': self.external_user_id,
            'username': self.username,
            'description': self.description
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def from_dict(self, data, new_user=False):
        for field in [
                        'external_user_id',
                        'username',
                        'first_name',
                        'last_name',
                        'email',
                        'description'
        ]:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def created_tasks(self):
        ct = Task.query.filter_by(user_id=self.id)
        return ct.order_by(Task.created.desc())

class Task(PaginatedAPIMixin, BaseModel):
    __tablename__ = 'task'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_type = db.Column(db.String(100))
    caption = db.Column(db.String(100))
    url = db.Column(db.String(500))
    video_key = db.Column(db.String(11), nullable=False, index=True)
    reaction = db.Column(db.Integer)
    status = db.Column(db.Integer)

    def to_dict(self, flag=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'system': self.system,
            'platform': self.platform,
            'platform_type': self.platform_type,
            'caption': self.caption,
            'url': self.url,
            'video_key': self.video_key,
            'reaction': self.reaction,
            'status': self.status,
            '_links': {
                'self': url_for('api.get_task', id=self.id),
                'user': url_for('api.get_user', id=self.user_id)
            }
        }
        return data
    
    def from_dict(self, data, new_task=False):
        for field in [  
                        'user_id',
                        'system',
                        'platform',
                        'platform_type',
                        'caption',
                        'url',
                        'video_key',
                        'reaction',
                        'status'
        ]:
            if field in data:
                setattr(self, field, data[field])
        if new_task or 'status' not in data:
            self.status = 0

class Video(PaginatedAPIMixin, BaseModel):
    __tablename__ = 'video'
    video_key = db.Column(db.String(11), unique=True, nullable=False, index=True)
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_type = db.Column(db.String(100))
    title = db.Column(db.String(500))
    url = db.Column(db.String(500))
    views = db.Column(db.Integer)
    author = db.Column(db.String(500))
    keywords = db.Column(db.Text)
    short_description = db.Column(db.Text)
    language_code = db.Column(db.String(10))
    length_seconds = db.Column(db.Integer)
    progressive_formats = db.Column(db.Text)
    adaptive_formats = db.Column(db.Text)
    is_translatable = db.Column(db.Boolean)
    video_info = db.Column(db.Text)

    def to_dict(self, flag=False):
        data = {
            'id': self.id,
            'video_key': self.video_key,
            'system': self.system,
            'platform': self.platform,
            'platform_type': self.platform_type,
            'title': self.title,
            'url': self.url,
            'video_key': self.video_key,
            'views': self.views,
            'author': self.author,
            'keywords': self.keywords,
            'short_description': self.short_description,
            'length_seconds': self.length_seconds,
            'language_code': self.language_code,
            'progressive_formats': self.progressive_formats,
            'adaptive_formats': self.adaptive_formats,
            'is_translatable': self.is_translatable,
            'video_info': self.video_info
        }
        return data
    
    def from_dict(self, data, new_task=False):
        for field in [
                        'video_key',
                        'system',
                        'platform',
                        'platform_type',
                        'title',
                        'url',
                        'vievs',
                        'author',
                        'keywords',
                        'short_description',
                        'length_seconds',
                        'language_code',
                        'progressive_formats',
                        'adaptive_formats',
                        'is_translatable',
                        'video_info'
        ]:
            if field in data:
                setattr(self, field, data[field])


class Transcript(PaginatedAPIMixin, BaseModel):
    __tablename__ = 'transcript'
    video_key = db.Column(db.String(11), unique=True, nullable=False, index=True)
    language =  db.Column(db.String(100))
    language_code =  db.Column(db.String(100))
    is_generated = db.Column(db.Boolean)
    is_translatable = db.Column(db.Boolean)
    translation_languages = db.Column(db.Text)
    auto_subtitles = db.Column(db.Text)
    manual_subtitles = db.Column(db.Text)
    transcript_info = db.Column(db.Text)

    def to_dict(self, flag=False):
        data = {
            'id': self.id,
            'video_key': self.video_key,
            'language': self.language,
            'language_code': self.language_code,
            'is_generated': self.is_generated,
            'is_translatable': self.is_translatable,
            'translation_languages': self.translation_languages,
            'auto_subtitles': self.auto_subtitles,
            'manual_subtitles': self.manual_subtitles,
            'transcript_info': self.transcript_info
        }
        return data
    
    def from_dict(self, data, new_task=False):
        for field in [
                        'video_key',
                        'language',
                        'language_code',
                        'is_generated',
                        'is_translatable',
                        'translation_languages',
                        'auto_subtitles',
                        'manual_subtitles',
                        'transcript_info'
        ]:
            if field in data:
                setattr(self, field, data[field])