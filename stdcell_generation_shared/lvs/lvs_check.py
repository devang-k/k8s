logger = logging.getLogger('sivista_app')

class LVSChecker:
    '''For running all the lvs checks'''
    def __init__(self, netlist_path, tech, technology_key, layout, cell, cell_name, layer_properties=None,):
        self.tech = tech
        self.technology_key = technology_key
        self.netlist_path = netlist_path
        self.layout = layout
        self.cell_name = cell_name
        self.cell = cell
        self.width = tech.nanosheet_width
        self.length = max(tech.layer_width['npoly'],tech.layer_width['ppoly'])
        self.layer_properties = layer_properties
        if self.layer_properties: 
            self.width = self.layer_properties.nanosheetWidth
            self.length = max(
                self.layer_properties.wireWidth["npoly"],
                self.layer_properties.wireWidth["ppoly"]
            )
        self.technology_map = {
            'cfet': cfet_netlist_extractor,
            'gaa': gaa_netlist_extractor,
            'finfet': finfet_netlist_extractor,
            'multiheight_gaa': multiheight_gaa_netlist_extractor
        }

    def run_check(self):
        '''Logic for checking LVS'''
        # Read and convert reference netlist
        reference_netlist = read_and_convert_netlist(
            self.netlist_path, self.width, self.length, self.tech.scaling_factor
        )

        # Remove all unused circuits
        circuits_to_delete = {
            c for c in reference_netlist.each_circuit() if c.name != self.cell_name
        }
        for c in circuits_to_delete:
            reference_netlist.remove(c)

        # Extract netlist from layout
        if self.technology_key == 'gaa' and self.tech.height_req >1: 
            extractor = self.technology_map.get(f'multiheight_{self.technology_key}')
        else:
            extractor = self.technology_map.get(self.technology_key)

        if extractor is None:
            raise ValueError(f"Unknown technology: {self.technology_key}")
        extracted_netlist = extractor(self.layout, self.cell)

        # Compare netlists
        lvs_success = netlist_comparer(extracted_netlist, reference_netlist)
        return  {
            "lvs_success": lvs_success,
            "extracted_netlist": extracted_netlist,
            "reference_netlist": reference_netlist
            }
