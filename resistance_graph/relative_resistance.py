import sys
import os
from pnr_permutations.generate_permutations import PermutationEngine, LayerProperties, Polygon
from resistance_graph.equivalent_resistance import EquivalentResistance
from utils.reader.gds_reader import GDSReader
from stdcell_generation_client.technology_utils import load_tech_file
from os import makedirs, listdir
from tqdm.auto import tqdm
import logging
import networkx as nx
from collections import deque
from itertools import count
from os.path import exists, isfile
import argparse
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
from json import load
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
logger = logging.getLogger('sivista_app')
class CustomGraph:
    def __init__(self, graph: nx.Graph = None, node : any = None):
        self.graph = graph 
        self.node = node
        
        
    def visualizeGraph(self):
        pos = nx.circular_layout(self.graph) # Other layouts: planar_layout, random_layout, spectral_layout, spring_layout, shell_layout
        self.edge_labels = {}
        for u, v, edge_attr in self.graph.edges.data():
            logger.debug(f"Edge: ({u}, {v}), Data: {edge_attr}") 
            self.edge_labels[(u,v)] = f"{edge_attr['data'].layer} - {edge_attr['resistance']:.2f}"
        
        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=1500, edge_color='gray')
        nx.draw_networkx_edge_labels(
            self.graph, pos,
            edge_labels=self.edge_labels,
            font_color='red'
        )
        plt.show()

class BulkResistance:
    def __init__(self, polygon, length = 1, rho = 100000):
        self.area  = polygon.area
        self.length = length
        self.rho = rho
    
    def get_resistance(self):
        return (self.rho*self.length)/self.area


class customBFS:
    def __init__(self):
        pass 
    def getGraph(self, top_polygon:Polygon):
        graph = nx.Graph()
        counter = count(0)
        root = next(counter)
        graph.add_node(root)
        bfs = [(root, top_polygon)]
        visited = set()
        visited.add(top_polygon)
        while bfs:
            curNode, polygon = bfs.pop(0)
            logger.debug(f'custom BFS: Adding {polygon.layer}, {polygon.point.bounds}')
            newParent = next(counter)
            graph.add_node(newParent)
            graph.add_edge(curNode, newParent, data=polygon, resistance = BulkResistance(polygon.point).get_resistance())
            for child_polygon in polygon.adjacencyList:
                if child_polygon not in visited:
                    bfs.append((newParent, child_polygon))
                    visited.add(child_polygon)
            if polygon.connectedGate:
                if polygon.connectedGate not in visited:
                    bfs.append((newParent, polygon.connectedGate))
                    visited.add(polygon.connectedGate)
            if polygon.connectedInterconnect:
                if polygon.connectedInterconnect not in visited:
                    bfs.append((newParent, polygon.connectedInterconnect))
                    visited.add(polygon.connectedInterconnect)
            if polygon.planarConnectedPolygon:
                if polygon.planarConnectedPolygon not in visited:
                    bfs.append((newParent, polygon.planarConnectedPolygon))
                    visited.add(polygon.planarConnectedPolygon)
        return CustomGraph(graph, root)
            

        

class ConductanceGraphConstructor:
    def __init__(self, permutation_engine: PermutationEngine, top_layers : list[int]):
        self.permutation_engine = permutation_engine
        self.top_layers = top_layers
        self.conductance_dict : Dict[str, CustomGraph] = {}
        
        
    def get_top_polygons(self):
        top_polygons: Dict[str, Polygon] = {}
        for layer in self.top_layers:
            for polygon in self.permutation_engine.layerMap[layer].polygons:
                if polygon.textPolygons:
                    for textPoly in polygon.textPolygons:
                        top_polygons[textPoly.string] = polygon
        return top_polygons
    
    def construct_graph(self):
        for net, polygon in self.get_top_polygons().items():
            logger.debug(f"Constructing graph for {net}")
            self.conductance_dict[net] = customBFS().getGraph(polygon)
        return self.conductance_dict

class ResistanceExtractor:
    def __init__(self, permutation_engine: PermutationEngine, top_layers : list[int]):
        self.conductanceGraph: Dict[str, CustomGraph] = ConductanceGraphConstructor(permutation_engine, top_layers).construct_graph()
    
    def extract_resistance_dict(self):
        resistance_dict = {}
        for key, val in self.conductanceGraph.items():  
            resistance_dict[key] = EquivalentResistance(val.graph, start_node=0).getResistance()
        return resistance_dict
        
        
class RelativeResistance:
    """
    This class is used to extract the relative resistance of the netlist
    """
    def extract_files(self, gds_dir):
        files = []
        if isfile(gds_dir):
            files.append(gds_dir)
        else:    
            for gds_file in listdir(gds_dir):
                if gds_file.endswith(".gds"):
                    files.append( f'{gds_dir}/{gds_file}')
        return files
    
    def __init__(self, gds_dir, layer_map):
        self.files = self.extract_files(gds_dir)
        self.layer_map_dir = layer_map
              
    def extract_resistance(self):
        """
        This function is used to extract the relative resistance for a gds file

        Returns:
            resistance_dict: Dict[str, Dict[str, float]]
        """
        resistance_dict = {}
        for gds_file in self.files:
            permutation_engine = PermutationEngine(gds_file,self.layer_map_dir)
            resistance_dict[gds_file] = ResistanceExtractor(permutation_engine, [200,202,300]).extract_resistance_dict()
        return resistance_dict

                

def main(args):
    """
    Modified main function to work with sivista.py flow
    """
    gds_dir = os.path.abspath(args.get('gds_dir'))
    layer_map = os.path.abspath(args.get('layer_map'))
    
    print(RelativeResistance(gds_dir, layer_map).extract_resistance())  
            
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        description='Generate GDS layout from  netlist.')
    parser.add_argument('--gds_dir', required=True,
                        metavar='FILE', type=str, help='gds file')
    parser.add_argument('--layer_map', 
                        metavar='FILE', type=str, help='path to store the cell names')
    args, unknown = parser.parse_known_args()
    args = {
            "gds_dir" : args.gds_dir, 
            'layer_map': args.layer_map,
            } 
    main(args)  

   