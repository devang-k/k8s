logger = logging.getLogger('sivista_app')
class DtcoLayout:

    def __init__(self,
                 tech,
                 layout: pya.Layout,
                 layout_optimized: pya.Layout,
                 placer: BasePlacement,
                 debug_routing_graph: bool = False,
                 debug_smt_solver: bool = False,
                 cell_name: str = '_',
                 debug_plots: bool = False,
                 defaultTransistorLayout = CFETLayout
                 ):
        assert isinstance(layout, pya.Layout)
        assert isinstance(layout_optimized, pya.Layout)
        assert isinstance(placer, BasePlacement)

        self.tech = tech
        self.layout = layout
        self.layout_optimized = layout_optimized
        self.placer = placer
        self.debug_routing_graph = debug_routing_graph
        self.debug_smt_solver = debug_smt_solver
        self.debug_plots = debug_plots
        self.cell_name = cell_name
        self.io_pins = None
        self.supply_voltage_net = None
        self.gnd_net = None

        # Top layout cell.
        self.top_cell: pya.Cell = None
        self.top_cell_optimized: pya.Cell = None
        self.abstract_transistors: List[Transistor] = None
        self.transistor_layout: Dict[Transistor, Device] = None
        self.shapes: Dict[str, db.Shapes] = dict()
        self.shapes_optimized: Dict[str, db.Shapes] = dict()
        self._routing_terminal_debug_layers = None
        self.temp_cell: Cell = None
        self.cell_width = None
        self.cell_height = None

        # Routing graph.
        self._routing_graph: nx.Graph = None
        self._routing_trees = None

        # Pin definitions.
        self.defaultTransistorLayout = defaultTransistorLayout
        self.PTG_count = 1

    def netlist_loader(self, netlist_path: str, cell_name: str):
        # Load netlist of cell.

        logger.info(f'Load netlist: {netlist_path}')
        self.cell_name = cell_name

        self.abstract_transistors, cell_pins = load_transistor_netlist(
            netlist_path, cell_name)
        
        self.io_pins = get_io_pins(cell_pins)

        ground_nets = {p for p in cell_pins if is_ground_net(p)}
        supply_nets = {p for p in cell_pins if is_supply_net(p)}
        assert len(ground_nets) > 0, "Could not find net name of ground."
        assert len(supply_nets) > 0, "Could not find net name of supply voltage."
        assert len(ground_nets) == 1, "Multiple ground net names: {}".format(
            ground_nets)
        assert len(supply_nets) == 1, "Multiple supply net names: {}".format(
            supply_nets)
        self.supply_voltage_net = supply_nets.pop()
        self.gnd_net = ground_nets.pop()
        logger.info("Supply net: {}".format(self.supply_voltage_net))
        logger.info("Ground net: {}".format(self.gnd_net))
            
    def create_initial_layout(self):
        logger.info(f'Cell name: {self.cell_name}')
        self.top_cell = self.layout.create_cell(self.cell_name)
        self.top_cell_optimized = self.layout_optimized.create_cell(self.cell_name)
        self.shapes_optimized = dict()
        # Setup layers.
        self.shapes = dict()
        for name, (num, purpose) in layermap.items():
            layer = self.layout.layer(num, purpose)
            layer = self.layout_optimized.layer(num, purpose)
            self.shapes[name] = self.top_cell.shapes(layer)
            self.shapes_optimized[name] = self.top_cell_optimized.shapes(layer)

        if self.debug_routing_graph:
            # Layers for displaying routing terminals.
            self._routing_terminal_debug_layers = {
                l: self.layout.layer(idx, 200) for l, (idx, _) in layermap.items()
            }

    def transistor_placement(self):
        # Place transistors
        logging.info('Find transistor placement')
        abstract_cell = self.placer.get_placement(self.abstract_transistors)
        if abstract_cell is None: return
        abstract_cell = NFoldTransistorPlacer().fold_placement(single_line_placement=abstract_cell, height_req=self.tech.height_req)
        logger.info(f"Cell placement:\n\n{abstract_cell}\n")
        self.temp_cell = abstract_cell
        if self.temp_cell.cells is None:
            self.temp_cell.cells = [self.temp_cell.lower, self.temp_cell.upper]
    
    def get_floating_gate(self, transistor_dict, x, y):
        class TempTransistor:
            source_net = ''
            drain_net = ''
            gate_net = ''
        t = TempTransistor()
        if (x-1,y) in transistor_dict:
            t.source_net = transistor_dict.get((x-1,y)).drain_net
        if (x+1, y) in transistor_dict:
            t.drain_net = transistor_dict[(x+1,y)].source_net 
        t.gate_net = f'G{self.PTG_count}'
        self.PTG_count+=1
        return t
    
    def base_layers_drawing(self):
        # Get the locations of the transistors.
        transistor_locations= self.temp_cell.get_transistor_locations()
        transistor_locations_dict = {(x,y): t for t,(x,y) in transistor_locations}
        channel_type_dict = {y: t.channel_type for t,(x,y) in transistor_locations}
        # Create the layouts of the single transistors. Layouts are already translated to the absolute position.
        def opp(y):
            if y%2 == 0: return y+1
            else: return y-1
        self.transistor_layout = {
            t: self.defaultTransistorLayout(
                t,
                (x, y),
                self.tech,
                self.temp_cell,
                counter_transistor=transistor_locations_dict.get((x, opp(y)), self.get_floating_gate(transistor_locations_dict, x, opp(y))),
                transistordict=transistor_locations_dict
            )
            for (x, y), t in transistor_locations_dict.items()
        }
        t = self.temp_cell.cells
        idx = product(range(self.temp_cell.width), range(self.tech.height_req*2))
        for (x,y) in idx:
            if not t[y][x]:
                channel_type = channel_type_dict.get(y, None)
                # Extend logic for height of 2+ 
                if channel_type is None:
                    channel_type = ChannelType.NMOS if self.tech.height_req > 1 and y in [0, 3] else ChannelType.PMOS
                if channel_type:
                    self.transistor_layout[f'PTG{self.PTG_count}'] = self.defaultTransistorLayout(None, (x, y), self.tech, self.temp_cell, channel_type=channel_type)
                    self.PTG_count+=1
 
        # Draw the transistors
        for i, l in enumerate(self.transistor_layout.values()):
            assert isinstance(l, self.defaultTransistorLayout), f'{str(l)} is of type {type(l)}'
            l.deviceDrawing(self.shapes)

            l.draw_tsvBar(self.shapes, extension=0)

        #draw diffusion Gates
        max_x = 0
        y_set = set()
        T = None
        for t,(x,y) in transistor_locations:
            max_x = max(max_x, x)
            y_set.add(y)
        x_set = [-1,max_x+1]
        for x in x_set:
            for y in y_set:
                channel_type = channel_type = channel_type_dict.get(y, None)
                l = self.defaultTransistorLayout(T,(x,y), self.tech, self.temp_cell, channel_type=channel_type)
                l.draw_diffusionGate(self.shapes)

    def power_layers_drawing(self):
        # Calculate dimensions of cell.
        flipped = True
        num_unit_cells = self.temp_cell.width
        self.cell_width = (num_unit_cells + 1) * self.tech.cell_width
        self.cell_height = self.tech.cell_height
        self.tech.cell_width = (num_unit_cells + 1) * self.tech.cell_width
        self.tech.cell_height = self.tech.cell_height
        # Draw cell template.
        if self.tech.technology == 'finfet':
            layer_generation_helper.nwell_layer(self.shapes,
                shape=(
                    self.cell_width, self.cell_height), tech=self.tech
                )
        if self.tech.half_dr and self.tech.backside_power_rail:
        # Draw power rails.
            vss_rail = pya.Path([pya.Point(0, self.tech.cell_height + self.tech.power_rail_width//2),
                                pya.Point(self.cell_width, self.tech.cell_height + self.tech.power_rail_width//2 )],
                                self.tech.power_rail_width)
            vdd_rail = pya.Path([pya.Point(0, - self.tech.power_rail_width//2),
                                pya.Point(self.cell_width, - self.tech.power_rail_width//2)],
                                self.tech.power_rail_width)
        else:
            vss_rail = pya.Path([pya.Point(0, self.tech.cell_height ),
                                pya.Point(self.cell_width, self.tech.cell_height)],
                                self.tech.power_rail_width)
            vdd_rail = pya.Path([pya.Point(0, 0),
                                pya.Point(self.cell_width, 0)],
                                self.tech.power_rail_width)

        if self.tech.backside_power_rail:
            power_layer = back_metal0
            power_pin_layer = back_metal0_pin
            power_label = back_metal0 + '_label'
            power_pin_label = back_metal0_pin_label
        else:
            power_layer = metal0
            power_pin_layer = metal0_pin
            power_label = metal0_label
            power_pin_label = metal0_pin_label

        # Insert power rails into layout.
        self.shapes[power_layer].insert(vdd_rail).set_property('net', self.supply_voltage_net)
        if self.tech.height_req == 1: self.shapes[power_layer].insert(vss_rail).set_property('net', self.gnd_net)
        if self.tech.half_dr and not self.tech.backside_power_rail:
            self.shapes[cell_boundary].insert(db.Box(0, 0, self.cell_width, self.cell_height))
        elif self.tech.half_dr and self.tech.backside_power_rail:
            self.shapes[cell_boundary].insert(db.Box(0, -self.tech.power_rail_width//2, self.cell_width, self.cell_height - self.tech.power_rail_width//2))
        else:
            self.shapes[cell_boundary].insert(db.Box(0, -self.tech.power_rail_width//2, self.cell_width, self.cell_height + self.tech.power_rail_width//2))
            
        # Add pin layers
        self.shapes[power_pin_layer].insert(vdd_rail)
        if self.tech.height_req == 1: self.shapes[power_pin_layer].insert(vss_rail)
        # Register Pins/Ports for LEF file.
        bbox = vdd_rail.bbox()
        text_x = bbox.center().x
        text_y = bbox.center().y
        if flipped:
            bottom_text_label = self.gnd_net
        else:
            bottom_text_label = self.supply_voltage_net
        text = pya.Text(bottom_text_label, pya.Trans(text_x, text_y))
        text.text_size = 3000
        self.shapes[power_label].insert(text)
        self.shapes[power_pin_label].insert(text)
        if self.tech.height_req == 1:
            if flipped:
                top_text_label = self.supply_voltage_net
            else:
                top_text_label = self.gnd_net
            text = pya.Text(top_text_label, pya.Trans(vss_rail.bbox().center().x, vss_rail.bbox().center().y))
            text.text_size = 3000
            self.shapes[power_label].insert(text)
            self.shapes[power_pin_label].insert(text)
        seperation = self.cell_height//self.tech.height_req
        for i in range(self.tech.height_req):
            if self.tech.height_req == 1:
                return
            offset_y = (i+1)*seperation
            if self.tech.backside_power_rail:
                p_rail = pya.Path([pya.Point(0, offset_y - self.tech.power_rail_width//2),
                                    pya.Point(self.cell_width, offset_y - self.tech.power_rail_width//2)],
                                    self.tech.power_rail_width)
            else:
                p_rail = pya.Path([pya.Point(0, offset_y), pya.Point(self.cell_width, offset_y)], self.tech.power_rail_width)
            self.shapes[power_layer].insert(p_rail).set_property('net', self.supply_voltage_net)
            self.shapes[power_pin_layer].insert(p_rail)
            bbox = p_rail.bbox()
            text_x = bbox.center().x
            text_y = bbox.center().y
            rail_text = self.gnd_net if bottom_text_label == self.supply_voltage_net else self.supply_voltage_net
            bottom_text_label = rail_text
            text = pya.Text(rail_text, pya.Trans(text_x, text_y))
            text.text_size = 3000
            self.shapes[power_label].insert(text)
            self.shapes[power_pin_label].insert(text)

    def _get_track_centers(self):
        # Get the center of the horizontal routing tracks along the y-axis.
        if self.tech.height_req == 1:
            if self.tech.backside_power_rail:  
                if not self.tech.half_dr:      
                    lower_Y = -self.tech.power_rail_width//2 + self.tech.layer_width[metal0]//2 + (self.tech.m0_pitch - self.tech.layer_width[metal0])//2
                    upper_Y = self.tech.cell_height + self.tech.power_rail_width//2 - (self.tech.m0_pitch - self.tech.layer_width[metal0])//2
                else:
                    lower_Y = -self.tech.power_rail_width//2 + self.tech.m0_pitch
                    upper_Y = self.tech.cell_height + self.tech.power_rail_width//2 - self.tech.layer_width[metal0]//2   
            else:
                # Align signal tracks without overlapping with power/ground 
                lower_Y = self.tech.power_rail_width//2 + self.tech.pg_signal_spacing + self.tech.layer_width[metal0]//2  
                upper_Y = self.tech.cell_height - self.tech.power_rail_width//2 - self.tech.pg_signal_spacing
            track_centers = list(range(lower_Y, upper_Y, self.tech.m0_pitch))
        else:
            track_centers = []
            subcell_height = self.tech.cell_height//self.tech.height_req
            for i in range(self.tech.height_req):
                if self.tech.backside_power_rail:
                    lower_Y = (subcell_height * i) -self.tech.power_rail_width//2 + self.tech.m0_pitch
                    upper_Y = subcell_height * (i + 1) - self.tech.m0_pitch +  self.tech.layer_width[metal0]//2
                else:
                    lower_Y = (subcell_height * i) + self.tech.power_rail_width//2 + self.tech.pg_signal_spacing + self.tech.layer_width[metal0]//2
                    upper_Y = subcell_height * (i + 1) - self.tech.power_rail_width//2- self.tech.pg_signal_spacing
                track_centers += list(range(lower_Y, upper_Y, self.tech.m0_pitch))
            lower_Y = track_centers[0]
            upper_Y = track_centers[-1]
        return track_centers, lower_Y, upper_Y

    def route_cell(self):
        track_centers, lower_Y, upper_Y = self._get_track_centers()

        def create_horizontal_polygons(width):
            left_X = 0  # tech.grid_offset_x
            right_X = self.tech.grid_offset_x + self.cell_width - self.tech.grid_offset_x
            for y in track_centers:
                M_Track = pya.Path(
                    [pya.Point(left_X, y) ,pya.Point(right_X, y)],
                    width
                )
                self.shapes[metal0_track_guide].insert(M_Track)
        
        def create_vertical_polygons(width):
            allowed_vertical_rt_area = self.cell_width-self.tech.vertical_metal_pitch
            n = allowed_vertical_rt_area%self.tech.vertical_metal_pitch
            diff = self.tech.vertical_metal_pitch/2 + n/2
            left_X = int(diff)
            right_X = self.cell_width
            if self.tech.backside_power_rail and self.tech.half_dr:
                bottom_y = -self.tech.power_rail_width
                top_y = self.tech.cell_height
            else:
                bottom_y = -self.tech.power_rail_width//2
                top_y = self.tech.cell_height + self.tech.power_rail_width//2
            for x in range(left_X, right_X,self.tech.vertical_metal_pitch):
                M_Track = pya.Path(
                        [pya.Point(x, top_y)
                        ,pya.Point(x, bottom_y)]
                        , width
                    )
                self.shapes[metal1_track_guide].insert(M_Track)

        # Construct two dimensional grid which defines the routing graph on a single layer.
        grid = Grid2D(
            (self.tech.grid_offset_x, lower_Y),
            (self.tech.grid_offset_x + self.cell_width -self.tech.grid_offset_x, upper_Y),
            (self.tech.routing_grid_pitch_x, self.tech.m0_pitch)
        )
        
        create_horizontal_polygons(self.tech.layer_width[metal0_track_guide])
        if self.tech.routing_capability == 'Two Metal Solution':
            create_vertical_polygons( self.tech.layer_width[metal1_track_guide])
        # Create base graph
        # G = create_routing_graph_base(grid, self.tech)
        x_axis_points = list(range(self.tech.grid_offset_x,
            self.tech.grid_offset_x + self.cell_width -self.tech.grid_offset_x,
            self.tech.routing_grid_pitch_x))
        G = create_routing_graph_base_new(x_axis_points, track_centers, self.tech)
        #get nodes of each net and print their edges and nodes on the graph
        for node in G.nodes():
            if 'pos' not in G.nodes[node]:
                G.nodes[node]['pos'] = node[1]
        terminals_by_net = identify_terminal_nodes(G, self.shapes, self.tech)
       
        if self.debug_plots:
            show_nx(G, self.cell_name)

        # Logic to insert diff_interconnect for CFET only
        if self.tech.technology == 'cfet':
            yposition = sum(track_centers[:2])//2
            #check if yposition satisfies the minimum spacing rule from nanosheet
            min_spacing_yposition = (self.tech.cell_height//2-self.tech.nanosheet_width//2) - self.tech.min_spacing.get((nanosheet,diff_interconnect), 0) -  self.tech.via_size_vertical[diff_interconnect]//2
            #check if min_spacig_yposition does not exceed the circcuit overall height
            if min_spacing_yposition-self.tech.via_size_vertical[diff_interconnect]//2 <-self.tech.power_rail_width//2:
                assert False, "Minimum spacing rule for nanosheet and Via connecting PMOS and NMOS interconnect does not match"
            else:
                yposition = min(yposition, min_spacing_yposition)
            
            grid_x = range(self.tech.grid_offset_x,
                            self.tech.grid_offset_x + self.cell_width -self.tech.grid_offset_x,
                                self.tech.routing_grid_pitch_x)
            vias = set()
            for shape1 in self.shapes[pdiffcon].each():
                for shape2 in self.shapes[ndiffcon].each():
                    props1 = shape1.property('net')
                    props2 = shape2.property('net')
                    if props1!=None and props1 == props2 and (not is_power_net(props1)) and (not is_power_net(props2)):
                    
                        bbox1 = shape1.bbox()
                        bbox2 = shape2.bbox()
                
                        x1 = None
                        for x in grid_x:
                            if bbox1.contains(pya.Point(x, yposition)) and bbox2.contains(pya.Point(x, yposition)):
                                x1 = x
                                break
                        if x1 is None:
                            continue
                        if (x1,yposition) in vias:
                            continue
                        vias.add((x,yposition))
                        center_x = x1
                        center_y = yposition
                        self.shapes[diff_interconnect].insert(create_rectangle_from_center(center_x,center_y,self.tech.via_size_horizontal[diff_interconnect], self.tech.via_size_vertical[diff_interconnect]))
           
        if self.tech.routing_capability == 'Two Metal Solution':
            metal0_routing_engine_router = Metal1RoutingEngine(self.tech, terminals_by_net, track_centers, self.shapes, self.temp_cell, self.io_pins, self.cell_name, self.debug_plots)
        else:
            metal0_routing_engine_router = Metal0RoutingEngine(self.tech, terminals_by_net, track_centers, self.shapes, self.temp_cell, self.io_pins, self.cell_name, self.debug_plots)
        self.shapes = metal0_routing_engine_router.route()
        #assert False, f"{terminals_with_different_gate_nets} , {gate_terminal_subgraph.keys()}, {terminal_subgraph_nodes.keys()}"
        return
    
    def layer_merging(self):
        for layer, shape in self.shapes.items():
            if '_label' not in layer:
                region = pya.Region(shape)
                polygons_to_keep = pya.Region()
                for polygon in region:
                    polygons_to_keep += polygon
                region = polygons_to_keep
                region.merge()
                shape.clear()
                shape.insert(region)

    def create_cell_layout(self,
                           cell_name: str,
                           netlist_path: str) \
            -> Tuple[pya.Cell, Dict[str, List[Tuple[str, pya.Shape]]]]:
        self.netlist_loader(netlist_path, cell_name)
        self.create_initial_layout()
        self.transistor_placement()
        self.base_layers_drawing()
        self.power_layers_drawing()
        self.route_cell()
        return self.top_cell
    
