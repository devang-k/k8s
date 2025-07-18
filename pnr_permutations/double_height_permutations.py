#!/usr/bin/env python
#  element:  boundary | path | sref | aref | text | node | box

from __future__ import print_function
from builtins import print as println
from dataclasses import dataclass, fields, field
from datetime import datetime
from json import JSONEncoder, load, dumps, dump
from os import makedirs, listdir
from os.path import exists, isfile
from pandas import read_csv, merge, DataFrame
from pnr_permutations.design_rule_constraints.cfet_rule_checker import CFETDesignRuleCheck
from pnr_permutations.design_rule_constraints.gaa_rule_checker import GAADesignRuleCheck
from pnr_permutations.design_rule_constraints.finfet_rule_checker import FINFETDesignRuleCheck
from pnr_permutations.design_rule_constraints.gaa_dubheight_rule_checker import GAADoubleHeightDesignRuleCheck
from shapely.geometry import Polygon as Point
from shapely.geometry import box, Polygon
from shapely.ops import unary_union  
from sys import stdout
from tqdm.auto import tqdm
from typing import List, Dict, Union
from sivista_db.models.permutation_model import Permutation
from sivista_db.repository.permutation_repository import PermutationRepository
from stdcell_generation_client.technology_utils import load_tech_file
from gdsast import gds_read
from pnr_permutations.LVSClient import LVSClientHandler
from copy import deepcopy
from pathlib import Path
import copy
import os
from typing import Set
from collections import defaultdict

class PointEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__
layerNumber = {} # layer name to layer number mapping
import logging
logger = logging.getLogger('sivista_app')

@dataclass
class LayerProperties:
    Layers: Dict[str, Union[str, bool, int]] = field(default_factory=dict)
    LayerNumbers: Dict[str, str] = field(default_factory=dict)
    layer1000Pitch: int = 0
    layer1050Pitch: int = 0
    layer1000Spacing: int = 0
    InnerSpaceWidth: int = 0
    ViaExtension: float = 0
    layerExtension: float = 0
    gateSheetExtension: int = 0
    interconnectSheetExtension: int = 0
    via600SheetGap: int = 0
    InterconnectExtensionfromM0: float = 0
    GateExtensionfromM0: float = 0
    permLayers: List[int] = field(default_factory=list)
    stepSize: int = 0
    moveTogether: bool = False
    technology: str = 'cfet'
    flipped: str = 'R0'
    backside_power_rail: bool = True
    height_req: int = 1
    nanosheetWidth: int = 0
    vertical_gate_spacing: int = 0
    vertical_interconnect_spacing: int = 0
    np_spacing: int = 0
    io_pins: List[str] = field(default_factory=list)
    wireWidth: Dict[str, Union[str, bool, int]] = field(default_factory=dict)

    def update_from_dict(self, demo):
        for field in fields(self):
            field_name = field.name
            if field_name in demo:
                setattr(self, field_name, demo[field_name])

def is_ground_net(net: str) -> bool:
    """ Test if net is something like 'gnd' or 'vss'.
    """
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets

def is_supply_net(net: str) -> bool:
    """ Test if net is something like 'vcc' or 'vdd'.
    """
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets

def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)

class ProgressBar:
    def __init__(self, total_calls, bar_length=50):
        self.total_calls = total_calls
        self.bar_length = bar_length
        self.calls_completed = -1

    def update(self):
        self.calls_completed += 1
        progress = self.calls_completed# / self.total_calls
        arrow = '=' * int(round(self.bar_length * (progress/100)))
        spaces = ' ' * (self.bar_length - len(arrow))

        stdout.write(f'\r[{arrow + spaces}] {int(progress )}')
        stdout.flush()

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj
    
def usage(prog):
    logger.debug(f'Usage: {prog} <input_gds>')
    logger.debug('If no directory is provided, the current directory will be used.')

class Polygon:
    _id_counter = 1

    def __init__(self, datatype, XY, direction, layer, layer_props, isVia=False):
        self.id = f'polygon_{Polygon._id_counter}'
        Polygon._id_counter += 1
        self.layer_properties = layer_props
        self.type = "boundary"
        self.datatype = datatype
        self.viaLayerMap = None
        self.adjacencyList: Set[Polygon] = set()
        self.direction = direction
        self.layerMap = []
        self.layer = layer
        self.topPolygon = (layer in (self.layer_properties.permLayers + [self.layer_properties.LayerNumbers['BSPowerRail'], self.layer_properties.LayerNumbers['M1']]) and datatype == 0)
        self.textPolygons: Set[TextLabel] = set()
        self.connectedGate = None
        self.connectedInterconnect = None
        self.isVia = isVia
        if len(XY)!=10:
            logger.debug("XY coordinate dimension is incorrect.")
            exit(1)
        coords =  [[XY[0],XY[1]],
         [XY[2],XY[3]],
         [XY[4],XY[5]],
         [XY[6],XY[7]],
         [XY[0],XY[1]]]
        self.coord1 = coords[0]
        self.coord2 = coords[1]
        self.coord3 = coords[2]
        self.coord4 = coords[3]
        self.point = Point(coords)
        self.planarConnected = None
        self.planarConnectedPolygon = None
        self.bounds = None
        self.maxBounds = None
        self.layer_name = ""

    def updatePoint(self):
        self.point = Point([self.coord1,self.coord2,self.coord3,self.coord4,self.coord1])

    def updateCoords(self, point):
        self.coords = [[int(x), int(y)] for x, y in point.exterior.coords]
        self.coord1, self.coord2, self.coord3, self.coord4 = self.coords[0], self.coords[1], self.coords[2], self.coords[3]
        self.updatePoint()

    def extract_as_dict(self):
        element = {}
        element["id"] = self.id
        element["element"] = self.type
        element["datatype"] = self.datatype
        element["xy"] = [self.coord1, self.coord2, self.coord3, self.coord4, self.coord1]
        element["planarConnectedPolygon"] = self.planarConnectedPolygon.id if self.planarConnectedPolygon else None
        element["connectedGate"] = self.connectedGate.id if self.connectedGate else None
        element["connectedInterconnect"] = self.connectedInterconnect.id if self.connectedInterconnect else None
        element["adjacencyList"] = [p.id for p in self.adjacencyList]
        element["isVia"] = self.isVia
        element["layer_name"] = self.layer_name
        element["topPolygon"] = self.topPolygon
        element["layerMap"] = [p.id for p in self.layerMap]
        element["textPolygons"] = [text.id for text in self.textPolygons]
         #subtract planar connected from whole polygon(both planar and current) only when planar componenet is present
        if self.planarConnected:
            point_bounds = self.point.difference(self.planarConnected).bounds
            point_bounds = [int(x) for x in point_bounds]
            coords =  [ [point_bounds[0], point_bounds[1]],
                        [point_bounds[0], point_bounds[3]],
                        [point_bounds[2], point_bounds[3]],
                        [point_bounds[2], point_bounds[1]],
                         ]
            coord1, coord2, coord3, coord4 = coords[0], coords[1], coords[2], coords[3]
            element["xy"] = [coord1, coord2, coord3, coord4, coord1]
        return element
    
    def extract_as_text_dict(self):
        element = {}
        element["id"] = self.id
        element["type"] = self.type
        element["datatype"] = self.datatype
        element["xy"] = [self.coord1]
        element["presentation"] = self.presentation
        element["string"] = self.string
        return element
            
    def shiftPolygon(self, direction="",offset=0):
        # direction is vertical or horizontal to shift the polygon
        if direction=="H":
            self.coord1[0]+=offset
            self.coord2[0]+=offset 
            self.coord3[0]+=offset 
            self.coord4[0]+=offset 
        if direction=="V":
            self.coord1[1]+=offset
            self.coord2[1]+=offset 
            self.coord3[1]+=offset 
            self.coord4[1]+=offset 
        self.updatePoint()
    
    def cutPolygon(self, direction="", offset=0):
       
        #offset is negative if shape is reduced and it is positive if the shape is expanded
        if direction=="T":
            self.coord2[1]+=offset
            self.coord3[1]+=offset
        
        if direction=="B":
            self.coord1[1]-=offset
            self.coord4[1]-=offset
        
        if direction=="L":
            self.coord1[0]-=offset
            self.coord2[0]-=offset
        
        if direction=="R":
            self.coord3[0]+=offset
            self.coord4[0]+=offset
        self.updatePoint()
    
    def getWidth(self,direction):
        bounds = self.point.bounds
        if direction =='H':
            return bounds[3]-bounds[1]
        return bounds[2]-bounds[0]
    
    def updateCoordsFromBounds(self,point_bounds):
        point_bounds = [int(x) for x in point_bounds]
        coords =  [ [point_bounds[0], point_bounds[1]],
                   [point_bounds[0], point_bounds[3]],
                   [point_bounds[2], point_bounds[3]],
                   [point_bounds[2], point_bounds[1]],
        ]
        self.coord1 = coords[0]
        self.coord2 = coords[1]
        self.coord3 = coords[2]
        self.coord4 = coords[3]
        self.updatePoint()

    def setMaxBounds(self):
        self.maxBounds = self.point.bounds
    
    def addPlanarConnected(self,planar_point,planar_polygon):
            if self.planarConnected:
                return
            self.updateCoordsFromBounds(self.point.union(planar_point).bounds)
            self.planarConnected = planar_point
            self.planarConnectedPolygon = planar_polygon

class TextLabel:
    _id_counter = 1

    def __init__(self, datatype=0, XY=[], string="", presentation=0):
        self.id = f'text_{TextLabel._id_counter}'
        TextLabel._id_counter += 1
        self.type = "text"
        self.datatype = datatype
        self.presentation = presentation
        self.string  = string
        if len(XY)!=2:
            logger.debug("XY coordinate dimension is incorrect.")
            exit(1)
        self.coord1 = list(XY)
        self.point = Point([XY for _ in range(4)])
        

    def shiftPolygon(self, direction="",offset=0):
        if direction=="H":
            self.coord1[0]+=offset
        if direction=="V":
            self.coord1[1]+=offset
    
    def updateCoords(self, point):
        pass
    
    def extract_as_dict(self):
        element = {}
        element["element"] = self.type
        element["id"] = self.id
        element["datatype"] = self.datatype
        element["xy"] = [self.coord1]
        element["presentation"] = self.presentation
        element["text"] = self.string
        return element
            
class Layer:
    def __init__(self, layer,layer_properties, isVia=False):
      
        self.polygons : List[Polygon] = []
        self.labels = []
        self.direction = None
        self.width = None
        self.connector = None
        self.isVia = isVia
        self.layer = layer
        self.layer_properties = layer_properties
        self.hinder = self.layer_properties.Layers[str(self.layer)].get("hinder", None)
        self.layer_name = self.layer_properties.Layers[str(self.layer)]["Name"]
        if "width" in self.layer_properties.Layers[str(self.layer)]:
            self.width = self.layer_properties.Layers[str(self.layer)]["width"]
        if "direction" in self.layer_properties.Layers[str(self.layer)]:
            self.direction = self.layer_properties.Layers[str(self.layer)]["direction"]
        if "connector" in self.layer_properties.Layers[str(self.layer)]:
            self.connector = self.layer_properties.Layers[str(self.layer)]["connector"]
        self.planar_connection = self.layer_properties.Layers[str(self.layer)].get("planarConnections",None)
        self.backside_power_rail = self.layer_properties.backside_power_rail

    def addPolygon(self, datatype, XY):
        self.polygons.append(Polygon(datatype, XY, direction=self.direction, layer=self.layer, layer_props=self.layer_properties, isVia=self.isVia))
        #sort the polgon
    def sortPolygons(self):
        if self.direction == 'H':
            self.polygons.sort(key=lambda x: x.point.bounds[1])
        else:
            self.polygons.sort(key=lambda x: x.point.bounds[0]) # Sort with cmp
    def addTextLabel(self, datatype, XY, string, presentation):
        self.labels.append(TextLabel(datatype, XY, string, presentation))
    def mapTextLabels(self):
        for polygon in self.polygons:
            for textP in self.labels:
                if polygon.point.contains(textP.point):
                        polygon.textPolygons.add(textP)
                        
                    
    def checkWidth(self, update=False):
        if self.width:
            for polygon in self.polygons:
                if polygon.datatype==0:
                    if self.backside_power_rail or (not self.backside_power_rail and polygon.layer != int(self.layer_properties.LayerNumbers['M0'])):
                        #check if width is equal to the given parameter
                        if polygon.getWidth(self.direction) == self.width:
                            # logger.debug(f"Layer {self.layer} Width matches {self.width}")
                            continue
                        else:
                            logger.debug(f"Layer {self.layer} Width error: {polygon.getWidth(self.direction)} does not match {self.width} --- {polygon.point}---{polygon.point.bounds}")
                            if update:
                                self.width = polygon.getWidth(self.direction)
                                return True
                            return False
                    else:
                        # Condition to check layer 1000 polygons of topside power
                        for text in polygon.textPolygons:
                            text_dictionary = text.extract_as_dict()
                            # If polygon is a power/gnd net, it's width should be equal to power rail width
                            if is_power_net(text_dictionary['text']): 
                                #check if width is equal to the given parameter
                                if polygon.getWidth(self.direction) == self.layer_properties.Layers[self.layer_properties.LayerNumbers['BSPowerRail']]['width']:
                                    # logger.debug(f"Layer {self.layer} Width matches power rail width {self.layer_properties.Layers[self.layer_properties.LayerNumbers['BSPowerRail']]['width']}")
                                    continue
                                else:
                                    logger.debug(f"Layer {self.layer} Width error: {polygon.getWidth(self.direction)} does not match power rail width {self.layer_properties.Layers[self.layer_properties.LayerNumbers['BSPowerRail']]['width']} --- {polygon.point}---{polygon.point.bounds}")
                                    return False
                            else: 
                                # condition for 1000 polygons appart from power/gnd nets
                                if polygon.getWidth(self.direction) == self.width:
                                    # logger.debug(f"Layer {self.layer} Width matches {self.width}")
                                    continue
                                else:
                                    logger.debug(f"Layer {self.layer} Width error: {polygon.getWidth(self.direction)} does not match {self.width} --- {polygon.point}---{polygon.point.bounds}")
                                    if update:
                                        self.width = polygon.getWidth(self.direction)
                                        return True
                                    return False
        return True
    
    def checkconnection(self):
        for layer1Polygon in self.polygons:
            if layer1Polygon.datatype==0:
                for layer2Polygon in layer1Polygon.layerMap:
                    if not layer1Polygon.point.intersects(layer2Polygon.point): 
                        if layer1Polygon.planarConnected and not layer1Polygon.planarConnected.intersects(layer2Polygon.point):
                            logger.debug(f"Layer connection check Failed for {layer1Polygon.layer} and {layer2Polygon.layer}")
                            return False
                        return True
        return True

class PermutationEngine:

    def __init__(self,gds_file,layer_map_dir):
        global layerNumber
        #shortlisting data  
        with open(gds_file, "rb") as f:
            gds_data = gds_read(f)
        self.bgnlibTime = gds_data["timestamp"]
        self.libname = gds_data["name"]
        self.units = gds_data["units"]
        self.bgnstrTime = gds_data["structures"][0]["timestamp"]
        self.strname = gds_data["structures"][0]["name"]
        data = gds_data["structures"][0]
        self.scaleH = round(self.units[0]*(10**9),4)
        self.scaleV = round(self.units[1]*(10**9),4)
        logger.debug(self.scaleV)
        self.base_layout_name = gds_file
        #rewrite the width information in config
        logger.debug("Adjusting scales")              
        self.outputCount = 1
        self.drc_clean_count = 0
        self.lvs_clean_count = 0
        layer_number_dictionary = {}
        self.layer_properties = self.getLayerProperties(gds_file,layer_map_dir)

        for k,v in self.layer_properties.Layers.items():
            if "width" in v:
                self.layer_properties.Layers[k]["width"] = int(self.layer_properties.Layers[k]["width"]/self.scaleV)           
            layer_number_dictionary[v.get('Name', '')] = k

        self.layer_properties.layer1000Pitch = int(self.layer_properties.layer1000Pitch/self.scaleV)
        self.layer_properties.layer1050Pitch = int(self.layer_properties.layer1050Pitch/self.scaleH)
        self.layer_properties.InnerSpaceWidth = int(self.layer_properties.InnerSpaceWidth/self.scaleV)
        self.layer_properties.ViaExtension = int(self.layer_properties.ViaExtension/self.scaleV)
        self.layer_properties.stepSize = int(self.layer_properties.stepSize/self.scaleV)
        self.layer_properties.layerExtension = int(self.layer_properties.layerExtension/self.scaleV) 
        self.layer_properties.gateSheetExtension = int(self.layer_properties.gateSheetExtension/self.scaleV)
        self.layer_properties.interconnectSheetExtension = int(self.layer_properties.interconnectSheetExtension/self.scaleV)
        self.layer_properties.via600SheetGap = int(self.layer_properties.via600SheetGap/self.scaleV)
        self.layer_properties.InterconnectExtensionfromM0 = int(self.layer_properties.InterconnectExtensionfromM0/self.scaleV) 
        self.layer_properties.GateExtensionfromM0 = int(self.layer_properties.GateExtensionfromM0/self.scaleV)
        self.layer_properties.nanosheetWidth = int(self.layer_properties.nanosheetWidth/self.scaleV)
        self.layer_properties.vertical_interconnect_spacing = int(self.layer_properties.vertical_interconnect_spacing/self.scaleV)
        self.layer_properties.vertical_gate_spacing = int(self.layer_properties.vertical_gate_spacing/self.scaleV)
        self.layer_properties.np_spacing = int(self.layer_properties.np_spacing/self.scaleV)
        for w in self.layer_properties.wireWidth:
            self.layer_properties.wireWidth[w] = int(self.layer_properties.wireWidth[w]/self.scaleV)
        self.layer_properties.LayerNumbers = layer_number_dictionary
        self.technology = self.layer_properties.technology
        self.flipped = self.layer_properties.flipped
        self.backside_power_rail = self.layer_properties.backside_power_rail
        self.height_req = self.layer_properties.height_req
        drc_checker = {
            'gaa': GAADoubleHeightDesignRuleCheck,
        }
        k = 10
        while not k//self.layer_properties.stepSize:
            k = k*10
        self.layer_properties.stepFactor = k
        self.layerMap : Dict[int, Layer]= {}
        for k,v in self.layer_properties.Layers.items():
            self.layerMap[int(k)] = Layer(int(k),self.layer_properties ,'connector' in v.keys())
            if v['Name'] != 'Unused_Component': layerNumber[v["Name"]] = int(k)
        self.globalBoundary = [float('inf'),float('inf'),float('-inf'),float('-inf')]
        for element in data["elements"]:
            if self.technology == "finfet" or layerNumber.get("Nwell") != element["layer"]:
                elemClass = self.getLayerObject(element["layer"])
                if element["element"] == "boundary" and element["datatype"] != 2:
                    elemClass.addPolygon(datatype=element["datatype"], XY = [item for sublist in element["xy"] for item in sublist])
                if element["element"] == "text" and element["datatype"] != 3:
                    elemClass.addTextLabel(datatype=element["datatype"], XY=element["xy"][0], string=element["text"], presentation=1)
        for l,lc in self.layerMap.items():
            lc.sortPolygons()
        for l,lc in self.layerMap.items():
            for polygon in lc.polygons:
                bounds = polygon.point.bounds
                if l == layerNumber["Boundary"]:
                    self.globalBoundary[0] = bounds[0]
                    self.globalBoundary[1] = bounds[1]
                    self.globalBoundary[2] = bounds[2]
                    self.globalBoundary[3] = bounds[3]
                else:
                    self.globalBoundary[0] = min(self.globalBoundary[0], bounds[0])
                    self.globalBoundary[1] = min(self.globalBoundary[1], bounds[1])
                    self.globalBoundary[2] = max(self.globalBoundary[2], bounds[2])
                    self.globalBoundary[3] = max(self.globalBoundary[3], bounds[3])
                polygon.layer_name = self.layer_properties.Layers[str(polygon.layer)]["Name"]
       
        self.globalBoundary = [int(x) for x in self.globalBoundary]
        self.io_pins = self.layer_properties.io_pins
        self.getSubcellYBounds()
        self.tech = None
        self.drc  = drc_checker[self.technology](self.layerMap,self.layer_properties, layerNumber, self.y_min, self.y_mid, self.y_max)
        self.drc.checkDummyislands(layerNumber["VIA_Inteconnect_BSPowerRail"], layerNumber["PMOSInterconnect"], layerNumber["NMOSInterconnect"]) 
        self.mapconnectedGates(layerNumber["PMOSGate"], layerNumber["NMOSGate"])  
        self.mapInterconnectConnections(layerNumber["PMOSInterconnect"], layerNumber["NMOSInterconnect"], layerNumber["VIA_PMOSInterconnect_NMOSInterconnect"])
        
        for l,viaClass in self.layerMap.items():
            if viaClass.connector:
                for via in viaClass.polygons:
                    via.layerMap = []
                    found = False
                    for connector in viaClass.connector:                
                        layer1,layer2 = connector
                        for  polygon in self.layerMap[layer1].polygons:
                            if polygon.datatype==0  and polygon.point.intersects(via.point):
                                via.layerMap.append(polygon)
                                polygon.layerMap.append(via)
                                via.adjacencyList.add(polygon)
                                polygon.adjacencyList.add(via)
                                for  polygon2 in self.layerMap[layer2].polygons:
                                    if polygon2.datatype==0 and polygon2.point.intersects(via.point):
                                        via.layerMap.append(polygon2)
                                        polygon2.layerMap.append(via)
                                        via.adjacencyList.add(polygon2)
                                        polygon2.adjacencyList.add(via)
                                        #appending polygons to each layer
                                        polygon2.layerMap.append(polygon)
                                        polygon.layerMap.append(polygon2)
                                        found = True
                                        break
                                if found:
                                    break
                            if found:
                                break
                    via.layerMap = list(set(via.layerMap))       

        self.mapPlanarConnection()                
        self.layerMap[layerNumber['M0']].mapTextLabels()        
        self.layerMap[layerNumber['M1']].mapTextLabels()
        self.layerMap[layerNumber['BSPowerRail']].mapTextLabels()
        self.addLayerBounds()
        self.drc.set_layerMap(self.layerMap)
        self.summary_report = []
    
    def initialize_lvs_client(self, netlist_path: str, file_name: str, cell_name: str, tech: str, output_folder: str, batch_size: int = 50, limiter=None):
        if limiter:
            batch_size = limiter
        self.lvs_client = LVSClientHandler(self.layer_properties, file_name, batch_size, netlist_path, cell_name, tech, output_folder, limiter=limiter)

    def getSubcellYBounds(self):
        y_min, y_max = sorted((self.globalBoundary[1],
                            self.globalBoundary[3]))
        mid = (y_min + y_max) / 2
        self.y_min = self.globalBoundary[1]
        self.y_mid = mid
        self.y_max = self.globalBoundary[3] 

    def getLayerObject(self, layer):
      layer_object = self.layerMap.get(layer, None)
      if layer_object is None:
          logger.error(f"Layer {layer} not found in layerMap")
      return layer_object
    
    def getLayerProperties(self,gds_file,layer_map_dir):
        original_fileName = os.path.basename(gds_file).replace('.gds','')       
        base_fileName = original_fileName
        tokens = original_fileName.split('_')
        if len(tokens) > 1 and tokens[-1].isdigit():
            if tokens[-2].isdigit():
                base_fileName = '_'.join(tokens[:-1])
        layer_properties = LayerProperties()
        fileName =f"{layer_map_dir}/layerMap{base_fileName}.json" 
        if isfile(layer_map_dir):
            fileName = layer_map_dir  
        try: 
            with open(fileName) as f:
                    layer_properties.update_from_dict(load(f))
                    layer_properties.moveTogether = True         
        except Exception as e:     
            
            logger.error(f"Error loading layer_properties for {fileName}: {str(e)}")
        return layer_properties

    def remove_power_ground_polygons(self, polygons_to_permutate):
        polygons_to_remove = []
        for polygon in polygons_to_permutate:
            for text in polygon.textPolygons:
                text_dictionary = text.extract_as_dict()
                if is_power_net(text_dictionary['text']): 
                    element = polygon.extract_as_dict()
                    polygons_to_remove.append(polygon)
        return [polygon for polygon in polygons_to_permutate if polygon not in polygons_to_remove]

    def mapconnectedGates(self, layer1, layer2):
        for polygon1 in self.layerMap[layer1].polygons:
            for polygon2 in self.layerMap[layer2].polygons:
                if polygon1.point.equals(polygon2.point):
                    polygon1.connectedGate = polygon2
                    polygon2.connectedGate = polygon1
    
    def mapInterconnectConnections(self, layer1, layer2, via_layer):
        for polygon1 in self.layerMap[layer1].polygons:
            for polygon2 in self.layerMap[layer2].polygons:
                if polygon1.point.intersects(polygon2.point):
                    for via in self.layerMap[via_layer].polygons:
                        if via.point.intersects(polygon1.point) and via.point.intersects(polygon2.point):
                            polygon1.connectedInterconnect = polygon2
                            polygon2.connectedInterconnect = polygon1

    def mapPlanarConnection(self):
        for l,layerObj in self.layerMap.items():
            if layerObj.planar_connection:
                    logger.debug(f" class has planar connection - layer {layerObj.layer}")
                    for layer1_polygon in layerObj.polygons:
                        for planar_connector in layerObj.planar_connection:
                            #do we need to add error checks for if theres layers ecist:
                            for layer2_polygon in self.layerMap[planar_connector].polygons:
                                if layer2_polygon.point.touches(layer1_polygon.point):
                                    layer1Point = layer1_polygon.point
                                    layer2Point = layer2_polygon.point
                                    layer_2_polygon_copy = layer2_polygon
                                    layer_1_polygon_copy = layer1_polygon
                                    layer1_polygon.addPlanarConnected(layer2Point,layer_2_polygon_copy)
                                    layer2_polygon.addPlanarConnected(layer1Point,layer_1_polygon_copy) 
                                    layer1_polygon.layerMap.append(layer2_polygon)
                                    layer2_polygon.layerMap.append(layer1_polygon)
                                    logger.debug(f"planar connection found between layer1 {layer1_polygon.layer} and layer2 {layer2_polygon.layer}")
                                    break  
    def addLayerBounds(self):
         #adding bounds to restrict going beyong those bounds
         for l,layerObj in self.layerMap.items():
            technology = {'gaa': ["PMOSGate", "PMOSInterconnect", "NMOSGate", "NMOSInterconnect"],
                          'cfet': ["PMOSGate", "PMOSInterconnect", "NMOSGate", "NMOSInterconnect"],
                          'finfet': ["PMOSGate", "PMOSInterconnect", "NMOSGate", "NMOSInterconnect"]}
            if layerObj.layer_name in technology[self.technology]:
                for polygon in layerObj.polygons:
                    polygon.setMaxBounds()            
                
    def duplicatelayer(self, layer, datatype, elements):
        for polygon in self.layerMap[layer].polygons:
            element = polygon.extract_as_dict()
            element["id"] = f'{element["id"]}_dup'
            element["layer"] = layer
            element["datatype"] = datatype
            elements.append(element)
    
    def duplicateText(self, layer, datatype, elements):
        tmp_list = []
        for elem in elements:
            if 'datatype' in elem.keys() and elem["layer"] == layer and elem['datatype'] == 1:
                tmp_list.append(dict(elem))
        for tmp_elem in tmp_list:
            tmp_elem['datatype'] = datatype
            tmp_elem["id"] = f'{tmp_elem["id"]}_dup'
            elements.append(tmp_elem)

    def extendLayer(self, layer, result, elements):
        layer, datatype = layer
        for polygon in self.layerMap[layer].polygons:
            new_bounds = list(polygon.point.bounds)
            new_bounds[1], new_bounds[3] = self.globalBoundary[1], self.globalBoundary[3]
            new_bounds = [int(x) for x in new_bounds]
            min_x,min_y,max_x, max_y = new_bounds         
            coords =  [
                [min_x, min_y],
                [max_x, min_y],
                [max_x, max_y],
                [min_x, max_y],
                [min_x, min_y]
            ]
            element = polygon.extract_as_dict()         
            element["layer"] = result[0]
            element["datatype"] = result[1]
            element['xy'] = coords
            element["id"] = f'{element["id"]}_ext'
            element["planarConnectedPolygon"] = None
            element["connectedGate"] = None
            element["connectedInterconnect"] = None
            element["adjacencyList"] = []
            element["isVia"] = polygon.isVia
            element["layer_name"] = polygon.layer_name  
            elements.append(element)
    
    def addPatternCut(self, layer, datatype, elements, extraLayer = None):
        region = []
        gloablX_max = float('-inf')
        gloablX_min = float('inf')
        for polygon in self.layerMap[layer].polygons:
            # Initialize min and max Y
            min_y = float('inf')
            max_y = float('-inf')
            min_x = float('inf')
            max_x = float('-inf')
            # Iterate over the points of the polygon
            for x, y in polygon.point.exterior.coords:
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                min_x = min(min_x, x)
                max_x = max(max_x, x)         
            min_x -= (self.layer_properties.InnerSpaceWidth + self.layer_properties.Layers[str(layerNumber["NMOSInterconnect"])]['width']//2)
            max_x += (self.layer_properties.InnerSpaceWidth + self.layer_properties.Layers[str(layerNumber["NMOSInterconnect"])]['width']//2)
            gloablX_max = max(gloablX_max, max_x)
            gloablX_min = min(gloablX_min, min_x)
            if self.is_top_subcell(polygon):
                bounds1 = (min_x,self.y_mid, max_x, min_y)
                bounds2 = (min_x,self.y_max, max_x, max_y) 
            else:
                bounds1 = (min_x,self.y_min, max_x, min_y)
                bounds2 = (min_x,self.y_mid, max_x, max_y) 
            bounds1 = (min_x,self.globalBoundary[1], max_x, min_y)
            bounds2 = (min_x,self.globalBoundary[3], max_x, max_y)            
            rectangle1 = box(*bounds1)
            rectangle2 = box(*bounds2)
            region.append(rectangle1)
            region.append(rectangle2)
            
          
        # Merge all boxes (equivalent to region.merge())
        merged_region = unary_union(region)

        # Handle both single Polygon and MultiPolygon
        if merged_region.geom_type == 'Polygon':
            polygons = [merged_region]
        elif merged_region.geom_type == 'MultiPolygon':
            polygons = list(merged_region.geoms)
        else:
            polygons = []

        # Convert polygons to element format
        for poly in polygons:
            coords = list(poly.exterior.coords)
            polygon_points = [[int(coord[0]), int(coord[1])] for coord in coords]

            # Append starting point at the end if not already closed (just in case)
            if coords[0] != coords[-1]:
                polygon_points.append([int(coords[0][0]), int(coords[0][1])])

            elements.append({
                'element': 'boundary',
                'layer': layer,
                'datatype': datatype,
                'xy': polygon_points,
                'id': f'{polygon.id}_cut_1',
                'planarConnected': None,
                'connectedGate': None,
                'connectedInterconnect': None,
                'connections': []
            })

        # Create left boundary polygon
        lBounds = list(self.globalBoundary)
        lBounds[2] = gloablX_min
        left_box = box(*lBounds)
        polygon_points = [[int(pt[0]), int(pt[1])] for pt in list(left_box.exterior.coords)]

        elements.append({
            'element': 'boundary',
            'layer': layer,
            'datatype': datatype,
            'xy': polygon_points,
            'id': f'{polygon.id}_cut_2',
            'planarConnected': None,
            'connectedGate': None,
            'connectedInterconnect': None,
            'connections': []
        })

        # Create right boundary polygon
        rBounds = list(self.globalBoundary)
        rBounds[0] = gloablX_max
        right_box = box(*rBounds)
        polygon_points = [[int(pt[0]), int(pt[1])] for pt in list(right_box.exterior.coords)]

        elements.append({
            'element': 'boundary',
            'layer': layer,
            'datatype': datatype,
            'xy': polygon_points,
            'id': f'{polygon.id}_cut_3',
            'planarConnected': None,
            'connectedGate': None,
            'connectedInterconnect': None,
            'connections': []
        })

    def create_metal_pins(self, layer, datatype, texttype, elements):
        for polygon in self.layerMap[layer].polygons:
            for text in polygon.textPolygons:
                text_dictionary = text.extract_as_dict()
                if text_dictionary['text'] in self.io_pins or (not self.backside_power_rail and is_power_net(text_dictionary['text'])): 
                    element = polygon.extract_as_dict()
                    element["id"] = f'{element["id"]}_pin'
                    element["layer"] = layer
                    element["datatype"] = datatype
                    element["adjacencyList"] = [p.id for p in polygon.adjacencyList]
                    element["topPolygon"] = False
                    elements.append(element)
                    element_txt = text.extract_as_dict()
                    element_txt["id"] = f'{element_txt["id"]}_pin'
                    element_txt["layer"] = layer
                    element_txt["datatype"] = texttype
                    element_txt["adjacencyList"] = [p.id for p in polygon.adjacencyList]
                    element_txt["isVia"] = polygon.isVia
                    elements.append(element_txt)

    def combineLayer(self, src, dest, elements):
        srcLayer, srcDatatype = src
        destLayer, destDatatype = dest 
        for polygon in self.layerMap[srcLayer].polygons:
            if polygon.datatype == srcDatatype:
                element = polygon.extract_as_dict()
                element["id"] = f'{element["id"]}_combine'
                element["layer"] = destLayer
                element["datatype"] = destDatatype
                element["adjacencyList"] = []
                element["isVia"] = polygon.isVia
                elements.append(element)
    
    def is_bottom_subcell(self, component):
        """True if the component lies entirely in the lower half of the global Y-range."""
        # sort so we know which is min/max
        low, high = self.y_min, self.y_mid
        y1, y2 = component.point.bounds[1], component.point.bounds[3]
        return (low <= y1 <= high) and (low <= y2 <= high)

    def is_top_subcell(self, component):
        """True if the component lies entirely in the upper half of the global Y-range."""
        low, high = self.y_mid, self.y_max
        y1, y2 = component.point.bounds[1], component.point.bounds[3]
        return (low <= y1 <= high) and (low <= y2 <= high)

    def getOptimizedBounds(self, component):
        if self.is_bottom_subcell(component=component):
            component_top = self.y_mid
            component_bottom = self.y_min
            subcell_flag = 'bottom'
        elif self.is_top_subcell(component=component):
            component_top = self.y_max
            component_bottom = self.y_mid
            subcell_flag = 'top'
        else:
            component_top = self.y_max
            component_bottom = self.y_min
            # print(f'layer both: {component.layer_name}')
            subcell_flag = 'both'

        nanosheet = None

        component_extenstion = self.layer_properties.gateSheetExtension if component.layer in [layerNumber["PMOSGate"], layerNumber["NMOSGate"]] else  self.layer_properties.interconnectSheetExtension if component.layer in [layerNumber["NMOSInterconnect"],layerNumber["PMOSInterconnect"]] else 0
        if self.layerMap[component.layer].layer_name.startswith("NMOS"):
            nanosheet = "NmosNanoSheet"
        elif self.layerMap[component.layer].layer_name.startswith("PMOS"):
            nanosheet = "PmosNanoSheet"
        if nanosheet:
            for sheet_polygon in self.layerMap[layerNumber[nanosheet]].polygons:
                if self.is_bottom_subcell(sheet_polygon) and subcell_flag == 'bottom':
                    nanosheet_bounds = sheet_polygon.point.bounds
                    component_top = max(nanosheet_bounds[1], nanosheet_bounds[3]) + component_extenstion
                    component_bottom = min(nanosheet_bounds[1], nanosheet_bounds[3]) - component_extenstion
                elif self.is_top_subcell(sheet_polygon) and subcell_flag == 'top':
                    nanosheet_bounds = sheet_polygon.point.bounds
                    component_top = max(nanosheet_bounds[1], nanosheet_bounds[3]) + component_extenstion
                    component_bottom = min(nanosheet_bounds[1], nanosheet_bounds[3]) - component_extenstion
                elif self.is_bottom_subcell(sheet_polygon) and subcell_flag == 'both':
                    nanosheet_bounds = sheet_polygon.point.bounds
                    component_bottom = min(nanosheet_bounds[1], nanosheet_bounds[3]) - component_extenstion
                elif self.is_top_subcell(sheet_polygon) and subcell_flag == 'both':
                    nanosheet_bounds = sheet_polygon.point.bounds
                    component_top = max(nanosheet_bounds[1], nanosheet_bounds[3]) + component_extenstion

        for via in component.layerMap:
            if via.isVia:
                # print(f'via.layer_name: {via.layer_name}')
                if subcell_flag == 'both' and self.is_bottom_subcell(via): 
                    via_bounds = via.point.bounds
                    if via.layer_name == "VIA_M0_M1":   # handles multiple via0 in single x axis
                        if component_bottom == self.y_min:
                            component_bottom = max(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                        else:
                            component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                    else:
                        component_bottom = min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension 
                elif subcell_flag == 'both' and self.is_top_subcell(via):
                    via_bounds = via.point.bounds
                    if via.layer_name == "VIA_M0_M1": # handles multiple via0 in single x axis
                        if component_top == self.y_max:
                            component_top = min(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        else:
                            component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                    else:
                        component_top = max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension
                elif subcell_flag == 'both' and not self.is_top_subcell(via) and not self.is_bottom_subcell(via):
                    # Handles pviat for VDD connections
                    pass
                else:
                    via_bounds = via.point.bounds
                    if self.is_bottom_subcell(via):
                        # handles via0 in same subcell m1 height
                        if component_top == self.y_mid:
                            component_top = min(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        else:
                            component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        if component_bottom == self.y_min:
                            component_bottom = max(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                        else:
                            component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                    elif self.is_top_subcell(via):
                        # handles via0 in same subcell m1 height
                        if component_top == self.y_max:
                            component_top = min(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        else:
                            component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        if component_bottom == self.y_mid:
                            component_bottom = max(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                        else:
                            component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension)
                    else:
                        component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension )
                    
        
        if component.planarConnected:
            for via in component.planarConnectedPolygon.layerMap:
                if via.isVia:
                    if self.is_bottom_subcell(via) and subcell_flag == 'bottom':
                        via_bounds = via.point.bounds   
                        component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension )
                    elif self.is_top_subcell(via) and subcell_flag == 'top': 
                        via_bounds = via.point.bounds
                        component_top = max(component_top, max(via_bounds[1], via_bounds[3]) + self.layer_properties.ViaExtension)
                        component_bottom = min(component_bottom, min(via_bounds[1], via_bounds[3])-self.layer_properties.ViaExtension )
                    
            if subcell_flag == 'bottom':
                if component.layer in [layerNumber["PMOSGate"],layerNumber['PMOSInterconnect']]:
                    component_bottom = min(component.planarConnected.bounds[1],component.planarConnected.bounds[3])
                if component.layer in [layerNumber["NMOSGate"],layerNumber['NMOSInterconnect']]:
                    component_top = max(component.planarConnected.bounds[1],component.planarConnected.bounds[3])   
            elif subcell_flag == 'top':
                if component.layer in [layerNumber["PMOSGate"],layerNumber['PMOSInterconnect']]:
                    component_top = max(component.planarConnected.bounds[1],component.planarConnected.bounds[3])       
                if component.layer in [layerNumber["NMOSGate"],layerNumber['NMOSInterconnect']]:
                    component_bottom = min(component.planarConnected.bounds[1],component.planarConnected.bounds[3])                

        else:
            if component.maxBounds:
                # if subcell_flag == 'both':
                #     pass
                # else:
                    component_top = min(component_top, max(component.maxBounds[1], component.maxBounds[3]))
                    component_bottom = max(component_bottom, min(component.maxBounds[1], component.maxBounds[3]))

        new_bounds = list(component.point.bounds)
        new_bounds[1] = component_bottom
        new_bounds[3] = component_top
        new_bounds = [int(x) for x in new_bounds]
        min_x,min_y,max_x, max_y = new_bounds        
        coords =  [
            [min_x, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [min_x, max_y],
            [min_x, min_y]
        ]       
        return Point(coords)
    
    def optimizeLayers(self, layer):
        changes = dict()    
        for polygon in self.layerMap[layer].polygons:   
            # for textPolygon in polygon.textPolygons:
            #     print(f'metal label: {textPolygon.string}')        
            for comp in polygon.layerMap:
                if not comp.isVia and comp.layer!=layer:                   
                    if comp not in changes:
                        changes[comp] = comp.point
                        comp.updateCoords(self.getOptimizedBounds(comp))
                    if comp.connectedGate:                      
                        if comp.connectedGate not in changes:
                            changes[comp.connectedGate] = comp.connectedGate.point
                            comp.connectedGate.updateCoords(comp.point)
                    if comp.planarConnected:                      
                        if comp.planarConnected not in changes:
                            changes[comp.planarConnectedPolygon] = comp.planarConnectedPolygon.point
                            comp.planarConnectedPolygon.updateCoords(self.getOptimizedBounds(comp.planarConnectedPolygon))
                    for connectedComponent in comp.layerMap:
                        if not connectedComponent.isVia and connectedComponent.layer!=layer and connectedComponent not in changes:                          
                            changes[connectedComponent] = connectedComponent.point
                            connectedComponent.updateCoords(self.getOptimizedBounds(connectedComponent))
        for layerName in ["NMOSGate", "PMOSGate", "NMOSInterconnect", "PMOSInterconnect"]:
            for comp in self.layerMap[layerNumber[layerName]].polygons:
                if comp.datatype==0 and comp not in changes:
                    changes[comp] = comp.point
                    comp.updateCoords(self.getOptimizedBounds(comp))   
        return changes
    
    def post_processing(self, elements):
        self.duplicatelayer(layerNumber["NmosNanoSheet"], 1, elements)
        self.duplicatelayer(layerNumber["PmosNanoSheet"], 1, elements)
        self.duplicatelayer(layerNumber["BSPowerRail"], 2, elements)
        self.duplicateText(layerNumber["BSPowerRail"], 3, elements)
        self.extendLayer((layerNumber["NMOSGate"], 0),(layerNumber["NMOSGate"], 1), elements)
        self.extendLayer((layerNumber["PMOSGate"], 0),(layerNumber["PMOSGate"],1), elements)
        self.extendLayer((layerNumber["Diffusion_Break"], 0),(layerNumber["NMOSGate"], 1), elements)
        self.extendLayer((layerNumber["Diffusion_Break"], 1),(layerNumber["PMOSGate"],1), elements)
        self.addPatternCut(layerNumber["NMOSGate"], 2, elements)
        self.addPatternCut(layerNumber["PMOSGate"], 2, elements)      
        self.combineLayer((layerNumber["NMOSInterconnect"],3) , (layerNumber["NMOSInterconnect"],0), elements)
        self.create_metal_pins(layerNumber["M0"], 2, 3, elements)
        self.create_metal_pins(layerNumber["M1"], 2, 3, elements)
               
    def convert_to_json(self):
        retData = {}
        retData["version"] = 600
        elements = []
        for layer, layerClass in self.layerMap.items():
            for polygon in layerClass.polygons:
                element = polygon.extract_as_dict()
                element["layer"] = layer
                elements.append(element)
            for labels in layerClass.labels:
                element = labels.extract_as_dict()
                element["layer"] = layer
                element["strans"] = 32768
                element["text"] = element["text"].upper()
                elements.append(element)
        self.post_processing(elements)
        retData["timestamp"] = self.bgnstrTime
        retData["name"] = self.libname
        retData["units"] = self.units
        retData["structures"] = []
        structures = {
            "timestamp": self.bgnstrTime,
            "name": self.strname,
            "elements": elements
        }
        retData["structures"].append(structures)
        retData["base_layout_name"] = self.base_layout_name
        return retData

    def checkBoundary(self, polygon):
        bounds = polygon.bounds
        if self.globalBoundary[0]<=bounds[0] and self.globalBoundary[1]<=bounds[1] and self.globalBoundary[2]>=bounds[2] and self.globalBoundary[3]>=bounds[3]:
            return True
        return False
    
    def generatePermutationHelper(self):    
        changes = self.optimizeLayers(layerNumber['M0'])
        if self.drc.checkDRC():
            self.drc_clean_count+=1
            newgdsJson = self.convert_to_json()
            for boundary in self.layerMap[layerNumber["Boundary"]].polygons:
                #fixing the bounding box
                boundary.coord1[1] = self.globalBoundary[1]
                boundary.coord2[1] = self.globalBoundary[3]
                boundary.coord3[1] = self.globalBoundary[3]
                boundary.coord4[1] = self.globalBoundary[1]
                boundary.updatePoint()

            self.lvs_client.add_gds_json(key=f'{self.drc_clean_count}', gds_json=deepcopy(newgdsJson))

        for component, point in changes.items():
            component.updateCoords(point)
        return 
     
    
    def optimizeGDS(self):
        self.lvs_client.suffix = False
        self.optimizeLayers(layerNumber['M0'])
        if self.drc.checkDRC():
            self.drc_clean_count+=1
            newgdsJson = self.convert_to_json()
            self.lvs_client.add_gds_json(key=f'{self.drc_clean_count}', gds_json=deepcopy(newgdsJson))
            self.lvs_client.run()


    def generatePermutations(self, polygons_to_permutate, limiter):
        direction = 'V'
        track_centers = [track_polygon.point.centroid.y for track_polygon in self.layerMap[layerNumber['HorizontalTracks']].polygons]
        clashes_with = defaultdict(list)
        track_restrictions = defaultdict(list)

        def create_valid_permutation(position_set):
            for i, pos in enumerate(position_set):
                connector = polygons_to_permutate[i]
                vias = set()
                for polygon in connector.layerMap:
                    if polygon.isVia:
                        vias.add(polygon)
                center_y = track_centers[pos]
                step = int(center_y - connector.point.centroid.y)
                for via in vias:
                    via.shiftPolygon(direction=direction, offset=step)
                connector.shiftPolygon(direction=direction, offset=step)
                for textPolygon in connector.textPolygons:
                    textPolygon.shiftPolygon(direction=direction, offset=step)
            if limiter and self.lvs_client.lvs_clean_count >= limiter:
                return
            self.generatePermutationHelper()

        def find_valid_permutations(num_tracks, num_metals, clashes_with, limit=1000000):
            valid_permutations = set()
            current_assignment = [-1] * num_metals  # Track assignments for metals
            def backtrack(metal):
                if limiter and self.outputCount>limiter:
                    logger.debug(f'{limiter} files have been generated.')
                    return
                if len(valid_permutations) >= limit:
                    return
                if metal == num_metals:
                    if tuple(current_assignment) not in valid_permutations:
                        logger.debug(f"Testing valid permutation: {current_assignment}")
                        create_valid_permutation(current_assignment)
                    valid_permutations.add(tuple(current_assignment))
                    return
                for track in range(num_tracks):
                    # Skip tracks restricted for this metal
                    if track in track_restrictions.get(metal, []):
                        continue

                    clash_list = clashes_with.get(metal, [])
                    if all(
                        current_assignment[m] != track or m not in clash_list
                        for m in range(metal)
                    ):
                        current_assignment[metal] = track
                        backtrack(metal + 1)
                        current_assignment[metal] = -1  # Reset for next iteration
            backtrack(0)
            return len(valid_permutations)

        def get_planarConnected_flag(metal):
            """return True if for the given metal, there exists polygons associated with M0 that are not planar connected
            return False (all polygons associated with M0 are planar connected)"""
            vias = set()
            planar_connected_poly = set()
            non_planar_connected_poly = set()
            for polygon in metal.layerMap:
                if polygon.isVia:
                    vias.add(polygon.point)
                elif polygon.planarConnected:
                    planar_connected_poly.add(polygon.point)
                elif not polygon.planarConnected:
                    non_planar_connected_poly.add(polygon.layer)
            return len(vias) != len(planar_connected_poly), non_planar_connected_poly
        
        def calculate_restricted_tracks(non_planar_layers, num_tracks, subcell_location):
            """Calculates restricted tracks based on orientation and PMOS/NMOS zone"""
            # Create the full range
            full_range = list(range(num_tracks))

            # Split into top and bottom halves
            midpoint = num_tracks // 2
            bottom = full_range[:midpoint]   # [0, 1, 2, 3, 4]
            top = full_range[midpoint:]      # [5, 6, 7, 8, 9]

            # Further split each into upper and lower halves
            def split_half(half):
                n = len(half)
                if n == 1:
                    return [], []
                elif n == 2:
                    return [half[1]], [half[0]]
                else:
                    mid = n // 2
                    if n % 2 == 0:
                        lower_half = half[:mid]
                        upper_half = half[mid:]
                    else:
                        lower_half = half[:mid]
                        upper_half = half[mid+1:]
                    return upper_half, lower_half

            top_upper_half, top_lower_half = split_half(top)
            bottom_upper_half, bottom_lower_half = split_half(bottom)
            restriction = None
            for layer in non_planar_layers:
                # Creating restrictions based on PMOS/NMOS zone
                if layer in [layerNumber["PMOSGate"],layerNumber['PMOSInterconnect']]:
                    restriction = 'PMOS'
                if layer in [layerNumber["NMOSGate"],layerNumber['NMOSInterconnect']]:
                    restriction = 'NMOS'

            if subcell_location == 'top':
                if restriction == 'PMOS': return top_upper_half
                elif restriction == 'NMOS': return top_lower_half
            elif subcell_location == 'bottom':
                if restriction == 'PMOS': return bottom_lower_half
                elif restriction == 'NMOS': return bottom_upper_half

            return []

        for i in range(len(polygons_to_permutate)):
            metal_i = polygons_to_permutate[i]
            # for textPolygon in metal_i.textPolygons:
            #     print(f'metal label: {textPolygon.string}')
            metal_i_boundsx = [metal_i.coord1[0], metal_i.coord4[0]]
            if metal_i.coord1[1] < self.y_mid: # if polygon in bottom subcell
                subcell_location = 'bottom'
            else: # if polygon in top subcell
                subcell_location = 'top'
            clashes = []
            for j in range(len(polygons_to_permutate)):
                if i == j:
                    continue
                metal_j = polygons_to_permutate[j]
                metal_j_boundsx = [metal_j.coord1[0], metal_j.coord4[0]]
                if max(metal_i_boundsx[0], metal_j_boundsx[0]) <= min(metal_i_boundsx[1], metal_j_boundsx[1]):  # Clashes due to overlap of M0
                    clashes.append(j)
                elif metal_i.point.centroid.x < metal_j.point.centroid.x:
                    if metal_j_boundsx[0] - metal_i_boundsx[1] < self.layer_properties.layer1000Spacing: # Clashes due to ETE M0 spacing DRC
                        clashes.append(j)
                elif metal_j.point.centroid.x < metal_i.point.centroid.x:
                    if metal_i_boundsx[0] - metal_j_boundsx[1] < self.layer_properties.layer1000Spacing: # Clashes due to ETE M0 spacing DRC
                        clashes.append(j)
            if self.technology in ['gaa', 'finfet']: 
                flag, non_planar_layers = get_planarConnected_flag(metal_i)
                if flag:
                    restricted_tracks = calculate_restricted_tracks(non_planar_layers, len(track_centers), subcell_location)
                    track_restrictions[i] = restricted_tracks
            if subcell_location == 'bottom': # if polygon in bottom subcell
                track_restrictions[i].extend(list(range(len(track_centers)//2, len(track_centers))))
            else: # if polygon in top subcell
                track_restrictions[i].extend(list(range(0, len(track_centers)//2)))
                
            clashes_with[i] = clashes
        #     print(f'track restrictions : {track_restrictions[i]}')
        #     print(f'clashes: {clashes_with[i]}')
        metal_positions = find_valid_permutations(len(track_centers), len(polygons_to_permutate), clashes_with)
        logger.debug(f"We went through {metal_positions} permutations, out of a total of {len(track_centers)**len(polygons_to_permutate)} possible permutations.")
        self.lvs_client.run()

    def get_summary_array(self):
        return self.lvs_client.summary_report
      
def main(args):
    args_gds_file = args.get("gds_file")
    DEBUG = args.get("debugger",True)
    limiter = args.get("limiter",None)
    cell_name = args.get("cell")
    netlist_path = args.get("netlist")
    tech = args.get('tech')
    tech = load_tech_file(tech)
    permutation_summary = []

    progress_bar = ProgressBar(total_calls=100)
    if limiter:
        progress_bar = ProgressBar(total_calls=limiter)  # Total calls for fibonacci(n) is 2^n - 1
    else:
        progress_bar = ProgressBar(total_calls=1000)  # Total calls for fibonacci(n) is 2^n - 1
    output_folder = args.get("output_dir")  
    if not exists(output_folder):
        logger.debug("creating directory")
        makedirs(output_folder)
    gds_file = args_gds_file 
    flow_type = args.get("flow_type")
    Path(f'{output_folder}/layout_reports/').mkdir(parents=True, exist_ok=True)

    def make_permutation_summary(file_path):
        if not exists(file_path):
            print(f"File not found: {file_path}")
            logger.debug(f"File not found: {file_path}")
            return None
        df = read_csv(file_path)
        df = df.drop(columns=['DRC', 'LVS'], errors='ignore')
        
        permutation_df = DataFrame(permutation_summary)
        result = merge(permutation_df, df, right_on='File name', left_on='layoutName', how='left')
        result = result.drop(columns=['layoutName', 'placer'], errors='ignore')
        result.to_csv(f'{output_folder}/summary.csv')

    if flow_type == "gds" :
        handler = None
    else:        
        logger.debug("Creating permtuation repository ")
        handler = PermutationRepository() 

    total_drc_count = 0
    total_lvs_count = 0
    total_count = 0
  

    if isfile(gds_file):
        fileName = gds_file.split('/')[-1].replace('.gds','')
        args_gds_file = '/'.join(args_gds_file.split('/')[:-1])
        permutation_engine = PermutationEngine(f"{gds_file}",f"{args_gds_file}/")
        permutation_engine.initialize_lvs_client(netlist_path, gds_file, cell_name, tech, output_folder, limiter=limiter)
        permutation_engine.tech = tech
        if permutation_engine.drc.checkDRC(strict = False):
            tqdm.write("\r Generating second degree Permutations for: {}".format(fileName))        
            polygons_to_permutate = []
            for layer in permutation_engine.layer_properties.permLayers:
                polygons_to_permutate.extend(permutation_engine.layerMap[layer].polygons)
                if not permutation_engine.layer_properties.backside_power_rail:
                    polygons_to_permutate = permutation_engine.remove_power_ground_polygons(polygons_to_permutate)
            if args.get("onlyOne", False):
                permutation_engine.optimizeGDS()
            else:
                permutation_engine.generatePermutations(polygons_to_permutate, limiter)
            total_drc_count = permutation_engine.drc_clean_count
            total_lvs_count = permutation_engine.lvs_client.lvs_clean_count
            total_count = permutation_engine.outputCount - 1
            print(f'\r DRC clean stage 2 layouts: {total_drc_count} for {fileName}')
            print(f'\r LVS clean stage 2 layouts: {total_lvs_count} for {fileName}')
            logger.info(f'DRC clean stage 2 layouts: {total_drc_count} for {fileName}')
            logger.info(f'LVS clean stage 2layouts: {total_lvs_count} for {fileName}')
        else:
            logger.debug("Some rules Failed") 

    else:
        files = []
        for gds_file in listdir(args_gds_file):
            if gds_file.endswith(".gds"):
                files.append(gds_file)
        for gds_file in tqdm(files):
            fileName = gds_file.split('/')[-1].replace('.gds','')
            permutation_engine = PermutationEngine(f"{args_gds_file}/{gds_file}",args_gds_file)
            permutation_engine.initialize_lvs_client(netlist_path, gds_file, cell_name, tech, output_folder, limiter=limiter)
            permutation_engine.tech = tech
            if permutation_engine.drc.checkDRC(strict = False):
                tqdm.write("\r Generating second degree Permutations for: {}".format(fileName))        
                polygons_to_permutate = []
                for layer in permutation_engine.layer_properties.permLayers:
                    polygons_to_permutate.extend(permutation_engine.layerMap[layer].polygons)
                    if not permutation_engine.layer_properties.backside_power_rail:
                        polygons_to_permutate = permutation_engine.remove_power_ground_polygons(polygons_to_permutate)
                if args.get("onlyOne", False):
                    permutation_engine.optimizeGDS()
                else:
                    permutation_engine.generatePermutations(polygons_to_permutate, limiter)
                drc_count = permutation_engine.drc_clean_count
                lvs_count = permutation_engine.lvs_client.lvs_clean_count
                total_drc_count += drc_count
                total_lvs_count += lvs_count
                total_count += (permutation_engine.outputCount - 1)
                print(f'\r DRC clean stage 2 layouts: {drc_count} for {fileName}')
                print(f'\r LVS clean stage 2 layouts: {lvs_count} for {fileName}')
                logger.info(f'DRC clean stage 2 layouts: {drc_count} for {fileName}')
                logger.info(f'LVS clean stage 2 layouts: {lvs_count} for {fileName}')
            else:
                logger.debug("Some rules Failed")
            permutation_summary.extend(permutation_engine.get_summary_array())
        if not args.get("onlyOne", False):
            make_permutation_summary(f'{args_gds_file}/summary.csv')
 
    #do final insert and close session
    if handler is not None:
        handler.close()
    return {
        'lvs': total_lvs_count,
        'drc': total_drc_count,
        'total': total_count
    }
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Generate GDS layout from  netlist.')
    parser.add_argument('--gds_file', required=True,
                        metavar='FILE', type=str, help='gds file')
    parser.add_argument('--output_dir', default="outputs/",
                        metavar='FILE', type=str, help='path to store the cell names')
    parser.add_argument('--limiter', default=None,type=int, help='path to store the cell names')
    parser.add_argument('--debugger', default=False, dest='debugger', action='store_true')
    parser.add_argument('--no_debugger', default=False,dest='debugger', action='store_false')
    parser.add_argument('--flow_type', choices=['db', 'gds'],default = "gds", help = "Write permutatations to gds files, or use db to write")
    parser.add_argument('--netlist', default='cells.sp', metavar='FILE', type=str, help='path to SPICE netlist (cells.sp)')
    parser.add_argument('--cell', required=True, metavar='NAME', type=str, help='cell name (e.g., NAND2X1)')
    parser.add_argument('--tech', default='tech.py', metavar='FILE', type=str, help='technology file (tech.py)')
    args, unknown = parser.parse_known_args()
    args = {
            "gds_file" : args.gds_file, 
            'tech':args.tech,
            'netlist':args.netlist_path,
            "cell": args.cell_name,
            "output_dir": args.output_dir,
            "limiter" : args.limiter,
            "debugger" : args.debugger,
            "flow_type":args.flow_type,
            "onlyOne": False
            } 
    main(args)
