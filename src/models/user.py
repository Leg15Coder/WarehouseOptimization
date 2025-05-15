from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from src.parsers.db_parser import db


class User(db.base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    phone_number = Column(String, unique=True)
    is_admin = Column(Boolean, default=False)
    password = Column(String, nullable=False)

    zones = relationship('Zone', secondary=user_x_zone, back_populates='users')
