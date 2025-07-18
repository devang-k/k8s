import json
from typing import List, Dict, Optional
from shapely.geometry import Polygon
import logging
from pnr_permutations.generate_permutations import LayerProperties
import os
from os.path import isfile
from collections import defaultdict
from json import load

logger = logging.getLogger(__name__)


def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets


def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets


def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)


class PolygonInfo:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __hash__(self):
        # Use the id as the basis for hashing since it should be unique
        return hash(self.id)

    def __eq__(self, other):
        # Two PolygonInfo objects are equal if they have the same ids
        if not isinstance(other, PolygonInfo):
            return False
        return self.id == other.id


class TextLabel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class PolygonProcessor:
    """_summary_
    This class takes in gds json file path,layer map path and processes the polygon information and converts to layermap
    """

    def __init__(self, json_file_path: str, layer_map_path: str):
        self.json_file_path = json_file_path
        json_data = self._load_gds_json_file(json_file_path)
        self.layer_to_polygons = defaultdict(list)
       
        self.text_labels = {}
        self._convert_to_text_labels(json_data["structures"][0]["elements"])
        self.polygons = {}
        self._convert_to_polygon_info(json_data["structures"][0]["elements"])
        self.base_layout_name = json_data.get('base_layout_name')
        self.layer_to_layer_name = {}
        self.layerMap = {}
        self._convert_to_old_layerMapPolygons()
        self.layer_properties = self.get_layer_properties(layer_map_path)
        self.layer_numbers = {}
        self.get_layer_to_layer_name()

    def _load_gds_json_file(self, json_file_path: str):
        try:
            with open(json_file_path, 'r') as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: with path {json_file_path} {e}")
            exit(1)
        return json_data

    def _convert_to_polygon_info(self, elements):
        """_summary_
        convert elements to polygon info objects

        Args:
            elements (List): elements from gds json file

        Returns:
            None
        """
      
        for element in elements:
            datatype = element.get('datatype', 0)
            if element.get('element') == 'boundary' and datatype == 0:
                layer = element.get('layer')
                self.polygons[element.get('id')] = PolygonInfo(
                    id=element.get('id'),
                    datatype=element.get('datatype', 0),
                    layer=layer,  # element.get('layer'),
                    xy=element.get('xy', []),
                    point=Polygon(element.get('xy', [])),  # point,
                    adjacencyList=element.get('adjacencyList', []),
                    planarConnectedPolygon=element.get(
                        'planarConnectedPolygon', None),  # planar_connected,
                    connectedGate=element.get('connectedGate', None),
                    connectedInterconnect=element.get(
                        'connectedInterconnect', None),
                    isVia=element.get('isVia', False),  # is_via,
                    layer_name=element.get('layer_name', f"Layer_{layer}"),
                    textPolygons=set(element.get('textPolygons', [])),
                    layerMap=element.get('layerMap', None))
                self.layer_to_polygons[layer].append(element.get('id'))
        for key, value in self.polygons.items():
            adjacencyList = value.adjacencyList
            for i, polygon_id in enumerate(adjacencyList):
                if polygon_id in self.polygons:
                    value.adjacencyList[i] = self.polygons[polygon_id]
            layerMap = value.layerMap
            for i, polygon_id in enumerate(layerMap):
                if polygon_id in self.polygons:
                    value.layerMap[i] = self.polygons[polygon_id]
            # add polygoninfo value for planarConnectedPolygon
            if value.planarConnectedPolygon:
                value.planarConnectedPolygon = self.polygons[value.planarConnectedPolygon]
            # add polygoninfo value for connectedGate
            if value.connectedGate:
                value.connectedGate = self.polygons[value.connectedGate]
            # add polygoninfo value for connectedInterconnect
            if value.connectedInterconnect:
                value.connectedInterconnect = self.polygons[value.connectedInterconnect]

    def get_layer_properties(self, layer_map_dir):
        """_summary_

        Args:
            layer_map_dir (_type_): get layer properties from layer map directory

        Raises:
            e: error loading layer properties

        Returns:
            layer_properties: layer properties
        """
        # can get layername from here.
        original_fileName = os.path.basename(
            self.base_layout_name).replace('.gds', '')
        base_fileName = original_fileName
        tokens = original_fileName.split('_')
        if len(tokens) > 1 and tokens[-1].isdigit():
            if tokens[-2].isdigit():
                base_fileName = '_'.join(tokens[:-1])
        layer_properties = LayerProperties()
        fileName = f"{layer_map_dir}/layerMap{base_fileName}.json"
        if isfile(layer_map_dir):
            fileName = layer_map_dir
        try:
            with open(fileName) as f:

                layer_properties.update_from_dict(load(f))
                layer_properties.moveTogether = True
        except Exception as e:
            logger.error(f"Error loading layer properties: {e}")
            raise e
        return layer_properties

    def get_layer_to_layer_name(self):
        """_summary_
        @return: dictionary of layer numbers and layer names.
        This function takes in the layer_map and returns a dictionary of layer numbers and layer names.
        """
        layers = self.layer_properties.Layers
        self.layer_to_layer_name = {}
        for layer_number, layer_properties in layers.items():
            self.layer_to_layer_name[int(
                layer_number)] = layer_properties["Name"]
            self.layer_numbers[layer_properties["Name"]] = int(layer_number)

    def _convert_to_text_labels(self, elements: List):
        """_summary_
        convert elements to text labels
        Args:
            elements (List): elements from gds json file

        Returns:
            None
        """
        # convert to text labels
        for element in elements:
            if element.get('element') == 'text' and element.get('datatype') == 1:
                XY = element.get('xy', [])
                XY = XY[0]
                self.text_labels[element.get('id')] = TextLabel(
                    id=element.get('id'),  # text_label_id,
                    type="text",
                    datatype=element.get('datatype', 1),
                    presentation=element.get('presentation', 0),
                    XY=XY,
                    string=element.get('text', ""),
                    point=Polygon([(XY[0], XY[1]) for _ in range(4)])  # point
                )

    def _convert_to_old_layerMapPolygons(self):
        """_summary_
        convert layer to polygons to old layer map
        """
        for layer_number, polygons in self.layer_to_polygons.items():
            if layer_number not in self.layerMap:
                self.layerMap[int(layer_number)] = []
            for polygon_id in polygons:
                # Skip text elements - they should not be treated as polygons
                if polygon_id.startswith('text_'):
                    continue
                if polygon_id in self.polygons:
                    polygon_info = self.polygons[polygon_id]
                    self.layerMap[int(layer_number)].append(polygon_info)
                else:
                    logger.warning(
                        f"Polygon ID {polygon_id} not found in polygons dictionary")
        # Print layerMap contents after all polygons are processed
