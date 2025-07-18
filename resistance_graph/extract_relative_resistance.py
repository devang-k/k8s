from resistance_graph.relative_resistance import RelativeResistance
import csv
import argparse
import pandas as pd
import logging
logger = logging.getLogger('sivista_app')
# from stdcell_generation.common.net_util import is_power_net
def is_ground_net(net: str) -> bool:
    ground_nets = {0, '0', 'gnd', 'vss', 'vgnd'}
    return net.lower() in ground_nets

def is_supply_net(net: str) -> bool:
    supply_nets = {'vcc', 'vdd', 'vpwr', 'pwr'}
    return net.lower() in supply_nets

def is_power_net(net: str) -> bool:
    return is_ground_net(net) or is_supply_net(net)
class ResistanceWriter():
    """
    This class is used to write the relative resistance to a file.
    """
    def __init__(self, relative_resistance):
        self.data = relative_resistance
    
    def write_resistance_to_csv(self, output_file, pex_file, combine_resistance,suffix):
        """
        This function writes the relative resistance to a file.
        Args:
            output_file (str): The path to the file where the relative resistance will be written.
        """
        try:
         

            logger.info(f"Combining resistance data with suffix: {suffix}")
            # Collect all unique nets
            all_nets = set()
            for net_dict in self.data.values():
                all_nets.update(net_dict.keys())

            # Read PEX predictions
            pex_df = pd.read_csv(pex_file)

            # Build resistance rows
            rows = []
            for file_name, net_dict in self.data.items():
                file_key = file_name.split('/')[-1].replace('.gds', '')  # consistent naming
                row = {"File": file_key}
                for net in sorted(all_nets):
                    if not is_power_net(net):
                        row[f"{suffix}_{net}"] = net_dict.get(net, 0)
                rows.append(row)

            # Create DataFrame and merge
            resistance_df = pd.DataFrame(rows)
            if combine_resistance:
                merged_df = pd.merge(pex_df, resistance_df, on='File', how='inner')
                merged_df.to_csv(pex_file, index=False)
                logger.info(f"Successfully merged resistance predictions into {pex_file}")
            else:
                resistance_df.to_csv(output_file, index=False)
                logger.info(f"Successfully wrote resistance predictions to {output_file}")

        except Exception as e:
            logger.error(f"Error merging resistance predictions: {str(e)}")
            raise
      

def main(args):
    gds_dir = args.get('gds_dir')
    layer_map = args.get('layer_map')
    output_file = args.get('output_file')
    pex_file = args.get('pex_file')
    combine_resistance = args.get('combine_resistance')
    relative_resistance = RelativeResistance(gds_dir, layer_map).extract_resistance()
    resistance_writer = ResistanceWriter(relative_resistance)
    resistance_writer.write_resistance_to_csv(output_file, pex_file, combine_resistance,"R_REL")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract relative resistance from GDS files')
    parser.add_argument('--gds_dir', type=str, required=True, help='Directory containing GDS files')
    parser.add_argument('--layer_map', type=str, required=True, help='Path to layer map file')
    parser.add_argument('--output_file', type=str, required=True, help='Output file path')
    parser.add_argument('--pex_file', type=str, required=True, help='PEX file path')
    parser.add_argument('--combine_resistance', type=bool, required=True, help='Combine resistance')
    args = parser.parse_args()
    args = {
        'gds_dir': args.gds_dir,
        'layer_map': args.layer_map,
        'output_file': args.output_file,
        'pex_file': args.pex_file,
        'combine_resistance': args.combine_resistance,

    }
    main(args)