"""Prediction Script for Regression Models.

This script provides functions to perform predictions using trained regression models,
such as Mixture of Experts (MoE) and Graph Neural Networks (GNN). It loads the necessary models,
preprocesses the input data, runs the prediction pipeline, and saves the results.

Example usage:
    python pex_extraction/dtco_ml_predict.py --input_path metrics_folder_gaa/AND2X1_metrics.csv --output csv --model gnn --data_results_format net-to-net
"""

import sys
import os
import argparse
import logging
import warnings

import pandas as pd
import torch

# Append project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stdcell_generation_client.technology_utils import load_tech_file
from pex_extraction.regression.inference import MoeModel, GNNModel
from pex_extraction.data_utils.preprocessing_encoding import load_and_preprocess_data
from pex_extraction.data_utils.utils import (
    IL_layers_hardcoded_1,
    add_prefix_to_list,
    IL_layers_hardcoded_gaa
)
from utils.config import model_paths

# Set up logging
logger = logging.getLogger('sivista_app')

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

def model_factory(model_type, required_columns, isGAA=False):
    """Factory function to load the appropriate regression model.

    Args:
        model_type (str): Type of the model to load ('moe' or 'gnn').
        required_columns (list): List of required columns for preprocessing.
        isGAA (bool, optional): Flag indicating if the technology is GAA. Defaults to False.

    Returns:
        object: An instance of the selected model class.

    Raises:
        ValueError: If an unknown model type is provided.
        FileNotFoundError: If required model paths are not found.
    """
    model_mapping = {
        "moe": MoeModel,
        "gnn": GNNModel,
    }
    if model_type not in model_mapping:
        raise ValueError(f"Unknown model type: {model_type}")

    # Select technology based on isGAA flag
    technology_str = "gaa" if isGAA else "cfet"
    model_type_paths = model_paths[model_type][technology_str]
    logger.info('\n\n')
    logger.info(f"Loading weights from: \n {model_type_paths}")
    logger.info('\n\n')

    try:
        encoder_path = model_type_paths["encoder_path"]
        scaler_path = model_type_paths["scaler_path"]
        model_path = model_type_paths["predictor_path"]
    except KeyError as e:
        raise FileNotFoundError(f"Required path not found for {model_type} model of {technology_str}: {e}")

    if model_type == "gnn":
        # model_init_params is needed only for GNN model
        model_init_params = model_type_paths.get("model_init_params")
        return model_mapping[model_type](
            model_path,
            encoder_path,
            scaler_path,
            required_columns,
            model_init_params,
            isGAA=isGAA,
        )
    return model_mapping[model_type](
        model_path,
        encoder_path,
        scaler_path,
        required_columns,
        isGAA=isGAA,
    )

def main(args):
    """Main function to run the prediction pipeline.

    Args:
        args (dict): Dictionary of command-line arguments.
    """
    input_path = args.get("input_path", "net_to_net/net_labeled_AOI21X1_metrics.csv")
    output_path = args.get("output", "csv")
    model_type = args.get("model", "gnn")
    data_results_format = args.get("data_results_format", "net-to-net")
    batch_size = 100
    pdk = args.get("pdk", "monCFET")

    # Load technology information
    tech_data = args.get("tech")
    tech = load_tech_file(tech_data)
    technology = tech.technology
    logger.info(f"Technology is {technology}")

    # Define required_columns based on the technology variable
    global required_columns
    if technology == "gaa" or technology == "finfet":
        required_columns = add_prefix_to_list(IL_layers_hardcoded_gaa)
        isGAA = True
    else:
        required_columns = add_prefix_to_list(IL_layers_hardcoded_1)
        isGAA = False

    # Load and preprocess data
    validated_df = load_and_preprocess_data(input_path, required_columns, isGAA=isGAA)

    # Initialize the model
    model = model_factory(model_type, required_columns, isGAA)

    # Run the prediction pipeline
    if model_type == "gnn":
        capsum = True if data_results_format == "individual-net" else False
        predictions = model.run_pipeline(
            validated_df,
            batch_size,
            output_path=output_path,
            capsum=capsum
        )
    else:
        predictions = model.run_pipeline(
            validated_df,
            batch_size,
            output_path=output_path
        )

    # Load the input DataFrame for merging with predictions
    input_df = pd.read_csv(input_path)

    # Save the results
    model.save_results(predictions, output_path, input_df)

if __name__ == "__main__":
    """Entry point for the prediction script.

    Example usage:
        python pex_extraction/dtco_ml_predict.py --input_path metrics_folder_gaa/AND2X1_metrics.csv --output csv --model gnn --data_results_format net-to-net
    """
    parser = argparse.ArgumentParser(description="Make predictions for specific GDS files")
    parser.add_argument("--input_path", type=str, help="Path to CSV inputs file.")
    parser.add_argument(
        "--output",
        type=str,
        nargs='+',
        default="csv",
        help="Output formats for metrics, separated by space (e.g., json csv markdown)"
    )
    parser.add_argument("--model", choices=["moe", "gnn"], default="gnn", help="Type of model to use for predictions.")
    parser.add_argument(
        "--data_results_format",
        choices=["net-to-net", "individual-net"],
        default="net-to-net",
        help="Data results format for GNN model. Default is net-to-net."
    )
    parser.add_argument('--pdk', default='monCFET', type=str, help="Process Design Kit (PDK) to use.")

    parser.add_argument('--tech', default='tech.py',
                        metavar='FILE', type=str, help='technology file')
    
    args, unknown = parser.parse_known_args()
    args = {
        "input_path": args.input_path,
        "output": args.output,
        "model": args.model,
        "data_results_format": args.data_results_format,
        "pdk": args.pdk,
        "tech":args.tech
    }
    main(args)