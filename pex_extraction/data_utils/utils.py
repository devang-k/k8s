"""
This module provides utility functions and classes for data manipulation and processing.
It includes functions for converting JSON data to DataFrames, calculating net sums, merging columns,
and a PyTorch Dataset class for memory-mapped spatial data.

Functions:
- add_prefix_to_list: Adds a prefix to each item in a list.
- gnn_json_to_dataframe: Converts a dictionary of dictionaries (from JSON) into a pandas DataFrame.
- gnn_calculate_net_sum: Calculates the sum of capacitance for net pairs containing specified nets.
- merge_equivalent_columns: Merges equivalent columns in a DataFrame by taking the mean.

Classes:
- MemmapDataset: A PyTorch Dataset for memory-mapped spatial data.
"""

import pandas as pd
from torch.utils.data import Dataset
import numpy as np
import torch
import os
# -------------------------------
# Constants
# -------------------------------

# Hardcoded columns for SiVista 1.0 (Obsolete)
required_columns = [
    'Polygons_220:0', 'Polygons_102:1', 'Polygons_102:2', 'Polygons_103:1',
    'Polygons_103:2', 'Polygons_104:3', 'Polygons_110:0', 'Polygons_CELL_BOUNDARY',
    'Polygons_M0', 'Polygons_M2_BACKSIDE_POWER_LINES', 'Polygons_NMOS_ACT_PATTERNED',
    'Polygons_NMOS_GATE', 'Polygons_NMOS_INTERCONNECT', 'Polygons_NMOS_NANOSHEET',
    'Polygons_PMOS_ACT_PATTERNED', 'Polygons_PMOS_GATE', 'Polygons_PMOS_INTERCONNECT',
    'Polygons_PMOS_NANOSHEET', 'Polygons_SINGLE_DIFFUSION_BREAK',
    'Polygons_VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR',
    'Polygons_VIA_FROM_M0_TO_PMOS_GATE_VG', 'Polygons_VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT',
    'Polygons_VIA_FROM_PMOS_INTERCONNECT_TO_NMOS_INTERCONNECT', 'Polygons_122:0',
    'Polygons_107:0', 'Polygons_109:0'
]

# Hardcoded columns for current implementation of CFET
IL_layers_hardcoded_1 = [
    '220:0', '221:0', '110:0',
    'CELL_BOUNDARY', 'M0', 'M2_BACKSIDE_POWER_LINES', 'NMOS_ACT_PATTERNED',
    'NMOS_GATE', 'NMOS_INTERCONNECT', 'NMOS_NANOSHEET', 'PMOS_ACT_PATTERNED',
    'PMOS_GATE', 'PMOS_INTERCONNECT', 'PMOS_NANOSHEET', 'SINGLE_DIFFUSION_BREAK',
    'VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR', 'VIA_FROM_M0_TO_PMOS_GATE_VG',
    'VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT'
]

# Hardcoded columns for current implementation of GAA
IL_layers_hardcoded_gaa = [
     '220:0', '221:0', 
    'CELL_BOUNDARY', 'M0', 'M2_BACKSIDE_POWER_LINES', 'NMOS_ACT_PATTERNED',
    'NMOS_GATE', 'NMOS_INTERCONNECT', 'NMOS_NANOSHEET', 'PMOS_ACT_PATTERNED',
    'PMOS_GATE', 'PMOS_INTERCONNECT', 'PMOS_NANOSHEET', 'SINGLE_DIFFUSION_BREAK',
    'VIA_FROM_INTERCONNECT_TO_BACKSIDE_POWER_TSVBAR', 'VIA_FROM_M0_TO_PMOS_GATE_VG',
    'VIA_FROM_M0_TO_PMOS_INTERCONNECT_VCT', 'M1'
]

def add_prefix_to_list(input_list):
    """Adds a prefix 'Polygons_' to each item in the input list.

    Args:
        input_list (list): List of strings to which the prefix will be added.

    Returns:
        list: List of strings with the prefix added.
    """
    return [f"Polygons_{item}" for item in input_list]

def gnn_json_to_dataframe(data):
    """Converts a dictionary of dictionaries (as loaded from JSON) into a pandas DataFrame.

    Args:
        data (dict): The input dictionary containing the JSON data.

    Returns:
        pd.DataFrame: A DataFrame containing the combined data.
    """
    # Prepare a list to hold individual DataFrames
    dataframes = []

    # Iterate over each item in the JSON data
    for key, value in data.items():
        # Create a DataFrame for each entry
        df = pd.DataFrame({
            'Net Pair': value['Net Pairs'],
            'Capacitance': value['Capacitance']
        })
        # Add a column for the identifier
        df['Identifier'] = key
        # Append the DataFrame to the list
        dataframes.append(df)

    # Concatenate all DataFrames into a single DataFrame
    result_df = pd.concat(dataframes, ignore_index=True)

    return result_df

def gnn_calculate_net_sum(group, net_names):
    """Calculates the sum of capacitance for net pairs containing specified nets.

    Args:
        group (pd.DataFrame): DataFrame containing net pair and capacitance data.
        net_names (list): List of net names to calculate the sum for.

    Returns:
        pd.Series: Series containing the sum of capacitance for each net.
    """
    net_sums = {}
    for net in net_names:
        # Sum capacitance for net pairs containing the net
        net_sums[f'{net}'] = group[group['Net Pair'].str.contains(net)]['Capacitance'].sum()
    return pd.Series(net_sums)

def merge_equivalent_columns(df):
    """Merges equivalent columns in a DataFrame by taking the mean.

    Args:
        df (pd.DataFrame): DataFrame with columns to be merged.

    Returns:
        pd.DataFrame: DataFrame with merged columns.
    """
    # Create a dictionary to map sorted net pairs to their original columns
    pair_map = {}
    
    for col in df.columns:
        if col != 'Identifier':
            # Sort the net names in the pair
            sorted_pair = '_to_'.join(sorted(col.split('_to_')))
            if sorted_pair not in pair_map:
                pair_map[sorted_pair] = []
            pair_map[sorted_pair].append(col)
    
    # Create a new DataFrame to store merged columns
    merged_df = df[['Identifier']].copy()
    
    for sorted_pair, cols in pair_map.items():
        if len(cols) > 1:
            # Merge equivalent columns by taking the mean
            merged_df[sorted_pair] = df[cols].mean(axis=1)
        else:
            # If there's only one column, just copy it
            merged_df[sorted_pair] = df[cols[0]]
    
    return merged_df

class MemmapDataset(Dataset):
    """A PyTorch Dataset for memory-mapped spatial data."""

    def __init__(self, memmap_file, indices, grid_size=64, num_columns=26):
        """Initializes the MemmapDataset.

        Args:
            memmap_file (str): Path to the memory-mapped file.
            indices (list): List of indices for the subset (train or test).
            grid_size (int, optional): Size of the grid. Defaults to 64.
            num_columns (int, optional): Number of columns in the data. Defaults to 26.
        """
        # Calculate the number of samples based on the file size
        file_size = os.path.getsize(memmap_file)
        element_size = np.dtype('float32').itemsize
        num_samples = file_size // (grid_size * grid_size * num_columns * element_size)

        # Load the memory-mapped array with the calculated dataset size
        self.memmap_data = np.memmap(memmap_file, dtype='float32', mode='r', shape=(num_samples, grid_size, grid_size, num_columns))
        self.indices = indices  # Store the indices for the subset (train or test)

    def __len__(self):
        """Returns the length of the subset (train or test).

        Returns:
            int: Length of the subset.
        """
        return len(self.indices)

    def __getitem__(self, idx):
        """Fetches the data at the specified index.

        Args:
            idx (int): Index of the data to fetch.

        Returns:
            tuple: A tuple containing the input tensor and target tensor (same for autoencoder).
        """
        # Use the indices to access the correct rows in the full dataset
        actual_index = self.indices[idx]  # Map the index to the full dataset
        spatial_input = self.memmap_data[actual_index]  # Fetch the data at this index
        spatial_input_tensor = torch.tensor(spatial_input).float().permute(2, 0, 1)  # Convert to tensor
        return spatial_input_tensor, spatial_input_tensor  # Input and target are the same for autoencoder
