import math
from functools import lru_cache
import torch
from torch_geometric.data import Data as PyGData
from resistance_graph.graph_nodes import NanosheetNode
import matplotlib.pyplot as plt
from pex_extraction.data_utils.preprocessing_regression import normalize_name
import networkx as nx
from typing import Dict, List
import pandas as pd
import re
import traceback
import logging
logger = logging.getLogger(__name__)

def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets

def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets

def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)

@lru_cache(maxsize=None)
def calculate_edge_features(connection_type: str, z_distance: float,bounds1: tuple, bounds2: tuple):
    """_summary_
    This function calculates the edge features for the given connection type, z distance, bounds1 and bounds2.
    Args:
        connection_type (str): connection type of an edge
        z_distance (float): z distance
        bounds1 (tuple): bounds of polygon 1
        bounds2 (tuple): bounds of polygon 2

    Returns:
        list: features converted to model input
    """
    types = ['GATE', 'INTERCONNECT', 'VIA', 'NANOSHEET']
    #features = [1.0 if t in connection_type.upper() else 0.0 for t in types]
    features = [1.0 if t in t else 0.0 for t in types]
    
    if bounds1 and bounds2:
        c1x = (bounds1[0] + bounds1[2]) / 2
        c1y = (bounds1[1] + bounds1[3]) / 2
        c2x = (bounds2[0] + bounds2[2]) / 2
        c2y = (bounds2[1] + bounds2[3]) / 2
        dist = ((c1x - c2x) ** 2 + (c1y - c2y) ** 2) ** 0.5
        features.append(dist)

    # Z-distance positional encoding (dim=4)
    pos_encoding_dim = 4
    for i in range(pos_encoding_dim // 2):
        freq = 1.0 / (10000 ** (2 * i / pos_encoding_dim))
        features.append(math.sin(z_distance * freq))
        features.append(math.cos(z_distance * freq))
    
    return features

@lru_cache(maxsize=None)
def calculate_node_features(layer_name: str, z_index: float, is_nanosheet: bool, suffix: float = 0.0,bounds: tuple = None):
    """_summary_
    This function calculates the node features for the given layer name, z index, is nanosheet, suffix and bounds.
    Args:
        layer_name (str): layer name
        z_index (float): z index
        is_nanosheet (bool): is nanosheet - identifies if a layer is a nanosheet
        suffix (float, optional): suffix. Defaults to 0.0. Suffix associated with a node
        bounds (tuple, optional): bounds. Defaults to None. Bounds of the polygon in the node

    Returns:
        list: features converted to model input
    """
    features = []
    layer_types = [
        'M0', 'M1', 'BSPowerRail', 'PMOSGate', 'NMOSGate',
        'PMOSInterconnect', 'NMOSInterconnect',
        'VIA_M0_M1', 'VIA_M1_M2', 'VIA_Interconnect',
        'PmosNanoSheet', 'NmosNanoSheet', 'Unused'
    ]
    features.extend([1.0 if lt.lower() in layer_name.lower() else 0.0 for lt in layer_types])
    pos_encoding_dim = 4
    for i in range(pos_encoding_dim // 2):
        freq = 1.0 / (10000 ** (2 * i / pos_encoding_dim))
        features.extend([math.sin(z_index * freq), math.cos(z_index * freq)])
    
    #if bounds are provided, add width and height to the features
    if bounds:
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        features.extend([width, height])
   
    features.append(float(is_nanosheet))
    try:
        nanosheet_index = float(suffix) if is_nanosheet else 0.0
    except ValueError:
        nanosheet_index = 0.0
    features.append(nanosheet_index)
   
    return features

def get_node_bounds(node):
    node_polygon = node.polygon
    bounds = node.polygon.point.bounds
    if node_polygon.connectedGate:
        bounds = node.polygon.point.union(node_polygon.connectedGate.point).bounds
    if node_polygon.connectedInterconnect:
        bounds = node.polygon.point.union(node_polygon.connectedInterconnect.point).bounds
    if node_polygon.planarConnectedPolygon:
        bounds = node.polygon.point.union(node_polygon.planarConnectedPolygon.point).bounds
    return bounds

def get_edge_features(graph: nx.Graph,node_map: Dict[str, int], net_name=''):
    """ gets edge features required for ML model for the given graph

    Args:
        graph (nx.Graph): graph object
        node_map (Dict[str, int]): node map for the given graph

    Returns:
        list: edge features
    """

    edge_index = []
    edge_features = []
    edge_resistance = []
    edge_mask = []
    sorted_edges = sorted(graph.edges(), key=lambda edge: "_".join(sorted((edge[0]+'_to_'+edge[1]).split("_"))))
    for u, v in sorted_edges:
        if str(u)<str(v):
            u,v = v,u
        node1 = graph.nodes[u]["data"]
        node2 = graph.nodes[v]["data"]
        conn_type = graph.edges[u, v].get("connection_type", "")
        z1 = float(node1.z_index if hasattr(node1, 'z_index') else 0)
        z2 = float(node2.z_index if hasattr(node2, 'z_index') else 0)
        z_distance = abs(z1 - z2)
        node1_bounds = get_node_bounds(node1)
        node2_bounds = get_node_bounds(node2)
        if str(node1_bounds)>str(node2_bounds):
            node2_bounds, node1_bounds = node1_bounds, node2_bounds
        features = calculate_edge_features(conn_type, z_distance,tuple(node1_bounds), tuple(node2_bounds))
        #dynamic = get_dynamic_edge_feature(tuple(node1.polygon.point.bounds), tuple(node2.polygon.point.bounds))
        #eatures = static# + dynamic
        edge_index.extend([[node_map[u], node_map[v]], [node_map[v], node_map[u]]])
        edge_features.extend([features, features])
        resistance = graph.edges[u, v].get('resistance', 0.0)
        has_csv_value = graph.edges[u, v].get('resistance_from_csv', False)
        if math.isnan(resistance) or resistance <= 0:
            resistance = 0.0
            has_csv_value = False

        edge_resistance.extend([resistance, resistance])
        edge_mask.extend([has_csv_value, has_csv_value])

    edge_index = torch.tensor(edge_index, dtype=torch.long).t()
    edge_attr = torch.tensor(edge_features, dtype=torch.float)
    y = torch.tensor(edge_resistance, dtype=torch.float).view(-1, 1)
    mask = torch.tensor(edge_mask, dtype=torch.bool)
    return edge_index, edge_attr, y, mask
    
def get_node_features(graph: nx.Graph):
    """_summary_

    Args:
        graph (nx.Graph): gets node features required for ML model for the given graph

    Returns:
        list: node features
    """
        # Collect node features
    node_features = []
    for node in sorted(graph.nodes(), key=lambda x: str(x)):
        node = graph.nodes[node]["data"]
        node_suffix = getattr(node, "suffix", 0.0)
        features = calculate_node_features(node.layer_name, float(node.z_index), isinstance(node, NanosheetNode), node_suffix, tuple(get_node_bounds(node)))
        node_features.append(features)
    return node_features

def convert_to_pyg_data(graph: nx.Graph, net_name=''):
        """Convert NetworkX graph to PyTorch Geometric Data object
        Node features structure:
        - Layer type one-hot encoding (len(layer_types) dimensions)
        - Z-index positional encoding (4 dimensions)
        - Polygon width (1 dimension)
        - Polygon height (1 dimension)
        - Is nanosheet flag (1 dimension)
        - Nanosheet index (1 dimension)
        """
        node_map = {node: idx for idx, node in enumerate(sorted(graph.nodes(), key=lambda x: str(x)))}
        idx_to_name = {idx: node for node, idx in node_map.items()}  
        node_features = get_node_features(graph)
        x = torch.tensor(node_features, dtype=torch.float)
        edge_index, edge_attr, y, mask = get_edge_features(graph,node_map, net_name)
        pyg_data = PyGData(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y, edge_mask=mask)
        pyg_data.node_names = [idx_to_name[i] for i in range(len(node_map))]
        return pyg_data

def visualize_all_graphs(graph_dict: Dict[str, nx.Graph], output_dir=None):
        # Create graphs directory if it doesn't exist
        import os
        if output_dir is None:
            graphs_dir = "./graphs"
        else:
            graphs_dir = output_dir
        os.makedirs(graphs_dir, exist_ok=True)
        for net_name, net_graph in graph_dict.items():
            output_path = os.path.join(
                graphs_dir, f"{normalize_name(net_name)}.png")
            net_graph.visualize_graph_old(output_path, show_z_index=True)
        #print(f"finished visualizing all graphs")

def visualize_graph_old(graph: nx.Graph, output_path: str, show_z_index=False):
        """Visualize the graph with basic layout"""
       
        graph_obj = graph
        
        plt.figure(figsize=(30, 20))
        pos = nx.spring_layout(graph_obj)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph_obj, pos, node_size=3000)
        
        # Draw edges
        nx.draw_networkx_edges(graph_obj, pos, arrows=True, width=2.0)
        
        # Draw node labels
        labels = {node: node for node in graph_obj.nodes()}
        nx.draw_networkx_labels(graph_obj, pos, labels, font_size=10)
        
        plt.title('Graph Structure', fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        
        # Save the visualization
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()

def ingest_resistance_from_csv(graph: nx.Graph, csv_path: str, file_identifier: str, debug_edge_match=True):
        """
        Ingest resistance values from CSV and add them to the graph edges.
        
        Args:
            csv_path (str): Path to CSV file containing resistance breakdown.
            file_identifier (str): Layout identifier to match in CSV.
            debug_edge_match (bool): Enable detailed edge matching debugging.
        """
        # Setup debug logging with a buffer (instead of writing to file on every log)
        debug_buffer = [] if debug_edge_match else None
        def debug_log(message):
            if debug_buffer is not None:
                debug_buffer.append(message)
        
        def get_gate_line(m):
            return re.search(r'_([\w]+)GateLine$', m.group(1)).group(1)
        
        def get_via_layer(m):
            return re.search(r'_([\w]+)ViaInt\d*$', m.group(1)).group(1)
        
        def get_metal0_top(m):
            # Extract the number after ViaInt; default to '0' if missing.
            return re.search(r'ViaInt(\d*)', m.group(1)).group(1) or '0'
        
        def flip_pm_nmos(key: str) -> str:
            """
            Flip PMos and NMos tokens using a temporary placeholder.
            """
            return key.replace('NMos', 'TEMP').replace('PMos', 'NMos').replace('TEMP', 'PMos')
        
        # Cache for candidate variations to avoid redundant recalculation.
        candidate_variation_cache = {}

        def get_variations(candidate: str) -> List[str]:
            if candidate in candidate_variation_cache:
                return candidate_variation_cache[candidate]
            variations = [candidate]
            if "_to_" in candidate:
                parts = candidate.split("_to_")
                variations.append(f"{parts[1]}_to_{parts[0]}")
                variations.append(swap_edge_tokens(candidate))
            variations.extend(swap_underscore_parts(candidate))
            candidate_variation_cache[candidate] = variations
            return variations
        
        # EXTRA CACHE: Save the underscore swap variations for a given node id.
        node_variations_cache = {}

        def get_node_variations(node_id: str) -> List[str]:
            if node_id not in node_variations_cache:
                node_variations_cache[node_id] = swap_underscore_parts(node_id)
            return node_variations_cache[node_id]
        
        def try_candidate(candidate_key: str) -> bool:
            nonlocal found_match, edges_updated_total
            debug_log(f"Trying candidate: {candidate_key}")
            if candidate_key in resistance_dict:
                resistance_value = resistance_dict[candidate_key]
                debug_log(f"  Success! Found resistance: {resistance_value}")
                graph.edges[u, v]['resistance'] = resistance_value
                graph.edges[u, v]['resistance_from_csv'] = True
                found_match = True
                edges_updated_total += 1
            return found_match
        
        def swap_underscore_parts(node_id: str) -> List[str]:
            """Generate variations of node_id by swapping parts around underscores."""
            parts = node_id.split('_')
            if len(parts) <= 1:
                return [node_id]
            
            variations = []
            # Add original
            variations.append(node_id)
            # Add variation with first two parts swapped
            if len(parts) >= 2:
                swapped = parts.copy()
                swapped[0], swapped[1] = swapped[1], swapped[0]
                variations.append('_'.join(swapped))
            return variations
        
        def swap_edge_tokens(candidate: str) -> str:
            """
            For a candidate with a '_to_' delimiter, swap the first two underscore-delimited tokens
            in each half and return the new candidate.
            For example, for "NMos6_VDDMetal0Top0_to_NMos7_VDDMetal0Top0" it returns
            "VDDMetal0Top0_NMos6_to_VDDMetal0Top0_NMos7".
            """
            if "_to_" not in candidate:
                return candidate
            left, right = candidate.split("_to_", 1)
            return f"{swap_first_two(left)}_to_{swap_first_two(right)}"
        
        def swap_first_two(part: str) -> str:
            """
            Swap the first two tokens in an underscore-delimited string.
            """
            tokens = part.split("_")
            if len(tokens) < 2:
                return part
            tokens[0], tokens[1] = tokens[1], tokens[0]
            return "_".join(tokens)
        
        try:
            # Read CSV file and find the matching row for our file identifier.
            df = pd.read_csv(csv_path)
            row = df[df['File'] == file_identifier]
            if len(row) == 0:
                logger.warning(
                    f"No matching row found for file '{file_identifier}'")
                return
            
            # Convert the row to a dictionary for easier key look-ups.
            resistance_dict = row.iloc[0].to_dict()
            
            # Define regex patterns for edge matching:
            patterns = [
                # GateLine pattern.
                (r'(.+_\w+GateLine) to ([NP]Mos\d+)',
                 lambda m: [
                     f"{m.group(1)}_to_{m.group(2)}_{get_gate_line(m)}GateLine",
                     f"{m.group(2)}_{get_gate_line(m)}GateLine_to_{m.group(1)}"
                 ]),
                
                # Metal/Via pattern.
                (r'(.+_\w+ViaInt\d*) to ([NP]Mos\d+)',
                 lambda m: [
                     f"{m.group(1)}_to_{get_via_layer(m)}Metal0Top{get_metal0_top(m)}_{m.group(2)}",
                     f"{get_via_layer(m)}Metal0Top{get_metal0_top(m)}_{m.group(2)}_to_{m.group(1)}"
                 ])
            ]
            
            edges_updated_total = 0
            for u, v, edge_data in graph.edges(data=True):
                if debug_edge_match:
                    debug_log(f"\nProcessing edge: ({u}, {v})")
                    debug_log(f"Edge data: {edge_data}")
                
                # Skip edges that already have CSV-based resistance values.
                if edge_data.get('resistance_from_csv', False):
                    continue
                
                # Get the connection type from the edge.
                edge_type = edge_data.get('connection_type', '')
                # Standardize "ViaInt" and "Metal0Top" (adding default numbers if necessary).
                edge_type_std = re.sub(r'ViaInt(?!\d)', 'ViaInt0', edge_type)
                edge_type_std = re.sub(
                    r'Metal0Top(?!\d)', 'Metal0Top0', edge_type_std)
                
                found_match = False  # Flag to mark if we found a candidate.
                
                # 1. Try candidates using underscore delimiter only
                if try_candidate(edge_type_std):
                    continue
                
                # 2. Try the reverse of the edge (swapping u and v) with underscore only
                reverse_edge_std = f"{v}_to_{u}"
                if try_candidate(reverse_edge_std):
                    continue
                
                # 3. Use regex-based pattern matching on the version with spaces.
                for pattern, formatter in patterns:
                    match = re.match(pattern, edge_type_std)
                    if match:
                        possible_matches = formatter(match)
                        for candidate in possible_matches:
                            candidate_variations = get_variations(candidate)
                            match_found = False
                            for cand in candidate_variations:
                                if try_candidate(cand):
                                    match_found = True
                                    break
                            if match_found:
                                break
                        if found_match:
                            break
                if not found_match:
                    # Instead of recomputing, get cached variations for the node identifiers.
                    u_variations = get_node_variations(u)
                    v_variations = get_node_variations(v)
                    
                    # Try regular variations.
                    for u_var in u_variations:
                        for v_var in v_variations:
                            candidate = f"{u_var}_to_{v_var}"
                            candidate_variations = get_variations(candidate)
                            for cand in candidate_variations:
                                if try_candidate(cand):
                                    found_match = True
                                    break
                            if found_match:
                                break
                                
                            candidate_flipped = flip_pm_nmos(candidate)
                            candidate_variations = get_variations(
                                candidate_flipped)
                            for cand in candidate_variations:
                                if try_candidate(cand):
                                    found_match = True
                                    break
                            if found_match:
                                break
                        if found_match:
                            break
                                
                    # Additionally, if either endpoint contains patterns that might need digit suffixes,
                    # generate fallback candidate variations.
                    if not found_match and (
                        ("Metal0Top" in u and re.search(r'Metal0Top(?!\d)', u)) or 
                        ("Metal0Top" in v and re.search(r'Metal0Top(?!\d)', v)) or
                        ("MetalBPRVia" in u and re.search(r'MetalBPRVia(?!\d)', u)) or
                        ("MetalBPRVia" in v and re.search(r'MetalBPRVia(?!\d)', v))
                    ):
                        # Creates fallback strings with digit suffixes for both patterns
                        u_fallback = u.replace("Metal0Top", "Metal0Top0").replace(
                            "MetalBPRVia", "MetalBPRVia0")
                        v_fallback = v.replace("Metal0Top", "Metal0Top0").replace(
                            "MetalBPRVia", "MetalBPRVia0")
                        u_fallback_variations = get_node_variations(u_fallback)
                        v_fallback_variations = get_node_variations(v_fallback)
                        
                        for u_var in u_fallback_variations:
                            for v_var in v_fallback_variations:
                                candidate = f"{u_var}_to_{v_var}"
                                candidate_variations = get_variations(
                                    candidate)
                                for cand in candidate_variations:
                                    if try_candidate(cand):
                                        found_match = True
                                        break
                                if found_match:
                                    break
                                
                                candidate_flipped = flip_pm_nmos(candidate)
                                candidate_variations = get_variations(
                                    candidate_flipped)
                                for cand in candidate_variations:
                                    if try_candidate(cand):
                                        found_match = True
                                        break
                                
                                if found_match:
                                    break
                                
                                candidate_swapped = swap_edge_tokens(candidate)
                                candidate_variations = get_variations(
                                    candidate_swapped)
                                for cand in candidate_variations:
                                    if try_candidate(cand):
                                        found_match = True
                                        break
                                if found_match:
                                    break
                            if found_match:
                                break
                        if found_match:
                            break
                if debug_edge_match and not found_match:
                    debug_log("No match found for this edge")
            
            if edges_updated_total == 0:
                logger.warning("No edges were updated with resistance values")
                logger.debug(
                    f"Sample edge types in graph: {[d.get('connection_type', '') for _, _, d in list(graph.edges(data=True))[:5]]}")
            else:
                logger.debug(
                    f"Updated a total of {edges_updated_total} edges with resistance values")
        
        except Exception as e:
            logger.error(f"Error ingesting resistance values: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            if debug_buffer is not None:
                with open('edge_matching_debug.txt', 'w') as df:
                    df.write("\n".join(debug_buffer))

def visualize_graph_old(graph: nx.Graph, output_path: str, show_z_index=False):
        """Visualize the graph with basic layout"""
      
        graph_obj = graph
        
        plt.figure(figsize=(30, 20))
        pos = nx.spring_layout(graph_obj)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph_obj, pos, node_size=3000)
        
        # Draw edges
        nx.draw_networkx_edges(graph_obj, pos, arrows=True, width=2.0)
        
        # Draw node labels
        labels = {node: node for node in graph_obj.nodes()}
        nx.draw_networkx_labels(graph_obj, pos, labels, font_size=10)
        
        plt.title('Graph Structure', fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        
        # Save the visualization
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
