from peewee import *
from datetime import datetime, date
from app.database import db
from playhouse.shortcuts import model_to_dict

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    full_name = CharField()
    birthdate = DateField()
    region = CharField()
    district = CharField()
    avatar = CharField(default='default_avatar.jpg')  # O'zgartirilgan qator
    created_at = DateTimeField(default=datetime.now)
    
    def to_dict(self):
        return model_to_dict(self, exclude=[User.password])

class GameResult(BaseModel):
    user = ForeignKeyField(User, backref='results')
    score = IntegerField()
    level = IntegerField()
    stage = IntegerField()
    grid_size = IntegerField()
    duration = IntegerField()
    completed = BooleanField()
    date = DateTimeField(default=datetime.now)
    
    def to_dict(self):
        return model_to_dict(self)

class Session(BaseModel):
    session_id = CharField(unique=True)
    user = ForeignKeyField(User, backref='sessions')
    expiry = DateTimeField()
    
    def is_valid(self):
        return datetime.now() < self.expiry