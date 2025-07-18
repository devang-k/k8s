#!/usr/bin/env python
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','.'))

# Append the project root to sys.path
sys.path.append(project_root)

# Add the utils directory to sys.path
utils_path = os.path.join(project_root, 'utils')
sys.path.append(utils_path)
import json
import csv
import argparse
import glob
import logging
from tqdm import tqdm
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from collections import defaultdict
import json
from json import JSONEncoder
from sivista_db.repository.layer_metrics_repository import LayerMetricsRepository
from sivista_db.repository.permutation_repository import PermutationRepository
from stdcell_generation_client.technology_utils import load_tech_file
from utils.reader.gds_reader import GDSReader


# Initialize logging
logger = logging.getLogger('sivista_app')
#This is used for comments
class PointEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

class ReportGenerator:
    def __init__(self, data, f2f_dicts):
        self.data = data
        self.f2f_layers = f2f_dicts

    def write_to_db(self):
        layer_metric_repository = LayerMetricsRepository()
        for file, layers in self.data.items():
            for layer, metrics in layers.items():
                adjacent_layer = self.f2f_layers.get(layer, "N/A")   
                polygon_str = json.dumps(metrics["polygons"])
                label_str = json.dumps(metrics["labels"])
                layer_metric_dict = {"permutation_id" :file,"Layer":layer,"Total Polygon Area (µm²)" : metrics["total_area_um2"],"Density (%)" : metrics["density_percentage"], "Total Polygon Length (µm)" : metrics["total_length_um"],
                                     "Number of Polygons" : metrics["num_polygons"],"F2F Total Length (µm)": metrics["f2f"],"Polygons" : polygon_str, "Adjacent Layer":adjacent_layer, "Labels":label_str} 
                layer_metric_repository.upsert(layer_metric_dict)
        layer_metric_repository.close()

    def write_to_file(self, output_file):
        with open(output_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([])
            writer.writerow(["File", "Layer", "Total Polygon Area (µm²)", "Density (%)", "Total Polygon Length (µm)", "F2F Total Length (µm)", "Number of Polygons", "Polygons", "Adjacent Layer", "Labels"])
            for file, layers in self.data.items():
                if file in self.f2f_layers.keys():
                    matching_key = file
                else:
                    matching_key = [k for k in self.f2f_layers if file.startswith(k)]
                    matching_key = next(iter(matching_key), 'default')
                for layer, metrics in layers.items():
                    adjacent_layer = self.f2f_layers[matching_key].get(layer, "N/A") 
                    writer.writerow([file, layer, metrics["total_area_um2"], metrics["density_percentage"], metrics["total_length_um"], metrics["f2f"], metrics["num_polygons"], metrics["polygons"], adjacent_layer, metrics["labels"]])

def read_layer_map(layermap):
    layer_map = {}
    for layerdata in layermap:
        layer_map[(str(layerdata[1][0]), str(layerdata[1][1]))] = layerdata[0]
    return layer_map

def create_layer_maps_and_f2f(directory_path, default_layer_map=None):
    layermaps = defaultdict(lambda: default_layer_map)
    f2f_dicts = defaultdict(lambda: dict)
    for filename in os.listdir(directory_path):
        if filename.startswith("layerMap") and filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r') as file:
                try:
                    json_content = json.load(file)
                    metricsmap = json_content['metricsMap']
                    key = filename.split('.')[0].replace('layerMap', '')
                    layermaps[key] = read_layer_map(metricsmap)
                    f2f_dicts[key] = json_content['f2fLayers']
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {filename}: {e}")

    return layermaps, f2f_dicts

def process_polygon_coordinates(xy_list, units):  
    return [(xy[0] * units, xy[1] * units) for xy in xy_list]

def calculate_metrics_from_table(data,layer_map):
    units = data.get("bgnlib", [{}])[0].get("units", [1.0])[0]  # Fetching scaling unit
    elements = data.get("bgnlib", [{}])[0].get("bgnstr", [{}])[0].get("elements", [])
    layer_metrics = {}
    cell_boundary_area = 0  # in um^2
    textElements = {}
    for element in elements:
        if element["type"]=='text':
            layer = str(element["layer"])
            datatype = str(element["texttype"])
            layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")
            textElements.setdefault(layer_name, []).append(element)
        if element["type"]!='boundary':
            continue
        layer = str(element["layer"])
        datatype = str(element["datatype"])     
        layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")
        polygon = Polygon(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
        if layer_name == "CELL_BOUNDARY":
            cell_boundary_area = polygon.area  # Fetching cell boundary area for density calculation, in um^2
        if layer_name not in layer_metrics:
            layer_metrics[layer_name] = {"polygons": []}
        layer_metrics[layer_name]["polygons"].append(polygon)
    for layer_name, data in layer_metrics.items():
        merged_polygon = unary_union(data["polygons"])
        total_area = merged_polygon.area  # in um^2
        density = (total_area / cell_boundary_area) * 100 if cell_boundary_area > 0 else 0  # in percentage
        total_length = sum(p.exterior.length for p in data["polygons"])  # in um
        num_polygons = len(data["polygons"])
        labels = []
        if layer_name + "_LABEL" in textElements:
            for polygon in data["polygons"]:
                for element in textElements[layer_name + "_LABEL"]:
                    text = Point(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
                    if polygon.contains(text):
                        labels.append(element['string'])
        metrics = {
            "total_area_um2": total_area,  # in um^2
            "density_percentage": density,  # in percentage
            "total_length_um": total_length,  # in um
            "num_polygons": num_polygons,
            "polygons" : [polygon.bounds for polygon in data["polygons"]],
            "labels" : labels if len(labels)>0 else None
        }
        layer_metrics[layer_name] = metrics  
    return layer_metrics


def calculate_metrics_from_json(json_file, layer_map, f2f_layers, height_req):
    gds_reader = GDSReader()
    data = gds_reader.read(json_file)
    units = data.get("units", [1.0])[0]  # Fetching scaling unit
    elements = data.get("structures", [{}])[0].get("elements", [])
    layer_metrics = {}
    cell_boundary_area = 0  # in um^2
    subcell_boundaries = []
    textElements = {}
    for element in elements:
        if element["element"]=='text':
            layer = str(element["layer"])
            datatype = str(element["datatype"])
            layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")
            textElements.setdefault(layer_name, []).append(element)
        if element["element"]!='boundary':
            continue
        layer = str(element["layer"])
        datatype = str(element["datatype"])
        layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")

        polygon = Polygon(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
        if layer_name == "CELL_BOUNDARY":
            cell_boundary_area = polygon.area  # Fetching cell boundary area for density calculation, in um^2
            x1, y1, x2, y2 = polygon.bounds
            subcell_height = (y2 - y1) / height_req
            for i in range(height_req):
                new_y1 = y1 + i * subcell_height
                new_y2 = y1 + (i + 1) * subcell_height
                subcell_boundaries.append((x1, new_y1, x2, new_y2))

        if layer_name not in layer_metrics:
            layer_metrics[layer_name] = {"polygons": []}

        layer_metrics[layer_name]["polygons"].append(polygon)
    for layer_name, data in layer_metrics.items():
        gate_f2f_total = 0
        if layer_name in f2f_layers.keys():
            layer1 = layer_name
            layer2, f2f_axis = f2f_layers[layer_name]
            layer1Polygons = [polygon.bounds for polygon in layer_metrics[layer1]["polygons"]]
            layer2Polygons = [polygon.bounds for polygon in layer_metrics[layer2]["polygons"]]
            f2f_val = calculate_f2f_length(layer1Polygons, layer2Polygons, f2f_axis, subcell_boundaries)
            gate_f2f_total = f2f_val
        merged_polygon = unary_union(data["polygons"])
        total_area = merged_polygon.area  # in um^2
        density = (total_area / cell_boundary_area) * 100 if cell_boundary_area > 0 else 0  # in percentage
        total_length = sum(p.exterior.length for p in data["polygons"])  # in um
        num_polygons = len(data["polygons"])
        labels = []
        if layer_name + "_LABEL" in textElements:
            for polygon in data["polygons"]:
                for element in textElements[layer_name + "_LABEL"]:
                    text = Point(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
                    if polygon.contains(text):
                        labels.append(element['text'])
        metrics = {
            "total_area_um2": total_area,  # in um^2
            "density_percentage": density,  # in percentage
            "total_length_um": total_length,  # in um
            "num_polygons": num_polygons,
            "polygons" : [polygon.bounds for polygon in data["polygons"]],
            "labels" : labels if len(labels)>0 else None,
            "f2f": gate_f2f_total if layer_name in f2f_layers.keys() else 0
        }
        layer_metrics[layer_name] = metrics
       
    return layer_metrics

def calculate_metrics_from_json_without_gds(data, layer_map, f2f_layers):

    units = data.get("bgnlib", [{}])[0].get("units", [1.0])[0]  # Fetching scaling unit
    elements = data.get("bgnlib", [{}])[0].get("bgnstr", [{}])[0].get("elements", [])
    layer_metrics = {}
    cell_boundary_area = 0  # in um^2
    textElements = {}
    for element in elements:
        if element["type"]=='text':
            layer = str(element["layer"])
            datatype = str(element["texttype"])
            layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")
            textElements.setdefault(layer_name, []).append(element)
        if element["type"]!='boundary':
            continue
        layer = str(element["layer"])
        datatype = str(element["datatype"])
        layer_name = layer_map.get((layer, datatype), f"{layer}:{datatype}")

        polygon = Polygon(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
        if layer_name == "CELL_BOUNDARY":
            cell_boundary_area = polygon.area  # Fetching cell boundary area for density calculation, in um^2

        if layer_name not in layer_metrics:
            layer_metrics[layer_name] = {"polygons": []}

        layer_metrics[layer_name]["polygons"].append(polygon)
    for layer_name, data in layer_metrics.items():
        gate_f2f_total = 0
        if layer_name in f2f_layers.keys():
            layer1 = layer_name
            layer2, f2f_axis = f2f_layers[layer_name]
            layer1Polygons = [polygon.bounds for polygon in layer_metrics[layer1]["polygons"]]
            layer2Polygons = [polygon.bounds for polygon in layer_metrics[layer2]["polygons"]]
            f2f_val = calculate_f2f_length(layer1Polygons, layer2Polygons, f2f_axis)
            gate_f2f_total = f2f_val
        merged_polygon = unary_union(data["polygons"])
        total_area = merged_polygon.area  # in um^2
        density = (total_area / cell_boundary_area) * 100 if cell_boundary_area > 0 else 0  # in percentage
        total_length = sum(p.exterior.length for p in data["polygons"])  # in um
        num_polygons = len(data["polygons"])
        labels = []
        if layer_name + "_LABEL" in textElements:
            for polygon in data["polygons"]:
                for element in textElements[layer_name + "_LABEL"]:
                    text = Point(process_polygon_coordinates(element["xy"], units))  # Scaling coordinates
                    if polygon.contains(text):
                        labels.append(element['string'])
        metrics = {
            "total_area_um2": total_area,  # in um^2
            "density_percentage": density,  # in percentage
            "total_length_um": total_length,  # in um
            "num_polygons": num_polygons,
            "polygons" : [polygon.bounds for polygon in data["polygons"]],
            "labels" : labels if len(labels)>0 else None,
            "f2f": gate_f2f_total if layer_name in f2f_layers.keys() else 0
        }
        layer_metrics[layer_name] = metrics
    return layer_metrics

def calculate_unidirectional_overlap_length(segment1, segment2):
    overlap = max(0, min(segment1[1], segment2[1]) - max(segment1[0], segment2[0]))
    return overlap

def get_longer_axis(bounds):
    min_x, min_y, max_x, max_y = bounds
    return 'x' if (max_x - min_x) > (max_y - min_y) else 'y'

def get_axis_segments(bounds, axis):
    #get coordinates from bounds
    coords = [(bounds[0], bounds[1]) , (bounds[0], bounds[3]) , (bounds[2], bounds[3]) , (bounds[2], bounds[1]), (bounds[0], bounds[1])]
    segments = []
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        if axis == 'x' and y1 == y2:
            segments.append((min(x1, x2), max(x1, x2)))
        elif axis == 'y' and x1 == x2:
            segments.append((min(y1, y2), max(y1, y2)))
    return segments

def merge_and_sort_polygons(layer1_polygons, layer2_polygons, axis):
    sort_dim = 0 if axis == 'y' else 1
    merged_polygons = layer1_polygons + layer2_polygons
    return sorted(merged_polygons, key=lambda x: x[sort_dim])

def calculate_f2f_length_between_polygons(polygon1, polygon2, axis):
    # min_x, min_y, max_x, max_y
    if axis == 'x':
        dims = [0, 2]
    else:
        dims = [1, 3]
    overlap = max(0, min(polygon1[dims[1]], polygon2[dims[1]]) - max(polygon1[dims[0]], polygon2[dims[0]]))
    return overlap

def clip_polygon(inner, outer):
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer
    nx1 = max(ix1, ox1)
    ny1 = max(iy1, oy1)
    nx2 = min(ix2, ox2)
    ny2 = min(iy2, oy2)
    if nx1 < nx2 and ny1 < ny2:
        return (nx1, ny1, nx2, ny2)
    else:
        return None

def assign_polygons_to_subcells(boundaries, small_rectangles):
    boundary_dict = {boundary: [] for boundary in boundaries}
    for small_rect in small_rectangles:
        for boundary in boundaries:
            clipped = clip_polygon(small_rect, boundary)
            if clipped:
                boundary_dict[boundary].append(clipped)
    return boundary_dict

def calculate_f2f_length(layer1_polygons, layer2_polygons, axis, subcell_boundaries=[]):
    subcell_f2f = {}
    subell_polygons1 = assign_polygons_to_subcells(subcell_boundaries, layer1_polygons)
    subell_polygons2 = assign_polygons_to_subcells(subcell_boundaries, layer2_polygons)
    for subcell_boundary in subcell_boundaries:
        subcell_f2f[subcell_boundary] = 0
        sorted_polygons = merge_and_sort_polygons(subell_polygons1[subcell_boundary], subell_polygons2[subcell_boundary], axis)
        for i in range(len(sorted_polygons) - 1):
            polygon1 = sorted_polygons[i]
            polygon2 = sorted_polygons[i + 1]
            f2f = calculate_f2f_length_between_polygons(polygon1, polygon2, axis)
            subcell_f2f[subcell_boundary] += f2f
    return sum([v for k,v in subcell_f2f.items()])

def create_consolidated_metrics_from_file(input_path,consolidated_metrics,layer_map_dict,f2f_dicts, height_req):
        files = []
        if os.path.isdir(input_path):
            files = glob.glob(os.path.join(input_path, "*.gds"))
        elif os.path.isfile(input_path):
            files = [input_path]
        else:
            files = glob.glob(input_path) 
        results= []
        for file in files:
            key = file.split('/')[-1].split('.')[0]
            if key in layer_map_dict:
                results.append(calculate_metrics_from_json(file, layer_map_dict[key], f2f_dicts[key], height_req))
            else:
                matching_key = [k for k in layer_map_dict if key.startswith(k)]
                matching_key = next(iter(matching_key), 'default')
                results.append(calculate_metrics_from_json(file, layer_map_dict[matching_key], f2f_dicts[matching_key], height_req))
        for file, metrics in zip(files, results):
            if metrics is not None:
                file_name = os.path.splitext(os.path.basename(file))[0]
                consolidated_metrics[file_name] = metrics
        return consolidated_metrics

def create_consolidated_metrics_from_db(consolidated_metrics,cell_name,layer_map_dict,f2f_dicts):
        permutation_repository = PermutationRepository()
        permutations = permutation_repository.fetch_records_cell_name(cell_name)
        for permutation in permutations:
            file_name = permutation.permutation_id
            data = json.loads(permutation.gds_json)
            key = '_'.join(file_name.split('_')[:-1])
            metrics = calculate_metrics_from_table(data, layer_map_dict[key])
            if metrics is not None:
                consolidated_metrics[file_name] = metrics
        return consolidated_metrics
                        
def main(args):

    # Default values for each expected argument
    input_path = args.get('input_path')
    cell = args.get('cell', "")
    output_folder = args.get('output_dir', f'{cell}/')
    flow_type = args.get('flow_type')
    tech = args.get('tech', None)
    default_layer_map = None
    height_req = 1
    if tech:
        tech_data = load_tech_file(tech)
        default_layer_map = tech_data.metrics_map
        height_req = tech_data.height_req
        
    layermap_path = args.get('layermap_path')
    layer_maps, f2f_dicts = create_layer_maps_and_f2f(layermap_path, default_layer_map)
    if not layer_maps or not f2f_dicts:
        return
    consolidated_metrics = {}
    layer_maps['default'] = default_layer_map

    if flow_type == "gds" :
        consolidated_metrics = create_consolidated_metrics_from_file(input_path,consolidated_metrics,layer_maps,f2f_dicts, height_req)
    elif flow_type == "db" :
        consolidated_metrics = create_consolidated_metrics_from_db(consolidated_metrics,cell,layer_maps,f2f_dicts)

    reporter = ReportGenerator(consolidated_metrics, f2f_dicts) 
    os.makedirs(output_folder, exist_ok=True)
    consolidated_output_file = os.path.join(output_folder, f"{cell}_metrics.csv")
    reporter.write_to_file(consolidated_output_file)
    if flow_type == "db":
        reporter.write_to_db()
   
    logging.info(f"SUCCESS: Saved DTCO metrics to: {consolidated_output_file}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Calculate various metrics for each layer in GDSII JSON files.")
    parser.add_argument("--input_path", type=str, help="Path to JSON file or directory containing JSON files")
    parser.add_argument("--layermap_path", type=str, help="Path to folder with layermap JSON files.")
    parser.add_argument("--output", type=str, nargs='+', choices=["csv","db"], default=["csv"], help="Output formats for metrics, separated by space (e.g., json csv markdown)")
    parser.add_argument("--cell",type = str,help ="")
    parser.add_argument("--tech", type=str, help="Layer map file in plain text format")
    parser.add_argument("--flow_type",choices=['db', 'gds'],default = "gds", help ="Variable indicates whether to read gds files or gds info from gds files or  database")
    args, unknown = parser.parse_known_args()
    args = {
    "input_path": args.input_path,
    "layermap_path": args.layermap_path,
    "output": args.output,
    "tech": args.tech,
    "cell": args.cell,
    "flow_type":args.flow_type
    }
    main(args)