from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from src.server.base import Base

user_x_zone = Table(
    'user_x_zone', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id'), primary_key=True),
    Column('zone_id', Integer, ForeignKey('zone.zone_id'), primary_key=True)
)


class Zone(Base):
    __tablename__ = 'zone'

    zone_id = Column(Integer, primary_key=True)
    zone_name = Column(String, nullable=False)
    zone_type = Column(String)

    cells = relationship('Cell', back_populates='zone')
    users = relationship('User', secondary=user_x_zone, back_populates='zones')

