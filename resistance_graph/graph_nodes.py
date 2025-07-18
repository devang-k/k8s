import networkx as nx


# from stdcell_generation.common.net_util import  is_power_net,is_ground_net,is_supply_net

from pex_extraction.data_utils.preprocessing_regression import normalize_name

import logging

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('sivista_app')


def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets


# Module-level counter variables - one instance, never reset unless explicitly called
VIA_TECH_DICT = {
    "cfet": {"power": "BPR", "ground": "BPR", "default": "Int"},
    "gaa": {"power": "", "ground": "", "default": ""},
    "finfet": {"power": "", "ground": "", "default": ""},
}

METAL_NUMBER_DICT = {
    'M0': {"vertical": "1", "default": ""},
    'M1': {"vertical": "2", "default": ""},
    'VIA_M0_M1': {"vertical": "2", "default": "2"},
    'BSPowerRail': {"vertical": "1", "default": ""},
    'VIA_M0_NMOSInterconnect': {"vertical": "1", "default": ""},
    'VIA_M0_NMOSGate': {"vertical": "1", "default": ""},
    'VIA_M0_PMOSGate': {"vertical": "1", "default": ""},
    'VIA_M0_PMOSInterconnect': {"vertical": "1", "default": ""},
    'VIA_Inteconnect_BSPowerRail': {"vertical": "1", "default": ""},
    'VIA_PMOSInterconnect_NMOSInterconnect': {"vertical": "1", "default": ""}
}

INTERCONNECT_DICT = {
    "cfet": {"power": "Top", "ground": "Bottom", "default": "Top"},
    "gaa": {"power": "", "ground": "", "default": ""},
    "finfet": {"power": "", "ground": "", "default": ""}
}

GATE_DICT = {
    "cfet": {"power": "GateLine", "ground": "GateLine", "default": "GateLine"},
    "gaa": {"power": "GateLine", "ground": "GateLine", "default": "GateLine"},
    "finfet": {"power": "GateLine", "ground": "GateLine", "default": "GateLine"}
}


def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets


def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)


class BaseNode(ABC):
    def __init__(self, node_id, polygon, net_name, suffix="", layer_z_indices=None, delta=0, metal_counter="", device_suffix="", parent_node=None, cell_name=""):
        self.node_id = node_id
        self.polygon = polygon
        self.layer = self.polygon.layer
        self.polygon_id = self.polygon.id
        self.layer_name = self.polygon.layer_name
        self.suffix = f"{suffix}"
        self.coordinates = self.polygon.point.bounds
        self.metal_counter = metal_counter
        self.device_suffix = device_suffix
        self.parent_node = parent_node
        self.common_string = ""
        self.cell_name = cell_name
        self.z_index = layer_z_indices.get(self.layer, -1) + delta
        self.net_name = normalize_name(net_name)

    @abstractmethod
    def create_node_id(self, via_suffix, polygon, net_name):
        pass

    # if vertical is detectd then all normal metal layers(1000) and connections to that should contain metal1. and if not its ""


class ViaNode(BaseNode):

    def __init__(self, via_polygon, net_name, via_suffix, layer_z_indices, delta=0, metal_counter="", device_suffix="", technology="cfet", is_vertical=False, parent_node=None, cell_name=""):
        super().__init__(0, via_polygon, net_name, suffix=via_suffix, layer_z_indices=layer_z_indices, delta=delta,
                         metal_counter=metal_counter, device_suffix=device_suffix, parent_node=parent_node, cell_name=cell_name)
        # call the via counters and get the via suffix
        self.node_id, self.common_string = self.create_node_id(
            via_suffix, via_polygon, net_name, metal_counter, technology, is_vertical, parent_node)

    def create_node_id(self, via_suffix, polygon, net_name, metal_counter, technology, is_vertical, parent_node):

        if is_vertical:
            metal_number_fixed = METAL_NUMBER_DICT[str(
                self.layer_name)]['vertical']
        else:
            metal_number_fixed = METAL_NUMBER_DICT[str(
                self.layer_name)]['default'] if technology == "cfet" else f"1{METAL_NUMBER_DICT[str(self.layer_name)]['default']}"

        if technology == "cfet":

            via_id = f"{net_name}Via{VIA_TECH_DICT[technology]['default']}{via_suffix}_{net_name}Metal{VIA_TECH_DICT[technology]['default']}{metal_number_fixed}"
            if is_ground_net(net_name):
                via_id = f"VSSMetalBPR{via_suffix}"
                common_string = f"VSSMetalBPR{via_suffix}"
            if is_supply_net(net_name):
                via_id = f"VDDMetalBPVDDMetalBPRVia{via_suffix}"
                common_string = f"VDDMetalBPRVia{via_suffix}"
        else:
            via_id = f"{net_name}Metal{metal_number_fixed}{self.parent_node.common_string}_{net_name}Metal{metal_number_fixed}Via{via_suffix}"
            if not is_vertical :    #or not (self.cell_name == "HAX1")
                via_suffix = 0 if via_suffix == "" else via_suffix
                if is_ground_net(net_name):

                    via_id = f"VSSBSPR_VSSBSPRViaBlock{via_suffix + 1}"
                    common_string = f"VSSBSPRViaBlock{via_suffix + 1}"
                if is_supply_net(net_name):
                    via_id = f"VDDBSPR_VDDBSPRViaBlock{via_suffix +1}"
                    common_string = f"VDDBSPRViaBlock{via_suffix +1}"
      
        if not is_power_net(net_name) or ((technology == "gaa" or technology == "finfet") and is_vertical):
            common_string = via_id.split("_")
           
            if len(common_string) > 1:
                common_string = common_string[0] if "Via" in common_string[0] else common_string[1]
            else:
                common_string = via_id

        return via_id, common_string


class DeviceNode(BaseNode):
    def __init__(self, device_polygon, net_name, via_suffix, layer_z_indices, delta=0, metal_counter="", device_suffix="", technology="cfet", is_vertical=False, parent_node=None, cell_name=""):

        super().__init__(0, device_polygon, net_name, suffix=via_suffix, layer_z_indices=layer_z_indices, delta=delta,
                         metal_counter=metal_counter, device_suffix=device_suffix, parent_node=parent_node, cell_name=cell_name)
        self.node_id = self.create_node_id(
            via_suffix, device_polygon, net_name, device_suffix, technology, is_vertical)

        # Device suffix should be replaced by the gate map

    def create_node_id(self, via_suffix, polygon, net_name, device_suffix, technology, is_vertical):
        layer_name = polygon.layer_name
        if "Gate" in layer_name:
            # {device_suffix}"#Gateline block starts from 1 for GAA
            device_id = f"{net_name}{GATE_DICT[technology]['default']}"
            device_id = self.parent_node.common_string + "_" + device_id if technology == "cfet" else device_id + \
                f"{device_suffix+1}_" + \
                self.parent_node.common_string  # Gateline block starts from 1 for GAA

        elif "Interconnect" in layer_name:
            device_id = f"{net_name}Metal0{INTERCONNECT_DICT[technology]['default']}{device_suffix}" + \
                "_" + self.parent_node.common_string
        if is_power_net(net_name):
            if is_supply_net(net_name):

                device_id = f"VDDMetal0{INTERCONNECT_DICT[technology]['power']}{device_suffix}" + \
                    "_" + self.parent_node.common_string

                if technology == "gaa" or technology == "finfet":#and not self.cell_name == "HAX1"

                    device_id = f"VDDMetal0{INTERCONNECT_DICT[technology]['power']}{device_suffix}" + \
                        "_" + \
                        f"VDDBSPRViaBlock{self.parent_node.common_string[-1]}"

            elif is_ground_net(net_name):
                device_id = f"VSSMetal0{INTERCONNECT_DICT[technology]['ground']}{device_suffix}" + \
                    "_" + self.parent_node.common_string
                if technology == "gaa" or technology == "finfet": #and not self.cell_name == "HAX1"
                    device_id = f"VSSMetal0{INTERCONNECT_DICT[technology]['ground']}{device_suffix}" + \
                        "_" + \
                        f"VSSBSPRViaBlock{self.parent_node.common_string[-1]}"
        return device_id


class MetalNode(BaseNode):
    def __init__(self, metal_polygon, net_name, metal_suffix, layer_z_indices, delta=0, metal_counter="", device_suffix="", technology="cfet", is_vertical=False, parent_node=None, cell_name=""):
        super().__init__(0, metal_polygon, net_name, suffix=metal_counter, layer_z_indices=layer_z_indices, delta=delta,
                         metal_counter=metal_counter, device_suffix=device_suffix, parent_node=parent_node, cell_name=cell_name)
        metal_id, metal_counter = self.create_node_id(
            metal_suffix, net_name, metal_counter, is_vertical, technology)
        metal_id = metal_id
        self.node_id = metal_id
        self.common_string = metal_counter

    def create_node_id(self, metal_suffix, net_name, metal_counter, is_vertical, technology):
        if is_supply_net(net_name):
            net_name = "VDD"
        elif is_ground_net(net_name):
            net_name = "VSS"
        metal_fixed = METAL_NUMBER_DICT[str(
            self.layer_name)]['vertical'] if is_vertical else METAL_NUMBER_DICT[str(self.layer_name)]['default']

        if metal_counter == 0:
            if not is_vertical or self.layer_name == 'M1':
                metal_counter = ""
            if is_vertical and self.layer_name == 'M0':
                if self.parent_node is None:
                    metal_counter = ""
        if metal_counter == 0:
            if is_vertical and (self.layer_name == 'M0') and self.parent_node:
                metal_id = f"{net_name}Metal{metal_fixed}{metal_counter}"
            if self.layer_name == 'BSPowerRail':
                metal_id = f"{net_name}"
                metal_counter = ""
        else:

            metal_id = f"{net_name}{metal_fixed}{metal_counter if metal_counter else metal_suffix}"
            if self.parent_node is not None and technology == "gaa":
                metal_id = f"{net_name}Metal{metal_fixed}{metal_counter if metal_counter else metal_suffix}"
        # print(f"metal_id: {metal_id}, metal_counter: {metal_counter}")
        return metal_id, metal_counter


class NanosheetNode(BaseNode):
    def __init__(self, nanosheet_polygon, device_polygon, net_name, nanosheet_id, layer_z_indices, device_node, delta=0, intersection_coordinates=None, metal_counter="", device_suffix=""):
        super().__init__(1, nanosheet_polygon, net_name, suffix=nanosheet_id,
                         layer_z_indices=layer_z_indices, delta=delta)
        self.device_polygon = device_polygon
        self.device_node = device_node
        self.node_id = self.create_node_id(nanosheet_id, device_node, net_name)
        self.coordinates = intersection_coordinates

    def create_node_id(self, nanosheet_base_id, device_node, net_name):
        """Create nanosheet node ID based on device type and connections"""
        device_id = device_node.node_id
        device_part_str = ""

        device_parts = device_id.split("_")
        for device_part in device_parts:
            if not "Via" in device_part:
                device_part_str = device_part
        if "Gate" in device_node.layer_name:
            nanosheet_id = f"{nanosheet_base_id}_{device_part_str}"
        else:
            nanosheet_id = f"{device_part_str}_{nanosheet_base_id}"
        return nanosheet_id


class UnusedLayerNode(BaseNode):
    def __init__(self, unused_layer_polygon, net_name, via_suffix, layer_z_indices, delta=0):
        node_id = self.create_node_id(
            via_suffix, unused_layer_polygon, net_name)
        super().__init__(node_id, unused_layer_polygon, net_name,
                         suffix="", layer_z_indices=layer_z_indices, delta=delta)

    def create_node_id(self, via_suffix, unused_layer_polygon, net_name):
        return f"{net_name}MetalBPR{via_suffix}"


class NodeFactory:
    """Factory Method to dynamically return the correct node class."""

    # Map node types to their respective classes
    node_classes = {
        "via": ViaNode,
        "device": DeviceNode,
        "metal": MetalNode,
        "nanosheet": NanosheetNode,
        "unused": UnusedLayerNode
    }

    @staticmethod
    def create_node(polygon, net_name, via_suffix, layer_z_indices, delta=0, metal_counter="", device_suffix="", technology="cfet", is_vertical=False, parent_node=None, cell_name=""):
        """Returns an instance of the correct node class based on `polygon.layer_name`."""
        layer_name = polygon.layer_name.lower()  # Normalize case
        # Determine the node type using a lookup table
        node_type = NodeFactory.get_node_type(polygon)
        # Dynamically instantiate the correct node type
        if node_type in NodeFactory.node_classes:
            return NodeFactory.node_classes[node_type](polygon, net_name, via_suffix, layer_z_indices, delta=delta, metal_counter=metal_counter, device_suffix=device_suffix, technology=technology, is_vertical=is_vertical, parent_node=parent_node, cell_name=cell_name)
        else:
            raise ValueError(
                f"Unknown layer type: {layer_name} (Layer: {polygon.layer})")

    @staticmethod
    def get_node_type(polygon):
        """Determines the node type based on layer name or layer number."""
        layer_name = polygon.layer_name
    
        layer_node_type = {
            # Via layers
            "VIA_M0_PMOSInterconnect": "via",  # VIA_M0_M1
            "VIA_M0_PMOSGate": "via",  # VIA_M1_M2
            "VIA_M0_NMOSInterconnect": "via",  # VIA_M2_M3
            "VIA_M0_NMOSGate": "via",  # VIA_M3_M4
            "VIA_Inteconnect_BSPowerRail": "via",  # VIA_Inteconnect_BSPowerRail
            # VIA_PMOSInterconnect_NMOSInterconnect
            "VIA_PMOSInterconnect_NMOSInterconnect": "via",
            "VIA_M0_M1": "via",

            # Metal layers
            "M0": "metal",  # M0
            "M1": "metal",  # M1
            "BSPowerRail": "metal",   # BSPowerRail

            # Device layers (Gates and Interconnects)
            "PMOSGate": "device",  # PMOSGate
            "NMOSGate": "device",  # NMOSGate
            "PMOSInterconnect": "device",  # PMOSInterconnect
            "NMOSInterconnect": "device",  # NMOSInterconnect

            # Nanosheet layers
            "PmosNanoSheet": "nanosheet",  # PmosNanoSheet
            "NmosNanoSheet": "nanosheet",  # NmosNanoSheet

            # Unused layer
            "unused": "unused"
        }
        #print(f"layer_name: {layer_name}")
        #print(f"if node name in layer_name: {layer_name in layer_node_type}")
        return layer_node_type.get(layer_name, None)  # Unknown layer
