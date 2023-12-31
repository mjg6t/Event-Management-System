import random
import string

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, func, Double
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'app_user'
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.now())
    modified_at = Column(TIMESTAMP(timezone=False), default=None)
    status = Column(Integer, default=1)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    # declaring one to one
    auth_token = relationship('Auth', back_populates='user', uselist=False)
    events = relationship('Event', back_populates='user')


class Auth(Base):
    __tablename__ = 'auth_token'
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.now())
    user_id = Column(Integer, ForeignKey('app_user.id'), unique=True)
    token = Column(String(255), nullable=False)
    # declaring one to one
    user = relationship('User', back_populates='auth_token')

    @classmethod
    def generate_token(cls):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.token:
            self.token = self.generate_token()


class Event(Base):
    __tablename__ = 'event_detail'
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.now())
    modified_at = Column(TIMESTAMP(timezone=False), default=None)
    status = Column(Integer, default=0)
    event_name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    start_date = Column(TIMESTAMP(timezone=False), nullable=False)
    end_date = Column(TIMESTAMP(timezone=False), nullable=False)
    guest = Column(String(255), nullable=True)
    audience_type = Column(String(255), nullable=True)
    place_id = Column(Integer, ForeignKey('place_detail.id'))
    place = relationship("Place", back_populates="event")
    user_id = Column(Integer, ForeignKey('app_user.id'))
    user = relationship("User", back_populates="events")


    def to_json(self):
        # Convert the Event attributes to a JSON-compatible dictionary
        event_json = {
            'id': self.id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'modified_at': self.modified_at.strftime('%Y-%m-%d %H:%M:%S') if self.modified_at else None,
            'status': self.status,
            'event_name': self.event_name,
            'description': self.description,
            'start_date': self.start_date.strftime('%Y-%m-%d %H:%M:%S') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d %H:%M:%S') if self.end_date else None,
            'guest': self.guest,
            'audience_type': self.audience_type,
            'place': self.place.to_json() if self.place else None,
            'user_id': self.user_id
        }
        return event_json


class Place(Base):
    __tablename__ = 'place_detail'
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.now())
    modified_at = Column(TIMESTAMP(timezone=False), default=None)
    status = Column(Integer, default=0)
    place_name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    audience_capacity = Column(Integer)
    air_conditioner = Column(Boolean, default=False)
    projector = Column(Boolean, default=False)
    sound_system = Column(Boolean, default=False)
    latitude = Column(Double, nullable=False)
    longitude = Column(Double, nullable=False)
    event = relationship("Event", back_populates="place")


    def to_json(self):
        # Convert the Place attributes to a JSON-compatible dictionary
        place_json = {
            'id': self.id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'modified_at': self.modified_at.strftime('%Y-%m-%d %H:%M:%S') if self.modified_at else None,
            'status': self.status,
            'place_name': self.place_name,
            'description': self.description,
            'audience_capacity': self.audience_capacity,
            'air_conditioner': self.air_conditioner,
            'projector': self.projector,
            'sound_system': self.sound_system,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }
        return place_json
