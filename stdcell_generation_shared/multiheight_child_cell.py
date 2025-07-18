

class CellMultiHeight:
    """ Class to create dual row cell.
    """

    def __init__(self, width: int, height : int):
        self.width = width
        self.height = height
        self.cells = [[None]*width for _ in range(height)]
        self.upper = [None] * width
        self.lower = [None] * width

    def get_transistor_locations(self) -> Set[Tuple[Transistor, Tuple[int, int]]]:
        """Get transistor locations"""
        assert len(self.lower) == len(self.upper)
        t = self.cells#[self.lower, self.upper]

        idx = product(range(self.width), range(self.height))
        
        return set((t[y][x], (x, y)) for x, y in idx if t[y][x] is not None)
    
    def cut_height(self):
        return
        # height = 0
        # for y in range(self.height-1, -1,-2):
        #     if self.cells[y] == self.cells[y-1] and self.cells[y] == [None]*len(self.cells[y]):
        #         height-=2
        # self.height -= height
        # self.cells = self.cells[:self.height]

    def adjust_cell_parameters(self):
        new_cells = [
            [] for i in range(self.height)
        ]
        for y in range(self.height):
            new_cells[y].append(self.cells[y][0])
        max_width = 0
        for x in range(1, self.width):
            extra_needed = False
            for y in range(self.height):
                if self.cells[y][x-1] and self.cells[y][x] and self.cells[y][x-1].drain_net != self.cells[y][x].source_net:
                    extra_needed = True
            if extra_needed:
                for y in range(self.height):
                    new_cells[y].append(None)
            
            for y in range(self.height):
                new_cells[y].append(self.cells[y][x])
            max_width   = max(max_width, len(new_cells[y]))
        for y in range(self.height):
            while len(new_cells[y])<max_width:
                new_cells[y].append(None)
        total_cutoff = 100000
        for y in range(self.height):
            cutoff = 0
            x = len(new_cells[y])-1
            while x>=0 and not new_cells[y][x]:
                cutoff+=1
                x-=1
            total_cutoff = min(total_cutoff, cutoff)
        for y in range(self.height):
            new_cells[y] = new_cells[y][:-total_cutoff]
        self.cells = new_cells
        #print("Past", self.width, len(new_cells[0]))
        # x = input()
        self.width = len(new_cells[0])
        self.height = len(self.cells)

    def get_passthrough_transistors(self) -> Set[Tuple[Transistor, Tuple[int, int]]]:
        assert len(self.lower) == len(self.upper)

        t = [self.lower, self.upper]
        idx = product(range(self.width), range(2))

        return set((None, (x, y)) for x, y in idx if t[y][x] is None)
    
    def __repr__(self):
        """ Simple print statement"""
        self.cells
        return (
                "".join([" | ".join(['{:^16}'.format(str(t)) for t in upper]) +
                "\n" for upper in self.cells])           
        )
