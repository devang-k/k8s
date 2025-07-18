import unittest
import json
import pandas as pd
import logging
import sys
import pya
import os
from os import makedirs, listdir, devnull, system, getcwd
from os.path import join, isfile, exists, abspath, dirname, isdir
import json
import traceback
from datetime import datetime
sys.path.append(abspath(join(dirname(__file__), '..')))
import random
import glob
random.seed(43)
from contextlib import redirect_stdout
from pdf_writer import PDFWriter
from utils.reader.gds_reader import GDSReader
from stdcell_generation_client.processPermutationsNew import main as generate_layout_main
from pnr_permutations.generate_permutations import main as pnr_main
from shutil import rmtree
from utils.config import klayout_configs
from fixtures.tech.default import tech_dic
from shapely.geometry import Polygon, Point
import pya
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')
log_file = ".test_np_gap"

class LayoutGenerationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        setup_logging(log_file)
        cls.file_dict = {"base0":"min_routing_tracks_base0.csv" ,"base1":"min_routing_tracks_base1.csv"}#"hierarchical_test_1.csv"}#
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
        self.pdf_writer = PDFWriter(title="Minimum routing tracks test", path="test_np_gap.pdf", date=datetime.now().strftime("%Y-%m-%d"))
    
    def set_tech_file(self,my_dict, config_name, backside_power_rail, number_of_routing_tracks,placer,power_rail_type):
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
                        if key_values['key']['key1'] == 'vertical_metal_pitch':
                            key_values['val'] = 30
                    if key_values['key']['key1'] == 'placer':
                        key_values['val'] = placer
                    if config_name =='cfet':
                        if key_values['key']['key1'] == 'routing_capability':
                            key_values['val'] = "Single Metal Solution"
                        if key_values['key']['key1'] == 'm0_pitch':
                            key_values['val'] = 25
                    if power_rail_type=="topside":
                        if key_values['key']['key1'] == 'power_rail_type':
                             key_values['val'] = "topside"

        return my_dict
    
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

    def test_nanosheet_gap(self):
        for placer in [ "base0","base1"]:
            self.df = pd.read_csv(self.file_dict[placer])
            # Print the exact column names to check for hidden spaces or characters
            column_names = self.df.columns
       
            for idx, row in self.df.iterrows():
                cell_name = row["Cell Name"]
                # Define configurations to test directly from the CSV
                cell_name = row["Cell Name"]
                columns =self.df.columns
                configurations = [
                    #("cfet", True, row[columns[1]]),
                    ("gaa", True, row[columns[3]]),
                    ("gaa", False, row[columns[3]]),
                    ("finfet", True, row[columns[3]]),
                    ("finfet", False, row[columns[3]])
                ]
                try:
                    for config_name, backside_power_rail, routing_tracks in configurations:
                        if routing_tracks == "NA":
                            continue
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
                        
                        # #Generate layout
                        # with open(os.devnull, 'w') as f:
                        #     with redirect_stdout(f):
                        #         generate_layout_main(layout_args)
                        gdsJson = self.read_gds(layout_output_dir)
            
                        # Check the polygons for the layout
                        json_dir = f"{cell_name}/{config_name}_{backside_power_rail}_{placer}/"
                        self.check_nanosheet_gap(config_name,gdsJson,cell_name,tech['scaling_factor'],routing_tracks)
                        #permutation_output_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/"
                        permutation_output_dir = f"{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/"
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
                        #     # Generate permutations
                        # with open(devnull,'w') as f:
                        #     with redirect_stdout(f):
                        #         pnr_main(permutation_args)

                        permutation_files = [name for name in listdir(permutation_output_dir) if isfile(join(permutation_output_dir, name)) and name.endswith('.gds')]
                        gds_reader = GDSReader()
                        for file in permutation_files:
                            print(f"permutation file {file}")
                            gdsJson = gds_reader.read(join(permutation_output_dir, file))
                            self.check_nanosheet_gap(config_name,gdsJson,cell_name,tech['scaling_factor'],routing_tracks)
                except Exception as e:
                    # Record the error and continue
                    error_message = f"Error for {cell_name} in config {config_name} ( {backside_power_rail}, Routing Tracks: {routing_tracks}): {str(e)}"
                    self.errors.append({'message': error_message, 'cell': cell_name})
                    print(traceback.format_exc())
                    #logger.error(error_message)

        #Assert no errors were recorded
        error_cells = []
        for error in self.errors:
            error_cells.append(error['cell'])
            #print(error['message'])
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
    
    def read_gds_file(self,input_path):
        #print(f"input path {input_path}")
        if os.path.isdir(input_path):
        # If it's a directory, pick the first .gds file found (if any).
            matched_files = glob.glob(os.path.join(input_path, "*.gds"))
            #print(f"matched_files {matched_files}")
            if matched_files:
                return matched_files[0]  # Return the first file
            else:
                return None 

    def process_polygon_coordinates(self,xy_list):  
        return xy_list
        return [(xy_list[i] , xy_list[i + 1] ) for i in range(0, len(xy_list), 2)]      

    def read_gds(self,layout_output_dir):
        gds_reader = GDSReader()
        file_path = self.read_gds_file(layout_output_dir)
        #print(f"file_path {file_path}")
        try:
            gdsJson = gds_reader.read(file_path)
            #print(f"{gdsJson}")
        except Exception as e:
            print(e)
            logger.error(f"{e}")
        return gdsJson
                        
    def load_json(self,layout_output_dir):
        file_path = self.read_gds_file(layout_output_dir)
        file_path = file_path.replace(".gds", ".json")
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data

    def check_nanosheet_gap(self,config_name,gdsJson,cell_name,scaling_factor,routing_track):
        # units = gdsJson.get("bgnlib", [{}])[0].get("units", [1.0])[0]  # Fetching scaling unit
        elements = gdsJson['structures'][0]['elements']
        n_nanosheet = []
        p_nanosheet = []
        for element in elements:
            if element['layer'] == 100 and element['element']=='boundary' and element['datatype']==0:
                logger.debug(f"elelent xy for n nanaosheet {element['xy']}")
                polygon = Polygon(self.process_polygon_coordinates(element['xy']))
                n_nanosheet.append(polygon)
                logger.debug(f"n_naosheet polygon {polygon}")
            if element['layer'] == 101 and element['element']=='boundary' and element['datatype']==0:
                polygon = Polygon(self.process_polygon_coordinates(element['xy']))
                p_nanosheet.append(polygon)
                logger.debug(f"p_naosheet polygon {polygon}")
        logger.debug(f"p_nanosheet {p_nanosheet}")
        logger.debug(f"n nanosheet {n_nanosheet}")
        n_nanosheet = n_nanosheet[0]
        p_nanosheet = p_nanosheet[0]
        logger.debug(f"n nanpsheet bounds {n_nanosheet.bounds}")
        logger.debug(f"p_nanosheet bounds {p_nanosheet.bounds}")       
        _,nmos_y_bottom,_,nmos_y_top = n_nanosheet.bounds
        _,pmos_y_bottom,_,pmos_y_top = p_nanosheet.bounds
        if config_name in ['gaa', 'finfet']:
            # Check the flipped condition and validate gap
            # if flipped!="R0":
            #     # Check that PMOS is at the bottom (its top should be below NMOS bottom)
            #     if pmos_y_top >= nmos_y_bottom:
            #         self.errors.append(f"PMOS is not above NMOS when flipped. PMOS Y top: {pmos_y_top}, NMOS Y bottom: {nmos_y_bottom}")
            #         self.fail(f"PMOS is not above NMOS when flipped. PMOS Y top: {pmos_y_top}, NMOS Y bottom: {nmos_y_bottom}")
            #     # Ensure the gap between them is at least 50
            #     if nmos_y_bottom - pmos_y_top !=50:
            #         self.fail(f"The gap between PMOS and NMOS is less than 50. Gap: {nmos_y_top - pmos_y_bottom}")
            # else:
                # If not flipped: PMOS should be at the top and NMOS should be at the bottom
                # Check that PMOS is at the top (its bottom should be above NMOS top)
            if nmos_y_top >= pmos_y_bottom:
                message = f"PMOS is not above NMOS. PMOS Y top: {pmos_y_top}, NMOS Y bottom: {nmos_y_bottom}"
                self.errors.append({"message":message,"cell":cell_name})
                #self.fail(f"PMOS is not above NMOS when flipped is False. NMOS Y top: {nmos_y_top}, PMOS Y bottom: {pmos_y_bottom}")
            # Ensure the gap between them is at least 50
                
            ideal_gap = self.np_spacing_dict[str(routing_track)]*scaling_factor
            if pmos_y_bottom - nmos_y_top != (ideal_gap):
                self.errors.append({"message":f" PMOS Y bottom: {pmos_y_bottom}, NMOS Y top: {nmos_y_top}. Gap: {pmos_y_bottom - nmos_y_top},ideal gap shoul dbe {ideal_gap},routing_tracks {routing_track}","cell":cell_name})
                #self.fail(f"The gap between NMOS and PMOS is less than 50. Gap: {pmos_y_bottom - nmos_y_top}")
        else:
            #nanosheet top and bottom y should be the same for CFET
            if nmos_y_bottom == pmos_y_bottom and nmos_y_top == pmos_y_top:
                logger.debug(f"nmos and pmos y's have the same values...")
            else:
                self.errors.append({"message":f"nmos and pmos dont have the same y values for CFET","cell":cell_name})

if __name__ == '__main__':
    unittest.main()
     
""" 
PDF saved successfully to test_min_routing_permutation.pdf
Error for OAI22X1 in config cfet ( True, Routing Tracks: 5): local variable 'gdsJson' referenced before assignment OAI22X1
Error for OAI22X1 in config cfet ( True, Routing Tracks: 5): local variable 'gdsJson' referenced before assignment OAI22X1
"""