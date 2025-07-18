"""Inference Module for Regression Models.

This module provides classes and functions for performing inference using trained regression models such as
Mixture of Experts (MoE) and Graph Neural Networks (GNN). It includes data preprocessing, model loading,
and prediction pipelines.
"""

import os
import gc
import json
import numpy as np
import pandas as pd
import platform
import tensorflow as tf
import joblib
import warnings
import pickle
import torch
import torch.nn as nn
import ast
from abc import ABC, abstractmethod
from torch_geometric.loader import DataLoader
from torch_geometric.nn import NNConv

from pex_extraction.data_utils.preprocessing_encoding import (
    extract_and_expand, convert_to_spatial_legacy, convert_to_spatial, numpize
)
from pex_extraction.data_utils.preprocessing_regression import (
    create_graph_data_for_inference, normalize_name
)
from pex_extraction.encoders.autoencoder_model import AutoencoderIncremental
from pex_extraction.encoders.encode_and_save import EncoderWrapper
from pex_extraction.regression.gnn_model import initGNN
from pex_extraction.data_utils.utils import (
    gnn_calculate_net_sum, gnn_json_to_dataframe, merge_equivalent_columns
)
import logging

logger = logging.getLogger('sivista_app')


class BaseModel(ABC):
    """Abstract Base Class for Regression Models.

    This class provides a template for different regression models and ensures consistent methods
    across models.
    """

    @abstractmethod
    def load_model(self):
        """Load the trained model from disk."""
        pass

    @abstractmethod
    def process_batches(self, validated_df, batch_size, output_path):
        """Process data in batches and perform inference.

        Args:
            validated_df (DataFrame): Validated input data.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.
        """
        pass

    @abstractmethod
    def run_pipeline(self, validated_df, batch_size, output_path):
        """Run the full inference pipeline.

        Args:
            validated_df (DataFrame): Validated input data.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.
        """
        pass

    @abstractmethod
    def save_results(self, data, output_path, validated_df):
        """Save inference results to disk.

        Args:
            data: Inference results data.
            output_path (str): Path to save output results.
            validated_df (DataFrame): Validated input data.
        """
        pass


class MoeModel(BaseModel):
    """Mixture of Experts (MoE) Model Class.

    This class handles loading, processing, and inference for the MoE model.

    Args:
        model_path (str): Path to the saved MoE model.
        encoder_path (str): Path to the saved encoder model.
        scaler_path (str): Path to the saved scaler.
        required_columns (list): List of required columns.
        M0_only (bool, optional): If True, only use M0 layer. Defaults to False.
        use_legacy_spatial (bool, optional): If True, use legacy spatial conversion. Defaults to False.
        isGAA (bool, optional): If True, indicates GAA technology. Defaults to False.
    """

    def __init__(
        self,
        model_path,
        encoder_path,
        scaler_path,
        required_columns,
        M0_only=False,
        use_legacy_spatial=False,
        isGAA=False,
    ):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.encoder_path = encoder_path

        self.model = None
        self.scaler = None
        self.required_columns = required_columns
        self.M0_only = M0_only
        self.use_legacy_spatial = use_legacy_spatial
        self.isGAA = isGAA

        # Configure TensorFlow to use GPU if available
        self.autoencoder = AutoencoderIncremental(num_channels=len(self.required_columns)).to(
            self.device
        )
        self.encoder = EncoderWrapper(self.autoencoder).to(self.device)
        if tf.config.list_physical_devices("GPU"):
            gpus = tf.config.list_physical_devices("GPU")
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        else:
            # Check for Apple Silicon and prompt for tensorflow-metal installation
            if platform.system() == "Darwin":
                pass
            else:
                pass

    @property
    def device(self):
        """Determine the device to use (GPU if available, else CPU).

        Returns:
            torch.device: The device to use for computations.
        """
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_model(self):
        """Load the MoE model and scaler."""
        # Load the encoder's state_dict
        self.encoder.load_state_dict(
            torch.load(self.encoder_path, map_location=torch.device("cpu"))
        )
        self.encoder.eval()
        # Load the Keras MoE model
        self.model = tf.keras.models.load_model(self.model_path, safe_mode=False)
        # Load the scaler
        self.scaler = joblib.load(self.scaler_path)

    def predict(self, data):
        """Make predictions using the MoE model.

        Args:
            data (ndarray): Input data for prediction.

        Returns:
            ndarray: Predicted capacitance values.
        """
        # Scale the data using the scaler
        scaled_data = numpize(data, self.scaler)
        # Make predictions using the loaded MoE model
        return self.model.predict(scaled_data).flatten().astype(np.float64)

    def process_batches(self, validated_df, encoder, batch_size, output_path):
        """Process data in batches and make predictions using the MoE model.

        Args:
            validated_df (DataFrame): Validated input data.
            encoder (nn.Module): Encoder model to generate embeddings.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.

        Returns:
            list: List of DataFrames containing predictions.
        """
        num_batches = int(np.ceil(len(validated_df) / batch_size))
        dfs = []
        for batch_idx in range(num_batches):
            print(f"Processing batch {batch_idx + 1}/{num_batches}")
            batch = validated_df.iloc[
                batch_idx * batch_size : (batch_idx + 1) * batch_size
            ]
            # Convert to spatial and encode data
            expanded = extract_and_expand(
                batch, M0_only=self.M0_only, isGAA=self.isGAA
            )
            if self.use_legacy_spatial:
                full_spatial_np = convert_to_spatial_legacy(
                    expanded, self.required_columns
                )
            else:
                full_spatial_np = convert_to_spatial(expanded, self.required_columns)
            full_spatial = (
                torch.tensor(full_spatial_np).float().permute(0, 3, 1, 2)
            )  # Shape: [batch_size, channels, height, width]
            self.encoder.eval()
            with torch.no_grad():
                encoded_data = encoder(full_spatial)
            # Move encoded data to CPU for Keras prediction
            encoded_data_np = encoded_data.numpy()
            # Predict using the MoE model
            predictions = self.predict(encoded_data_np)
            # Postprocessing: prepare for output
            file_col = pd.DataFrame(expanded[["File", "Root", "Net"]])
            indexed_results = pd.concat(
                [file_col, pd.DataFrame({"Capacitance": predictions})], axis=1
            )
            pivot_df = (
                indexed_results.pivot(index="Root", columns="Net", values="Capacitance")
                .fillna(0)
                .reset_index()
            )
            pivot_df.columns.name = None
            pivot_df.columns = ["File"] + list(pivot_df.columns[1:])
            dfs.append(pivot_df)
            # Free up memory
            torch.cuda.empty_cache()
            del (
                encoded_data,
                full_spatial,
                full_spatial_np,
                expanded,
                indexed_results,
                file_col,
                pivot_df,
            )
            gc.collect()
        return dfs

    def run_pipeline(self, validated_df, batch_size, output_path):
        """Run the full inference pipeline for the MoE model.

        Args:
            validated_df (DataFrame): Validated input data.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.

        Returns:
            list: List of DataFrames containing predictions.
        """
        self.load_model()
        return self.process_batches(validated_df, self.encoder, batch_size, output_path)

    def save_results(self, dfs, output_path, validated_df):
        """Postprocess and save the MoE model's results.

        Args:
            dfs (list): List of DataFrames containing predictions.
            output_path (str): Path to save output results.
            validated_df (DataFrame): Validated input data.
        """
        final_df = pd.concat(dfs, ignore_index=True)
        final_df.fillna(0, inplace=True)
        final_df["Capacitance Sum"] = final_df.iloc[:, 1:].sum(axis=1)
        cell_area_df = validated_df[
            validated_df["Layer"] == "CELL_BOUNDARY"
        ][
            ["File", "Total Polygon Area (µm²)"]
        ]
        cell_area_df = cell_area_df.rename(columns={"Total Polygon Area (µm²)": "Cell Area (µm²)"})
        
        cell_df = validated_df[
            validated_df["Layer"] == "CELL_BOUNDARY"
        ][
            ["File", "Polygons"]
        ]
        cell_df['Cell Height (µm)'] = cell_df['Polygons'].apply(find_cell_height)
        cell_df['Cell Width (µm)'] = cell_df['Polygons'].apply(find_cell_width)
        cell_df.drop(columns=['Polygons'], inplace=True)

        validated_df = validated_df[
            ["File", "F2F Total Length (µm)", "Total Polygon Area (µm²)", "Total Polygon Length (µm)"]
        ]
        validated_df = validated_df.groupby("File", as_index=False)[
            ["F2F Total Length (µm)", "Total Polygon Area (µm²)", "Total Polygon Length (µm)"]
        ].sum()
        final_df = pd.merge(final_df, validated_df, left_on="File", right_on="File")
        final_df = pd.merge(final_df, cell_area_df, left_on="File", right_on="File")
        final_df = pd.merge(final_df, cell_df, left_on="File", right_on="File")
        final_df['ID'] = range(1, len(final_df) + 1)  # Adds ID as the last column
        final_df.to_csv(output_path, index=False)
        print(f"MoE results saved to {output_path}")


from torch_geometric.data import Data
from torch_geometric.loader import DataLoader


class GNNModel(BaseModel):
    """Graph Neural Network (GNN) Model Class.

    This class handles loading, processing, and inference for the GNN model.

    Args:
        gnn_path (str): Path to the saved GNN model.
        encoder_path (str): Path to the saved encoder model.
        scaler_path (str): Path to the saved scaler.
        required_columns (list): List of required columns.
        model_init_params (str): Path to the model initialization parameters.
        M0_only (bool, optional): If True, only use M0 layer. Defaults to False.
        use_legacy_spatial (bool, optional): If True, use legacy spatial conversion. Defaults to False.
        isGAA (bool, optional): If True, indicates GAA technology. Defaults to False.
    """

    def __init__(
        self,
        gnn_path,
        encoder_path,
        scaler_path,
        required_columns,
        model_init_params,
        M0_only=False,
        use_legacy_spatial=False,
        isGAA=False,
    ):
        self.model_path = gnn_path
        self.model = None
        self.scalar_path = scaler_path
        self.encoder_path = encoder_path
        self.model_init_params = model_init_params

        self.required_columns = required_columns
        self.M0_only = M0_only
        self.use_legacy_spatial = use_legacy_spatial
        self.isGAA = isGAA
        print(f"Performing GAA PEX: {self.isGAA}")
        # Prioritize CUDA, fall back to CPU if CUDA is not available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize the Autoencoder and EncoderWrapper
        num_channels = len(self.required_columns)
        self.autoencoder = AutoencoderIncremental(
            num_channels=num_channels
        ).to(self.device)
        self.encoder = EncoderWrapper(self.autoencoder).to(self.device)
        self.embedding_dim = 2312

    def load_model(self):
        """Load the GNN model and associated components."""
        # Load hyperparameters
        with open(self.model_init_params, "rb") as f:
            best_params = pickle.load(f)
        logger.debug(f"Loaded hyperparameters: {best_params}")

        # Initialize the model with the best parameters
        self.model = initGNN(
            self.embedding_dim, best_params, self.model_path, self.device
        ).to(self.device)
        logger.debug(f"GNN model loaded from {self.model_path}.")

        # Load pre-trained weights into the Autoencoder
        self.autoencoder.load_state_dict(
            torch.load(self.encoder_path, map_location=self.device)
        )
        self.autoencoder.eval()

    def predict(self, embeddings_df):
        """Make predictions using the GNN model.

        Args:
            embeddings_df (DataFrame): DataFrame containing encoded embeddings.

        Returns:
            tuple: file_df, predictions, prediction_columns_list
        """
        # Generate inference graph data
        (
            file_df,
            inference_graph_data_list,
            prediction_columns_list,
            files,
        ) = create_graph_data_for_inference(embeddings_df, isGAA=self.isGAA)

        inference_loader = DataLoader(inference_graph_data_list, batch_size=1, shuffle=False)
        self.model.eval()

        predictions = []

        with torch.no_grad():
            for data in inference_loader:
                data = data.to(self.device)

                # Generate edge attributes if required by the model
                if isinstance(self.model.convs[0], NNConv):
                    row, col = data.edge_index
                    data.edge_attr = (data.x[row] - data.x[col]).abs()
                else:
                    pass  # Edge attributes not required for other conv types

                prediction = self.model(data)
                predictions.append(prediction.cpu().numpy().flatten())

        return file_df, predictions, prediction_columns_list

    def process_batches(self, validated_df, batch_size, output_path, capsum=False):
        """Process data in batches and make predictions using the GNN model.

        Args:
            validated_df (DataFrame): Validated input data.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.
            capsum (bool, optional): If True, returns the sum of capacitances for each net. Defaults to False.

        Returns:
            DataFrame: DataFrame containing prediction results.
        """
        num_batches = int(np.ceil(len(validated_df) / batch_size))
        gnn_file_cols = []
        gnn_node_embeddings = []
        for batch_idx in range(num_batches):
            logger.debug(f"Processing batch {batch_idx + 1}/{num_batches}")
            batch = validated_df.iloc[
                batch_idx * batch_size : (batch_idx + 1) * batch_size
            ]
            # Convert to spatial and encode data
            expanded = extract_and_expand(
                batch, M0_only=self.M0_only, isGAA=self.isGAA
            )
            if self.use_legacy_spatial:
                full_spatial_np = convert_to_spatial_legacy(
                    expanded, self.required_columns
                )
            else:
                full_spatial_np = convert_to_spatial(expanded, self.required_columns)
            full_spatial = (
                torch.tensor(full_spatial_np).float().permute(0, 3, 1, 2).to(self.device)
            )
            self.encoder.eval()
            with torch.no_grad():
                encoded_data = self.encoder(full_spatial)
            gnn_file_cols.append(expanded[["File"]])
            gnn_node_embeddings.append(encoded_data.cpu().numpy().tolist())
            # Free up memory
            del (
                encoded_data,
                full_spatial,
                full_spatial_np,
                expanded,
            )
            gc.collect()
        all_file_col = pd.concat(gnn_file_cols, axis=0, ignore_index=True)

        all_node_embeddings = np.stack(
            [array for chunk in gnn_node_embeddings for array in chunk]
        ).tolist()
        encoded_df = pd.DataFrame({"Encoded_Data": all_node_embeddings})
        embeddings_df = pd.concat([all_file_col, encoded_df], axis=1)
        embeddings_df["Encoded_Data"] = embeddings_df["Encoded_Data"].apply(tuple)
        # Split File column into FilePrefix and Net_Name using the '|' separator
        file_parts = embeddings_df["File"].str.split("|")
        embeddings_df["FilePrefix"] = file_parts.str[:-1].str.join("_")
        embeddings_df["Net_Name"] = file_parts.str[-1:].str.join("_")

        file_df, predictions, prediction_columns_list = self.predict(embeddings_df)
        filenames = file_df["FilePrefix"].unique().tolist()
        data = {}
        for i, name in enumerate(filenames):
            data[name] = {
                "Net Pairs": prediction_columns_list[i],
                "Capacitance": predictions[i].tolist(),
            }
        gnn_df = gnn_json_to_dataframe(data)
        pivoted_df = gnn_df.pivot(
            index="Identifier", columns="Net Pair", values="Capacitance"
        )

        # Remove this line if you want to keep the NaNs should there be instance of input of multiple cells
        pivoted_df.fillna(0, inplace=True)

        pivoted_df.reset_index(inplace=True)
        gnn_df_net_to_net = merge_equivalent_columns(pivoted_df)
        gnn_df_net_to_net.rename(columns={"Identifier": "File"}, inplace=True)
        if capsum:
            net_names = set()
            for pair in gnn_df["Net Pair"]:
                net1, net2 = pair.split("_to_")
                net_names.add(net1)
                net_names.add(net2)
            gnn_df_individual_net = (
                gnn_df.groupby("Identifier")
                .apply(lambda group: gnn_calculate_net_sum(group, net_names))
                .reset_index()
            )
            cols_to_drop = [col for col in ['VDD','VCC','VSS','GND'] if col in gnn_df_individual_net.columns]
            if any(col in gnn_df_individual_net.columns for col in ['VDD', 'VCC']) and any(col in gnn_df_individual_net.columns for col in ['GND','VSS']):
                gnn_df_individual_net.drop(cols_to_drop, axis=1, inplace=True)
                
            rename_net_columns = {
               x:f'Cap_{x}' for x in gnn_df_individual_net.columns if x!='Identifier'
            }
            rename_net_columns["Identifier"] = "File"
            gnn_df_individual_net.rename(columns=rename_net_columns, inplace=True)
            return gnn_df_individual_net

        return gnn_df_net_to_net

    def run_pipeline(self, validated_df, batch_size, output_path, capsum=False):
        """Run the full inference pipeline for the GNN model.

        Args:
            validated_df (DataFrame): Validated input data.
            batch_size (int): Size of each data batch.
            output_path (str): Path to save output results.
            capsum (bool, optional): If True, returns the sum of capacitances for each net. Defaults to False.

        Returns:
            DataFrame: DataFrame containing prediction results.
        """
        self.load_model()
        return self.process_batches(
            validated_df, batch_size, output_path, capsum=capsum
        )

    def save_results(self, data, output_path, validated_df):
        """Postprocess and save the GNN model's results.

        Args:
            data (DataFrame): Prediction results data.
            output_path (str): Path to save output results.
            validated_df (DataFrame): Validated input data.
        """
        if isinstance(output_path, list):
            output_path = output_path[0]

        final_df = pd.DataFrame(data)
        final_df.fillna(0, inplace=True)
        final_df["Capacitance Sum"] = final_df.iloc[:, 1:].sum(axis=1)
        cell_area_df = validated_df[
            validated_df["Layer"] == "CELL_BOUNDARY"
        ][
            ["File", "Total Polygon Area (µm²)"]
        ]
        cell_area_df = cell_area_df.rename(columns={"Total Polygon Area (µm²)": "Cell Area (µm²)"})
        #TO-DO: Move calculation to -calculate_metrics.py
        cell_df = validated_df[
            validated_df["Layer"] == "CELL_BOUNDARY"
        ][
            ["File", "Polygons"]
        ]
        cell_df['Cell Height (µm)'] = cell_df['Polygons'].apply(find_cell_height)
        cell_df['Cell Width (µm)'] = cell_df['Polygons'].apply(find_cell_width)
        cell_df.drop(columns=['Polygons'], inplace=True)

        validated_df = validated_df[
            ["File", "F2F Total Length (µm)", "Total Polygon Area (µm²)", "Total Polygon Length (µm)"]
        ]
        validated_df = validated_df.groupby("File", as_index=False)[
            ["F2F Total Length (µm)", "Total Polygon Area (µm²)", "Total Polygon Length (µm)"]
        ].sum()
        final_df = pd.merge(final_df, validated_df, left_on="File", right_on="File")
        final_df = pd.merge(final_df, cell_area_df, left_on="File", right_on="File")
        final_df = pd.merge(final_df, cell_df, left_on="File", right_on="File")
        final_df['ID'] = range(1, len(final_df) + 1)  # Adds ID as the last column
        final_df.to_csv(output_path, index=False)
        print(f"GNN results saved to {output_path}")

def find_cell_width(data):
    data = ast.literal_eval(data)
    res = abs(max(data[0][2], data[0][0]) - min(data[0][2], data[0][0]))
    return str(res)

def find_cell_height(data):
    data = ast.literal_eval(data)
    res = abs(max(data[0][3], data[0][1]) - min(data[0][3], data[0][1]))
    return str(res)

class EncoderWrapper(nn.Module):
    """Wrapper Class for the Encoder Part of AutoencoderIncremental.

    This class extracts the encoder part of the trained AutoencoderIncremental model for encoding data.
    """

    def __init__(self, autoencoder):
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