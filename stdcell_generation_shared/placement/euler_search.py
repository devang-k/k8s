logger = logging.getLogger('sivista_app')


def check_and_fetch_odd_nodes(graph: nx.MultiGraph) -> Optional[List[int]]:
    """Check graph structure and return nodes with odd degree if applicable."""
    assert isinstance(graph, nx.MultiGraph), Exception("Expected a MultiGraph input.")

    if nx.is_empty(graph):
        logger.debug("Input graph has no edges.")
    elif not nx.is_connected(graph):
        logger.debug("Graph appears disconnected")

    odd_nodes = [node for node, degree in graph.degree if degree % 2 == 1]
    odd_nodes.sort()

    if len(odd_nodes) % 2 != 0:
        logger.warning("Odd count of odd-degree nodes. Cannot proceed with pairing.")
        return None

    if not odd_nodes:
        if not nx.is_connected(graph):
            logger.warning("All degrees are even, but graph is disconnected.")
            return None
        return []  # Indicates the input already satisfies the requirement

    return odd_nodes


def deduplicate_graphs_by_edge_set(candidates: List[nx.MultiGraph]) -> List[nx.MultiGraph]:
    """Filters out structurally identical graphs using edge signature hashing."""
    fingerprints = set()
    filtered = []
    for subgraph in candidates:
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return
        edge_signature = tuple(sorted((min(a, b), max(a, b)) for a, b in subgraph.edges()))
        if edge_signature not in fingerprints:
            fingerprints.add(edge_signature)
            filtered.append(subgraph)
    return filtered


def build_even_multigraphs(base: nx.MultiGraph) -> List[nx.MultiGraph]:
    """Generate all graph variants with even degrees by adding the minimal edge set."""

    odd_ends = check_and_fetch_odd_nodes(base)
    if odd_ends is None:
        return []

    if not odd_ends:
        return [base.copy()]  # Already balanced

    logger.debug(f"Identifying complementary node groupings among {len(odd_ends)} odd-degree nodes.")

    combo_pool = list(combinations(odd_ends, len(odd_ends) // 2))
    group_one_set = combo_pool[:len(combo_pool) // 2]
    group_two_set = combo_pool[:len(combo_pool) // 2 - 1:-1]
    logger.debug("Candidate node groupings prepared.")

    generated_structures = []

    for group_a, group_b in zip(group_one_set, group_two_set):
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return
        if set(chain(group_a, group_b)) != set(odd_ends):
            continue
        if set(group_a) & set(group_b):
            continue

        for match in permutations(group_b):
            if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return
            working_copy = base.copy()
            valid_merge = True
            for src, tgt in zip(group_a, match):
                if working_copy.degree(src) % 2 != 1 or working_copy.degree(tgt) % 2 != 1:
                    valid_merge = False
                    break
                working_copy.add_edge(src, tgt)

            if not valid_merge:
                continue

            if any(deg % 2 != 0 for _, deg in working_copy.degree):
                continue

            if nx.is_connected(working_copy):
                generated_structures.append(working_copy)

    return deduplicate_graphs_by_edge_set(generated_structures)

def exhaustive_euler_search(graph: nx.MultiGraph, origin=None, destination=None, traversed=None, upper_limit=None) -> List[List[Tuple]]:
    if traversed is None:
        if not _has_even_degrees(graph):
            return []
        traversed = set()

    completed_paths = []

    if origin is None:
        origin = min(graph.nodes)

    if destination is None:
        destination = origin

    if len(traversed) == len(graph.edges):
        return []

    candidates = list(graph.edges(origin, keys=True))
    if not candidates:
        return []

    for x, y, label in candidates:
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return
        tag = _stable_edge_id(x, y, label)
        if tag in traversed:
            continue

        traversed.add(tag)

        if len(traversed) == len(graph.edges):
            if y == destination:
                completed_paths.append([(x, y, label)])
        else:
            next_paths = exhaustive_euler_search(graph, y, destination, traversed, upper_limit)
            for path in next_paths or []:
                completed_paths.append([(x, y, label)] + path)
                if upper_limit and len(completed_paths) >= upper_limit:
                    traversed.remove(tag)
                    return completed_paths[:upper_limit]

        traversed.remove(tag)

        if upper_limit and len(completed_paths) >= upper_limit:
            break

    return completed_paths[:upper_limit] if upper_limit else completed_paths

def _stable_edge_id(n1, n2, key):
    return (min(n1, n2), max(n1, n2), key)

def _has_even_degrees(g: nx.MultiGraph) -> bool:
    return all(degree % 2 == 0 for _, degree in g.degree())

def exhaustive_euler_search_timeout(graph, upper_limit):
    while True:
    # Check elapsed time
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout):
            logger.debug("Function execution timed out - euler tours with timer!")
            return   # Exit early
        return exhaustive_euler_search(graph, upper_limit=upper_limit)
    
