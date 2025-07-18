
logger = logging.getLogger('sivista_app')


def load_tech_file(data={}):
    logger.info('Loading tech file')
    tech_vals = TechFile()
    if isinstance(data, dict):
        adapter = DictionaryAdapter(tech_vals, data)
    elif isinstance(data, str) and data.endswith('.tech'):
        adapter = TextFileAdapter(tech_vals, data)
    elif isinstance(data, str):
        try:
            adapter = JsonAdapter(tech_vals, data)
        except:
            from ast import literal_eval
            data = literal_eval(data)
            if isinstance(data, dict):
                adapter = DictionaryAdapter(tech_vals, data)
            else:
                raise ValueError(f"Invalid data type: {type(data)}")
    adapter.update_values()
    return adapter.tech_file
 
def _scale_tech_values(tech):
    #scale all the parameters
    tech.gate_extension =  int(tech.gate_extension * tech.scaling_factor)
    tech.grid_offset_x =  int(tech.grid_offset_x * tech.scaling_factor)
    tech.grid_offset_y =  int(tech.grid_offset_y * tech.scaling_factor)
    tech.inner_space_width =  int(tech.inner_space_width * tech.scaling_factor)
    tech.interconnect_extension =  int(tech.interconnect_extension * tech.scaling_factor)
    tech.nanosheet_width = int(tech.nanosheet_width * tech.scaling_factor)
    tech.power_rail_width = int(tech.power_rail_width * tech.scaling_factor)
    tech.routing_grid_pitch_x = int(tech.routing_grid_pitch_x * tech.scaling_factor)
    tech.m0_pitch = int(tech.m0_pitch * tech.scaling_factor)
    tech.pg_signal_spacing = int(tech.pg_signal_spacing * tech.scaling_factor)
    tech.np_spacing = int(tech.np_spacing * tech.scaling_factor)
    tech.cell_height = int(tech.cell_height * tech.scaling_factor)
    tech.cell_width = int(tech.cell_width * tech.scaling_factor)
    tech.via_extension = int(tech.via_extension*tech.scaling_factor)
    tech.vertical_gate_spacing = int(tech.vertical_gate_spacing*tech.scaling_factor)
    tech.vertical_interconnect_spacing = int(tech.vertical_interconnect_spacing*tech.scaling_factor)
    tech.vertical_metal_pitch = int(tech.vertical_metal_pitch*tech.scaling_factor)
    for key,value in tech. min_spacing.items():
        tech.min_spacing[key] = int(value*tech.scaling_factor)
    for key,value in tech.layer_width.items():
        tech.layer_width[key] = int(value*tech.scaling_factor)
    for key,value in tech.via_size_horizontal.items():
        tech.via_size_horizontal[key] = int(value * tech.scaling_factor)
    for key,value in tech.via_size_vertical.items():
        tech.via_size_vertical[key] = int(value * tech.scaling_factor)
    return tech

def _adjustTechValues(tech):
    tech.number_of_routing_tracks = int(tech.number_of_routing_tracks)
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
    setattr(tech, 'via_size_vertical', d)
    return tech

def show_nx(Graph, cell_name = 'NOCELL'):
    G_New = nx.Graph()
    color_map = {'ndiffcon': 'steelblue', 'pdiffcon': 'forestgreen', 'ppoly': 'limegreen', 'npoly': 'deepskyblue'}
    node_colors = [color_map.get(node[0], 'darkorange') for node in Graph.nodes()]
    for k,w in Graph.edges.items():
        e1,e2 = k
        w = w['weight']
        G_New.add_edge(str(e1), str(e2), weight=round(w,2))
    pos = { str(node): node[1] for node in Graph.nodes }
    _, ax = plt.subplots()
    nx.draw(G_New, pos=pos, node_color=node_colors, ax=ax)
    plt.axis("on")
    plt.title('All nodes in routing tracks')
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)

    try:
        os.mkdir(f'{cell_name}/plots')
    except OSError as e:
        logger.debug(e.strerror)
    
    plt.savefig(f'{cell_name}/plots/main_graph.png')
    plt.close()
