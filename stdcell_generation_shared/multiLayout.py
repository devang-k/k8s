

logger = logging.getLogger('sivista_app')

def _adjustTechValues(tech):

    tech.cell_height = tech.cell_height - tech.power_rail_width
    tech.cell_width = (max(tech.layer_width[npoly], tech.layer_width[ppoly])+2*tech.inner_space_width)+max(tech.layer_width[ndiffcon], tech.layer_width[pdiffcon])
    tech.routing_grid_pitch_x = tech.cell_width / 2
    tech.grid_offset_x = tech.routing_grid_pitch_x
    tech.grid_offset_y = -tech.power_rail_width/2 + tech.m0_pitch/2
    tech.layer_width[metal0_track_guide] = tech.layer_width[metal0]
    tech.layer_width[metal1_track_guide] = tech.layer_width[metal1]
    d = {}
    d[pviag]= tech.layer_width[ppoly] + 2*tech.via_extension
    d[nviag]= tech.layer_width[npoly] + 2*tech.via_extension
    d[ndiff_dvb]= tech.layer_width[ndiffcon]
    d[pdiff_dvb]= tech.layer_width[pdiffcon]
    d[diff_interconnect]= max(tech.layer_width[ndiffcon], tech.layer_width[pdiffcon])
    d[pviat]= tech.layer_width[pdiffcon] + 2*tech.via_extension
    d[nviat]= tech.layer_width[pdiffcon] + 2*tech.via_extension
    d[via0]= tech.layer_width[metal1] + 2*tech.via_extension
    # d[via1]= tech.layer_width[metal2] + 2*tech.via_extension
    setattr(tech, 'via_size_horizontal', d)
    d = {}
    d[pviag]= tech.layer_width[metal0] + 2*tech.via_extension
    d[nviag]= tech.layer_width[metal0] + 2*tech.via_extension
    d[ndiff_dvb]= tech.power_rail_width//2 if tech.half_dr else min(0.72*(tech.power_rail_width) + 2*tech.via_extension, tech.power_rail_width)
    d[pdiff_dvb]= tech.power_rail_width//2 if tech.half_dr else min(0.72*(tech.power_rail_width) + 2*tech.via_extension, tech.power_rail_width)
    d[diff_interconnect]= tech.layer_width[pdiffcon] + tech.via_extension
    d[pviat]= tech.layer_width[metal0] + 2*tech.via_extension
    d[nviat]= tech.layer_width[metal0] + 2*tech.via_extension
    d[via0]= tech.layer_width[metal0] + 2*tech.via_extension
    # d[via1]= tech.layer_width[metal2] + 2*tech.via_extension
    setattr(tech, 'via_size_vertical', d)
    return tech

def _adjust_routing_tracks(tech):
    if tech.height_req > 1:
        tech.number_of_routing_tracks *= tech.height_req
    if tech.height_req > 1:
        subcell_tracks = tech.number_of_routing_tracks // tech.height_req
        if tech.backside_power_rail:
            tech.cell_height = ((subcell_tracks+1)*tech.m0_pitch) * tech.height_req
        else:
            tech.cell_height = (tech.power_rail_width + 2*tech.pg_signal_spacing + (subcell_tracks - 1)*tech.m0_pitch + tech.layer_width[metal0]) * tech.height_req
    elif tech.number_of_routing_tracks != None:
        if tech.backside_power_rail:
            if not tech.half_dr:
                tech.cell_height = tech.number_of_routing_tracks*tech.m0_pitch -tech.power_rail_width # backside bspdn true
            else:
                tech.cell_height = (tech.number_of_routing_tracks+1)*tech.m0_pitch -tech.power_rail_width
        else:
            tech.cell_height = tech.power_rail_width + 2*tech.pg_signal_spacing + tech.number_of_routing_tracks*tech.layer_width[metal0] + (tech.number_of_routing_tracks -1)*(tech.m0_pitch - tech.layer_width[metal0])

    max_ext_spacing = max(2*tech.gate_extension + tech.vertical_gate_spacing, 2*tech.interconnect_extension + tech.vertical_interconnect_spacing)
    if tech.technology in ['gaa', 'finfet']:
        minimum_cell_height = max_ext_spacing + 2*tech.nanosheet_width + tech.np_spacing 
        if tech.height_req > 1:
            if not minimum_cell_height <= tech.cell_height/2:
                logger.debug(f"No Layout Generated! Minimum Cell Construction Height Not Satisfied")
                return False
        else:
            if not minimum_cell_height <= tech.cell_height:
                logger.debug(f"No Layout Generated! Minimum Cell Construction Height Not Satisfied")
                return False
    else:
        minimum_cell_height = max_ext_spacing + tech.nanosheet_width 
        if tech.height_req > 1:
            if not (minimum_cell_height <= tech.cell_height/2):
                logger.debug(f"No Layout Generated! Minimum Cell Construction Height Not Satisfied")
                return False
        else:
            if not (minimum_cell_height <= tech.cell_height):
                logger.debug(f"No Layout Generated! Minimum Cell Construction Height Not Satisfied")
                return False
    return tech

def make_dummy_metrics(layout_dir, cell_name):
    # make dummy metrics and pex folders
    layout_dir = layout_dir[:-1] if layout_dir.endswith('/') else layout_dir
    parent_dir = '/'.join(layout_dir.split('/')[:-1])
    metrics_path = os.path.join(parent_dir, f'{cell_name}_metrics')
    pex_path = os.path.join(parent_dir, f'{cell_name}_predictions')
    os.makedirs(metrics_path, exist_ok=True)
    os.makedirs(pex_path, exist_ok=True)
    gds_file_names = [name.split('.')[0] for name in os.listdir(layout_dir) if os.path.isfile(os.path.join(layout_dir, name)) and name.endswith('.gds')]
    df = pd.DataFrame(gds_file_names, columns=["File"])
    df.to_csv(f'{metrics_path}/{cell_name}_metrics.csv', index=False)
    df.to_csv(f'{pex_path}/{cell_name}_GDS_PEX_PREDICTION_ML.csv', index=False)

def main(args):
    # List of available placer engines.
    placers = {
        'base0': Base0Wrapper,
        'base1': Base1Wrapper
    }
    placer_dict = defaultdict(lambda: f"placer_{len(placer_dict)}")
    signal_routers = {
        'dijkstra': DijkstraRouter,
    }
    
    layermaps = {
        'gaa': GAALayerMap,
        'cfet': CFETLayerMap,
        'finfet': FINFETLayerMap
    }
    transistor_layouts = {
        'gaa': GAALayout,
        'cfet': CFETLayout,
        'finfet': FinFETLayout
    }
    # Parse arguments
    args_signal_router = args.get("signal_router")
    placement_file = args.get("placement_file") 
    log = '.log.file'#args.get("log")
    quiet = args.get("quiet") 
    output_dir = args.get("output_dir")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if quiet:
        log_level = logging.FATAL
    # Setup logging
    logging.basicConfig(format='%(asctime)s %(module)16s %(levelname)8s: %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S",
                        level=log_level,
                        filename = log)
    # Load netlist of cell
    cell_name = args.get("cell")
    netlist_path = args.get("netlist")
    tech_data = args.get("tech")
    debug_plots = args.get("debug_plots")

    count = {
        'clean': 1,
        'total': 1,
        'pnr_fail': 0
    }
    Path(f'{output_dir}layout_reports/').mkdir(parents=True, exist_ok=True)
   
    tech = load_tech_file(tech_data)
    technology = tech.technology
    layerMap_exporter = layermaps[technology]()
    
    layout_summary = []
    permuteKeys = [key for key,val in tech.permutation.items()]
    permuteValues = [val for key,val in tech.permutation.items()]

    def permuteHelper(count, toVals, layerMap_exporter):
        tech = load_tech_file(tech_data)
        index = 0
        for key,v in tech.permutation.items():
            if key == 'placer':
                continue
            curr = getattr(tech, key[0])
            if isinstance(curr, dict):
                curr[globals().get(key[1], key[1])] = toVals[index]
                setattr(tech, key[0], curr)
            else:
                setattr(tech, key[0], toVals[index])
            index+=1
        message, valid_permutation = permutation_isvalid(tech)
        if not valid_permutation:
            report_name = f'layout_reports/drc_fail_{count["total"]}_{cell_name}.txt'
            make_layout_summary_file(tech, False, False, report_name, count, output_dir)
            count['total'] += 1
            count['pnr_fail'] += 1
            update_summary(tech, False, False, cell_name, permuteKeys, placer_dict, layout_summary, remark=message)
            return
        _, cell_pins = load_transistor_netlist(netlist_path, cell_name)
        io_pins = get_io_pins(cell_pins)
        tech = _adjustTechValues(tech)
        layerMap_exporter.exportLayerMap(tech, f"{args['output_dir']}/layerMap{args['cell']}_{count['clean']}_RT_{tech.number_of_routing_tracks*2}.json", list(io_pins))
        tech = _scale_tech_values(tech)

        routing_tracks_val= _adjust_routing_tracks(tech)

        if not routing_tracks_val:
            return False

        # Create empty layout
        layout = pya.Layout()

        # Setup placer algorithm
        placer = placers[tech.placer]()
        logger.info("Placement algorithm: {}".format(type(placer).__name__))

        # Setup routing algorithm
        signal_router = signal_routers[args_signal_router]()
        logger.info("Signal routing algorithm: {}".format(
            type(signal_router).__name__))

        layout_optimized = pya.Layout()
        layouter = DtcoLayout(tech=tech,
                            layout=layout,
                            layout_optimized=layout_optimized,
                            placer=placer,
                            cell_name=cell_name,
                            debug_plots=debug_plots,
                            defaultTransistorLayout = transistor_layouts[tech.technology])
        # Run layout synthesis
        time_start = time.process_time()      
        try:
            cell = layouter.create_cell_layout(
                cell_name, netlist_path)
            layouter.layer_merging()
        except Exception as e: 
            logger.debug(f"routing Failed for Layout {e}")
            logger.debug(traceback.format_exc())
            report_name = f'layout_reports/drc_fail_{count["total"]}_{cell_name}.txt'
            make_layout_summary_file(tech, False, False, report_name, count, output_dir)
            count['total'] += 1
            count['pnr_fail'] += 1
            update_summary(tech, False, False, cell_name, permuteKeys, placer_dict, layout_summary, remark=str((traceback.format_exc())))
            return
           
        # LVS check
        logger.info("Running LVS check for Stage 1")
        results = LVSChecker(netlist_path, tech, technology, layout, cell, cell_name)
        result= results.run_check()
        lvs_success = result['lvs_success']
        print(f'LVS success : {lvs_success} for {cell_name}')
        logger.info(f'LVS success : {lvs_success} for {cell_name}')

        #Changing layout orientation
        flipping(tech, layout)

        output_writers = [
    
            GdsWriter(
                db_unit=tech.db_unit,
                output_map=tech.layer_map
            ),
        ]
        
        if lvs_success:
            for writer in output_writers:          
                assert isinstance(writer, Writer)
                writer.write_layout(
                        layout=layout,
                        top_cell=cell,
                        output_dir=output_dir
                    )
                old_gds_file_path = Path(f'{output_dir}{cell.name}.gds')
                remane_gds_file_path = old_gds_file_path.with_name(f"{cell.name}_{count['clean']}_RT_{tech.number_of_routing_tracks}.gds")
                old_gds_file_path.rename(remane_gds_file_path)
            gds_name = f"{cell.name}_{count['clean']}_RT_{tech.number_of_routing_tracks}"
            nets = list({shape.text.string for shape in layouter.shapes[metal0_label]} | {shape.text.string for shape in layouter.shapes[metal1_label]})
            highest_metal = 'M1' if len(layouter.shapes[metal1_label]) else 'M0'
            print("\r Generating permutations for cell {}, Generated : {} files".format(cell.name, count['clean']), end='')
            report_name = f'layout_reports/lvs_pass_{count["total"]}_{cell.name}_{count["clean"]}_RT_{tech.number_of_routing_tracks}.txt'
            make_layout_summary_file(tech, True, True, report_name, count, output_dir, gds_name=gds_name, nets=nets, highest_metal=highest_metal, lvs_extracted=str(result['extracted_netlist']), lvs_reference=str(result['reference_netlist']))
            update_summary(tech, True, True, cell_name, permuteKeys, placer_dict, layout_summary, gds_name, layouter.shapes)
            count['clean'] += 1
        else:
            report_name = f'layout_reports/lvs_fail_{count["total"]}_{cell.name}.txt'
            make_layout_summary_file(tech, False, True, report_name, count, output_dir, lvs_extracted=str(result['extracted_netlist']), lvs_reference=str(result['reference_netlist']))
            update_summary(tech, False, True, cell_name, permuteKeys, placer_dict, layout_summary, remark='LVS check failed')
        count['total'] += 1
        time_end = time.process_time()
        duration = datetime.timedelta(seconds=time_end - time_start)
        print("Done (Total duration: {})".format(duration))
    
    def permutation_isvalid(tech):
        message = None
        if tech.layer_width[ppoly] != tech.layer_width[npoly]:
            message = 'No layout generated! We support only the nmos pmos layers with same width.'
        if tech.layer_width[ndiffcon] != tech.layer_width[pdiffcon]:
            message = 'No layout generated! We support only the nmos pmos layers with same width.'
        if tech.technology in ['gaa', 'finfet'] and tech.np_spacing < max(2*tech.gate_extension + tech.vertical_gate_spacing, 2*tech.interconnect_extension + tech.vertical_interconnect_spacing):
            message = 'No layout generated! np spacing, gate/interconnect extension and gate/interconnect spacing calculation not valid'
        # if tech.layer_width[metal0] > tech.layer_width[metal0_track_guide] or tech.layer_width[metal1] > tech.layer_width[metal1_track_guide]:
        #     message = 'No layout generated! Width of metal should be less than width of metal tracks '
        if message: logger.debug(message)
        return message, message is None

    def permute(keys, values, layerMap_exporter):
        
        keys = list(keys)
        values = [list(value) for value in values]
        def helper(index, current_permutation):
            if index == len(keys):
                permute_helper_val = permuteHelper(count, current_permutation.copy(), layerMap_exporter)
                if not permute_helper_val:
                    return False
                return
            for val in values[index]:
                current_permutation[index] = val
                helper_val = helper(index + 1, current_permutation)
                if not helper_val:
                    continue

        helper(0, {})
    permute(permuteKeys, permuteValues, layerMap_exporter)
    print(f"\nGenerated {count['clean']-1} files")

    with open(f'{output_dir}/summary.csv', mode="w", newline="", encoding="utf-8") as file:
        if layout_summary:
            writer = DictWriter(file, fieldnames=layout_summary[0].keys())
            writer.writeheader()
            writer.writerows(layout_summary)

    return {
        'generated': count['clean'] - 1,
        'drc_failures': count['pnr_fail'],
        'lvs_failures': count['total'] - count['clean'] - count['pnr_fail']
    }     
if __name__ == '__main__': 

    import argparse
    parser = argparse.ArgumentParser(
        description='Generate GDS layout from SPICE netlist.')
    parser.add_argument('--cell', required=True,
                        metavar='NAME', type=str, help='cell name (e.g., NAND2X1)')
    parser.add_argument('--netlist', default='cells.sp',
                        metavar='FILE', type=str, help='path to SPICE netlist (cells.sp)')
    parser.add_argument('--output-dir', default='./outputs/', metavar='DIR',
                        type=str, help='output directory for layouts')
    parser.add_argument('--tech', default='tech.py',
                        metavar='FILE', type=str, help='technology file (tech.py)')
    
    args = parser.parse_args()
    args.signal_router = 'dijkstra'
    args.debug_routing_graph = False
    args.debug_smt_solver = False
    args.placement_file = None
    args.log = None
    args.quiet = True
    cell_name = args.cell
    netlist_path = args.netlist
    
    args = {
        "cell":cell_name,
        "netlist":netlist_path,
        "output_dir" :args.output_dir,
        "tech": args.tech,
        "log":None,
        "quiet":True,
        "debug_plots": False
        }
    main(args)