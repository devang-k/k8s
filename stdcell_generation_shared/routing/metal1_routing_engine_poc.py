logger = logging.getLogger('sivista_app')

def show_nx3d(G, terminal, subgraph, metal0_routing_engine_edges=[], cell_name='NOCELL', num_access_points=0, track_span=0, name_prefix=''):
    G_New = nx.Graph()
    color_map = {'ndiffcon': 'steelblue', 'pdiffcon': 'forestgreen', 'ppoly': 'limegreen', 'npoly': 'deepskyblue', 'metal0_track_guide': 'gold', 'metal1_track_guide': 'goldenrod'} #'metal2_track_guide': 'orangered'
    size_map = {'ndiffcon': 600, 'pdiffcon': 300, 'ppoly': 300, 'npoly': 600}
    z_axis = {'ndiffcon': 0, 'pdiffcon': 1, 'ppoly': 1, 'npoly': 0, 'metal0_track_guide': 1, 'metal1_track_guide': 2} #'metal2_track_guide': 3
    for k,w in G.edges.items():
        try:
            e1, e2, _ = k
        except:
            e1, e2 = k
        w = w['weight']
        if e1[1] != e2[1]:
            G_New.add_edge(e1, e2, weight=round(w,2))
    node_colors = [color_map.get(node[0], 'gold') for node in G_New.nodes()]
    sizes = [size_map.get(node[0], 450) for node in G_New.nodes()]
    pos_3d = {node: (node[1][0], node[1][1], z_axis.get(node[0], 0)) for node in G_New.nodes()}
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    labels = nx.get_edge_attributes(G_New, 'weight')
    metal0_routing_engine_labels = {(n1, n2):int(labels.get((n1, n2), 0)) for n1,n2 in metal0_routing_engine_edges}
    labels = {k:int(v) for k,v in labels.items() if k not in metal0_routing_engine_labels}
    xs = [pos_3d[node][0] for node in G_New.nodes()]
    ys = [pos_3d[node][1] for node in G_New.nodes()]
    zs = [pos_3d[node][2] for node in G_New.nodes()]
    ax.scatter(xs, ys, zs, c=node_colors, s=sizes, alpha=0.5)
    for edge in G_New.edges():
        x_vals = [pos_3d[edge[0]][0], pos_3d[edge[1]][0]]
        y_vals = [pos_3d[edge[0]][1], pos_3d[edge[1]][1]]
        z_vals = [pos_3d[edge[0]][2], pos_3d[edge[1]][2]]
        ax.plot(x_vals, y_vals, z_vals, color='black')
    for edge in metal0_routing_engine_edges:
        x_vals = [pos_3d[edge[0]][0], pos_3d[edge[1]][0]]
        y_vals = [pos_3d[edge[0]][1], pos_3d[edge[1]][1]]
        z_vals = [pos_3d[edge[0]][2], pos_3d[edge[1]][2]]
        ax.plot(x_vals, y_vals, z_vals, color='red')
    plt.axis("on")
    plt.title(f'{name_prefix}{subgraph} - {terminal} terminal for {cell_name}')
    plt.xlabel(f'Subgraph has a span of {track_span}')
    plt.ylabel(f'Number of access points: {num_access_points}')
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.show()
    # plt.savefig(f'{cell_name}/plots/{name_prefix}{terminal}_{subgraph}.png')
    plt.close()

def show_nx2d(G, terminal, metal0_routing_engine_edges=[], cell_name='NOCELL', num_access_points=0, track_span=0, name_prefix='', margin=0):
    G_New = nx.Graph()
    color_map = {'ndiffcon': 'steelblue', 'pdiffcon': 'forestgreen', 'ppoly': 'limegreen', 'npoly': 'deepskyblue', 'metal0_track_guide': 'gold', 'metal1_track_guide': 'orange'} #'metal2_track_guide': 'red'
    size_map = {'ndiffcon': 600, 'pdiffcon': 350, 'ppoly': 350, 'npoly': 600, 'metal0_track_guide': 250, 'metal1_track_guide': 100} #'metal2_track_guide': 100
    for k,w in G.edges.items():
        try:
            e1, e2, _ = k
        except:
            e1, e2 = k
        w = w['weight']
        if e1[1] != e2[1]:
            G_New.add_edge(e1, e2, weight=round(w,2))
    node_colors = [color_map.get(node[0], 'red') for node in G_New.nodes()]
    sizes = [size_map.get(node[0], 450) for node in G_New.nodes()]
    pos = {node: node[1] for node in G_New.nodes()}
    _, ax = plt.subplots()
    labels = nx.get_edge_attributes(G_New, 'weight')
    metal0_routing_engine_labels = {(n1, n2): int(labels.get((n1, n2), 0)) for n1,n2 in metal0_routing_engine_edges}
    labels = {k: int(v) for k,v in labels.items() if k not in metal0_routing_engine_labels}
    xs = [pos[node][0] for node in G_New.nodes()]
    ys = [pos[node][1] for node in G_New.nodes()]
    ax.scatter(xs, ys, c=node_colors, s=sizes, alpha=0.5)
    try:
        for edge in G_New.edges():
            x_vals = [pos[edge[0]][0], pos[edge[1]][0]]
            y_vals = [pos[edge[0]][1], pos[edge[1]][1]]
            ax.plot(x_vals, y_vals, color='black')
            label = labels.get(edge, 0)
            x = (x_vals[0] + x_vals[1]) / 2
            y = (y_vals[0] + y_vals[1]) / 2
            ax.text(x, y, str(label), fontsize=8, color='black', ha='center', va='center')
        for edge in metal0_routing_engine_edges:
            x_vals = [pos[edge[0]][0], pos[edge[1]][0]]
            y_vals = [pos[edge[0]][1], pos[edge[1]][1]]
            ax.plot(x_vals, y_vals, color='red')
            label = metal0_routing_engine_labels.get(edge, 0)
            x = (x_vals[0] + x_vals[1]) / 2
            y = (y_vals[0] + y_vals[1]) / 2
            ax.text(x, y, str(label), fontsize=8, color='red', ha='center', va='center')
    except Exception as e:
        pass
    plt.axis("on")
    plt.title(f'{name_prefix} - {terminal} terminal for {cell_name}')
    plt.xlabel(f'Subgraph has a span of {track_span}')
    plt.ylabel(f'Number of access points: {num_access_points}')
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.savefig(f'{cell_name}/plots/{name_prefix}{terminal}.png')
    plt.close()

class Metal1RoutingEngine(Route):
    def __init__(self, tech, terminals_by_net, track_centers, shapes, abstract_cell, io_pins, cell_name, debug_plots, safe=True):
        super().__init__()
        self.tech = tech
        self.SINGLE_HORIZONTAL_WEIGHT = 1  # Lower weight for single horizontal connection
        self.MULTIPLE_HORIZONTAL_WEIGHT = 10  # Higher weight for multiple horizontal connections
        self.HINDER_PENALTY = 1000
        self.ITERATIONS = 200
        self.track_centers = track_centers
        self.global_center_y = (self.track_centers[0] + self.track_centers[-1])/2
        self.tracks_per_cell = len(track_centers) // self.tech.height_req
        # if self.tech.height_req > 1:
        #     self.cell_height = (self.tech.cell_height + self.tech.power_rail_width)//self.tech.height_req - self.tech.power_rail_width
        # else:
        self.cell_height = self.tech.cell_height
        self.shapes = shapes
        self.unique_points = set()
        self.terminals_by_net = terminals_by_net
        self.illegal_edges = set()
        self.abstract_cell = abstract_cell
        self.io_pins = io_pins
        self.cell_name = cell_name
        self.debug_plots = debug_plots
        self.restricted_nodes = set()
        self.terminal_restrictions = {}
        self.terminal_edges = {}
        self.via_map = {
            (metal0_track_guide, metal1_track_guide): via0,
            (pdiffcon, metal0_track_guide): pviat,
            (ndiffcon, metal0_track_guide): nviat,
            (ppoly, metal0_track_guide): pviag,
            (npoly, metal0_track_guide): nviag
        }
        self.safe = safe
    
    def order_subgraph(self, terminal_subgraph: dict):
        subgraph_list = [[k, v] for k, v in terminal_subgraph.items()]
        nets_at_point = {}
        x_track_nets = defaultdict(list)
        self.priority_tracks = {}
        for subgraph in subgraph_list:
            net = subgraph[0]
            nodes = subgraph[1]
            tracks = {}
            layerTracks = {}
            tracks_y = {}
            track_span = 0
            track_span_y = 0
            for n in nodes:
                layer, (x, y) = n
                tracks.setdefault(y, set()).add(x)
                tracks_y.setdefault(net, set()).add(y)
                layerTracks.setdefault(y, {}).setdefault(layer, []).append(x)
                x_track_nets[x].append(net)
            max_len = max([len(track) for _,track in tracks.items()])
            min_x = 1e7
            max_x = -1e3
            for t in tracks:
                if len(tracks[t]) == max_len:
                    self.priority_tracks[net] = self.priority_tracks.get(net, []) + [t]
                min_x = min(min_x, min(tracks[t]))
                max_x = max(max_x, max(tracks[t]))
            track_span = max_x - min_x
            track_span_y = max(tracks_y[net]) - min(tracks_y[net])
            # Calculation for number of access points
            num_access_points = 0
            for ht in tracks.keys():
                if len(tracks[ht])<max_len:
                    continue
                hindered = False
                npoly_hinder = False
                for layer, x_vals in layerTracks[ht].items():
                    if layer in self.tech.hinder:
                        for x in x_vals:
                            if subgraph[0] != self.node_terminal_info.get((self.tech.hinder[layer], (x, ht)), ''):
                                hindered = True
                                npoly_hinder = layer == 'npoly'
                                break
                if hindered:
                    if npoly_hinder:
                        num_access_points -= 2 # Giving more weightage to hindered npoly nodes than ndiffcon nodes
                    else:
                        num_access_points -= 1
                else: 
                    num_access_points += 1        
            subgraph.extend([num_access_points, track_span, track_span_y])
            if self.debug_plots:
                try:
                    mkdir(f'{self.cell_name}/plots/initial')
                except OSError as e:
                    logger.debug(e.strerror)
                G = nx.Graph()
                for n in nodes: G.add_node(n)
                # Add edges to the graph - horizontal or vertical only
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        # Check if nodes are horizontal or vertical neighbors
                        if nodes[i][1][0] == nodes[j][1][0] or nodes[i][1][1] == nodes[j][1][1]:
                            G.add_edge(nodes[i], nodes[j], weight=0)
                show_nx2d(G, subgraph[0], [], self.cell_name, num_access_points, track_span, 'initial/', margin=2*self.tech.m0_pitch)
        left_nets = Counter()
        right_nets = Counter()
        for nets in x_track_nets.values():
            right_nets.update(nets)
        nets_at_point = {}
        # Traverse from left to right
        for x in sorted(x_track_nets.keys()):
            current_nets = Counter(x_track_nets[x]) 
            right_nets.subtract(current_nets)
            intersection = left_nets & right_nets
            nets_at_point[x] = set(intersection.elements())
            left_nets.update(current_nets)
        subgraph_list.sort(key=lambda x: (x[2], -x[3], -x[4], x[0]))
        subgraph_list = [i for i in subgraph_list if i[0] in self.io_pins or abs(i[3])>0 or abs(i[4])>0]    
        return [tuple(s) for s in subgraph_list], nets_at_point, x_track_nets
    
    def routing_setup(self):
        # remove the VDD and GND from the terminals by net
        self.terminal_subgraph_nodes = defaultdict(lambda: [])
        self.node_terminal_info = defaultdict(lambda: None)
        terminal_region_dict = defaultdict(lambda:pya.Region())
        for terminal_info in self.terminals_by_net:
            terminal,_,_,terminal_region  = terminal_info
            terminal_region_dict[terminal].insert(terminal_region)

        for terminal in terminal_region_dict:
            terminal_region_dict[terminal].merge()

        for terminal_info in self.terminals_by_net:
            terminal, layer, nodes,terminal_region = terminal_info
            #append all info for one terminal in 
            for node in nodes:
                if not is_power_net(terminal):
                    self.unique_points.add(node)
                    #terminal_region_dict[terminal].insert(terminal_region)
                    terminal_region = terminal_region_dict[terminal]
                    margin_x = self.tech.layer_width[layer]//2
                    margin_y = self.tech.layer_width[metal0]//2 + 2*self.tech.via_extension
                    is_interacts =  is_point_near_region(node,terminal_region,margin_x,margin_y)
                    if is_interacts:
                        self.terminal_subgraph_nodes[terminal].append((layer, node))
                    else:
                        continue
                self.node_terminal_info[(layer, node)] = terminal  
        self.terminal_subgraph_nodes, nets_at_point, x_track_nets = self.order_subgraph(self.terminal_subgraph_nodes)
        self.track_x = set()
        self.all_track_x = set()
        self.track_y = set()

        for y in self.track_centers:
            self.track_y.add(y)
            
        allowed_vertical_rt_area = self.tech.cell_width-self.tech.vertical_metal_pitch
        n = allowed_vertical_rt_area%self.tech.vertical_metal_pitch
        diff = self.tech.vertical_metal_pitch/2 + n/2
        left_X = int(diff)
        right_X = self.tech.cell_width
        for x in range(left_X, right_X,self.tech.vertical_metal_pitch):
            self.track_x.add(x)
            self.all_track_x.add(x)
        
        left_X = self.tech.grid_offset_x 
        right_X = self.tech.cell_width 
        for x in range(left_X, right_X, self.tech.routing_grid_pitch_x):
            self.all_track_x.add(x)

    def getValues(self, track, pitch, node_pos):
        l = bisect.bisect_left(track, node_pos-pitch)
        r = bisect.bisect_right(track, node_pos+pitch)
        #print( track, node_pos, pitch, track[l:r])
        return track[l:r]
    
    def get_node_restrictions(self, node, track_x, track_y):
        rest_nodes = set()
        if node[0] == metal0_track_guide:
            for val in self.getValues(track_x, self.tech.vertical_metal_pitch, node[1][0]):
                rest_nodes.add( (metal0_track_guide, (val, node[1][1])))
        if node[0] == metal1_track_guide:
            for val in self.getValues(track_y, self.tech.vertical_metal_pitch, node[1][1]):
                rest_nodes.add( (metal1_track_guide, (node[1][0],val)))
        # if node[0] == metal2_track_guide:
        #     for val in self.getValues(track_x, self.tech.vertical_metal_pitch, node[1][0]):
        #         rest_nodes.add( (metal2_track_guide, (val, node[1][1])))
        return list(rest_nodes)      
    
    def get_restricted_nodes(self, edges):
        rest_nodes = set()
        horizontal_tracks = {}
        for e1, e2 in edges:
            if e1[0] == 'metal0_track_guide' and e2[0] == 'metal0_track_guide':
                y = e1[1][1]
                if y in horizontal_tracks:
                    horizontal_tracks[y].add(e1[1][0])
                    horizontal_tracks[y].add(e2[1][0])
                else:
                    horizontal_tracks[y] = {e1[1][0], e2[1][0]}
        for track in horizontal_tracks.keys():
            rest_nodes.add(('metal0_track_guide', (min(horizontal_tracks[track]) - self.tech.routing_grid_pitch_x, track)))
            rest_nodes.add(('metal0_track_guide', (max(horizontal_tracks[track]) + self.tech.routing_grid_pitch_x, track)))
        track_x = sorted(list(self.all_track_x))
        track_y = sorted(list(self.track_y))
        for e1,e2 in edges:
            for n in self.get_node_restrictions(e1, track_x, track_y):
                rest_nodes.add(n)
            for n in self.get_node_restrictions(e2, track_x, track_y):
                rest_nodes.add(n)
        return rest_nodes

    def node_cost(self, node):
        return 1
    
    def getabs(self, x):
        return abs(x) if x!=0 else 1

    def edge_cost(self, edge):
        ((layer1, (x1, y1)), (layer2, (x2, y2))) = edge
        span_penalty = 0
        # if layer1 == l_metal3_tracks or layer2 == l_metal3_tracks:
        #     span_penalty = 1
        if layer1 in [metal0_track_guide, metal1_track_guide] and layer2 in [metal0_track_guide, metal1_track_guide]: # add l_metal3/l_metal3_tracks in list
            if layer1 != layer2:
                return 0  # orientation change penalty - moving from one metal to another
            delta = 1e-5
            if x1 == x2:
                weight = self.MULTIPLE_HORIZONTAL_WEIGHT  # weight for vertical metal track
            else:
                if self.global_center_y <= y1 <= self.cell_height:
                    global_center_y = self.global_center_y + (self.global_center_y//2)
                else:
                    global_center_y = self.global_center_y - (self.global_center_y//2)
                weight = abs(x1 - x2) # weight for horizontal metal track
                weight = weight/self.getabs(global_center_y - y1) + delta*y2
                if y1 not in self.priority_tracks[self.current_net]:
                    span_penalty = 100
        elif layer1 != layer2:
            weight = 2
        else:
            weight = 1
        return weight * 1000 + span_penalty
    
    def is_metal_used(self, edges):
        for node1, node2 in edges:
            if node1[0] == metal0_track_guide or node2[0] == metal0_track_guide:
                return True
        return False
    
    def add_safe_edge(self, G, e1, e2, weight=None):
        if e1 in self.restricted_nodes or e2 in self.restricted_nodes:
            return
        if not weight:
            weight = self.edge_cost((e1, e2))
        G.add_edge(e1, e2, weight=weight)
    
    def reduceHeight(self, shape_name, x, y):
        track = self.track_centers.index(y)
        cell_mid_point = self.cell_height//2 + ((self.cell_height + self.tech.power_rail_width) * (track//self.tracks_per_cell))
        for shape in self.shapes[shape_name]:
        # Check if the shape intersects at the specified x-coordinate
            bounds = shape.bbox()  # Get the bounding box of the shape
            if bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top:
                shape.delete()
                if y < cell_mid_point:
                    new_bottom = y + self.tech.m0_pitch - self.tech.layer_width[metal0]//2 - self.tech.via_extension
                    box = pya.Box(
                        bounds.left,
                        min(new_bottom, cell_mid_point - self.tech.nanosheet_width//2 - self.tech.interconnect_extension),
                        bounds.right,
                        bounds.top
                    )
                else:
                    new_top = y - self.tech.m0_pitch + self.tech.layer_width[metal0]//2 + self.tech.via_extension
                    box = pya.Box(
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        max(new_top, cell_mid_point + self.tech.nanosheet_width//2 + self.tech.interconnect_extension)
                    )
                self.shapes[shape_name].insert(box)

    def draw_vias_and_tracks(self, edges, metal_name):
        metal_width = {
            metal0_track_guide: self.tech.layer_width[metal0],
            metal1_track_guide: self.tech.layer_width[metal1],
            # l_metal3_tracks: self.tech.layer_width[l_metal3]
        }
        for e1,e2 in edges:
            #print(f'Terminal: {key} E1: {e1} -------->>>>> E2: {e2}')
            if e1[0] == e2[0]:
                if e1[0] in [metal0_track_guide, metal1_track_guide]: # add l_metal3_tracks
                    #print(f"Drawing edge for metal {e1[0]} from {e1[1]} to {e2[1]}")
                    M_Track = pya.Path(
                        [pya.Point(e1[1][0] , e1[1][1]), pya.Point(e2[1][0] , e2[1][1])],
                        metal_width[e1[0]]
                    )
                    M_Track_bbox = M_Track.bbox()
                    text_x = M_Track_bbox.center().x
                    text_y = M_Track_bbox.center().y
                    text = pya.Text(metal_name, pya.Trans(text_x, text_y))
                    text.text_size = 3000
                    
                    # if e1[0]==l_metal3_tracks:
                    #     self.shapes[l_metal3].insert(M_Track)
                    #     self.shapes[l_metal3_label].insert(text)
                    #     if metal_name in self.io_pins:
                    #         self.shapes[l_metal3_pin].insert(M_Track)
                    #         self.shapes[l_metal3_pin_label].insert(text)
                    if e1[0]==metal1_track_guide:
                        self.shapes[metal1].insert(M_Track)
                        self.shapes[metal1_label].insert(text)
                        if metal_name in self.io_pins:
                            self.shapes[metal1_pin].insert(M_Track)
                            self.shapes[metal1_pin_label].insert(text)
                    if e1[0]==metal0_track_guide:
                        self.shapes[metal0].insert(M_Track)
                        self.shapes[metal0_label].insert(text)
                        if metal_name in self.io_pins:
                            self.shapes[metal0_pin].insert(M_Track)
                        if metal_name in self.io_pins:
                            self.shapes[metal0_pin_label].insert(text)
            else:
                #print(f"Entering the Via drawing {(e1[0], e2[0])} - {(e2[0], e1[0])}")
                via_layer = None
                if (e1[0], e2[0]) in self.via_map:
                    via_layer = self.via_map[(e1[0], e2[0])]
                if (e2[0], e1[0]) in self.via_map:
                    via_layer = self.via_map[(e2[0], e1[0])]
                metal_layer = set()
                metal_track_layers = [metal0_track_guide, metal1_track_guide] # add metal2_track_guide
                track_metal = {
                    metal0_track_guide: metal0,
                    metal1_track_guide: metal1,
                    # metal2_track_guide: metal2
                }
                if e1[0] in metal_track_layers:
                    metal_layer.add(track_metal[e1[0]])
                if e2[0] in metal_track_layers:
                    metal_layer.add(track_metal[e2[0]])
                #print(f"drawing the via - {via_layer}")
                if via_layer and e1[1] == e2[1]:
                    via_width = self.tech.via_size_horizontal.get(via_layer, self.tech.via_size[via_layer])
                    via_height = self.tech.via_size_vertical.get(via_layer, self.tech.via_size[via_layer])
                    #print(via_layer, e1, e2, via_height, via_width)
                    #via_width = self.tech.via_size[via_layer]
                    x,y = e1[1]
                    box =  pya.Box(
                            x - via_width//2,
                            y - via_height//2,
                            x + via_width//2,
                            y + via_height//2,
                    ) 
                    if len(metal_layer):
                        M_Track = pya.Path(
                            [pya.Point(e1[1][0] , e1[1][1])
                            ,pya.Point(e2[1][0] , e2[1][1])]
                            , self.tech.layer_width[e1[0]]
                        )
                        if metal0 in metal_layer:
                            M_box =  pya.Box(
                                x - via_width//2,
                                y - self.tech.layer_width[metal0]//2,
                                x + via_width//2,
                                y + self.tech.layer_width[metal0]//2,
                            )
                            self.shapes[metal0].insert(M_box)
                            text_x = M_box.center().x
                            text_y = M_box.center().y
                            text = pya.Text(metal_name, pya.Trans(text_x, text_y))
                            text.text_size = 3000
                            self.shapes[metal0_label].insert(text)
                            if metal_name in self.io_pins:
                                self.shapes[metal0_pin].insert(M_box)
                                self.shapes[metal0_pin_label].insert(text)
                        if metal1 in metal_layer:
                            M_box =  pya.Box(
                                x - self.tech.layer_width[metal1]//2,
                                y - via_height//2,
                                x + self.tech.layer_width[metal1]//2,
                                y + via_height//2,
                            )
                            self.shapes[metal1].insert(M_box)
                            if metal_name in self.io_pins:
                                self.shapes[metal1_pin].insert(M_box)
                        # if l_metal3 in metal_layer:
                        #     M_box =  pya.Box(
                        #         x - via_width//2,
                        #         y - self.tech.layer_width[l_metal3]//2,
                        #         x + via_width//2,
                        #         y + self.tech.layer_width[l_metal3]//2,
                        #     )
                        #     self.shapes[l_metal3].insert(M_box)
                        #     text_x = M_box.center().x
                        #     text_y = M_box.center().y
                        #     text = pya.Text(metal_name, pya.Trans(text_x, text_y))
                        #     text.text_size = 3000
                        #     self.shapes[l_metal3_label].insert(text)
                        #     if metal_name in self.io_pins:
                        #         self.shapes[l_metal3_pin].insert(M_box)
                        #         self.shapes[l_metal3_pin_label].insert(text)
                    self.shapes[via_layer].insert(box)
                    if self.tech.technology == 'cfet' and via_layer == nviat:
                        bottom_layer = e1[0] if e2[0] in [metal0_track_guide, metal1_track_guide] else e2[0]
                        self.reduceHeight(self.tech.hinder[bottom_layer], x, y)
    
    def mergeLabels(self, layer, labelLayer):
        s = self.shapes.get(layer, pya.Region())
        r = pya.Region(s)
        r.merge()
        s.clear()
        s.insert(r)
        layer_shapes = self.shapes[layer]
        all_labels = defaultdict(list)
        label_shapes = self.shapes.get(labelLayer, pya.Region())
        for label in label_shapes.each():
            if label.is_text():
                label = label.text
                all_labels[label.string].append(label.trans.disp)
        label_shapes.clear()
        for layer in layer_shapes.each():
            bbox = layer.bbox()
            center_x = (bbox.p1.x + bbox.p2.x) // 2
            center_y = (bbox.p1.y + bbox.p2.y) // 2
            layer_text = ''
            for text, positions in all_labels.items():
                for pos in positions:
                    if bbox.contains(pya.Point(pos.x, pos.y)):
                        layer_text = text
                        break
                if layer_text:
                    break
            new_text = pya.Text.new(layer_text, pya.Trans(center_x, center_y))
            label_shapes.insert(new_text)


    def check_pin_placement(self):
        # Finds all pin labels and metal labels and adds them in a set
        routed_pins = set()
        routed_terminals = set()
        pin_label_shapes = self.shapes.get(metal0_pin_label, pya.Region())
        metal0_label_shapes = self.shapes.get(metal0_label, pya.Region())
        metal1_label_shapes = self.shapes.get(metal1_label, pya.Region())
        # metal2_label_shapes = self.shapes.get(metal2_label, pya.Region())
        for label in pin_label_shapes.each():
            if label.is_text():
                routed_pins.add(label.text.string)
        for label in metal0_label_shapes.each():
            if label.is_text():
                routed_terminals.add(label.text.string)
        for label in metal1_label_shapes.each():
            if label.is_text():
                routed_terminals.add(label.text.string)
        # for label in metal3_label_shapes.each():
        #     if label.is_text():
        #         routed_terminals.add(label.text.string)
        logger.debug(f'Routed terminals : {routed_terminals}')
        logger.debug(f'Routed pins : {routed_pins}')
        logger.debug(f'Input and output pins as per netlist: {self.io_pins}')
        if not self.tech.backside_power_rail:
            # Removes power nets for Topside power
            for terminal in routed_pins.copy():
                if is_power_net(terminal):
                    routed_pins.remove(terminal)
            logger.debug(f'Routed pins update for Topside power: {routed_pins}')
        # This check confirms that pins are a subset of all terminals
        assert routed_pins.issubset(routed_terminals), "Routed pins not a subset of routed terminals"
        # This check confirms that all pins/terminals in .sbckt definition are routed in the layout, is a routing failure otherwise
        assert self.io_pins.issubset(routed_terminals), "Failed to route all pin terminals"

    def route(self):
        self.routing_setup()
        to_route = self.terminal_subgraph_nodes.copy()
        self.process_routing(to_route)
        for key, value in self.terminal_edges.items():
            self.draw_vias_and_tracks(value, key)
        self.mergeLabels(metal0, metal0_label)
        self.mergeLabels(metal1, metal1_label)
        # self.mergeLabels(metal2, metal2_label)
        self.mergeLabels(metal0_pin, metal0_pin_label)
        self.mergeLabels(metal1_pin, metal1_pin_label)
        # self.mergeLabels(metal2_pin, metal2_pin_label)
        self.check_pin_placement()
        return self.shapes

    def process_routing(self, to_route):
        routed = []
        curr_iteration = 0
        memo = set()
        while to_route and curr_iteration < self.ITERATIONS:
            logger.debug(f'To route: {[i[0] for i in to_route]}, routed: {[i[0] for i in routed]}')
            curr_routing_terminal = to_route.pop(0)
            terminal_net, terminal_nodes, num_access_points, track_span, track_span_y = curr_routing_terminal
            self.current_net = terminal_net
            nodes = set()
            track_x = self.track_x.copy()
            G = nx.Graph()

            for x in track_x:
                for y in self.track_y:
                    nodes.add((metal0_track_guide, (x,y)))
                    nodes.add((metal1_track_guide, (x,y)))
                    # nodes.add((metal2_track_guide, (x,y)))
                    #adding via from metal tracks
                    self.add_safe_edge(
                        G,
                        (metal0_track_guide, (x,y)),
                        (metal1_track_guide, (x,y))
                    )
                    # self.add_safe_edge(
                    #     G,
                    #     (l_metal2_tracks, (x,y)),
                    #     (l_metal3_tracks, (x,y))
                    # )

            li = sorted(list(self.track_y))
            for x in track_x:
                for i in range(1, len(li)):
                    y1, y2 = li[i-1], li[i]
                    self.add_safe_edge(
                        G,
                        (metal1_track_guide, (x,y1)), 
                        (metal1_track_guide, (x,y2))
                    )

            point_dict = dict()
            for node in terminal_nodes:
                if node[0] in self.tech.hinder:
                    if self.node_terminal_info.get((self.tech.hinder[node[0]], node[1]), terminal_net) != terminal_net:
                        if node[0] == npoly:
                            continue
                        if node[0] == ndiffcon:
                            via_width = self.tech.via_size_horizontal.get(nviat, self.tech.via_size[nviat])
                            via_height = self.tech.via_size_vertical.get(nviat, self.tech.via_size[nviat])
                            x,y = node[1]
                            box = pya.Box(
                                x - via_width//2,
                                y - via_height//2,
                                x + via_width//2,
                                y + via_height//2,
                            )
                            if not pya.Region(self.shapes[pdiff]).get_nearby_points(pya.Region(box)).is_empty():
                                # self.shapes[l_test].insert(box)
                                continue
                    if node[0] == npoly and not self.node_terminal_info.get((self.tech.hinder[node[0]], node[1]), None):
                        via_height = self.tech.via_size_vertical[nviag]
                        via_width = self.tech.via_size_vertical[nviag]
                        x,y = node[1]
                        box = pya.Box(
                            x - via_width//2,
                            y - via_height//2,
                            x + via_width//2,
                            y + via_height//2,
                        )
                        if not pya.Region(self.shapes[self.tech.hinder[npoly]]).get_nearby_points(pya.Region(box)).is_empty():
                            # self.shapes[l_test].insert(box)
                            continue
                if node[1] not in point_dict:
                    point_dict[node[1]] = node
                else:
                    currNodeType, prevNodeType = node[0], point_dict[node[1]][0]
                    if routing_order[prevNodeType] > routing_order[currNodeType]:
                        point_dict[node[1]] = node
            nodes = list(point_dict.values())
            terminals = sorted(nodes, key=lambda x: (x[1][0], x[1][1]))
            #add a via from to m0
            for i in range(1,len(terminals)):
                e1, e2 = terminals[i-1], terminals[i]
                track_x.add(e1[1][0])
                track_x.add(e2[1][0])
                if e1[1][0] == e2[1][0]: # x coordinates are the same
                    if e1[0] == e2[0] and abs(e1[1][1] - e2[1][1]) <= self.tech.m0_pitch: # If layers are equal & difference between y coords
                        self.add_safe_edge(G, e1, e2)
                    elif e1[0] != e2[0] and abs(e1[1][1] - e2[1][1]) <= self.tech.m0_pitch:
                        self.add_safe_edge(G, e1, e2)
                #edge to metal
                self.add_safe_edge(G, (metal0_track_guide, e1[1]), e1)
                self.add_safe_edge(G, (metal0_track_guide, e2[1]), e2)
            for y in self.track_y:
                li = sorted(list(track_x))
                for i in range(1, len(li)):
                    x1, x2 = li[i-1], li[i]
                    self.add_safe_edge(
                        G,
                        (metal0_track_guide, (x1,y)),
                        (metal0_track_guide, (x2,y))
                    )
                    # self.add_safe_edge(
                    #     G,
                    #     (l_metal3_tracks, (x1,y)),
                    #     (l_metal3_tracks, (x2,y))
                    # )
            if self.debug_plots:
                try:
                    mkdir(f'{self.cell_name}/plots/point_set')
                except OSError as e:
                    logger.debug(e.strerror)
                show_nx2d(G, terminal_net, [], self.cell_name, num_access_points, track_span, 'point_set/', margin=2*self.tech.m0_pitch)
            router = DijkstraRouter()

            try:
                tree = router.route(G, terminals, node_cost_fn=self.node_cost, edge_cost_fn=self.edge_cost)
                assert nx.is_tree(tree), "Routing solution should be a tree!"
                for n in terminals:
                    assert n in tree, "Terminal is not in routing tree!"
                if self.debug_plots:
                    try:
                        mkdir(f'{self.cell_name}/plots/before')
                    except OSError as e:
                        logger.debug(e.strerror)
                    show_nx2d(G, terminal_net, [], self.cell_name, num_access_points, track_span, 'before/', margin=2*self.tech.m0_pitch)
                edges = list(tree.edges)
                
                if self.debug_plots:
                    try:
                        mkdir(f'{self.cell_name}/plots/after')
                    except OSError as e:
                        logger.debug(e.strerror)
                    show_nx2d(G, terminal_net, edges, self.cell_name, num_access_points, track_span, 'after/', margin=2*self.tech.m0_pitch)
                if not self.is_metal_used(edges) and terminal_net in self.io_pins:
                    node = None
                    for node1, node2 in edges:
                        if not node and (metal0_track_guide, node1[1]) not in self.restricted_nodes:
                            node = node1
                            break
                        elif not node and (metal0_track_guide, node2[1]) not in self.restricted_nodes:
                            node = node2
                            break
                    assert node is not None, f"No place to route pin {terminal_net}"
                    if node:
                        edges.append((node, (metal0_track_guide, node[1])))
                        edges.append(((metal0_track_guide, node[1]), (metal0_track_guide, node[1])))
                
                self.terminal_restrictions[terminal_net] = self.get_restricted_nodes(edges)
                self.restricted_nodes.update(self.terminal_restrictions[terminal_net])
                self.terminal_edges[terminal_net] = edges
                routed.append(curr_routing_terminal)
                logger.debug(f'Successfully routed {terminal_net}')
            
            except Exception as e:
                logger.debug(f'Failed to route {terminal_net}')
                # traceback.print_exc()
                if not routed:
                    to_route.insert(1, curr_routing_terminal)
                else:
                    self.remove_route(routed[-1][0])
                    to_route.insert(0, curr_routing_terminal)
                    to_route.insert(1, routed[-1])
                    routed = routed[:-1]
                    def create_memo(nets_list):
                        return '-'.join([subgraph[0] for subgraph in nets_list])
                    if create_memo(to_route) in memo and routed:
                        logger.debug(f'{create_memo(to_route)} has been seen before so we unroute {routed[-1][0]}')
                        self.remove_route(routed[-1][0])
                        to_route.insert(1, routed[-1])
                        routed = routed[:-1]
                    memo.add(create_memo(to_route))
            
            curr_iteration += 1

        logger.debug(f'Routed: {[i[0] for i in routed]}')
        assert len(routed) == len(self.terminal_subgraph_nodes), "Failed to route all terminals."

    def remove_route(self, terminal):
        self.terminal_edges[terminal] = []
        self.terminal_restrictions[terminal] = set()
        self.restricted_nodes = set.union(*self.terminal_restrictions.values())