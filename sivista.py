#!/usr/bin/env python3

import sys

try:
    # When running as a bundled app
    base_path = sys._MEIPASS

    # following paths are required to find klayout pylibs and base dependencies inside docker conatiner when code is packaged as an executable
    sys.path.insert(0,"/usr/lib/python3.10/")
    sys.path.insert(0,"/usr/local/lib/python3.10/dist-packages")
except AttributeError:
    # When running as a script
    pass

import logging
logger = logging.getLogger('sivista_app')
from utils.logging_config import setup_logging
log_file = ".sivista_log"
setup_logging(log_file)
import random
random.seed(43)
# import sys
import os
import shutil
import subprocess
import argparse
import json
from pathlib import Path
from yaspin import yaspin
from yaspin.spinners import Spinners
import datetime
import multiprocessing
import pretty_errors
import logging
import siclarity_lm.license_manager as lm
import pandas as pd
from pnr_permutations.generate_permutations import main as pnr_main
from pnr_permutations.double_height_permutations import main as multi_height_pnr_main
from metrics_calculation.calculate_metrics import main as metrics_main
from pex_extraction.dtco_ml_predict import main as pex_predict_main
from stdcell_generation_client.processPermutationsNew import main as process_permutations_main
# from stdcell_generation.multiLayout import main as multi_height_main
from resistance_graph.inference_resistance_gnn import main as resistance_predict_main
from utils.config import model_paths
from resistance_graph.extract_relative_resistance import main as extract_relative_resistance_main

# For development only
# import sys
# sys.path.append('./lib_utils')
# from lib_utils.stdcell_generation.processPermutations import main as process_permutations_main

def check_licenses(modules):
    """
    Check licenses for a list of modules.
    """
    return True
    for module_name in modules:
        if not lm.check_license(module_name):
            print(f"Invalid license for {module_name}.")
            return False
    return True

def move_and_overwrite(src, dst):
    """
    Move and overwrite a directory.
    """
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)

def get_json_string(file_path):
    # Open and load the JSON file
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    # Convert the JSON object to a string
    return json.dumps(json_data)

def parse_args():

    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="SiClarity SiVista SmartCell-Generation: Monolithic CFET"
    )
    parser.add_argument(
        "-c", "--cell", dest="cell", help="The name of the standard cell"
    )
    parser.add_argument(
        "-tech", dest="tech_path", default="tech/monCFET/monCFET.tech", help="Path for tech file"
    )
    parser.add_argument(
        "-netlist", dest="netlist_path", default="tech/monCFET/monCFET.spice", help="Path for spice file"
    )
    parser.add_argument(
        "--all-cells",
        action="store_true",
        help="Process all cells from the tech/monCFET/monCFET.spice file",
    )
    parser.add_argument(
        "-mh",
        "--multiheight",
        action="store_true",
        help="Generate multiheight layouts",
    )
    parser.add_argument(
        "-v",
        "--variations",
        action="store_true",
        help="Generate all permutations of the cell",
    )
    parser.add_argument(
        "-m", "--metrics", action="store_true", help="Calculate metrics for the cell"
    )
    parser.add_argument(
        "-p",
        "--predict-pex",
        action="store_true",
        help="Predict parasitics using machine learning",
    )
    parser.add_argument(
        "--flow_type",
        dest ="flow_type",
        choices =['db', 'gds'],
        default = "gds",
        required = False,
        help = "Select the flow type: db for database or gds for GDS file-based flow"
    )
    parser.add_argument(
        "-dp",
        "--debug-plots",
        action="store_true",
        help = "Do you want to see plots of subgraphs?"
    )
    parser.add_argument(
        "-limit",
        "--limiter",
        type=int,
        default = None,
        help = "Would you like to limit the files being generated?"
    )
    return parser.parse_args()

def get_all_cells_from_spice(spice_file):
    """
    Extracts all cell names from a spice file.
    """
    cell_names = []
    with open(spice_file, "r") as file:
        for line in file:
            if line.startswith(".subckt"):
                parts = line.split()
                if len(parts) > 1:
                    cell_names.append(parts[1])
    return cell_names

def prepare_working_directory(directory):
    """
    Prepare the working directory by clearing or creating it.
    """
    dir_path = Path(directory)
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)

def file_exists(file_path, error_message):
    """
    Check if a file exists, and exit with an error if not.
    """
    if not os.path.exists(file_path):
        print(error_message)
        sys.exit(1)

def run_command(command):
    """
    Run a shell command.
    """
    process = subprocess.run(command, shell=True)
    if process.returncode != 0:
        sys.exit(1)

def print_gds_count(cell):
    """
    Print the count of GDS files generated.
    """
    command = f"ls -1 {cell}/{cell}_permutations/*.gds | wc -l"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    # ANSI escape codes for colors and styles
    ANSI_BOLD = "\033[1m"
    ANSI_RED = "\033[31m"
    ANSI_GREEN = "\033[32m"
    ANSI_YELLOW = "\033[33m"
    ANSI_RESET = "\033[0m"  # Reset to default
    if result.returncode == 0:
        count = result.stdout.strip()
        print(f"{ANSI_BOLD}{ANSI_YELLOW}Generated {count} GDS files. {ANSI_RESET}\n")
    else:
        print(f"{ANSI_BOLD}{ANSI_RED}Error in counting .gds files{ANSI_RESET}\n")

def generate_layout(cell,args, debug_plots=False):
    logger.error("License check failed for 'generate_layout'")
    with yaspin(color="green") as spinner:
        if not check_licenses(["generate_layout"]):
            spinner.fail("?")
            print("License check failed for 'generate_layout'")
            sys.exit(1)
        spinner.ok("? License check succeeded for 'generate_layout'")
        layout_args = {
                'tech':os.path.abspath(args.tech_path),
                'netlist':os.path.abspath(args.netlist_path),
                'output_dir':os.path.abspath(f'{cell}')+'/',
                'cell' :f'{cell}',
                "placer":'base0' ,
                "signal_router" : 'dijkstra',
                "debug_routing_graph":False,
                "debug_smt_solver":False,
                "placement_file":None,
                "log":None,
                "quiet":True,
                "debug_plots": debug_plots,
                "height_req": 2 if args.multiheight else 1,
                }
        process_permutations_main(layout_args)
       
def generate_permutations(cell, flow_type,args, limiter=None):
    with yaspin(color="green") as spinner:
        if not check_licenses(["generate_permutations"]):
            spinner.fail("? License check failed for 'generate_permutations'")
            sys.exit(1)
        spinner.ok("? License check succeeded for 'generate_permutations'")
    os.makedirs(f"{cell}/{cell}_permutations", exist_ok=True)
    console_message = f"Generating permutations for {cell}..."
    with yaspin(text=console_message, color="cyan"):
        perm_args = {"gds_file":f"{cell}/", 
                'tech':os.path.abspath(args.tech_path),
                'netlist':os.path.abspath(args.netlist_path),
                'cell' :f'{cell}',
                "output_dir": f'{cell}/{cell}_permutations',
                "limiter" : limiter, 
                "debugger" : False,
                "flow_type": flow_type
                }
        if args.multiheight:
            multi_height_pnr_main(perm_args) 
        else:
            pnr_main(perm_args)       
      
def calculate_metrics(cell,args,flow_type):
    with yaspin(color="green") as spinner:
        if not check_licenses(["calculate_metrics"]):
            spinner.fail("? License check failed for 'calculate_metrics'")
            sys.exit(1)
        spinner.ok("? License check succeeded for 'calculate_metrics'")
    os.makedirs(f"{cell}/{cell}_metrics", exist_ok=True)
    console_message = f"Calculating cell metrics for {cell}..."
    with yaspin(Spinners.noise, text=console_message, color="white"):       
        metrics_args = {
        "input_path": f'{cell}/{cell}_permutations',
        "output_dir": f'{cell}/{cell}_metrics',
        "tech": os.path.abspath(args.tech_path),
        "layermap_path": f'{cell}',
        "cell": cell,
        "flow_type":flow_type
        }
       
        metrics_main(metrics_args)
    print(f"DTCO metrics for {cell} were successfully calculated.\n")


def predict_parasitics(cell, args, flow_type):
    with yaspin(color="green") as spinner:
        if not check_licenses(["predict_parasitics"]):
            spinner.fail("? License check failed for 'predict_parasitics'")
            sys.exit(1)
        spinner.ok("? License check succeeded for 'predict_parasitics'")
    
    console_message = "Predicting parasitics..."
    try:
        # Predict capacitance
        pex_file = f'{cell}/{cell}_GDS_PEX_PREDICTION_ML.csv'
        with yaspin(Spinners.noise, text="Predicting capacitance...", color="red") as spinner:
            pex_args = {
                "input_path": f'{cell}/{cell}_metrics/{cell}_metrics.csv',
                "output": pex_file,
                "model": "gnn",
                "tech": os.path.abspath(args.tech_path),
            }
            pex_predict_main(pex_args)

        # Predict resistance
        with yaspin(Spinners.noise, text="Predicting resistance...", color="red") as spinner:
            try:
                # Get nets from metrics data
                metrics_file = f"{cell}/{cell}_metrics/{cell}_metrics.csv"
                
                resistance_args = {
                    "metrics_file": metrics_file,
                    "gds_dir": f"{cell}/{cell}_permutations",
                    "cell_name": cell,
                    "model_path": model_paths["gnn"]["cfet"]["resistance_predictor_path"],
                    "norm_path": model_paths["gnn"]["cfet"]["resistance_norm_params"],
                    "tech_file": os.path.abspath(args.tech_path),
                    "layer_map_dir": f"{cell}",
                    "silent": True,
                    "output_dir": f"{cell}/{cell}_resistance_predictions",
                    "pex_file": pex_file,  # Pass the PEX file path instead
                    "combine_resistance": False,
                    "output_file": f"{cell}/{cell}_predicted_equivalent_resistance.csv"
                }
                
                # Process all layouts in directory
                resistance_predict_main(resistance_args)
                
                output_dir = f"{cell}/{cell}_resistance_predictions"
                print(f"Resistance prediction for cell: {cell} is saved in {output_dir}!")
                
            except Exception as e:
                logger.error(f"Error in resistance prediction: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error in parasitic prediction: {str(e)}")
        raise

    print(f"PEX prediction for cell: {cell} is complete!")

def extract_relative_resistance(cell,args,flow_type):
    with yaspin(color="green") as spinner:
        if not check_licenses(["extract_relative_resistance"]):
            spinner.fail("? License check failed for 'extract_relative_resistance'")
            sys.exit(1)
        spinner.ok("? License check succeeded for 'extract_relative_resistance'")
        console_message = "Extracting relative resistance..."
        try:
            with yaspin(Spinners.noise, text = console_message, color="red") as spinner:
                relative_resistance_args = {
                "gds_dir": f'{cell}/{cell}_permutations',
                "layer_map": f'{cell}',
                "output_file": f'{cell}/{cell}_relative_resistance.csv',
                "pex_file": f'{cell}/{cell}_GDS_PEX_PREDICTION_ML.csv',
                "combine_resistance": True
                }
            extract_relative_resistance_main(relative_resistance_args)
            print(f"Relative resistance for {cell} is saved at {cell}/{cell}_relative_resistance.csv")
        except Exception as e:
            print(f"Error: {e}")

        

def combine_pex_metrics(cell):
    """
    combine pex predictions and metrics together
    """ 
    file1 = f"{cell}/{cell}_metrics/{cell}_metrics.csv"
    df1 = pd.read_csv(file1)
    file2 = f"{cell}/{cell}_GDS_PEX_PREDICTION_ML.csv"
    df2 = pd.read_csv(file2)
    #columns_to_drop - Unnamed - index column in pex_prediction_ml
    if 'Unnamed: 0' in df2.columns:
        df2.drop('Unnamed: 0',axis = 1,inplace = True)
    output = f"{cell}/{cell}_gds_pex_metrics.csv"   
   
    try:
        df = pd.merge(df1,df2, on='File')
        df.rename(columns={'File': 'permutation_id'}, inplace=True) 
        df.to_csv(output, index=False)                
    except Exception as e:
         print(f"Error: {e}")
    
def prepare_result(cell):
    """
    Prepare the result directory, moving and organizing files.
    """
    working_dir = Path(cell) / ".working"
    layout_dir = Path(cell) / f"{cell}_layout"

    # Creating .working and layout directories
    prepare_working_directory(working_dir)
    prepare_working_directory(layout_dir)

    # Moving JSON and GDS files to the .working directory
    for file in Path(cell).glob("*.json"):
        shutil.move(str(file), str(working_dir))
    for file in Path(cell).glob("*.gds"):
        shutil.move(str(file), str(working_dir))
    # Renaming optimized_geometries directory to {cell}_layout
    optimized_geometries_dir = Path(cell) / "optimized_geometries"
    if optimized_geometries_dir.exists():
        shutil.move(str(optimized_geometries_dir), str(layout_dir))

def prepare_result(cell):
    """
    Prepare the result directory, moving and organizing files as per the Bash script.
    """
    working_dir = Path(cell) / ".working"
    layout_dir = Path(cell) / f"{cell}_layout"

    # Creating .working and layout directories
    prepare_working_directory(working_dir)
    prepare_working_directory(layout_dir)

    # Moving JSON, text and GDS files to the .working directory
    for file in Path(cell).glob("*.json"):
        shutil.move(str(file), str(working_dir))
    for file in Path(cell).glob("*.gds"):
        shutil.move(str(file), str(working_dir))
    for file in Path(cell).glob("*.txt"):
        shutil.move(str(file), str(working_dir))

    # Renaming optimized_geometries directory to {cell}_layout
    optimized_geometries_dir = Path(cell) / "optimized_geometries"
    if optimized_geometries_dir.exists():
        shutil.move(str(optimized_geometries_dir), str(layout_dir))

def process_cell_wrapper(cell_pdk_args):
    cell,args = cell_pdk_args
    process_cell(cell,args)

def process_cell(cell, args):
    """
    Process a single cell based on the provided arguments.
    """
    cell_path = Path(cell)
    if cell_path.exists():
        shutil.rmtree(cell_path)  # Overwrite the existing cell directory
    cell_path.mkdir(parents=True, exist_ok=True)

    permutations_dir = cell_path / f"{cell}_permutations"
    metrics_dir = cell_path / f"{cell}_metrics"
    prepare_working_directory(permutations_dir)
    print(f"creating the directory {metrics_dir}")
    prepare_working_directory(metrics_dir)
    flow_type = args.flow_type

    # Corrected Indentation
    if not any([args.variations, args.metrics, args.predict_pex]):
        generate_layout(cell, args, args.debug_plots)
        generate_permutations(cell, flow_type,args, args.limiter)
        print_gds_count(cell)
        calculate_metrics(cell, args,flow_type)
        predict_parasitics(cell, args, flow_type)
        #extract_relative_resistance(cell, args, flow_type)
        if args.flow_type == "gds":
            combine_pex_metrics(cell)
    else:
        if args.cell or args.variations or args.metrics or args.predict_pex:
            generate_layout(cell,args)
        if args.variations:
            generate_permutations(cell, args,flow_type)
        if args.metrics:
            calculate_metrics(cell, args,flow_type)
        if args.predict_pex:
            predict_parasitics(cell, args, flow_type)
        # if args.relative_resistance:
        #     extract_relative_resistance(cell, args, flow_type)
    prepare_result(cell)


def main():
    is_valid = notify_support_expiry()
    if is_valid:
        args = parse_args()
        tech_file=args.tech_path
        spice_file = args.netlist_path
        if not spice_file:
                print("\033[91mError: Netlist file path required.\033[0m", file=sys.stderr)
                sys.exit(1)
        if not tech_file:
                print("\033[91mError: Tech file path required.\033[0m", file=sys.stderr)
                sys.exit(1)
        if args.all_cells: 
            all_cells = get_all_cells_from_spice(spice_file)
            print(all_cells)
            # Determine the number of processes based on the available CPU cores
            num_processes = min(len(all_cells), multiprocessing.cpu_count())
            # Create a pool of workers
            with multiprocessing.Pool(num_processes) as pool:
                # Map process_cell function to all cells
                pool.map(process_cell_wrapper, [(cell,args) for cell in all_cells])
        else:
            cell = args.cell
            if not cell:
                print("Error: Cell name is required.")
                sys.exit(1)
            process_cell(cell, args)

def notify_support_expiry():
    cutoff_date = datetime.datetime(2025, 12, 31, 23, 59, 59)  # Dec 31, 2025, at 24:00 (midnight)
    notification_date = cutoff_date - datetime.timedelta(days=10)  # 10 days prior (Dec 21, 2025)
    current_datetime = datetime.datetime.now()

    # Check if the current date is after the cutoff date (support has ended)
    if current_datetime > cutoff_date:
        message = '\033[91m🔴 Support for this service has ended on December 31, 2025.\033[0m'
        logger.debug("Support for this service has ended on December 31, 2025.")
        print(message)
        return False
    elif notification_date <= current_datetime <= cutoff_date:
        message = '\033[93m⚠️  Support for this service will end on December 31, 2025. Please take necessary actions.\033[0m'
        logger.warning("Support for this service will end on December 31, 2025. Please take necessary actions.")
        print(message)
        return True
    else:
        return True

if __name__ == "__main__":
    main()
