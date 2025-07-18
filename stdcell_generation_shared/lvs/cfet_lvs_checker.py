logger = logging.getLogger('sivista_app')
    
def cfet_netlist_extractor(layout: db.Layout, top_cell: db.Cell) -> db.Netlist:
    """
    Extract cfet netlist for 3 terminal.
    """
    
    # Without netlist comparision capabilities.
    layout_to_netlist = db.LayoutToNetlist(db.RecursiveShapeIterator(layout, top_cell, []))
    logger.info(f'top cell: {top_cell}')
    def create_layer(name: str):
        layer = layout_to_netlist.make_layer(layout.layer(*layermap[name]), name)
        return layer if name.endswith("label") else layer.merge()

    # Layer Definitions
    # Diffusion layers
    n_diff = create_layer(ndiff) 
    p_diff = create_layer(pdiff)
    n_poly = create_layer(npoly)
    p_poly = create_layer(ppoly)

    # Contacts
    n_diff_dvb = create_layer(ndiff_dvb)
    p_diff_dvb = create_layer(pdiff_dvb)
    bspdn_pmos = create_layer(bspdn_pmos_via)
    p_viag = create_layer(pviag)
    n_viag = create_layer(nviag)

    # Vias
    interconnect_via = create_layer(diff_interconnect)
    p_viat = create_layer(pviat)
    n_viat = create_layer(nviat)

    # Metal layers and vias
    p_diffcon = create_layer(pdiffcon)
    n_diffcon = create_layer(ndiffcon)
    back_metal_0_label = create_layer(back_metal0_label)
    back_metal_0 = create_layer(back_metal0)
    metal_0 = create_layer(metal0)
    metal_0_label	 = create_layer(metal0_label) 
    metal_1 = create_layer(metal1)
    metal_1_label = create_layer(metal1_label)
    via_0 = create_layer(via0)

    gate_diffusion = create_layer(gate_isolation)
    boundary = create_layer(cell_boundary)

    # Computed layers
    #pmos
    pgate       = p_poly & p_diff
    psd         = p_diff - pgate

    #nmos
    ngate      = n_poly & n_diff
    nsd        = n_diff - ngate

    poly_via = (boundary - gate_diffusion) & (p_poly & n_poly) # Virtual via to establish p_poly-n_poly connection in absense of gate diffusion

    layout_to_netlist.register(poly_via, 'poly_via')
    layout_to_netlist.register(ngate, 'ngate')
    layout_to_netlist.register(pgate, 'pgate')
    layout_to_netlist.register(nsd, 'nsd')
    layout_to_netlist.register(psd, 'psd')

    # Device extraction
    # 3 terminal PMOS transistor device extraction
    pmos_extractor = db.DeviceExtractorMOS3Transistor("PMOS")
    layout_to_netlist.extract_devices(pmos_extractor, {"SD": psd, "G": pgate, "P": p_poly})

    # 3 terminal NMOS transistor device extraction
    nmos_extractor = db.DeviceExtractorMOS3Transistor("NMOS")
    layout_to_netlist.extract_devices(nmos_extractor, {"SD": nsd, "G": ngate, "P": n_poly})

    # Layer connectivities
    # At VSS
    layout_to_netlist.connect(back_metal_0, n_diff_dvb)
    layout_to_netlist.connect(n_diff_dvb, n_diffcon)
    layout_to_netlist.connect(back_metal_0, p_diff_dvb)
    layout_to_netlist.connect(p_diff_dvb, n_diffcon)   # Needed since pdiffcontact = ndiffcontact in layermap in tech file
    # At VDD
    layout_to_netlist.connect(back_metal_0, bspdn_pmos)
    layout_to_netlist.connect(bspdn_pmos, p_diffcon)
    # At Gate
    layout_to_netlist.connect(p_poly, poly_via)
    layout_to_netlist.connect(n_poly, poly_via)
    layout_to_netlist.connect(p_viag, metal_0)
    layout_to_netlist.connect(p_viag, p_poly)
    layout_to_netlist.connect(n_viag, metal_0)
    layout_to_netlist.connect(n_viag, n_poly)
    # At Source/Drain
    layout_to_netlist.connect(n_diffcon, interconnect_via)
    layout_to_netlist.connect(interconnect_via, p_diffcon)
    layout_to_netlist.connect(p_viat, metal_0)
    layout_to_netlist.connect(p_viat, p_diffcon)
    layout_to_netlist.connect(n_viat, metal_0)
    layout_to_netlist.connect(n_viat, n_diffcon)
    # At transistor
    layout_to_netlist.connect(nsd, n_diffcon)
    layout_to_netlist.connect(psd, p_diffcon)
    layout_to_netlist.connect(p_poly, pgate)
    layout_to_netlist.connect(n_poly, ngate)
    # Connect labels
    layout_to_netlist.connect(metal_0, metal_0_label)
    layout_to_netlist.connect(back_metal_0, back_metal_0_label)
    layout_to_netlist.connect(metal_1, metal_1_label)
    # At front metals
    layout_to_netlist.connect(metal_0, via_0)
    layout_to_netlist.connect(metal_1, via_0)

    logger.debug("Extracting netlist from layout")
    
    layout_to_netlist.extract_netlist()
    l_to_n_netlist = layout_to_netlist.netlist()
    
    l_to_n_netlist.make_top_level_pins()
    l_to_n_netlist.purge()
    l_to_n_netlist.combine_devices()
    l_to_n_netlist.purge_nets()   
    l_to_n_netlist.simplify()

    return l_to_n_netlist.dup()
