# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from resistance_graph.graph_nodes import NodeFactory, BaseNode, NanosheetNode, ViaNode
from pnr_permutations.generate_permutations import LayerProperties
from collections import deque
from shapely.geometry import Polygon
import math

import matplotlib.pyplot as plt
from itertools import combinations
from resistance_graph.resistance_gnn import ResistanceRGCN, ResistanceDataset
from resistance_graph.node_renamer_factory import NodeRenamerFactory
import traceback
from abc import ABC, abstractmethod
import json
from json import load
import logging
from pex_extraction.data_utils.preprocessing_regression import normalize_name
import re
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Optional
from dataclasses import dataclass
import networkx as nx

from pathlib import Path
from resistance_graph.polygon_processor import PolygonProcessor, PolygonInfo
from resistance_graph.graph_utils import convert_to_pyg_data
import os
import torch
from torch_geometric.data import Data as PyGData

logger = logging.getLogger(__name__)
layer_to_key_dict = {
    "M0": "M0",
    "M1": "M1",
    "BSPowerRail": "M0",
    "VIA_M0_M1": "M1_via",
    "VIA_M0_NMOSGate": "M0_via",
    "VIA_M0_PMOSInterconnect": "M0_via",
    "VIA_M0_PMOSGate": "M0_via",
    "VIA_M0_NMOSInterconnect": "M0_via",
    "VIA_Inteconnect_BSPowerRail": "M0_via",
    "PMOSGate": "Gate",
    "PMOSInterconnect": "Interconnect",
    "NMOSGate": "Gate",
    "NMOSInterconnect": "Interconnect",
    "VIA_PMOSInterconnect_NMOSInterconnect": "Via"
}


def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets


def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets


def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)


class TransistorPolygonManager:
    """
    This class is used to create a gate map and a drain neighbour map.
    It is used to create the gate map and the drain neighbour map for the transistor polygons.
    """

    def __init__(self, drain_neighbour_map: Dict[str, Dict[str, PolygonInfo]], gate_map: Dict[str, Dict[str, int]], num_of_gates: Dict[str, int], layer_numbers: Dict[str, int], polygon_processor: PolygonProcessor):
        self.polygon_processor = polygon_processor
        self.layer_properties = self.polygon_processor.layer_properties
        self.drain_neighbour_map = drain_neighbour_map
        self.gate_map = gate_map
        self.num_of_gates = num_of_gates
        self.layer_numbers = layer_numbers

    def create_gate_map(self, polygons, polygon_type):
        counter = 1
        if self.layer_properties.technology == "gaa":
            counter = 2
        gate_name = "PMos" if polygon_type == "PMOS" else "NMos"

        for i in range(len(polygons)):
            layer_name = polygons[i].layer_name
            if "Gate" in layer_name:
                key = polygons[i]

                self.gate_map[key] = {f"{gate_name}{i}": counter}
                counter += 1
        self.num_of_gates[polygon_type] = counter-1
        if self.layer_properties.technology == "gaa":
            self.num_of_gates[polygon_type] += 1

    def get_drain_neighbour_map(self):
        return self.drain_neighbour_map

    def get_gate_map(self):
        return self.gate_map

    def get_num_of_gates(self):
        return self.num_of_gates

    def create_drain_map(self, polygons, polygon_type):
        gate = "PMos" if polygon_type == "PMOS" else "NMos"
        for i in range(len(polygons) - 1):
            index_1 = i
            index_2 = i+1
            polygon_1 = polygons[index_1]
            polygon_2 = polygons[index_2]
            if polygon_1.layer == self.layer_numbers[f"{polygon_type}Interconnect"] and polygon_2.layer == self.layer_numbers[f"{polygon_type}Gate"]:
                self.drain_neighbour_map[polygon_1][f"{gate}{index_2}"] = polygon_2
            if polygon_1.layer == self.layer_numbers[f"{polygon_type}Gate"] and polygon_2.layer == self.layer_numbers[f"{polygon_type}Interconnect"]:
                self.drain_neighbour_map[polygon_2][f"{gate}{index_1}"] = polygon_1

    def create_neighbour_map(self):
        pmos = ["PMOSGate", "PMOSInterconnect"]
        nmos = ["NMOSGate", "NMOSInterconnect"]
        pmos_polygons = self.get_sorted_polygons_by_type(pmos)
        nmos_polygons = self.get_sorted_polygons_by_type(nmos)

        self.create_gate_map(pmos_polygons, "PMOS")
        self.create_gate_map(nmos_polygons, "NMOS")
        self.create_drain_map(pmos_polygons, "PMOS")
        self.create_drain_map(nmos_polygons, "NMOS")

        return self.drain_neighbour_map, self.gate_map

    def get_sorted_polygons_by_type(self, layers):
        polygons = []
        for layer_name in layers:
            polygons.extend(
                self.polygon_processor.layerMap[self.layer_numbers[layer_name]])

        polygons = [x for x in polygons if (x.datatype == 0 and (
            x.layerMap or x.connectedGate))]  # x.connectedGate is for CFET
        polygons = sorted(polygons, key=lambda x: x.point.bounds[0])
        return polygons


class BaseNetGraph():
    """
     Graph data container for a net
    """

    def __init__(self, graph: nx.Graph, net_name: str, root_node: str, layer_node_dict: Dict[str, List[str]], layer_to_key_dict: Dict[str, str], polygon_processor: PolygonProcessor, layer_z_indices: Dict[str, int], is_vertical: bool, cell_name: str, polygon_info_dict: Dict = None):

        self.graph = graph
        self.layer_node_dict = layer_node_dict
        self.layer_to_key_dict = layer_to_key_dict
        self.polygon_processor = polygon_processor
        self.net_name = net_name
        self.root_node = root_node
        self.layer_z_indices = layer_z_indices
        self.is_vertical = is_vertical
        self.cell_name = cell_name
        self.polygon_info = polygon_info_dict

    def get_graph(self):
        return self.graph


class BaseNetGraphBuilder():
    """_summary_
    Builds a graph from a list of polygons by traversing the graph using BFS - Builder class.
    """

    def __init__(self, top_polygons, num_nanosheet_nodes, net_name, neighbour_map, gate_map, nanosheet_polygons, num_of_gates, polygon_processor: PolygonProcessor, layer_z_indices, is_vertical, cell_name="", polygon_info_dict: Dict = None):
        self.graph = nx.Graph()
        self.top_polygons = top_polygons
        self.num_nanosheet_nodes = num_nanosheet_nodes
        self.net_name = net_name
        self.polygon_info = polygon_info_dict
        self.visited = set()
        self.neighbour_map = neighbour_map
        self.gate_map = gate_map
        self.nanosheet_polygons = nanosheet_polygons
        self.num_of_gates = num_of_gates
        self.root_node = None
        self.polygon_processor = polygon_processor
        self.layer_z_indices = layer_z_indices
        self.is_vertical = is_vertical
        self.layer_properties = self.polygon_processor.layer_properties
        self.technology = self.layer_properties.technology
        self.layer_node_dict = defaultdict(list)
        self.cell_name = cell_name
        self.net_graph = None
        self.build_graph_new(self.top_polygons)

    def build_graph_new(self, polygons):
        # for polygon in polygons:
        result = self.build_graph_bfs_new(polygon=polygons)
        if result is None:
            return None
        # The net_graph is already set by _finalize() in build_graph_bfs_new
        return self.net_graph

    def update_graph_with_new_polygons(self, polygons: Dict[str, PolygonInfo]):
        """_summary_
        Args:
            polygons (Dict[str, PolygonInfo]): _description_
        """
        for node_id in self.graph.nodes():
            node = self.graph.nodes[node_id]["data"]
            # call the pyg data object to update the node features
            if "NanoSheet" not in node.layer_name:
                new_polygon = polygons[node.polygon_id]
                node.polygon = new_polygon
                node.coordinates = new_polygon.point.bounds

            # call pyg features f=to fix the node fatures an
          # Then update ALL edge distances (including nanosheet node edges)
        for u, v, edge_data in self.graph.edges(data=True):
            node1 = self.graph.nodes[u]['data']
            node2 = self.graph.nodes[v]['data']
            old_distance = edge_data.get('euclidean_distance', 0.0)
            new_distance = self.calculate_euclidean_distance(node1, node2)
            if old_distance != new_distance:
                self.graph.edges[u, v]['euclidean_distance'] = new_distance

        self.net_graph.graph = self.graph

    def build_graph_bfs_new(self, polygon: PolygonInfo):
        # class polygon here should be polygon info
        """
        Builds a graph using BFS traversal, handling planar connections by queuing them immediately
        but using the same node for both the original polygon and its planar connected polygon.
        Uses the layer_node_dict to determine suffixes based on the count of existing nodes in each layer.
        Multimetal handling is done in the reset_node_id method instead.
        
        """

        polygon_info = self.polygon_info[polygon.id]
        if polygon in self.visited:
            return None
        self.visited.add(polygon)
        queue = deque()  # BFS queue
        collect_vias = []
        # Root node always empty suffix
        # HERE POLYGON SHOULD BE THE POLYGON  INFO NOW AND WE RETRIEVE THE REST OF THE INFO
        polygon_node = self.add_node(
            polygon,
            via_suffix="",
            metal_counter=0,
            device_suffix="",
            technology=self.technology,
            is_vertical=self.is_vertical,
            parent_node=None
        )
        # class polygon here should be polygon info
        self.root_node = polygon_node.node_id
        queue.append((polygon, polygon_node, "", 0))
        self.layer_node_dict[layer_to_key_dict[polygon.layer_name]].append(
            polygon_node.node_id)
        self.planarConnectedMap = {}
        while queue:
            current_polygon, parent_node, suffix, depth = queue.popleft()
            child_queue = []
            # Get unvisited immediate neighbors
            unvisited_neighbors = sorted([p for p in current_polygon.adjacencyList if p not in self.visited],
                                         key=lambda x: (x.point.bounds[0]))
            neighbors_count = len(unvisited_neighbors)
            for child_polygon in unvisited_neighbors:
                if child_polygon in self.visited or child_polygon.layer == self.polygon_processor.layer_numbers['VIA_PMOSInterconnect_NMOSInterconnect']:
                    continue
                self.visited.add(child_polygon)
                # Determine suffixes based on layer type
                layer = child_polygon.layer
                layer_name = child_polygon.layer_name
                
                # and parent_node is None:#,1050]:  and parent_node is None
                if neighbors_count == 1 and (current_polygon.layer in [self.polygon_processor.layer_numbers['M0'], self.polygon_processor.layer_numbers['M1']] and not (len(self.layer_node_dict.get('M0_via', [])) >= 1 or len(self.layer_node_dict.get('M1_via', [])) >= 1)):
                    suffix = ""
                else:
               
                    suffix = len(
                        self.layer_node_dict[layer_to_key_dict[layer_name]])
                if child_polygon.planarConnectedPolygon:
                    # to prevent
                    if child_polygon.planarConnectedPolygon in self.planarConnectedMap:
                        child_node = self.planarConnectedMap[child_polygon.planarConnectedPolygon]
                    else:
                        child_node = self.add_node(
                            child_polygon,
                            via_suffix=suffix,
                            metal_counter=suffix,
                            device_suffix=suffix,
                            technology=self.technology,
                            is_vertical=self.is_vertical,
                            parent_node=parent_node
                        )
                        # moved here to prevent the creation of the same node again for planar connected polygons and create incorrect device number suffixes
                        self.layer_node_dict[layer_to_key_dict[child_polygon.layer_name]].append(
                            child_node.node_id)
                        # store planar connected polygon and its node in a map to prevent the creation of the same node again for planar connected polygons
                        self.planarConnectedMap[child_polygon.planarConnectedPolygon] = child_node
                        self.planarConnectedMap[child_polygon] = child_node
                else:
                    child_node = self.add_node(
                        child_polygon,
                        via_suffix=suffix,
                        metal_counter=suffix,
                        device_suffix=suffix,
                        technology=self.technology,
                        is_vertical=self.is_vertical,
                        parent_node=parent_node
                    )
                    self.layer_node_dict[layer_to_key_dict[child_polygon.layer_name]].append(
                        child_node.node_id)
                if (current_polygon.layer == self.polygon_processor.layer_numbers['M0'] or current_polygon.layer == self.polygon_processor.layer_numbers['M1']) and child_polygon.isVia:
                    collect_vias.append(child_node)
                # might have to move this above and check before we add the node.
                # Add node to layer_node_dict
                self.add_edge(parent_node, [child_node])
                child_queue.append((child_polygon, child_node, suffix, depth + 1))
                # Queue planar connected polygon for traversal but use the same node - order of the queue is important here.
                if child_polygon.planarConnectedPolygon:
                    child_queue.append(
                        (child_polygon.planarConnectedPolygon, child_node, suffix, depth + 1))

                # self.create_edges_between_vias(collect_vias)
            # Process device nodes if applicable
            if current_polygon.layer in [self.polygon_processor.layer_numbers['NMOSGate'], self.polygon_processor.layer_numbers['PMOSGate'], self.polygon_processor.layer_numbers['NMOSInterconnect'], self.polygon_processor.layer_numbers['PMOSInterconnect']]:  # Device layers
                device_polygons = []
                if current_polygon.connectedGate:
                    device_polygons.append(current_polygon.connectedGate)
                if current_polygon.connectedInterconnect:
                    device_polygons.append(
                        current_polygon.connectedInterconnect)
                if current_polygon.planarConnectedPolygon:
                    device_polygons.append(
                        current_polygon.planarConnectedPolygon)
                device_polygons.append(current_polygon)
                self.add_nanosheet_nodes(device_polygons, parent_node)
            child_queue = sorted(child_queue, key =lambda x : x[0].layer_name  )
            queue.extend(child_queue)
        if self.root_node and (is_ground_net(self.net_name)) and self.technology == "cfet":
            if is_ground_net(self.net_name):
                # Get all nodes and their connections first
                self.remove_cfet_ground_net_nodes(polygon_node)
        self.graph = self._finalize()
        return polygon_node

    def remove_cfet_ground_net_nodes(self, polygon_node):
        if is_ground_net(self.net_name):
            # Get all nodes and their connections first
            nodes_to_process = list(self.graph.neighbors(polygon_node.node_id))
            # Add all edges first
            for child_node in nodes_to_process:
                child_neighbors = list(self.graph.neighbors(child_node))
                for child_neighbor in child_neighbors:
                    if child_neighbor != polygon_node.node_id:
                        child_node_data = self.graph.nodes[child_neighbor]['data']
                        # Add edges inside loop
                        self.add_edge(polygon_node, [child_node_data])

            # Remove nodes after all edges are added
            for child_node in nodes_to_process:

                self.graph.remove_node(child_node)  # Remove nodes outside loop

    def add_edge(self, polygon_node, node_list: List[BaseNode], debug_connections=False):
        for node in node_list:
            if polygon_node.node_id != node.node_id:
                edge_type = f"{polygon_node.node_id}_to_{node.node_id}"

                euclidean_distance = self.calculate_euclidean_distance(
                    polygon_node, node)

                self.graph.add_edge(polygon_node.node_id, node.node_id, connection_type=edge_type, source_layer=polygon_node.layer_name,
                                    target_layer=node.layer_name, resistance=0.0, euclidean_distance=euclidean_distance)

                # Debug connection types if enabled
                if debug_connections:
                    with open('connection_types.txt', 'a') as f:
                        f.write(f"Connection Type: {edge_type}\n")
                        f.write(f"Source Layer: {polygon_node.layer_name}\n")
                        f.write(f"Target Layer: {node.layer_name}\n")
                        f.write("-" * 50 + "\n")

    def add_node(self, polygon, via_suffix, metal_counter=0, device_suffix="", technology="cfet", is_vertical=False, parent_node=None):
        try:
            node = NodeFactory.create_node(polygon, self.net_name, via_suffix, layer_z_indices=self.layer_z_indices,
                                           metal_counter=metal_counter, device_suffix=device_suffix,
                                           technology=technology, is_vertical=is_vertical, parent_node=parent_node, cell_name=self.cell_name)
            if node is None:
                logger.error(
                    f"NodeFactory.create_node returned None for {polygon.layer_name}")
                return None

            if self.graph.has_node(node.node_id):

                return self.graph.nodes[node.node_id]['data']

            if not hasattr(node, 'node_id') or not hasattr(node, 'layer_name'):
                logger.error(
                    f"Invalid node created for polygon {polygon.layer_name} - missing required attributes")
                return None

            self.graph.add_node(node.node_id, data=node)
            return node
        except Exception as e:
            import traceback
            logger.error(f"Error in add_node:")
            logger.error(f"Polygon: {polygon.layer_name}")
            logger.error(f"Net: {self.net_name}")
            logger.error(f"Technology: {technology}")
            logger.error(f"Exception: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def calculate_euclidean_distance(self, node1, node2):
        bounds1 = node1.coordinates
        bounds2 = node2.coordinates
        # Calculate center points
        center1 = ((bounds1[0] + bounds1[2])/2, (bounds1[1] + bounds1[3])/2)
        center2 = ((bounds2[0] + bounds2[2])/2, (bounds2[1] + bounds2[3])/2)
        distance = ((center1[0] - center2[0])**2 +
                    (center1[1] - center2[1])**2)**0.5
        return distance

    def add_nanosheet_nodes(self, polygons, polygon_node):
        nanosheet_node_list = []
        for device_polygon in polygons:
            nanosheet_nodes = self.add_nanosheet_node(
                device_polygon, polygon_node)
            for node in nanosheet_nodes:
                self.graph.add_node(node.node_id, data=node)
            nanosheet_node_list.extend(nanosheet_nodes)
            self.add_edge(polygon_node, nanosheet_nodes)
            nanosheet_node_list = list(set(nanosheet_node_list))

        for node_1, node_2 in combinations(nanosheet_node_list, 2):
            self.add_edge(node_1, [node_2])

    def get_intersection_coordinates(self, nanosheet_polygon, device_polygon_for_nanosheet, intersection_polygon):
        device_union = device_polygon_for_nanosheet.point.union(
            intersection_polygon.point)
        intersection_coordinates = device_union.intersection(
            nanosheet_polygon.point)
        # Check for empty intersection
        if intersection_coordinates.is_empty:
            return None
          # Get bounds and check for NaN
        bounds = intersection_coordinates.bounds
        if any(math.isnan(x) for x in bounds):
            return None

        return bounds

    def add_nanosheet_node(self, device_polygon_for_nanosheet, polygon_node):

        nanosheet = "PmosNanoSheet" if device_polygon_for_nanosheet.layer_name.startswith(
            "PMOS") else "NmosNanoSheet"
        device_layers_allowed = ["PMOSGate", "NMOSGate",
                                 "PMOSInterconnect", "NMOSInterconnect"]
        node_list = []
        # needs to be fixd properly - adding to the gate_map affects this - ideally should me max of counter  number
        num_of_gates = self.num_of_gates

        # check if device_polygon intersects with nanosheet_polygon
        nanosheet_handlers = []
        for nanosheet_polygon in self.nanosheet_polygons[nanosheet]:
            if device_polygon_for_nanosheet.layer_name in device_layers_allowed and "Gate" in device_polygon_for_nanosheet.layer_name:
                nanosheet_base_id = "PMos" if nanosheet == "PmosNanoSheet" else "NMos"
                for key, value in self.gate_map[device_polygon_for_nanosheet].items():
                    base_num_id = value
                    intersection_polygon = device_polygon_for_nanosheet
                    intersection_coordinates = self.get_intersection_coordinates(
                        nanosheet_polygon, device_polygon_for_nanosheet, intersection_polygon)
                    if intersection_coordinates is not None:
                        nanosheet_handler = NanosheetHandler(device_polygon_for_nanosheet, nanosheet_polygon, self.net_name, num_of_gates,
                                                             base_num_id, nanosheet_base_id, self.num_nanosheet_nodes, self.layer_z_indices, polygon_node, intersection_coordinates)
                        nanosheet_handlers.append(nanosheet_handler)
            elif device_polygon_for_nanosheet.layer_name in device_layers_allowed and "Interconnect" in device_polygon_for_nanosheet.layer_name:
                for gate_neighbour, gate_polygon in self.neighbour_map[device_polygon_for_nanosheet].items():
                    for transistor_key, counter_value in self.gate_map[gate_polygon].items():
                        nanosheet_base_id = re.sub(r'\d+$', '', transistor_key)
                    base_num_id = self.gate_map[gate_polygon][gate_neighbour]
                    intersection_polygon = gate_polygon
                    intersection_coordinates = self.get_intersection_coordinates(
                        nanosheet_polygon, device_polygon_for_nanosheet, intersection_polygon)
                    if intersection_coordinates is not None:
                        nanosheet_handler = NanosheetHandler(device_polygon_for_nanosheet, nanosheet_polygon, self.net_name, num_of_gates,
                                                             base_num_id, nanosheet_base_id, self.num_nanosheet_nodes, self.layer_z_indices, polygon_node, intersection_coordinates)
                        nanosheet_handlers.append(nanosheet_handler)
        node_list = []
        for nanosheet_handler_obj in nanosheet_handlers:
            nanosheet_node_list = nanosheet_handler_obj.create_nanosheet_nodes()
            node_list.extend(nanosheet_node_list)
        return node_list

    def _finalize(self):

        try:
            renamer = NodeRenamerFactory.get_renamer(
                self.technology, self.graph, self.layer_node_dict, self.root_node, self.net_name, self.is_vertical)
            renamer.rename()
        except Exception as e:
            logger.error(f"Error in get_renamer: {str(e)}")
            logger.error(traceback.format_exc())

        self.net_graph = BaseNetGraph(
            graph=renamer.graph,
            net_name=self.net_name,
            root_node=renamer.root_node,
            layer_node_dict=self.layer_node_dict,
            layer_to_key_dict=layer_to_key_dict,
            polygon_processor=self.polygon_processor,
            layer_z_indices=self.layer_z_indices,
            is_vertical=self.is_vertical,
            cell_name=self.cell_name,
            polygon_info_dict=self.polygon_info
        )
        return renamer.graph
    def get_net_graph(self):
        return self.net_graph


class NanosheetHandler:
    def __init__(self, device_polygon, nanosheet_polygon, net_name, num_gates, base_num_id, nanosheet_base_id, num_nanosheet_nodes, layer_z_indices, polygon_node, intersection_coordinates):
        self.device_polygon = device_polygon
        self.nanosheet_polygon = nanosheet_polygon
        self.net_name = net_name
        self.num_gates = num_gates
        self.base_num_id = base_num_id
        self.num_nanosheet_nodes = num_nanosheet_nodes
        self.nanosheet_base_id = nanosheet_base_id
        self.layer_z_indices = layer_z_indices
        self.polygon_node = polygon_node
        self.intersection_coordinates = intersection_coordinates

    def create_nanosheet_nodes(self):
        node_list = []
        delta = 0
        for i in range(self.num_nanosheet_nodes):
            # add 1/num of nanosheets to the z_index
            try:
                gate_type = "PMOS" if self.nanosheet_polygon.layer_name.upper(
                ).startswith("PMO") else "NMOS"
                nanosheet_node_id = f"{self.nanosheet_base_id}{self.base_num_id + i*self.num_gates[gate_type]}"

                node = NanosheetNode(self.nanosheet_polygon, self.device_polygon, self.net_name, nanosheet_node_id,
                                     self.layer_z_indices, self.polygon_node, delta=delta, intersection_coordinates=self.intersection_coordinates)
                delta += 1/self.num_nanosheet_nodes
                if not hasattr(node, 'node_id') or not hasattr(node, 'layer_name'):
                    logger.error(
                        f"Invalid nanosheet node created: {nanosheet_node_id}")
                    continue
                node_list.append(node)
            except Exception as e:
                logger.error(f"Error creating nanosheet node: {str(e)}")

        return node_list


class ResistanceGraph:

    def __init__(self, gds_file, num_nanosheet_nodes, layer_properties_pdk, layer_map_dir, show_graphs=False, cell_name="", polygon_processor: PolygonProcessor = None) -> None:

        self.layer_map_dir = layer_map_dir
        self.layer_properties = None
        self.polygon_processor = polygon_processor
        self.layer_properties = self.polygon_processor.layer_properties
        self.layerMap = self.polygon_processor.layerMap
        self.layer_to_layer_name = self.polygon_processor.layer_to_layer_name
        self.num_nanosheet_nodes = num_nanosheet_nodes
        self.layer_numbers = self.polygon_processor.layer_numbers
        self.drain_neighbour_map = defaultdict(dict)
        self.gate_map = {}
        self.num_of_gates = {"PMOS": 0, "NMOS": 0}
        self.layer_z_indices = {}
        self.layer_properties_pdk = layer_properties_pdk
        self.create_z_index_map()
        self.transistor_polygon_manager = TransistorPolygonManager(
            self.drain_neighbour_map, self.gate_map, self.num_of_gates, self.layer_numbers, self.polygon_processor)
        self.drain_neighbour_map, self.gate_map = self.transistor_polygon_manager.create_neighbour_map()
        self.num_gates = self.transistor_polygon_manager.get_num_of_gates()
        self.cell_name = cell_name
        self.polygon_info_dict = self.polygon_processor.polygons
        self.text_labels = self.polygon_processor.text_labels
        self.graph_dict = None

    def build_graph(self):

        net_graphs = {}
        net_polygons = defaultdict(set)
        metal_polygon_layers = [self.polygon_processor.layer_numbers['M0'],
                                self.polygon_processor.layer_numbers['M1']]  # [200, 202]
        vss_vdd_polygons = defaultdict(set)
        # backside power rail ---> the 1000 should handle it for backside pwoer rail false
        VSS_VDD = [self.polygon_processor.layer_numbers['BSPowerRail']]
        nanosheet_polygons = []
        nanosheet_layers = [self.polygon_processor.layer_numbers['PmosNanoSheet'],
                            self.polygon_processor.layer_numbers['NmosNanoSheet']]
        is_vertical = False

        for layer in metal_polygon_layers:
            for polygon in self.polygon_processor.layerMap.get(layer, []):
                if polygon.datatype == 0 and polygon.layer in metal_polygon_layers:
                    if polygon.layer == self.polygon_processor.layer_numbers['M1']:
                        is_vertical = True

                if polygon.datatype == 0 and polygon.textPolygons:
                    for text_label in polygon.textPolygons:
                        text_label_string = self.polygon_processor.text_labels[text_label].string
                        net_name = normalize_name(text_label_string)
                        net_polygons[net_name] = set([polygon])

        # Sort polygons within each net by x coordinate from bounds

        for net_name in net_polygons:
            net_polygons[net_name] = sorted(
                net_polygons[net_name], key=lambda polygon: polygon.point.bounds[0])
            net_polygons[net_name] = sorted(
                net_polygons[net_name], key=lambda polygon: polygon.point.bounds[1], reverse=True)
            net_polygons[net_name] = [net_polygons[net_name][0]]

        for layer in VSS_VDD:
            for polygon in self.polygon_processor.layerMap.get(layer, []):
                if polygon.datatype == 0 and polygon.textPolygons:
                    for text_label in polygon.textPolygons:
                        text_label_string = self.polygon_processor.text_labels[text_label].string
                        net_name = normalize_name(text_label_string)
                        net_polygons[net_name] = set([polygon])

        # Sort polygons within each net by x coordinate from bounds
        for net_name in vss_vdd_polygons:
            vss_vdd_polygons[net_name] = sorted(
                vss_vdd_polygons[net_name], key=lambda polygon: polygon.point.bounds[0])

        nanosheet_polygons = defaultdict(list)
        for nanosheet_layer in nanosheet_layers:
            for nanosheet_polygon in self.polygon_processor.layerMap.get(nanosheet_layer, []):
                layer_name = nanosheet_polygon.layer_name
                nanosheet_polygons[layer_name].append(nanosheet_polygon)

        for net_name, polygons in net_polygons.items():
            for polygon in polygons:
                graph_builder = BaseNetGraphBuilder(polygon,
                                                    self.num_nanosheet_nodes,
                                                    net_name, neighbour_map=self.drain_neighbour_map,
                                                    gate_map=self.gate_map,
                                                    nanosheet_polygons=nanosheet_polygons,
                                                    num_of_gates=self.num_of_gates,
                                                    polygon_processor=self.polygon_processor,
                                                    layer_z_indices=self.layer_z_indices,
                                                    is_vertical=is_vertical,
                                                    cell_name=self.cell_name,
                                                    polygon_info_dict=self.polygon_info_dict)

                net_graphs[net_name] = graph_builder

        # VDD and VSS
        for net_name, polygons in vss_vdd_polygons.items():
            for polygon in polygons:
                graph_builder = BaseNetGraphBuilder(polygon,
                                                    self.num_nanosheet_nodes,
                                                    net_name, neighbour_map=self.drain_neighbour_map,
                                                    gate_map=self.gate_map,
                                                    nanosheet_polygons=nanosheet_polygons,
                                                    num_of_gates=self.num_of_gates,
                                                    polygon_processor=self.polygon_processor,
                                                    layer_z_indices=self.layer_z_indices,
                                                    is_vertical=is_vertical,
                                                    cell_name=self.cell_name,
                                                    polygon_info_dict=self.polygon_info_dict)

                net_graphs[net_name] = graph_builder

        return net_graphs

    def create_z_index_map(self):

        if self.layer_properties_pdk:
            # Sort layers by their total z position (offset + height)
            z_positions = []
            for layer_num, props in self.layer_properties_pdk.items():
                try:
                    layer_num_int = int(layer_num) if isinstance(
                        layer_num, str) else layer_num
                    z_positions.append(
                        (layer_num_int, props['offset'] + props['height']))
                except (ValueError, TypeError):
                    continue
            # Sort by z position and assign indices (0 = bottom, n = top)
            sorted_layers = sorted(z_positions, key=lambda x: x[1])
            for index, (layer_num, _) in enumerate(sorted_layers):
                self.layer_z_indices[layer_num] = index


class ResistanceGraphManager:
    def __init__(self):
        try:
            self.graph_cache: Dict[str, ResistanceGraph] = {}
            self.active_graph: Optional[ResistanceGraph] = None
            self.pyg_data_cache = {}
        except Exception as e:
            print(f"Error initializing ResistanceGraphManager: {str(e)}")
            raise

    def get_polygon_processor(self, gds_path: str, layer_map_dir: str):

        polygon_processor = PolygonProcessor(gds_path, layer_map_dir)
        return polygon_processor

    def initialise_or_update_graph(self, gds_path: str, layer_properties_pdk: Dict, layer_map_dir: str, polygon_processor: PolygonProcessor, dataset: ResistanceDataset, num_nanosheets: int):
        """
        - Initializes or updates the ResistanceGraph for a given base layout.
        - If it's the first time seeing this base layout, create and cache the full graph.
        - If it's a permutation of an existing base layout, update polygon geometries only.

        @param gds_path: path to the gds file
        @param layer_properties_pdk: layer properties from the pdk
        @param layer_map_dir: directory containing the layer map
        @param polygon_processor: polygon processor object
        @param dataset: resistance dataset object
        @param num_nanosheets: number of nanosheets
        """
        try:
            
           
        
            
            base_layout_name = polygon_processor.base_layout_name
            
            layout_name = Path(gds_path).stem
            all_pyg_data = []
            
            if base_layout_name not in self.graph_cache:
               
                graph = ResistanceGraph(
                    gds_file=gds_path,
                    num_nanosheet_nodes=num_nanosheets,
                    layer_properties_pdk=layer_properties_pdk,
                    layer_map_dir=layer_map_dir,
                    show_graphs=False,
                    polygon_processor=polygon_processor
                )
                
                graph.graph_dict = graph.build_graph()
                self.graph_cache[base_layout_name] = graph
                self.active_graph = graph
                
                # Create PyG data objects for each net in the graph
                
                for net_name, net_graph_builder in graph.graph_dict.items():
                    try:
                       
                        net_graph = net_graph_builder.get_net_graph()
                        pyg_data = convert_to_pyg_data(net_graph.graph)
                        root_node_id = net_graph.root_node
                        graph_obj = net_graph.graph
                        processed_data = dataset.process_inference_graph(pyg_data)
                        all_pyg_data.append(
                            (layout_name, net_name, processed_data, root_node_id, graph_obj, gds_path))
                    except Exception as e:
                        logger.error(f"Error processing net {net_name}: {str(e)}")
                        logger.error(f"Full error traceback:\n{traceback.format_exc()}")
                        continue
            else:
                
                base_graph = self.graph_cache[base_layout_name]
                for net_name, net_graph_builder in base_graph.graph_dict.items():
                    try:
                       
                        net_graph_builder.update_graph_with_new_polygons(
                            polygon_processor.polygons)
                        net_graph = net_graph_builder.get_net_graph()
                        root_node_id = net_graph.root_node
                        graph_obj = net_graph.graph
                        pyg_data = convert_to_pyg_data(net_graph.graph)
                        processed_data = dataset.process_inference_graph(pyg_data)
                        all_pyg_data.append(
                            (layout_name, net_name, processed_data, root_node_id, graph_obj, gds_path))
                    except Exception as e:
                        logger.error(f"Error updating net {net_name}: {str(e)}")
                        logger.error(f"Full error traceback:\n{traceback.format_exc()}")
                        continue

            return all_pyg_data
        except Exception as e:
            logger.error(f"Error in initialise_or_update_graph: {str(e)}")
            logger.error(f"Full error traceback:\n{traceback.format_exc()}")
            raise
