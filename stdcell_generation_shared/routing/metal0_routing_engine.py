logger = logging.getLogger('sivista_app')

def show_nx(G, terminal, subgraph, metal0_routing_engine_edges=[], cell_name='NOCELL', num_access_points=0, track_span=0, name_prefix=''):
    G_New = nx.Graph()
    color_map = {'ndiffcon': 'steelblue', 'pdiffcon': 'forestgreen', 'ppoly': 'limegreen', 'npoly': 'deepskyblue'}
    size_map = {'ndiffcon': 600, 'pdiffcon': 300, 'ppoly': 300, 'npoly': 600}
    for k,w in G.edges.items():
        try:
            e1, e2, _ = k
        except:
            e1, e2 = k
        w = w['weight']
        if e1[1] != e2[1]:
            G_New.add_edge(e1, e2, weight=round(w,2))
    pos = { node: node[1] for node in G_New.nodes }
    node_colors = [color_map.get(node[0], 'gold') for node in G_New.nodes()]
    sizes = [size_map.get(node[0], 450) for node in G_New.nodes()]
    legend_labels = [Patch(facecolor=color, label=label) for label, color in color_map.items()]
    _, ax = plt.subplots()
    labels = nx.get_edge_attributes(G_New, 'weight')
    metal0_routing_engine_labels = {(n1, n2):int(labels.get((n1, n2), 0)) for n1,n2 in metal0_routing_engine_edges}
    labels = {k:int(v) for k,v in labels.items() if k not in metal0_routing_engine_labels}
    nx.draw_networkx_nodes(G_New, pos=pos, node_color=node_colors, node_size=sizes, ax=ax, alpha=0.5)
    nx.draw_networkx_edges(G_New, pos, edgelist=[k for k in labels], style='solid', edge_color='black')
    nx.draw_networkx_edges(G_New, pos, edgelist=[k for k in metal0_routing_engine_labels], style='solid', edge_color='red')
    nx.draw_networkx_edge_labels(G_New, pos, edge_labels=labels, ax=ax, font_size=8)
    nx.draw_networkx_edge_labels(G_New, pos, edge_labels=metal0_routing_engine_labels,font_color='red', ax=ax, font_size=8)
    plt.axis("on")
    plt.title(f'{name_prefix}{subgraph} - {terminal} terminal for {cell_name}')
    plt.xlabel(f'Subgraph has a span of {track_span}')
    plt.ylabel(f'Number of access points: {num_access_points}')
    plt.legend(handles=legend_labels, title="Node Types")
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.savefig(f'{cell_name}/plots/{name_prefix}{terminal}_{subgraph}.png')
    plt.close()

class Metal0RoutingEngine(Route):
    def __init__(self, tech, terminals_by_net, track_centers, shapes, abstract_cell, io_pins, cell_name, debug_plots, safe=True):
        super().__init__()
        self.tech = tech
        self.SINGLE_HORIZONTAL_WEIGHT = 1  # Lower weight for single horizontal connection
        self.MULTIPLE_HORIZONTAL_WEIGHT = 10  # Higher weight for multiple horizontal connections
        self.HINDER_PENALTY = 1000
        self.SPAN_PENALTY = 1000
        self.global_center_y = (tech.cell_height + tech.power_rail_width//2)//2
        self.track_centers = track_centers
        self.global_center_y = (track_centers[0] + track_centers[-1])/2
        self.shapes = shapes
        self.unique_points = set()
        self.terminals_by_net = terminals_by_net
        self.illegal_edges = set()
        self.abstract_cell = abstract_cell
        self.io_pins = io_pins
        self.cell_name = cell_name
        self.debug_plots = debug_plots
        self.safe = safe
        self.nanosheet_region = calculate_nanosheet_region(self.shapes)
        self.via_dict = {}
        self.cell_bottom_y = - self.tech.power_rail_width//2
        self.cell_center_y = self.tech.cell_height//2
        self.cell_top_y = self.tech.cell_height + self.tech.power_rail_width//2
        self.interconnect_via_center_list = polygon_centers(self.shapes, diff_interconnect)

    def calculate_restricted_extension(self, min_extension, layer_t=''):
        """Calculates region of min extension of gate/diffcon from the nanosheet"""
        bbox = self.nanosheet_region.bbox()
        expanded_region = pya.Region().insert(pya.DBox(bbox.left, bbox.bottom - min_extension, bbox.right, bbox.top + min_extension))
        for layer, _shapes in self.shapes.items():        
            if layer == gate_isolation and layer_t == 'gate':
                gate_diffusion_region = optimize_shape_merge(_shapes)
                if not gate_diffusion_region:
                    expanded_region = ()
                    return expanded_region
                expanded_region = expanded_region & gate_diffusion_region
        return expanded_region
    
    def is_connected(self,edge_list,complete_graph,terminal):
        """
        check if the graph is connected
        @returns 
        True: if graph is connected
        False: if graph is not connected
        """
        G = nx.Graph()
        G.add_nodes_from(complete_graph)     
        G.add_edges_from(edge_list)
        if nx.is_empty(G):
            print((f"{terminal} has an empty graph.."))
            assert False,"Graph is empty"
   
        if not nx.is_connected(G) :
            print(f"{terminal} has disconnected graph")
            logger.error(f"Terminal : {terminal} has disconnected graph") 
        assert nx.is_connected(G)

        return True    

    def pitch_variables(self, node):
        x,y = node
        self.illegal_edges.add((x,y))
        self.illegal_edges.add((x-self.tech.routing_grid_pitch_x, y))
        self.illegal_edges.add((x+self.tech.routing_grid_pitch_x, y))

    def pitch_variables_AB(self, node1, node2):
        x1 , y1 = node1
        x2 , y2 = node2
        if x1>x2:
            x1,x2 = x2,x1
        if y1!=y2:
            assert False, 'A non horizontal edge is places'
        for point in self.unique_points:
            x,y = point
            if y==y1 and x>=x1 and x<=x2:
                self.pitch_variables((x,y))

    def calculate_invalid_node(self, node):
        """For input node, returns a flag that defines if a node is invalid for routing
        because of CFET hindering
        """
        base_layer, (x, y) = node
        point = x, y
        for terminal in self.via_dict:
            for node_range in self.via_dict[terminal]:
                base_layer_ref, (x_ref, y_ref), (x1, (y1, y2)) = node_range            
                invalid_range = x1, (y1, y2)
                if self.is_point_in_range(point, invalid_range):
                    if {base_layer, base_layer_ref} in [{ppoly, npoly}, {pdiffcon, ndiffcon}]:
                        return True
        return False

    def is_point_in_range(self, point, range_tuple):
        x, (y1, y2) = range_tuple
        X1, Y1 = point
        return X1 == x and y1 <= Y1 <= y2

    def calculate_restricted_range(self, layer, node):
        """"Calculates a restricted range of opposing layer in CFET
        """
        restricted_range = 0, (0, 0)
        x, y = node
        if layer in [ppoly, pdiffcon]:
            # Restricted range for npoly and ndiffcon
            if self.cell_center_y <= y <= self.cell_top_y:
                restricted_range = x, (self.cell_center_y, y)
            else:
                restricted_range = x, (y, self.cell_center_y)
        if layer in [npoly, ndiffcon]:
            # Restricted range for ppoly and pdiffcon
            if self.cell_center_y <= y <= self.cell_top_y:
                restricted_range = x, (y, self.cell_top_y) 
            else:
                restricted_range = x, (self.cell_bottom_y, y)
        return restricted_range
    
    def create_via_dict(self, terminal, base_layer, node):
        """Finds location of via placement from routed graph edges
        """
        rest_range = self.calculate_restricted_range(base_layer, node)
        self.via_dict.setdefault(terminal, []).append((base_layer, node, rest_range)) 

    def reduceHeight(self, shape_name, x, y, min_extension):
        for shape in self.shapes[shape_name]:
        # Check if the shape intersects at the specified x-coordinate
            bounds = shape.bbox()  # Get the bounding box of the shape
            if bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top:
                shape.delete()
                if y < self.tech.cell_height//2:
                    new_bottom = y + self.tech.m0_pitch - self.tech.layer_width[metal0]//2 - 2*self.tech.via_extension
                    box = pya.Box(
                        bounds.left,
                        min(new_bottom, self.tech.cell_height//2 - self.tech.nanosheet_width//2 - min_extension),
                        bounds.right,
                        bounds.top
                    )
                else:
                    new_top = y - self.tech.m0_pitch + self.tech.layer_width[metal0]//2 + 2*self.tech.via_extension
                    box = pya.Box(
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        max(new_top, self.tech.cell_height//2 + self.tech.nanosheet_width//2 + min_extension)
                    )
                self.shapes[shape_name].insert(box)

    def getabs(self, x):
        return abs(x) if x!=0 else 1
    
    def check_pin_placement(self):
        # Finds all pin labels and metal labels and adds them in a set
        routed_pins = set()
        routed_terminals = set()
        pin_label_shapes = self.shapes.get(metal0_pin_label, pya.Region())
        metal0_label_shapes = self.shapes.get(metal0_label, pya.Region())
        for label in pin_label_shapes.each():
            if label.is_text():
                routed_pins.add(label.text.string)
        for label in metal0_label_shapes.each():
            if label.is_text():
                routed_terminals.add(label.text.string)
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
        assert self.io_pins == routed_pins, "Failed to route all pin terminals"

    def metal0_routing_engine_routing(self, terminal_subgraph_nodes: list, weightFn: str = None, subgraph_name: str = ''):
        for terminal, nodes, num_access_points, track_span in terminal_subgraph_nodes:
            complete_graph = nx.Graph()
            point_dict = dict()
            for node in nodes:
                if self.tech.technology == 'cfet':
                    flag = self.calculate_invalid_node(node) 
                    if flag: continue
                if node[1] not in point_dict:
                    point_dict[node[1]] = node
                else:
                    currNodeType, prevNodeType = node[0], point_dict[node[1]][0]
                    if routing_order[prevNodeType] > routing_order[currNodeType]:
                        point_dict[node[1]] = node
            nodes = list(point_dict.values())
            nodes.sort(key=lambda x: (x[1][0], x[1][1]))
            for i in range(len(nodes)-1, -1, -1):
                if nodes[i][1] in self.illegal_edges:
                    continue
                for j in range(i, len(nodes)):
                    if nodes[j][1] in self.illegal_edges:
                        continue
                    if nodes[i][1][1] == nodes[j][1][1] and nodes[i][1][0] != nodes[j][1][0]:
                        #check if any of the nodes in between the nodes[i] and nodes[j] are already used
                        start_x = min(nodes[i][1][0],nodes[j][1][0])
                        end_x = max(nodes[i][1][0],nodes[j][1][0])
                        check_y = nodes[i][1][1]
                        illegal = False
                        intermediate_nodes = []
                        for x in range(start_x, end_x+1, self.tech.routing_grid_pitch_x):
                            if (x,check_y) in self.illegal_edges:
                                illegal = True
                                break
                            if (x, check_y) in point_dict:
                                intermediate_nodes.append(point_dict[(x, check_y)])
                        if illegal:
                            continue
                        if len(intermediate_nodes)==1:
                            intermediate_nodes.extend(intermediate_nodes)
                        intermediate_nodes = [[intermediate_nodes[i], intermediate_nodes[i+1]] for i in range(len(intermediate_nodes)-1)]
                        weight = abs(nodes[i][1][0] - nodes[j][1][0])   # Horizontal distance + number of hindered nodes as base edge weight
                        weight = (weight * self.MULTIPLE_HORIZONTAL_WEIGHT) / len(intermediate_nodes)
                        span_penalty = self.SPAN_PENALTY if end_x - start_x < track_span else 0
                        delta = 1e-6
                        if weightFn:
                            if weightFn=="topBottomPriority":
                                weight = weight/self.getabs(self.global_center_y - nodes[i][1][1]) + delta*nodes[i][1][1]
                                complete_graph.add_edges_from(intermediate_nodes, weight=weight/len(intermediate_nodes) + span_penalty)
                            elif weightFn=="midPriority":
                                weight = 1/(weight/self.getabs(self.global_center_y - nodes[i][1][1]) + delta*nodes[i][1][1])
                                complete_graph.add_edges_from(intermediate_nodes, weight=weight/len(intermediate_nodes) + span_penalty)
                            elif weightFn=="topPriority":
                                weight = weight/self.getabs(self.global_center_y - nodes[i][1][1]) if (self.global_center_y - nodes[i][1][1])<0 else 20*weight*self.getabs(self.global_center_y - nodes[i][1][1]) + delta*nodes[i][1][1]
                                complete_graph.add_edges_from(intermediate_nodes, weight=weight/len(intermediate_nodes) + span_penalty)
                            elif weightFn=="bottomPriority":
                                weight = weight/self.getabs(self.global_center_y - nodes[i][1][1]) if (self.global_center_y - nodes[i][1][1])>0 else 20*weight*self.getabs(self.global_center_y - nodes[i][1][1]) + delta*nodes[i][1][1]
                                complete_graph.add_edges_from(intermediate_nodes, weight=weight/len(intermediate_nodes) + span_penalty)
                        else:
                            weight = abs(self.global_center_y - nodes[i][1][1])*weight + delta*nodes[i][1][1]
                            complete_graph.add_edges_from(intermediate_nodes, weight=weight/len(intermediate_nodes) + span_penalty)
                        
                    elif nodes[i][1][0] == nodes[j][1][0]:
                        complete_graph.add_edge(nodes[i], nodes[j], weight=0)
            if self.debug_plots:
                makedirs(f'{self.cell_name}/plots/pre_metal0_routing_engine', exist_ok=True)
                show_nx(complete_graph, terminal, subgraph_name, [], self.cell_name, num_access_points, track_span, 'pre_metal0_routing_engine/')
            # Compute Minimum Spanning Tree
            if len(complete_graph.nodes())==1:
                edge_list = list(complete_graph.edges())
            else:
                metal0_routing_engine_edges = nx.minimum_spanning_edges(complete_graph, algorithm='kruskal', data=True)
                metal0_routing_engine_edges = list(metal0_routing_engine_edges)
                edge_list = [(e[0], e[1]) for e in metal0_routing_engine_edges]
                if self.safe:
                    self.is_connected(edge_list,complete_graph,terminal)
                if self.debug_plots:
                    show_nx(complete_graph, terminal, subgraph_name, edge_list, self.cell_name, num_access_points, track_span)
            horizontal_edges = {}
            
            for node1, node2 in edge_list:
                if node1[1][1] == node2[1][1] and node1[1][0] != node2[1][0]:
                    self.pitch_variables_AB(node1[1], node2[1])
                    horizontal_edges[(node1,node2)] = terminal
                    #horizontal_edges[node2] = terminal
            if len(horizontal_edges)==0 and terminal in self.io_pins:
                node = None
                for node1, node2 in edge_list:
                    if not node and node1[1] not in self.illegal_edges:
                        node = node1
                    if abs(self.global_center_y-node1[1][1])<=abs(self.global_center_y-node[1][1]) and node1[1] not in self.illegal_edges:
                        node = node1
                    elif abs(self.global_center_y-node2[1][1])<=abs(self.global_center_y-node[1][1]) and node2[1] not in self.illegal_edges:
                        node = node2
                if node:
                    self.pitch_variables(node[1])
                    horizontal_edges[(node,node)] = terminal
            if not len(horizontal_edges):
                continue
            
            points = defaultdict(lambda:[])
            for temp_vias in horizontal_edges.keys():
                temp_vias = sorted(temp_vias, key = lambda x: x[1][0])
                start = list(temp_vias[0][1])
                end = start.copy()
                startLayer = None
                endLayer = None
               
                for l, (x,y) in temp_vias:
                    points[y].append((l,x,y))
                    if x<=start[0]:
                        start = [x,y]
                        startLayer = l
                    if x>=end[0]:
                        end = [x,y]
                        endLayer = l 
                    if l == 'pdiffcon' or l=='ndiffcon':
                        if self.node_terminal_info.get(('pdiffcon', (x,y)), '') == terminal:
                            self.shapes[pviat].insert(create_rectangle_from_center(x,y,self.tech.via_size_horizontal[pviat], self.tech.via_size_vertical[pviat]))
                            if self.tech.technology == 'cfet':
                                self.create_via_dict(terminal, pdiffcon, (x, y))
                        else:
                            self.shapes[nviat].insert(create_rectangle_from_center(x,y,self.tech.via_size_horizontal[pviat], self.tech.via_size_vertical[pviat]))
                            self.reduceHeight(pdiffcon, x, y, self.tech.interconnect_extension)
                            if self.tech.technology == 'cfet':
                                self.create_via_dict(terminal, ndiffcon, (x, y))
                    else:
                        if self.node_terminal_info.get(('ppoly', (x,y)), '') == terminal:
                            self.shapes[pviag].insert(create_rectangle_from_center(x,y,self.tech.via_size_horizontal[pviag], self.tech.via_size_vertical[pviag]))
                            if self.tech.technology == 'cfet':
                                self.create_via_dict(terminal, ppoly, (x, y)) 
                        else:
                            self.shapes[nviag].insert(create_rectangle_from_center(x,y,self.tech.via_size_horizontal[pviag], self.tech.via_size_vertical[pviag]))
                            self.reduceHeight(ppoly, x, y, self.tech.gate_extension)
                            if self.tech.technology == 'cfet':
                                self.create_via_dict(terminal, npoly, (x, y))

                if startLayer == 'pdiffcon' or startLayer=='ndiffcon': 
                    start[0] = start[0] - self.tech.via_size_horizontal[pviat]//2
                else:
                    start[0] = start[0] - self.tech.via_size_horizontal[pviag]//2
                
                if endLayer == 'pdiffcon' or endLayer=='ndiffcon': 
                    end[0] = end[0] + self.tech.via_size_horizontal[pviat]//2
                else:
                    end[0] = end[0] + self.tech.via_size_horizontal[pviag]//2
                M0_Box = pya.Path(
                    [pya.Point(start[0],start[1]),
                    pya.Point(end[0], end[1])],
                    self.tech.layer_width[metal0]
                )
                self.shapes[metal0].insert(M0_Box)
                # Insert pin polygon for inputs & outputs
                if terminal in self.io_pins:
                    self.shapes[metal0_pin].insert(M0_Box)
            for y, coords in points.items():
                lis = [x for _,x,_ in coords ]
                text_x = sum(lis)//len(lis)
                text_y = y
                text = pya.Text(terminal, pya.Trans(text_x, text_y))
                text.text_size = 3000
                self.shapes[metal0_label].insert(text)
                # Insert pin label for inputs and outputs
                if terminal in self.io_pins:
                    self.shapes[metal0_pin_label].insert(text)

    def draw_inital_plot(self, nodes, subgraph, num_access_points, track_span):
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
        show_nx(G, subgraph[0], '', [], self.cell_name, num_access_points, track_span, 'initial/')
    
    def order_subgraph(self, terminal_subgraph: dict):
        subgraph_list = [[k, v] for k, v in terminal_subgraph.items()]
        nets_at_point = {}
        x_track_nets = defaultdict(list)
        self.priority_tracks = {}
        for subgraph in subgraph_list:
            net = subgraph[0]
            nodes = subgraph[1]
            tracks = {}
            tracks_width = {}
            layerTracks = {}
            track_span = 0
            # Calculation for span
            for n in nodes:
                layer, (x, y) = n
                tracks_width.setdefault(net, set()).add(x)
                tracks.setdefault(y, set()).add(x)
                layerTracks.setdefault(y, {}).setdefault(layer, []).append(x)
                x_track_nets[x].append(net)
            max_len = max([len(track) for _,track in tracks.items()]) # finds most number of x values stored in any y
            track_span = max(tracks_width[net]) - min(tracks_width[net])
            # Calculation for number of access points
            num_access_points = 0
            for ht in tracks.keys():
                if len(tracks[ht])<max_len:
                    continue
                hindered = False
                for layer, x_vals in layerTracks[ht].items():
                    if layer in self.tech.hinder:
                        for x in x_vals:
                            if subgraph[0] != self.node_terminal_info.get((self.tech.hinder[layer], (x, ht)), ''):
                                hindered = True
                                break
                if hindered:
                    num_access_points -= 1
                else: 
                    num_access_points += 1
                        
            subgraph.extend([num_access_points, track_span])
            if self.debug_plots:
                self.draw_inital_plot(nodes, subgraph, num_access_points, track_span)
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
        subgraph_list.sort(key=lambda x: (x[2], -x[3], x[0]))
        subgraph_list = [i for i in subgraph_list if i[0] in self.io_pins or abs(i[3])>0]
        return [tuple(s) for s in subgraph_list]

    def routing_setup(self):
        #remove the VDD and GND from the terminals by net
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
                    if layer in self.tech.hinder:
                        terminal_region -= self.nanosheet_region
                        if layer == npoly:
                            gate_extension_region = self.calculate_restricted_extension(self.tech.gate_extension, "gate")
                            if gate_extension_region == ():
                                terminal_region += self.nanosheet_region
                            else:
                                terminal_region -= gate_extension_region
                        if layer == ndiffcon:
                            x, y = node
                            if x in self.interconnect_via_center_list:
                                terminal_region += self.nanosheet_region
                            else: 
                                diffcon_extension_region = self.calculate_restricted_extension(self.tech.interconnect_extension)
                                terminal_region -= diffcon_extension_region
                    margin_x = self.tech.layer_width[layer]//2
                    margin_y = self.tech.layer_width[metal0]//2 + 2*self.tech.via_extension
                    is_interacts =  is_point_near_region(node,terminal_region,margin_x,margin_y)
                    if is_interacts:
                        self.terminal_subgraph_nodes[terminal].append((layer, node))
                    else:
                        continue
                self.node_terminal_info[(layer, node)] = terminal 
        self.terminal_subgraph_nodes = self.order_subgraph(self.terminal_subgraph_nodes) 
        return

    def route(self):
        self.routing_setup()
        self.metal0_routing_engine_routing(self.terminal_subgraph_nodes, "topBottomPriority", 'all_subgraph_nodes')
        self.check_pin_placement()
        return self.shapes