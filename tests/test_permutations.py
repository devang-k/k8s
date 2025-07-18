import unittest
import sys
import pya
import random
import logging
from contextlib import redirect_stdout
from datetime import datetime
from os import listdir, devnull, makedirs, getcwd, system
from os.path import join, isfile, exists, isdir, abspath, dirname
from shutil import rmtree
from pdf_writer import PDFWriter
sys.path.append(abspath(join(dirname(__file__), '..')))
random.seed(43)
from stdcell_generation.processPermutationsNew import main as process_permutations_main
from pnr_permutations.generate_permutations import main as pnr_main
from utils.config import klayout_configs
from utils.logging_config import setup_logging

logger = logging.getLogger('sivista_app')
log_file = ".test_automate"

class TestPermutations(unittest.TestCase):

    def setUp(self):
        """ Set up test environment, create layouts for INVD4, MUX21X1 and AOI21X1. """
        setup_logging(log_file)
        self.netlist_path = './fixtures/netlist/all_cells.spice'
        self.cells_to_test = ['INVD4', 'AOI21X1', 'MUX21X1']
        self.tech_path = './fixtures/tech/cfet.tech'
        self.iterations = 5
        self.error_cells = set()
        self.counter = 0
        self.pdf_writer = PDFWriter(title="Permutation test", path="test_permutations.pdf", date=datetime.now().strftime("%Y-%m-%d"))
        self.pdf_writer.append("text", f"The following cells were tested in this test: {', '.join(self.cells_to_test)}")
        makedirs('wrong_cells', exist_ok=True)
        args = {
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
        print('GENERATING INITIAL LAYOUTS')
        for cell in self.cells_to_test:
            for iter in range(self.iterations):
                args['cell'] = cell
                args['output_dir'] = f'{cell}/{iter}/{cell}_layouts/'
                print(f'ITERATION {iter}: Genrating layouts for {cell}')
                with open(devnull,'w') as f:
                    with redirect_stdout(f):
                        process_permutations_main(args)

    def gds_xor(self, layout1, layout2, output_file):
        layer_to_check = [(104, 0), (105, 0), (100, 0), (101, 0), (102, 0), (122, 0), (121, 0), (103, 0), (106, 0), (107, 0), (111, 0), (111, 0), (123, 0), (108, 0), (109, 0), (300, 0),(300, 1),(300, 2),(300, 3), (1, 0), (110, 0), (200, 0), (200, 1),(200, 2), (200, 3), (202, 0),(202, 1), (220,0),  (221,0),  (201, 0)]
        new_layout = pya.Layout()
        new_layout.create_cell("TOP_CELL")
        new_layout.dbu = layout1.dbu
        dss = pya.DeepShapeStore()
        def region1(layer,datatype):
            return pya.Region(layout1.top_cell().begin_shapes_rec(layout1.layer(layer, datatype)), dss)
        def region2(layer,datatype):
            return pya.Region(layout2.top_cell().begin_shapes_rec(layout2.layer(layer, datatype)), dss)
        for li in layer_to_check:
            l,d = li
            r1 = layout1.top_cell().shapes(layout1.layer(l, d))
            r2 = layout2.top_cell().shapes(layout2.layer(l, d))
            text_elements = {}
            for shape in r1:
                if shape.is_text():
                    x, y, s = shape.text.position().x, shape.text.position().y, shape.text.string
                    text_elements[f'{x}_{y}_{s}'] = shape
            for shape in r2:
                if shape.is_text():
                    x, y, s = shape.text.position().x, shape.text.position().y, shape.text.string
                    st = f'{x}_{y}_{s}'
                    if st in text_elements:
                        del text_elements[st]
                    else:
                        text_elements[st] = shape
            for val in text_elements.values():
                new_layout.top_cell().shapes(new_layout.layer(l, d)).insert(val)
            new_layout.top_cell().shapes(new_layout.layer(l, d)).insert(region1(l,d)^region2(l,d))
        new_layout.write(output_file)
        layout1.write(output_file.replace('_diff.gds', '_orig.gds'))
        layout2.write(output_file.replace('_diff.gds', '_generated.gds'))
        return

    def compare_gds(self, file1, file2, file_name):
        diff = pya.LayoutDiff()

        # Load the layouts
        layout1 = pya.Layout()
        layout1.read(file1)
        
        layout2 = pya.Layout()
        layout2.read(file2)
        
        # Check if the layouts are identical
        diff = diff.compare(layout1, layout2)
        if not diff:
            self.gds_xor(layout1, layout2, f'wrong_cells/{file_name}_diff.gds')
            self.counter += 1
        return diff

    def test_permutations(self):
        """ Test if the permutations are generated for each cell """
        args = {
            "gds_file": '',
            "output_dir": '',
            'netlist': self.netlist_path,
            "limiter": None,
            "debugger": False,
            "flow_type": 'gds',
            "tech": self.tech_path,
            'cell': None
        }
        for cell in self.cells_to_test:
            # Initial layouts get generated self.iterations times
            golden_layouts = [name for name in listdir(f'golden_data/6RT_CFET_M0/{cell}/{cell}_layouts/') if isfile(join(f'golden_data/6RT_CFET_M0/{cell}/{cell}_layouts/', name)) and name.endswith('.gds')]
            golden_permutations = [name for name in listdir(f'golden_data/6RT_CFET_M0/{cell}/{cell}_permutations/') if isfile(join(f'golden_data/6RT_CFET_M0/{cell}/{cell}_permutations/', name)) and name.endswith('.gds')]
            for iter in range(self.iterations):
                correctly_generated = True
                layout_files = [name for name in listdir(f'{cell}/{iter}/{cell}_layouts/') if isfile(join(f'{cell}/{iter}/{cell}_layouts/', name)) and name.endswith('.gds')]
                correctly_generated = len(layout_files) > 0
                if not correctly_generated: print(f'ITERATION {iter}: No layouts were generated for {cell} in iteration {iter}.')
                correctly_generated = len(layout_files) == len(golden_layouts)
                if not correctly_generated: print(f'ITERATION {iter}: Number of layouts generated for {cell} in iteration {iter} does not match with the golden data.')
                if not correctly_generated:
                    self.error_cells.add((cell, iter))
                    continue
                for file in golden_layouts:
                    #print(f'ITERATION {iter}: Comparing golden_data/6RT_CFET_M0/{cell}/{cell}_layouts/{file} and {cell}/{iter}/{cell}_layouts/{file}')
                    if not isfile(join(f'{cell}/{iter}/{cell}_layouts/', file)):
                        #print(f'ITERATION {iter}: {cell}/{iter}/{cell}_layouts/{file} is not present.')
                        self.error_cells.add((cell, iter))
                        correctly_generated = False
                    if not self.compare_gds(join(f'golden_data/6RT_CFET_M0/{cell}/{cell}_layouts/', file), join(f'{cell}/{iter}/{cell}_layouts/', file), file.replace('.gds', '')):
                        print(f'Mismatch in GDS files: {cell}/{iter}/{cell}_layouts/{file}')
                        self.error_cells.add((cell, iter))
                        correctly_generated = False
            
            wrong_layouts = set([i[0] for i in self.error_cells])
            if cell in wrong_layouts:
                print(f'NOT CHECKING PERMUTATIONS FOR {cell} SINCE THE INITIAL LAYOUTS ARE INCORRECT')
                continue
            # Permutations get generated just once
            print(f'GENERATING PERMUTATIONS FOR {cell}:')
            args['cell'] = cell
            args['gds_file'] = f'{cell}/0/{cell}_layouts/'
            args['output_dir'] = f'{cell}/0/{cell}_permutations'
            with open(devnull,'w') as f:
                with redirect_stdout(f):
                    pnr_main(args)
            correctly_generated = True
            permutations = [name for name in listdir(f'{cell}/0/{cell}_permutations/') if isfile(join(f'{cell}/0/{cell}_permutations/', name)) and name.endswith('.gds')]
            correctly_generated = len(permutations)>0
            if not correctly_generated: print(f'No permutations were generated for {cell}.')
            correctly_generated = len(permutations) == len(golden_permutations)
            if not correctly_generated: print(f'Number of permutations generated for {cell} does not match with the golden data.')
            if not correctly_generated:
                continue
            for file in golden_permutations:
                #print(f'Comparing golden_data/6RT_CFET_M0/{cell}/{cell}_permutations/{file} and {cell}/0/{cell}_permutations/{file}')
                if not isfile(join(f'{cell}/0/{cell}_permutations/', file)):
                    #print(f'{cell}/0/{cell}_permutations/{file} is not present.')
                    self.error_cells.add((cell, iter))
                    correctly_generated = False
                if not self.compare_gds(join(f'golden_data/6RT_CFET_M0/{cell}/{cell}_permutations/', file), join(f'{cell}/0/{cell}_permutations/', file), file.replace('.gds', '')):
                    print(f'Mismatch in GDS files: {cell}/0/{cell}_permutations/{file}')
                    self.error_cells.add((cell, iter))
                    correctly_generated = False
            
            if correctly_generated: print(f'{cell} HAS PASSED THE TEST!')

        self.assertFalse(len(self.error_cells), "Some errors occured,")
                
    def tearDown(self):
        """ Delete the cell folders after running the test """
        wrong_cells = set([i[0] for i in self.error_cells])
        # Delete the folders of all the cells that passed the tests
        for cell in self.cells_to_test:
            if exists(f'{cell}/') and isdir(f'{cell}/'): #  and cell not in wrong_cells:
                rmtree(f'{cell}/')
        # Keep cell folders for failing iterations
        # for cell in wrong_cells:
        #     for iter in range(self.iterations):
        #         if exists(f'{cell}/{iter}/') and isdir(f'{cell}/{iter}/') and cell not in wrong_cells:
        #             rmtree(f'{cell}/{iter}/')
        self.pdf_writer.append("text", f"The following cells had errors: {', '.join(wrong_cells)}")
        cwd = getcwd()
        system(f"'{klayout_configs['path']}' -z -r {cwd}/../utils/thumbnail/thumbnail.py -rd layer_properties='{cwd}/../{klayout_configs['layerproperties']}' -rd gds_folder='wrong_cells/'")
        mismatched_images = [name for name in listdir('wrong_cells/') if isfile(join('wrong_cells/', name)) and name.endswith('.png')]
        mismatched_images = list({'_'.join(name.split('_')[:-1]) for name in mismatched_images})
        for mi in mismatched_images:
            self.pdf_writer.append("text", f"{mi}:")
            self.pdf_writer.append("images", {
                'Generated image': f'wrong_cells/{mi}_generated.png',
                'Golden data': f'wrong_cells/{mi}_orig.png',
                'Difference': f'wrong_cells/{mi}_diff.png',
            })
        self.pdf_writer.save()
        rmtree('wrong_cells/')


if __name__ == '__main__':
    unittest.main()