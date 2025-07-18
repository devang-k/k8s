from utils.tech.techClass import TechFile
from typing import Dict, List
from utils.tech.adapters.BaseAdapter import BaseAdapter
from json import loads
from dataclasses import fields
from numpy import arange
from stdcell_generation_client.layout.layer_stack import *

class JsonAdapter(BaseAdapter):
    def __init__(self, tech_file: TechFile, json_data: str):
        super().__init__(tech_file)
        self.data = loads(json_data)

    def get_data(self) -> Dict:
        return self.data
    
    def update_values(self) -> None:
        display_values = {}
        data = self.get_data()
        field_names = {field.name for field in fields(self.tech_file)}
        for obj in data['FileContent']:
            if obj['name'] == 'permutation':
                current_dict = getattr(self.tech_file, obj['name'])
                new_dict = self.get_permutation(obj['data'])
                current_dict.update(new_dict)
            elif obj['name'] in field_names:
                ui_visible = obj['uiVisible']
                current_dict = getattr(self.tech_file, obj['name'])
                new_dict = {}
                for element in obj['data']:
                    if len(element['key'].keys()) == 1:
                        key = globals().get(element['key']['key1'], element['key']['key1'])
                    elif len(element['key'].keys()) == 2:
                        key = (globals().get(element['key']['key1'], element['key']['key1']), globals().get(element['key']['key2'], element['key']['key2']))
                    if element['type'] in [1, 4, 5]:  # numbers, dictionaries or boolean
                        val = element['val']
                    elif element['type'] == 3:  # strings
                        val = globals().get(element['val'], element['val'])
                    elif element['type'] == 2:  # lists/tuples
                        val = tuple(element['val'])
                    new_dict[key] = val
                current_dict.update(new_dict)
                if not ui_visible:
                    continue
                for element in obj['data']:
                    key = [obj['name']]
                    val = [obj['displayName']]
                    for i in range(len(element['key'])):
                        key.append(globals().get(element['key'][f'key{i+1}'], element['key'][f'key{i+1}']))
                        val.append(element['keyDisplayName'][f'displayNameKey{i+1}'])
                        if element['uiVisible']:
                            display_values['-'.join(key)] = '-'.join(val)
            else:
                for element in obj['data']:
                    if element['type'] in [1, 5] and element['key']['key1'] in field_names:  # numbers, boolean
                        val = element['val']
                    elif element['type'] == 3 and element['key']['key1'] in field_names:  # strings
                        val = globals().get(element['val'], element['val'])
                    elif element['type'] == 2 and element['key']['key1'] in field_names:  # lists/tuples
                        val = tuple(element['val'])
                    setattr(self.tech_file, element['key']['key1'], val)
                    if element['uiVisible'] and element['key']['key1'] in field_names:
                        display_values[element['key']['key1']] = element['keyDisplayName']['displayNameKey1']
        setattr(self.tech_file, 'display_names', display_values)
        self.tech_file.configure()

    def get_permutation(self, data: List[Dict]) -> Dict:
        permutations = {}
        for perm in data:
            if isinstance(perm['value'], dict):
                value = arange(perm['value']['start'], perm['value']['end'] + 0.00000000001, perm['value']['step']).tolist()
            else:
                value = perm['value']
            if isinstance(perm['attribute'], list):
                attribute = tuple([globals().get(attr, attr) for attr in perm['attribute']])
            else:
                attribute = globals().get(perm['attribute'], perm['attribute'])
            permutations[(perm['name'], attribute)] = value
        return permutations
