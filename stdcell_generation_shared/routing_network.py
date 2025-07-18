

logger = logging.getLogger('sivista_app')

def create_routing_graph(grid, tech) -> nx.Graph:
    logging.debug("Building routing graph...")
    G = nx.Graph()

    # Add nodes for each layer at all grid points
    for layer in tech.routing_layers:
        for coord in grid:
            G.add_node((layer, coord))

    # Add via edges between adjacent layers
    for src_layer, dst_layer, via_info in via_layers.edges(data=True):
        via_layer = via_info['layer']
        for coord in grid:
            n1, n2 = (src_layer, coord), (dst_layer, coord)
            weight = via_weightage.get((src_layer, dst_layer),
                      via_weightage.get((dst_layer, src_layer)))
            G.add_edge(n1, n2, weight=weight,layer=via_layer)

    # Add intra-layer routing edges
    for layer, directions in tech.routing_layers.items():
        for x, y in grid:
            origin = (layer, (x, y))

            if 'h' in directions:
                right = (x + tech.routing_grid_pitch_x, y)
                neighbor = (layer, right)
                if neighbor in G:
                    w = horizontal_edge_weights[layer] * tech.routing_grid_pitch_x
                    G.add_edge(origin, neighbor, weight=w, orientation='h', layer=layer)

            if 'v' in directions:
                up = (x, y + tech.m0_pitch)
                neighbor = (layer, up)
                if neighbor in G:
                    w = vertical_edge_weights[layer] * tech.m0_pitch
                    G.add_edge(origin, neighbor, weight=w, orientation='v', layer=layer)

    assert nx.is_connected(G), "Graph is not connected."
    return G

def _collect_routing_nodes_by_layer(graph: nx.Graph) -> Dict[Any, Set[Tuple[int, int]]]:

    routing_layers = defaultdict(set)
    
    for (layer1, pos1), (layer2, pos2) in graph.edges:
        routing_layers[layer1].add(pos1)
        routing_layers[layer2].add(pos2)

    return routing_layers

def identify_terminal_nodes(
    graph: nx.Graph,
    shape_layers: Dict[str, pya.Shapes],
    tech
):
    routing_positions = _collect_routing_nodes_by_layer(graph)
    terminals = []

    for layer, shapes in shape_layers.items():
        for shape in shapes.each():
            net_name = shape.property('net')
            if not net_name:
                continue

            # Get possible via layers for current layer
            via_candidates = [data['layer'] for _, _, data in via_layers.edges(layer, data=True)]
            logger.debug(f"{layer}, {via_candidates}")

            max_enclosure = max((tech.minimum_enclosure.get((layer, via), 0) for via in via_candidates), default=0)
            max_via_dim = max((tech.via_size.get(via, 0) for via in via_candidates), default=0)

            # Convert shape to region
            temp_shapes = db.Shapes()
            temp_shapes.insert(shape)
            region = pya.Region(temp_shapes)

            if layer in tech.routing_layers:
                # Use relaxed proximity for routing layers
                threshold = 1
                terminals_found = get_nearby_points(routing_positions[layer], region, threshold)
            else:
                # Stricter enclosure requirement for non-routing layers
                threshold = max_enclosure + (max_via_dim // 2)
                terminals_found = filter_points_within_region(routing_positions[layer], region, threshold)

            terminals.append((net_name, layer, terminals_found, region))

            # Avoid reusing terminal points in the routing graph
            routing_positions[layer] -= set(terminals_found)

    return terminals

def create_routing_graph_base_new(x_axis: list, y_axis: list, tech) -> nx.Graph:
    def _get_next_element(lst: list, current):
        try:
            index = lst.index(current)
            return lst[index + 1]
        except (ValueError, IndexError):
            return None
    
    logging.debug('Create routing graph.')
    # Create routing graph.
    # Create nodes and vias.
    G = nx.Graph()
    grid = [(x, y) for x in x_axis for y in y_axis]

    # Create nodes on routing layers.
    for layer, directions in tech.routing_layers.items():
        for p in grid:
            n = layer, p
            G.add_node(n, pos=p)
    

    # Create via edges.
    for l1, l2, data in via_layers.edges(data=True):
        via_layer = data['layer']
        for p in grid:
            n1 = (l1, p)
            n2 = (l2, p)

            weight = via_weightage.get((l1, l2))
            if weight is None:
                weight = via_weightage[(l2, l1)]

            # Create edge: n1 -- n2
            G.add_edge(n1, n2,
                       weight=weight,
                       layer=via_layer
                       )

    # Create intra layer routing edges.
    for layer, directions in tech.routing_layers.items():
        for p1 in grid:
            x1, y1 = p1
            x2 = _get_next_element(x_axis, x1)
            y2 = _get_next_element(y_axis, y1)

            # ID of the graph node.
            n = layer, p1

            # Horizontal edge.
            if 'h' in directions:
                n_right = layer, (x2, y1)
                if x2 and n_right in G.nodes:
                    weight = horizontal_edge_weights[layer] * abs(x2 - x1)
                    G.add_edge(n, n_right, weight=weight,
                               orientation='h', layer=layer)

            # Vertical edge.
            if 'v' in directions:
                n_upper = layer, (x1, y2)
                if y2 and n_upper in G.nodes:
                    weight = vertical_edge_weights[layer] * abs(y2 - y1)
                    G.add_edge(n, n_upper, weight=weight,
                               orientation='v', layer=layer)

    assert nx.is_connected(G)
    return G

