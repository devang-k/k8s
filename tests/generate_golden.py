import json
import pandas as pd

import sys
from os import makedirs, listdir
import shutil
from os.path import join, isfile, exists, abspath, dirname
from pathlib import Path
sys.path.append(abspath(join(dirname(__file__), '..')))
import random
random.seed(43)
from stdcell_generation.processPermutations import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from utils.reader.gds_reader import GDSReader
from metrics_calculation.calculate_metrics import main as metrics_main
from fixtures.tech.default import tech_dic
from os import makedirs
from os.path import exists
import logging
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')
log_file = ".generate_golden"
setup_logging(log_file)
# Load the results DataFrame with min routing tracks for each configuration
# file_name = "min_routing_tracks_base0.csv"
# df = pd.read_csv(file_name)
pdk = "monCFET"
errors = []
def reset_directory(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

# Function to set the tech file with specific parameters
def set_tech_file(my_dict, config_name, backside_power_rail, number_of_routing_tracks,placer):
#add code for no_spacing
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
                if config_name in ['gaa','finfet']:
                    if key_values['key']['key1'] == 'routing_capability':
                        key_values['val'] = "Two Metal Solution"
                    if key_values['key']['key1'] == 'm0_pitch':
                        key_values['val'] = 30
                    if key_values['key']['key1'] == 'vertical_metal_pitch':
                        key_values['val'] = 30
                if config_name =='cfet':
                    if key_values['key']['key1'] == 'routing_capability':
                        key_values['val'] = "Single Metal Solution"
                    if key_values['key']['key1'] == 'm0_pitch':
                        key_values['val'] = 25
    return my_dict
# Load the base tech file

def prepare_tech(config_name, backside_power_rail, number_of_routing_tracks, placer):
    tech = tech_dic
    tech['technology'] = config_name
    tech['backside_power_rail'] = backside_power_rail
    tech['routing_capability'] = 'Single Metal Solution' if config_name == "cfet" else "Two Metal Solution"
    #print(f"type of number_of_routing_tracks{type(number_of_routing_tracks)}, number of routing tracks {number_of_routing_tracks}")
    tech['number_of_routing_tracks'] =int(number_of_routing_tracks)
    tech['placer'] = placer
    np_spacing_dict = {"4" : 40,
            "5": 40,
            "6":50,
            "7": 65,
            "8":75,
            "9":85,
            "10":90
        }

    

    tech['m0_pitch'] = 25 if config_name == 'cfet' else 30
    if config_name in ["gaa","finfet"]:
        tech['vertical_metal_pitch'] = tech['m0_pitch']
    tech['np_spacing'] = np_spacing_dict[str(number_of_routing_tracks)]

    return tech

with open('./fixtures/tech/techData.json', 'r') as f:
    base_tech_dict = json.load(f)

placer_algo = ["base0","base1"]
file_dict = {"base0":"min_routing_tracks_base0.csv" ,"base1": "min_routing_tracks_base1.csv"}
# Iterate over each cell in the DataFrame to apply configurations and generate layouts and permutations
#cfet,backside
routing_capability = ['Single Metal Solution','Two Metal Solution']
#for routing in routing_capability:
for placer in placer_algo:
    df = pd.read_csv(file_dict[placer])
    column_names = df.columns
    for i in range(len(column_names)):
        print(f"column i {i} is {column_names[i]}")


    for idx, row in df.iterrows():
        cell_name = row["Cell Name"]
        # Define the configurations
        configurations = [
            ("cfet", True, row[column_names[1]]),
            ("cfet", False, row[column_names[1]]),
            ("gaa", True, row[column_names[3]]),
            ("gaa", False, row[column_names[3]]),
            ("finfet", True, row[column_names[3]]),
            ("finfet", False, row[column_names[3]])
        ]
        golden_data_path = './golden_data/golden_new_all_cells'
        # Process each configuration
        #try
        for config_name, backside_power_rail, routing_tracks in configurations:
            if routing_tracks == "N/A":  # Skip if no `valid routing tracks are set
                continue
            #if config_name == 'cfet'
            # Modify tech file JSON based on configuration
            # tech_dict = set_tech_file(base_tech_dict, config_name, backside_power_rail, routing_tracks, placer)
            # tech_json_str = json.dumps(tech_dict)
            tech = prepare_tech(config_name, backside_power_rail, routing_tracks, placer)
            # cell_path = Path(cell)
            # reset_directory(cell_path) 
            # Set up arguments for generating layout
            layout_output_dir =  f'{golden_data_path}/{cell_name}/{config_name}_{backside_power_rail}_{placer}/'
            layout_args = {
                'tech': tech,
                'netlist': './fixtures/netlist/all_cells.spice',
                'output_dir':layout_output_dir,
                'cell': f'{cell_name}',
                'placer': 'base0',
                'signal_router': 'dijkstra',
                'debug_routing_graph': False,
                'debug_smt_solver': False,
                'quiet': True,
                'debug_plots': False
            }
            
            # Ensure the output directory exists
            if not exists(layout_args['output_dir']):
                makedirs(layout_args['output_dir'])
            

            # Generate layout for the current configuration
            print(f"Generating layout for {cell_name} with {routing_tracks} routing tracks, "
                f"technology = {config_name}, backside_power_rail = {backside_power_rail},placer {placer}")
            generate_layout_main(layout_args)
            if not exists(layout_output_dir):
                errors.append(f"Output directory {layout_output_dir} was not created for {cell_name} "
                        f"in config {config_name} with {routing_tracks} routing tracks, "
                        f"backside_power_rail = {backside_power_rail}, placer = {placer}.")
                raise FileNotFoundError(f"Output directory {layout_output_dir} was not created for {cell_name} "
                        f"in config {config_name} with {routing_tracks} routing tracks, "
                        f"backside_power_rail = {backside_power_rail}, placer = {placer}.")
            layout_files = [file for file in listdir(layout_output_dir) if file.endswith(".gds") and isfile(join(layout_output_dir,file))]
            if len(layout_files) == 0:
                raise FileNotFoundError(f"No GDS files created in {layout_output_dir}for {cell_name} in config {config_name} with {routing_tracks} routing tracks,{backside_power_rail} and placer {placer} .")

            permutation_output_dir = f'{golden_data_path}/{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations'
            # Set up arguments for generating permutations based on generated layout
            permutation_args = {
                                'tech': tech,
                                'netlist': './fixtures/netlist/all_cells.spice',
                                'cell': cell_name,
                                "gds_file":f"{golden_data_path}/{cell_name}/{config_name}_{backside_power_rail}_{placer}/", 
                                "output_dir": permutation_output_dir,
                                "limiter" : None, 
                                "debugger" : False,
                                "flow_type": "gds",
                                "onlyOne":True
                    }

            # Ensure the permutation output directory exists
            if not exists(permutation_args["output_dir"]):
                makedirs(permutation_args["output_dir"])
            
 
            # Generate permutations for the layout
            print(f"Generating permutations for {cell_name} with config {config_name}, "
                f"backside_power_rail = {backside_power_rail}, routing_tracks = {routing_tracks},placer :{placer}")
            pnr_main(permutation_args)

            print(f"Generating Metrics for {cell_name} with config {config_name}, "
                f"backside_power_rail = {backside_power_rail}, routing_tracks = {routing_tracks},placer :{placer}")
            permutation_args['input_path'] = permutation_args['output_dir']
            permutation_args["layermap_path"] = permutation_args['gds_file']
            metrics_main(permutation_args)

            gds_files = [f for f in listdir(permutation_output_dir) if f.endswith(".gds") and isfile(join(permutation_output_dir, f))]

            # Assert that GDS files were created for this configuration
            if len(gds_files) == 0:
                raise FileNotFoundError(f"No GDS files created in {permutation_output_dir}for {cell_name} in config {config_name} with {routing_tracks} routing tracks,{backside_power_rail} and placer {placer} .")
        # except Exception as e:
        #     error_message = f"Error for {cell_name} in config {config_name} (Backside Power Rail: {backside_power_rail}, Routing Tracks: {routing_tracks}): {e}"
        
        #     logger.error(error_message)
        #     errors.append(error_message)

# Display all errors at the end
if errors:
    print("\nErrors encountered during execution:")
    for error in errors:
        print(error)
else:
    print("Execution completed with no errors.")