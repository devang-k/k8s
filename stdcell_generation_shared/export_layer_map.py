

class LayerMap(ABC):
    @abstractmethod
    def exportLayerMap(self, tech, file_name):
        pass

class CFETLayerMap(LayerMap):
    def exportLayerMap(self, tech, file_name, io_pins):
        content = {
            "Layers": {
                str(tech.layer_map.get(ndiff)[0]): {
                    "Name": "NmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(pdiff)[0]): {
                    "Name": "PmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(npoly)[0]): {
                    "Name": "NMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[npoly]
                },
                str(tech.layer_map.get(ppoly)[0]): {
                    "Name": "PMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[ppoly]
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "DiffusionLayer",
                    "direction": "V"
                },
                str(tech.layer_map.get(ndiffcon)[0]): {
                    "Name": "NMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[ndiffcon]
                },
                str(tech.layer_map.get(pdiffcon)[0]): {
                    "Name": "PMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[pdiffcon]
                },
                str(tech.layer_map.get(ndiff_dvb)[0]): {
                    "Name": "VIA_Inteconnect_BSPowerRail",
                    "connector": [
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ],
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ]
                    ]
                },
                str(tech.layer_map.get(diff_interconnect)[0]): {
                    "Name": "VIA_PMOSInterconnect_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(pdiffcon)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ]

                },
                str(tech.layer_map.get(bspdn_pmos_via)[0]): {
                    "Name": "Unused_Component",
                    "layer": tech.layer_map.get(bspdn_pmos_via)[0]

                },
                str(tech.layer_map.get(gate_isolation)[0]): {
                    "Name": "Gate_Diffusion",
                    "layer": tech.layer_map.get(gate_isolation)[0]
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "Diffusion_Break",
                    "direction": "H"
                },
                str(tech.layer_map.get(pviat)[0]): {
                    "Name": "VIA_M0_PMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ]
                    ],
                    "hinder": None if routing_order[pdiffcon]<routing_order[ndiffcon] else "NMOSInterconnect",
                },
                str(tech.layer_map.get(nviat)[0]): {
                    "Name": "VIA_M0_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ],
                    "hinder": None if routing_order[ndiffcon]<routing_order[pdiffcon] else "PMOSInterconnect",
                },
                
                str(tech.layer_map.get(pviag)[0]): {
                    "Name": "VIA_M0_PMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ppoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[ppoly]<routing_order[npoly] else "NMOSGate",
                },
                str(tech.layer_map.get(nviag)[0]): {
                    "Name": "VIA_M0_NMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(npoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[npoly]<routing_order[ppoly] else "PMOSGate",
                },
                str(tech.layer_map.get(via0)[0]):{
                    "Name":"VIA_M0_M1",
                    "connector":[
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(metal1)[0]
                        ]
                    ]
                }
                ,
                str(tech.layer_map.get(back_metal0)[0]): {
                    "Name": "BSPowerRail",
                    "direction": "H",
                    "width": tech.power_rail_width
                },
                str(tech.layer_map.get(metal0)[0]): {
                    "Name": "M0",
                    "direction": "H",
                    "width": tech.layer_width[metal0]
                },
                str(tech.layer_map.get(metal0_track_guide)[0]): {
                    "Name": "HorizontalTracks",
                    "direction": "H"
                },
                str(tech.layer_map.get(metal1_track_guide)[0]):{
                    "Name":"VerticalTracks",
                    "direction":"V"
                }
                ,
                str(tech.layer_map.get(metal1)[0]):{
                    "Name":"M1",
                    "direction":"V",
                    "width":tech.layer_width[metal1]
                }
                ,
                str(tech.layer_map.get(cell_boundary)[0]): {
                    "Name": "Boundary"
                },
            },
            "layer1000Pitch": tech.m0_pitch,
            "layer1050Pitch": tech.vertical_metal_pitch,
            "layer1000Spacing": tech.routing_grid_pitch_x,
            "InnerSpaceWidth": tech.inner_space_width,
            "ViaExtension": tech.via_extension,
            "layerExtension": tech.via_extension,
            "gateSheetExtension": tech.gate_extension,
            "interconnectSheetExtension": tech.interconnect_extension,
            "via600SheetGap": tech.min_spacing[(nanosheet, diff_interconnect)],
            "InterconnectExtensionfromM0": tech.via_extension,
            "GateExtensionfromM0": tech.via_extension,
            "permLayers": [
                tech.layer_map.get(metal0)[0],
            ],
            "stepSize": tech.m0_pitch,
            "moveTogether": True,
            "metricsMap": tech.metrics_map,
            'f2fLayers': tech.f2f_layers if hasattr(tech, 'f2f_layers') else {'NMOS_GATE': ['NMOS_INTERCONNECT', 'y'],'PMOS_GATE': ['PMOS_INTERCONNECT', 'y']},
            "technology": 'cfet',
            "flipped": tech.flipped,
            "backside_power_rail": tech.backside_power_rail,
            "height_req": tech.height_req,
            "nanosheetWidth": tech.nanosheet_width,
            "wireWidth": {
                "npoly": tech.layer_width[npoly],
                "ppoly": tech.layer_width[ppoly],
                "metal0": tech.layer_width[metal0],
                "ndiffcon": tech.layer_width[ndiffcon],
                "pdiffcon": tech.layer_width[pdiffcon],
                "metal0_track_guide": tech.layer_width[metal0_track_guide],
                "metal1": tech.layer_width[metal1],
                "metal1_track_guide": tech.layer_width[metal1_track_guide]
            },
            "io_pins": io_pins
        }
        
        with open(file_name, 'w') as f:
            dump(content, f, ensure_ascii=False, indent=4)

class GAALayerMap(LayerMap):
    def exportLayerMap(self, tech, file_name, io_pins):
        content = {
            "Layers": {
                str(tech.layer_map.get(ndiff)[0]): {
                    "Name": "NmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(pdiff)[0]): {
                    "Name": "PmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(npoly)[0]): {
                    "Name": "NMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[npoly],
                    "planarConnections":[tech.layer_map.get(ppoly)[0]] 
                },
                str(tech.layer_map.get(ppoly)[0]): {
                    "Name": "PMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[ppoly],
                    "planarConnections":[tech.layer_map.get(npoly)[0]] 
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "DiffusionLayer",
                    "direction": "V"
                },
                str(tech.layer_map.get(ndiffcon)[0]): {
                    "Name": "NMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[ndiffcon],
                    "planarConnections":[tech.layer_map.get(pdiffcon)[0]]
                },
                str(tech.layer_map.get(pdiffcon)[0]): {
                    "Name": "PMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[pdiffcon],
                    "planarConnections":[tech.layer_map.get(ndiffcon)[0]]
                },
                str(tech.layer_map.get(ndiff_dvb)[0]): {
                    "Name": "VIA_Inteconnect_BSPowerRail",
                    "connector": [
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ],
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ]
                    ]
                },
                str(tech.layer_map.get(diff_interconnect)[0]): {
                    "Name": "VIA_PMOSInterconnect_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(pdiffcon)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ]

                },
                str(tech.layer_map.get(bspdn_pmos_via)[0]): {
                    "Name": "Unused_Component",
                    "layer": tech.layer_map.get(bspdn_pmos_via)[0]

                },
                str(tech.layer_map.get(gate_isolation)[0]): {
                    "Name": "Gate_Diffusion",
                    "layer": tech.layer_map.get(gate_isolation)[0]
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "Diffusion_Break",
                    "direction": "H"
                },
                str(tech.layer_map.get(pviat)[0]): {
                    "Name": "VIA_M0_PMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ],
                        [   tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ],
                    "hinder": None if routing_order[pdiffcon]<routing_order[ndiffcon] else "NMOSInterconnect",
                },
                str(tech.layer_map.get(nviat)[0]): {
                    "Name": "VIA_M0_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]

                        ]
                    ],
                    "hinder": None if routing_order[ndiffcon]<routing_order[pdiffcon] else "PMOSInterconnect",
                },
                str(tech.layer_map.get(pviag)[0]): {
                    "Name": "VIA_M0_PMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ppoly)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(npoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[ppoly]<routing_order[npoly] else "NMOSGate",
                },
                str(tech.layer_map.get(nviag)[0]): {
                    "Name": "VIA_M0_NMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(npoly)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ppoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[npoly]<routing_order[ppoly] else "PMOSGate"
                },
                str(tech.layer_map.get(via0)[0]):{
                    "Name":"VIA_M0_M1",
                    "connector":[
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(metal1)[0]
                        ]
                    ]
                }
                ,
                str(tech.layer_map.get(back_metal0)[0]): {
                    "Name": "BSPowerRail",
                    "direction": "H",
                    "width": tech.power_rail_width
                },
                str(tech.layer_map.get(metal0)[0]): {
                    "Name": "M0",
                    "direction": "H",
                    "width": tech.layer_width[metal0]
                },
                   str(tech.layer_map.get(metal1)[0]):{
                    "Name":"M1",
                    "direction":"V",
                    "width":tech.layer_width[metal1]
                },
                str(tech.layer_map.get(metal0_track_guide)[0]): {
                    "Name": "HorizontalTracks",
                    "direction": "H"
                },
                str(tech.layer_map.get(metal1_track_guide)[0]):{
                    "Name":"VerticalTracks",
                    "direction":"V"
                },
                str(tech.layer_map.get(cell_boundary)[0]): {
                    "Name": "Boundary"
                },
            },
            "layer1000Pitch": tech.m0_pitch,
            "layer1050Pitch": tech.vertical_metal_pitch,
            "layer1000Spacing": tech.routing_grid_pitch_x,
            "InnerSpaceWidth": tech.inner_space_width,
            "ViaExtension": tech.via_extension,
            "layerExtension": tech.via_extension,
            "gateSheetExtension": tech.gate_extension,
            "interconnectSheetExtension": tech.interconnect_extension,
            "via600SheetGap": tech.min_spacing[(nanosheet, diff_interconnect)],
            "InterconnectExtensionfromM0": tech.via_extension,
            "GateExtensionfromM0": tech.via_extension,
            "permLayers": [
                tech.layer_map.get(metal0)[0],
            ],
            "stepSize": tech.m0_pitch,
            "moveTogether": True,
            "metricsMap": tech.metrics_map,
            'f2fLayers': tech.f2f_layers if hasattr(tech, 'f2f_layers') and tech.f2f_layers else {'NMOS_GATE': ['NMOS_INTERCONNECT', 'y'],'PMOS_GATE': ['PMOS_INTERCONNECT', 'y']},
            "technology": 'gaa',
            "flipped": tech.flipped,
            "backside_power_rail": tech.backside_power_rail,
            "height_req": tech.height_req,
            "np_spacing": tech.np_spacing,
            "vertical_gate_spacing": tech.vertical_gate_spacing,
            "vertical_interconnect_spacing": tech.vertical_interconnect_spacing,
            "height_req": tech.height_req,
            "nanosheetWidth": tech.nanosheet_width,
            "wireWidth": {
                "npoly": tech.layer_width[npoly],
                "ppoly": tech.layer_width[ppoly],
                "metal0": tech.layer_width[metal0],
                "ndiffcon": tech.layer_width[ndiffcon],
                "pdiffcon": tech.layer_width[pdiffcon],
                "metal0_track_guide": tech.layer_width[metal0_track_guide],
                "metal1": tech.layer_width[metal1],
                "metal1_track_guide": tech.layer_width[metal1_track_guide]
            },
            "io_pins": io_pins
        }
        
        with open(file_name, 'w') as f:
            dump(content, f, ensure_ascii=False, indent=4)
            
class FINFETLayerMap(LayerMap):
    def exportLayerMap(self, tech, file_name, io_pins):
        content = {
            "Layers": {
                str(tech.layer_map.get(ndiff)[0]): {
                    "Name": "NmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(pdiff)[0]): {
                    "Name": "PmosNanoSheet",
                    "direction": "H"
                },
                str(tech.layer_map.get(nwell)[0]): {
                    "Name": "Nwell",
                    "direction": "H"
                },
                str(tech.layer_map.get(npoly)[0]): {
                    "Name": "NMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[npoly],
                    "planarConnections":[tech.layer_map.get(ppoly)[0]] 
                },
                str(tech.layer_map.get(ppoly)[0]): {
                    "Name": "PMOSGate",
                    "direction": "V",
                    "width": tech.layer_width[ppoly],
                    "planarConnections":[tech.layer_map.get(npoly)[0]] 
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "DiffusionLayer",
                    "direction": "V"
                },
                str(tech.layer_map.get(ndiffcon)[0]): {
                    "Name": "NMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[ndiffcon],
                    "planarConnections":[tech.layer_map.get(pdiffcon)[0]]
                },
                str(tech.layer_map.get(pdiffcon)[0]): {
                    "Name": "PMOSInterconnect",
                    "direction": "V",
                    "width": tech.layer_width[pdiffcon],
                    "planarConnections":[tech.layer_map.get(ndiffcon)[0]]
                },
                str(tech.layer_map.get(ndiff_dvb)[0]): {
                    "Name": "VIA_Inteconnect_BSPowerRail",
                    "connector": [
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ],
                        [
                            tech.layer_map.get(back_metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ]
                    ]
                },
                str(tech.layer_map.get(diff_interconnect)[0]): {
                    "Name": "VIA_PMOSInterconnect_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(pdiffcon)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ]

                },
                str(tech.layer_map.get(bspdn_pmos_via)[0]): {
                    "Name": "Unused_Component",
                    "layer": tech.layer_map.get(bspdn_pmos_via)[0]

                },
                str(tech.layer_map.get(gate_isolation)[0]): {
                    "Name": "Gate_Diffusion",
                    "layer": tech.layer_map.get(gate_isolation)[0]
                },
                str(tech.layer_map.get(dummy_gate)[0]): {
                    "Name": "Diffusion_Break",
                    "direction": "H"
                },
                str(tech.layer_map.get(pviat)[0]): {
                    "Name": "VIA_M0_PMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]
                        ],
                        [   tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ]
                    ],
                    "hinder": None if routing_order[pdiffcon]<routing_order[ndiffcon] else "NMOSInterconnect",
                },
                str(tech.layer_map.get(nviat)[0]): {
                    "Name": "VIA_M0_NMOSInterconnect",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ndiffcon)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(pdiffcon)[0]

                        ]
                    ],
                    "hinder": None if routing_order[ndiffcon]<routing_order[pdiffcon] else "PMOSInterconnect",
                },
                str(tech.layer_map.get(pviag)[0]): {
                    "Name": "VIA_M0_PMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ppoly)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(npoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[ppoly]<routing_order[npoly] else "NMOSGate",
                },
                str(tech.layer_map.get(nviag)[0]): {
                    "Name": "VIA_M0_NMOSGate",
                    "connector": [
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(npoly)[0]
                        ],
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(ppoly)[0]
                        ]
                    ],
                    "hinder": None if routing_order[npoly]<routing_order[ppoly] else "PMOSGate"
                },
                str(tech.layer_map.get(via0)[0]):{
                    "Name":"VIA_M0_M1",
                    "connector":[
                        [
                            tech.layer_map.get(metal0)[0],
                            tech.layer_map.get(metal1)[0]
                        ]
                    ]
                }
                ,
                str(tech.layer_map.get(back_metal0)[0]): {
                    "Name": "BSPowerRail",
                    "direction": "H",
                    "width": tech.power_rail_width
                },
                str(tech.layer_map.get(metal0)[0]): {
                    "Name": "M0",
                    "direction": "H",
                    "width": tech.layer_width[metal0]
                },
                   str(tech.layer_map.get(metal1)[0]):{
                    "Name":"M1",
                    "direction":"V",
                    "width":tech.layer_width[metal1]
                },
                str(tech.layer_map.get(metal0_track_guide)[0]): {
                    "Name": "HorizontalTracks",
                    "direction": "H"
                },
                str(tech.layer_map.get(metal1_track_guide)[0]):{
                    "Name":"VerticalTracks",
                    "direction":"V"
                },
                str(tech.layer_map.get(cell_boundary)[0]): {
                    "Name": "Boundary"
                },
            },
            "layer1000Pitch": tech.m0_pitch,
            "layer1050Pitch": tech.vertical_metal_pitch,
            "layer1000Spacing": tech.routing_grid_pitch_x,
            "InnerSpaceWidth": tech.inner_space_width,
            "ViaExtension": tech.via_extension,
            "layerExtension": tech.via_extension,
            "gateSheetExtension": tech.gate_extension,
            "interconnectSheetExtension": tech.interconnect_extension,
            "via600SheetGap": tech.min_spacing[(nanosheet, diff_interconnect)],
            "InterconnectExtensionfromM0": tech.via_extension,
            "GateExtensionfromM0": tech.via_extension,
            "permLayers": [
                tech.layer_map.get(metal0)[0],
            ],
            "stepSize": tech.m0_pitch,
            "moveTogether": True,
            "metricsMap": tech.metrics_map,
            'f2fLayers': tech.f2f_layers if hasattr(tech, 'f2f_layers') and tech.f2f_layers else {'NMOS_GATE': ['NMOS_INTERCONNECT', 'y'],'PMOS_GATE': ['PMOS_INTERCONNECT', 'y']},
            "technology": 'finfet',
            "flipped": tech.flipped,
            "backside_power_rail": tech.backside_power_rail,
            "height_req": tech.height_req,
            "np_spacing": tech.np_spacing,
            "vertical_gate_spacing": tech.vertical_gate_spacing,
            "vertical_interconnect_spacing": tech.vertical_interconnect_spacing,
            "nanosheetWidth": tech.nanosheet_width,
            "wireWidth": {
                "npoly": tech.layer_width[npoly],
                "ppoly": tech.layer_width[ppoly],
                "metal0": tech.layer_width[metal0],
                "ndiffcon": tech.layer_width[ndiffcon],
                "pdiffcon": tech.layer_width[pdiffcon],
                "metal0_track_guide": tech.layer_width[metal0_track_guide],
                "metal1": tech.layer_width[metal1],
                "metal1_track_guide": tech.layer_width[metal1_track_guide]
            },
            "io_pins": io_pins
        }
        
        with open(file_name, 'w') as f:
            dump(content, f, ensure_ascii=False, indent=4)
