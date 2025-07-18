# utils/writer/writer.py
from abc import ABC, abstractmethod
import json

class Writer(ABC):
    @abstractmethod
    def write(data: json, oname: str):
        pass
    @abstractmethod
    def close():
        pass