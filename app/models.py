from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Увеличьте длину до 256
    sounds_downloaded = db.Column(db.Integer, default=0)
    subscribed = db.Column(db.Boolean, default=False)
    daily_downloads = db.Column(db.Integer, default=0)
    last_download = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def check_download_limit(self):
        if (datetime.utcnow() - self.last_download).days > 0:
            self.daily_downloads = 0
        return self.daily_downloads < 3 if not self.subscribed else self.daily_downloads < 15

    def __repr__(self):
        return f'<User {self.username}>'

class Sound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64))
    tags = db.Column(db.String(256))  # Поле для тегов, разделенных запятыми
    bitrate = db.Column(db.String(64))
    quality = db.Column(db.String(64))
    duration = db.Column(db.Float)
    url = db.Column(db.String(256), nullable=False)
    exclusive = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Связь с пользователем

    def __repr__(self):
        return f'<Sound {self.title}>'

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sounds = db.relationship('Sound', secondary='collection_sounds', backref='collections')

collection_sounds = db.Table('collection_sounds',
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id')),
    db.Column('sound_id', db.Integer, db.ForeignKey('sound.id'))
)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sound_id = db.Column(db.Integer, db.ForeignKey('sound.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Notification {self.message}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
