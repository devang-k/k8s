logger = logging.getLogger('sivista_app')




def _remove_duplicate_sequences(sequences: List[List['Transistor']]) -> List[Tuple['Transistor']]:
    """Removes duplicate sequences by converting each sequence to a tuple and keeping only unique ones."""
    seen = set()
    unique_sequences = []
    for path in map(tuple, sequences):
        if path not in seen:
            seen.add(path)
            unique_sequences.append(path)
    return unique_sequences


def _convert_edge_to_transistor(edge_triplet: Tuple[Any, Any, int]) -> List['Transistor']:
    """Converts a list of edge triplets into transistor objects."""
    result = []
    for left, right, meta in edge_triplet:
        instance = None
        if isinstance(meta, Transistor):
            instance = meta if meta.source_net == left else meta.flipped()
            if instance.source_net != left or instance.drain_net != right:
                return
        result.append(instance)
    return result


def _identify_minimal_shifted_paths(candidate_paths: List[List['Transistor']]) -> List[List['Transistor']]:
    """Shifts and trims paths to find all optimal (shortest) versions of them."""
    if not candidate_paths:
        return []

    best_paths = []
    shortest_length = float('inf')

    for route in candidate_paths:
        # Inline _trim_none: remove Nones from the start and end
        start, end = 0, len(route)
        while start < end and route[start] is None:
            start += 1
        while end > start and route[end - 1] is None:
            end -= 1
        trimmed = route[start:end]

        if not trimmed:
            return []

        if trimmed[0].source_net != trimmed[-1].drain_net:
            trimmed = trimmed + [None]

        for shift_by in range(len(trimmed)):
            # Rotate the list
            rotated = trimmed[shift_by:] + trimmed[:shift_by]

            if rotated[0] is None:
                continue

            # Inline _trim_none again
            r_start, r_end = 0, len(rotated)
            while r_start < r_end and rotated[r_start] is None:
                r_start += 1
            while r_end > r_start and rotated[r_end - 1] is None:
                r_end -= 1
            clean_rotated = rotated[r_start:r_end]

            if not clean_rotated:
                continue

            path_len = len(clean_rotated)
            if path_len < shortest_length:
                best_paths.clear()
                shortest_length = path_len
            if path_len == shortest_length:
                best_paths.append(clean_rotated)

    return _remove_duplicate_sequences(best_paths)


def compute_transistor_placements(graph_model: nx.MultiGraph, upper_limit=None) -> List[List['Transistor']]:
    """Generates optimized linear placements of transistors from a given circuit graph."""

    balanced_graphs = build_even_multigraphs(graph_model)
    if not balanced_graphs:
        logger.warning("No balanced subgraphs were generated from the input graph.")
        return

    logger.debug("Identified %d balanced subgraphs for placement trials", len(balanced_graphs))

    # Collect all Eulerian paths from each balanced subgraph
    eulerian_paths = []
    for subgraph in balanced_graphs:
        paths = exhaustive_euler_search_timeout(subgraph, upper_limit)
        if paths is None:
            logger.warning("Path search failed for a subgraph. Aborting placement computation.")
            return
        eulerian_paths.extend(paths)

    if not eulerian_paths:
        logger.info("No Eulerian paths found from any of the balanced subgraphs.")
        return

    logger.debug("Discovered %d raw paths", len(eulerian_paths))
    unique_paths = _remove_duplicate_sequences(eulerian_paths)
    logger.debug("Retained %d unique paths after de-duplication", len(unique_paths))

    # Convert edge sequences into transistor chains
    transistor_chains = []
    for path in unique_paths:
        transistors = _convert_edge_to_transistor(path)
        if transistors:
            transistor_chains.append(transistors)

    if not transistor_chains:
        logger.info("No valid transistor chains could be reconstructed from unique paths.")
        return

    # Optimize the transistor placements through cyclic shifts
    optimal_arrangements = _identify_minimal_shifted_paths(transistor_chains)
    if not optimal_arrangements:
        logger.info("No optimal transistor arrangements were found after evaluating shifts.")
        return

    return optimal_arrangements
