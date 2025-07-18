"""Script to Encode and Save Net Data using a Trained Autoencoder.

This script loads a pre-trained autoencoder model, encodes input data from CSV files, and saves the encoded representations.

Example commands to run:

For CFET:
    python pex_extraction/encoders/encode_and_save.py --metrics_folder metrics_folder_cfet --model_path AE_layers_with_0_CFET.pth --output_file encoded_data_layers_with_0_CFET.csv --model_type incremental

For GAA:
    python pex_extraction/encoders/encode_and_save.py --metrics_folder metrics_folder_gaa --model_path AE_layers_with_0_GAA.pth --output_file encoded_data_layers_with_0_GAA.csv --model_type incremental --isGAA
"""

import argparse
import os
import glob
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import random
import sys
import platform
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.data import ConcatDataset
import logging

# Include project root in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# Import required modules
from pex_extraction.encoders.autoencoder_model import AutoencoderIncremental
from pex_extraction.data_utils.preprocessing_encoding import (
    preprocess_data_training_incremental_ae,
)
from pex_extraction.data_utils.utils import IL_layers_hardcoded_1, IL_layers_hardcoded_gaa

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sivista_app')

# -------------------------------
# Utility Functions
# -------------------------------

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility.

    Args:
        seed (int): Seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    elif torch.backends.mps.is_available():
        torch.manual_seed(seed)
    logger.info(f"Random seed set to {seed}")

class EncoderWrapper(nn.Module):
    """A wrapper class to extract the encoder part of the trained AutoencoderIncremental."""

    def __init__(self, autoencoder):
        """Initialize the EncoderWrapper.

        Args:
            autoencoder (nn.Module): The trained autoencoder model.
        """
        super(EncoderWrapper, self).__init__()
        self.res_block1 = autoencoder.res_block1
        self.pool1 = autoencoder.pool1
        self.res_block2 = autoencoder.res_block2
        self.pool2 = autoencoder.pool2
        self.flatten = autoencoder.flatten

    def forward(self, x):
        """Forward pass through the encoder.

        Args:
            x (Tensor): Input tensor.

        Returns:
            Tensor: Encoded representation.
        """
        x = self.res_block1(x)
        x = self.pool1(x)
        x = self.res_block2(x)
        x = self.pool2(x)
        x = self.flatten(x)
        return x

# -------------------------------
# Main Processing Script
# -------------------------------

def main():
    """Main function to encode and save net data using a trained autoencoder."""
    parser = argparse.ArgumentParser(description='Encode and Save Net Data using Trained Autoencoder')
    parser.add_argument('--metrics_folder', type=str, required=True, help='Path to the folder containing CSV metrics files')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the trained autoencoder model')
    parser.add_argument('--output_file', type=str, default='encoded_data.csv', help='Output file to save the encoded data')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for data processing')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--model_type', type=str, choices=['incremental', 'incremental_light'], default='incremental', help='Type of autoencoder model to use')
    parser.add_argument('--isGAA', action='store_true', help='Use GAA layers')
    args = parser.parse_args()

    # Set random seed
    set_seed(args.seed)

    # Determine device
    if sys.platform == 'darwin' and platform.machine() == 'arm64' and torch.backends.mps.is_available():
        device = torch.device('mps')
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")

    # Define required_columns based on isGAA argument
    global required_columns
    if args.isGAA:
        required_columns = IL_layers_hardcoded_gaa
    else:
        required_columns = IL_layers_hardcoded_1
    num_channels = len(required_columns)
    logger.info(f"Number of channels (common layers): {num_channels}")

    # Initialize the autoencoder model based on the specified type
    
    autoencoder = AutoencoderIncremental(num_channels=num_channels).to(device)
    

    # Load the pre-trained weights
    autoencoder.load_state_dict(torch.load(args.model_path, map_location=device))
    autoencoder.eval()  # Set model to evaluation mode
    logger.info(f"Loaded trained autoencoder from {args.model_path}")

    # Create encoder wrapper
    encoder = EncoderWrapper(autoencoder).to(device)
    encoder.eval()  # Ensure encoder is in evaluation mode

    # Get list of CSV files
    csv_files = glob.glob(os.path.join(args.metrics_folder, '*.csv'))
    csv_files.sort()  # Ensure consistent order

    encoded_data_list = []

    # Process data in batches
    for csv_file in csv_files:
        logger.info(f"Processing file: {csv_file}")
        # Load data from CSV
        data = pd.read_csv(csv_file)

        # Preprocess data and get net names
        spatial_features_tensor, net_names_col = preprocess_data_training_incremental_ae(
            data, required_columns, return_net_names=True, isGAA=args.isGAA
        )

        # Create DataLoader
        dataset = TensorDataset(spatial_features_tensor)
        data_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)

        # Encode data in batches
        all_encoded_outputs = []
        with torch.no_grad():
            for batch in data_loader:
                inputs = batch[0].to(device)
                encoded_outputs = encoder(inputs)
                all_encoded_outputs.append(encoded_outputs.cpu())

        # Concatenate all encoded outputs
        all_encoded_outputs = torch.cat(all_encoded_outputs, dim=0)
        # Convert to numpy array
        encoded_array = all_encoded_outputs.numpy()

        # Create a DataFrame with net names and encoded features as a tuple
        encoded_df = pd.DataFrame({
            'Net_Name': net_names_col.values,
            'Encoded_Values': [tuple(row) for row in encoded_array]
        })

        encoded_data_list.append(encoded_df)

    # Concatenate data from all CSV files
    final_encoded_df = pd.concat(encoded_data_list, ignore_index=True)
    # Save the final DataFrame to CSV
    final_encoded_df.to_csv(args.output_file, index=False)
    logger.info(f"Encoded data saved to {args.output_file}")

if __name__ == '__main__':
    main() 