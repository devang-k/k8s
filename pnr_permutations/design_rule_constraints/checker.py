# pnr_permutations/DRC/checker.py
from abc import ABC,abstractmethod
# from stdcell_generation.common.net_util import is_ground_net, is_supply_net
from shapely.geometry import Point
import logging
logger = logging.getLogger('sivista_app')

def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets

def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets

class RuleChecker:
    def __init__(self,layerMap,layer_properties, layerNumber):
        self.layerMap = layerMap
        self.ignoredLBounds = set()
        self.layer_properties = layer_properties
        self.layerNumber = layerNumber
    
    def get_layerMap(self):
        """Getter for layerMap."""
        return self.layerMap
     
    def set_layerMap(self, new_map):
        if not isinstance(new_map, dict):
                raise ValueError("LayerMap must be a dictionary")
            # You can include additional validation or processing here
        self.layerMap = new_map
    
    def ignoredLBounds(self):
        """Getter for ignoredLBounds."""
        return self.ignoredLBounds   
    
    def get_ignoredLBounds(self, value):
        """Setter for ignoredLBounds. Value should be a set."""
        if not isinstance(value, set):
            raise ValueError("ignoredLBounds must be a set")
        self.ignoredLBounds = value
    
    def get_layer_properties(self):
        """Getter for layer_properties."""
        return self.layer_properties

    def set_layer_properties(self, value):

        """Setter for layer_properties."""
        self.layer_properties = value

    def checkWidth(self, update = False):
        for l,lc in self.layerMap.items():
            if update:
                lc.checkWidth(update)
            if not lc.checkWidth():
                return False
        return True
    
    def checkReach(self):
        for l,lc in self.layerMap.items():
            if lc.hinder:
                # logger.debug(f"checking the hindering layer : {lc.hinder} for layer {l}")
                for polygon in self.layerMap[self.layerNumber[lc.hinder]].polygons:
                    for viapolygon in lc.polygons:
                        if viapolygon.point.intersects(polygon.point):
                            logger.debug(f'Failed check reach - Checking for the intersection {viapolygon.point} vs {polygon.point}')
                            return False
        return True
        
    
    def checkconnections(self):
        for l,lc in self.layerMap.items():
            if not lc.checkconnection():
                return False
        return True
    
    def checkVddVssPosition(self, flipped = 'R0'):
        vdd = set()
        vss = set()
        if self.layer_properties.backside_power_rail:
            for polygon in self.layerMap[self.layerNumber['PMOSInterconnect']].polygons:
                for connection in polygon.layerMap:
                    if connection.layer == self.layerNumber['BSPowerRail']:
                        vdd.add(connection.point.bounds)
            for polygon in self.layerMap[self.layerNumber['NMOSInterconnect']].polygons:
                for connection in polygon.layerMap:
                    if connection.layer == self.layerNumber['BSPowerRail']:
                        vss.add(connection.point.bounds)
        else:
            #extract pwr/gnd polygons in layer 1000 in topside
            for polygon in self.layerMap[self.layerNumber['M0']].polygons:
                for text in polygon.textPolygons:
                    text_dictionary = text.extract_as_dict()
                    if is_supply_net(text_dictionary['text']):
                        vdd.add(polygon.point.bounds)
                    if is_ground_net(text_dictionary['text']):
                        vss.add(polygon.point.bounds)
        vddX1,vddY1,vddX2,vddY2 = vdd.pop()
        vssX1,vssY1,vssX2,vssY2 = vss.pop()
        if flipped == 'Mx':
            if not vssY1>vddY2:
                logger.debug("VDD is not south-side & VSS is not north-side")
                return False
        else:
            if not vddY1>vssY2:
                logger.debug("VDD is not north-side & VSS is not south-side")
                return False
        # logger.debug("VDD and VSS are in valid positions")
        return True

    def checkInnerSpace(self, val, update = False):
        uniqueBounds = set()
        for l,v in self.layerMap.items():
            if (self.layerMap[l].layer_name.startswith("NMOS")  or self.layerMap[l].layer_name.startswith("PMOS")) and v.direction == 'V':
                for polygon in v.polygons:
                    #add the vertical bounds of the polygon
                    if polygon.datatype==0:
                        bnd = polygon.point.bounds
                        l,r = bnd[0],bnd[2]
                        uniqueBounds.add((l,r))
        uniqueBounds = list(uniqueBounds)
        uniqueBounds.sort(key=lambda x: (x[0]))
        calculatedInnerWidth = float("inf")
        for i in range(1,len(uniqueBounds)):
            calculatedInnerWidth = min(calculatedInnerWidth, uniqueBounds[i][0]-uniqueBounds[i-1][1])
        if calculatedInnerWidth >= val:
            # logger.debug("Inner Space width satisfied")
            return True
        else:
            actual = val
            logger.debug(f"Inner space width does not match Specified: {actual} and Calculated : {calculatedInnerWidth}")
            if update:
                return val
                
        return False
    def checkDummyislands(self, via, layer1, layer2):      
        #hardcoded for dummy islands
        for via in self.layerMap[via].polygons:
                # logger.debug(f'{via.point.bounds} via')
                for polygon1 in self.layerMap[layer1].polygons:
                    # logger.debug(f'{polygon1.point.bounds}  layer1: {layer1}')
                    if via.point.intersects(polygon1.point):
                        #logger.debugln(f"{via.point.bounds} intersecting {polygon1.point.bounds}")
                        dummyIsland = False    
                        for polygon2 in self.layerMap[layer2].polygons:
                            # logger.debug(f'{polygon2.point.bounds} layer2: {layer2}')
                            if via.point.intersects(polygon2.point):
                                polygon2.datatype = 3
                                dummyIsland = True
                                self.ignoredLBounds.add(polygon2.point.bounds)
                                break
                        if not dummyIsland:
                            logger.debug(f"Dummy Island Missing for via at {via.point.bounds}")
                            return False
        # logger.debug("Dummy Islands Found")
        return True
    
    def checkPitch(self,layer = 0, val=0, update = False):
        if layer==0:
            return True
        centerPoints = set()
        lc = self.layerMap[layer]
        for i in range(len(lc.polygons)):
            for j in range(i+1,len(lc.polygons)):
                p1,p2 = lc.polygons[i].point,lc.polygons[j].point
                if p1.intersects(p2):
                    logger.debug(f"Layer {layer} Pitch Failed as the layers intersect")
                    return False
        for polygon in lc.polygons:
            if polygon.datatype==0:
                bnd = polygon.point.bounds
                if lc.direction=='H':    
                    centerPoints.add(bnd[1]+(bnd[3]-bnd[1])/2)
                else:
                    centerPoints.add(bnd[0]+(bnd[2]-bnd[0])/2)
        centerPoints = list(centerPoints)
        centerPoints.sort()
        calculatedPitch = float("inf")
        for i in range(1,len(centerPoints)):
            calculatedPitch = min(calculatedPitch, centerPoints[i]-centerPoints[i-1])
        if calculatedPitch >= val:
            # logger.debug(f"Layer {layer} Pitch satisfied")
            return True
        else:
            actual = val
            logger.debug(f"Pitch does not match Specified: {actual} and Calculated : {calculatedPitch}")
            if update:
                return val
        return False

    def checkViaExtension(self, via, val, update = False):
        if self.layer_properties.backside_power_rail:
            # logger.debug("Via Extension Rule .... ")
            for viaPolygon in self.layerMap[via].polygons:
                for layerPolygon in viaPolygon.layerMap:
                    viaBounds, layerBounds = viaPolygon.point.bounds, layerPolygon.point.bounds
                    if layerPolygon.direction == "H":
                        topExtension = layerBounds[1] - viaBounds[1]
                        bottomExtension = viaBounds[3] - layerBounds[3]
                        if topExtension<val or bottomExtension<val:
                            logger.debug(f"Failed for layer {via} , {layerPolygon.point.bounds}")
                            if update:
                                return topExtension
                            return False
                    elif layerPolygon.direction == "V":
                        leftExtension = layerBounds[0] - viaBounds[0]
                        rightExtension = viaBounds[2] - layerBounds[2]
                        if leftExtension<val or rightExtension<val:
                            logger.debug(f"Failed for layer {via} , {layerPolygon.point.bounds}")
                            if update:
                                return leftExtension
                            return False
                        
            # logger.debug(f"Passed for layer : {via}")
        return True
    
    def checkLayerViaExtension(self, layer, val, update = False):
        # logger.debug("Layer Extension Rule Past Via .... ")
        for layerPolygon in self.layerMap[layer].polygons:
            for viaPolygon in layerPolygon.layerMap:
                viaBounds, layerBounds = viaPolygon.point.bounds, layerPolygon.point.bounds
                if layerPolygon.direction == "V":
                    topExtension = layerBounds[1] - viaBounds[1]
                    bottomExtension = viaBounds[3] - layerBounds[3]
                    if topExtension<val or bottomExtension<val:
                        logger.debug(f"Failed for layer {layer} , {layerPolygon.point.bounds}")

                        return False
                elif layerPolygon.direction == "H":
                    leftExtension = layerBounds[0] - viaBounds[0]
                    rightExtension = viaBounds[2] - layerBounds[2]
                    if leftExtension<val or rightExtension<val:
                        logger.debug(f"Failed for layer {layer} , {layerPolygon.point.bounds}")
                        return False
        # logger.debug(f"Passed for layer : {layer}")
        return True
    
    def checkLayerNanoSheetExtension(self, layer1,layer2, val):
        # logger.debug("Checking Nanosheet extension ....")
        for layer1Polygon in self.layerMap[layer1].polygons:
            if layer1Polygon.datatype==0:
                for layer2Polygon in self.layerMap[layer2].polygons:
                    if layer2Polygon.datatype==0:
                        l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                        topExtension = l1Bounds[1] - l2Bounds[1]
                        bottomExtension = l2Bounds[3] - l1Bounds[3]
                        if topExtension<val or bottomExtension<val:
                            logger.debug(f"Failed for layer : {layer2} - {l2Bounds}")
                            return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True
    
    def checkLayerLayerGap(self, layer1, layer2, val, direction):
        # logger.debug(f"Checking layer gap in the {'horizontal' if direction == 'H' else 'vertical'} direction ....")

        def bounded_by(layer1, layer2):
            if direction == 'V':
                diff1 = layer2.point.bounds[0] - layer1.point.bounds[0]
                diff2 = layer2.point.bounds[2] - layer1.point.bounds[2]
            else:
                diff1 = layer2.point.bounds[1] - layer1.point.bounds[1]
                diff2 = layer2.point.bounds[3] - layer1.point.bounds[3]
            return diff1*diff2 <= 0

        for layer1Polygon in self.layerMap[layer1].polygons:
            if layer1Polygon.datatype==0:
                for layer2Polygon in self.layerMap[layer2].polygons:
                    if layer2Polygon.datatype==0:
                        center1 = layer1Polygon.point.centroid
                        center2 = layer2Polygon.point.centroid
                        if layer1==layer2 and layer1Polygon==layer2Polygon:
                            continue
                        if direction == 'V' and (center1.x == center2.x or bounded_by(layer1Polygon, layer2Polygon)):
                            if center1.y < center2.y:
                                bottomPolygon = layer1Polygon
                                topPolygon = layer2Polygon
                            else:
                                bottomPolygon = layer2Polygon
                                topPolygon = layer1Polygon
                            if topPolygon.point.intersects(bottomPolygon.point) or topPolygon.point.bounds[1] - bottomPolygon.point.bounds[3] < val:
                                logger.debug(f'Failed vertical gap check for layers {layer1} and {layer2}')
                                return False
                        elif direction == 'H' and (center1.y == center2.y or bounded_by(layer1Polygon, layer2Polygon)):
                            if center1.x < center2.x:
                                leftPolygon = layer1Polygon
                                rightPolygon = layer2Polygon
                            else:
                                leftPolygon = layer2Polygon
                                rightPolygon = layer1Polygon
                            if leftPolygon.point.intersects(rightPolygon.point) or rightPolygon.point.bounds[0] - leftPolygon.point.bounds[2] < val:
                                logger.debug(f'Failed horizontal gap check for layers {layer1} and {layer2}')
                                return False
        # logger.debug(f"Passed for layers : {layer1} and {layer2} in {direction}")
        return True

    def checkNanoSheetGap(self, layer1, layer2, val):
        # logger.debug("Checking Nanosheet Gap ....")
        for layer1Polygon in self.layerMap[layer1].polygons:
            if layer1Polygon.datatype==0:
                for layer2Polygon in self.layerMap[layer2].polygons:
                    if layer2Polygon.datatype==0:
                        l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                        topGap = l1Bounds[1] - l2Bounds[3]
                        bottomGap = l2Bounds[1] - l1Bounds[3]
                        if (topGap>0 and topGap<val) or (bottomGap>0 and bottomGap<val):
                            logger.debug(f"Failed for layer : {layer2}")
                            return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True

    def checkNwell(self, layer, gateSheetExtension):
        pnanosheets = set()
        nwell = set()
        for polygon in self.layerMap[self.layerNumber['PmosNanoSheet']].polygons:
            pnanosheets.add(polygon.point.bounds)
        for polygon in self.layerMap[layer].polygons:
            nwell.add(polygon.point.bounds)

        nwellX1,nwellY1,nwellX2,nwellY2 = nwell.pop()
        for layer1Polygon in self.layerMap[self.layerNumber['Boundary']].polygons:
            if layer1Polygon.datatype == 0:
                bounds = layer1Polygon.point.bounds
        for pnanosheet in pnanosheets:
            if pnanosheet[0] >= nwellX1 and pnanosheet[1] >= nwellY1 and pnanosheet[2] <= nwellX2 and pnanosheet[3] <= nwellY2 and nwellX1 >= bounds[0] and pnanosheet[1]-nwellY1 == gateSheetExtension and nwellX2 >= bounds[2] and nwellY2-pnanosheet[3] == gateSheetExtension:
                # logger.debug("Nwell to pdiff spacing is valid")
                return True
        logger.debug("Nwell to pdiff spacing is invalid")
        return False

    def checkLayerLayerExtension(self, layer1, layer_number_list, val):
        # logger.debug("Checking Layer layer Extension.... ")
        polygon_list = self.layerMap[layer1].polygons # layer 1 = M0
        if not self.layer_properties.backside_power_rail:
            # Remove polygons associated with VDD & VSS in M0 
            # First and last polygons are associated with VDD & VSS in polygon list sorted at initialization
            polygon_list = polygon_list[1:-1]
        for layer1Polygon in polygon_list:
            for layer2Polygon in layer1Polygon.layerMap: 
                if layer2Polygon.layer in layer_number_list:
                    l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                    leftExtension = l2Bounds[0] - l1Bounds[0] 
                    rightExtension = l1Bounds[2] - l2Bounds[2]
                    topExtension = l1Bounds[1] - l2Bounds[1]
                    bottomExtension =l2Bounds[3] - l1Bounds[3]

                    if topExtension < val or bottomExtension < val or leftExtension < val or rightExtension < val:
                        logger.debug(f"Failed for layer {layer2Polygon.layer} {layer1} {layer2Polygon.direction} {topExtension} {bottomExtension} {val}")
                        return False

        # logger.debug(f"Passed for layer : {layer1} - {layer2} {layer2Polygon.direction}")
        return True

    def find_nearest_coordinate(self, y1_cord, y2_cord):
        nearest_pair = None
        min_diff = float('inf')

        for cord1 in y1_cord:
            for cord2 in y2_cord:
                diff = abs(cord1 - cord2)  # Absolute difference
                if diff < min_diff:
                    min_diff = diff
                    nearest_pair = (cord1, cord2)

        return nearest_pair, min_diff

    def checkVerticalGateSpacing(self, layer1, layer2, val):
        # logger.debug("Checking Vertical Gate Spacing ....")
        for layer1Polygon, layer2Polygon in zip(self.layerMap[layer1].polygons, self.layerMap[layer2].polygons):
            if layer2Polygon.datatype == 0 and layer1Polygon.datatype == 0:
                l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                distance = 0
                if not max(l1Bounds[1], l2Bounds[1]) <= min(l1Bounds[3], l2Bounds[3]):
                    nearest_pair, distance = self.find_nearest_coordinate([l1Bounds[1],l1Bounds[3]],[l2Bounds[1],l2Bounds[3]])
                if distance != 0 and distance < val:
                    logger.debug(f"Failed for layer : {layer2}")
                    return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True   
    
    def checkVerticalInterconnectSpacing(self, layer1, layer2, val):
        # logger.debug("Checking Vertical Interconnect Spacing ....")
        for layer1Polygon, layer2Polygon in zip(self.layerMap[layer1].polygons, self.layerMap[layer2].polygons):
            if layer2Polygon.datatype == 0 and layer1Polygon.datatype == 0:
                l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                distance = 0
                if not max(l1Bounds[1], l2Bounds[1]) <= min(l1Bounds[3], l2Bounds[3]):
                    nearest_pair, distance = self.find_nearest_coordinate([l1Bounds[1],l1Bounds[3]],[l2Bounds[1],l2Bounds[3]])
                if distance != 0 and distance < val:
                    logger.debug(f"Failed for layer : {layer2}")
                    return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True
    
    def checkVerticalNanosheetSpacing(self, layer1, layer2, val):
        # logger.debug("Checking Vertical Nanosheet Spacing ....")
        for layer1Polygon in self.layerMap[layer1].polygons:
            for layer2Polygon in self.layerMap[layer2].polygons:
                if layer2Polygon.datatype == 0 and layer1Polygon.datatype == 0:
                    l1Bounds, l2Bounds = layer1Polygon.point.bounds, layer2Polygon.point.bounds
                    nearest_pair, distance = self.find_nearest_coordinate([l1Bounds[1],l1Bounds[3]],[l2Bounds[1],l2Bounds[3]])
                    if distance != val:
                        logger.debug(f"Failed for layer : {layer2}")
                        return False
        # logger.debug(f"Passed for layer : {layer2}")
        return True
    
    def checkViaEnclosure(self, viaLayer, top_layers, bottom_layers):
        if viaLayer == 0:
            return True
        # logger.debug(f'Checking if via {viaLayer} is bounded by layers {bottom_layers} and {top_layers}')
        via_list = self.layerMap[viaLayer].polygons
        layer1_polygons = []
        for layer in bottom_layers:
            layer1_polygons.extend(self.layerMap[layer].polygons)
        layer2_polygons = []
        for layer in top_layers:
            layer2_polygons.extend(self.layerMap[layer].polygons)
        for via in via_list:
            via_center_x = (via.point.bounds[0] + via.point.bounds[2]) // 2
            via_center_y = (via.point.bounds[1] + via.point.bounds[3]) // 2
            via_center = Point(via_center_x, via_center_y)
            if not any(p.point.contains(via_center) for p in layer1_polygons):
                logger.debug(f"Fail: via not enclosed by layer {bottom_layers}")
                return False
            if not any(p.point.contains(via_center) for p in layer2_polygons):
                logger.debug(f"Fail: via not enclosed by layer {top_layers}")
                return False
        return True

    @abstractmethod
    def checkDRC(self,update=False,map={}):
        return False
    
