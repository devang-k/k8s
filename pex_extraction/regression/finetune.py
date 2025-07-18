"""Finetuning Script for Regression Models.

This script provides classes and functions to finetune regression models such as Mixture of Experts (MoE)
and Graph Neural Networks (GNN) on new data. It supports loading pre-trained models,
performing finetuning, and integrates with MLflow for experiment tracking.

Example commands to run:

For MoE:
    python pex_extraction/regression/finetune.py --model moe --input_path new_data.csv --label_path new_labels.csv --pre_trained_model_path path_to_moe_model

For GNN:
    python pex_extraction/regression/finetune.py --model gnn --input_path new_data.csv --label_path new_labels.csv --pre_trained_model_path path_to_gnn_model

Please review config settings prior to running the commands.
"""

import argparse
import random
import numpy as np
import pandas as pd
import sys
import os
import pickle
import json
import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

# Determine the project root directory and append it to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# TensorFlow imports
import tensorflow as tf
from tensorflow import keras
from keras.models import Model, load_model


# PyTorch imports
import torch
from torch_geometric.loader import DataLoader
import torch.optim as optim
import torch.nn as nn
# MLflow imports
import mlflow
import mlflow.keras
import mlflow.pytorch

# Custom module imports
from pex_extraction.data_utils.utils import (
    IL_layers_hardcoded_1, add_prefix_to_list, IL_layers_hardcoded_gaa
)
from pex_extraction.data_utils.preprocessing_encoding import (
    preprocess_data_training_moe, preprocess_data_training_gnn
)
from pex_extraction.regression.gnn_model import EdgeRegressionGNN, initGNN, get_activation_function

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sivista_app')

# -------------------------------
# Configuration Classes
# -------------------------------

@dataclass
class MoEFinetuneConfig:
    """Configuration for Mixture of Experts (MoE) model finetuning.

    Attributes:
        seed (int): Random seed for reproducibility.
        model_save_path (str): Path to save the finetuned MoE model.
        pre_trained_model_path (str): Path to the pre-trained MoE model.
        batch_size (int): Batch size for training.
        epochs (int): Number of epochs for finetuning.
        learning_rate (float): Learning rate for optimizer.
        activation (str): Activation function name.
    """
    seed: int = 42
    model_save_path: str = 'finetuned_moe_model.keras'
    pre_trained_model_path: str = 'pretrained_moe_model.keras'
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-4
    activation: str = 'relu'

@dataclass
class GNNFinetuneConfig:
    """Configuration for Graph Neural Network (GNN) model finetuning.

    Attributes:
        seed (int): Random seed for reproducibility.
        model_save_path (str): Path to save the finetuned GNN model.
        pre_trained_model_path (str): Path to the pre-trained GNN model.
        batch_size (int): Batch size for training.
        epochs (int): Number of epochs for finetuning.
        learning_rate (float): Learning rate for optimizer.
        weight_decay (float): Weight decay (L2 regularization) factor.
        activation (str): Activation function name.
        device (str): Device to use for training ('cpu' or 'cuda').
    """
    seed: int = 42
    model_save_path: str = 'finetuned_gnn_model.pth'
    pre_trained_model_path: str = 'pretrained_gnn_model.pth'
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    activation: str = 'relu'
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'

# -------------------------------
# Base Finetuner Class
# -------------------------------

class BaseFinetuner(ABC):
    """Abstract Base Class for Model Finetuners.

    This class provides a template for finetuning different regression models.

    Args:
        config: Configuration object specific to the model.
        input_path (str): Path to the input data.
        label_path (str): Path to the label data.
    """
    def __init__(self, config, input_path, label_path):
        self.config = config
        self.input_path = input_path
        self.label_path = label_path

    @abstractmethod
    def load_data(self):
        """Load and preprocess data for finetuning."""
        pass

    @abstractmethod
    def load_model(self):
        """Load the pre-trained model to be finetuned."""
        pass

    @abstractmethod
    def finetune(self):
        """Perform the finetuning process."""
        pass

    @abstractmethod
    def save_model(self):
        """Save the finetuned model."""
        pass

    @abstractmethod
    def run(self):
        """Run the full finetuning pipeline."""
        pass

# -------------------------------
# MoE Finetuner
# -------------------------------

class MoEFinetuner(BaseFinetuner):
    """Finetuner for Mixture of Experts (MoE) Model.

    This class handles loading, finetuning, and saving the MoE model.

    Args:
        config (MoEFinetuneConfig): Configuration for finetuning.
        input_path (str): Path to the input data.
        label_path (str): Path to the label data.
    """

    def load_data(self):
        """Load and preprocess data for MoE finetuning."""
        logger.info("Loading and preprocessing data for MoE model finetuning...")
        # Implement data loading and preprocessing
        # Example:
        # self.X_train, self.y_train = preprocess_data_training_moe(
        #     self.input_path, required_columns, self.label_path
        # )
        # For simplicity, let's assume data is loaded into self.X_train and self.y_train
        pass

    def load_model(self):
        """Load the pre-trained MoE model."""
        logger.info("Loading pre-trained MoE model...")
        self.model = load_model(self.config.pre_trained_model_path)
        logger.info("Pre-trained MoE model loaded.")

    def finetune(self):
        """Finetune the MoE model."""
        logger.info("Starting MoE model finetuning...")
        optimizer = keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        self.model.compile(optimizer=optimizer, loss='mse')

        # Implement finetuning process, e.g., fitting the model on new data
        # self.model.fit(self.X_train, self.y_train, batch_size=self.config.batch_size,
        #                epochs=self.config.epochs)

        logger.info("MoE model finetuning completed.")

    def save_model(self):
        """Save the finetuned MoE model."""
        self.model.save(self.config.model_save_path)
        logger.info(f"Finetuned MoE model saved to {self.config.model_save_path}")

    def run(self):
        """Run the full finetuning pipeline for MoE model."""
        self.load_data()
        self.load_model()
        self.finetune()
        self.save_model()

# -------------------------------
# GNN Finetuner
# -------------------------------

class GNNFinetuner(BaseFinetuner):
    """Finetuner for Graph Neural Network (GNN) Model.

    This class handles loading, finetuning, and saving the GNN model.

    Args:
        config (GNNFinetuneConfig): Configuration for finetuning.
        input_path (str): Path to the input data.
        label_path (str): Path to the label data.
    """

    def load_data(self):
        """Load and preprocess data for GNN finetuning."""
        logger.info("Loading and preprocessing data for GNN model finetuning...")
        # Implement data loading and preprocessing
        # Example:
        # self.train_data_list = preprocess_data_training_gnn(
        #     self.input_path, required_columns, self.label_path
        # )
        pass

    def load_model(self):
        """Load the pre-trained GNN model."""
        logger.info("Loading pre-trained GNN model...")
        self.device = torch.device(self.config.device)
        # Assume we have best_params to initialize the GNN model appropriately
        # Here, we need to know the embedding dimension and other parameters
        # For simplicity, we will load the model directly
        self.model = EdgeRegressionGNN(...)  # Replace with appropriate initialization
        self.model.load_state_dict(torch.load(self.config.pre_trained_model_path, map_location=self.device))
        self.model.to(self.device)
        logger.info("Pre-trained GNN model loaded.")

    def finetune(self):
        """Finetune the GNN model."""
        logger.info("Starting GNN model finetuning...")
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate, weight_decay=self.config.weight_decay)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(self.config.epochs):
            for data in self.train_data_list:
                data = data.to(self.device)
                optimizer.zero_grad()
                out = self.model(data)
                loss = criterion(out, data.y)
                loss.backward()
                optimizer.step()
            logger.info(f"Epoch {epoch+1}/{self.config.epochs}, Loss: {loss.item()}")

        logger.info("GNN model finetuning completed.")

    def save_model(self):
        """Save the finetuned GNN model."""
        torch.save(self.model.state_dict(), self.config.model_save_path)
        logger.info(f"Finetuned GNN model saved to {self.config.model_save_path}")

    def run(self):
        """Run the full finetuning pipeline for GNN model."""
        self.load_data()
        self.load_model()
        self.finetune()
        self.save_model()

# -------------------------------
# Finetuner Registry
# -------------------------------

def get_finetuner(model_name: str) -> Type[BaseFinetuner]:
    """Get the finetuner class based on the model name.

    Args:
        model_name (str): Name of the model ('moe' or 'gnn').

    Returns:
        Type[BaseFinetuner]: Finetuner class.

    Raises:
        ValueError: If the model name is unsupported.
    """
    finetuners = {
        'moe': MoEFinetuner,
        'gnn': GNNFinetuner
    }
    if model_name not in finetuners:
        raise ValueError(f"Unsupported model: {model_name}")
    return finetuners[model_name]

def get_finetune_config(model_name: str):
    """Get the finetuning configuration class based on the model name.

    Args:
        model_name (str): Name of the model ('moe' or 'gnn').

    Returns:
        Configuration object.

    Raises:
        ValueError: If the model name is unsupported.
    """
    configs = {
        'moe': MoEFinetuneConfig,
        'gnn': GNNFinetuneConfig
    }
    if model_name not in configs:
        raise ValueError(f"Unsupported model: {model_name}")
    return configs[model_name]()

# -------------------------------
# Main Function
# -------------------------------

def main():
    """Main function to run the finetuning process.

    Recommended commands to run at the SiVista main directory:

    For MoE:
    python pex_extraction/regression/finetune.py --model moe --input_path new_data.csv --label_path new_labels.csv --pre_trained_model_path path_to_moe_model

    For GNN:
    python pex_extraction/regression/finetune.py --model gnn --input_path new_data.csv --label_path new_labels.csv --pre_trained_model_path path_to_gnn_model

    Please also review config settings prior to running the commands.
    """
    parser = argparse.ArgumentParser(description='Model Finetuning Script')
    parser.add_argument('--model', type=str, choices=['moe', 'gnn'], required=True,
                        help='Choose the model to finetune: "moe" or "gnn"')
    parser.add_argument('--input_path', type=str, required=True,
                        help='Path to the input data')
    parser.add_argument('--label_path', type=str, required=True,
                        help='Path to the label data')
    parser.add_argument('--pre_trained_model_path', type=str, required=True,
                        help='Path to the pre-trained model')
    parser.add_argument('--save_model_path', type=str, required=False,
                        help='Path to save the finetuned model')
    parser.add_argument('--config', type=str, required=False,
                        help='Path to configuration JSON file')
    parser.add_argument('--isGAA', action='store_true',
                        help='Use GAA layers')
    args = parser.parse_args()

    # Define required_columns based on isGAA argument
    global required_columns
    if args.isGAA:
        required_columns = add_prefix_to_list(IL_layers_hardcoded_gaa)
    else:
        required_columns = add_prefix_to_list(IL_layers_hardcoded_1)

    # Get the configuration class
    config = get_finetune_config(args.model)

    # Override paths if provided
    if args.save_model_path:
        config.model_save_path = args.save_model_path
    config.pre_trained_model_path = args.pre_trained_model_path

    # Load configurations from a JSON file if provided
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Ignoring unknown configuration key: {key}")
    config.isGAA = args.isGAA

    # Create finetuner instance
    FinetunerClass = get_finetuner(args.model)
    finetuner = FinetunerClass(config, args.input_path, args.label_path)

    # Run the finetuning process
    finetuner.run()

if __name__ == "__main__":
    main()
