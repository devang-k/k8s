import sys
from os.path import join, abspath, dirname
sys.path.append(abspath(join(dirname(__file__), '../../..')))
from stdcell_generation_client.layout.layer_stack import *

tech_dic = {
    'layer_map': {
        ndiff: (100, 0),
        pdiff: (101, 0),
        nwell: (120, 0),
        ndiffcon: (104, 0),
        pdiffcon: (105, 0),
        ndiff_dvb: (111, 0),
        pdiff_dvb: (111, 0),
        npoly: (102, 0),
        ppoly: (103, 0),
        dummy_gate: (121, 0),
        gate_isolation: (122, 0),
        diff_interconnect: (123, 0),
        bspdn_pmos_via: (110, 0),
        pviat: (108, 0),
        pviag: (106, 0),
        nviat: (109, 0),
        nviag: (107, 0),
        via0: (201, 0),
        back_metal0: (300, 0),
        back_metal0_label: (300, 1),
        back_metal0_pin: (300, 2),
        back_metal0_pin_label: (300, 3),
        metal0: (200, 0),
        metal0_label: (200, 1),
        metal0_pin: (200, 2),
        metal0_pin_label: (200, 3),
        metal1: (202, 0),
        metal1_label: (202, 1),
        metal1_pin: (202, 2),
        metal1_pin_label: (202, 3),
        metal0_track_guide: (220, 0),
        metal1_track_guide: (221, 0),
        cell_boundary: (1, 0),
    },

    # Component widths
    'inner_space_width': 6,
    'nanosheet_width': 21,
    'power_rail_width': 37.5,
    'flipped': 'R0',
    'technology': 'cfet',
    'backside_power_rail': True,
    'routing_capability': 'Single Metal Solution',
    'half_dr' : True,
    #extensions
    'via_extension': 2.5,
    'gate_extension': 15,
    'interconnect_extension': 0,
    #gate_spacing
    'vertical_gate_spacing': 10,
    'pg_signal_spacing':10,
    #interconnect_spacing 
    'vertical_interconnect_spacing': 20,
    #pitch
    'm0_pitch': 25,
    'vertical_metal_pitch': 30,
    #variable parameters
    'number_of_routing_tracks': 6,
    #kind of implementation
    'placer': 'base0',
    'np_spacing':50,
    # Minimum spacing rules for layer pairs.
    'min_spacing': {
        (nanosheet, diff_interconnect):15
    },
    #wire width
    'layer_width': {
        npoly: 15,
        ppoly: 15,
        metal0: 12,
        ndiffcon: 18,
        pdiffcon: 18,
        metal0_track_guide: 12.5,
        metal1: 12,
        metal1_track_guide: 12.5,
    },
    'hinder': {
        'ndiffcon': 'pdiffcon',
        'npoly': 'ppoly'
    },
    'permutation': {
    #    ('min_spacing', (nanosheet, diff_interconnect)):range(15,20),
    #    ('gate_extension',''): range(10,15),
    #    ('layer_width','poly'): range(15,20),
   # ('placer', ''): ('base0', 'base1'),
    #   ('number_of_routing_tracks', ''): range(3,7)
    },
    # parameters that are not required
    'scaling_factor': 4,
    'db_unit': 1e-9,
    'cell_width': 45,
    'cell_height': 150,
    'routing_layers': {
        ndiffcon: 'v',
        pdiffcon: 'v',
        poly: 'v',
        npoly: 'v',
        ppoly: 'v',
        metal0: 'h',
        back_metal0: 'h',
        nanosheet: 'h',
    },
    'via_size': {
        pviag: 23,
        pdiff_dvb: 18,
        ndiff_dvb: 18,
        pviat: 15,
        diff_interconnect:15,
        nviat: 15,
        nviag: 23,
        via0: 12.5,
    },
    'minimum_enclosure': {
        (ndiffcon, pviag): 0,
        (pdiffcon, pviag): 0,
        (metal0, pviat): 0,
        (metal0, pviag): 0,
        (back_metal0, ndiff_dvb): 0,
        (nanosheet, pviag): 0,
        (poly, pviat): 0,
    },
    'f2f_layers': {
        'NMOS_GATE': ['NMOS_INTERCONNECT', 'y'],
        'PMOS_GATE': ['PMOS_INTERCONNECT', 'y']
    },
    'layer_properties_cfet': {
        1: { 'color': 0xEFEFEF, 'opacity': 1, 'offset': -5, 'height': 5, 'shape': 'box', 'name': 'CELL_BOUNDARY' },
        111: { 'color': 0xFF0000, 'opacity': 1, 'offset': 4, 'height': 12, 'shape': 'box', 'name': 'VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR' },
        104: { 'color': 0x37FEFD, 'opacity': 1, 'offset': 8, 'height': 6, 'shape': 'box', 'name': 'NMOS_INTERCONNECT' },
        100: { 'color': 0xFF9966, 'opacity': 1, 'offset': 6, 'height': 10, 'shape': 'nanosheet', 'name': 'NMOS_NANOSHEET' },
        102: { 'color': 0x30B0B0, 'opacity': 1, 'offset': 8, 'height': 8, 'shape': 'box', 'name': 'NMOS_GATE' },
        103: { 'color': 0x46C773, 'opacity': 1, 'offset': 16, 'height': 8, 'shape': 'box', 'name': 'PMOS_GATE' },
        105: { 'color': 0x61CB21, 'opacity': 1, 'offset': 16, 'height': 6, 'shape': 'box', 'name': 'PMOS_INTERCONNECT' },
        101: { 'color': 0x444444, 'opacity': 1, 'offset': 14, 'height': 10, 'shape': 'nanosheet', 'name': 'PMOS_NANOSHEET' },
        108: { 'color': 0xFF0080, 'opacity': 1, 'offset': 22, 'height': 10, 'shape': 'box', 'name': 'VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT' },
        106: { 'color': 0xFF00FF, 'opacity': 1, 'offset': 24, 'height': 8, 'shape': 'box', 'name': 'VIA_FROM_M0_TO_PMOS_GATE_VG' },
        109: { 'color': 0xD133FF, 'opacity': 1, 'offset': 14, 'height': 18, 'shape': 'box', 'name': 'VIA_FROM_M0_TO_NMOS_INTERCONNECT_VCT' },
        107: { 'color': 0x8D0000, 'opacity': 1, 'offset': 16, 'height': 16, 'shape': 'box', 'name': 'VIA_FROM_M0_TO_NMOS_GATE_VG'  },
        122: { 'color': 0xFFD6D6, 'opacity': 1, 'offset': 14, 'height': 4, 'shape': 'box', 'name': 'DIFFUSION_BREAK' },
        123: { 'color': 0x62FF00, 'opacity': 1, 'offset': 14, 'height': 2, 'shape': 'box', 'name': 'VIA_FROM_PMOS_INTERCONNECT_TO_NMOS_INTERCONNECT' },
        200: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 32, 'height': 5, 'shape': 'box', 'name': 'M0' },
        201: {'color': 0xDF4EC8, 'opacity': 1, 'offset': 37, 'height': 8, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_M1' },
        202: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 45, 'height': 5, 'shape': 'box', 'name': 'M1' },
        300: { 'color': 0xFD68B3, 'opacity': 1, 'offset': 0, 'height': 5, 'shape': 'box', 'name': 'M2_BACKSIDE_POWER_LINES' }
    },
    'layer_properties_gaa': {
        1: { 'color': 0xEFEFEF, 'opacity': 1, 'offset': -5, 'height': 5, 'shape': 'box', 'name': 'CELL_BOUNDARY' },
        100: { 'color': 0xFF9966, 'opacity': 1, 'offset': 125, 'height': 6, 'shape': 'nanosheet', 'name': 'NMOS_NANOSHEET' },
        101: { 'color': 0x444444, 'opacity': 1, 'offset': 125, 'height': 6, 'shape': 'nanosheet', 'name': 'PMOS_NANOSHEET' },
        102: { 'color': 0x30B0B0, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'NMOS_GATE' },
        103: { 'color': 0x46C773, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'PMOS_GATE' },
        104: { 'color': 0x37FEFD, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'NMOS_INTERCONNECT' },
        105: { 'color': 0x61CB21, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'PMOS_INTERCONNECT' },
        106: { 'color': 0xFF00FF, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_PMOS_GATE_VG' },
        107: { 'color': 0xFF00FF, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_NMOS_GATE_VG' },
        108: { 'color': 0xFF0080, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT' },
        109: { 'color': 0xFF0080, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_NMOS_INTERCONNECT_VCT' },
        111: { 'color': 0xFF0000, 'opacity': 1, 'offset': 90, 'height': 20, 'shape': 'cylinder', 'name': 'VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR' },
        122: { 'color': 0xFFD6D6, 'opacity': 1, 'offset': 14, 'height': 4, 'shape': 'box', 'name': 'DIFFUSION_BREAK' },
        200: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 198 , 'height': 27, 'shape': 'box', 'name': 'M0' },
        201: {'color': 0xDF4EC8, 'opacity': 1, 'offset': 225, 'height': 20, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_M1' },
        202: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 245, 'height': 50, 'shape': 'box', 'name': 'M1' },
        300: { 'color': 0xFD68B3, 'opacity': 1, 'offset': 0, 'height': 90, 'shape': 'box', 'name': 'M2_BACKSIDE_POWER_LINES' }
    },
    'layer_properties_finfet': {
        1: { 'color': 0xEFEFEF, 'opacity': 1, 'offset': -5, 'height': 5, 'shape': 'box', 'name': 'CELL_BOUNDARY' },
        100: { 'color': 0xFF9966, 'opacity': 1, 'offset': 125, 'height': 6, 'shape': 'nanosheet', 'name': 'NMOS_NANOSHEET' },
        101: { 'color': 0x444444, 'opacity': 1, 'offset': 125, 'height': 6, 'shape': 'nanosheet', 'name': 'PMOS_NANOSHEET' },
        102: { 'color': 0x30B0B0, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'NMOS_GATE' },
        103: { 'color': 0x46C773, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'PMOS_GATE' },
        104: { 'color': 0x37FEFD, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'NMOS_INTERCONNECT' },
        105: { 'color': 0x61CB21, 'opacity': 1, 'offset': 110, 'height': 70, 'shape': 'box', 'name': 'PMOS_INTERCONNECT' },
        106: { 'color': 0xFF00FF, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_PMOS_GATE_VG' },
        107: { 'color': 0xFF00FF, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_NMOS_GATE_VG' },
        108: { 'color': 0xFF0080, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT' },
        109: { 'color': 0xFF0080, 'opacity': 1, 'offset': 180, 'height': 18, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_NMOS_INTERCONNECT_VCT' },
        111: { 'color': 0xFF0000, 'opacity': 1, 'offset': 90, 'height': 20, 'shape': 'cylinder', 'name': 'VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR' },
        122: { 'color': 0xFFD6D6, 'opacity': 1, 'offset': 14, 'height': 4, 'shape': 'box', 'name': 'DIFFUSION_BREAK' },
        200: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 198 , 'height': 27, 'shape': 'box', 'name': 'M0' },
        201: {'color': 0xDF4EC8, 'opacity': 1, 'offset': 225, 'height': 20, 'shape': 'cylinder', 'name': 'VIA_FROM_M0_TO_M1' },
        202: { 'color': 0xF0FF69, 'opacity': 1, 'offset': 245, 'height': 50, 'shape': 'box', 'name': 'M1' },
        300: { 'color': 0xFD68B3, 'opacity': 1, 'offset': 0, 'height': 90, 'shape': 'box', 'name': 'M2_BACKSIDE_POWER_LINES' }
    }
}