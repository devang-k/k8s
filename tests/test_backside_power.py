import unittest
import json
import pandas as pd
import logging
import sys
import pya
import os
from os import makedirs, listdir, devnull, system, getcwd
from os.path import join, isfile, exists, abspath, dirname, isdir
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
from stdcell_generation_client.layout.layer_stack import *
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')

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

log_file = ".test_backside_power"

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

    def setUp(self) -> None:
        self.counter = 0
        makedirs('wrong_cells', exist_ok=True)
        self.pdf_writer = PDFWriter(title="Minimum routing tracks test", path="test_backside_power.pdf", date=datetime.now().strftime("%Y-%m-%d"))
    
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
                    if config_name in ['gaa', 'finfet']:
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
        np_spacing_dict = {"4" : 40,
            "5": 40,
            "6":50,
            "7": 65,
            "8":75,
            "9":85,
            "10":90
        }
        tech['m0_pitch'] = 25 if config_name == 'cfet' else 30
        if config_name in ["gaa", "finfet"]:
            tech['vertical_metal_pitch'] = tech['m0_pitch']
        tech['np_spacing'] = np_spacing_dict[str(number_of_routing_tracks)]
        return tech

    def test_generate_layout(self):
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
                ("finfet", False, row[column_names[3]])
                ]
                #try:
                for config_name, backside_power_rail, routing_tracks in configurations:
                    if routing_tracks == "NA":
                        continue
                    # Prepare the tech dictionary for the current configuration
                    # tech_dict = self.set_tech_file(self.base_tech_dict, config_name, backside_power_rail, routing_tracks,placer,power_rail_type)
                    # tech_json_str = json.dumps(tech_dict)
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
                        
                    #gdsJson = self.load_json(layout_output_dir)#needs code to be executed before.
                    gdsJson = self.read_gds(layout_output_dir)
                    # Check the polygons for the layout
                    json_dir = f"{cell_name}/{config_name}_{backside_power_rail}_{placer}/"
                    self.check_polygons_backside(backside_power_rail,gdsJson,cell_name)
                        #{golden_data_path}/{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations'
                        # Set up paths for golden data comparison
                    golden_layout_path = join(self.golden_data_base, cell_name, f"{config_name}_{backside_power_rail}_{placer}/")
                    #layout_output_dir =  f'{golden_data_path}/{cell_name}/{config_name}_{backside_power_rail}_{placer}/'
                    #golden_permutations_path = join(self.golden_data_base, cell_name, f"{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/")
                    files = [file for file in listdir(layout_output_dir) if file.endswith(".gds")]
    
                            # print(f"comparing gds {generated_file_path} with {golden_file_path}")
                            # if not compare_gds(generated_file_path, golden_file_path, f'{config_name}_{backside_power_rail}_{routing_tracks}_{placer}_lay_{file.replace(".gds", "")}'):
                            #     # print(f"gds mismatch")
                        #       raise AssertionError(f"Layout GDS mismatch for {cell_name} in {file},{generated_file_path},golden :{golden_file_path}")

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
                    
                    # # Generate permutations
                    # with open(devnull,'w') as f:
                    #     with redirect_stdout(f):
                    #         pnr_main(permutation_args)

                    permutation_files = [name for name in listdir(permutation_output_dir) if isfile(join(permutation_output_dir, name)) and name.endswith('.gds')]
                    gds_reader = GDSReader()
                    for file in permutation_files:
                        print(f"permutation file {file}")
                        gdsJson = gds_reader.read(join(permutation_output_dir, file))
                        self.check_polygons_backside(backside_power_rail,gdsJson,cell_name)
                # except Exception as e:
                #     # Record the error and continue
                #     error_message = f"Error for {cell_name} in config {config_name} ,{backside_power_rail}, Routing Tracks: {routing_tracks}: {e}"
                #     self.errors.append({'message': error_message, 'cell': cell_name})
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
        # for e in self.errors:
        #     #print(e["message"], e['cell'])
        self.assertEqual(len(self.errors), 0, f"Errors encountered during test:\n")

    def load_json(self,layout_output_dir):
        file_path = self.read_gds_file_path(layout_output_dir)
        file_path = file_path.replace(".gds", ".json")
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    
    
    def read_gds_file_path(self,input_path):
        #print(f"input path {input_path}")
        if os.path.isdir(input_path):
        # If it's a directory, pick the first .gds file found (if any).
            matched_files = glob.glob(os.path.join(input_path, "*.gds"))
            #print(f"matched_files {matched_files}")
            if matched_files:
                return matched_files[0]  # Return the first file
            else:
                return None 
    
    def read_gds(self,layout_output_dir):
        gds_reader = GDSReader()
        file_path = self.read_gds_file_path(layout_output_dir)
        try:
            gdsJson = gds_reader.read(file_path)
        except Exception as e:
            print(e)
            logger.error(f"{e}")
        return gdsJson
            
    def process_polygon_coordinates(self,xy_list):  
        return xy_list
        return [(xy_list[i] , xy_list[i + 1] ) for i in range(0, len(xy_list), 2)]
    
    def check_polygons_backside(self, backside_power_rail, gdsJson, cell_name):
        """
        Check that the VSS/VDD polygons or text are inside the correct layers
        depending on whether backside_power_rail is True (layer 300) or
        False (layer 200).
        """
        
        if not gdsJson:
            # No data, skip or record an error
            error_message = f"No GDS JSON data found for cell '{cell_name}'."
            logger.error(error_message)
            self.errors.append({'message': error_message, 'cell': cell_name})
            return

        units = gdsJson.get("bgnlib", [{}])[0].get("units", [1.0])[0]  # scaling unit
        power_text = ["VDD", "GND", "VSS"]
        elements = gdsJson.get("bgnlib", [{}])[0].get("bgnstr", [{}])[0].get("elements", [])
        
        power_rail_polygons = []
        metal_bar_points = []
        vss_vdd_points = []

        for element in elements:
            # If backside power is True, we expect layer 300 for power rails
            if backside_power_rail:
                if element['layer'] == 300:
                    # Polygons
                    if element['type'] == 'boundary' and element['datatype'] == 0:
                        polygon = Polygon(self.process_polygon_coordinates(element["xy"]))
                        #CHECK IF THE POWER RAIL WIDHT IS 37.5
                        power_rail_polygons.append(polygon)
                    # Text
                    if element['type'] == 'text':
                        text_string = element["string"]
                        # Convert the single text coordinate to a Shapely Point
                        coords = self.process_polygon_coordinates(element["xy"])
                        if coords:
                            point = Point(coords[0])
                            if text_string in power_text:
                                vss_vdd_points.append(point)
            else:
                # If not backside, we do NOT expect layer 300. If we see it, it's an error.
                if element['layer'] == 300:
                    error_message = (
                        "Layer 300 (datatype 0) found in a topside power rail configuration; "
                        "it should NOT be present for topside power rail."
                    )
                    logger.error(error_message)
                    self.errors.append({'message': error_message, 'cell': cell_name})
                
                # For topside, we expect power rails on layer 200
                if element['layer'] == 200:
                    if element['type'] == "boundary" and element['datatype'] == 0:
                        metal_polygon = Polygon(self.process_polygon_coordinates(element["xy"]))
                        metal_bar_points.append(metal_polygon)
                    if element['type'] == 'text' and 'string' in element:
                        text_string = element['string']
                        coords = self.process_polygon_coordinates(element["xy"])
                        if coords:
                            point = Point(coords[0])
                            if text_string in power_text:
                                vss_vdd_points.append(point)

        # Now check if the text (VSS/VDD) is inside the correct polygons
        for point in vss_vdd_points:
            if backside_power_rail:
                inside_power_rail = any([polygon.contains(point) for polygon in power_rail_polygons])
                if inside_power_rail:
                    print(f"Text is inside a power rail polygon at {point}")
                else:
                    error_message = "VSS/VDD text not inside power rail polygons (backside)."
                    logger.error(error_message)
                    self.errors.append({'message': error_message, 'cell': cell_name})
            else:
                inside_metal = any([polygon.contains(point) for polygon in metal_bar_points])
                if not inside_metal:
                    error_message = "VSS/VDD text not inside metal polygons for topside."
                    logger.error(error_message)
                    self.errors.append({'message': error_message, 'cell': cell_name})
                else:
                    logger.debug("VSS/VDD text properly placed in topside power metal.")
  
    def check_polygon_width(self,polygon_bounds,tech,ideal_width,cell_name):
        min_X,min_y,max_X,max_Y = polygon_bounds
        width = max_Y - min_y
        if width ==(ideal_width):
            return True
        return False


    def  check_power_rail_width(self,backside_power_rail, gdsJson, cell_name,tech):
        #incase of backwise_powerail
        #powerrail width - layer 300 - should be 37.5.. power rail width. is defined by layer 300//  so should conmtain only two elements with type == boundary and layer 300
        """
        the tech file have the metal bar width too.. two metal bars for that condition 0 with backside_powerrail false - shoudl be of width 37.5.. and the test should be of length lets say x.. or layer_width. for when backside = true - ill check for power rial wifth and for false it has to two of the layer =200 which is metal have to match that widht and the rest hav to metal bar widht . for backside power rail = true - those two (layer 300) have to be power rail width. .. and none in the metal bars should ideally be that width. so you can actually do multiple checks here - ensure every metal bar in this case is metal bar width.  i created a small helper method here - def check_polygon_width(self,polygon_bounds,tech,ideal_width):
        min_X,min_y,max_X,max_Y = polygon_bounds
        width = max_Y - min_y
        """
        if not gdsJson:
            # No data, skip or record an error
            error_message = f"No GDS JSON data found for cell '{cell_name}'."
            logger.error(error_message)
            self.errors.append({'message': error_message, 'cell': cell_name})
            return
        # units = gdsJson.get("bgnlib", [{}])[0].get("units", [1.0])[0]  # scaling unit
        power_text = ["VDD", "GND", "VSS"]
        elements = gdsJson['structures'][0]['elements']
        power_rail_polygons = []
        metal_bar_polygons = []
        vss_vdd_points = []
        for element in elements:
            # If backside power is True, we expect layer 300 for power rails
            if element['element'] == 'boundary' and element['datatype'] == 0:
                if backside_power_rail and element['layer'] == 300:
                # Polygons
                    polygon = Polygon(self.process_polygon_coordinates(element["xy"]))
                    power_rail_polygons.append(polygon)
                elif not backside_power_rail and element['layer'] == 200:                
                    polygon = Polygon(self.process_polygon_coordinates(element["xy"]))
                    metal_bar_polygons.append(polygon)

        ideal_power_width = tech['power_rail_width']*tech['scaling_factor']
        metal_bar_width = (tech['layer_width'][metal0])*tech['scaling_factor']
        logger.debug(f"check_backside_rail_width : {ideal_power_width}")
        logger.debug(f"metal_bar_width {metal_bar_width}")
        error_message = ""
        if backside_power_rail:
            backside_count = 0
            #error_message = f"width { }is incorrect - it is not equal to {(ideal_width)} "
            for polygon in power_rail_polygons:
                #check width is 37.5
                if self.check_polygon_width(polygon.bounds,tech,ideal_power_width,cell_name):
                    backside_count+=1
            if backside_count!=2:
                self.errors.append({"message":f"backside number of power rail polygons is not 2,its {backside_count}","cell":cell_name})
        else:
            metal_bars_of_correct_width = 0
            metal_bars_power_rail_width = 0
            # print(metal_bar_polygons, 'gfewduyigfewyuihfiduewghi')
            # input()
            for polygon in metal_bar_polygons:
                #two should be of width power rail width
                if self.check_polygon_width(polygon.bounds,tech,metal_bar_width,cell_name):
                    metal_bars_of_correct_width +=1
                elif self.check_polygon_width(polygon.bounds,tech,ideal_power_width,cell_name):
                    metal_bars_power_rail_width +=1
            logger.debug(f"number of metal_bars_of_correct_width length {metal_bars_of_correct_width}")
            logger.debug(f"number of metal_bars_power_rail_width {metal_bars_power_rail_width}")
            if metal_bars_power_rail_width!=2:
                self.errors.append({"message":f"should contain atleast 2 metal_bars of power rail width ,found only {metal_bars_power_rail_width}","cell":cell_name})

    def test_power_width(self):
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
                #("cfet", True, row[column_names[1]]),
                ("cfet", False, row[column_names[1]]),
            #("gaa", True, row[column_names[3]]),
                ("gaa", False, row[column_names[3]]),
                ("finfet", False, row[column_names[3]]),
                ]
                #try:
                for config_name, backside_power_rail, routing_tracks in configurations:
                    if routing_tracks == "NA":
                        continue
                    # Prepare the tech dictionary for the current configuration
                    # tech_dict = self.set_tech_file(self.base_tech_dict, config_name, backside_power_rail, routing_tracks,placer,power_rail_type)
                    # tech_json_str = json.dumps(tech_dict)
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
                    if not exists(layout_output_dir):
                        makedirs(layout_output_dir)
                    
                    #Generate layout
                    # with open(os.devnull, 'w') as f:
                    #     with redirect_stdout(f):
                    #         generate_layout_main(layout_args)
                        
                    gdsJson = self.load_json(layout_output_dir)#needs code to be executed before.
                    #gdsJson = self.read_gds(layout_output_dir)
                    # Check the polygons for the layout
                    json_dir = f"{cell_name}/{config_name}_{backside_power_rail}_{placer}/"
                    self.check_power_rail_width(backside_power_rail,gdsJson,cell_name,tech)
                        #{golden_data_path}/{cell_name}/{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations'
                        # Set up paths for golden data comparison
                    golden_layout_path = join(self.golden_data_base, cell_name, f"{config_name}_{backside_power_rail}_{placer}/")
                    #layout_output_dir =  f'{golden_data_path}/{cell_name}/{config_name}_{backside_power_rail}_{placer}/'
                    #golden_permutations_path = join(self.golden_data_base, cell_name, f"{cell_name}_{config_name}_{backside_power_rail}_{placer}_permutations/")
                    files = [file for file in listdir(layout_output_dir) if file.endswith(".gds")]
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
                      # Generate permutations
                    # with open(devnull,'w') as f:
                    #     with redirect_stdout(f):
                    #         pnr_main(permutation_args)

                    permutation_files = [name for name in listdir(permutation_output_dir) if isfile(join(permutation_output_dir, name)) and name.endswith('.json')]
                    for file in permutation_files:
                        print(f"permutation file {file}")
                        with open(join(permutation_output_dir, file), 'r') as f:
                            gdsJson = json.load(f)
                        self.check_power_rail_width(backside_power_rail,gdsJson,cell_name,tech)

                        #gds_writer.convert_gds_to_json(join(permutation_output_dir, file))
                # except Exception as e:
                #     # Record the error and continue
                #     error_message = f"Error for {cell_name} in config {config_name} ,{backside_power_rail}, Routing Tracks: {routing_tracks}: {e}"
                #     self.errors.append({'message': error_message, 'cell': cell_name})
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

    
if __name__ == '__main__':
    unittest.main()