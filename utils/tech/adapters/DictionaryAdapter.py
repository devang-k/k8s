from utils.tech.techClass import TechFile
from typing import Dict, List
from utils.tech.adapters.BaseAdapter import BaseAdapter
from dataclasses import fields
from stdcell_generation_client.layout.layer_stack import *

class DictionaryAdapter(BaseAdapter):
    def __init__(self, tech_file: TechFile, data: Dict):
        super().__init__(tech_file)
        self.data = data
    
    def update_values(self) -> None:
        data = self.get_data()
        field_names = {field.name for field in fields(self.tech_file)}
        for key, value in data.items():
            if isinstance(value, dict) and key in field_names:
                current_dict = getattr(self.tech_file, key)
                if key in ['min_spacing', 'minimum_enclosure', 'via_weightage']:
                    new_dict = {(globals().get(k[0], k[0]), globals().get(k[1], k[1])): v for k, v in value.items()}
                else:
                    new_dict = {globals().get(k, k): v for k, v in value.items()}
                current_dict.update(new_dict)
            elif isinstance(value, list) and key == 'permutation':
                current_dict = getattr(self.tech_file, key)
                new_dict = self.get_permutation(value)
                current_dict.update(new_dict)
            elif isinstance(value, set) and key in field_names:
                value = {globals().get(elem, elem) for elem in value}
                setattr(self.tech_file, key, value)
            elif key in field_names:
                try:
                    setattr(self.tech_file, key, globals().get(value, value))
                except:
                    setattr(self.tech_file, key, value)
        self.tech_file.configure()

    def get_permutation(self, data: List[Dict]) -> Dict:
        permutations = {}
        for perm in data:
            if isinstance(perm['permutation'], dict):
                value = range(perm['permutation']['start'], perm['permutation']['end'], perm['permutation']['step'])
            else:
                value = tuple(perm['permutation'])
            permutations[(perm['name'], perm['attribute'])] = value
        return permutations

    def get_data(self) -> Dict:
        return self.data
