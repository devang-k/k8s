logger = logging.getLogger('sivista_app')

class Device:
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], distance_to_outline: int, tech):
        raise NotImplemented()

class DeviceLayout(Device):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech,num_transistors, counter_transistor=None, channel_width =None, toFull=False):
        self.abstract_transistor = abstract_transistor
        self.to_optimize = True
        self.location = location
        self.tech = tech
        self.num_transistors = num_transistors
        # Bottom left of diffcon.
        self.x, self.y = location
        self.extended_cell_height = self.tech.cell_height + self.tech.power_rail_width//2 - (-self.tech.power_rail_width//2)
        self.center_x = (self.x + 1) * self.tech.cell_width
        self.counter_transistor = counter_transistor
        self.interconnect_width =  max(self.tech.layer_width[pdiffcon],self.tech.layer_width[ndiffcon])
        self._diffusion = None
        self.interconnect_top_fix = defaultdict(lambda:0)
        self.interconnect_bottom_fix = defaultdict(lambda:0)
        self.gate_top_fix = 0
        self.gate_bottom_fix = 0
        self.nanosheet_left_x = 0
        self.transistor_center_x = 0
        self.transistor_center_y = -self.tech.power_rail_width//2 + self.extended_cell_height//2
        self._tsvPath = None
        self.flipped = False
        if (self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0: 
            self.diffcon = ndiffcon
            self.diff_dvb = ndiff_dvb
            self.poly = npoly
            self.l_nanosheet = ndiff
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
            self.l_nanosheet = pdiff
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
                (self.poly, (self.center_x, self.tech.cell_height  + min(self.tech.gate_extension, self.tech.power_rail_width//2-self.tech.via_extension))),
                (self.poly, (self.center_x, self.tech.cell_height//2 - self.tech.nanosheet_width//2 - self.tech.gate_extension)),   
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
            Draw transistor outline box for pmos transistors
        """
        
        raise NotImplemented()

    @abstractmethod
    def nmos_virtual_box(self):
        """
            Draw transistor outline box for pmos transistors
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
        if self._source_path:
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
            shapes[gate_isolation].insert(self._diffusion) 
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
            shapes[self.l_nanosheet].insert(self._nanosheet_path)
       
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
                inst = shapes[dummy_gate].insert(self._gate_path)
                inst.set_property('optimize', False)
    
    @abstractmethod
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0):
        raise NotImplemented()

class GAALayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech,num_transistors, counter_transistor=None, channel_width =None, toFull=False):
        super().__init__(abstract_transistor, location, tech, num_transistors, counter_transistor, channel_width, toFull)
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
            nanosheet_right_x =   (self.x + 2)*self.tech.cell_width
        if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
            # Calculation for NMOS at top
            nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
        else:
            # Calculation for PMOS at bottom
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
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                    self.sd_top -= self.tech.vertical_interconnect_spacing//2
                else:
                    self.sd_bottom += self.tech.vertical_interconnect_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                    self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                else:
                    self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2
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

    def calculate_gate_path_half_dr(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix
        if self.tech.backside_power_rail:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                gate_top -= self.tech.vertical_gate_spacing//2
            else:
                gate_bottom += self.tech.vertical_gate_spacing//2
        else:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                gate_top = gate_top - self.tech.vertical_gate_spacing//2 - self.tech.power_rail_width//2
            else:
                gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2 + self.tech.power_rail_width//2
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path
         
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            shapes[self.diff_dvb].insert(self._tsvPath)
class FinFETLayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech,num_transistors, counter_transistor=None, channel_width =None, toFull=False):
        super().__init__(abstract_transistor, location, tech, num_transistors, counter_transistor, channel_width, toFull)
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
            nanosheet_right_x =   (self.x + 2)*self.tech.cell_width
        if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
            # Calculation for NMOS at top
            nanosheet_center_y= self.transistor_bbox.bottom + self.tech.np_spacing//2 + self.tech.nanosheet_width//2 
        else:
            # Calculation for PMOS at bottom
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
            if self.tech.backside_power_rail:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                    self.sd_top -= self.tech.vertical_interconnect_spacing//2
                else:
                    self.sd_bottom += self.tech.vertical_interconnect_spacing//2
            else:
                if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                    self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                else:
                    self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2
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

    def calculate_gate_path_half_dr(self):
        gate_top = self.transistor_bbox.top
        gate_bottom = self.transistor_bbox.bottom
        if not self.abstract_transistor or (self.counter_transistor and (self.abstract_transistor.gate_net != self.counter_transistor.gate_net)):
            if self.location[0] > -1 and self.location[0] < self.num_transistors: # should not apply for diffussion break
                gate_top += self.gate_top_fix
                gate_bottom += self.gate_bottom_fix
        if self.tech.backside_power_rail:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                gate_top -= self.tech.vertical_gate_spacing//2
            else:
                gate_bottom += self.tech.vertical_gate_spacing//2
        else:
            if ((self.abstract_transistor and self.abstract_transistor.channel_type == ChannelType.NMOS) or self.y==0):
                gate_top = gate_top - self.tech.vertical_gate_spacing//2 - self.tech.power_rail_width//2
            else:
                gate_bottom = gate_bottom + self.tech.vertical_gate_spacing//2 + self.tech.power_rail_width//2
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path
         
    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            shapes[self.diff_dvb].insert(self._tsvPath)

class CFETLayout(DeviceLayout):
    def __init__(self, abstract_transistor: Transistor, location: Tuple[int, int], tech,num_transistors, counter_transistor=None, channel_width =None, toFull=False):
        super().__init__(abstract_transistor,location, tech, num_transistors, counter_transistor, channel_width, toFull)

    def pmos_virtual_box(self):
        self.transistor_bbox = pya.Path(
                [   pya.Point(self.center_x - self.tech.layer_width[self.poly]//2 - self.tech.inner_space_width - self.interconnect_width,self.transistor_center_y),#replace x_Eff
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
            pya.Point(self.transistor_center_x, self.transistor_bbox.top - self.tech.power_rail_width),
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
                        bottom = min(self.tech.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, bottom)
                        self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom
                    elif is_ground_net(counter_net):
                        self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + self.tech.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension 
                else:
                    if is_supply_net(counter_net):
                        bottom = self.tech.power_rail_width//2 
                        bottom = min(self.tech.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                        self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom
                    elif is_ground_net(counter_net):
                        top = self.tech.cell_height - self.tech.power_rail_width//2
                        top = max(self.tech.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
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
                self.sd_top = self.sd_top - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                self.sd_bottom = self.sd_bottom + self.tech.vertical_interconnect_spacing//2 + self.tech.power_rail_width//2
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

    def __calculate_sd_interconnect_half_dr(self,net_type):  
        counter_net = getattr(self.counter_transistor,net_type)
        abstract_net = getattr(self.abstract_transistor,net_type)
        if self.tech.backside_power_rail:
            if ((not is_power_net(abstract_net)) and is_power_net(counter_net)):
                if is_supply_net(counter_net):
                    bottom = self.tech.power_rail_width//2 
                    bottom = min(self.tech.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                    self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom - self.tech.vertical_interconnect_spacing//2 
                elif is_ground_net(counter_net):
                    top = self.tech.cell_height - self.tech.power_rail_width//2
                    top = max(self.tech.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
                    self.interconnect_top_fix[net_type] = -self.transistor_bbox.top + top + self.tech.vertical_interconnect_spacing//2 
        else:
            if ((not is_power_net(abstract_net)) and is_power_net(counter_net)):
                if is_supply_net(counter_net):
                    bottom = self.tech.power_rail_width//2 
                    bottom = min(self.tech.cell_height//2 -  self.tech.nanosheet_width//2 - self.tech.interconnect_extension, float('inf'))
                    self.interconnect_bottom_fix[net_type] = bottom - self.transistor_bbox.bottom - self.tech.vertical_interconnect_spacing//2 - self.tech.power_rail_width//2
                elif is_ground_net(counter_net):
                    top = self.tech.cell_height - self.tech.power_rail_width//2
                    top = max(self.tech.cell_height//2 +  self.tech.nanosheet_width//2 + self.tech.interconnect_extension, top)
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
        if not self.tech.backside_power_rail:
            gate_top -= self.tech.power_rail_width//2
            gate_bottom += self.tech.power_rail_width//2
        gate_path = pya.Path.new([
                pya.Point(self.transistor_center_x, gate_top),
                pya.Point(self.transistor_center_x, gate_bottom)],
                self.tech.layer_width[self.poly],
                0,
                0)
        return gate_path

    def draw_tsvBar(self, shapes: Dict[Any, pya.Shapes], extension = 0) -> None:
        if self._tsvPath:
            shapes[self.diff_dvb].insert(self._tsvPath)
            if self.tech.backside_power_rail and (self.abstract_transistor.channel_type == ChannelType.PMOS):
                p1 = self._tsvPath.bbox().p1  # Bottom-left point
                p2 = self._tsvPath.bbox().p2  # Top-right point
                # Create a new box with adjusted height
                new_box = pya.Box(p1.x, p1.y - extension, p2.x, p2.y + extension)
                shape = shapes[ndiffcon].insert(new_box)
                shapes[bspdn_pmos_via].insert(self._tsvPath)
                