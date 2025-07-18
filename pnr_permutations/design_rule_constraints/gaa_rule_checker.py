from pnr_permutations.design_rule_constraints.checker import RuleChecker
import logging
logger = logging.getLogger('sivista_app')


class GAADesignRuleCheck(RuleChecker):
    def checkDRC(self, strict=True, update=False):
        if not self.checkWidth(update):
            return False
        if not self.checkconnections():
            return False
        if not self.checkLayerLayerExtension(self.layerNumber['M0'],[self.layerNumber['PMOSInterconnect'], self.layerNumber['NMOSInterconnect'],self.layerNumber['NMOSGate'], self.layerNumber['PMOSGate'] ],self.layer_properties.InterconnectExtensionfromM0):
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
