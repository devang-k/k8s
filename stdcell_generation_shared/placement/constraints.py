logger = logging.getLogger('sivista_app')




def get_1D_routing(nets: Iterable[Tuple[Hashable, float]]) -> float:
    """
    Streaming implementation of 1D wiring length calculation.
    :param nets: Iterable of (net, x) tuples
    :return: Total wiring length (sum of bounding box widths per net)
    """
    minmax_x = defaultdict(lambda: [float('inf'), float('-inf')])

    for net, x in nets:
        if net is None:
            continue
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout):
            return None
        minmax_x[net][0] = min(minmax_x[net][0], x)
        minmax_x[net][1] = max(minmax_x[net][1], x)

    routing_length = [xmax - xmin for xmin, xmax in minmax_x.values()]
    return sum(routing_length)

def apply_gate_sharing_constraint(cells: Iterable["Cell"]) -> List["Cell"]:
    """
    Streaming version that avoids materializing the full list.
    Keeps only cells with the max number of gate matches.
    """
    max_match_count = -1
    gate_matched_cells = []

    for cell in cells:
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return None
        upper_gates = [t.gate_net if t else None for t in cell.upper]
        lower_gates = [t.gate_net if t else None for t in cell.lower]

        matches = sum(
            1 for a, b in zip(upper_gates, lower_gates)
            if a is not None and b is not None and a == b
        )

        if matches > max_match_count:
            max_match_count = matches
            gate_matched_cells = [cell]
        elif matches == max_match_count:
            gate_matched_cells.append(cell)

    return gate_matched_cells

def apply_1D_routing_constraint(cells: Iterable["Cell"]) -> List["Cell"]:
    """
    Streaming version of apply_1D_routing_constraint.
    Finds all cells with the minimum 1D wiring length without materializing the full list.
    """
    def wiring_length(cell: "Cell") -> float:
        net_positions = []
        for row in (cell.upper, cell.lower):
            for pos, net in enumerate(chain(*(t.terminals() for t in row if t is not None))):
                net_positions.append((net, pos))

        if not net_positions:
            return 0.0

        # Group net positions and compute bounding box width
        nets, positions = zip(*net_positions)
        positions = np.array(positions)
        nets = np.array(nets)

        unique_nets = np.unique(nets)
        total_width = 0.0

        for net in unique_nets:
            net_pos = positions[nets == net]
            total_width += np.max(net_pos) - np.min(net_pos)

        return total_width

    optimally_routed_cells = []
    min_length = None

    for cell in cells:
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return None
        length = wiring_length(cell)
        if min_length is None or length < min_length:
            min_length = length
            optimally_routed_cells = [cell]
        elif length == min_length:
            optimally_routed_cells.append(cell)

    return optimally_routed_cells
