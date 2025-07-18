logger = logging.getLogger('sivista_app')


class ChildCell:
    """ Abstract representation of a set of devices. """

    def __init__(self, width, terminals, row, label):
        self.width = width
        self.terminals = terminals
        self.row = row
        self.location = (None, None)
        self.label = label

    def __repr__(self):
        return "ChildCell(%d, %s)" % (self.width, self.terminals)
    
class Base1Placement(BasePlacement):
    def __init__(self):
        pass

class Base1Placement(BasePlacement):
    def __init__(self):
        pass

    def get_placement(self, transistors: Iterable[Transistor]) -> Cell:

        std_utils.start_time = time.time()
        logger.info(f'Base1 Placement Initiated: {std_utils.start_time}')

        nmos_devices, pmos_devices = self._split_transistors(transistors)

        nmos_partitioned = self._partition_graphs(nmos_devices)
        nmos_placements = [self.find_partial_placement(g) for g in nmos_partitioned]
        if not nmos_placements:
            return
        nmos_childcells = [self.create_childcell_from_placements(pl, 1) for pl in nmos_placements]
        nmos_permutations = custom_permutations(nmos_childcells)
        if nmos_permutations is None:
            return
        
        pmos_partitioned = self._partition_graphs(pmos_devices)
        pmos_placements = [self.find_partial_placement(g) for g in pmos_partitioned]
        if not pmos_placements:
            return
        pmos_childcells = [self.create_childcell_from_placements(pl, 0) for pl in pmos_placements]
        pmos_permutations = custom_permutations(pmos_childcells)
        if pmos_permutations is None:
            return
        
        if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return

        optimal_child_placements = self.get_optimal_childcell_placements(pmos_permutations, nmos_permutations)

        if not optimal_child_placements:
            return

        return self.find_optimal_placement(optimal_child_placements)

    # -------------------------------------------
    # Helper methods
    # -------------------------------------------

    def _split_transistors(self, transistors):
        nmos_devices = [t for t in transistors if t.channel_type == ChannelType.NMOS]
        pmos_devices = [t for t in transistors if t.channel_type == ChannelType.PMOS]
        return nmos_devices, pmos_devices

    def _partition_graphs(self, transistors):
        graph = create_multigraph(transistors)
        return decompose_connectivity(graph)

    def find_partial_placement(self, graph: nx.MultiGraph) -> List[List[Transistor]]:
        placements = compute_transistor_placements(graph)
        if not placements:
            return
        return [list(chain(p, [None])) for p in placements]  # add diffusion gap

    def create_childcell_from_placements(self, placement_options: List[List[Transistor]], row_idx: int) -> ChildCell:
        if not placement_options:
            return ChildCell(0, set(), row_idx, placement_options)

        flattened_transistors = list(chain.from_iterable(placement_options))
        valid_transistors = [t for t in flattened_transistors if t]

        terminal_nets = {
            net for transistor in valid_transistors
            for net in transistor.terminals()
            if not net_util.is_power_net(net)
        }

        placement_options = sorted(placement_options, key=repr)
        return ChildCell(len(placement_options[0]), terminal_nets, row_idx, placement_options)

    def compute_childcell_terminal_position(self, childcell_row: List[Any]) -> List[Tuple[Any, float]]:
        """
        Compute the terminal (net, x) positions for a single permutation of childcells.
        :param childcell_row: One permutation (row) of ChildCell objects
        :return: List of (net, x-position) tuples
        """
        offset = 0
        terminals_with_positions = []
        for child_cell in childcell_row:
            x_center = offset + child_cell.width / 2
            terminals_with_positions.extend((net, x_center) for net in child_cell.terminals)
            offset += child_cell.width
        return terminals_with_positions

    def get_optimal_childcell_placements(
        self,
        pmos_permutations: List[List[Any]],
        nmos_permutations: List[List[Any]]
    ) -> List[Tuple[List[Any], List[Any]]]:
        """
        Streaming version of get_optimal_childcell_placements using the same variable names
        as the original vectorized version. Preserves logic and structure.
        """
        if not pmos_permutations or not nmos_permutations:
            return []

        logger.debug('Computing terminal positions for pmos_permutations and nmos_permutations')

        best_pairs = []
        min_length = None

        for p_row in pmos_permutations:
            ppos = self.compute_childcell_terminal_position(p_row)

            for n_row in nmos_permutations:
                npos = self.compute_childcell_terminal_position(n_row)

                combined_positions = ppos + npos
                metal_length_1D = get_1D_routing(combined_positions)

                if metal_length_1D is None:
                    return

                if min_length is None or metal_length_1D < min_length:
                    best_pairs = [(p_row, n_row)]
                    min_length = metal_length_1D
                elif metal_length_1D == min_length:
                    best_pairs.append((p_row, n_row))

        logger.debug('Best childcell combinations found: %d', len(best_pairs))
        return best_pairs

    def get_childcell_x_offsets(self, childcell_row: Iterable[ChildCell], offset: int = 0) -> Dict[Any, float]:
        offsets = {}
        for childcell in childcell_row:
            offsets[childcell] = offset
            offset += childcell.width
        return offsets

    def get_optimal_intra_childcell_placement(
        self,
        ps: List[ChildCell],
        ns: List[ChildCell]
    ) -> Dict[ChildCell, List[Transistor]]:
        """
        Evaluate optimal transistor placements inside each group of dependent ChildCells
        using a streaming wiring length calculator.
        """

        width = max(sum(child_cell.width for child_cell in ps), sum(child_cell.width for child_cell in ns))
        height = 2
        matrix = np.ndarray((height, width), dtype=object)

        # Step 1: Build the childcell occupancy matrix
        for row_idx, childcells in enumerate([ns, ps]):
            row = list(chain(*([s] * s.width for s in childcells)))
            row += [None] * (width - len(row))
            matrix[row_idx, :] = row

        # Step 2: Build connectivity graph (edges if shared nets between PMOS/NMOS)
        connectivity_graph = nx.Graph()
        connectivity_graph.add_nodes_from(chain(ns, ps))

        for a, b in zip(matrix[0].flat, matrix[1].flat):
            if a and b and (a.terminals & b.terminals):
                connectivity_graph.add_edge(a, b)

        subgraphs = [connectivity_graph.subgraph(c) for c in nx.connected_components(connectivity_graph)]
        dependent_cell_groups = [list(g.nodes) for g in subgraphs]

        x_offsets = {**self.get_childcell_x_offsets(ps), **self.get_childcell_x_offsets(ns)}
        best_child_placements = {}

        # Step 3: Evaluate each dependent group of childcells
        for childcells in dependent_cell_groups:
            childcells.sort(key=lambda child_cell: str(child_cell.label))
            external_net_positions = {
                (net, x_offsets[child_cell] + child_cell.width / 2)
                for child_cell in chain(ps, ns)
                if child_cell not in childcells
                for net in child_cell.terminals
            }

            placements_grid = list(product(*(child_cell.label for child_cell in childcells)))
            if not placements_grid:
                continue

            min_length = None
            best_placements = []

            for placements in placements_grid:
                net_positions = []
                for child_cell, placement in zip(childcells, placements):
                    for idx, net in enumerate(chain(*(t.terminals() for t in placement if t))):
                        if not net_util.is_power_net(net):
                            pos = x_offsets[child_cell] + idx / 3
                            net_positions.append((net, pos))
                net_positions.extend(external_net_positions)

                wiring_length = get_1D_routing(net_positions)
                if wiring_length is None:
                    return

                if min_length is None or wiring_length < min_length:
                    min_length = wiring_length
                    best_placements = [placements]
                elif wiring_length == min_length:
                    best_placements.append(placements)

            best_placement = best_placements[0]
            for child_cell, placement in zip(childcells, best_placement):
                best_child_placements[child_cell] = placement

        return best_child_placements


    def find_optimal_placement(self, optimal_child_placements):
        all_candidate_cells = []

        for p_blocks, n_blocks in optimal_child_placements:
            if std_utils.has_timed_out(std_utils.start_time, std_utils.timeout): return
            child_placements = self.get_optimal_intra_childcell_placement(p_blocks, n_blocks)
            if not child_placements:
                return

            upper_row = list(chain(*(child_placements[p] for p in p_blocks)))
            lower_row = list(chain(*(child_placements[n] for n in n_blocks)))

            cell = construct_cell(lower_row, upper_row)
            cell = remove_unnecessary_gaps(cell)
            all_candidate_cells.append(cell)

        if not all_candidate_cells:
            return None

        # Step 1: Filter by gate match constraint
        gate_filtered = apply_gate_sharing_constraint(all_candidate_cells)

        # Step 2: Filter by minimal 1D wire length
        routing_filtered = apply_1D_routing_constraint(gate_filtered)

        # Step 3: Return the first (any optimal) result

        return routing_filtered[-1] if routing_filtered else None


