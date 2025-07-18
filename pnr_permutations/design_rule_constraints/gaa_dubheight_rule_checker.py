from pnr_permutations.design_rule_constraints.checker import RuleChecker
import logging
logger = logging.getLogger('sivista_app')

def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets

def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets

def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)


class GAADoubleHeightDesignRuleCheck(RuleChecker):

    def __init__(self, layerMap, layer_properties, layerNumber, y_min, y_mid, y_max):
        super().__init__(layerMap, layer_properties, layerNumber)
        self.y_min = y_min
        self.y_mid = y_mid
        self.y_max = y_max

    def checkLayerLayerExtension(self, layer1, layer_number_list, val):
        # logger.debug("Checking Layer layer Extension.... ")
        polygon_list = self.layerMap[layer1].polygons # layer 1 = M0
        new_polygon_list = []
        flag = False
        if not self.layer_properties.backside_power_rail:
            # Remove polygons associated with VDD & VSS in M0 
            for m0_polygon in polygon_list:
                flag = False  # Reset flag for every m0_polygon
                for textPolygon in m0_polygon.textPolygons:
                    if is_power_net(textPolygon.string):
                        flag = True
                        break  # No need to check further labels if one matches
                if not flag:
                    new_polygon_list.append(m0_polygon)
        polygon_list = new_polygon_list
        for layer1Polygon in polygon_list:
            for layer2Polygon in layer1Polygon.layerMap: 
                if layer2Polygon.layer in layer_number_list:
                    l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                    if (self.is_top_subcell(layer1Polygon) and self.is_top_subcell(layer2Polygon)) or self.is_bottom_subcell(layer1Polygon) and self.is_bottom_subcell(layer2Polygon):
                        leftExtension = l2Bounds[0] - l1Bounds[0] 
                        rightExtension = l1Bounds[2] - l2Bounds[2]
                        topExtension = l1Bounds[1] - l2Bounds[1]
                        bottomExtension =l2Bounds[3] - l1Bounds[3]

                        if topExtension < val or bottomExtension < val or leftExtension < val or rightExtension < val:
                            logger.debug(f" Extension DRC Failed for layer {layer2Polygon.layer} {layer1} {layer2Polygon.direction} {topExtension} {bottomExtension} {val}")
                            return False

        # logger.debug(f"Passed for layer : {layer1} - {layer2} {layer2Polygon.direction}")
        return True
    
    def checkLayerNanoSheetExtension(self, layer1,layer2, val):
        # logger.debug("Checking Nanosheet extension ....")
        for layer1Polygon in self.layerMap[layer1].polygons:
            if layer1Polygon.datatype==0:
                for layer2Polygon in self.layerMap[layer2].polygons:
                    if layer2Polygon.datatype==0:
                        if (self.is_top_subcell(layer1Polygon) and self.is_top_subcell(layer2Polygon)) or self.is_bottom_subcell(layer1Polygon) and self.is_bottom_subcell(layer2Polygon):
                            l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                            topExtension = l1Bounds[1] - l2Bounds[1]
                            bottomExtension = l2Bounds[3] - l1Bounds[3]
                            if topExtension<val or bottomExtension<val:
                                logger.debug(f"Failed for layer : {layer2} - {l2Bounds}")
                                return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True
    
    def checkVddVssPosition(self, flipped = 'R0'):
        vdd = set()
        vss = set()
        if self.layer_properties.backside_power_rail:
            for polygon in self.layerMap[self.layerNumber['BSPowerRail']].polygons:
                for text in polygon.textPolygons:
                    text_dictionary = text.extract_as_dict()
                    if is_supply_net(text_dictionary['text']):
                        vdd.add(polygon)
                    if is_ground_net(text_dictionary['text']):
                        vss.add(polygon)
        else:
            #extract pwr/gnd polygons in layer 1000 in topside
            for polygon in self.layerMap[self.layerNumber['M0']].polygons:
                for text in polygon.textPolygons:
                    text_dictionary = text.extract_as_dict()
                    if is_supply_net(text_dictionary['text']):
                        vdd.add(polygon)
                    if is_ground_net(text_dictionary['text']):
                        vss.add(polygon)
        if len(vdd) != 1 and len(vss) !=2 : return False
        vss = list(vss)
        vdd = list(vdd)
        if min(vss[0].point.bounds[1], vss[0].point.bounds[3]) < min(vss[1].point.bounds[1], vss[1].point.bounds[3]):
            if min(vss[0].point.bounds[1], vss[0].point.bounds[3]) < min(vdd[0].point.bounds[1], vdd[0].point.bounds[3]) < min(vss[1].point.bounds[1], vss[1].point.bounds[3]):
                return True
        elif min(vss[0].point.bounds[1], vss[0].point.bounds[3]) > min(vss[1].point.bounds[1], vss[1].point.bounds[3]):
            if min(vss[0].point.bounds[1], vss[0].point.bounds[3]) > min(vdd[0].point.bounds[1], vdd[0].point.bounds[3]) > min(vss[1].point.bounds[1], vss[1].point.bounds[3]):
                return True
        logger.debug('Failed: VDD VSS positions incorrect')
        return False
    
    def checkVerticalNanosheetSpacing(self, layer1, layer2, val):
        # logger.debug("Checking Vertical Nanosheet Spacing ....")
        for layer1Polygon in self.layerMap[layer1].polygons:
            for layer2Polygon in self.layerMap[layer2].polygons:
                if layer2Polygon.datatype == 0 and layer1Polygon.datatype == 0:
                    l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                    if (self.is_top_subcell(layer1Polygon) and self.is_top_subcell(layer2Polygon)) or self.is_bottom_subcell(layer1Polygon) and self.is_bottom_subcell(layer2Polygon):
                        nearest_pair, distance = self.find_nearest_coordinate([l1Bounds[1],l1Bounds[3]],[l2Bounds[1],l2Bounds[3]])
                        if distance != val:
                            logger.debug(f" NP diffusion spacing - Failed for layer : {layer1} {layer2}")
                            return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True
    
    def checkVerticalInterconnectSpacing(self, layer1, layer2, val):

        for layer1Polygon in self.layerMap[layer1].polygons:
            if layer1Polygon.datatype != 0:
                continue  # Skip early if datatype is not 0

            layer1_is_top = self.is_top_subcell(layer1Polygon)
            layer1_is_bottom = self.is_bottom_subcell(layer1Polygon)
            layer1_is_middle = not (layer1_is_top or layer1_is_bottom)
            l1_bounds = layer1Polygon.point.bounds  # Cache once

            for layer2Polygon in self.layerMap[layer2].polygons:
                if layer2Polygon.datatype != 0:
                    continue  # Skip early

                layer2_is_top = self.is_top_subcell(layer2Polygon)
                layer2_is_bottom = self.is_bottom_subcell(layer2Polygon)
                layer2_is_middle = not (layer2_is_top or layer2_is_bottom)
                l2_bounds = layer2Polygon.point.bounds  # Cache once

                # Group matching conditions to handle pdiffcon connections to VDD in multiheight
                same_vertical_group = (
                    (layer1_is_top and (layer2_is_top or layer2_is_middle)) or
                    (layer2_is_top and layer1_is_middle) or
                    (layer1_is_bottom and (layer2_is_bottom or layer2_is_middle)) or
                    (layer2_is_bottom and layer1_is_middle)
                )

                if not same_vertical_group:
                    continue  # Skip early

                # Check if they are aligned in x-axis
                if l1_bounds[0] != l2_bounds[0] or l1_bounds[2] != l2_bounds[2]:
                    continue

                # Check Y coordinate overlap
                if not max(l1_bounds[1], l2_bounds[1]) <= min(l1_bounds[3], l2_bounds[3]):
                    _, distance = self.find_nearest_coordinate(
                        [l1_bounds[1], l1_bounds[3]],
                        [l2_bounds[1], l2_bounds[3]]
                    )
                    if distance != 0 and distance < val:
                        logger.debug(f"Diffcon ETE spacing : Failed for layer : {layer2}")
                        return False

        return True
    
    def is_bottom_subcell(self, component):
        """True if the component lies entirely in the lower half of the global Y-range."""
        low, high = self.y_min, self.y_mid
        y1, y2 = component.point.bounds[1], component.point.bounds[3]
        return (low <= y1 <= high) and (low <= y2 <= high)

    def is_top_subcell(self, component):
        """True if the component lies entirely in the upper half of the global Y-range."""
        low, high = self.y_mid, self.y_max
        y1, y2 = component.point.bounds[1], component.point.bounds[3]
        return (low <= y1 <= high) and (low <= y2 <= high)
    
    def checkDRC(self, strict=True, update=False):
        if not self.checkWidth(update):
            return False
        if not self.checkconnections():
            return False
        if not self.checkLayerLayerExtension(self.layerNumber['M0'],[self.layerNumber['PMOSInterconnect'], self.layerNumber['NMOSInterconnect'],self.layerNumber['NMOSGate'], self.layerNumber['PMOSGate'] ],self.layer_properties.InterconnectExtensionfromM0):
            return False
        if not self.checkLayerLayerGap(self.layerNumber['M1'], self.layerNumber['M1'], self.layer_properties.layer1000Pitch - self.layer_properties.wireWidth['metal1'], 'V'):
            return False
        if not self.checkLayerLayerGap(self.layerNumber['M0'], self.layerNumber['M0'], self.layer_properties.layer1000Spacing, 'H'):
            return False
        if not self.checkVddVssPosition(flipped=self.layer_properties.flipped):
            return False
        if not self.checkInnerSpace(self.layer_properties.InnerSpaceWidth):
            if update:
                if update:
                    self.layer_properties.InnerSpaceWidth = self.checkInnerSpace(self.layer_properties.InnerSpaceWidth, update)
                    return self.checkInnerSpace(self.layer_properties.InnerSpaceWidth)
            return False
        if not self.checkPitch(layer=self.layerNumber['M0'], val=self.layer_properties.layer1000Pitch):
            return False
        if not self.checkPitch(layer=self.layerNumber['M1'], val=self.layer_properties.layer1050Pitch):
            return False
        if not self.checkViaExtension(self.layerNumber['VIA_M0_PMOSInterconnect'], self.layer_properties.ViaExtension):
            return False
        if not self.checkViaExtension(self.layerNumber['VIA_M0_PMOSGate'], self.layer_properties.ViaExtension):
            return False   
        if not self.checkViaExtension(self.layerNumber['VIA_M0_NMOSInterconnect'], self.layer_properties.ViaExtension):
            return False
        if not self.checkViaExtension(self.layerNumber['VIA_M0_NMOSGate'], self.layer_properties.ViaExtension):
            return False   
        if not self.checkLayerNanoSheetExtension(self.layerNumber['NmosNanoSheet'], self.layerNumber['NMOSGate'], self.layer_properties.gateSheetExtension):
            return False
        if not self.checkLayerNanoSheetExtension(self.layerNumber['PmosNanoSheet'], self.layerNumber['PMOSGate'], self.layer_properties.gateSheetExtension):
            return False
        if not self.checkLayerNanoSheetExtension(self.layerNumber['NmosNanoSheet'], self.layerNumber['NMOSInterconnect'], self.layer_properties.interconnectSheetExtension):
            return False
        if not self.checkLayerNanoSheetExtension(self.layerNumber['PmosNanoSheet'], self.layerNumber['PMOSInterconnect'], self.layer_properties.interconnectSheetExtension):
            return False     
        if not self.checkVerticalNanosheetSpacing(self.layerNumber['PmosNanoSheet'],self.layerNumber['NmosNanoSheet'],self.layer_properties.np_spacing):
            return False        
        if not self.checkVerticalGateSpacing(self.layerNumber['PMOSGate'],self.layerNumber['NMOSGate'],self.layer_properties.vertical_gate_spacing):
            return False        
        if not self.checkVerticalInterconnectSpacing(self.layerNumber['PMOSInterconnect'],self.layerNumber['NMOSInterconnect'],self.layer_properties.vertical_interconnect_spacing):
            return False
        if not self.checkViaEnclosure(self.layerNumber['VIA_M0_PMOSInterconnect'], [self.layerNumber['M0']], [self.layerNumber['PMOSInterconnect'], self.layerNumber['NMOSInterconnect']]):
            return False
        if not self.checkViaEnclosure(self.layerNumber['VIA_M0_NMOSInterconnect'], [self.layerNumber['M0']], [self.layerNumber['NMOSInterconnect'], self.layerNumber['PMOSInterconnect']]):
            return False
        if not self.checkViaEnclosure(self.layerNumber['VIA_M0_PMOSGate'], [self.layerNumber['M0']], [self.layerNumber['PMOSGate'], self.layerNumber['NMOSGate']]):
            return False
        if not self.checkViaEnclosure(self.layerNumber['VIA_M0_NMOSGate'], [self.layerNumber['M0']], [self.layerNumber['NMOSGate'], self.layerNumber['PMOSGate']]):
            return False
        if not self.checkViaEnclosure(self.layerNumber.get('VIA_M0_M1', 0), [self.layerNumber['M0']], [self.layerNumber['M1']]):
            return False
        return True