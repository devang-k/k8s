logger = logging.getLogger('sivista_app')


def create_multigraph(transistors: Iterable[Transistor]) -> nx.MultiGraph:
    """ Create networkx multigraph where each edge is a transistor gate and nodes are source/drain
    """
    G = nx.MultiGraph()
    for t in transistors: G.add_edge(t.source_net, t.drain_net, t)
    return G
    
def custom_permutations(iterable):
    def backtrack(path, available):
        nonlocal timed_out

        # Check for timeout
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout):
            timed_out = True
            return  # No need to return None explicitly

        # If all elements are used, store the permutation
        if not available:
            result.append(tuple(path))
            return

        for i in range(len(available)):
            if timed_out:  # Stop further recursion if timeout occurred
                return
            backtrack(path + [available[i]], available[:i] + available[i+1:])  # Don't check for None

    result = []
    timed_out = False

    backtrack([], list(iterable))  # Just call backtrack without checking return value

    return None if timed_out else result  # Only return None if timed out

def remove_unnecessary_gaps(cell: Cell) -> Cell:
    """
    Remove unnecessary diffusion gaps from the input cell while ensuring no short circuits.
    :param cell: The input cell.
    :return: A new compacted Cell object.
    """
    if len(cell.upper) != len(cell.lower):
        return  # Mismatched rows

    compact_upper, compact_lower = [], []
    n = len(cell.upper)

    def needs_diff_gap(left: Transistor, right: Transistor) -> bool:
        return left and right and left.drain_net != right.source_net

    for i in range(n):
        up, lo = cell.upper[i], cell.lower[i]

        if up or lo:
            compact_upper.append(up)
            compact_lower.append(lo)
        elif 1 <= i < n - 1:
            # Peek adjacent transistors only if this slot is empty
            if (
                needs_diff_gap(compact_upper[-1], cell.upper[i + 1]) or
                needs_diff_gap(compact_lower[-1], cell.lower[i + 1])
            ):
                compact_upper.append(None)
                compact_lower.append(None)

    return construct_cell(compact_lower, compact_upper)


def construct_cell(nmos_row: List[Transistor], pmos_row: List[Transistor]) -> Cell:
    """
    Assemble a Cell object from NMOS and PMOS transistor rows.
    :param nmos_row: Transistors for the lower row 
    :param pmos_row: Transistors for the upper row 
    :return: Cell object
    """
    cell_width = max(len(nmos_row), len(pmos_row))
    cell = Cell(cell_width)

    for i, pmos_transistor in enumerate(pmos_row):
        cell.upper[i] = pmos_transistor

    for i, nmos_transistor in enumerate(nmos_row):
        cell.lower[i] = nmos_transistor

    return cell

def decompose_connectivity(original_graph: nx.MultiGraph) -> List[nx.MultiGraph]:
    """
    Partition a MultiGraph into connected components, treating each occurrence of power nets as distinct
    to effectively ignore them during connectivity checks.
    
    :param original_graph: Input circuit graph with possible power nets.
    :return: List of connected subgraphs with original node names restored.
    """
    logger.debug("Partitioning graph while ignoring power net connections...")

    renamed_graph = nx.MultiGraph()
    node_id_generator = count()
    reverse_node_map = {}

    def transform_node(node):
        # Power nets are treated as distinct by giving them unique suffixes
        identifier = next(node_id_generator) if net_util.is_power_net(node) else 0
        transformed = (node, identifier)
        reverse_node_map[transformed] = node
        return transformed

    for src, dst, key, attr in original_graph.edges(keys=True, data=True):
        new_src = transform_node(src)
        new_dst = transform_node(dst)
        renamed_graph.add_edge(new_src, new_dst, key=key, **attr)

    num_components = nx.number_connected_components(renamed_graph)
    logger.debug("Found %d connected component(s)", num_components)

    # Revert node names to original ones
    subgraphs = [
        nx.relabel_nodes(renamed_graph.subgraph(component), reverse_node_map, copy=True)
        for component in nx.connected_components(renamed_graph)
    ]

    return subgraphs

