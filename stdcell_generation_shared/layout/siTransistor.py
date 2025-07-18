logger = logging.getLogger('sivista_app')

class Device:
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], distance_to_outline: int, tech):
        raise NotImplemented()

class DeviceLayout(Device):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech, all_transistors, counter_transistor=None, channel_width =None, toFull=False, transistordict = {}, channel_type=None):
        self.abstract_transistor = abstract_transistor
        self.to_optimize = True
        self.location = location
        self.channel_type = channel_type
        self.tech = tech
        if self.tech.height_req > 1:
            self.tech.half_dr = True
        self.num_transistors = all_transistors.width
        self.all_transistors = all_transistors.cells 
        # Bottom left of diffcon.
        self.x, self.y = location
        self.interconnect_width =  max(self.tech.layer_width[pdiffcon],self.tech.layer_width[ndiffcon])
        self.tech.layer_width[poly] = max(self.tech.layer_width[ppoly], self.tech.layer_width[npoly])
        self.center_x = (self.x + 1) * self.tech.cell_width
        seperation = self.tech.cell_height//self.tech.height_req
        self.subcell_bottom = ((self.y//2) * seperation)
        self.subcell_top = ((self.y//2 + 1) * seperation)
        self.cell_height = self.subcell_top - self.subcell_bottom - self.tech.power_rail_width if self.tech.height_req > 1 else self.tech.cell_height
        self.extended_cell_height = self.cell_height + self.tech.power_rail_width
        self.offset_y = (self.y//2) * seperation
        self.counter_transistor = counter_transistor
        self.above_transistor = self.get_above_transistor(self.x, self.y)
        self.preceeding_transistor = self.get_below_transistor(self.x, self.y)
        self.interconnect_width = max(self.tech.layer_width[pdiffcon],self.tech.layer_width[ndiffcon])
        self._diffusion = None
        self.interconnect_top_fix = defaultdict(lambda:0)
        self.interconnect_bottom_fix = defaultdict(lambda:0)
        self.gate_top_fix = 0
        self.gate_bottom_fix = 0
        self.nanosheet_left_x = 0
        self.transistor_center_x = 0
        if self.tech.height_req == 1:
            self.transistor_center_y = -self.tech.power_rail_width//2 + self.extended_cell_height//2
        else:
            self.transistor_center_y = -self.tech.power_rail_width//2 + seperation//2 if self.tech.backside_power_rail else seperation//2
        self._tsvPath = None
        self.flipped = True
        if (self.y//2) % 2 == 1:
            self.flipped = False
        if (self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS: 
            self.diffcon = ndiffcon
            self.diff_dvb = ndiff_dvb
            self.poly = npoly
            self.nanosheet = ndiff
            self.well= nwell
            if self.tech.backside_power_rail:
                self.diff_dvb = ndiff_dvb
            else:
                self.diff_dvb = nviat
            if self.flipped:
                self.pmos_virtual_box()
            else:
                self.nmos_virtual_box()
        else:
            self.diffcon = pdiffcon
            self.diff_dvb = pdiff_dvb
            self.poly = ppoly
            self.nanosheet = pdiff
            self.well= pwell
            if self.tech.backside_power_rail:
                self.diff_dvb = pdiff_dvb
            else:
                self.diff_dvb = pviat
            if self.flipped:
                self.nmos_virtual_box()
            else:
                self.pmos_virtual_box()
        self.calculate_nanosheet_path()

        # Well layer.
        if self.abstract_transistor is None:
            # Diffusion layer.
            self.transistor_center_x = self.transistor_bbox.center().x
            self.gate_top_fix = -self.transistor_bbox.top + self.nanosheet_bbox.top + self.tech.gate_extension
            self.gate_bottom_fix = -self.transistor_bbox.bottom + self.nanosheet_bbox.bottom - self.tech.gate_extension
            self._gate_path = self.calculate_gate_path()
            self._source_path = self.calculate_none_sd_interconnect(self.transistor_bbox.left  + self.interconnect_width//2)
            self._drain_path = self.calculate_none_sd_interconnect(self.transistor_bbox.right - self.interconnect_width//2)
            self._tsvbar = None
            self._diffusion = None
            self._nanosheet_path = pya.Region(self.nanosheet_bbox) - pya.Region(self._gate_path)
            self._tsvPath = None
            return 
        terminals = {
            abstract_transistor.gate_net: [
                (self.poly, (self.center_x, self.cell_height  + min(self.tech.gate_extension, self.tech.power_rail_width//2-self.tech.via_extension))),
                (self.poly, (self.center_x, self.cell_height//2 - self.tech.nanosheet_width//2 - self.tech.gate_extension)),   
            ]
        }
        if self.abstract_transistor:
            self.transistor_center_x = self.transistor_bbox.center().x
            if not self.tech.half_dr:
                self._source_path = self.calculate_sd_points(self.abstract_transistor.source_net, "source_net", self.tech,self.transistor_bbox.left  + self.interconnect_width//2)
                self._drain_path = self.calculate_sd_points(self.abstract_transistor.drain_net,"drain_net", self.tech, self.transistor_bbox.right - self.interconnect_width//2)
                self._gate_path = self.calculate_gate_path()
            else:
                self._source_path = self.calculate_sd_half_dr(self.abstract_transistor.source_net, "source_net", self.tech,self.transistor_bbox.left  + self.interconnect_width//2)
                self._drain_path = self.calculate_sd_half_dr(self.abstract_transistor.drain_net,"drain_net", self.tech, self.transistor_bbox.right - self.interconnect_width//2)
                self._gate_path = self.calculate_gate_path_half_dr()
        self.terminals = terminals

    @abstractmethod
    def pmos_virtual_box(self):
        """
            Draw device outline box for pmos transistors
        """
        
        raise NotImplemented()

    @abstractmethod
    def nmos_virtual_box(self):
        """
            Draw device outline box for pmos transistors
        """
        raise NotImplemented()

    def calculate_sd_points(self, abstract_transister_net, net_type, tech, center_x):
        if is_supply_net(abstract_transister_net) or is_ground_net(abstract_transister_net):
            self._tsvPath = pya.Path.new([
                    pya.Point(center_x, self.tsvBox.top),
                    pya.Point(center_x, self.tsvBox.bottom)],
                    self.interconnect_width,     
                    0,              
                    0)
            self.sd_top = self._tsvPath.bbox().top 
            self.sd_bottom = self._tsvPath.bbox().bottom 
            self.sd_top = max(self.sd_top, self.nanosheet_bbox.p2.y + self.tech.interconnect_extension)
            self.sd_bottom = min(self.sd_bottom, self.nanosheet_bbox.p1.y - self.tech.interconnect_extension )
        else:
            self.sd_top = self.transistor_bbox.top
            self.sd_bottom = self.transistor_bbox.bottom
            if self.counter_transistor :
                net1 = getattr(self.abstract_transistor, net_type)
                net2 = getattr(self.counter_transistor, net_type)
                if net1 != net2:
                        self.sd_top = self.sd_top + self.interconnect_top_fix.get(net_type,0) 
                        self.sd_bottom = self.sd_bottom +self.interconnect_bottom_fix.get(net_type,0)
        path = pya.Path.new([
                pya.Point(center_x, self.sd_top),
                pya.Point(center_x, self.sd_bottom)],
                self.interconnect_width,    
                0,             
                0)
        return path
    
    def calculate_none_sd_interconnect(self,center_x):
        self.sd_top  = (self.nanosheet_bbox.top + self.tech.interconnect_extension)
        self.sd_bottom  =  self.nanosheet_bbox.bottom -self.tech.interconnect_extension
        path = pya.Path.new([
                pya.Point(center_x, self.sd_top),
                pya.Point(center_x, self.sd_bottom)],
                self.interconnect_width,    
                0,             
                0)
        return path

    def calculate_gate_path(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix
                  
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path

    def printPoint(self, box):
        if isinstance(box, pya.Path):
            ret = ""
            for index, point in enumerate(box.each_point()):
                ret += f"Point {index}: ({point.x}, {point.y}) --- "
            return ret
        elif isinstance(box, pya.Box):
            return (box.left, box.top, box.right, box.bottom)

    def deviceDrawing(self, shapes: Dict[Any, pya.Shapes]) -> None:
        """ Draw a Device.
        """

        if self._nanosheet_path:
            if self.tech.half_dr:
                self._nanosheet_path = pya.Path(
                    [
                        pya.Point(max(self._nanosheet_path.bbox().p1.x, self.tech.layer_width[self.poly]//2), self._nanosheet_path.bbox().center().y),
                        pya.Point(min(self._nanosheet_path.bbox().p2.x, int(self.tech.cell_width * (self.num_transistors + 1)) - self.tech.layer_width[self.poly]//2), self._nanosheet_path.bbox().center().y)
                    ],
                    self.tech.nanosheet_width
                )
            if not self.abstract_transistor:
                self._nanosheet_path = pya.Region(self._nanosheet_path) - pya.Region(self._gate_path)
            self._nanosheet_path.move(0, self.offset_y)
            shapes[self.nanosheet].insert(self._nanosheet_path)

        if self._source_path:
            self._source_path.move(0, self.offset_y)
            inst = shapes[self.diffcon].insert(self._source_path)
            if self.abstract_transistor:
                inst.set_property('net', self.abstract_transistor.source_net)
                bbox = self._source_path.bbox()
                text_x = bbox.center().x
                text_y = bbox.center().y
                text = pya.Text(self.abstract_transistor.source_net, pya.Trans(text_x, text_y))
                text.text_size = 3000
                shapes[self.diffcon].insert(text)
        
        if self._drain_path:
            self._drain_path.move(0, self.offset_y)
            inst = shapes[self.diffcon].insert(self._drain_path)
            if self.abstract_transistor:
                inst.set_property('net', self.abstract_transistor.drain_net)
                bbox = self._drain_path.bbox()
                text_x = bbox.center().x
                text_y = bbox.center().y
                text = pya.Text(self.abstract_transistor.drain_net, pya.Trans(text_x, text_y))
                text.text_size = 3000
                shapes[self.diffcon].insert(text)
        if self._gate_path:
            self._gate_path.move(0, self.offset_y)
            inst = shapes[self.poly].insert(self._gate_path)
            if self.abstract_transistor:
                inst.set_property('net', self.abstract_transistor.gate_net)
                inst.set_property('optimize', self.to_optimize)
                bbox = self._gate_path.bbox()
                text_x = bbox.center().x
                text_y = bbox.center().y
                text = pya.Text(self.abstract_transistor.gate_net, pya.Trans(text_x, text_y))
                text.text_size = 3000
                shapes[self.poly].insert(text)

        if self._diffusion:
            self._diffusion.move(0, self.offset_y)
            shapes[gate_isolation].insert(self._diffusion) 
            
    def draw_diffusionGate(self, shapes: Dict[Any, pya.Shapes]) -> None:
        """ Draw a diffusionGate.
        """
        # Create well and active shape.
        if self._gate_path:
            if self.tech.half_dr and not self.tech.backside_power_rail:
                p1 = self._gate_path.bbox().p1  # Bottom-left point
                p2 = self._gate_path.bbox().p2  # Top-right point
                # Create a new box with adjusted height
                if self.tech.technology == 'cfet':
                    new_box = pya.Box(p1.x, p1.y + self.tech.power_rail_width//2, p2.x, p2.y - self.tech.power_rail_width//2)
                else:
                    new_box = pya.Box(p1.x, 0 , p2.x, self.tech.cell_height)
                inst = shapes[dummy_gate].insert(new_box)
                inst.set_property('optimize', False)
            else:
                p1 = self._gate_path.bbox().p1  # Bottom-left point
                p2 = self._gate_path.bbox().p2  # Top-right point
                # Create a new box with adjusted height
                if self.tech.technology == 'cfet':
                    new_box = pya.Box(p1.x, p1.y + self.tech.power_rail_width//2, p2.x, p2.y - self.tech.power_rail_width//2)
                else:
                    new_box = pya.Box(p1.x, - self.tech.power_rail_width//2 , p2.x, self.tech.cell_height - self.tech.power_rail_width//2)
                inst = shapes[dummy_gate].insert(new_box)
                inst.set_property('optimize', False)
    
    @abstractmethod
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0):
        raise NotImplemented()
    
    def get_above_transistor(self, x, y):
        following_y = None
        pattern = "NPPN" #if self.tech.flipped == 'R0' else "PNNP"
        pattern_length = len(pattern)
        channel_type = pattern[y % pattern_length]
        # Search for the next occurrence of the same channel type
        for i in range(y + 1, len(self.all_transistors)):
            if pattern[i % pattern_length] == channel_type:
                following_y = i
                break
        if following_y and 0 <= x < self.num_transistors:
            return self.all_transistors[following_y][x]
        return None
    
    def get_below_transistor(self, x, y):
        preceeding_y = None
        pattern = "NPPN" #if self.tech.flipped == 'R0' else "PNNP"
        pattern_length = len(pattern)
        channel_type = pattern[y % pattern_length]
        # Search for the next occurrence of the same channel type
        for i in range(y-1, -1, -1):
            if pattern[i % pattern_length] == channel_type:
                preceeding_y = i
                break
        if preceeding_y and 0 <= x < self.num_transistors:
            return self.all_transistors[preceeding_y][x]
        return None

class GAALayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech, all_transistors, counter_transistor=None, channel_width=None, toFull=False, transistordict={}, channel_type=None):
        super().__init__(abstract_transistor, location, tech, all_transistors, counter_transistor, channel_width, toFull, transistordict, channel_type)
    def pmos_virtual_box(self):
        self.interconnect_width = self.tech.layer_width[self.diffcon] 
        if self.tech.backside_power_rail:
            self.transistor_center_y = -self.tech.power_rail_width//2 + self.extended_cell_height//4
        else:
            self.transistor_center_y = self.extended_cell_height//4
        self.transistor_bbox = pya.Path(
                [
                    pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width, self.transistor_center_y),
                    pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, self.transistor_center_y)
                ],
            self.extended_cell_height//2
        ).bbox()
        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2),
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom)],
                self.interconnect_width,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom)],
            self.interconnect_width,     
            0,              
            0).bbox()
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 - self.tech.via_size_vertical[self.diff_dvb]//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
       
        self.interconnect_top_fix["source_net"] = -self.tech.vertical_interconnect_spacing//2
        self.interconnect_top_fix["drain_net"] = -self.tech.vertical_interconnect_spacing//2
        self.gate_top_fix = -self.tech.vertical_gate_spacing//2
        self.gate_bottom_fix  = 0

    def nmos_virtual_box(self):
        if self.tech.backside_power_rail:
            self.transistor_center_y = -self.tech.power_rail_width//2 + self.extended_cell_height - self.extended_cell_height//4
        else:
            self.transistor_center_y = self.extended_cell_height - self.extended_cell_height//4
        self.transistor_bbox = pya.Path(
                [
                    pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width, self.transistor_center_y),#replace x_Eff
                    pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, self.transistor_center_y) #replacex_Eff1
                ],
            self.extended_cell_height//2
    ).bbox()
        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_center_x, self.transistor_bbox.top),
                pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
                self.interconnect_width,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2  - self.tech.via_size_vertical[self.diff_dvb]//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
        self.interconnect_bottom_fix["source_net"] = self.tech.vertical_interconnect_spacing//2
        self.interconnect_bottom_fix["drain_net"] = self.tech.vertical_interconnect_spacing//2
        self.gate_top_fix = 0
        self.gate_bottom_fix  = self.tech.vertical_gate_spacing//2

    def calculate_nanosheet_path(self):
        # Calculates location of pdiff and ndiff based on np_spacing
        nanosheet_right_x = self.transistor_bbox.right
        if self.x!= 0:
            self.nanosheet_left_x = self.transistor_bbox.left
        if (self.x + 1) == self.num_transistors:
            nanosheet_right_x = (self.x + 2)*self.tech.cell_width
        if not self.flipped:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                # Calculation for NMOS at top
                nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
            else:
                # Calculation for PMOS at bottom
                nanosheet_center_y= self.transistor_bbox.top - self.tech.np_spacing//2 - self.tech.nanosheet_width//2
        else:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                # Calculation for PMOS at top
                nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
            else:
                # Calculation for NMOS at bottom
                nanosheet_center_y= self.transistor_bbox.top - self.tech.np_spacing//2 - self.tech.nanosheet_width//2
        #nanosheet 
        self._nanosheet_path = pya.Path([
                    pya.Point(self.nanosheet_left_x,nanosheet_center_y),
                    pya.Point(nanosheet_right_x,nanosheet_center_y)],
                self.tech.nanosheet_width)
        self.nanosheet_bbox = self._nanosheet_path.bbox()
    
    def calculate_sd_half_dr(self, abstract_transister_net, net_type, tech, center_x):
        if is_supply_net(abstract_transister_net) or is_ground_net(abstract_transister_net):
            self._tsvPath = pya.Path.new([
                    pya.Point(center_x, self.tsvBox.top),
                    pya.Point(center_x, self.tsvBox.bottom)],
                    self.interconnect_width,     
                    0,              
                    0)
            self.sd_top = self._tsvPath.bbox().top 
            self.sd_bottom = self._tsvPath.bbox().bottom 
            self.sd_top = max(self.sd_top, self.nanosheet_bbox.p2.y + self.tech.interconnect_extension)
            self.sd_bottom = min(self.sd_bottom, self.nanosheet_bbox.p1.y - self.tech.interconnect_extension)
        else:
            self.sd_top = self.transistor_bbox.top
            self.sd_bottom = self.transistor_bbox.bottom
            if not self.flipped:
                if self.tech.backside_power_rail:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                        self.sd_top -= self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom += self.tech.vertical_interconnect_spacing//2
                else:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                        self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2
            else:
                if self.tech.backside_power_rail:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                        self.sd_top -= self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom += self.tech.vertical_interconnect_spacing//2
                else:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                        self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2
            if self.counter_transistor :
                net1 = getattr(self.abstract_transistor, net_type)
                net2 = getattr(self.counter_transistor, net_type)
                if net1 != net2:
                        self.sd_top = self.sd_top + self.interconnect_top_fix.get(net_type,0) 
                        self.sd_bottom = self.sd_bottom +self.interconnect_bottom_fix.get(net_type,0)
            # tsvbox_center = (self.tsvBox.top + self.tsvBox.bottom) // 2
            # nanosheet_center = (self.nanosheet_bbox.top + self.nanosheet_bbox.bottom) // 2
            # if self.above_transistor and abstract_transister_net == getattr(self.above_transistor, net_type):
            #     if not is_power_net(abstract_transister_net) and tsvbox_center > nanosheet_center:
            #         self.sd_top += self.tech.vertical_interconnect_spacing
        path = pya.Path.new([
                pya.Point(center_x, self.sd_top),
                pya.Point(center_x, self.sd_bottom)],
                self.interconnect_width,    
                0,             
                0)
        return path

    def calculate_gate_path_half_dr(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix
        if not self.flipped:
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                    gate_top -= self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom += self.tech.vertical_gate_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                    gate_top = gate_top - self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2
        else:
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                    gate_top -= self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom += self.tech.vertical_gate_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                    gate_top = gate_top - self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2
        # if self.abstract_transistor and self.above_transistor and self.abstract_transistor.gate_net == self.above_transistor.gate_net:
            # print(f'top and bottom gates match at {(self.x, self.y)} - {self.abstract_transistor.gate_net} & {self.following_transistor.gate_net}')
            # gate_top += 2*self.tech.vertical_gate_spacing
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path
         
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            self._tsvPath.move(0, self.offset_y)
            shapes[self.diff_dvb].insert(self._tsvPath)

class FinFETLayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech, all_transistors, counter_transistor=None, channel_width=None, toFull=False, transistordict={}, channel_type=None):
        super().__init__(abstract_transistor, location, tech, all_transistors, counter_transistor, channel_width, toFull, transistordict, channel_type)
    def pmos_virtual_box(self):
        self.interconnect_width = self.tech.layer_width[self.diffcon] 
        
        self.transistor_center_y = -self.tech.power_rail_width//2 + self.extended_cell_height//4
        self.transistor_bbox = pya.Path(
                [
                    pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width,self.transistor_center_y),
                    pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, self.transistor_center_y)
                ],
            self.extended_cell_height//2
        ).bbox()
        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2),
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom)],
                self.interconnect_width,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 - self.tech.via_size_vertical[self.diff_dvb]//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
       
        self.interconnect_top_fix["source_net"] = -self.tech.vertical_interconnect_spacing//2
        self.interconnect_top_fix["drain_net"] = -self.tech.vertical_interconnect_spacing//2
        self.gate_top_fix = -self.tech.vertical_gate_spacing//2
        self.gate_bottom_fix  = 0

    def nmos_virtual_box(self):
        self.transistor_bbox = pya.Path(
                [
                    pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width,-self.tech.power_rail_width//2 + self.extended_cell_height - self.extended_cell_height//4),#replace x_Eff
                    pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, -self.tech.power_rail_width//2 + self.extended_cell_height - self.extended_cell_height//4) #replacex_Eff1
                ],
            self.extended_cell_height//2
    ).bbox()
        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_center_x, self.transistor_bbox.top),
                pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
                self.interconnect_width,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2  - self.tech.via_size_vertical[self.diff_dvb]//2)],
            self.interconnect_width,     
            0,              
            0).bbox()
        self.interconnect_bottom_fix["source_net"] = self.tech.vertical_interconnect_spacing//2
        self.interconnect_bottom_fix["drain_net"] = self.tech.vertical_interconnect_spacing//2
        self.gate_top_fix = 0
        self.gate_bottom_fix  = self.tech.vertical_gate_spacing//2

    def calculate_nanosheet_path(self):
        # Calculates location of pdiff and ndiff based on np_spacing
        nanosheet_right_x = self.transistor_bbox.right
        if self.x!= 0:
            self.nanosheet_left_x = self.transistor_bbox.left
        if (self.x + 1) == self.num_transistors:
            nanosheet_right_x = (self.x + 2)*self.tech.cell_width
        if not self.flipped:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                # Calculation for NMOS at top
                nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
            else:
                # Calculation for PMOS at bottom
                nanosheet_center_y= self.transistor_bbox.top - self.tech.np_spacing//2 - self.tech.nanosheet_width//2
        else:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                # Calculation for PMOS at top
                nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
            else:
                # Calculation for NMOS at bottom
                nanosheet_center_y= self.transistor_bbox.top - self.tech.np_spacing//2 - self.tech.nanosheet_width//2
        #nanosheet 
        self._nanosheet_path = pya.Path([
                    pya.Point(self.nanosheet_left_x,nanosheet_center_y),
                    pya.Point(nanosheet_right_x,nanosheet_center_y)],
                self.tech.nanosheet_width)
        self.nanosheet_bbox = self._nanosheet_path.bbox()
    
    def calculate_sd_half_dr(self, abstract_transister_net, net_type, tech, center_x):
        if is_supply_net(abstract_transister_net) or is_ground_net(abstract_transister_net):
            self._tsvPath = pya.Path.new([
                    pya.Point(center_x, self.tsvBox.top),
                    pya.Point(center_x, self.tsvBox.bottom)],
                    self.interconnect_width,     
                    0,              
                    0)
            self.sd_top = self._tsvPath.bbox().top 
            self.sd_bottom = self._tsvPath.bbox().bottom 
            self.sd_top = max(self.sd_top, self.nanosheet_bbox.p2.y + self.tech.interconnect_extension)
            self.sd_bottom = min(self.sd_bottom, self.nanosheet_bbox.p1.y - self.tech.interconnect_extension )
        else:
            self.sd_top = self.transistor_bbox.top
            self.sd_bottom = self.transistor_bbox.bottom
            if not self.flipped:
                if self.tech.backside_power_rail:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                        self.sd_top -= self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom += self.tech.vertical_interconnect_spacing//2
                else:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                        self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                    else:
                        self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2
            else:
                if self.tech.backside_power_rail:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                        self.sd_top -= self.tech.vertical_interconnect_spacing//2
                    else:
                        self.sd_bottom += self.tech.vertical_interconnect_spacing//2
                else:
                    if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                        self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                    else:
                        self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2
            if self.counter_transistor :
                net1 = getattr(self.abstract_transistor, net_type)
                net2 = getattr(self.counter_transistor, net_type)
                if net1 != net2:
                        self.sd_top = self.sd_top + self.interconnect_top_fix.get(net_type,0) 
                        self.sd_bottom = self.sd_bottom +self.interconnect_bottom_fix.get(net_type,0)
            tsvbox_center = (self.tsvBox.top + self.tsvBox.bottom) // 2
            nanosheet_center = (self.nanosheet_bbox.top + self.nanosheet_bbox.bottom) // 2
            if self.above_transistor and abstract_transister_net == getattr(self.above_transistor, net_type):
                if not is_power_net(abstract_transister_net) and tsvbox_center > nanosheet_center:
                    self.sd_top += self.tech.vertical_interconnect_spacing
        path = pya.Path.new([
                pya.Point(center_x, self.sd_top),
                pya.Point(center_x, self.sd_bottom)],
                self.interconnect_width,    
                0,             
                0)
        return path

    def calculate_gate_path_half_dr(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix
        if not self.flipped:
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                    gate_top -= self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom += self.tech.vertical_gate_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.channel_type == ChannelType.NMOS):
                    gate_top = gate_top - self.tech.vertical_gate_spacing//2 - self.tech.power_rail_width//2
                else:
                    gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2 + self.tech.power_rail_width//2
        else:
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                    gate_top -= self.tech.vertical_gate_spacing//2
                else:
                    gate_bottom += self.tech.vertical_gate_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.PMOS) or self.channel_type == ChannelType.PMOS):
                    gate_top = gate_top - self.tech.vertical_gate_spacing//2 - self.tech.power_rail_width//2
                else:
                    gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2 + self.tech.power_rail_width//2
        if self.abstract_transistor and self.above_transistor and self.abstract_transistor.gate_net == self.above_transistor.gate_net:
            gate_top += 2*self.tech.vertical_gate_spacing
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path
         
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            self._tsvPath.move(0, self.offset_y)
            shapes[self.diff_dvb].insert(self._tsvPath)

class CFETLayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech, all_transistors, counter_transistor=None, channel_width=None, toFull=False, transistordict={}, channel_type=None):
        super().__init__(abstract_transistor, location, tech, all_transistors, counter_transistor, channel_width, toFull, transistordict, channel_type)

    def pmos_virtual_box(self):
        self.transistor_bbox = pya.Path(
                [   pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width, self.transistor_center_y),#replace x_Eff
                    pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, self.transistor_center_y) #replacex_Eff1
                ],
            self.extended_cell_height
    ).bbox()
        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2),
                pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom)],
                self.interconnect_width,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom)],
            self.interconnect_width,     
            0,              
            0).bbox()       
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_bbox.center().x, self.transistor_bbox.bottom + self.tech.power_rail_width//2 - self.tech.via_size_vertical[self.diff_dvb]//2)],
            self.interconnect_width,     
            0,              
            0).bbox()    
        if self.counter_transistor:
            if self.abstract_transistor.gate_net != self.counter_transistor.gate_net:
                diffusion_top =  self.transistor_bbox.top 
                diffusion_bottom = self.transistor_bbox.bottom 
                if self.tech.half_dr and not self.tech.backside_power_rail:
                    diffusion_top -= self.tech.power_rail_width//2
                    diffusion_bottom += self.tech.power_rail_width//2
                self._diffusion = pya.Path.new([
                        pya.Point(self.center_x, diffusion_top),
                        pya.Point(self.center_x, diffusion_bottom)],
                        abs(-(self.tech.layer_width[self.poly] + 2*self.tech.inner_space_width + self.interconnect_width)),
                        0,
                        0)  
            if not self.tech.half_dr:
                self.__calculate_sd_interconnect("source_net")
                self.__calculate_sd_interconnect("drain_net")
            else:
                self.__calculate_sd_interconnect_half_dr("source_net")
                self.__calculate_sd_interconnect_half_dr("drain_net")
                            
        self.top_fix = 0
        self.bottom_fix = 0
        self.gate_top_fix = 0
        self.gate_bottom_fix  = 0
        self.well= pwell

    def nmos_virtual_box(self):
        self.transistor_bbox= pya.Path(
            [   pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width,self.transistor_center_y),
                pya.Point(self.center_x + self.tech.layer_width[self.poly]//2 + self.tech.inner_space_width + self.interconnect_width, self.transistor_center_y)
            ],
            self.extended_cell_height
        ).bbox()
        if self.counter_transistor:            
            if self.abstract_transistor.gate_net != self.counter_transistor.gate_net:
                diffusion_top =  self.transistor_bbox.top 
                diffusion_bottom = self.transistor_bbox.bottom 
                if self.tech.half_dr and not self.tech.backside_power_rail:
                    diffusion_top -= self.tech.power_rail_width//2
                    diffusion_bottom += self.tech.power_rail_width//2
                self._diffusion = pya.Path.new([
                        pya.Point(self.center_x, diffusion_top),
                        pya.Point(self.center_x, diffusion_bottom)],
                        abs(-(self.tech.layer_width[self.poly] + 2*self.tech.inner_space_width + self.interconnect_width)),
                        0,
                        0)
        
                self.to_optimize = False
            if not self.tech.half_dr:
                self.__calculate_sd_interconnect("source_net")
                self.__calculate_sd_interconnect("drain_net")
            else:
                self.__calculate_sd_interconnect_half_dr("source_net")
                self.__calculate_sd_interconnect_half_dr("drain_net")

        if self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
                pya.Point(self.transistor_center_x, self.transistor_bbox.top),
                pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
                self.interconnect_width//2,     
                0,              
                0).bbox()
        elif not self.tech.backside_power_rail and self.tech.half_dr:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2)],
            self.interconnect_width//2,     
            0,              
            0).bbox()
        else:
            self.tsvBox = pya.Path.new([
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2 + self.tech.via_size_vertical[self.diff_dvb]//2),
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width//2  - self.tech.via_size_vertical[self.diff_dvb]//2 )],
            self.interconnect_width//2,     
            0,              
            0).bbox()
        
        self.bottom_fix =  0
        self.top_fix = 0
        self.gate_top_fix = 0
        self.gate_bottom_fix  = 0
        self.well= nwell
    
    def __calculate_sd_interconnect(self,net_type):  
         counter_net = getattr(self.counter_transistor,net_type)
         abstract_net = getattr(self.abstract_transistor,net_type)
         if ((not is_power_net(abstract_net)) and is_power_net(counter_net)):
                if self.flipped:
                    if is_supply_net(counter_net):
                        bottom = self.tech.power_rail_width//2 
                        bottom = min(self.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, bottom)
                        self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom
                    elif is_ground_net(counter_net):
                        self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + self.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension 
                else:
                    if is_supply_net(counter_net):
                        bottom = self.tech.power_rail_width//2 
                        bottom = min(self.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                        self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom
                    elif is_ground_net(counter_net):
                        top = self.cell_height - self.tech.power_rail_width//2
                        top = max(self.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
                        self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + top

    def calculate_nanosheet_path(self):
        # Calculates location of ndiff and pdiff
        nanosheet_center_y= self.transistor_bbox.center().y
        nanosheet_right_x = self.transistor_bbox.right
        if self.x!= 0:
            self.nanosheet_left_x = self.transistor_bbox.left
        if (self.x + 1) == self.num_transistors:
            nanosheet_right_x =   (self.x + 2)*self.tech.cell_width
        #nanosheet 
        self._nanosheet_path = pya.Path([
                    pya.Point(self.nanosheet_left_x,nanosheet_center_y),
                    pya.Point(nanosheet_right_x,nanosheet_center_y)],
                self.tech.nanosheet_width)
        self.nanosheet_bbox = self._nanosheet_path.bbox()

    def calculate_sd_half_dr(self, abstract_transister_net, net_type, tech, center_x):
        if is_supply_net(abstract_transister_net) or is_ground_net(abstract_transister_net):
            self._tsvPath = pya.Path.new([
                    pya.Point(center_x, self.tsvBox.top),
                    pya.Point(center_x, self.tsvBox.bottom)],
                    self.interconnect_width,     
                    0,              
                    0)
            self.sd_top = self._tsvPath.bbox().top 
            self.sd_bottom = self._tsvPath.bbox().bottom 
            self.sd_top = max(self.sd_top, self.nanosheet_bbox.p2.y + self.tech.interconnect_extension)
            self.sd_bottom = min(self.sd_bottom, self.nanosheet_bbox.p1.y - self.tech.interconnect_extension )
        else:
            self.sd_top = self.transistor_bbox.top
            self.sd_bottom = self.transistor_bbox.bottom
            if self.tech.backside_power_rail:
                self.sd_top -= self.tech.vertical_interconnect_spacing//2
                self.sd_bottom += self.tech.vertical_interconnect_spacing//2
            else:
                self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2
                self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2
            if self.counter_transistor :
                net1 = getattr(self.abstract_transistor, net_type)
                net2 = getattr(self.counter_transistor, net_type)
                if net1 != net2:
                        self.sd_top = self.sd_top + self.interconnect_top_fix.get(net_type,0) 
                        self.sd_bottom = self.sd_bottom +self.interconnect_bottom_fix.get(net_type,0)
            if self.above_transistor and abstract_transister_net == getattr(self.above_transistor, net_type):
                if not is_power_net(abstract_transister_net):
                    self.sd_top += self.tech.vertical_interconnect_spacing
        path = pya.Path.new([
                pya.Point(center_x, self.sd_top),
                pya.Point(center_x, self.sd_bottom)],
                self.interconnect_width,    
                0,             
                0)
        return path

    def __calculate_sd_interconnect_half_dr(self,net_type):  
        counter_net = getattr(self.counter_transistor,net_type)
        abstract_net = getattr(self.abstract_transistor,net_type)
        if self.tech.backside_power_rail:
            if ((not is_power_net(abstract_net)) and is_power_net(counter_net)):
                if is_supply_net(counter_net):
                    bottom = self.tech.power_rail_width//2 
                    bottom = min(self.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                    self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom - self.tech.vertical_interconnect_spacing//2 
                elif is_ground_net(counter_net):
                    top = self.cell_height - self.tech.power_rail_width//2
                    top = max(self.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
                    self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + top + self.tech.vertical_interconnect_spacing//2 
        else:
            if ((not is_power_net(abstract_net)) and is_power_net(counter_net)):
                if is_supply_net(counter_net):
                    bottom = self.tech.power_rail_width//2 
                    bottom = min(self.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                    self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                elif is_ground_net(counter_net):
                    top = self.cell_height - self.tech.power_rail_width//2
                    top = max(self.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
                    self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + top + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2

    def calculate_gate_path_half_dr(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        gate_top -= self.tech.vertical_gate_spacing//2
        gate_bottom += self.tech.vertical_gate_spacing//2
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix 
                if self.gate_top_fix !=0:
                    gate_top += self.tech.vertical_gate_spacing//2
                if self.gate_bottom_fix !=0:
                    gate_bottom -= self.tech.vertical_gate_spacing//2
                if not self.tech.backside_power_rail:
                    if self.gate_top_fix !=0:
                        gate_top += self.tech.power_rail_width//2
                    if self.gate_bottom_fix !=0:
                        gate_bottom -= self.tech.power_rail_width//2
        # if not self.tech.backside_power_rail:
        #     gate_top -= self.tech.power_rail_width//2
        #     gate_bottom += self.tech.power_rail_width//2
        if self.abstract_transistor and self.above_transistor and self.abstract_transistor.gate_net == self.above_transistor.gate_net:
            # print(f'top and bottom gates match at {(self.x, self.y)} - {self.abstract_transistor.gate_net} & {self.following_transistor.gate_net}')
            gate_top += 2*self.tech.vertical_gate_spacing
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path

    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            self._tsvPath.move(0, self.offset_y)
            shapes[self.diff_dvb].insert(self._tsvPath)
            if self.tech.backside_power_rail and (self.abstract_transistor.channel_type == ChannelType.PMOS):
                p1 = self._tsvPath.bbox().p1  # Bottom-left point
                p2 = self._tsvPath.bbox().p2  # Top-right point
                # Create a new box with adjusted height
                new_box = pya.Box(p1.x, p1.y - extension, p2.x, p2.y + extension)
                shape = shapes[ndiffcon].insert(new_box)
                shapes[bspdn_pmos_via].insert(self._tsvPath)