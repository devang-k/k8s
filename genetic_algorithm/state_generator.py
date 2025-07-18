from utils.reader.gds_reader import GDSReader
from utils.writer.gds_writer import GDSWriter
import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pnr_permutations.generate_permutations import PermutationEngine,layerNumber,LayerProperties
from os import makedirs, listdir
from json import JSONEncoder, load, dumps
from os.path import abspath,exists, isfile,join,dirname
import logging
from tqdm.auto import tqdm
from dataclasses import dataclass, fields, field
from typing import List, Dict, Union
import json
from metrics_calculation.calculate_metrics import calculate_metrics_from_json_without_gds,create_layer_maps_and_f2f,calculate_f2f_length,main as calculate_metrics
from pex_extraction.dtco_ml_predict import main as pex_predict,model_factory
from stdcell_generation_client.technology_utils import load_tech_file
from pex_extraction.data_utils.utils import IL_layers_hardcoded_1,add_prefix_to_list,IL_layers_hardcoded_gaa
from pex_extraction.data_utils.preprocessing_encoding import load_and_preprocess_data
import pandas as pd
from utils.config import model_paths
#from stdcell_generation.processPermutations import main as process_permutations_main
from pathlib import Path
import shutil
import logging
sys.path.append(abspath(join(dirname(__file__), '..')))
logger = logging.getLogger('sivista_app')

class StateGenerator:
    def __init__(self, cell, model_type, tech, netlist,output_folder) -> None:
        self.args_gds_file  = f"{output_folder}/"
        tech_data = load_tech_file(tech)    
        self.required_columns = add_prefix_to_list(IL_layers_hardcoded_1) if tech_data.technology == 'cfet' else add_prefix_to_list(IL_layers_hardcoded_gaa)
        self.cell = cell
        self.polygon_position = {}
        # self.reader = GDSReader()
        self.generate_layout(cell, tech, netlist,output_folder)
        self.layer_properties = None
        self.permutation_engine = self.initialise_permutation_engine()
        self.permutation_engine.io_pins = io_pins
        self.permutation_engine.tech = tech_data
        if self.permutation_engine.drc.checkDRC(strict = False):
            self.permutation_layer_map = self.permutation_engine.layerMap
        self.model_type = model_type
        self.tech = tech_data #for future need
        self.output_folder = output_folder
        files = []
        for gds_file in listdir(self.args_gds_file):
            if gds_file.endswith(".gds"):
                files.append(gds_file)
        layer_map_path = f'{output_folder}/'#f'{cell}'
        gds_file = f"{cell}/"
        default_layer_map = tech_data.metrics_map
        layer_map, self.f2f_layers =  create_layer_maps_and_f2f(layer_map_path,default_layer_map)

        if layer_map is None:
            return
        layer_map['default'] = default_layer_map
        #needs to be fixed.
        file_name = files[0].split('/')[-1].replace('.gds','')
        self.file_name = file_name
        self.layer_name_map =  layer_map[file_name]
    
        self.f2f_dict_key = self.f2f_layers[file_name]
        self.metal_polygons = []
        for layer in self.layer_properties.permLayers:
                if tech_data.backside_power_rail:
                    self.metal_polygons.extend(self.permutation_layer_map[layer].polygons)
                else:
                    self.metal_polygons.extend(self.permutation_engine.remove_power_ground_polygons(self.permutation_layer_map[layer].polygons))
                                         
        self.track_polygons = sorted(
                self.permutation_layer_map[layerNumber['HorizontalTracks']].polygons,
                key = lambda poly: poly.point.bounds[1]
        )

    def initialise_permutation_engine(self):
        gds_file = self.args_gds_file 
        permutation_engine = None      
        if isfile(gds_file):
            permutation_engine = PermutationEngine(f"{gds_file}",f"{self.args_gds_file}")
            self.layer_properties = permutation_engine.layer_properties
        else:
            for gds_file in tqdm(listdir(self.args_gds_file)): 
                    if gds_file.endswith(".gds"):
                        permutation_engine = PermutationEngine(f"{self.args_gds_file}{gds_file}",f"{self.args_gds_file}")
                        self.layer_properties = permutation_engine.layer_properties
        return permutation_engine
        
    def getState(self):
        """_summary_

        Args:
            layer_map:layer map containing polygons and layer mapping

        Returns:
            Returns the state as a list of metal positions (e.g., [1, 2, 3, 4]).
            _type_: list [1,2,3,4]
        """
        metal_polygon_tracks = []
        for metal_id, metal_polygon in enumerate(self.metal_polygons):
                for track_number, track_polygon in enumerate(self.track_polygons):
                    if metal_polygon.point.intersects(track_polygon.point) or metal_polygon.point.within(track_polygon.point):
                         metal_polygon_tracks.append(track_number)
                         self.polygon_position[metal_id] = track_number  
                         break       
        return metal_polygon_tracks
       
    def getData(self,state):
        """
        Get the gds json description of the gds file
        Args:
            state (_type_): array of metal positions

        Returns:
            _type_: gds json-json description of the gds file
        """
        vias = set()
        connectors = set()
        direction = "V"
        connectedComponents = None
        for index,track_number in enumerate(state):
            current_metal_polygon = self.metal_polygons[index]
            vias = set()
            connectors = set()
            connectors.add(current_metal_polygon)
            if not connectedComponents:
                connectedComponents = set()
            for connector in connectors:            
                for polygon in connector.layerMap:               
                    if polygon.isVia:
                        vias.add(polygon)
                    else:
                        connectedComponents.add(polygon)
            vias = list(vias) 

            #shift original polygon to that track
            #assumption here is they are always int he same order - so we take the step from the initial state created.
            
            step = int(self.track_polygons[track_number].point.centroid.y - current_metal_polygon.point.centroid.y)
            for via in vias:
                    via.shiftPolygon(direction=direction,offset=step)
            for connector in connectors:
                    connector.shiftPolygon(direction=direction,offset=step)
                    for textPolygon in connector.textPolygons:
                        textPolygon.shiftPolygon(direction=direction,offset=step)  
        if self.permutation_engine.checkBoundary(vias[0].point):
            if self.permutation_engine.drc.checkPitch(layer=layerNumber['M0'], val=self.layer_properties.layer1000Pitch):
                changes = self.permutation_engine.optimizeLayers(layerNumber['M0'])
                if self.permutation_engine.drc.checkDRC():
                    newgdsJson = self.permutation_engine.convert_to_json()
                    for boundary in self.permutation_engine.layerMap[layerNumber["Boundary"]].polygons:
                        #fixing the bounding box
                        boundary.coord1[1] = self.permutation_engine.globalBoundary[1]
                        boundary.coord2[1] = self.permutation_engine.globalBoundary[3]
                        boundary.coord3[1] = self.permutation_engine.globalBoundary[3]
                        boundary.coord4[1] = self.permutation_engine.globalBoundary[1]
                        boundary.updatePoint()
                    file_name = f"{''.join(map(str, state))}_1_RT_6_1"
                                 
                    return newgdsJson
                else:
                    logger.debug(f" fails DRC")
                    return None# doesnt pass DRC
            else:
                return None
        else:
             logger.debug(f"beyond legal boundary")
             return None

        
    def getDrc(self,state):
        """
        Checks if state  passes drcCheck
        Args:
            data  containing polygon/metal details.
        Returns:
            Score (1 for DRC pass, 0 for DRC fail).
        """
        gdsJson = self.getData(state)
        return int(gdsJson is not None)
    
    def getCapacitance(self,state):
        """
        Get the capacitance of the gds file
        Args:
            state: array of metal positions
        Returns:
            capacitance: capacitance of the gds file
        """
        gds_json = self.getData(state) 
        metrics_df = self.calculate_metrics(gds_json ,state)       
        validated_df = load_and_preprocess_data(metrics_df, self.required_columns,isGAA=self.tech.technology == 'gaa')
        data = self.predicit_capacitance(validated_df)
        return data
         
    def calculate_metrics(self,gds_json,state):
        """
        Calculate the metrics of the gds file
        Args:
            gds_json: gds json description of the gds file
            state: array of metal positions
        Returns:
            metrics: metrics of the gds file
        """
        column_names =  ["File", "Layer", "Total Area (µm²)", "Density (%)", "Total Length (µm)", "F2F Total Length (µm)", "Number of Polygons", "Polygons", "Adjacent Layer", "Labels"]
        f2f_metrics = {}
        consolidated_metrics = {}
        metrics = calculate_metrics_from_json_without_gds(gds_json,self.layer_name_map,self.f2f_dict_key)      
        file = f"{''.join(map(str, state))}_1_RT_6_1"

        consolidated_metrics[file] = metrics
        layer_pairs = list(self.layer_name_map.keys())   
        # Fix: Unpack a and b from each tuple in layer_pairs before zipping
        flat_layer_pairs = [(str(a), str(b)) for a, b in layer_pairs]
        layer_pairs = [(self.layer_name_map[a], self.layer_name_map[b]) for a, b in zip(flat_layer_pairs[:-1], flat_layer_pairs[1:])]
        for layer1, layer2 in layer_pairs:      
            layer1_polygons = metrics.get(layer1,{}).get("polygons", [])
            layer2_polygons = metrics.get(layer2,{}).get('polygons',[])
            f2f_length = calculate_f2f_length(layer1_polygons, layer2_polygons, "y")
            f2f_metrics[layer1] = {"f2f_length": f2f_length, "adjacent_layer": layer2}
        rows = []
        for file, layers in consolidated_metrics.items():
            matching_key = self.file_name
            for layer, metrics in layers.items():
                adjacent_layer = self.f2f_layers[matching_key].get(layer, "N/A") 
                label_str = json.dumps(metrics["labels"]) if metrics["labels"] is not None else "" 
                row = [file, layer, metrics["total_area_um2"], metrics["density_percentage"], metrics["total_length_um"],
                        metrics["f2f"], metrics["num_polygons"], metrics["polygons"], 
                        adjacent_layer, label_str]
                rows.append(row)
        metrics_df = pd.DataFrame(rows,columns = column_names)
        return metrics_df
    
    def predicit_capacitance(self,validated_df):
        """
        Predict the capacitance of the gds file
        Args:
            validated_df: dataframe of the gds file
        Returns:
            capacitance: capacitance of the gds file
        """
        model = model_factory(self.model_type, self.required_columns,isGAA=self.tech.technology == 'gaa')
        batch_size = 100
        data = model.run_pipeline(validated_df, batch_size, output_path = "")
        if not isinstance(data,list):
             data = [data]
        return data
    
    def generate_layout(self,cell,tech,netlist,output_folder):
            args = {
                'tech':tech,
                'netlist':netlist, 
                'output_dir':output_folder,
                'cell' :f'{cell}',
                "placer":'base0' ,
                "signal_router" : 'dijkstra',
                "debug_routing_graph": False,
                "debug_smt_solver": False,
                "placement_file": None,
                "log": None,
                "quiet": True,
                "debug_plots": False
                }
            process_permutations_main(args)

def prepare_working_directory(directory):
    """
    Prepare the working directory by clearing or creating it.
    """
    dir_path = Path(directory)
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
            
def main(args):
     cell = args.get("cell")
     model_type = args.get("model","gnn")
     pdk = args.get("pdk","monCFET")
     tech = args.get("tech",f'./tech/{pdk}/{pdk}.tech')
     output_folder = args.get("output_dir")
     netlist = args.get("netlist",f'./tech/{pdk}/{pdk}.spice')
     state_generator = StateGenerator(cell, model_type, tech, netlist,output_folder)
     initial_state = state_generator.getState()
    #  

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Generate GDS layout from  netlist.')
    parser.add_argument('--netlist', default='cells.sp',
                        metavar='FILE', type=str, help='path to SPICE netlist (cells.sp)')  
    parser.add_argument('--pdk',type = str)
    parser.add_argument("--tech", type=str, help="Layer map file in plain text format")
    parser.add_argument("--model",choices=["moe","gnn"],default="gnn")
    parser.add_argument('--cell', required=True,         
                        metavar='NAME', type=str, help='cell name (e.g., NAND2X1)')
    parser.add_argument("--output_dir")
    
    args, unknown = parser.parse_known_args()
    args = { 
            "cell":args.cell  ,
            "model":args.model,
            "tech":args.tech,
            "netlist":args.netlist,
            "pdk": args.pdk,
            "output_dir":args.output_dir
              }

    main(args)