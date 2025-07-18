import networkx as nx
from typing import Any, Dict, Tuple
import logging
from utils.tech.techClass import TechFile
from utils.tech.adapters.DictionaryAdapter import DictionaryAdapter
from utils.tech.adapters.JsonAdapter import JsonAdapter
from utils.tech.adapters.TechFileAdapter import TextFileAdapter



def load_tech_file(data={}):
    logger = logging.getLogger('sivista_app')
    logger.info('Loading tech file')

    tech_vals = TechFile()
    if isinstance(data, dict):
        adapter = DictionaryAdapter(tech_vals, data)
    elif isinstance(data, str) and data.endswith('.tech'):
        adapter = TextFileAdapter(tech_vals, data)
    elif isinstance(data, str):
        adapter = JsonAdapter(tech_vals, data)
    adapter.update_values()
    return adapter.tech_file