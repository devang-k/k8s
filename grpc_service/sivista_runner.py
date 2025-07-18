from os import makedirs, listdir, system, getcwd
from os.path import join, exists, abspath, isfile, relpath
from pathlib import Path
from shutil import rmtree, move
from re import findall, MULTILINE, IGNORECASE
from json import load, dumps, loads
import logging
import sys
import random
random.seed(43)
from utils.storage.s3 import S3Service
from utils.storage.local import LocalFileService
from utils.storage.gcsbucket import GCSBucketService
from utils.config import klayout_configs, storage_type, model_paths, shared_memory

from stdcell_generation_client.processPermutationsNew import main as process_permutations_main
from pnr_permutations.generate_permutations import main as pnr_main
from pnr_permutations.double_height_permutations import main as double_height_pnr_main
from metrics_calculation.calculate_metrics import main as metrics_main
from pex_extraction.dtco_ml_predict import main as pex_predict_main
from genetic_algorithm.genetic_algorithms import main as gen_alg_main
from resistance_graph.inference_resistance_gnn import main as resistance_predict_main 
from resistance_graph.extract_relative_resistance import main as extract_relative_resistance_main
from utils.logging_config import log_performance

logger = logging.getLogger(__name__)
def setup_logging(log_file):
    try:
        log = logging.getLogger()  # root logger
        for hdlr in log.handlers[:]:  # remove all old handlers
            log.removeHandler(hdlr)
    except:
        print('Logger not initiated')
    logging.basicConfig(
        level=logging.DEBUG,
        filename=log_file,
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger('matplotlib.font_manager').disabled = True
log_file = ".sivista_log"
setup_logging(log_file)

def read_json_as_string(file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = load(file)
            json_string = dumps(json_data)
            return json_string
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None

class SiVistaRunner:
    def __init__(self, data):
        self.cell_name = data.get('cell', 'INVALID')
        self.netlist_path = data.get('netlist_data', None)
        self.job_id = data.get('job_id', '0')
        self.shared_memory = data.get('shared_memory', shared_memory)
        self.selected_gds_path = data.get('gds_folder_path', None)
        self.pdk = data.get('pdk', 'monCFET')
        self.tech_data = data.get('tech_data', {})
        self.type = data.get('type','0')
        self.layouts_folder = self.shared_memory + data.get('layouts_folder', f'{self.job_id}/{self.cell_name}/{self.cell_name}_layouts')
        self.permutations_folder = self.shared_memory + data.get('permutations_folder', f'{self.job_id}/{self.cell_name}/{self.cell_name}_permutations')
        self.metrics_folder = self.shared_memory + data.get('metrics_folder', f'{self.job_id}/{self.cell_name}/{self.cell_name}_metrics')
        self.pex_folder = self.shared_memory + data.get('predictions_folder', f'{self.job_id}/{self.cell_name}/{self.cell_name}_predictions')
        self.resistance_folder = data.get('resistance_folder', f'{self.pex_folder}/resistance_predictions')
        self.folder_info = {
            'layouts': None,
            'permutations': None,
            'metrics': None,
            'pex': None,
            'resistance': None
        }
        self.proceed = True
        if storage_type == 's3':
            self.storage_servicer = S3Service()
        elif storage_type == 'local':
            self.storage_servicer = LocalFileService()
        elif storage_type == 'gcs':
            self.storage_servicer = GCSBucketService()
        self.status = ''
        self.message = ''
        self.project_name = data.get('project_name', None)
        self.project_id = data.get('project_id', None)
        self.user_id = data.get('user_id', None)

    def set_status_message(self, status, message):
        self.status = status
        self.message = f'{self.cell_name}: {message}'
        self.proceed = status == '200'


    def run_layouts(self):
        if not self.proceed: return
        args = {
            'netlist': abspath(self.netlist_path),
            'output_dir': abspath(f'{self.layouts_folder}/') + '/',
            'cell': self.cell_name,
            "placer": 'base0',
            "signal_router": 'dijkstra',
            "tech": self.tech_data,
            "debug_routing_graph": False,
            "debug_smt_solver": False,
            "placement_file": None,
            "log": None,
            "quiet": True,
            "height_req": 1
        }
        counts = process_permutations_main(args)
        counts = loads(counts) if type(counts) == str else counts
        if not self.validate_layouts():
            self.set_status_message('400', 'Layout files were not created.')
        else:
            self.folder_info['layouts'] = abspath(f'{self.layouts_folder}/')
            self.set_status_message('200', f'{counts["generated"]} Layout files generated. (DRC fails: {counts["drc_failures"]}, LVS fails: {counts["lvs_failures"]})')

    @log_performance(service_name="SiVista")
    def run_permutations(self, flow1=False, double_height=False):
        if not self.proceed: return
        args = {
            "gds_file": f'{self.layouts_folder}/', 
            "output_dir": self.permutations_folder,
            "cell": self.cell_name,
            "netlist": self.netlist_path,
            "tech": self.tech_data,
            "limiter": None,
            "debugger": False,
            "flow_type": 'gds',
            "onlyOne": flow1
        }
        if not double_height:
            counts = pnr_main(args)
        else:
            counts = double_height_pnr_main(args)
        if not self.validate_permutations():
            self.set_status_message('400', 'Some DRC rules failed.')
        else:
            self.folder_info['permutations'] = abspath(f'{self.permutations_folder}/')
            if flow1:
                message = 'GDS files have been optimized successfully.'
            else:
                message = f'Number of DRC clean permutations generated: {counts["drc"]}\n Number of LVS clean permutations: {counts["lvs"]} for {self.cell_name}.'
            self.set_status_message('200', message)

    def run_metrics(self, flow2=False):
        if not self.proceed: return
        args = {
            "input_path": self.permutations_folder,
            "layermap_path": self.layouts_folder,
            "output_dir": self.metrics_folder,
            "cell": self.cell_name,
            "tech": self.tech_data,
            "flow_type": 'gds'
        }
        metrics_main(args)
        if not self.validate_metrics():
            self.set_status_message('400', 'Failed to calculate metrics.')
        else:
            self.folder_info['metrics'] = abspath(f'{self.metrics_folder}/')
            self.set_status_message('200', 'Metrics calculated successfully.')

    def run_pex(self):
        if not self.proceed: return
        makedirs(self.pex_folder, exist_ok=True)
        metrics_file = f'{self.metrics_folder}/{self.cell_name}_metrics.csv'
        args = {
            "input_path": metrics_file,
            "output": f'{self.pex_folder}/{self.cell_name}_GDS_PEX_PREDICTION_ML.csv',
            "model":"gnn",
            "tech": self.tech_data,
            "data_results_format": "individual-net",
        }
        pex_predict_main(args)
        
        resistance_args = {
                    "metrics_file": metrics_file,
                    "gds_dir":self.permutations_folder,  # Pass directory instead of individual files
                    "cell_name": self.cell_name,
                    "model_path": model_paths["gnn"]["cfet"]["resistance_predictor_path"],
                    "norm_path": model_paths["gnn"]["cfet"]["resistance_norm_params"],
                    "tech_file": self.tech_data,
                    "silent": True,
                    "layer_map_dir": self.layouts_folder,
                    "output_dir": self.resistance_folder,
                    "pex_file": f'{self.pex_folder}/{self.cell_name}_GDS_PEX_PREDICTION_ML.csv',
                    "combine_resistance": True,
                     "output_file": f'{self.pex_folder}/{self.cell_name}_predicted_equivalent_resistance.csv',
                }
        resistance_predict_main(resistance_args)
        if not self.validate_pex():
            self.set_status_message('400', 'Prediction of Parasitics failed.')
        else:
            self.folder_info['pex'] = abspath(f'{self.pex_folder}/')
            self.set_status_message('200', 'Parasitics extracted successfully.')
        if not self.validate_resistance():
            self.set_status_message('400', f'Prediction of resistance at path {self.resistance_folder} failed.')
        else:
            self.folder_info['resistance'] = abspath(f'{self.resistance_folder}/')
            self.set_status_message('200', 'Capacitance and Resistance parasitics extracted successfully.')


    def run_extract_relative_resistance(self):
        if not self.proceed: return
        args = {
            "gds_dir": self.permutations_folder,
            "layer_map": self.layouts_folder,
            "output_file": f'{self.pex_folder}/{self.cell_name}_relative_resistance.csv',
            "pex_file": f'{self.pex_folder}/{self.cell_name}_GDS_PEX_PREDICTION_ML.csv',
            "combine_resistance": False
        }
        extract_relative_resistance_main(args)
        if not self.validate_pex():
            self.set_status_message('400', 'Prediction of Parasitics failed.')
        else:
            self.folder_info['pex'] = abspath(f'{self.pex_folder}/')
            self.set_status_message('200', 'Relative Resistance extracted successfully.')
        #self.folder_info['resistance'] = abspath(f'{self.resistance_folder}/')

    def run_genetic_algorithm(self):
        args = {
             "cell" : self.cell_name,
             "tech":self.tech_data,
             'netlist': self.netlist_path,
             'output_folder':f'{self.layouts_folder}/',
             "model_type" : "gnn",
             "pdk" : "monCFET",
             "pop_size" : 10,
             "max_generations" : 10,
             "elite_size" :2,
             "mutation_rate" : 0.1,
             "convergence_threshold" : 1e-2,
             "convergence_generations" : 5,
             "min_gene_value" : 0,
             "max_gene_value" : 5
        } 
        gen_alg_main(args)
        self.folder_info['layouts'] = abspath(f'{self.layouts_folder}/')
        self.folder_info['metrics'] = abspath(f'{self.metrics_folder}/')
        self.folder_info['pex'] = abspath(f'{self.pex_folder}/')
        self.set_status_message('200', 'Genetic algorithm POC run complete.')

    def run_large_transistor_poc(self):
        if not self.proceed: return
        # if not self.type == '2':
        #     self.set_status_message('400', f'Incorrect parameter for multi-height cell POC.')
        #     return 
        args = {
            'netlist': self.netlist_path,
            'output_dir': f'{self.layouts_folder}/',
            'cell': self.cell_name,
            "placer": 'base0',
            "signal_router": 'dijkstra',
            "tech": self.tech_data,
            "debug_routing_graph": False,
            "debug_smt_solver": False,
            "placement_file": None,
            "log": None,
            "quiet": True,
            'height_req': 2
        }
        counts = process_permutations_main(args)
        counts = loads(counts)
        # make_dummy_metrics(self.layouts_folder, self.cell_name)
        if not self.validate_layouts():
            self.set_status_message('400', 'Layout files were not created.')
        else:
            self.folder_info['layouts'] = abspath(f'{self.layouts_folder}/')
            self.folder_info['metrics'] = abspath(f'{self.metrics_folder}/')
            self.folder_info['pex'] = abspath(f'{self.pex_folder}/')
            self.set_status_message('200', f'{counts["generated"]} Layout files generated. (DRC fails: {counts["drc_failures"]}, LVS fails: {counts["lvs_failures"]})')

    def validate_cell_name(self):
        self.all_cells = findall(r'^\.subckt\s+(\S+)', self.netlist_path, MULTILINE | IGNORECASE)
        return self.cell_name in self.all_cells

    def validate_layouts(self):
        return [name for name in listdir(f'{self.layouts_folder}/') if isfile(join(f'{self.layouts_folder}/', name)) and name.endswith('.gds')]

    def validate_permutations(self):
        return [name for name in listdir(f'{self.permutations_folder}/') if isfile(join(f'{self.permutations_folder}/', name)) and name.endswith('.gds')]

    def validate_metrics(self):
        return exists(f'{self.metrics_folder}/{self.cell_name}_metrics.csv')

    def validate_pex(self):
        return exists(f'{self.pex_folder}/{self.cell_name}_GDS_PEX_PREDICTION_ML.csv')
    
    def validate_resistance(self):
        return [name for name in listdir(f'{self.resistance_folder}/') if isfile(join(f'{self.resistance_folder}/', name)) and name.endswith('.log')]
    
    def genetic_algo_flow_prep(self):
        if not self.type == '1':
            self.set_status_message('400', f'Incorrect parameter for genetic algorithm POC.')
            return 
        if not self.tech_data:
            self.set_status_message('400', 'Missing technology file.')
            return
        if not self.cell_name:
            self.set_status_message('400', 'Cell name missing.')
        if not self.validate_cell_name():
            self.set_status_message('400', 'Invalid cell name.')
            return
        cell_path = Path(f'{self.job_id}/{self.cell_name}')
        if cell_path.exists():
            rmtree(cell_path)
        cell_path.mkdir(parents=True, exist_ok=True)
        netlist_filename = 'netlist.spice'
        with open(f'{self.job_id}/{self.cell_name}/{netlist_filename}', 'w') as file:
            file.write(self.netlist_path)
        if isfile(f'{self.job_id}/{self.cell_name}/{netlist_filename}'):
            self.netlist_path = f'{self.job_id}/{self.cell_name}/{netlist_filename}'
            setup_logging(f"{self.job_id}/{self.cell_name}/sivista.log")
            self.set_status_message('200', f'Collected resources for genetic algorithm POC (job id {self.job_id}).')
        else:
            self.set_status_message('400', 'Failed to load netlist file.')

    def layout_flow_prep(self):
        if not self.tech_data or not self.netlist_path:
            self.set_status_message('400', 'Missing technology file or netlist file or both.')
            return
        if not self.validate_cell_name():
            self.set_status_message('400', 'Invalid cell name.')
            return
        cell_path = Path(self.shared_memory + f'{self.job_id}/{self.cell_name}')
        if cell_path.exists():
            rmtree(cell_path)
        cell_path.mkdir(parents=True, exist_ok=True)
        netlist_filename = 'netlist.spice'
        with open(self.shared_memory + f'{self.job_id}/{self.cell_name}/{netlist_filename}', 'w') as file:
            file.write(self.netlist_path)
        if isfile(self.shared_memory + f'{self.job_id}/{self.cell_name}/{netlist_filename}'):
            self.netlist_path = self.shared_memory + f'{self.job_id}/{self.cell_name}/{netlist_filename}'
            setup_logging(self.shared_memory + f"{self.job_id}/{self.cell_name}/sivista.log")
            self.set_status_message('200', f'Collected resources for cell layout generation (job id {self.job_id}).')
        else:
            self.set_status_message('400', 'Failed to load netlist file.')

    def hyperexpressivity_flow_prep(self, s3_gds_path):
        cell_path = f'{self.job_id}/{self.cell_name}'
        if not self.tech_data or not self.netlist_path:
            self.set_status_message('400', 'Missing technology file or netlist file or both.')
            return
        if not self.selected_gds_path:
            self.set_status_message('400', 'No GDS files selected.')
            return
        self.move_s3_to_local(s3_gds_path, self.selected_gds_path)
        self.layouts_folder = self.selected_gds_path
        netlist_filename = 'netlist.spice'
        with open(f'{cell_path}/{netlist_filename}', 'w') as file:
            file.write(self.netlist_path)
        if isfile(f'{cell_path}/{netlist_filename}'):
            self.netlist_path = f'{cell_path}/{netlist_filename}'
            setup_logging(f"{cell_path}/sivista.log")
            self.set_status_message('200', f'Collected resources for cell layout generation (job id {self.job_id}).')
        else:
            self.set_status_message('400', 'Failed to load netlist file.')
    
    def move_thumbnails(self, source_folder, destination_folder):
        for file_name in listdir(source_folder):
            if file_name.endswith(".png"):
                source_path = join(source_folder, file_name)
                destination_path = join(destination_folder, file_name)
                move(source_path, destination_path)
    
    def save_log_file(self, s3_key):
        cell_path = Path(self.shared_memory + f'{self.job_id}/{self.cell_name}')
        s3_key += f'Logs/{self.job_id}_{self.cell_name}.log'
        if self.storage_servicer.upload_file(self.shared_memory + f"{self.job_id}/{self.cell_name}/sivista.log", s3_key):
            self.set_status_message('200', 'Log file uploaded to remote repository.')
        else:
            self.set_status_message('400', 'Failed to upload log file.')
        rmtree(cell_path)
        if not listdir(Path(self.shared_memory + self.job_id)):
            rmtree(Path(self.shared_memory + self.job_id))

    def get_folder_paths_for_s3(self):
        paths = {
            'layouts': relpath(f'{self.layouts_folder}/', self.shared_memory),
            'permutations': relpath(f'{self.permutations_folder}/', self.shared_memory),
            'metrics': relpath(f'{self.metrics_folder}/', self.shared_memory),
            'pex': relpath(f'{self.pex_folder}/', self.shared_memory),
            'resistance':relpath(f'{self.resistance_folder}/', self.shared_memory)
        }
        return {k: '/'.join(v.split('/')[1:]) for k, v in paths.items()}

    def move_local_to_s3(self, s3_prefix):
        cell_path = Path(self.shared_memory + f'{self.job_id}/{self.cell_name}')
        if not cell_path.exists():
            self.set_status_message('400', f'Couldn\'t find path: {cell_path}')
            return
        s3_paths = self.get_folder_paths_for_s3()
        for key, s3_path in s3_paths.items():
            if self.folder_info[key]:
                self.storage_servicer.upload_folder(self.folder_info[key], s3_prefix + s3_path)
        self.set_status_message('200', 'Files moved to remote repository.')

    def move_s3_to_local(self, s3_path, local_path):
        try:
            self.storage_servicer.download_folder(s3_path, local_path)
            self.set_status_message('200', 'Loaded cell layout data from remote repository')
        except:
            self.set_status_message('400', 'Failed to load resources from remote repository.')

    def make_gds_thumbnails(self, folder_path):
        # Get the absolute path to a required file.
        try:
            # When running as a bundled app
            base_path = sys._MEIPASS
        except AttributeError:
            # When running as a script
            base_path = getcwd()
        
        cwd = getcwd()
        system(f"'{klayout_configs['path']}' -z -r {base_path}/utils/thumbnail/thumbnail.py -rd layer_properties='{base_path}/{klayout_configs['layerproperties']}' -rd gds_folder='{folder_path}/'")
        self.set_status_message('200', f"Thumbnails generated for {folder_path.split('/')[-1]}.")