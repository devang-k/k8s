logger = logging.getLogger('sivista_app')

class NetlistSpiceReader(db.NetlistSpiceReaderDelegate):
    def __init__(self, width: float, length: float):
        self.width = width
        self.length = length

    def element(self, circuit: db.Circuit, element_type: str, name: str, model: str, value, nets: List[db.Net],
                params: Dict[str, float]) -> bool:
        if element_type != 'M' or len(nets) != 4:
            # All other elements are left to the standard implementation.
            return super().element(circuit, element_type, name, model, value, nets, params)
        else:
            # Provide a device class.
            cls = circuit.netlist().device_class_by_name(model)
            if not cls:
                # Create MOS3Transistor device class if it does not yet exist.
                cls = db.DeviceClassMOS3Transistor()
                cls.name = model
                circuit.netlist().add(cls)
            # Create MOS3 device.
            device: db.Device = circuit.create_device(cls, name)
            # Configure the MOS3 device.
            for terminal_name, net in zip(['D', 'G', 'S'], nets):
                device.connect_terminal(terminal_name, net)
            # Parameters in the model are given in micrometer units, so
            # we need to translate the parameter values from SI to um values.
            device.set_parameter('W', self.width * 1e-3 ) # Mapping with tech file parameters 
            device.set_parameter('L', self.length * 1e-3 ) # Mapping with tech file parameters

            return True

def netlist_comparer(extracted_netlist: db.Netlist, reference_netlist: db.Netlist) -> bool:
    extracted_netlist.simplify()
    reference_netlist.simplify()

    comparer = db.NetlistComparer()
    result = comparer.compare(extracted_netlist, reference_netlist)

    logger.debug("Netlist comparison result: %s", result)
    logger.debug("Extracted Netlist:\n%s", extracted_netlist)
    logger.debug("Reference Netlist:\n%s", reference_netlist)

    return bool(result)

def read_and_convert_netlist(
    netlist_path: str, nanosheet_width: int, poly_wire_width: int, scaling: int
) -> db.Netlist:
    logger.debug("Reading netlist from: %s", netlist_path)
    logger.debug("Conversion params - Width: %d, Length: %d, Scaling: %d", 
                 nanosheet_width, poly_wire_width, scaling)

    netlist = db.Netlist()
    spice_reader = NetlistSpiceReader(
        width=nanosheet_width, 
        length=poly_wire_width
    )
    netlist.read(netlist_path, db.NetlistSpiceReader(spice_reader))

    return netlist
