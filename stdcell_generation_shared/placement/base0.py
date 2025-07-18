logger = logging.getLogger('sivista_app')


class Base0Placement(BasePlacement):

    def __init__(self):
        pass

    def get_placement(self, transistors: Iterable[Transistor], upper_limit = None) -> Cell:
        """Finding placement for transistors - creates a matched PMOS and NMOS placement
        """
        std_utils.start_time = time.time()
        logger.info(f'Base0 Placement Initiated: {std_utils.start_time}')

        transistors = list(transistors)

        logger.debug('Find NMOS placement')
        nmos_devices = [t for t in transistors if t.channel_type == ChannelType.NMOS]
        nmos_connectivity = create_multigraph(nmos_devices)
        logger.debug('NMOS - Finding partial placement')
        nmos_placements = compute_transistor_placements(nmos_connectivity, upper_limit)
        if not nmos_placements: return
        logger.debug('Unique NMOS placements with rotation: %d', len(nmos_placements))

        logger.debug('Find PMOS placement')
        pmos_devices = [t for t in transistors if t.channel_type == ChannelType.PMOS]
        pmos_connectivity = create_multigraph(pmos_devices)
        logger.debug('PMOS - Finding partial placement')
        pmos_placements = compute_transistor_placements(pmos_connectivity, upper_limit)
        if not pmos_placements: return
        logger.debug('Unique PMOS placements with rotation: %d', len(pmos_placements))

        # Find all potential PMOS and NMOS options.
        pairs = product(nmos_placements, pmos_placements)

        # Construct the pmos-nmos pairs
        candidate_cells = (construct_cell(nmos, pmos) for nmos, pmos in pairs)
        
        # Applying constraints
        logger.debug('finding best cells gate matching')
        optimal_gate_sharing_cells = apply_gate_sharing_constraint(candidate_cells)
        if not optimal_gate_sharing_cells: return
        logger.debug(f'best cells gate matching: {len(optimal_gate_sharing_cells)}')

        logger.debug(f'finding best cells wiring')
        optimal_1D_routing_cells = apply_1D_routing_constraint(optimal_gate_sharing_cells)
        if not optimal_1D_routing_cells: return
        logger.debug(f'best cells wiring: {len(optimal_1D_routing_cells)}')

        optimal_cells = optimal_1D_routing_cells
        
        #Sorting the final list of best cells
        optimal_cells = sorted(optimal_cells, key=lambda x:str(x.__repr__))

        if not optimal_cells:
            return
        else:
            if len(optimal_cells) > 0:
                logger.info(f'{len(optimal_cells)} optimal placements found')
                return optimal_cells[0]    # Returns the first placement
        return





