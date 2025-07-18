from utils.tech.techClass import TechFile
from typing import Dict

class BaseAdapter:
    def __init__(self, tech_file: TechFile):
        self.tech_file = tech_file

    def get_data(self) -> Dict:
        raise NotImplementedError("Subclasses should implement this method.")
    
    def update_values(self) -> None:
        raise NotImplementedError("Subclasses should implement this method.")