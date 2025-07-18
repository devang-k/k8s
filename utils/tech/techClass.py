from stdcell_generation_client.layout.layer_stack import *
from dataclasses import dataclass, field

@dataclass
class TechFile:
    layer_map: dict = field(default_factory=lambda: {
        ndiffcon: (0, 0),
        pdiffcon: (0, 0),
        nwell: (120, 0),
        ndiff: (0, 0),
        pdiff: (0, 0),
        npoly: (0, 0),
        gate_isolation: (0,0),
        dummy_gate: (0,0),
        ppoly: (0, 0),
        pviag: (0, 0),
        nviag: (0, 0),
        ndiff_dvb: (0, 0),
        pdiff_dvb: (0, 0),
        metal0: (0, 0),
        metal0_label:(0, 1),
        metal0_pin: (0, 2),
        metal0_pin_label: (0, 3),
        diff_interconnect: (0,0),
        metal0_track_guide : (0,0), 
        pviat: (0, 0),
        nviat: (0, 0),
        back_metal0: (0, 0),
        back_metal0_label:(0, 1),
        back_metal0_pin:(0, 2),
        back_metal0_pin_label:(0, 3),
        cell_boundary: (0, 0),
        bspdn_pmos_via: (0,0),
        metal1: (0, 0),
        metal1_label:(0, 1),
        metal1_pin: (0, 2),
        metal1_pin_label: (0, 3),
        metal0_track_guide : (0,0), 
        metal1_track_guide : (0,0), 
        via0: (0, 0),
    })
    inner_space_width: float = 0
    nanosheet_width: float = 0
    power_rail_width: float = 0
    flipped: str = 'R0'
    technology: str = 'gaa'
    pg_signal_spacing: float = 0
    backside_power_rail: bool = False
    routing_capability: str = 'Single Metal Solution'
    half_dr: bool = False
    via_extension: float = 0
    gate_extension: float = 0
    interconnect_extension: float = 0
    vertical_gate_spacing: float = 0
    vertical_interconnect_spacing: float = 0
    np_spacing: float = 0
    m0_pitch: float = 0
    vertical_metal_pitch: float = 0
    number_of_routing_tracks: int = 0
    placer: str = 'base0'
    min_spacing: dict = field(default_factory=lambda: {
        (nwell, pwell): 0,
        (pdiffcon, poly): 0,
        (ndiffcon, poly): 0,
        (pdiffcon, npoly): 0,
        (ndiffcon, npoly): 0,
        (pdiffcon, ppoly): 0,
        (ndiffcon, ppoly): 0,
        (metal0, metal0): 0,
        (nanosheet, diff_interconnect): 0,
        (back_metal0, back_metal0): 0,
        (nanosheet, nanosheet): 0
    })
    layer_width: dict = field(default_factory=lambda: {
        poly: 0,
        npoly: 0,
        ppoly: 0,
        metal0: 0,
        ndiffcon: 0,
        pdiffcon: 0,
        metal0_track_guide: 0,
        metal1: 0,
        metal1_track_guide: 0,
    })
    hinder: dict = field(default_factory=lambda: {
        'ndiffcon': 'pdiffcon',
        'npoly': 'ppoly'
    })
    permutation: dict = field(default_factory=dict)
    scaling_factor: float = 0
    db_unit: float = 0
    height_req: int = 1
    output_writers: list = field(default_factory=list)
    cell_width: float = 0
    cell_height: float = 0
    routing_layers: dict = field(default_factory=lambda: {
        ndiffcon: 'v',
        pdiffcon: 'v',
        poly: 'v',
        npoly: 'v',
        ppoly: 'v',
        metal0: 'h',
        back_metal0: 'h',
        nanosheet: 'h',
    })
    via_size: dict = field(default_factory=lambda: {
        pviag: 0,
        pdiff_dvb: 0,
        ndiff_dvb: 0,
        pviat: 0,
        diff_interconnect: 0,
        nviat: 0,
        nviag: 0,
        via0: 0,
    })
    minimum_enclosure: dict = field(default_factory=lambda: {
        (ndiffcon, pviag): 0,
        (pdiffcon, pviag): 0,
        (metal0, pviat): 0,
        (metal0, pviag): 0,
        (back_metal0, ndiff_dvb): 0,
        (nanosheet, pviag): 0,
        (poly, pviat): 0,
    })
    my_add_pmos_nanosheet: tuple = field(init=False)
    my_add_nmos_nanosheet: tuple = field(init=False)
    metrics_map: list = field(init=False)
    f2f_layers: dict = field(default_factory=lambda: {
        'NMOS_GATE': ['NMOS_INTERCONNECT', 'y'],
        'PMOS_GATE': ['PMOS_INTERCONNECT', 'y']
    })
    layer_properties: dict = field(default_factory=dict)
    display_names: dict = field(default_factory=dict)

    def configure(self):
        self.db_unit = (self.db_unit / self.scaling_factor) if self.scaling_factor else self.db_unit
        self.my_add_pmos_nanosheet = (self.layer_map.get(pdiff, (0, 0)), 1)
        self.my_add_nmos_nanosheet = (self.layer_map.get(ndiff, (0, 0)), 1)
        self.metrics_map = [
            ('NMOS_NANOSHEET', self.layer_map.get(ndiff, (0, 0))),
            ('NMOS_ACT_PATTERNED', self.my_add_nmos_nanosheet),
            ('PMOS_NANOSHEET', self.layer_map.get(pdiff, (0, 0))),
            ('PMOS_ACT_PATTERNED', self.my_add_pmos_nanosheet),
            ('NMOS_GATE', self.layer_map.get(npoly, (0, 0))),
            ('NMOS_INTERCONNECT', self.layer_map.get(ndiffcon, (0, 0))),
            ('PMOS_GATE', self.layer_map.get(ppoly, (0, 0))),
            ('PMOS_INTERCONNECT', self.layer_map.get(pdiffcon, (0, 0))),
            ('SINGLE_DIFFUSION_BREAK', self.layer_map.get(dummy_gate, (0, 0))),
            ('VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR', self.layer_map.get(ndiff_dvb, (0, 0))),
            ('VIA_FROM_PMOS_INTERCONNECT_TO_NMOS_INTERCONNECT', self.layer_map.get(diff_interconnect, (0, 0))),
            ('VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT', self.layer_map.get(pviat, (0, 0))),
            ('VIA_FROM_M0_TO_PMOS_GATE_VG', self.layer_map.get(pviag, (0, 0))),
            ('M2_BACKSIDE_POWER_LINES', self.layer_map.get(back_metal0, (0, 0))),
            ('M2_BACKSIDE_POWER_LINES_LABEL', self.layer_map.get(back_metal0_label, (0, 0))),
            ('M0', self.layer_map.get(metal0, (0, 0))),
            ('M0_LABEL', self.layer_map.get(metal0_label, (0, 0))),
            ('M1', self.layer_map.get(metal1, (0, 0))),
            ('M1_LABEL', self.layer_map.get(metal1_label, (0, 0))),
            ('CELL_BOUNDARY', self.layer_map.get(cell_boundary, (0, 0))),
        ]
        if self.technology in ['gaa', 'finfet']:
            self.hinder = {}