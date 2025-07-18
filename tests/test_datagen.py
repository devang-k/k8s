import unittest
import json
import pandas as pd
import logging
import sys
import pya
from os import makedirs, listdir, devnull, system, getcwd
from os.path import join, isfile, exists, abspath, dirname, isdir
from pdf_writer import PDFWriter
from datetime import datetime
sys.path.append(abspath(join(dirname(__file__), '..')))
import random
random.seed(43)
from contextlib import redirect_stdout
from stdcell_generation_client.processPermutationsNew import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from metrics_calculation.calculate_metrics import main as metrics_main
from pex_extraction.dtco_ml_predict import main as pex_predict_main
from resistance_graph.inference_resistance_gnn import main as resistance_predict_main 
from shutil import rmtree
from utils.config import model_paths
from fixtures.tech.default import tech_dic
import itertools
from utils.logging_config import setup_logging
import pya

logger = logging.getLogger('sivista_app')
log_file = ".test_datagen"

def gds_xor( layout1, layout2, output_file):
        layer_to_check = [(104, 0), (105, 0), (100, 0), (101, 0), (102, 0), (122, 0), (121, 0), (103, 0), (106, 0), (107, 0), (111, 0), (111, 0), (123, 0), (108, 0), (109, 0), (300, 0),(300, 1),(300, 2),(300, 3), (1, 0), (110, 0), (200, 0), (200, 1),(200, 2), (200, 3), (202, 0),(202, 1), (220,0),  (221,0),  (201, 0)]
        new_layout = pya.Layout()
        new_layout.create_cell("TOP_CELL")
        new_layout.dbu = layout1.dbu
        dss = pya.DeepShapeStore()
        def region1(layer,datatype):
            return pya.Region(layout1.top_cell().begin_shapes_rec(layout1.layer(layer, datatype)), dss)
        def region2(layer,datatype):
            return pya.Region(layout2.top_cell().begin_shapes_rec(layout2.layer(layer, datatype)), dss)
        for li in layer_to_check:
            l,d = li
            r1 = layout1.top_cell().shapes(layout1.layer(l, d))
            r2 = layout2.top_cell().shapes(layout2.layer(l, d))
            text_elements = {}
            for shape in r1:
                if shape.is_text():
                    x, y, s = shape.text.position().x, shape.text.position().y, shape.text.string
                    text_elements[f'{x}_{y}_{s}'] = shape
            for shape in r2:
                if shape.is_text():
                    x, y, s = shape.text.position().x, shape.text.position().y, shape.text.string
                    st = f'{x}_{y}_{s}'
                    if st in text_elements:
                        del text_elements[st]
                    else:
                        text_elements[st] = shape
            for val in text_elements.values():
                new_layout.top_cell().shapes(new_layout.layer(l, d)).insert(val)
            new_layout.top_cell().shapes(new_layout.layer(l, d)).insert(region1(l,d)^region2(l,d))
        new_layout.write(output_file)
        layout1.write(output_file.replace('_diff.gds', '_generated.gds'))
        layout2.write(output_file.replace('_diff.gds', '_orig.gds'))
        return
# Function to compare GDS files using pya.LayoutDiff
def compare_gds(file1, file2, counter):
    diff = pya.LayoutDiff()
    layout1 = pya.Layout()
    layout1.read(file1)
    layout2 = pya.Layout()
    layout2.read(file2)
     # Check if the layouts are identical
    diff = diff.compare(layout1, layout2)
    if not diff:
        gds_xor(layout1, layout2, f'wrong_cells/{counter}_diff.gds')
    return diff

class LayoutGenerationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        setup_logging(log_file)

        cls.file_dict = {"base0":"min_routing_tracks_base0.csv" ,"base1":"min_routing_tracks_base1.csv"}
        files = ['min_routing_tracks_base1.csv','min_routing_tracks_base0.csv']
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

    def setUp(self) -> None:
        self.counter = 0
        makedirs('wrong_cells', exist_ok=True)
        self.pdf_writer = PDFWriter(title="Minimum routing tracks test", path="test_min_routing_permutation.pdf", date=datetime.now().strftime("%Y-%m-%d"))
    
    def set_tech_file(self,my_dict, config_name, backside_power_rail, number_of_routing_tracks,placer):
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
                    if config_name in ['gaa','finfet']:
                        if key_values['key']['key1'] == 'routing_capability':
                            key_values['val'] = "Two Metal Solution"
                        if key_values['key']['key1'] == 'm0_pitch':
                            key_values['val'] = 30
                    if key_values['key']['key1'] == 'placer':
                        key_values['val'] = placer
                    if config_name =='cfet':
                        if key_values['key']['key1'] == 'routing_capability':
                            key_values['val'] = "Single Metal Solution"
                        if key_values['key']['key1'] == 'm0_pitch':
                            key_values['val'] = 25
        return my_dict
    
    def prepare_tech(self,config_name, backside_power_rail, number_of_routing_tracks, placer):
        tech = tech_dic
        tech['technology'] = config_name
        tech['layer_properties'] = tech[f'layer_properties_{config_name}']
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
    
    def test_generate_layout_and_permutations(self):
        for placer in [ "base0","base1"]:
            self.df = pd.read_csv(self.file_dict[placer])
            column_names =self.df.columns    
            for idx, row in self.df.iterrows():
                cell_name = row["Cell Name"]
                configurations = [
                    ("cfet", True, row[column_names[1]]),
                    ("cfet", False, row[column_names[1]]),
                    ("gaa", True, row[column_names[3]]),
                    ("gaa", False, row[column_names[3]]),
                    ("finfet", True, row[column_names[3]]),
                    ("finfet", False, row[column_names[3]])
                ]
            
                for config_name, backside_power_rail, routing_tracks in configurations:
                    if routing_tracks == "N/A":
                        continue

                    try:
                        # Set up the tech dictionary for the current configuration
                        # tech_dict = self.set_tech_file(self.base_tech_dict, config_name, backside_power_rail, routing_tracks,placer)
                        # tech_json_str = json.dumps(tech_dict)
                        tech = self.prepare_tech(config_name,backside_power_rail,routing_tracks,placer)
                        #{cell_name}/{config_name}_{backside_power_rail}_{placer}/
                        # Define dynamic paths for layout and permutation output
                        layout_output_dir = f"{cell_name}/{config_name}_{backside_power_rail}_{placer}/"
                        permutation_output_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/"
                        layout_output_dir = abspath(layout_output_dir)
                        layout_args = {
                            'tech': tech,
                            'netlist': self.netlist_path,
                            'output_dir': f'{layout_output_dir}/',
                            'cell': cell_name,
                            'placer': 'base0',
                            'signal_router': 'dijkstra',
                            'debug_routing_graph': False,
                            'debug_smt_solver': False,
                            'quiet': True,
                            'debug_plots': False
                        }

                        if not exists(layout_output_dir):
                            makedirs(layout_output_dir)
                        
                        # Generate layout
                        generate_layout_main(layout_args)

                        # Define permutation arguments
                        permutation_args = {
                            'tech': tech,
                            'netlist': self.netlist_path,
                            "gds_file": layout_output_dir,
                            'cell': cell_name,
                            "output_dir": permutation_output_dir,
                            'cell': cell_name,
                            "limiter": None, 
                            "debugger": False,
                            "flow_type": "gds",
                            "onlyOne": True
                        }

                        if not exists(permutation_output_dir):
                            makedirs(permutation_output_dir)
                        
                        # Generate permutations
                        with open(devnull,'w') as f:
                            with redirect_stdout(f):
                                pnr_main(permutation_args)
                        #{golden_data_path}/{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations'
                    except Exception as e:
                        # Record the error and continue
                        error_message = f"Error for {cell_name} in config {config_name} (Backside Power Rail: {backside_power_rail}, Routing Tracks: {routing_tracks}): {str(e)}"
                        self.errors.append({'message': error_message, 'cell': cell_name})
                        logger.error(error_message)
    
    def test_pex_data_gen(self):
        placers = ["base0", "base1"]
        backside_power_rails = [True, False]
        technologies = ["cfet", "gaa", "finfet"]
        run_combinations = list(itertools.product(placers, backside_power_rails, technologies))
        routing_tracks = 5
        cell_name = "AOI21X1"
        limiter = 10

        for placer, backside_power_rail, config_name in run_combinations:
            tech = self.prepare_tech(config_name, backside_power_rail, routing_tracks, placer)
            layout_output_dir = f"pex_test/{cell_name}/{config_name}_{backside_power_rail}_{placer}/layouts/"
            permutation_output_dir = f"pex_test/{cell_name}/{config_name}_{backside_power_rail}_{placer}/permutations/"
            metrics_output_dir = f"pex_test/{cell_name}/{config_name}_{backside_power_rail}_{placer}/metrics/"
            pex_output_dir = f"pex_test/{cell_name}/{config_name}_{backside_power_rail}_{placer}/capacitance/"
            resistance_output_dir = f"pex_test/{cell_name}/{config_name}_{backside_power_rail}_{placer}/resistance/"
            layout_output_dir = abspath(layout_output_dir)

            layout_args = {
                'tech': tech,
                'netlist': self.netlist_path,
                'output_dir': f'{layout_output_dir}/',
                'cell': cell_name,
                'placer': 'base0',
                'signal_router': 'dijkstra',
                'debug_routing_graph': False,
                'debug_smt_solver': False,
                'quiet': True,
                'debug_plots': False
            }
            if not exists(layout_output_dir):
                makedirs(layout_output_dir)
            generate_layout_main(layout_args)

            permutation_args = {
                'tech': tech,
                'netlist': self.netlist_path,
                "gds_file": layout_output_dir,
                'cell': cell_name,
                "output_dir": permutation_output_dir,
                'cell': cell_name,
                "limiter": limiter, 
                "debugger": False,
                "flow_type": "gds"
            }
            if not exists(permutation_output_dir):
                makedirs(permutation_output_dir)
            with open(devnull,'w') as f:
                with redirect_stdout(f):
                    pnr_main(permutation_args)
            
            metrics_args = {
                "input_path": permutation_output_dir,
                "output_dir": metrics_output_dir,
                "tech": tech,
                "layermap_path": layout_output_dir,
                "cell": cell_name,
                "flow_type": "gds"
            }
            if not exists(metrics_output_dir):
                makedirs(metrics_output_dir)
            metrics_main(metrics_args)

            pex_args = {
                "input_path": f'{metrics_output_dir}/AOI21X1_metrics.csv',
                "output": f'{pex_output_dir}/AOI21X1_GDS_PEX_PREDICTION_ML.csv',
                "model":"gnn",
                "tech": tech,
                "data_results_format": "individual-net",
            }
            if not exists(pex_output_dir):
                makedirs(pex_output_dir)
            pex_predict_main(pex_args)

            config_name = "gaa" if config_name == "finfet" else config_name
            resistance_args = {
                "metrics_file": f'{metrics_output_dir}/AOI21X1_metrics.csv',
                "gds_dir": permutation_output_dir,
                "cell_name": cell_name,
                "model_path": model_paths["gnn"][config_name]["resistance_predictor_path"],
                "norm_path": model_paths["gnn"][config_name]["resistance_norm_params"],
                "tech_file": tech,
                "silent": True,
                "layer_map_dir": layout_output_dir,
                "output_dir": resistance_output_dir,
                "pex_file": f'{pex_output_dir}/{cell_name}_GDS_PEX_PREDICTION_ML.csv',
                "combine_resistance": False,
                "output_file": f'{resistance_output_dir}/{cell_name}_predicted_equivalent_resistance.csv',
            }
            if not exists(resistance_output_dir):
                makedirs(resistance_output_dir)
            resistance_predict_main(resistance_args)

if __name__ == '__main__':
    unittest.main()