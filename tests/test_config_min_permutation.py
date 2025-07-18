import unittest
import json
import pandas as pd
import os
import logging
import sys
from os import makedirs, listdir
from os.path import join, isfile, exists, abspath, dirname
sys.path.append(abspath(join(dirname(__file__), '..')))
from stdcell_generation.processPermutations import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')
log_file = ".test_automate"

class LayoutGenerationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        setup_logging(log_file)
        
        # Load the results DataFrame with min routing tracks for each configuration
        cls.df = pd.read_csv("min_routing_tracks1.csv")
        
        # Load the base tech file JSON
        with open('./fixtures/tech/techData.json', 'r') as f:
            cls.base_tech_dict = json.load(f)
        
        cls.pdk = "monCFET"
        cls.netlist_path =  './fixtures/netlist/all_cells.spice'
        cls.errors = []  # Store errors here

    def set_tech_file(self, my_dict, config_name, backside_power_rail, number_of_routing_tracks):
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
        return my_dict
    
    def test_generate_layout_and_permutations(self):
        for idx, row in self.df.iterrows():
            cell_name = row["Cell Name"]
            
            # Define configurations to test
            configurations = [
                ("cfet", True, row["CFET (Backside Power Rail = True)"]),
                ("gaa", True, row["GAA (Backside Power Rail = True)"]),
                ("gaa", False, row["GAA (Backside Power Rail = False)"])
            ]
            
            for config_name, backside_power_rail, routing_tracks in configurations:
                if routing_tracks == "N/A":
                    continue  # Skip if no valid routing tracks value

                try:
                    # Set up the tech dictionary for the current configuration
                    tech_dict = self.set_tech_file(self.base_tech_dict, config_name, backside_power_rail, routing_tracks)
                    tech_json_str = json.dumps(tech_dict)
                    
                    # Define layout arguments
                    layout_args = {
                        'tech': tech_json_str,
                        'netlist': self.netlist_path,
                        'output_dir': f'{cell_name}/{config_name}_{backside_power_rail}/',
                        'cell': cell_name,
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
                    
                    # Generate layout
                    generate_layout_main(layout_args)
                    
                    # Define permutation arguments
                    permutation_output_dir = f'{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_permutations'
                    permutation_args = {
                        "gds_file": f"{layout_args['output_dir']}",
                        "output_dir": permutation_output_dir,
                        "limiter": None, 
                        "debugger": False,
                        "flow_type": "gds",
                        "onlyOne": True
                    }

                    # Ensure the permutation output directory exists
                    if not exists(permutation_output_dir):
                        makedirs(permutation_output_dir)
                    
                    # Generate permutations
                    pnr_main(permutation_args)

                    # Check for GDS files in the permutation output directory
                    gds_files = [f for f in listdir(permutation_output_dir) if f.endswith(".gds") and isfile(join(permutation_output_dir, f))]
                    
                    # Assert that GDS files were created for this configuration
                    if len(gds_files) == 0:
                        raise FileNotFoundError(f"No GDS files found for {cell_name} in config {config_name} with {routing_tracks} routing tracks.")

                except Exception as e:
                    # Record the error and continue
                    error_message = f"Error for {cell_name} in config {config_name} (Backside Power Rail: {backside_power_rail}, Routing Tracks: {routing_tracks}): {str(e)}"
                    self.errors.append(error_message)
                    logger.error(error_message)

        # Assert no errors were recorded
        self.assertEqual(len(self.errors), 0, f"Errors encountered during test:\n" + "\n".join(self.errors))

if __name__ == '__main__':
    unittest.main()
