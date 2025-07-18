# db/models.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base



Base = declarative_base()
class Permutation(Base):
    __tablename__ = 'permutations'
    permutation_id = Column(Integer, primary_key=True, autoincrement=True)
    permutation_num = Column(Integer)
    file_name = Column(String,nullable=False)
    gds_json = Column(Text,nullable=False)
    layer_metrics = relationship("LayerMetrics", back_populates="permutation")
    capacitance_metrics = relationship("CapacitanceMetrics", back_populates="permutation" ,uselist=False)





   


