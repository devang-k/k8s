import sys
from argparse import ArgumentParser
from contextlib import redirect_stdout
from os import listdir, devnull
from os.path import join, isfile, abspath, dirname
from shutil import rmtree
from pathlib import Path
from fixtures.tech.default import tech_dic
sys.path.append(abspath(join(dirname(__file__), '..')))
from stdcell_generation.processPermutations import main as process_permutations_main
from pnr_permutations.generate_permutations import main as pnr_main

def count_gds(dir_path):
    return len([name for name in listdir(f'{dir_path}/') if isfile(join(f'{dir_path}/', name)) and name.endswith('.gds')])

def get_output_dir(routing_tracks, technology, routing_type):
    if routing_tracks < 0:
        return False
    if technology not in ['gaa', 'cfet', 'finfet']:
        return False
    if routing_type not in ['m0', 'm01']:
        return False
    return f'golden_data/{routing_tracks}RT_{technology.upper()}_{routing_type.upper()}'

def prepare_tech(args):
    tech = tech_dic
    tech['technology'] = args.technology
    tech['number_of_routing_tracks'] = args.routing_tracks
    tech['m0_pitch'] = 25 if args.technology == 'cfet' else 30
    if args.routing == 'm01':
        tech['routing_capability'] = 'Two Metal Solution'
        tech['vertical_metal_pitch'] = tech['m0_pitch']
    elif args.routing == 'm0':
        tech['routing_capability'] = 'Single Metal Solution'
    return tech

def generate_layouts(cell, tech, netlist, dir_path):
    output_dir = f'{dir_path}/{cell}/{cell}_layouts/'
    args = {
        'tech': tech,
        'netlist': netlist,
        'output_dir': output_dir,
        'cell' : cell,
        "signal_router" : 'dijkstra',
        "debug_routing_graph": False,
        "debug_smt_solver": False,
        "placement_file": None,
        "log": None,
        "quiet": True
    }
    with open(devnull,'w') as f:
        with redirect_stdout(f):
            process_permutations_main(args)
    print(f'Number of GDS files produced: {count_gds(output_dir)}')

def generate_permutations(cell, dir_path, tech, netlist):
    output_dir = f'{dir_path}/{cell}/{cell}_permutations/'
    args = {
        'tech': tech,
        'netlist': netlist,
        'cell' : cell,
        "gds_file": f'{dir_path}/{cell}/{cell}_layouts/', 
        "output_dir": output_dir,
        "limiter" : None, 
        "debugger" : False,
        "flow_type": 'gds'
    }
    with open(devnull,'w') as f:
        with redirect_stdout(f):
            pnr_main(args)
    print(f'Number of GDS files produced: {count_gds(output_dir)}')

def main():
    netlist = './fixtures/netlist/all_cells.spice'
    cells = ['INVD4', 'AOI21X1', 'MUX21X1']
    routing_tracks = args.routing_tracks
    technology = args.technology
    routing = args.routing
    dir_name = get_output_dir(routing_tracks, technology, routing)
    assert dir_name, 'Invalid command line parameters'
    tech = prepare_tech(args)
    cell_path = Path(dir_name)
    if cell_path.exists():
        rmtree(cell_path)
    for cell in cells:
        print(f'{cell}: Generating layouts')
        generate_layouts(cell, tech, netlist, dir_name)
        print(f'{cell}: Generating permutations')
        generate_permutations(cell, dir_name, tech, netlist)

if __name__ == "__main__":
    parser = ArgumentParser(description="Collect routing information")
    parser.add_argument('-rt', type=int, default=6, dest='routing_tracks', help='Number of routing tracks')
    parser.add_argument('-t', type=str, default='cfet', dest='technology', help='Technology name')
    parser.add_argument('-r', type=str, default='m0', dest='routing', help='Routing type')
    args = parser.parse_args()
    main()