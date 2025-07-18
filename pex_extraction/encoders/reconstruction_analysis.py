"""Script to Analyze Reconstruction Errors of the Autoencoder on Datasets.

This script loads the pre-trained autoencoder model, reads each CSV file in the metrics_folder,
processes data in batches, performs reconstruction, computes the reconstruction error, plots them, and
computes the number of matching blocks between the original and reconstructed grids.

Example commands to run:
For CFET:
    python pex_extraction/encoders/reconstruction_analysis.py --metrics_folder metrics_folder --model_path autoencoder_model.pth --output_folder output_plots --model_type incremental

For GAA:
    python pex_extraction/encoders/reconstruction_analysis.py --metrics_folder metrics_folder_gaa --model_path incremental_autoencoder_normalized_shuffled_gaa.pth --output_folder output_plots_gaa --model_type incremental --isGAA
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from typing import List

# Append the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from pex_extraction.encoders.autoencoder_model import (
    Autoencoder2312,
    Autoencoder512,
    AutoencoderIncremental
)
from pex_extraction.data_utils.preprocessing_encoding import preprocess_data_training_incremental_ae
from pex_extraction.data_utils.utils import IL_layers_hardcoded_1, IL_layers_hardcoded_gaa
from torch.utils.data import DataLoader, Dataset

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sivista_app')

class SpatialDataset(Dataset):
    """Custom Dataset for loading spatial features from a pandas DataFrame."""

    def __init__(self, data: pd.DataFrame, common_layers: List[str], plot_grids=False, isGAA=False):
        """Initialize the SpatialDataset.

        Args:
            data (pd.DataFrame): Input data DataFrame.
            common_layers (List[str]): List of common layers.
            plot_grids (bool, optional): Whether to plot the grids. Defaults to False.
            isGAA (bool, optional): Whether to use GAA layers. Defaults to False.
        """
        self.data = data
        self.common_layers = common_layers
        self.isGAA = isGAA

        self.spatial_features, self.net_names = preprocess_data_training_incremental_ae(
            self.data,
            self.common_layers,
            return_net_names=True,
            plot_grids=plot_grids,
            isGAA=self.isGAA  # Pass isGAA to the preprocessing function
        )
        self.length = self.spatial_features.shape[0]

    def __getitem__(self, index):
        """Get item by index.

        Args:
            index (int): Index of the item.

        Returns:
            Tensor: Spatial feature tensor.
        """
        return self.spatial_features[index]

    def __len__(self):
        """Get the length of the dataset.

        Returns:
            int: Number of samples.
        """
        return self.length

def load_autoencoder(model_path: str, model_type: str = 'incremental', device: torch.device = None):
    """Load the pre-trained autoencoder model.

    Args:
        model_path (str): Path to the pre-trained model.
        model_type (str): Type of model ('2312', '512', 'incremental', 'incremental_light').
        device (torch.device, optional): Device to load the model onto.

    Returns:
        Tuple[nn.Module, torch.device]: The loaded autoencoder model and device.
    """
    if device is None:
        if torch.cuda.is_available():
            device = torch.device('cuda')
            logger.info("CUDA is available, using GPU")
        elif torch.backends.mps.is_available():
            device = torch.device('mps')
            logger.info("MPS is available, using GPU")
        else:
            device = torch.device('cpu')
            logger.info("No GPU available, using CPU")

    logger.info(f"Loading pre-trained autoencoder model '{model_type}' from {model_path}...")
    if model_type == '2312':
        autoencoder = Autoencoder2312().to(device)
    elif model_type == '512':
        autoencoder = Autoencoder512().to(device)
    elif model_type == 'incremental':
        autoencoder = AutoencoderIncremental(num_channels=len(required_columns)).to(device)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    autoencoder.load_state_dict(torch.load(model_path, map_location=device), strict=False)
    autoencoder.eval()
    logger.info("Pre-trained autoencoder model loaded.")
    return autoencoder, device

def compute_matching_blocks(original: np.ndarray, reconstructed: np.ndarray):
    """Compute the number of matching '1's between the original and reconstructed grids.

    Args:
        original (np.ndarray): Original binary grid of shape (N, C, H, W).
        reconstructed (np.ndarray): Reconstructed binary grid of shape (N, C, H, W).

    Returns:
        Tuple[int, int]: Number of matching '1's and total number of '1's in the original grid.
    """
    # Find positions where original is 1
    original_ones = original > 0
    # Check if reconstructed has 1 at those positions
    matching_ones = np.sum((original_ones) & (reconstructed > 0))
    # Total number of '1's in original
    total_ones = np.sum(original_ones)
    return matching_ones, total_ones

def plot_reconstruction_error(errors: List[float], csv_file: str, output_folder: str):
    """Plot the reconstruction error.

    Args:
        errors (List[float]): List of reconstruction errors.
        csv_file (str): Name of the CSV file being processed.
        output_folder (str): Folder to save the plot.
    """
    plt.figure()
    plt.plot(errors)
    plt.xlabel('Sample Index')
    plt.ylabel('Reconstruction Error')
    plt.title(f'Reconstruction Error for {csv_file}')
    plot_path = os.path.join(output_folder, f'reconstruction_error_{os.path.splitext(csv_file)[0]}.png')
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Plot saved to {plot_path}")

def plot_multilayer_grids(
    original: torch.Tensor,
    reconstructed: torch.Tensor,
    file_names: List[str],
    output_folder: str,
    sample_indices: List[int] = None,
    layers_to_plot: List[str] = None,
    layer_names: List[str] = None,
    grid_size: int = 64,  # Assuming grid size is 64x64
    plot_reconstructed: bool = False  # Optional parameter to plot reconstructed images
):
    """Plot the original and reconstructed grids for specified layers.

    Args:
        original (torch.Tensor): Original tensor of shape (N, C, H, W).
        reconstructed (torch.Tensor): Reconstructed tensor of shape (N, C, H, W).
        file_names (List[str]): List of file names corresponding to the samples.
        output_folder (str): Folder to save the plots and indices.
        sample_indices (List[int], optional): Indices of samples to plot. Defaults to None.
        layers_to_plot (List[str], optional): List of layer names to plot. Defaults to None.
        layer_names (List[str], optional): List of all layer names.
        grid_size (int, optional): Size of the grid (assuming square grid). Defaults to 64.
        plot_reconstructed (bool, optional): Whether to plot reconstructed images. Defaults to False.
    """
    if sample_indices is None:
        sample_indices = [0, 1]  # Default to the first samples

    if layer_names is None:
        raise ValueError("layer_names must be provided to map layer names to indices.")

    if layers_to_plot is None:
        layers_to_plot = ['M0','M2_BACKSIDE_POWER_LINES','PMOS_NANOSHEET']  # Default layers

    # Map layer names to indices
    layer_indices = [layer_names.index(layer) for layer in layers_to_plot if layer in layer_names]

    if not layer_indices:
        raise ValueError("None of the specified layers to plot were found in layer_names.")

    original = original.cpu().numpy()
    if plot_reconstructed:
        reconstructed = reconstructed.cpu().numpy()

    for idx in sample_indices:
        if idx >= original.shape[0]:
            logger.warning(f"Sample index {idx} is out of bounds. Skipping.")
            continue

        num_cols = 2 if plot_reconstructed else 1
        fig, axes = plt.subplots(len(layer_indices), num_cols, figsize=(10 * num_cols, 5 * len(layer_indices)))

        if len(layer_indices) == 1:
            axes = np.expand_dims(axes, axis=0)  # Ensure axes is 2D for consistency

        file_name = file_names[idx] if idx < len(file_names) else "Unknown File"

        for i, layer in enumerate(layer_indices):
            # Original
            grid_data = original[idx, layer]
            ax = axes[i, 0] if plot_reconstructed else axes[i]
            im = ax.imshow(grid_data, cmap='gray_r', vmin=0, vmax=1, origin='lower')
            ax.set_title(f'Original - {layer_names[layer]}')
            ax.set_xticks(np.arange(0, grid_size+1, 8))  # Adjust the step size as needed
            ax.set_yticks(np.arange(0, grid_size+1, 8))
            ax.grid(True, which='both', color='lightgrey', linewidth=0.5)
            ax.set_aspect('equal')

            # Number the cells with value 1
            coords = np.argwhere(grid_data == 1)
            for (y, x) in coords:
                ax.text(x + 0.5, y + 0.5, f'({x},{y})', color='red', fontsize=6, ha='center', va='center')

            # Save cell indices with value 1 to text files
            indices_text_path = os.path.join(output_folder, f'sample_{idx}_{layer_names[layer]}_indices.txt')
            with open(indices_text_path, 'w') as f:
                f.write(f'Original indices (layer {layer_names[layer]}):\n')
                for (y, x) in coords:
                    f.write(f'({x}, {y})\n')
            logger.info(f"Cell indices saved to {indices_text_path}")

            if plot_reconstructed:
                # Reconstructed
                grid_data_recon = reconstructed[idx, layer]
                ax_recon = axes[i, 1]
                ax_recon.imshow(grid_data_recon, cmap='gray_r', vmin=0, vmax=1, extent=(0, grid_size, 0, grid_size), origin='lower')
                ax_recon.set_title(f'Reconstructed - {layer_names[layer]}')
                ax_recon.set_xticks(np.arange(0, grid_size+1, 8))
                ax_recon.set_yticks(np.arange(0, grid_size+1, 8))
                ax_recon.grid(True, which='both', color='lightgrey', linewidth=0.5)
                ax_recon.set_aspect('equal')

                # Number the cells with value 1
                coords_recon = np.argwhere(grid_data_recon == 1)
                for (y, x) in coords_recon:
                    ax_recon.text(x + 0.5, y + 0.5, f'({x},{y})', color='blue', fontsize=6, ha='center', va='center')

                # Append reconstructed indices to the text file
                with open(indices_text_path, 'a') as f:
                    f.write('\nReconstructed indices:\n')
                    for (y, x) in coords_recon:
                        f.write(f'({x}, {y})\n')
                logger.info(f"Reconstructed cell indices appended to {indices_text_path}")

        # Add file name as the figure title
        fig.suptitle(f'Sample {idx} - File: {file_name}', fontsize=16)

        plot_path = os.path.join(output_folder, f'multilayer_grid_sample_{idx}_{file_name}.png')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make space for suptitle
        plt.savefig(plot_path, dpi=300)  # Increase DPI for higher resolution
        plt.close()
        logger.info(f"Multilayer grid plot saved to {plot_path}")

        # Create a combined plot for all layers
        combined_fig, combined_ax = plt.subplots(figsize=(10, 10))
        combined_ax.set_title(f'Combined Layers - Sample {idx}')
        combined_ax.set_xticks(np.arange(0, grid_size+1, 8))
        combined_ax.set_yticks(np.arange(0, grid_size+1, 8))
        combined_ax.grid(True, which='both', color='lightgrey', linewidth=0.5)
        combined_ax.set_aspect('equal')

        for i, layer in enumerate(layer_indices):
            grid_data = original[idx, layer]
            combined_ax.imshow(grid_data, cmap='gray_r', vmin=0, vmax=1, origin='lower', alpha=0.5)

        combined_plot_path = os.path.join(output_folder, f'combined_layers_sample_{idx}_{file_name}.png')
        combined_fig.tight_layout()
        combined_fig.savefig(combined_plot_path, dpi=300)
        plt.close(combined_fig)
        logger.info(f"Combined layers plot saved to {combined_plot_path}")

def process_csv(autoencoder: nn.Module, device: torch.device, csv_path: str, output_folder: str, batch_size: int = 32, common_layers: List[str] = IL_layers_hardcoded_1, isGAA: bool = False):
    """Process a single CSV file: load data in batches, perform reconstruction, compute error, and plot.

    Args:
        autoencoder (nn.Module): The autoencoder model.
        device (torch.device): Device for computations.
        csv_path (str): Path to the CSV file.
        output_folder (str): Folder to save plots.
        batch_size (int, optional): Batch size for processing data. Defaults to 32.
        common_layers (List[str], optional): List of common layers to be used for preprocessing. Defaults to IL_layers_hardcoded_1.
        isGAA (bool, optional): Whether to use GAA layers. Defaults to False.
    """
    logger.info(f"Processing file: {csv_path}")
    data = pd.read_csv(csv_path)
    
    # Ensure common_layers is provided
    if common_layers is None:
        raise ValueError("common_layers must be provided to process the dataset.")

    dataset = SpatialDataset(data, common_layers, isGAA=isGAA)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    total_loss = 0.0
    errors = []
    total_matching_blocks = 0
    total_blocks = 0
    all_original = []
    all_reconstructed = []

    for batch_idx, batch in enumerate(data_loader):
        batch = batch.float().to(device)
        with torch.no_grad():
            reconstructed = autoencoder(batch)
        if torch.all(reconstructed == 0):
            logger.warning("Reconstructed output is all zeros.")
            continue
        # Since data is binary, we binarize the reconstructed data
        reconstructed_binary = (reconstructed >= 0.5).float()

        # Accumulate batches for plotting and matching blocks calculation
        all_original.append(batch.cpu())
        all_reconstructed.append(reconstructed_binary.cpu())  # Use binarized data here

        # Compute reconstruction error for each sample in the batch
        batch_errors = ((batch - reconstructed_binary) ** 2).mean(dim=[1, 2, 3]).cpu().numpy()
        errors.extend(batch_errors.tolist())

        # Compute matching blocks
        original_np = batch.cpu().numpy()
        reconstructed_np = reconstructed_binary.cpu().numpy()
        matching_blocks_batch, total_blocks_batch = compute_matching_blocks(original_np, reconstructed_np)
        total_matching_blocks += matching_blocks_batch
        total_blocks += total_blocks_batch

        # Free up memory
        del batch
        del reconstructed
        del reconstructed_binary
        torch.cuda.empty_cache()

    # Concatenate all batches for plotting and matching blocks calculation
    all_original = torch.cat(all_original, dim=0)
    all_reconstructed = torch.cat(all_reconstructed, dim=0)
    
    # Plot multilayer grids
    csv_file_name = os.path.basename(csv_path)
    file_names = dataset.net_names
    plot_multilayer_grids(
        original=all_original,
        reconstructed=all_reconstructed,  # Pass reconstructed data for plotting
        file_names=file_names,
        output_folder=output_folder,
        layer_names=common_layers,
        plot_reconstructed=True  # Plot both original and reconstructed images
    )
    # Compute overall matching ratio
    matching_ratio = total_matching_blocks / total_blocks * 100
    logger.info(f"Total Matching blocks: {total_matching_blocks}/{total_blocks} ({matching_ratio:.2f}%)")

    # Save analysis to a text file
    analysis_file_path = os.path.join(output_folder, f'analysis_{os.path.splitext(csv_file_name)[0]}.txt')
    with open(analysis_file_path, 'w') as analysis_file:
        analysis_file.write(f"File: {csv_file_name}\n")
        analysis_file.write(f"Total Matching blocks: {total_matching_blocks}/{total_blocks} ({matching_ratio:.2f}%)\n")
        analysis_file.write(f"Reconstruction errors: {errors}\n")
    logger.info(f"Analysis saved to {analysis_file_path}")

    # Plot reconstruction errors
    plot_reconstruction_error(errors, csv_file_name, output_folder)

    logger.info(f"Completed processing for file: {csv_file_name}")

def main():
    """Main function to perform reconstruction analysis on datasets in metrics_folder."""
    parser = argparse.ArgumentParser(description='Autoencoder Reconstruction Analysis')
    parser.add_argument('--metrics_folder', type=str, required=True, help='Path to the folder containing CSV files')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the pre-trained autoencoder model')
    parser.add_argument('--model_type', type=str, choices=['2312', '512', 'incremental', 'incremental_light'], default='incremental', help='Type of autoencoder model (default: incremental)')
    parser.add_argument('--output_folder', type=str, required=True, help='Folder to save the output plots')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for processing data (default: 32)')
    parser.add_argument('--isGAA', action='store_true', help='Use GAA layers')

    args = parser.parse_args()

    # Define required_columns based on isGAA argument
    global required_columns
    if args.isGAA:
        required_columns = IL_layers_hardcoded_gaa
    else:
        required_columns = IL_layers_hardcoded_1

    # Ensure the output folder exists
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
        logger.info(f"Created output folder: {args.output_folder}")

    # Use required_columns based on isGAA
    common_layers = required_columns
    logger.info(f"Common layers: {common_layers}")

    # Load the autoencoder model
    autoencoder, device = load_autoencoder(args.model_path, args.model_type)

    # Process each CSV file in the metrics folder
    for csv_file in os.listdir(args.metrics_folder):
        csv_path = os.path.join(args.metrics_folder, csv_file)
        process_csv(autoencoder, device, csv_path, args.output_folder, batch_size=args.batch_size, common_layers=common_layers, isGAA=args.isGAA)

if __name__ == '__main__':
    main()
