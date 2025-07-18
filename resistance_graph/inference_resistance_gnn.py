import torch
import logging
import argparse
import os
from json import load
from pathlib import Path
from resistance_graph.resistance_gnn import ResistanceRGCN, ResistanceDataset
from os import listdir
from tqdm import tqdm
from torch_geometric.data import Data as PyGData
import math
from collections import defaultdict
import pandas as pd
from stdcell_generation_client.technology_utils import load_tech_file
import networkx as nx
import matplotlib.pyplot as plt
import time
import traceback
import csv
from resistance_graph.equivalent_resistance import EquivalentResistance
#from resistance_graph.resistance_graph_builder import ResistanceGraph, BaseNetGraph,ResistanceGraphManager
from resistance_graph.generate_resistance_graph import ResistanceGraphManager,BaseNetGraphBuilder,ResistanceGraph,BaseNetGraph
from resistance_graph.graph_nodes import NodeFactory, BaseNode, ViaNode, DeviceNode, MetalNode, NanosheetNode
from pex_extraction.data_utils.preprocessing_regression import normalize_name
from pnr_permutations.generate_permutations import LayerProperties
from resistance_graph.extract_relative_resistance import ResistanceWriter
# Suppress warnings
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore')
import torch.nn as nn
# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Instead, just get the logger without configuring it
logger = logging.getLogger('sivista_app')

def get_available_nets(metrics_data):
    """Get list of all nets in the M0 layer from metrics data"""
    # Filter for M0 layer rows
    m0_rows = metrics_data[metrics_data['Layer'] == 'M0']
    
    nets = set()
    for _, row in m0_rows.iterrows():
        if pd.notna(row['Labels']):  # Check if Labels is not NaN
            # Convert string representation of list to actual list
            labels = eval(row['Labels']) if isinstance(row['Labels'], str) else row['Labels']
            nets.update(labels)
    
    return sorted(list(nets))

def get_available_devices():
    """Get list of available computing devices: GPUs and CPU"""
    devices = []
    
    # Always add CPU
    cpu_device = torch.device('cpu')
    devices.append(cpu_device)
    
    # Add CUDA devices if available
    if torch.cuda.is_available():
        cuda_count = torch.cuda.device_count()
        for i in range(cuda_count):
            devices.append(torch.device(f'cuda:{i}'))
    
    # Add MPS device (for Apple Silicon) if available
    try:
        if torch.backends.mps.is_available():
            devices.append(torch.device('mps'))
    except:
        pass
    
    return devices


class DataParallelPassthrough(nn.DataParallel):
    """Custom DataParallel implementation that allows attribute access to the wrapped module"""
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.module, name)


def load_trained_model(model_path: str, dataset: ResistanceDataset, device: torch.device) -> tuple:
    """Load trained model and normalization parameters from checkpoint"""
    # Only log important info, not debug
    logger.info("Loading trained model...")
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=device)
    
    # Get model dimensions from checkpoint if available, otherwise use dataset
    num_node_features = checkpoint.get('num_node_features', 21)  # Default to 21 if not in checkpoint
    num_edge_features = checkpoint.get('num_edge_features', 9)   # Default to 9 if not in checkpoint
    
    # Initialize model with dimensions from checkpoint or defaults
    model = ResistanceRGCN(
        num_node_features=num_node_features,
        num_edge_features=num_edge_features, 
        num_relations=4
    ).to(device)
    
    # Load model state
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Get transformation parameters from training history
    transform_mean = checkpoint.get('transform_mean')
    transform_std = checkpoint.get('transform_std')
    transform_type = checkpoint.get('transform_type', 'log')  # Default to log for backward compatibility
    transform_lambda = checkpoint.get('transform_lambda')
    
    if transform_mean is None or transform_std is None:
        # Try loading from separate normalization file
        norm_path = Path(model_path).parent / 'normalization_params.pt'
        if norm_path.exists():
            norm_params = torch.load(norm_path, map_location=device)
            transform_mean = norm_params['transform_mean']
            transform_std = norm_params['transform_std']
            transform_type = norm_params.get('transform_type', 'log')
            transform_lambda = norm_params.get('transform_lambda')
            logger.info(f"Loaded training normalization parameters from {norm_path}")
            logger.info(f"Training date: {norm_params.get('training_date', 'unknown')}")
        else:
            raise ValueError("Training normalization parameters not found in checkpoint or separate file")
    
    logger.info(f"Loaded model from epoch {checkpoint['epoch']}")
    logger.info(f"Using transformation type: {transform_type}")
    logger.info(f"Transform parameters - mean: {transform_mean:.4f}, std: {transform_std:.4f}")
    if transform_lambda is not None:
        logger.info(f"Transform lambda: {transform_lambda:.4f}")
    
    return model, transform_mean, transform_std, transform_type, transform_lambda

def predict_resistances(model: ResistanceRGCN, data, transform_mean: float, transform_std: float,                   
                       transform_type: str, transform_lambda: float, device: torch.device):
    """Run inference on a single graph using normalization parameters from training"""
    with torch.no_grad():
        # Move data to device
        data = data.to(device)
        
        # For single graphs, create a batch tensor of zeros
        if data.batch is None:
            data.batch = torch.zeros(data.x.size(0), dtype=torch.long, device=device)
        
        # Forward pass
        pred = model(data.x, data.edge_index, data.edge_attr, data.batch)
        
        # Create a temporary dataset object for transformation functions
        temp_dataset = ResistanceDataset(inference_mode=True, transform_type=transform_type)
        temp_dataset.transform_mean = transform_mean
        temp_dataset.transform_std = transform_std
        temp_dataset.transform_lambda = transform_lambda
        
        # Denormalize predictions using training normalization parameters
        pred_norm = pred * transform_std + transform_mean
        pred_denorm = temp_dataset._inverse_transform_values(pred_norm)
        
        # Get edge information
        edge_info = []
        for i in range(data.edge_index.size(1)):
            src_idx = data.edge_index[0, i].item()
            dst_idx = data.edge_index[1, i].item()
            
            # Get node names if available
            src_name = data.node_names[src_idx] if hasattr(data, 'node_names') else f"Node_{src_idx}"
            dst_name = data.node_names[dst_idx] if hasattr(data, 'node_names') else f"Node_{dst_idx}"
            
            resistance = pred_denorm[i].item()
            edge_info.append({
                'edge': f"{src_name}_to_{dst_name}",
                'resistance': resistance
            })
        
        return edge_info

def write_predictions_to_log(layout_name: str, cell_name: str, net_name: str, gds_file: str, edge_predictions: list, eq_resistance: float = None,output_dir = ""):
    """Write predictions to a log file"""
    # Create cell directory if it doesn't exist
    os.makedirs(f'{output_dir}', exist_ok=True)
    
    # Use a consistent naming scheme with capacitance predictions
    log_file = f"{output_dir}/{layout_name}_resistance_pred.log"
    
    # Check if file exists to determine if we need to write the header
    file_exists = os.path.exists(log_file)
    
    # Open in append mode
    with open(log_file, 'a') as f:
        # Only write header information if this is a new file
        if not file_exists:
            f.write(f"Layout: {layout_name}\n")
            f.write(f"Cell: {cell_name}\n")
            f.write(f"GDS: {gds_file}\n\n")
            f.write("Predicted Resistances:\n")
            f.write("-" * 60 + "\n")
        else:
            # Add a separator between nets
            f.write("\n")  # Extra newline for separation
        
        # Write predictions for this net
        f.write(f"\nNet: {net_name}\n")  # Add net name header
        for pred in edge_predictions:
            # Include net name in the edge identifier
            edge_parts = pred['edge'].split('_to_')
            if len(edge_parts) == 2:
                # Format: node1_to_node2: resistance
                f.write(f"{pred['edge']}: {pred['resistance']:.4f} Ohms\n")
        
        # Add equivalent resistance if available
        if eq_resistance is not None:
            f.write(f"\nEquivalent Resistance: {eq_resistance:.4f} Ohms\n")

def create_inference_graph(layer_properties_pdk, layer_map_str: str, gds_file: str, layer_map_dir, rgm,dataset,technology: str = 'cfet') -> tuple:
    """
    Create a ResistanceGraph for inference without ingesting resistance values.
    
    Args:
        target_net_name (str): Net to build graph for
        layer_properties_pdk (dict): Layer properties from tech file
        layer_map_str (str): Path to layer map file
        gds_file (str): Path to the GDS file
        layer_map_dir (str): Directory containing layer map files
        technology (str): Technology type ('cfet' or 'gaa')
    """
    # Set number of nanosheets based on technology
    num_nanosheets = 3 if technology.lower() == 'gaa' else 4

    polygon_processor = rgm.get_polygon_processor(gds_file,layer_map_dir)
    print(f"inside create_inference_graph calling initialise_or_update_graph for file: {gds_file}")
    logger.info(f"inside create_inference_graph calling initialise_or_update_graph for file: {gds_file}")
    rgm.initialise_or_update_graph(gds_file, technology, layer_properties_pdk, layer_map_dir, polygon_processor, dataset,num_nanosheets)
    # Get the appropriate net graph from the graph dictionary
    rg = rgm.active_graph

    return rg
        
def write_resistance_to_csv(resistance_data, pex_file, combine_resistance,suffix):
    """
    Merges resistance data (absolute or relative) with PEX predictions.
    
    Args:
        resistance_data (dict): Dictionary of file → net → resistance.
        pex_file (str): Path to the PEX CSV file.
        suffix (str): Suffix to use for resistance columns (e.g., "R_REL" or "R_pred_eq").
        combine_resistance (bool): Whether to combine and write the results.
    """
    try:
        if not combine_resistance:
            return

        logger.info(f"Combining resistance data with suffix: {suffix}")
        # Collect all unique nets
        all_nets = set()
        for net_dict in resistance_data.values():
            all_nets.update(net_dict.keys())

        # Read PEX predictions
        pex_df = pd.read_csv(pex_file)

        # Build resistance rows
        rows = []
        for file_name, net_dict in resistance_data.items():
            file_key = file_name.split('/')[-1].replace('.gds', '')  # consistent naming
            row = {"File": file_key}
            for net in sorted(all_nets):
                row[f"{suffix}_{net}"] = net_dict.get(net, 0)
            rows.append(row)

        # Create DataFrame and merge
        resistance_df = pd.DataFrame(rows)
        merged_df = pd.merge(pex_df, resistance_df, on='File', how='inner')
        merged_df.to_csv(pex_file, index=False)
        logger.info(f"Successfully merged resistance predictions into {pex_file}")

    except Exception as e:
        logger.error(f"Error merging resistance predictions: {str(e)}")
        raise

def batch_process_all_layouts(model, gds_files, metrics_data, layer_properties_pdk, layer_map_dir, dataset, transform_params, device, cell_name, use_multi_gpu=False, max_workers=None,technology="cfet",net_names=None):
    """
    Process ALL layouts and nets across permutations in a single forward pass
    with optional multi-GPU support and parallel graph building
    """
    import time
    # Detailed timing information
    timing = {
        'graph_creation': 0,
        'data_preparation': 0,
        'model_inference': 0,
        'post_processing': 0
    }
    transform_mean, transform_std, transform_type, transform_lambda = transform_params
    # First, collect all graphs for all layouts and nets
    graph_start = time.time()
    # Dictionary to store all data: layout_name -> net_name -> [graph_obj, root_node_id, rg]
    all_graph_data = {}
    total_permutations = 0
    total_nets = 0
    rgm = ResistanceGraphManager()
    all_pyg_data = []
    num_nanosheets = 3 if technology.lower() != 'cfet' else 4
    #net_names = get_available_nets(metrics_data)
    layer_map = ""
    for gds_file in gds_files:
        layout_name = Path(gds_file).stem
        gds_file = gds_file.replace('.gds','.json')
        # Get nets for this layout
        if isinstance(net_names, str):
            net_names = [net_names]
        # Create a single ResistanceGraph for the layout with optional parallel graph building
        try:
            polygon_processor = rgm.get_polygon_processor(gds_file,layer_map_dir)
            try:               
                nets_pyg_data = rgm.initialise_or_update_graph(gds_file, 
                                                           layer_properties_pdk, 
                                                           layer_map_dir, 
                                                           polygon_processor, 
                                                           dataset,
                                                           num_nanosheets)                
                all_pyg_data.extend(nets_pyg_data)
            except Exception as e:
                logger.error(f"Error creating nets_pyg_data for layout {layout_name}: {str(e)}")
                continue

    # Get the appropriate net graph from the graph dictionary
            rg = rgm.active_graph
            all_graph_data[layout_name] = {}
            # Extract graphs for each net
            for (layout_name, net_name, processed_data, root_node_id, graph_obj, gds_path) in nets_pyg_data:         
                normalized_net = normalize_name(net_name)                
                all_graph_data[layout_name][normalized_net] = (graph_obj, root_node_id, gds_file)
                total_nets += 1
            
            total_permutations += 1
        except Exception as e:
            logger.error(f"Error creating graph for layout {layout_name}: {str(e)}")
            continue
    
        graph_end = time.time()
        timing['graph_creation'] = graph_end - graph_start
        logger.info(f"Created graphs for {total_permutations} layouts with {total_nets} total nets in {timing['graph_creation']:.2f}s")
        
    if total_nets == 0:
        logger.warning("No valid nets found for batch processing")
        return {}
    
    # Convert all graphs to PyG data
    data_prep_start = time.time()
    #all_pyg_data = []  # List of (layout_name, net_name, pyg_data) tuples
    
   
    # Create a single batch from all graphs
    from torch_geometric.data import Batch
    all_processed_data = [item[2] for item in all_pyg_data]
    batched_data = Batch.from_data_list(all_processed_data)
  
    # Check for multi-GPU support
    if use_multi_gpu and torch.cuda.is_available() and torch.cuda.device_count() > 1:
        logger.info(f"Using multi-GPU with {torch.cuda.device_count()} GPUs")
        # Wrap model with DataParallelPassthrough to maintain attribute access
        model = DataParallelPassthrough(model)
        
    batched_data = batched_data.to(device)
    
    data_prep_end = time.time()
    timing['data_preparation'] = data_prep_end - data_prep_start
    
    # Single forward pass for ALL nets across ALL layouts
    inference_start = time.time()
    
    model.eval()
    # with torch.no_grad():
    #     # Ensure batch tensor is correctly set
    #     if batched_data.batch is None:
    #         batched_data.batch = torch.zeros(batched_data.x.size(0), dtype=torch.long, device=device)
            
    #     all_predictions = model(batched_data.x, batched_data.edge_index, 
    #                         batched_data.edge_attr, batched_data.batch)
    
    inference_end = time.time()
    timing['model_inference'] = inference_end - inference_start
    
    # Process predictions
    post_proc_start = time.time()
    
    # Dictionary to store all results: layout_name -> net_name -> results
    all_results = {}
    
    start_idx = 0
    for i, (layout_name, net_name, processed_data, root_node_id, graph_obj, gds_file) in enumerate(all_pyg_data):
        # Initialize nested dictionary if needed
        if layout_name not in all_results:
            all_results[layout_name] = {}
        
        if len(graph_obj.nodes()) > 1:
            # Get the edge count for this graph
            edge_count = processed_data.edge_index.size(1) // 2  # Divide by 2 because edges are bidirectional
            
            start_idx += edge_count*2
            edge_info = predict_resistances(model, processed_data, transform_mean, transform_std, transform_type, transform_lambda, device)
            
            # Calculate equivalent resistance
            eq_resistance = EquivalentResistance(graph_obj, edge_info, root_node_id).getResistance()
            
            
            # Store results
            all_results[layout_name][net_name] = {
                'edge_predictions': edge_info,
                'eq_resistance': eq_resistance,
                'gds_file': gds_file
            }
    
    post_proc_end = time.time()
    timing['post_processing'] = post_proc_end - post_proc_start
    
    # Log detailed timing
    total_time = sum(timing.values())
    logger.info(f"Supercharged batch processing breakdown for {total_permutations} layouts and {total_nets} nets:")
    logger.info(f"  Graph creation: {timing['graph_creation']:.2f}s ({timing['graph_creation']/total_time*100:.1f}%)")
    logger.info(f"  Data preparation: {timing['data_preparation']:.2f}s ({timing['data_preparation']/total_time*100:.1f}%)")
    logger.info(f"  Model inference: {timing['model_inference']:.2f}s ({timing['model_inference']/total_time*100:.1f}%)")
    logger.info(f"  Post-processing: {timing['post_processing']:.2f}s ({timing['post_processing']/total_time*100:.1f}%)")
    logger.info(f"  Total time: {total_time:.2f}s, Avg time per net: {total_time/total_nets:.4f}s")
    
    return all_results

def main(args):
     # Create tracking dictionaries for timing
    timing_stats = {
        'total_time': 0,
        'graph_creation_time': 0,
        'batch_processing_time': 0,
        'layouts_processed': 0,
        'nets_processed': 0
    }
    
    total_start_time = time.time()
    """Modified main function to work with sivista.py flow"""
    gds_dir = args.get('gds_dir')
    metrics_file = args.get('metrics_file')
    tech_file = load_tech_file(args.get('tech_file', 'tech/monCFET/monCFET.tech'))
    layer_properties_pdk = tech_file.layer_properties
    metrics_data = pd.read_csv(metrics_file)
    layer_map_dir = args.get('layer_map_dir')
    equivalent_resistance = defaultdict(dict)
    pex_file = args.get('pex_file')
    combine_resistance = args.get('combine_resistance')
    output_file = args.get('output_file')
    technology = tech_file.technology    
     # List all GDS files
    gds_files = list(Path(gds_dir).glob("*.gds"))
    gds_files = [str(path) for path in gds_files]
    use_multi_gpu = True
    max_workers = 10
    if use_multi_gpu and torch.cuda.is_available():
        logger.info(f"Using multi-GPU acceleration with {torch.cuda.device_count()} GPUs")
    if max_workers:
        logger.info(f"Using {max_workers} worker threads for parallel graph building")

    try:
        # Respect silent mode from args
        if args.get('silent', False):
            logger.setLevel(logging.WARNING)  # Only show warnings and errors
        else:
            logger.setLevel(logging.INFO)  # Show info but not debug
        # Get nets from the provided net_names list
        net_names = get_available_nets(metrics_data)
        print(f"net_names: {net_names}")
       
        device_args = "cuda" if torch.cuda.is_available() else "cpu"        
        #print(f"Processing layout {layout_name} with nets: {net_names}")
       
        
        if isinstance(net_names, str):
            net_names = [net_names]     
 
        device_args = "cuda" if torch.cuda.is_available() else "cpu"
        device = torch.device(device_args)
        
        # Log available devices
        available_devices = get_available_devices()
        logger.info(f"Available devices: {available_devices}")
        
        # Create dataset for inference
        dataset = ResistanceDataset(
            graphs_dir="dummy", 
            inference_mode=True,
            num_node_features=21,
            num_edge_features=9
        )
        
        # Load model and normalization parameters
        model, transform_mean, transform_std, transform_type, transform_lambda = load_trained_model(
            args['model_path'], 
            dataset, 
            device
        )
        
        transform_params = (transform_mean, transform_std, transform_type, transform_lambda)
        
        # Process all layouts at once with parallelization options
        all_results = batch_process_all_layouts(
            model=model,
            gds_files=gds_files,
            metrics_data=metrics_data,
            layer_properties_pdk=layer_properties_pdk,
            layer_map_dir=layer_map_dir,
            dataset=dataset,
            transform_params=transform_params,
            device=device,
            cell_name=args['cell_name'],
            use_multi_gpu=use_multi_gpu,  # Pass multi-GPU flag
            max_workers=max_workers , # Pass max workers parameter
            technology=technology,
            net_names=net_names
        )
        
        # Process results
        for layout_name, net_results in all_results.items():
            file_name = layout_name.replace('.gds', '')
            
            for net_name, result in net_results.items():
                # Store equivalent resistance
                equivalent_resistance[file_name][net_name] = result['eq_resistance']
                
                # Write predictions to log
                write_predictions_to_log(
                        layout_name=layout_name,
                        cell_name=args['cell_name'],
                        net_name=net_name,
                        gds_file=result['gds_file'],
                        edge_predictions=result['edge_predictions'],
                        eq_resistance=result['eq_resistance'],
                        output_dir=args['output_dir']
                    )
            
            timing_stats['layouts_processed'] += 1
            timing_stats['nets_processed'] += len(net_results)
        
        # Clean up CUDA memory
        if device_args == 'cuda':
            torch.cuda.empty_cache()
        elif device_args == "mps":
            torch.mps.empty_cache()
    except Exception as e:
        logger.error(f"Error during inference: {str(e)}")
        raise
    resistance_writer = ResistanceWriter(equivalent_resistance)
    resistance_writer.write_resistance_to_csv(output_file, pex_file, combine_resistance,"Res")

    # Merge resistance and capacitance predictions

if __name__ == '__main__':
    main()