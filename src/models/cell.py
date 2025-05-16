from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.server.base import Base


class Cell(Base):
    __tablename__ = 'cell'

    cell_id = Column(Integer, primary_key=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    product_sku = Column(Integer, ForeignKey('product.sku'))
    count = Column(Integer, nullable=False)
    zone_id = Column(Integer, ForeignKey('zone.zone_id'))

    product = relationship('Product', back_populates='cells')
    zone = relationship('Zone', back_populates='cells')
