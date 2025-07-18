"""Data Preprocessing and Encoding Utilities.

This module provides functions and utilities for preprocessing spatial features and preparing
data for training autoencoders and regression models. It includes functions for converting
bounding boxes to grids, handling spatial features, and various utilities for data validation
and transformation.
"""
# -------------------------------
# Imports
# -------------------------------
import pandas as pd
import numpy as np
import ast
from collections import defaultdict
import torch
import logging
import glob
import os

logger = logging.getLogger('sivista_app')

# -------------------------------
# Utility Functions
# -------------------------------

def bounding_boxes_to_grid_legacy(bounding_boxes, grid_size):
    """Converts bounding boxes to a grid representation (legacy version).

    Args:
        bounding_boxes (list): List of bounding boxes, each defined by (lat1, lon1, lat2, lon2).
        grid_size (int): Size of the grid.

    Returns:
        np.ndarray: A 2D grid with bounding boxes marked.
    """
    grid = np.zeros((grid_size, grid_size))
    for box in bounding_boxes:
        lat1, lon1, lat2, lon2 = box
        y1, x1 = int(lat1 * grid_size), int(lon1 * grid_size)
        y2, x2 = int(lat2 * grid_size), int(lon2 * grid_size)
        grid[y1:y2, x1:x2] = 1
    return grid

def convert_to_spatial_legacy(spatial_features, polygon_columns):
    """Converts spatial features to a grid representation (legacy version).

    Args:
        spatial_features (pd.DataFrame): DataFrame containing spatial features.
        polygon_columns (list): List of columns containing polygon data.

    Returns:
        np.ndarray: A 4D array of spatial features.
    """
    columns_to_drop = ['File', 'M0_Layer_Label', 'Root', 'Net']
    existing_columns_to_drop = [col for col in columns_to_drop if col in spatial_features.columns]
    spatial_features_raw = spatial_features.drop(columns=existing_columns_to_drop)
    grid_size = 64
    spatial_features_grids = spatial_features_raw[polygon_columns].map(
        lambda boxes: bounding_boxes_to_grid_legacy(boxes, grid_size)
    )
    spatial_features_array = np.stack(spatial_features_grids[polygon_columns].map(
        lambda grid: grid.reshape((grid_size, grid_size, 1))
    ).values.flatten())
    spatial_features_array = np.stack(spatial_features_array).reshape(-1, grid_size, grid_size, len(polygon_columns))
    return spatial_features_array

def bounding_boxes_to_grid(bounding_boxes, grid_size, min_x, max_x, min_y, max_y, plot=False, title=''):
    """Converts bounding boxes to a grid representation.

    Args:
        bounding_boxes (list): List of bounding boxes, each defined by (x_min, y_min, x_max, y_max).
        grid_size (int): Size of the grid.
        min_x (float): Minimum x-coordinate for normalization.
        max_x (float): Maximum x-coordinate for normalization.
        min_y (float): Minimum y-coordinate for normalization.
        max_y (float): Maximum y-coordinate for normalization.
        plot (bool, optional): Whether to plot the grid. Defaults to False.
        title (str, optional): Title for the plot. Defaults to ''.

    Returns:
        np.ndarray: A 2D grid with bounding boxes marked.
    """
    grid = np.zeros((grid_size, grid_size))
    x_range = max_x - min_x
    y_range = max_y - min_y
    for box in bounding_boxes:
        x_min, y_min, x_max, y_max = box
        # Shift coordinates
        x_min_shifted = x_min - min_x
        x_max_shifted = x_max - min_x
        y_min_shifted = y_min - min_y
        y_max_shifted = y_max - min_y
        # Normalize coordinates
        x_min_norm = x_min_shifted / x_range
        x_max_norm = x_max_shifted / x_range
        y_min_norm = y_min_shifted / y_range
        y_max_norm = y_max_shifted / y_range
        # Convert to grid indices with rounding
        x1_idx = int(np.floor(x_min_norm * grid_size))
        x2_idx = int(np.ceil(x_max_norm * grid_size)) - 1
        y1_idx = int(np.floor(y_min_norm * grid_size))
        y2_idx = int(np.ceil(y_max_norm * grid_size)) - 1
        # Ensure indices are within grid bounds
        x1_idx = max(0, min(grid_size - 1, x1_idx))
        x2_idx = max(0, min(grid_size - 1, x2_idx))
        y1_idx = max(0, min(grid_size - 1, y1_idx))
        y2_idx = max(0, min(grid_size - 1, y2_idx))
        # Set grid values
        grid[y1_idx:(y2_idx + 1), x1_idx:(x2_idx + 1)] = 1

    # Plot the grid if requested
    if plot:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 6))
        plt.imshow(grid, cmap='gray_r', origin='lower')
        plt.title(f'Grid Visualization {title}')
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.grid(True)
        plt.show()

    return grid

def convert_to_spatial(spatial_features, polygon_columns, grid_size=64, reference_layer='Polygons_CELL_BOUNDARY', plot_grids=False):
    """Converts spatial features to a grid representation.

    Args:
        spatial_features (pd.DataFrame): DataFrame containing spatial features.
        polygon_columns (list): List of columns containing polygon data.
        grid_size (int, optional): Size of the grid. Defaults to 64.
        reference_layer (str, optional): Reference layer for bounding box calculation. Defaults to 'Polygons_CELL_BOUNDARY'.
        plot_grids (bool, optional): Whether to plot the grids. Defaults to False.

    Returns:
        np.ndarray: A 4D array of spatial features.
    """
    def get_bounding_box(polygons):
        all_boxes = [box for polygon in polygons if isinstance(polygon, list) for box in polygon]
        if not all_boxes:
            # Default bounding box if no polygons are present
            return 0.0, 1.0, 0.0, 1.0
        min_x = min([box[0] for box in all_boxes])
        max_x = max([box[2] for box in all_boxes])
        min_y = min([box[1] for box in all_boxes])
        max_y = max([box[3] for box in all_boxes])
        # Handle cases where max equals min to avoid division by zero
        if max_x == min_x:
            max_x += 1e-5
        if max_y == min_y:
            max_y += 1e-5
        return min_x, max_x, min_y, max_y

    spatial_features_grids = []

    for idx, row in spatial_features.iterrows():
        # Get the reference bounding box from the specified layer
        if reference_layer in row and isinstance(row[reference_layer], list):
            min_x, max_x, min_y, max_y = get_bounding_box([row[reference_layer]])
        else:
            # If reference layer is not available or doesn't contain polygons, compute from all polygons in the row
            all_polygons_in_row = [row[col] for col in polygon_columns if isinstance(row[col], list)]
            min_x, max_x, min_y, max_y = get_bounding_box(all_polygons_in_row)

        # For each layer, create the grid
        grids = []
        for col in polygon_columns:
            boxes = row[col] if isinstance(row[col], list) else []
            # Generate a title for plotting
            title = f'Index: {idx}, Layer: {col}'
            grid = bounding_boxes_to_grid(boxes, grid_size, min_x, max_x, min_y, max_y, plot=plot_grids, title=title)
            grids.append(grid)
        # Stack grids for all layers for this row
        grids_stacked = np.stack(grids, axis=-1)
        spatial_features_grids.append(grids_stacked)

    spatial_features_array = np.stack(spatial_features_grids)
    return spatial_features_array

def preprocess_data_training_incremental_ae(data, common_layers, grid_size=64, return_net_names=False, use_legacy=False, plot_grids=False, isGAA=False):
    """Preprocesses data for training an incremental autoencoder.

    Args:
        data (pd.DataFrame): Input data.
        common_layers (list): List of common layers.
        grid_size (int, optional): Size of the grid. Defaults to 64.
        return_net_names (bool, optional): Whether to return net names. Defaults to False.
        use_legacy (bool, optional): Whether to use legacy conversion. Defaults to False.
        plot_grids (bool, optional): Whether to plot grids. Defaults to False.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        torch.Tensor: Preprocessed spatial features as a PyTorch tensor.
        pd.Series, optional: Net names if return_net_names is True.
    """
    data = data[data['Layer'].isin(common_layers)].copy()

    # Handle M1 for GAA
    if isGAA and 'M1' not in common_layers:
        common_layers.append('M1')
        data['Polygons_M1'] = [[(0.0,0.0,0.0,0.0)]] * len(data)

    # Generate 'Polygons_' columns for each layer
    for layer in common_layers:
        layer_data = data[data['Layer'] == layer]
        data[f'Polygons_{layer}'] = layer_data['Polygons']

    # Fill missing 'Polygons_' columns with default values
    for layer in common_layers:
        col_name = f'Polygons_{layer}'
        if col_name not in data.columns:
            data[col_name] = pd.Series([[(0.0, 0.0, 0.0, 0.0)]] * len(data))
        else:
            data[col_name] = fill_polygon_nan(data[col_name])
    polygon_columns = [f'Polygons_{layer}' for layer in common_layers]
    validated_df = load_and_preprocess_data(data, polygon_columns, isGAA=isGAA)

    expanded_df = extract_and_expand(validated_df, isGAA=isGAA)
    net_names_col = expanded_df['File']
    # Now proceed to convert these 'Polygons_' columns into spatial grids
    if use_legacy:
        spatial_features_array = convert_to_spatial_legacy(expanded_df, polygon_columns)
    else:
        spatial_features_array = convert_to_spatial(expanded_df, polygon_columns, plot_grids=plot_grids)
    # Convert to PyTorch tensor
    spatial_features_tensor = torch.tensor(spatial_features_array).float().permute(0, 3, 1, 2)  # Shape: (N, C, H, W)
    if return_net_names:
        return spatial_features_tensor, net_names_col
    else:
        return spatial_features_tensor

def fill_polygon_nan(column):
    """Fills NaN values in a column of polygons.

    Args:
        column (pd.Series): Column containing polygon data.

    Returns:
        list: List of polygons with NaN values filled.
    """
    if column.isna().all():
        return [ [(0.0,0.0,0.0,0.0)] ] * len(column)

    lengths = []
    for item in column:
        if isinstance(item, str):
            try:
                lengths.append(len(eval(item)))
            except:
                lengths.append(0)
        elif isinstance(item, (list, tuple, np.ndarray)):
            if not np.any(pd.isna(item)):
                lengths.append(len(item))
            else:
                lengths.append(0)
        else:
            lengths.append(0)

    max_tuples = max(lengths, default=0)  # max with default to handle empty lists

    placeholder = [(0.0, 0.0, 0.0, 0.0)] * max_tuples

    result = []
    for item in column:
        if isinstance(item, str):
            result.append(eval(item))
        elif isinstance(item, (list, tuple, np.ndarray)):
            if not np.all(pd.isna(item)):  # Check if all elements are NaN
                result.append(item)
            else:
                result.append(placeholder)
        else:
            result.append(placeholder)

    return result

def deep_literal_eval(item):
    """Recursively evaluates a string representation of a Python literal.

    Args:
        item (str or list): String or list to evaluate.

    Returns:
        object: Evaluated Python object.
    """
    if isinstance(item, list):
        return [deep_literal_eval(subitem) for subitem in item]
    elif isinstance(item, str):
        try:
            # Try to convert string to list/tuple/number
            return deep_literal_eval(ast.literal_eval(item))
        except (ValueError, SyntaxError):
            # Return string as-is if it can't be converted
            return item
    else:
        return item

def extract_and_expand(dataframe, M0_only=False, isGAA=False):
    """Extracts and expands polygon data from the input DataFrame.

    Args:
        dataframe (pd.DataFrame): Input DataFrame.
        M0_only (bool, optional): Whether to process only M0 layer. Defaults to False.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        pd.DataFrame: Expanded DataFrame with polygon data.
    """
    polygon_columns = [col for col in dataframe.columns if col.startswith("Polygons_")]
    
    # Fill NaN values in polygon columns
    for col in polygon_columns:
        dataframe[col] = fill_polygon_nan(dataframe[col])
    
    # Build list of relevant columns for processing
    polygon_cols_with_file_label = polygon_columns.copy()
    polygon_cols_with_file_label.insert(0, "File")
    polygon_cols_with_file_label.append("M0_Layer_Label")
    if not M0_only:
        polygon_cols_with_file_label.append("M2_Layer_Label")
    if isGAA:
        polygon_cols_with_file_label.append("M1_Layer_Label")
    
    # Filter the dataframe to relevant columns
    dataframe_spatial = dataframe[polygon_cols_with_file_label]
    
    expanded_rows = []

    # Iterate through the rows of the dataframe
    for idx, row in dataframe_spatial.iterrows():
        file_name = row["File"]
        polygonsM0 = row["Polygons_M0"]
        
        # Process M0 layer
        labelsM0 = ast.literal_eval(row["M0_Layer_Label"]) if pd.notna(row["M0_Layer_Label"]) else []
        
        # Create a mapping from labels to list of polygons
        labels_to_polys_M0 = defaultdict(list)
        for poly, label in zip(polygonsM0, labelsM0):
            labels_to_polys_M0[label].append(poly)
        
        # Create a new row for each unique label in M0
        for label, polys in labels_to_polys_M0.items():
            new_row = row.copy()
            new_row["File"] = f"{file_name}|{label}"
            new_row["Root"] = file_name
            new_row["Net"] = label
            new_row["Polygons_M0"] = polys
            expanded_rows.append(new_row)

        # Process M2 layer if M0_only is False
        if not M0_only:
            polygonsM2 = row.get("Polygons_M2_BACKSIDE_POWER_LINES", [])
            if pd.isna(row["M2_Layer_Label"]):
                labelsM2 = []
                logger.warning(f"M2_Layer_Label is NaN for file {file_name}")
            else:
                labelsM2 = ast.literal_eval(row["M2_Layer_Label"])
            
            labels_to_polys_M2 = defaultdict(list)
            for poly, label in zip(polygonsM2, labelsM2):
                labels_to_polys_M2[label].append(poly)
            
            for label, polys in labels_to_polys_M2.items():
                new_row = row.copy()
                new_row["File"] = f"{file_name}|{label}"
                new_row["Root"] = file_name
                new_row["Net"] = label
                new_row["Polygons_M2_BACKSIDE_POWER_LINES"] = polys
                expanded_rows.append(new_row)

        # Process M1 layer if isGAA is True
        if isGAA:
            polygonsM1 = row.get("Polygons_M1", [])
            labelsM1 = ast.literal_eval(row["M1_Layer_Label"]) if pd.notna(row["M1_Layer_Label"]) else []
            
            labels_to_polys_M1 = defaultdict(list)
            for poly, label in zip(polygonsM1, labelsM1):
                labels_to_polys_M1[label].append(poly)
            
            # Only create M1 rows if we actually have M1 labels
            for label, polys in labels_to_polys_M1.items():
                new_row = row.copy()
                new_row["File"] = f"{file_name}|{label}"
                new_row["Root"] = file_name
                new_row["Net"] = label
                new_row["Polygons_M1"] = polys
                expanded_rows.append(new_row)
    
    # Create a new DataFrame from the expanded rows
    expanded_df = pd.DataFrame(expanded_rows)
    
    # Reset index if needed
    expanded_df.reset_index(drop=True, inplace=True)
    return expanded_df

def validate_and_handle_columns(df, required_columns, isGAA=False):
    """Validates and handles missing columns in the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame.
        required_columns (list): List of required columns.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        pd.DataFrame: DataFrame with validated and handled columns.
    """
    for col in required_columns:
        if col not in df.columns:
            df[col] = np.nan

    # Handle M1 for GAA: Ensure M1 columns exist and are zero-filled if missing
    if isGAA:
        if 'Polygons_M1' not in df.columns:
            df['Polygons_M1'] = [[(0.0,0.0,0.0,0.0)]] * len(df)
        if 'M1_Layer_Label' not in df.columns:
            df['M1_Layer_Label'] = np.nan

    final_cols = ['File'] + required_columns + ['M0_Layer_Label', 'M2_Layer_Label']
    if isGAA:
        final_cols.append('M1_Layer_Label')
    
    final_df = df.reindex(columns=final_cols, copy=False)
    return final_df

# -------------------------------
# Data Pivoting
# -------------------------------

def pivot_dataframe(test, accepted_layers, isGAA=False):
    """Pivots the DataFrame to organize data by layers.

    Args:
        test (pd.DataFrame): Input DataFrame.
        accepted_layers (list): List of accepted layers.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        pd.DataFrame: Pivoted DataFrame.
    """
    if isGAA and 'M1' not in accepted_layers:
        accepted_layers.append('M1')

    # Filter rows from df2 based on accepted_layers
    test['Polygons'] = test['Polygons'].apply(lambda x: deep_literal_eval(x))

    files = test['File'].unique()
    multi_index = pd.MultiIndex.from_product([files, accepted_layers], names=['File', 'Layer'])

    # Convert the multi-index to a dataframe
    temp_df = pd.DataFrame(index=multi_index).reset_index()

    mux_polygons_df = pd.merge(temp_df, test, on=['File', 'Layer'], how='left')

    indexed_df = mux_polygons_df.set_index(['File', 'Layer'])['F2F Total Length (µm)']
    pivoted_df = indexed_df.unstack()

    # Ensure all expected columns are present in the pivoted DataFrame
    for col in accepted_layers:
        if col not in pivoted_df.columns:
            pivoted_df[col] = -1

    # Order columns based on the expected relationships
    pivoted_df = pivoted_df[accepted_layers]

    # Convert each row to list to get the f2f_vector
    feature_df = pivoted_df.reset_index()
    feature_df['f2f_vector'] = feature_df[accepted_layers].fillna(-1).values.tolist()
    feature_df = feature_df[['File', 'f2f_vector']]

    df1 = mux_polygons_df.fillna('placeholder')
    pivot_permutated = pd.pivot_table(df1, index='File', columns='Layer',
                        values=['Total Polygon Area (µm²)', 'Density (%)',
                                'Total Polygon Length (µm)', 'Number of Polygons', 'Polygons'],
                        aggfunc={'Total Polygon Area (µm²)': lambda x: x,
                                'Density (%)': lambda x: x,
                                'Total Polygon Length (µm)': lambda x: x,
                                'Number of Polygons': lambda x: x,
                                'Polygons': lambda x: x})
    
    # Modify column naming to avoid double 'Polygons_' prefix
    pivot_permutated.columns = [
        'Polygons_' + col[1] if col[0] == 'Polygons' else '_'.join(col).strip() 
        for col in pivot_permutated.columns.values
    ]
    
    pivot_permutated.replace('placeholder', np.nan, inplace=True)
    pivot_permutated = pivot_permutated.infer_objects(copy=False)

    pivot_permutated = pivot_permutated.reset_index()
    polygon_columns = [col for col in pivot_permutated.columns if col.startswith("Polygons_")]
    m0_layer_labels = mux_polygons_df[mux_polygons_df['Layer'] == 'M0'][['File', 'Labels']]
    m2_layer_labels = mux_polygons_df[mux_polygons_df['Layer'] == 'M2_BACKSIDE_POWER_LINES'][['File', 'Labels']]
    
    file_to_m0_label = m0_layer_labels.set_index('File')['Labels'].to_dict()
    file_to_m2_label = m2_layer_labels.set_index('File')['Labels'].to_dict()
    
    pivot_permutated['M0_Layer_Label'] = pivot_permutated['File'].map(file_to_m0_label)
    pivot_permutated['M2_Layer_Label'] = pivot_permutated['File'].map(file_to_m2_label)

    if isGAA:
        m1_layer_labels = mux_polygons_df[mux_polygons_df['Layer'] == 'M1'][['File', 'Labels']]
        if len(m1_layer_labels) > 0:
            file_to_m1_label = m1_layer_labels.set_index('File')['Labels'].to_dict()
            pivot_permutated['M1_Layer_Label'] = pivot_permutated['File'].map(file_to_m1_label)
        else:
            pivot_permutated['M1_Layer_Label'] = np.nan
            if 'Polygons_M1' not in pivot_permutated.columns:
                pivot_permutated['Polygons_M1'] = pd.Series([[(0.0,0.0,0.0,0.0)]] * len(pivot_permutated))

    return pivot_permutated

# -------------------------------
# Data Loading and Preprocessing
# -------------------------------

def load_and_preprocess_data(input_path, required_columns, isGAA=False):
    """Loads and preprocesses data from a file or DataFrame.

    Args:
        input_path (str or pd.DataFrame): Path to the input file or a DataFrame.
        required_columns (list): List of required columns.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        pd.DataFrame: Preprocessed DataFrame.
    """
    if isinstance(input_path, str):
        data = pd.read_csv(input_path)
    elif isinstance(input_path, pd.DataFrame):
        data = input_path
    else:
        raise ValueError("input_data should be either a CSV file path or a pandas DataFrame.")
    
    # Remove the 'Polygons_' prefix from required_columns if it exists
    cleaned_required_columns = [col.replace('Polygons_', '') for col in required_columns]
    current_cells_accepted_layers = data.Layer.unique().tolist()
    pivoted_df = pivot_dataframe(data, current_cells_accepted_layers, isGAA=isGAA)
    # Add 'Polygons_' prefix only once during validation
    columns_with_prefix = [f'Polygons_{col}' if not col.startswith('Polygons_') else col 
                          for col in cleaned_required_columns]
    
    validated_df = validate_and_handle_columns(pivoted_df, columns_with_prefix, isGAA=isGAA)
    return validated_df

def preprocess_data_training_ae(data, required_columns=None, memmap_file=None, return_df=False, isGAA=False):
    """Preprocesses data for training an autoencoder.

    Args:
        data (pd.DataFrame): Input data.
        required_columns (list, optional): List of required columns. Defaults to None.
        memmap_file (str, optional): Path to memory-mapped file. Defaults to None.
        return_df (bool, optional): Whether to return the DataFrame. Defaults to False.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        torch.Tensor: Preprocessed spatial features as a PyTorch tensor.
        pd.DataFrame, optional: Expanded DataFrame if return_df is True.
    """
    polygon_columns = required_columns
    validated_df = load_and_preprocess_data(data, polygon_columns, isGAA=isGAA)
    expanded_df = extract_and_expand(validated_df, isGAA=isGAA)
    
    if memmap_file:
        spatial_features = convert_to_spatial_memmap(expanded_df, memmap_file)
    else:
        spatial_features = convert_to_spatial(expanded_df, polygon_columns)
        spatial_features = torch.tensor(spatial_features).float().permute(0, 3, 1, 2)
    
    if return_df:
        return spatial_features, expanded_df
    else:
        return spatial_features

def convert_to_spatial_memmap(spatial_features_raw, memmap_file, grid_size=64, batch_size=1000):
    """Converts spatial features to a memory-mapped array.

    Args:
        spatial_features_raw (pd.DataFrame): Raw spatial features.
        memmap_file (str): Path to memory-mapped file.
        grid_size (int, optional): Size of the grid. Defaults to 64.
        batch_size (int, optional): Batch size for processing. Defaults to 1000.

    Returns:
        np.memmap: Memory-mapped array of spatial features.
    """
    polygon_columns = [col for col in spatial_features_raw.columns if col.startswith("Polygons_")]
    columns_to_drop = ['File', 'M0_Layer_Label', 'Root', 'Net']
    existing_columns_to_drop = [col for col in columns_to_drop if col in spatial_features_raw.columns]
    spatial_features_raw = spatial_features_raw.drop(columns=existing_columns_to_drop)
    # Initialize memory-mapped array to store results
    num_samples = spatial_features_raw.shape[0]
    num_columns = len(polygon_columns)
    spatial_memmap = np.memmap(memmap_file, dtype='float32', mode='w+', shape=(num_samples, grid_size, grid_size, num_columns))

    # Process in batches
    for i in range(0, num_samples, batch_size):
        batch = spatial_features_raw.iloc[i:i+batch_size]

        # Convert bounding boxes to grids for each sample in the batch
        spatial_grids_batch = batch[polygon_columns].applymap(lambda boxes: bounding_boxes_to_grid(boxes, grid_size))

        # Convert the batch to a NumPy array
        spatial_array_batch = np.stack(spatial_grids_batch[polygon_columns].applymap(
            lambda grid: grid.reshape((grid_size, grid_size, 1))
        ).values.flatten())
        spatial_array_batch = spatial_array_batch.reshape(-1, grid_size, grid_size, num_columns)

        # Write the batch to the memory-mapped array
        spatial_memmap[i:i+batch_size] = spatial_array_batch

    # Ensure data is flushed to disk
    spatial_memmap.flush()

    return spatial_memmap

def load_label_data(input_path):
    """Loads label data from a CSV file.

    Args:
        input_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded label data.
    """
    data = pd.read_csv(input_path)
    return data

def extract_and_expand_clustering(whole_train_data, isGAA=False):
    """Extracts and expands polygon data for clustering.

    Args:
        whole_train_data (pd.DataFrame): Input training data.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        pd.DataFrame: Expanded DataFrame with polygon data.
    """
    polygon_columns = [col for col in whole_train_data.columns if col.startswith("Polygons_")]
    polygon_cols_with_file_label = polygon_columns.copy()
    for col in polygon_columns:
        whole_train_data[col] = fill_polygon_nan(whole_train_data[col])
    polygon_cols_with_file_label.insert(0, "File")
    polygon_cols_with_file_label.append('M0_Layer_Label')
    whole_train_data_spatial = whole_train_data[polygon_cols_with_file_label]
    return whole_train_data_spatial

def find_common_layers(metrics_folder):
    """Finds common layers across multiple CSV files in a folder.

    Args:
        metrics_folder (str): Path to the folder containing CSV files.

    Returns:
        list: Sorted list of common layers.
    """
    layers_sets = extract_unique_layers(metrics_folder)
    common_layers = set.intersection(*layers_sets)
    return sorted(list(common_layers))

def numpize(data, scaler):
    """Transforms data using a scaler.

    Args:
        data (array-like): Data to transform.
        scaler (object): Scaler object with a transform method.

    Returns:
        np.ndarray: Transformed data.
    """
    nparray = scaler.transform(data)
    return nparray

def preprocess_data_training_clustering_ae(input_path, required_columns, memmap_file=None, return_df=False, isGAA=False):
    """Preprocesses data for training an autoencoder for clustering.

    Args:
        input_path (str or pd.DataFrame): Path to the input file or a DataFrame.
        required_columns (list): List of required columns.
        memmap_file (str, optional): Path to memory-mapped file. Defaults to None.
        return_df (bool, optional): Whether to return the DataFrame. Defaults to False.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        torch.Tensor: Preprocessed spatial features as a PyTorch tensor.
        pd.DataFrame, optional: Expanded DataFrame if return_df is True.
    """
    validated_df = load_and_preprocess_data(input_path, required_columns, isGAA=isGAA)
    expanded_df = extract_and_expand_clustering(validated_df, isGAA=isGAA)
    if memmap_file:
        spatial_features = convert_to_spatial_memmap(expanded_df, memmap_file)
    else:
        spatial_features = convert_to_spatial(expanded_df, required_columns)
        spatial_features = torch.tensor(spatial_features).float().permute(0, 3, 1, 2)
    
    if return_df:
        return spatial_features, expanded_df.reset_index(drop=True)
    else:
        return spatial_features

def extract_unique_layers(metrics_folder):
    """Extracts unique layers from CSV files in a folder.

    Args:
        metrics_folder (str): Path to the folder containing CSV files.

    Returns:
        list: List of sets, each containing unique layers from a file.
    """
    csv_files = glob.glob(os.path.join(metrics_folder, '*.csv'))
    layers_sets = []

    for csv_file in csv_files:
        data = pd.read_csv(csv_file)
        unique_layers = set(data['Layer'].unique())
        layers_sets.append(unique_layers)

    return layers_sets

def preprocess_data_training_moe(input_path, required_columns, label_data_path, isGAA=False):
    """Preprocesses data for training a mixture of experts (MoE) model.

    Args:
        input_path (str or pd.DataFrame): Path to the input file or a DataFrame.
        required_columns (list): List of required columns.
        label_data_path (str): Path to the label data file.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        torch.Tensor: Preprocessed spatial features as a PyTorch tensor.
        pd.DataFrame: Filtered label data.
        pd.Series: File names.
    """
    validated_df = load_and_preprocess_data(input_path, required_columns, isGAA=isGAA)
    label_df = load_label_data(label_data_path)
    
    if 'File' not in label_df.columns or 'Capacitance' not in label_df.columns:
        raise ValueError("Label DataFrame must contain 'File' and 'Capacitance' columns.")
    if label_df.empty:
        raise ValueError("Label DataFrame is empty.")
    
    expanded_df = extract_and_expand(validated_df, isGAA=isGAA)
    common_files = pd.merge(expanded_df[['File']], label_df[['File']], on='File')['File']

    filteredX = expanded_df[expanded_df['File'].isin(common_files)].sort_values('File').reset_index(drop=True)
    filteredY = label_df[label_df['File'].isin(common_files)].sort_values('File').reset_index(drop=True)
    file_names_df = filteredX['File']
    spatial_features = convert_to_spatial(filteredX, required_columns)
    spatial_features = torch.tensor(spatial_features).float().permute(0, 3, 1, 2)
    return spatial_features, filteredY, file_names_df

def preprocess_data_training_gnn(input_path, required_columns, label_data_path, isGAA=False):
    """Preprocesses data for training a graph neural network (GNN).

    Args:
        input_path (str or pd.DataFrame): Path to the input file or a DataFrame.
        required_columns (list): List of required columns.
        label_data_path (str): Path to the label data file.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        torch.Tensor: Preprocessed spatial features as a PyTorch tensor.
        pd.DataFrame: Filtered label data.
        pd.Series: File names.
    """
    validated_df = load_and_preprocess_data(input_path, required_columns, isGAA=isGAA)
    label_df = load_label_data(label_data_path)
    
    if 'File' not in label_df.columns or not any('_to_' in col for col in label_df.columns if col != 'File'):
        raise ValueError("Label DataFrame must contain 'File' column and at least one 'xx_to_xx' column.")
    if label_df.empty:
        raise ValueError("Label DataFrame is empty.")
    
    common_files = pd.merge(validated_df[['File']], label_df[['File']], on='File')['File']
    filteredX_via_common_files = validated_df[validated_df['File'].isin(common_files)].sort_values('File').reset_index(drop=True)
    filteredY_via_common_files = label_df[label_df['File'].isin(common_files)].sort_values('File').reset_index(drop=True)

    expanded_df = extract_and_expand(filteredX_via_common_files, isGAA=isGAA)
    expanded_label_file_column = expand_file_with_nets(filteredY_via_common_files)

    common_files_expanded = pd.merge(expanded_df, expanded_label_file_column, on='File')

    filteredX = expanded_df[expanded_df['File'].isin(common_files_expanded['File'])]

    file_names_df = filteredX['File']
    spatial_features = convert_to_spatial(filteredX, required_columns)
    spatial_features = torch.tensor(spatial_features).float().permute(0, 3, 1, 2)
    return spatial_features, filteredY_via_common_files, file_names_df

# -------------------------------
# Net Name Expansion for GNN
# -------------------------------

def find_unique_net_names(label_df):
    """Finds unique net names from label DataFrame.

    Args:
        label_df (pd.DataFrame): Label DataFrame.

    Returns:
        list: Sorted list of unique net names.
    """
    net_list = label_df.drop(columns=['File']).columns.tolist()
    nets = set()
    for connection in net_list:
        net1, net2 = connection.split('_to_')
        nets.add(net1)
        nets.add(net2)

    unique_nets = sorted(nets)

    return unique_nets

def expand_file_with_nets(label_df):
    """Expands the File column with unique net names.

    Args:
        label_df (pd.DataFrame): Label DataFrame.

    Returns:
        pd.DataFrame: DataFrame with expanded file names.
    """
    unique_nets = find_unique_net_names(label_df)
    
    expanded_file_list = []
    
    for file_name in label_df['File']:
        expanded_files = [f"{file_name}_{net}" for net in unique_nets]
        expanded_file_list.extend(expanded_files)
    
    expanded_df = pd.DataFrame(expanded_file_list, columns=['File'])
    
    return expanded_df

# -------------------------------
# Data Loading - For Main
# -------------------------------

def load_data(input_data):
    """Loads data from a CSV file.

    Args:
        input_data (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded data.
    """
    data = pd.read_csv(input_data)
    return data

def load_data(input_path, file_format, **kwargs):
    """Loads data from the specified path into a pandas DataFrame.

    Args:
        input_path (str): Path to the input file.
        file_format (str): Format of the file ('csv', 'json', 'excel', etc.).
        **kwargs: Additional keyword arguments to pass to the pandas read function.

    Returns:
        pd.DataFrame: Loaded DataFrame.

    Raises:
        ValueError: If the specified file format is not supported.
    """
    # Supported file formats
    supported_formats = {'csv', 'json', 'excel'}

    # Convert file_format to lowercase to handle case insensitivity
    file_format = file_format.lower()

    if file_format not in supported_formats:
        raise ValueError(f"Unsupported file format: {file_format}. Supported formats are: {supported_formats}")

    # Load data based on the file format
    if file_format == 'csv':
        return pd.read_csv(input_path, **kwargs)
    elif file_format == 'json':
        return pd.read_json(input_path, **kwargs)
    elif file_format == 'excel':
        return pd.read_excel(input_path, **kwargs)
    else:
        # This should not be reached because of the earlier check
        raise ValueError(f"Unsupported file format: {file_format}. Supported formats are: {supported_formats}")

