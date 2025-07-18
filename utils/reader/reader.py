from abc import ABC, abstractmethod

class Reader(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def read():
        pass
    @abstractmethod
    def close():
        pass