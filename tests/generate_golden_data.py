import argparse
import json
import pandas as pd
import sys
from os import makedirs, listdir
import shutil
from os.path import join, isfile, exists, abspath, dirname
from pathlib import Path
sys.path.append(abspath(join(dirname(__file__), '..')))
from os import makedirs, listdir
import shutil
from os.path import join, isfile, exists, abspath, dirname
from pathlib import Path
import logging
from stdcell_generation.processPermutations import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')

# Function to parse boolean arguments
def str_to_bool(value):
    """
    Converts a string to a boolean value.

    Args:
        value (str): A string representing a boolean value ('true', 'false', 'yes', 'no', etc.).
    
    Returns:
        bool: The corresponding boolean value.

    Raises:
        argparse.ArgumentTypeError: If the input is not a valid boolean string.
    """
    if isinstance(value, bool):  # Pass through if already boolean
        return value
    if value.lower() in {'true', '1', 'yes'}:  # Handle True-like strings
        return True
    elif value.lower() in {'false', '0', 'no'}:  # Handle False-like strings
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got {value}")

# Function to reset a directory
def reset_directory(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

# Function to set up the tech file
def set_tech_file(my_dict, config_name, backside_power_rail, number_of_routing_tracks, placer):
    for file_content in my_dict['FileContent']:
        if file_content["name"] == "other":
            data = file_content["data"]
            for key_values in data:
                if key_values['key']['key1'] == 'number_of_routing_tracks':
                    key_values['val'] = number_of_routing_tracks
                if key_values['key']['key1'] == 'technology':
                    key_values['val'] = config_name
                if key_values['key']['key1'] == 'backside_power_rail':
                    key_values['val'] = backside_power_rail
                if key_values['key']['key1'] == 'placer':
                    key_values['val'] = placer
                if config_name == 'gaa':
                    if key_values['key']['key1'] == 'routing_capability':
                        key_values['val'] = "Two Metal Solution"
                    if key_values['key']['key1'] == 'm0_pitch':
                        key_values['val'] = 30
                if config_name == 'cfet':
                    if key_values['key']['key1'] == 'routing_capability':
                        key_values['val'] = "Single Metal Solution"
                    if key_values['key']['key1'] == 'm0_pitch':
                        key_values['val'] = 25
    return my_dict

# Function to process a single cell
def process_cell(cell_name, config_name, backside_power_rail, routing_tracks, placer, golden_data_path, base_tech_dict, errors, logger):
    try:
        if routing_tracks == "N/A":
            return

        # Modify tech file JSON based on configuration
        tech_dict = set_tech_file(base_tech_dict, config_name, backside_power_rail, routing_tracks, placer)
        tech_json_str = json.dumps(tech_dict)

        layout_output_dir = f'{golden_data_path}/{cell_name}/{config_name}_{backside_power_rail}_{placer}/'
        layout_args = {
            'tech': tech_json_str,
            'netlist': './fixtures/netlist/all_cells.spice',
            'output_dir': layout_output_dir,
            'cell': f'{cell_name}',
            'placer': placer,
            'signal_router': 'dijkstra',
            'debug_routing_graph': False,
            'debug_smt_solver': False,
            'quiet': True,
            'debug_plots': False
        }

        if not exists(layout_args['output_dir']):
            makedirs(layout_args['output_dir'])

        print(f"Generating layout for {cell_name} with {routing_tracks} routing tracks, "
              f"technology = {config_name}, backside_power_rail = {backside_power_rail}, placer = {placer}")
        generate_layout_main(layout_args)

        if not exists(layout_output_dir):
            raise FileNotFoundError(f"Output directory {layout_output_dir} was not created for {cell_name}")

        permutation_output_dir = f'{golden_data_path}/{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations'
        permutation_args = {
            "gds_file": layout_output_dir,
            "output_dir": permutation_output_dir,
            "limiter": None,
            "debugger": False,
            "flow_type": "gds",
            "onlyOne": True
        }

        if not exists(permutation_args["output_dir"]):
            makedirs(permutation_args["output_dir"])

        print(f"Generating permutations for {cell_name} with config {config_name}, "
              f"backside_power_rail = {backside_power_rail}, routing_tracks = {routing_tracks}, placer = {placer}")
        pnr_main(permutation_args)

        gds_files = [f for f in listdir(permutation_output_dir) if f.endswith(".gds") and isfile(join(permutation_output_dir, f))]
        if len(gds_files) == 0:
            raise FileNotFoundError(f"No GDS files created in {permutation_output_dir} for {cell_name}")
    except Exception as e:
        error_message = f"Error for {cell_name} in config {config_name} (Backside Power Rail: {backside_power_rail}, Routing Tracks: {routing_tracks}): {str(e)}"
        logger.error(error_message)
        errors.append(error_message)

def main():
    # Command-line argument parser
    parser = argparse.ArgumentParser(description="Golden Data Generation Script")
    parser.add_argument("--cell", type=str, help="Cell name to process")
    parser.add_argument("--config", type=str, choices=["cfet", "gaa"], help="Configuration type")
    parser.add_argument("--backside_power_rail", type=str_to_bool, help="Backside power rail (True/False)")
    parser.add_argument("--routing_tracks", type=int, help="Number of routing tracks")
    
    args = parser.parse_args()

    # Logging setup
    log_file = ".test_automate"
    setup_logging(log_file)

    # Base tech file
    with open('./fixtures/tech/techData.json', 'r') as f:
        base_tech_dict = json.load(f)

    # Constants
    placer_algo = ["base0", "base1"]
    file_dict = {"base0": "min_routing_tracks_base0.csv", "base1": "min_routing_tracks_base1.csv"}
    errors = []
    golden_data_path = './golden_data/golden_new_all_cells'

    if args.cell:
        # Single cell mode
        if not (args.config and args.backside_power_rail is not None and args.routing_tracks):
            raise ValueError("For single cell processing, --config, --backside_power_rail, and --routing_tracks must be specified.")
        for placer in placer_algo:
            process_cell(args.cell, args.config, args.backside_power_rail, args.routing_tracks, placer, golden_data_path, base_tech_dict, errors, logger)
    else:
        # Default mode for all cells
        for placer in placer_algo:
            df = pd.read_csv(file_dict[placer])
            for idx, row in df.iterrows():
                cell_name = row["Cell Name"]
                configurations = [
                    ("cfet", True, row["CFET (Backside Power Rail = True)"]),
                    ("gaa", True, row["GAA (Backside Power Rail = True)"]),
                    ("gaa", False, row["GAA (Backside Power Rail = False)"])
                ]
                for config_name, backside_power_rail, routing_tracks in configurations:
                    process_cell(cell_name, config_name, backside_power_rail, routing_tracks, placer, golden_data_path, base_tech_dict, errors, logger)

    if errors:
        print("\nErrors encountered during execution:")
        for error in errors:
            print(error)
    else:
        print("Execution completed with no errors.")

if __name__ == "__main__":
    main()
