from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import  Column, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint
from sivista_db.models.base_model import Base

class CapacitanceMetrics(Base):
    __tablename__ = 'capacitance_metrics'
    capacitance_metrics_id = Column(Integer, primary_key=True,name='capacitance_metrics_id',autoincrement=True)
    permutation_id = Column(Integer, ForeignKey('permutations.permutation_id'),unique=True)
    avg_capacitance_per_node = Column(Float, name='avg_capacitance_per_node')
    max_capacitance = Column(Float, name='max_capacitance')
    min_capacitance = Column(Float, name='min_capacitance')    
    node_capacitances_IN_OUT = Column(Float, name='node_capacitances_IN OUT')
    node_capacitances_IN_VDD = Column(Float, name='node_capacitances_IN VDD')
    node_capacitances_IN_VSS = Column(Float, name='node_capacitances_IN VSS')
    node_capacitances_OUT_VDD = Column(Float, name='node_capacitances_OUT VDD')
    node_capacitances_OUT_VSS = Column(Float, name='node_capacitances_OUT VSS')
    node_capacitances_VDD_VSS = Column(Float, name='node_capacitances_VDD VSS')
    highest_capacitance_node_pairs_IN_OUT = Column(Float, name='highest_capacitance_node_pairs_IN OUT')
    highest_capacitance_node_pairs_IN_VDD = Column(Float, name='highest_capacitance_node_pairs_IN VDD')
    highest_capacitance_node_pairs_IN_VSS = Column(Float, name='highest_capacitance_node_pairs_IN VSS')
    highest_capacitance_node_pairs_VDD_VSS = Column(Float, name='highest_capacitance_node_pairs_VDD VSS')
    highest_capacitance_node_pairs_OUT_VDD = Column(Float, name='highest_capacitance_node_pairs_OUT VDD')
    highest_capacitance_node_pairs_OUT_VSS = Column(Float, name='highest_capacitance_node_pairs_OUT VSS')
    permutation = relationship("Permutation", back_populates="capacitance_metrics")
    __table_args__ = (UniqueConstraint('permutation_id', name='_permutation_capacitance_uc'),)
