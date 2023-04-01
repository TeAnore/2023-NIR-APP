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

    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
    external_user_id = db.Column(db.String(255), unique=True, nullable=True)
    username = db.Column(db.String(255), nullable=False)
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
        for field in ['external_user_id', 'username', 'first_name', 'last_name', 'email', 'description']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def created_tasks(self):
        ct = Task.query.filter_by(user_id=self.id)
        return ct.order_by(Task.created.desc())

class Task(PaginatedAPIMixin, BaseModel):
    __tablename__ = 'task'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_type = db.Column(db.String(100))
    caption = db.Column(db.String(100))
    url = db.Column(db.String(500))
    video_key = db.Column(db.String(11))
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
        for field in ['user_id', 'system', 'platform', 'platform_type', 'caption', 'url', 'video_key', 'reaction', 'status']:
            if field in data:
                setattr(self, field, data[field])
        if new_task or 'status' not in data:
            self.status = 0

class Video(PaginatedAPIMixin, BaseModel):
    __tablename__ = 'video'
    video_key = db.Column(db.String(100), unique=True, nullable=True)
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_type = db.Column(db.String(100))
    title = db.Column(db.String(500))
    url = db.Column(db.String(500))
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
            'video_info': self.video_info,
        }
        return data
    
    def from_dict(self, data, new_task=False):
        for field in ['video_key', 'system', 'platform', 'platform_type', 'title', 'url', 'video_info']:
            if field in data:
                setattr(self, field, data[field])

'''
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(PaginatedAPIMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    external_user_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    tasks = db.relationship('Task', backref='author', lazy='dynamic')

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

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
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'external_user_id': self.external_user_id,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me', 'external_user_id']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Task(PaginatedAPIMixin, SearchableMixin, db.Model):
    __searchable__ = ['caption']

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    caption = db.Column(db.String(100))
    url = db.Column(db.String(500))
    reaction = db.Column(db.Integer)
    status = db.Column(db.Integer)
    language = db.Column(db.String(5))
    video_key = db.Column(db.String(11))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Task - id:{}| userId:{} | system:{} | platform:{} | caption:{} | reaction:{} | video_key{}>'.format(self.id, self.user_id, self.system, self.platform, self.caption, self.reaction, self.video_key)
    
    def to_dict(self, flag=False):
        data = {
            'id': self.id,
            'created': self.created.isoformat() + 'Z',
            'system': self.system,
            'platform': self.platform,
            'caption': self.caption,
            'url': self.url,
            'reaction': self.reaction,
            'status': self.status,
            'user_id': self.user_id,
            'language': self.language,
            'video_key': self.video_key,
            '_links': {
                'self': url_for('api.get_task', id=self.id),
                'user': url_for('api.get_user', id=self.user_id)
            }
        }
        return data
    
    def from_dict(self, data, new_task=False):
        for field in ['system', 'platform', 'caption', 'url', 'reaction', 'status', 'user_id', 'language', 'video_key']:
            if field in data:
                setattr(self, field, data[field])
        if new_task and 'status' not in data:
            self.status = 0

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    platform_type = db.Column(db.String(100))
    caption = db.Column(db.String(100))
    url = db.Column(db.String(500))
    video_info = db.Column(db.Text)


class Task_Video_Relation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer)
    video_id = db.Column(db.Integer)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100))
    name = db.Column(db.String(100))
'''