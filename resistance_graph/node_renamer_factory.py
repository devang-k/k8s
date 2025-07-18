import networkx as nx
from typing import Dict, List
from abc import ABC, abstractmethod
from resistance_graph.graph_nodes import  ViaNode, MetalNode,DeviceNode,NanosheetNode
import logging
logger = logging.getLogger(__name__)
from resistance_graph.graph_utils import is_power_net

class NodeRenamerFactory:
    @staticmethod
    def get_renamer(technology: str, graph: nx.Graph, layer_node_dict: Dict[str, List[str]], root_node: str,net_name: str,is_vertical: bool) -> 'NodeRenamer':
        
        if technology == "cfet":
            
            return CFETNodeRenamer(graph, layer_node_dict, root_node,net_name,technology,is_vertical)
        elif technology == "gaa" or technology == "finfet":
           
            return GAANodeRenamer(graph, layer_node_dict, root_node,net_name,technology,is_vertical)
        else:
            raise ValueError(f"Unsupported technology: {technology}")
    
 

class NodeRenamer:
    """_summary_

    
    Args:
        ABC (_type_): _description_
    """
    def __init__(self, graph: nx.Graph, layer_node_dict: Dict[str, List[str]], root_node: str,net_name: str,technology: str,is_vertical: bool):
        self.graph = graph
        self.layer_node_dict = layer_node_dict
        self.root_node = root_node
        self.net_name = net_name
        self.technology = technology
        self.is_vertical = is_vertical
    @abstractmethod
    def rename(self):
        pass


    def reset_single_device_node_ids(self,node,i):
        edges = [(u,v) for (u,v) in self.graph.edges() if u == node.node_id or v == node.node_id]
        id_mapping = {}
        #maybe exclude nets which are VDD or VSS - check for CFET and GAA both.
        if not is_power_net(self.net_name): 
            if isinstance(node,DeviceNode):
                old_node_id = node.node_id
                node_ids = old_node_id.split("_")
                for j in range(len(node_ids)):
                    if "Via" not in node_ids[j]:
                        #print(f"node_ids[j]: {node_ids[j]}")
                        # Check if last element is numeric and equals 0
                        if node_ids[j][-1].isdigit(): #and node_ids[j][-1] == '0':
                            node_ids[j] = node_ids[j][:-1]  # Remove the trailing 0
                new_node_id = "_".join(node_ids)
                id_mapping[old_node_id] = new_node_id
                #should now replace it for its nanosheeet nodes too.
                nanosheet_nodes_to_process = list(self.graph.neighbors(node.node_id))
                for nanosheet_node_id in nanosheet_nodes_to_process:
                    nanosheet_node = self.graph.nodes[nanosheet_node_id]['data']
                    if isinstance(nanosheet_node,NanosheetNode):
                        old_nanosheet_node_id = nanosheet_node.node_id
                        nanosheet_node_ids = nanosheet_node.node_id.split("_")
                        
                        for j in range(len(nanosheet_node_ids)):
                            if "NMos" not in nanosheet_node_ids[j] and "PMos" not in nanosheet_node_ids[j]:
                                if nanosheet_node_ids[j][-1].isdigit():
                                    nanosheet_node_ids[j] = nanosheet_node_ids[j][:-1]
                        new_nanosheet_node_id = "_".join(nanosheet_node_ids)
                        id_mapping[old_nanosheet_node_id] = new_nanosheet_node_id
           
        return id_mapping


    

class CFETNodeRenamer(NodeRenamer):
    def __init__(self, graph: nx.Graph, layer_node_dict: Dict[str, List[str]], root_node: str,net_name: str,technology: str,is_vertical: bool):
   
        super().__init__(graph, layer_node_dict, root_node,net_name,technology,is_vertical)

        self.polygon_node = graph.nodes[self.root_node]['data']
     
  

    def rename(self):
       
        self._reset_node_ids()
        
        self._rename_top_metal_nodes(self.polygon_node)


    def _rename_top_metal_nodes(self, polygon_node):
       
        logger.info(f"inside CFETrename top metal nodes")
        id_mapping = {}
        metal_node_id = polygon_node.node_id
        # for polygon in
        for metal_key in ['M0', 'M1']:
            metal_nodes = self.layer_node_dict[metal_key]
            for i, metal_node in enumerate(metal_nodes):
                metal_node_obj = self.graph.nodes[metal_node]['data']
                if metal_node_obj.parent_node is None and metal_node_obj.metal_counter == 0:
                    id_mapping[metal_node_obj.node_id] = self.net_name
                    self.layer_node_dict[metal_key][i] = self.net_name
                    self.root_node = self.net_name
                    #self.graph.nodes[self.root_node]['data'].node_id = self.net_name
                  
                    logger.info(f"metal_node_obj.node_id: {metal_node_obj.node_id}")
                    metal_node_obj.node_id = self.net_name
                

        self.graph = nx.relabel_nodes(self.graph, id_mapping)
        

    def _reset_node_ids(self):
        logger.info(f"inside CFET reset node ids")
        id_mapping = {}

        for layer, nodes in self.layer_node_dict.items():
            if len(self.layer_node_dict.get('M0', [])) > 1:
                if layer == "M0":
                    for i, old_node_id in enumerate(nodes):
                        # get node from graph
                        node = self.graph.nodes[old_node_id]['data']

                        # create new node id
                        id_mapping = self.create_new_node_id(node, i)
      
                        self.graph = nx.relabel_nodes(self.graph, id_mapping)
                        # relabel does not change the node_id attribute of the base node object only changes the graph node id
                        if self.root_node in id_mapping:
                            self.root_node = id_mapping[self.root_node]

            if (layer == "Interconnect" or layer == "Gate"):
                # only one gate or interconnect node present.
                if len(nodes) == 1:
                    for i, old_node_id in enumerate(nodes):
                        node = self.graph.nodes[old_node_id]['data']
                        device_id_mapping = self.reset_single_device_node_ids(
                            node, i)

                        self.graph = nx.relabel_nodes(
                            self.graph, device_id_mapping)
        
        self.graph = nx.relabel_nodes(self.graph, id_mapping)


    def create_new_node_id(self, node, i):
        # three types - metal, via and device.
        # Print edges connected to current node regardless of type
        edges = [(u, v) for (u, v) in self.graph.edges()
                 if u == node.node_id or v == node.node_id]
        id_mapping = {}
        
        if isinstance(node, MetalNode): 
            old_node_id = node.node_id

            node.common_string = str(i)
            node_id = self.net_name + f"Block{i+1}"

            id_mapping[old_node_id] = node_id
            self.layer_node_dict["M0"][i] = node_id
            node.node_id = node_id

            edges = [(u, v) for (u, v) in self.graph.edges()
                        if u == node.node_id or v == node.node_id]
            for edge in edges:
                node_id_1 = edge[0]
                node_id_2 = edge[1]
                node_1 = self.graph.nodes[node_id_1]['data']
                node_2 = self.graph.nodes[node_id_2]['data']
                if "Via" in node_id_1:
                    old_node_id_1 = node_id_1.split("_")
                    for j in range(len(old_node_id_1)):
                        if "Metal" in old_node_id_1[j]:

                            old_node_id_1[j] = old_node_id_1[j] + \
                                str(node.metal_counter)
                    new_node_id_1 = "_".join(old_node_id_1)
                    id_mapping[node_id_1] = new_node_id_1
                if "Via" in node_id_2:
                    old_node_id_2 = node_id_2.split("_")
                    for j in range(len(old_node_id_2)):
                        if "Metal" in old_node_id_2[j]:

                            old_node_id_2[j] = old_node_id_2[j] + \
                                str(node.metal_counter)
                    new_node_id_2 = "_".join(old_node_id_2)
                    id_mapping[node_id_2] = new_node_id_2

        return id_mapping


class GAANodeRenamer(NodeRenamer):
    """_summary_

    Args:
        NodeRenamer (_type_): _description_
    """
    def __init__(self, graph: nx.Graph, layer_node_dict: Dict[str, List[str]], root_node: str,net_name: str,technology: str,is_vertical: bool):
        super().__init__(graph, layer_node_dict, root_node,net_name,technology,is_vertical)
        self.polygon_node = graph.nodes[self.root_node]['data']

    def rename(self):
        self._reset_node_ids()
        # self._rename_multimetal_nodes()
        self._rename_top_metal_nodes(self.polygon_node)

    def _rename_top_metal_nodes(self, polygon_node):

        id_mapping = {}
        metal_node_id = polygon_node.node_id
        # for polygon in
        for metal_key in ['M0', 'M1']:
            metal_nodes = self.layer_node_dict[metal_key]
            for i, metal_node in enumerate(metal_nodes):
                metal_node_obj = self.graph.nodes[metal_node]['data']
                if metal_node_obj.parent_node is None and metal_node_obj.metal_counter == 0:
                    id_mapping[metal_node_obj.node_id] = self.net_name
                    self.layer_node_dict[metal_key][i] = self.net_name
                    self.root_node = self.net_name
                    #self.graph.nodes[self.root_node]['data'].node_id = self.net_name

                    metal_node_obj.node_id = self.net_name

        self.graph = nx.relabel_nodes(self.graph, id_mapping)

    def extract_suffix_after_net(self, full_string, known_net):
        if full_string.startswith(known_net):
            suffix = full_string[len(known_net):]
            if suffix.startswith("Metal"):
                metal_number = suffix[len("Metal"):]
                suffix = "Metal"
            return known_net, suffix if suffix else None, metal_number if metal_number else None
        return full_string, None, None
        
    def _reset_node_ids(self):

        id_mapping = {}
        for layer, nodes in self.layer_node_dict.items():

            if (layer == "Interconnect" or layer == "Gate"):
                # only one gate or interconnect node present.
                if len(nodes) == 1:
                    for i, old_node_id in enumerate(nodes):
                        node = self.graph.nodes[old_node_id]['data']
                        device_id_mapping = self.reset_single_device_node_ids(
                            node, i)

                        self.graph = nx.relabel_nodes(
                            self.graph, device_id_mapping)

        if len(self.layer_node_dict.get("M0", [])) == 1:

            m0_node = self.layer_node_dict["M0"][0]
            m0_node_obj = self.graph.nodes[m0_node]['data']
            if self.is_vertical:
                if m0_node_obj.parent_node is not None:
                    if isinstance(m0_node_obj.parent_node, ViaNode):
                        parent_node_split = m0_node_obj.parent_node.node_id.split(
                            "_")
                        for each in parent_node_split:
                            if "Via" in each:
                                via_suffix = each
                        full_string, suffix, metal_number = self.extract_suffix_after_net(
                            m0_node_obj.node_id, self.net_name)
                        end_suffix = f"{full_string}{suffix}{metal_number[0] if (metal_number and metal_number[0].isdigit()) else ''}"
                        new_name = via_suffix + "_" + end_suffix
                        id_mapping[m0_node] = new_name
                        neighbours = list(self.graph.neighbors(m0_node))
                        len_m0_vias = len(
                            self.layer_node_dict.get('M0_via', []))

                        for neighbour in neighbours:
                            if m0_node in neighbour:
                                parts_split = neighbour.split("_")
                                    # child_neighbour = list(
                                    #     self.graph.neighbors(neighbour))
                                for i, part in enumerate(parts_split):

                                    if m0_node in part:
                                        if part[-1] == "0":
                                            parts_split[i] = part[:-1]
                                    else:
                                        if len_m0_vias == 1 and part[-1] == "0":
                                            parts_split[i] = part[:-1]

                                new_id = "_".join(parts_split)
                                id_mapping[neighbour] = new_id
                                self.graph.nodes[neighbour]['data'].node_id = new_id
                        self.layer_node_dict["M0"] = [new_name]

                        self.graph.nodes[m0_node]['data'].node_id = new_name

            self.graph = nx.relabel_nodes(self.graph, id_mapping)
        

    def _rename_multimetal_nodes(self):

        m0_nodes = self.layer_node_dict["M0"]
        id_mapping = {}
        m1_nodes = self.layer_node_dict["M1"]
        
        metals = ["M0", "M1"]
        # mayf or this .. do M1 separately.. it needs to retain the SBAR20 AND SBAR21 in the via naming
        for metal in metals:
            m0_nodes = self.layer_node_dict.get(metal, [])
            if len(m0_nodes) > 1:
                for i, m0_node in enumerate(m0_nodes):
                    m0_node_obj = self.graph.nodes[m0_node]['data']
                    if self.is_vertical:
                        if m0_node_obj.parent_node is not None:  # and m0_node_obj.metal_counter > 0:
                            neighbours = list(
                                self.graph.neighbors(m0_node))
                            if isinstance(m0_node_obj.parent_node, ViaNode):
                                parent_node_split = m0_node_obj.parent_node.node_id.split(
                                    "_")

                                for each in parent_node_split:
                                    if "Via" in each:
                                        via_suffix = each

                                new_name = m0_node_obj.node_id + "_" + via_suffix
                                id_mapping[m0_node] = new_name
                                self.layer_node_dict[metal][i] = new_name
                                # replace with whateevr tis the layer number for vertical via
                                if m0_node_obj.parent_node.layer_name != 'VIA_M0_M1':
                                    # removing the via node THAT IS created aturally-  as part of traversal. needs to be removed only for the purpose of matching the edges.
                                    if m0_node_obj.parent_node.parent_node is not None:
                                        # add the new m0 node as a neighbour to the parent node
                                        self.graph.add_edge(m0_node_obj.parent_node.parent_node, [
                                                        self.graph.nodes[m0_node]['data']])
                                        self.graph.remove_node(
                                            m0_node_obj.parent_node.node_id)
                                        self.graph.nodes[m0_node]['data'].node_id = new_name
                    if m0_node_obj.parent_node is None:
                        if i == 0:
                            new_m0_node_id = m0_node_obj.node_id + "0"
                            id_mapping[m0_node] = new_m0_node_id
                            self.layer_node_dict[metal][i] = new_m0_node_id
                            # maybe can set this later
                            self.graph.nodes[m0_node]['data'].node_id = new_m0_node_id
                            neighbours = list(
                                self.graph.neighbors(m0_node))
                            for neighbour in neighbours:
                                parts = neighbour.split("_")
                                for index, part in enumerate(parts):
                                    if "Via" not in part:
                                        parts[index] = part + "0"
                                new_neighbour = "_".join(parts)

                                id_mapping[neighbour] = new_neighbour
                                self.graph.nodes[neighbour]['data'].node_id = new_neighbour
                    #
        # rename the nodes in the graph

        self.graph = nx.relabel_nodes(self.graph, id_mapping)