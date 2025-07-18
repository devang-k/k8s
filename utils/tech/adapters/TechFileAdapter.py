from utils.tech.techClass import TechFile
from typing import Dict
from utils.tech.adapters.BaseAdapter import BaseAdapter
from stdcell_generation_client.layout.layer_stack import *
import importlib.machinery
import types

class TextFileAdapter(BaseAdapter):
    def __init__(self, tech_file: TechFile, file_path: str):
        super().__init__(tech_file)
        self.loader = importlib.machinery.SourceFileLoader('module_name', file_path)
        with open(file_path, 'r') as file:
            self.data = file.read()

    def get_data(self) -> Dict:
        return self.data
    
    def update_values(self) -> None:
        data = self.get_data()
        additional_imports = """
from stdcell_generation_client.layout.layer_stack import *
import numpy as np
"""
        modified_content = additional_imports + "\n" + data
        tech = types.ModuleType(self.loader.name)
        exec(modified_content, tech.__dict__)
        self.tech_file = tech
        if self.tech_file.technology in ['gaa', 'finfet']:
            self.tech_file.hinder = {}
