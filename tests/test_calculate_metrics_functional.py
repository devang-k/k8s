import unittest
import json
import pandas as pd
import logging
import sys
import pya
import os
from os import makedirs, listdir, devnull, system, getcwd
from os.path import join, isfile, exists, abspath, dirname, isdir
import pandas.testing as pdt
from datetime import datetime
sys.path.append(abspath(join(dirname(__file__), '..')))
import random
import glob
random.seed(43)
from contextlib import redirect_stdout
from pdf_writer import PDFWriter
from utils.writer.gds_writer import GDSWriter
from stdcell_generation_client.processPermutationsNew import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from metrics_calculation.calculate_metrics import main as calculate_metrics_main
from shutil import rmtree
from utils.config import klayout_configs
from fixtures.tech.default import tech_dic
from shapely.geometry import Polygon, Point
import pya
from stdcell_generation_client.layout.layer_stack import *
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')
log_file = ".test_pg_signal"

class LayoutGenerationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        setup_logging(log_file)
        cls.file_dict = {"base0":"min_routing_tracks_base0.csv" ,"base1":"min_routing_tracks_base1.csv"}
        # Load the results DataFrame with min routing tracks for each configuration
        cls.df = pd.read_csv("min_routing_tracks_base0.csv")
        # Load the base tech file JSON
        with open('./fixtures/tech/techData.json', 'r') as f:
            cls.base_tech_dict = json.load(f)
        cls.pdk = "monCFET"
        cls.netlist_path = abspath('fixtures/netlist/all_cells.spice')#abspath(join(dirname(__file__), 'fixtures/netlist/all_cells.spice'))
        # Updated base golden data pat
        cls.golden_data_base ='./golden_data/golden_new_all_cells' #abspath(join(dirname(__file__), 'golden_data/golden_new_all_cells'))
        cls.errors = []  # Store errors here
        cls.np_spacing_dict = {"4" : 40,
            "5": 40,
            "6":50,
            "7": 65,
            "8":75,
            "9":85,
            "10":90
        }

    def setUp(self) -> None:
        self.counter = 0
        makedirs('wrong_cells', exist_ok=True)
        self.pdf_writer = PDFWriter(title="Minimum routing tracks test", path="test_backside_power.pdf", date=datetime.now().strftime("%Y-%m-%d"))
           
    def prepare_tech(self,config_name, backside_power_rail, number_of_routing_tracks, placer):
        tech = tech_dic
        tech['technology'] = config_name
        tech['backside_power_rail'] = backside_power_rail
        tech['routing_capability'] = 'Single Metal Solution' if config_name == "cfet" else "Two Metal Solution"
        #print(f"type of number_of_routing_tracks{type(number_of_routing_tracks)}, number of routing tracks {number_of_routing_tracks}")
        tech['number_of_routing_tracks'] =int(number_of_routing_tracks)
        tech['placer'] = placer
        tech['m0_pitch'] = 25 if config_name == 'cfet' else 30
        if config_name in ["gaa", "finfet"]:
            tech['vertical_metal_pitch'] = tech['m0_pitch']
        tech['np_spacing'] = self.np_spacing_dict[str(number_of_routing_tracks)]
        return tech

    def test_calculate_metrics(self):
        for placer in [ "base0","base1"]:
            self.df = pd.read_csv(self.file_dict[placer])
            # Print the exact column names to check for hidden spaces or characters
            column_names = self.df.columns
            for idx, row in self.df.iterrows():
                cell_name = row["Cell Name"]
                # Define configurations to test directly from the CSV
                cell_name = row["Cell Name"]
                # Define configurations to test directly from the CSV
                configurations = [
                ("cfet", True, row[column_names[1]]),
                ("cfet", False, row[column_names[1]]),
                ("gaa", True, row[column_names[3]]),
                ("gaa", False, row[column_names[3]]),
                ("finfet", True, row[column_names[3]]),
                ("finfet", False, row[column_names[3]]),
                ]
                try:
                    for config_name, backside_power_rail, routing_tracks in configurations:
                        if routing_tracks == "NA":
                            continue
                        # Prepare the tech dictionary for the current configuration
               
                        tech = self.prepare_tech(config_name, backside_power_rail, routing_tracks, placer)                   
                        # Define dynamic paths for layout and permutation output
                        layout_output_dir = f"{cell_name}/{config_name}_{backside_power_rail}_{placer}/"
                        layout_output_dir = abspath(layout_output_dir)
                        layout_args = {
                            'tech': tech,
                            'netlist':self.netlist_path,
                            'output_dir': f'{layout_output_dir}/',
                            'cell': cell_name,
                            'placer': 'base0',
                            'signal_router': 'dijkstra',
                            'debug_routing_graph': False,
                            'debug_smt_solver': False,
                            'quiet': True,
                            'debug_plots': False
                        }
                        # if not exists(layout_output_dir):
                        #     makedirs(layout_output_dir)
                        
                        #Generate layout
                        # with open(os.devnull, 'w') as f:
                        #     with redirect_stdout(f):
                        #         generate_layout_main(layout_args)
                            
                
                        permutation_output_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/"

                    # Define permutation arguments
                        permutation_args = {
                            'tech': tech,
                            'netlist': self.netlist_path,
                            "gds_file": layout_output_dir,
                            'cell': cell_name,
                            "output_dir": permutation_output_dir,
                            'netlist': self.netlist_path,
                            'cell': cell_name,
                            "limiter": None, 
                            "debugger": False,
                            "flow_type": "gds",
                            "onlyOne": True
                        }
                        # if not exists(permutation_output_dir):
                        #     makedirs(permutation_output_dir)
                        # Generate permutations
                        # with open(devnull,'w') as f:
                        #     with redirect_stdout(f):
                        #         pnr_main(permutation_args)
                        permutation_files = [name for name in listdir(permutation_output_dir) if isfile(join(permutation_output_dir, name)) and name.endswith('.gds')]
                        gds_writer = GDSWriter()
                        golden_capacitance_dir =f'{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_metrics'
                        capacitance_input_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations"
                        capacitance_output_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_metrics"
                        calculate_metrics_args = {
                        "input_path": capacitance_input_dir,
                        "output_dir": capacitance_output_dir,
                        "tech":tech,
                        "layermap_path": f"{cell_name}/{config_name}_{backside_power_rail}_{placer}",
                        "cell": cell_name,
                        "flow_type":"gds"
                        }
                        calculate_metrics_main(calculate_metrics_args)
                        generated_csv_path = join(capacitance_output_dir,f"{cell_name}_metrics.csv")
                        golden_csv_path = join(golden_capacitance_dir,f"{cell_name}_metrics.csv")
                        self.compare_csv_files(generated_csv_path, golden_csv_path, cell_name)
                except Exception as e:
                    # Record the error and continue
                    error_message = f"Error for {cell_name} in config {config_name} ,{backside_power_rail}, Routing Tracks: {routing_tracks}: {e}"
                    self.errors.append({'message': error_message, 'cell': cell_name})
        # Assert no errors were recorded
        error_cells = []
        for error in self.errors:
            error_cells.append(error['cell'])
            print(error['message'])
        cwd = getcwd()
        system(f"'{klayout_configs['path']}' -z -r {cwd}/../utils/thumbnail/thumbnail.py -rd layer_properties='{cwd}/../{klayout_configs['layerproperties']}' -rd gds_folder='wrong_cells/'")
        mismatched_images = [name for name in listdir('wrong_cells/') if isfile(join('wrong_cells/', name)) and name.endswith('.png')]
        mismatched_images = list({'_'.join(name.split('_')[:-1]) for name in mismatched_images})
        print('-----------------------------------',mismatched_images)
        for mi in mismatched_images:
            self.pdf_writer.append("text", f"{mi}:")
            self.pdf_writer.append("images", {
                'Generated image': f'wrong_cells/{mi}_generated.png',
                'Golden data': f'wrong_cells/{mi}_orig.png',
                'Difference': f'wrong_cells/{mi}_diff.png',
            })
        print('------------------------------------------before saving')
        self.pdf_writer.save()
        rmtree('wrong_cells/')
        for e in self.errors:
            print(e["message"], e['cell'])
        self.assertEqual(len(self.errors), 0, f"Errors encountered during test:\n")

    def compare_csv_files(self, generated_csv_path, golden_csv_path,cell_name):
        """Compares the generated CSV with the golden CSV for exact matches."""
        try:
            logger.debug(f"Comparing CSV files:\nGenerated: {generated_csv_path}\nGolden: {golden_csv_path}")
            generated_df = pd.read_csv(generated_csv_path)
            golden_df = pd.read_csv(golden_csv_path)

            # Sort and reset index for alignment
            generated_df.sort_values(by=generated_df.columns.tolist(), inplace=True)
            golden_df.sort_values(by=golden_df.columns.tolist(), inplace=True)
            generated_df.reset_index(drop=True, inplace=True)
            golden_df.reset_index(drop=True, inplace=True)

            # Assert DataFrames are equal
            pdt.assert_frame_equal(golden_df, generated_df, check_like=True)
            logger.debug("CSV files match exactly.")
        except AssertionError as e:
            logger.error(f"CSV comparison failed:\n{e}")
            self.errors.append({"message":f"CSV files left generated{generated_csv_path},golden{golden_csv_path} don't match ,error : {e}","cell":cell_name})
            raise
    

if __name__ == '__main__':
    unittest.main()