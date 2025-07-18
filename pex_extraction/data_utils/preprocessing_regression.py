"""
This module provides functions for preprocessing data for regression tasks using graph neural networks (GNNs).
It includes utilities for normalizing node names, extracting unique nodes, creating graph data for training and inference,
and loading CSV data.

Functions:
- normalize_name: Normalizes a name by removing special characters and converting to uppercase.
- extract_unique_nodes: Extracts unique nodes from embeddings and target DataFrames.
- create_graph_data_for_training: Creates graph data for training from embeddings and target DataFrames.
- create_graph_data_for_inference: Creates graph data for inference from embeddings DataFrame.
- gnn_train_from_embeddings_preprocessing: Preprocesses data for GNN training straight from embeddings.
- load_csv_data: Loads CSV data from a folder.
- gnn_train_preprocessing: Preprocesses data for GNN training.
"""

import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from sklearn.model_selection import train_test_split
import pandas as pd
import os
import re
import numpy as np

def normalize_name(name, is_inference=True):
    """Normalizes a name by removing all special characters and converting to uppercase.

    Args:
        name (str): The name to normalize.

    Returns:
        str: The normalized name.
    """
    if is_inference:
        return name
    normalized = re.sub(r'[^A-Za-z0-9]', '', name)
    return normalized.upper()

def extract_unique_nodes(embeddings_df, target_df):
    """Extracts unique nodes from embeddings and target DataFrames.

    Args:
        embeddings_df (pd.DataFrame): DataFrame containing node embeddings.
        target_df (pd.DataFrame): DataFrame containing target data.

    Returns:
        tuple: Filtered embeddings and target DataFrames.
    """
    node_names = []
    for _, row in target_df.iterrows():
        file_name = row['File']
        for column in target_df.columns[1:]:
            original_node1, original_node2 = column.split('_to_')

            # Normalize node names directly
            normalized_node1 = normalize_name(original_node1)
            normalized_node2 = normalize_name(original_node2)

            node1_name = file_name + "|" + normalized_node1
            node2_name = file_name + "|" + normalized_node2
            node_names.append(node1_name)
            node_names.append(node2_name)

    node_names = set(node_names)
    # Filter embeddings to include only relevant nodes
    filtered_embeddings_df = embeddings_df[embeddings_df['File'].isin(node_names)].reset_index(drop=True)

    # Identify valid files
    valid_files = set()
    for _, row in target_df.iterrows():
        file_name = row['File']
        is_valid = True
        for column in target_df.columns[1:]:
            original_node1, original_node2 = column.split('_to_')
            normalized_node1 = normalize_name(original_node1)
            normalized_node2 = normalize_name(original_node2)
            node1_name = f"{file_name}_{normalized_node1}"
            node2_name = f"{file_name}_{normalized_node2}"
            if (node1_name not in filtered_embeddings_df['File'].values) or (node2_name not in filtered_embeddings_df['File'].values):
                is_valid = False
                break
        if is_valid:
            valid_files.add(file_name)

    filtered_target_df = target_df[target_df['File'].isin(valid_files)].reset_index(drop=True)

    return filtered_embeddings_df, filtered_target_df

def create_graph_data_for_training(embedding_df, target_df, isGAA=False):
    """Creates graph data for training from embeddings and target DataFrames.

    Args:
        embedding_df (pd.DataFrame): DataFrame containing node embeddings.
        target_df (pd.DataFrame): DataFrame containing target data.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        list: List of graph data objects for training.
    """
    graph_data_list = []

    for index, row in target_df.iterrows():
        file_name = row['File']
        node_set = set()

        # Collect unique node names from the columns
        for column in target_df.columns[1:]:
            original_node1, original_node2 = column.split('_to_')
            node_set.update([original_node1, original_node2])

        # Normalize and sort node names
        node_names_normalized = sorted([normalize_name(n) for n in node_set])

        # Map node names to indices
        node_name_to_index = {n: idx for idx, n in enumerate(node_names_normalized)}

        # Collect node features
        node_features = []
        for n in node_names_normalized:
            node_name_full = file_name + "|" + n
            embeddings_found = embedding_df.loc[embedding_df['File'] == node_name_full, 'Encoded_Data']

            if embeddings_found.empty:
                continue  # Skip if the embedding is missing

            if isGAA and len(embeddings_found) > 1:
                # If multiple embeddings exist and isGAA=True, average them
                arrs = [np.array(e) for e in embeddings_found]
                merged = np.mean(arrs, axis=0)
                node_feature = torch.tensor(merged, dtype=torch.float)
            else:
                # Original behavior (no merging)
                node_feature = torch.tensor(embeddings_found.values[0], dtype=torch.float)

            node_features.append(node_feature)

        if not node_features:
            continue  # Skip if no node features are collected

        node_features = torch.stack(node_features)

        # Create fully connected edges
        num_nodes = len(node_names_normalized)
        edge_index = []
        edge_labels = []
        edge_mask = []

        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                n1 = node_names_normalized[i]
                n2 = node_names_normalized[j]
                edge_index.append([i, j])

                # Check if a label exists for this edge
                label_key_1 = f"{n1}_to_{n2}"
                label_key_2 = f"{n2}_to_{n1}"
                if label_key_1 in target_df.columns:
                    edge_labels.append(row[label_key_1])
                    edge_mask.append(1)
                elif label_key_2 in target_df.columns:
                    edge_labels.append(row[label_key_2])
                    edge_mask.append(1)
                else:
                    edge_labels.append(0.0)  # Placeholder label
                    edge_mask.append(0)      # Edge without label

        # Convert to tensors
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_labels = torch.tensor(edge_labels, dtype=torch.float)
        edge_mask = torch.tensor(edge_mask, dtype=torch.bool)

        graph_data = Data(x=node_features, edge_index=edge_index, y=edge_labels, edge_mask=edge_mask)
        graph_data_list.append(graph_data)

    return graph_data_list

def create_graph_data_for_inference(embedding_df, isGAA=False):
    """Creates graph data for inference from embeddings DataFrame.

    Args:
        embedding_df (pd.DataFrame): DataFrame containing node embeddings.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        tuple: Updated embeddings DataFrame, list of graph data objects, list of prediction columns, and list of files.
    """
    graph_data_list = []
    prediction_columns_list = []
    
    # Create a mapping between normalized and original names
    name_mapping = {}
    for original_name in embedding_df['Net_Name']:
        normalized_name = normalize_name(original_name)
        name_mapping[normalized_name] = original_name

    # Extract FilePrefix and group by it
    files = embedding_df['FilePrefix'].unique()

    # Add normalized names to the dataframe but keep original names
    embedding_df['Normalized_Net_Name'] = embedding_df['Net_Name'].apply(normalize_name)

    for file_name in files:
        file_group = embedding_df[embedding_df['FilePrefix'] == file_name]
        
        # Use normalized names for ordering
        node_names_normalized = sorted(file_group['Normalized_Net_Name'].unique().tolist())
        
        node_features = []
        valid_indices = []  # Keep track of valid indices for edge creation
        
        for idx, normalized_name in enumerate(node_names_normalized):
            original_name = name_mapping[normalized_name]
            # There might be multiple embeddings for the same net in the inference set as well
            embeddings_found = file_group.loc[file_group['Net_Name'] == original_name, 'Encoded_Data']

            if embeddings_found.empty:
                continue

            if isGAA and len(embeddings_found) > 1:
                # If multiple embeddings exist and isGAA=True, average them
                arrs = [np.array(e) for e in embeddings_found]
                merged = np.mean(arrs, axis=0)
                node_feature = torch.tensor(merged, dtype=torch.float)
            else:
                # Original behavior
                node_feature = torch.tensor(embeddings_found.values[0], dtype=torch.float)

            node_features.append(node_feature)
            valid_indices.append(idx)

        if not node_features:
            continue

        node_features = torch.stack(node_features)

        # Create edges between all possible pairs using valid indices
        edge_index = []
        prediction_columns = []

        for i_idx, i in enumerate(valid_indices):
            for j_idx, j in enumerate(valid_indices[i_idx + 1:], i_idx + 1):
                edge_index.append([i_idx, j_idx])
                
                # Use original names for prediction columns
                orig_name_i = name_mapping[node_names_normalized[i]]
                orig_name_j = name_mapping[node_names_normalized[j]]
                prediction_columns.append(f'{orig_name_i}_to_{orig_name_j}')

        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        graph_data = Data(x=node_features, edge_index=edge_index)
        graph_data_list.append(graph_data)
        prediction_columns_list.append(prediction_columns)

    return embedding_df, graph_data_list, prediction_columns_list, files

def gnn_train_from_embeddings_preprocessing(embeddings_df, y_dict, isGAA=False):
    """Preprocesses data for GNN training from embeddings.

    Args:
        embeddings_df (pd.DataFrame): DataFrame containing node embeddings.
        y_dict (dict): Dictionary of target DataFrames.
        isGAA (bool, optional): Whether to handle GAA-specific logic. Defaults to False.

    Returns:
        tuple: Dictionaries of training, testing, and full graph data, and a dictionary of filtered target DataFrames.
    """
    graph_data_dict_train = {}
    graph_data_dict_test = {}
    graph_data_dict_full = {}
    dfkeeper = {}
    for key, df in y_dict.items():
        key_embeddings_df = embeddings_df[embeddings_df['File'].str.startswith(key)]
        if key_embeddings_df.empty:
            print(f"No matching embeddings found for key: {key}")
            continue
        else:
            print(f"Matching embeddings found for key: {key}")

        # Now extract_unique_nodes returns filtered embeddings and target dfs
        filtered_embeddings_df, filtered_target_df = extract_unique_nodes(key_embeddings_df, df)
        
        print(f"Filtered embeddings: {filtered_embeddings_df.head()}")
        print(f"Filtered target: {filtered_target_df.head()}")

        # Create graph data list
        graph_data_list = create_graph_data_for_training(filtered_embeddings_df, filtered_target_df, isGAA=isGAA)

        train_data_list, test_data_list = train_test_split(graph_data_list, test_size=0.2, random_state=42)
        graph_data_dict_train[key] = train_data_list
        graph_data_dict_test[key] = test_data_list
        graph_data_dict_full[key] = graph_data_list
        dfkeeper[key] = filtered_target_df

    return graph_data_dict_train, graph_data_dict_test, graph_data_dict_full, dfkeeper

def load_csv_data(folder_path, M0_only=False):
    """Loads CSV data from a folder, using the file name to create variable names.

    Args:
        folder_path (str): Path to the folder containing CSV files.
        M0_only (bool, optional): Whether to exclude VDD and VSS columns. Defaults to False.

    Returns:
        dict: Dictionary of DataFrames keyed by variable names extracted from file names.
    """
    data_dict = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            filepath = os.path.join(folder_path, filename)
            # Extract variable name from the file name
            match = re.match(r"([A-Za-z0-9]+)", filename)
            if match:
                variable_name = match.group(1)
                df = pd.read_csv(filepath)
                df.columns = df.columns.str.replace("A254Block2", "A254")
                df.columns = df.columns.str.replace("A416Block2", "A416")
                if M0_only:
                    df = df.loc[:, ~df.columns.str.contains("VDD|VSS")]

                data_dict[variable_name] = df
            else:
                print(f"Could not extract variable name from {filename}")
    return data_dict

def gnn_train_preprocessing(embeddings_df, target_df):
    """Preprocesses data for GNN training.

    Args:
        embeddings_df (pd.DataFrame): DataFrame containing node embeddings.
        target_df (pd.DataFrame): DataFrame containing target data.

    Returns:
        tuple: Lists of training and testing graph data.
    """
    # Now extract_unique_nodes returns filtered embeddings and target dfs
    filtered_embeddings_df, filtered_target_df = extract_unique_nodes(embeddings_df, target_df)
    
    # Create graph data list without passing original_to_normalized_map
    graph_data_list = create_graph_data_for_training(filtered_embeddings_df, filtered_target_df)
    
    train_data_list, test_data_list = train_test_split(graph_data_list, test_size=0.2, random_state=42)
    
    return train_data_list, test_data_list
