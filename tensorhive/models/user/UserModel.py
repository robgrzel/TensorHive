from passlib.hash import pbkdf2_sha256 as sha256
import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from tensorhive.database import Base, db_session
import logging
log = logging.getLogger(__name__)

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(40), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    reservations = relationship('ReservationEventModel', backref='user')
    # TODO updated_at, role

    def __repr__(self):
        return '<User id={id}, username={username}>'.format(
            id=self.id, 
            username=self.username)


    def save_to_db(self):
        try:
            db_session.add(self)
            db_session.commit()
            log.debug('Created {}'.format(self))
            return True
        except SQLAlchemyError as e:
            db_session.rollback()
            log.error(e.__cause__)
            return False
            

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        return UserModel.query.all()

    @property
    def as_dict(self):
        '''Serializes model instance into dict (which is interpreted as json automatically)'''
        return {
            'id': self.id,
            'username': self.username,
            'createdAt': self.created_at.isoformat()
        }

