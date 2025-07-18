import unittest
import subprocess
import sys
from os import listdir
from os.path import join, isfile, exists, isdir, abspath, dirname
from shutil import rmtree
sys.path.append(abspath(join(dirname(__file__), '..')))
from stdcell_generation.processPermutations import main as process_permutations_main
import pya
from test_utils import compare_gds
import json
import os

class TestLayouts(unittest.TestCase):

    def setUp(self):
        """ Set up test environment, create layouts for INVD4, MUX21X1, and AOI21X1 """
        self.netlist_path = './fixtures/netlist/all_cells.spice'
        self.cells_to_test =  ['INVD4','AOI21X1','MUX21X1']
        self.tech_path = './fixtures/tech/cfet.tech'
        self.iterations = 5
        self.golden_data_path = './golden_data/generate_layout'
        self.args = {
            'netlist': self.netlist_path,
            'output_dir': '',
            'cell': '',
            "signal_router": 'dijkstra',
            "tech": self.tech_path,
            "debug_routing_graph": False,
            "debug_smt_solver": False,
            "placement_file": None,
            "log": None,
            "quiet": True,
        }
        
        # Generate layouts
        for cell in self.cells_to_test:
            for iter in range(self.iterations):
                self.args['cell'] = cell
                self.args['output_dir'] = f'{cell}/{iter}/{cell}_layouts/'
                process_permutations_main(self.args)

    def test_layouts(self):
        """ Test if the layouts match the golden data """
        errors = []  # To collect any comparison errors
        file_combos = []  # To store tuples of (golden file, generated file)
        for cell in self.cells_to_test:
            golden_layouts = [name for name in listdir(f'{self.golden_data_path}/{cell}/{cell}_layouts/') 
                              if isfile(join(f'{self.golden_data_path}/{cell}/{cell}_layouts/', name)) 
                              and name.endswith('.gds')]
            print(f"count golden layouts {len(golden_layouts)}")
            
            for iter in range(self.iterations):
                generated_layouts = [name for name in listdir(f'{cell}/{iter}/{cell}_layouts/') 
                                     if isfile(join(f'{cell}/{iter}/{cell}_layouts/', name)) 
                                     and name.endswith('.gds')]
                print(f"count generated layouts {len(generated_layouts)}")
                # Ensure that layouts were generated
                self.assertTrue(len(generated_layouts)>0, f'No layouts were generated for {cell} in iteration {iter}.')
                
                # Ensure the number of layouts match the golden data
                self.assertCountEqual(generated_layouts, golden_layouts, 
                                      f'Number of layouts generated for {cell} in iteration {iter} does not match with the golden data.')
                
                # Compare each generated layout with its golden version
                for file in golden_layouts:
                    generated_file = join(f'{cell}/{iter}/{cell}_layouts/', file)
                    golden_file = join(f'{self.golden_data_path}/{cell}/{cell}_layouts/', file)
                    try:
                        # Check if the generated file exists
                        self.assertTrue(isfile(generated_file), f'{generated_file} is not present.')
                        
                        # Compare GDS files and collect mismatch errors
                        if not compare_gds(golden_file, generated_file):
                            errors.append(f'Mismatch in GDS files:\n  Golden file: {golden_file}\n  Generated file: {generated_file}')
                    except AssertionError as e:
                        # Capture errors and continue checking other files
                        errors.append(f"Error with file: {generated_file}\n  Error: {str(e)}")

        # If there are any errors, report them all at the end
        if errors:
            # Join the errors into one string and raise the failure after all checks
            self.fail(f"Errors found in the following comparisons:\n" + "\n".join(errors))

if __name__ == '__main__':
    unittest.main()

