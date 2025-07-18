ndiffcon = 'ndiffcon'
pdiffcon = 'pdiffcon'
nwell = 'nwell'
pwell = 'pwell'
poly = 'poly'
npoly = 'npoly'
ppoly = 'ppoly'
poly_label = 'poly_label'
pdiff_dvb = 'pdiff_dvb'
ndiff_dvb = 'ndiff_dvb'
pviag = 'pviag'
metal0 = 'metal0'
metal0_label = 'metal0_label'
metal0_pin = 'metal0_pin'
metal0_pin_label = 'metal0_pin_label'
pviat = 'pviat'
back_metal0 = 'back_metal0'
back_metal0_label = 'back_metal0_label'
back_metal0_pin = 'back_metal0_pin'
back_metal0_pin_label = 'back_metal0_pin_label'
cell_boundary = 'cell_boundary'
nanosheet = 'nanosheet'
pdiff = 'pdiff'
ndiff = 'ndiff'
diff_interconnect = 'diff_interconnect'
metal0_track_guide = 'metal0_track_guide'
gate_isolation = 'gate_isolation'
dummy_gate = 'dummy_gate'
nviat = 'nviat'
nviag = 'nviag'
bspdn_pmos_via = 'bspdn_pmos_via'
via0 = 'via0'
metal1_track_guide = 'metal1_track_guide'
metal1 = 'metal1'
metal1_label = 'metal1_label'
metal1_pin = 'metal1_pin'
metal1_pin_label = 'metal1_pin_label'

layermap = {
    nwell: (1, 0),
    pwell: (2, 0),
    ndiffcon: (3, 0),
    pdiffcon: (4, 0),
    poly: (5, 0),
    npoly: (5, 1),
    ppoly: (5, 2),
    pdiff_dvb: (6, 0),
    ndiff_dvb: (6, 1),
    pviag: (7, 0),
    nviag: (7,1),
    metal0: (8, 0),
    metal0_label: (8, 1),
    metal0_pin: (8, 2),
    metal0_pin_label: (8, 3),
    pviat: (9, 0),
    nviat: (9,1),
    back_metal0: (10, 0),
    back_metal0_label: (10, 1),
    back_metal0_pin: (10, 2),
    back_metal0_pin_label: (10, 3),
    nanosheet: (11, 0),
    diff_interconnect: (12, 0),
    ndiff: (14, 0),
    pdiff: (15, 0),
    cell_boundary: (16, 0),
    metal0_track_guide: (17, 0),
    gate_isolation: (18, 0),
    dummy_gate: (19, 0),
    bspdn_pmos_via: (20, 0),
    via0: (21, 0),
    metal1_track_guide: (22, 0),
    metal1: (23, 0),
    metal1_label: (23, 1),
    metal1_pin: (23, 2),
    metal1_pin_label: (23, 3),
}

layermap_reverse = {v: k for k, v in layermap.items()}

via_layers = nx.Graph()

via_layers.add_edge(metal0, poly, layer=pviat)
via_layers.add_edge(ndiffcon, metal0, layer=pviag)
via_layers.add_edge(pdiffcon, metal0, layer=pviag)

via_layers.add_edge(ndiffcon, back_metal0, layer=ndiff_dvb)
via_layers.add_edge(pdiffcon, back_metal0, layer=pdiff_dvb)

via_layers.add_edge(ndiffcon, nanosheet, layer=pviag)
via_layers.add_edge(pdiffcon, nanosheet, layer=pviag)
via_layers.add_edge(poly, nanosheet, layer=pviag)


via_layers.add_edge(metal0, npoly, layer=pviat)
via_layers.add_edge(npoly, nanosheet, layer=pviag)

via_layers.add_edge(metal0, ppoly, layer=pviat)
via_layers.add_edge(ppoly, nanosheet, layer=pviag)
