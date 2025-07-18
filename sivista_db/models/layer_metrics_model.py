from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import UniqueConstraint
from sivista_db.models.base_model import Base
class LayerMetrics(Base):
    __tablename__ = 'layer_metrics'
    layer_metrics_id = Column(Integer, primary_key=True,name='layer_metrics_id')
    permutation_id = Column(Integer, ForeignKey('permutations.permutation_id'))
    layer = Column(String,name = "Layer")
    total_area_um2 = Column(Float,name="Total Area (µm²)")
    density_percent = Column(Float,name= "Density (%)" )
    total_length_um = Column(Float,name= "Total Length (µm)")
    number_of_polygons = Column(Integer,name= "Number of Polygons")
    polygons = Column(Text,name='Polygons')  # Assuming it's a string representation
    f2f_total_length = Column(Float,name="F2F Total Length (µm)")
    adjacent_layer = Column(String,name="Adjacent Layer") 
    labels = Column(Text,name = "Labels")
    permutation = relationship("Permutation", back_populates="layer_metrics")
    __table_args__ = (UniqueConstraint('permutation_id', 'Layer', 'Adjacent Layer', name='_permutation_layer_uc'),)