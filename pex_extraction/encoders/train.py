"""Autoencoder Training Script.

This script trains an autoencoder model either in-memory or out-of-core non-incrementally. As it highly depends on the dataset size,
it is currently obsolete, and we are using incremental learning instead.
It supports training models of type '2312' or '512'.

Example commands to run:

For in-memory training:
    python pex_extraction/encoders/train.py --input_path pex_extraction/MUX21X1_metrics.csv

For out-of-core training:
    python pex_extraction/encoders/train.py --input_path pex_extraction/MUX21X1_metrics.csv --use_out_of_core
"""

import argparse
import random
import numpy as np
import pandas as pd
import sys
import os
import pickle
import json
from sklearn.model_selection import train_test_split
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Type

# Determine the project root directory and append it to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from pex_extraction.data_utils.utils import (
    IL_layers_hardcoded_1,
    add_prefix_to_list,
    MemmapDataset,
    IL_layers_hardcoded_gaa,
)
from pex_extraction.data_utils.preprocessing_encoding import (
    preprocess_data_training_ae,
    convert_to_spatial_memmap,
)
from pex_extraction.encoders.autoencoder_model import Autoencoder2312, Autoencoder512

# Setting up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sivista_app')

# Additional MLflow imports
import mlflow
import mlflow.keras
import mlflow.pytorch

# -------------------------------
# Configuration Classes
# -------------------------------

@dataclass
class AutoencoderConfig:
    """Configuration class for the autoencoder training."""
    seed: int = 42
    model_save_path: str = 'autoencoder.pth'
    learning_rate: float = 1e-4
    batch_size: int = 32
    epochs: int = 10  # Adjust epochs for actual training (e.g., 150-250 for in-memory)
    num_workers: int = 0  # Number of workers for DataLoader
    model_type: str = '2312'  # Type of autoencoder model to train, '2312' or '512'

# -------------------------------
# Utility Functions
# -------------------------------

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility.

    Args:
        seed (int): The seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    elif torch.backends.mps.is_available():
        torch.manual_seed(seed)
    logger.info(f"Random seed set to {seed}")

# -------------------------------
# Base Classes
# -------------------------------

class AETrainer(ABC):
    """Abstract base class for Autoencoder trainers."""

    def __init__(self, config: AutoencoderConfig, input_path: str):
        """Initialize the trainer with configuration and input data path.

        Args:
            config (AutoencoderConfig): Configuration object.
            input_path (str): Path to the input data.
        """
        self.config = config
        set_seed(self.config.seed)
        self.input_path = input_path
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
            logger.info("CUDA is available, using GPU")
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
            logger.info("MPS is available, using GPU")
        else:
            self.device = torch.device('cpu')
            logger.info("No GPU available, using CPU")
        self.autoencoder = None
        self.train_loader = None
        self.test_loader = None
        self.criterion = nn.BCELoss()
        self.optimizer = None

    @abstractmethod
    def load_data(self):
        """Load and preprocess data specific to the trainer."""
        pass

    @abstractmethod
    def build_model(self):
        """Build the autoencoder model."""
        pass

    @abstractmethod
    def train(self):
        """Train the autoencoder."""
        pass

    @abstractmethod
    def evaluate(self):
        """Evaluate the autoencoder."""
        pass

    @abstractmethod
    def save_model(self):
        """Save the trained autoencoder model."""
        pass

    def run(self):
        """Execute the full training pipeline."""
        self.load_data()
        self.build_model()
        self.train()
        self.evaluate()
        self.save_model()

# -------------------------------
# In-Memory Autoencoder Trainer Class
# -------------------------------

class InMemoryAETrainer(AETrainer):
    """Trainer class for autoencoder with data that fits into memory."""

    def load_data(self):
        """Load and preprocess data for in-memory training."""
        logger.info("Loading and preprocessing data for in-memory autoencoder...")
        spatial_features = preprocess_data_training_ae(self.input_path, required_columns)
        train_spatial, test_spatial = train_test_split(
            spatial_features, test_size=0.2, random_state=self.config.seed
        )

        self.train_spatial = train_spatial.float()
        self.test_spatial = test_spatial.float()

        self.train_loader = DataLoader(
            self.train_spatial,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.num_workers,
        )

        self.test_loader = DataLoader(
            self.test_spatial,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
        )
        logger.info("Data loading and preprocessing completed.")

    def build_model(self):
        """Build the autoencoder model."""
        logger.info(f"Building autoencoder model '{self.config.model_type}'...")
        if self.config.model_type == '2312':
            self.autoencoder = Autoencoder2312().to(self.device)
        elif self.config.model_type == '512':
            self.autoencoder = Autoencoder512().to(self.device)
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")

        self.optimizer = optim.Adam(
            self.autoencoder.parameters(), lr=self.config.learning_rate
        )
        logger.info("Model built successfully.")

    def train(self):
        """Train the autoencoder."""
        logger.info("Starting training for in-memory autoencoder...")

        # Start MLflow run
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params({
                "learning_rate": self.config.learning_rate,
                "batch_size": self.config.batch_size,
                "epochs": self.config.epochs,
                "model_type": self.config.model_type,
                "optimizer": self.optimizer.__class__.__name__,
                "loss_function": self.criterion.__class__.__name__,
            })

            self.autoencoder.train()
            for epoch in range(self.config.epochs):
                total_loss = 0
                for batch in self.train_loader:
                    inputs = batch.to(self.device)
                    self.optimizer.zero_grad()
                    outputs = self.autoencoder(inputs)
                    loss = self.criterion(outputs, inputs)
                    loss.backward()
                    self.optimizer.step()
                    total_loss += loss.item()

                avg_loss = total_loss / len(self.train_loader)
                logger.info(f"Epoch [{epoch+1}/{self.config.epochs}], Loss: {avg_loss:.10f}")

                # Log metrics
                mlflow.log_metric("train_loss", avg_loss, step=epoch)

            # Evaluate after training
            test_loss = self.evaluate()
            mlflow.log_metric("test_loss", test_loss)

            # Save and log the model
            self.save_model()

            # Log the model with MLflow
            mlflow.pytorch.log_model(self.autoencoder, "model")

    def evaluate(self):
        """Evaluate the autoencoder on the test set.

        Returns:
            float: Average test loss.
        """
        logger.info("Evaluating the autoencoder...")
        self.autoencoder.eval()
        total_loss = 0
        with torch.no_grad():
            for batch in self.test_loader:
                inputs = batch.to(self.device)
                outputs = self.autoencoder(inputs)
                loss = self.criterion(outputs, inputs)
                total_loss += loss.item()
        avg_loss = total_loss / len(self.test_loader)
        logger.info(f"Test Loss: {avg_loss:.10f}")
        return avg_loss

    def save_model(self):
        """Save the trained autoencoder model."""
        torch.save(self.autoencoder.state_dict(), self.config.model_save_path)
        logger.info(f"Autoencoder model saved to {self.config.model_save_path}")

# -------------------------------
# Out-of-Core Autoencoder Trainer Class
# -------------------------------

class OutOfCoreAETrainer(AETrainer):
    """Trainer class for autoencoder with data that does not fit into memory."""

    def load_data(self):
        """Load and preprocess data for out-of-core training."""
        logger.info("Loading and preprocessing data for out-of-core autoencoder...")
        memmap_file = 'spatial_features_memmap.dat'
        if not os.path.exists(memmap_file):
            # Preprocess and save data to a memmap file
            convert_to_spatial_memmap(self.input_path, required_columns, memmap_file)
        else:
            logger.info(f"Memmap file '{memmap_file}' already exists. Using existing file.")

        indices = np.arange(os.path.getsize(memmap_file) // (64 * 64))  # Assuming float32 data

        train_indices, test_indices = train_test_split(
            indices, test_size=0.2, random_state=self.config.seed
        )

        self.train_dataset = MemmapDataset(memmap_file, train_indices)
        self.test_dataset = MemmapDataset(memmap_file, test_indices)

        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.num_workers,
        )
        self.test_loader = DataLoader(
            self.test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
        )
        logger.info("Data loading and preprocessing completed.")

    def build_model(self):
        """Build the autoencoder model."""
        logger.info(f"Building autoencoder model '{self.config.model_type}'...")
        if self.config.model_type == '2312':
            self.autoencoder = Autoencoder2312().to(self.device)
        elif self.config.model_type == '512':
            self.autoencoder = Autoencoder512().to(self.device)
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")

        self.optimizer = optim.Adam(
            self.autoencoder.parameters(), lr=self.config.learning_rate
        )
        logger.info("Model built successfully.")

    def train(self):
        """Train the autoencoder."""
        logger.info("Starting training for out-of-core autoencoder...")

        # Start MLflow run
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params({
                "learning_rate": self.config.learning_rate,
                "batch_size": self.config.batch_size,
                "epochs": self.config.epochs,
                "model_type": self.config.model_type,
                "optimizer": self.optimizer.__class__.__name__,
                "loss_function": self.criterion.__class__.__name__,
            })

            self.autoencoder.train()
            for epoch in range(self.config.epochs):
                total_loss = 0
                for batch_idx, (inputs, targets) in enumerate(self.train_loader):
                    inputs = inputs.to(self.device)
                    targets = targets.to(self.device)
                    self.optimizer.zero_grad()
                    outputs = self.autoencoder(inputs)
                    loss = self.criterion(outputs, targets)
                    loss.backward()
                    self.optimizer.step()
                    total_loss += loss.item()

                avg_loss = total_loss / len(self.train_loader)
                logger.info(f"Epoch [{epoch+1}/{self.config.epochs}], Loss: {avg_loss:.10f}")

                # Log metrics
                mlflow.log_metric("train_loss", avg_loss, step=epoch)

            # Evaluate after training
            test_loss = self.evaluate()
            mlflow.log_metric("test_loss", test_loss)

            # Save and log the model
            self.save_model()

            # Log the model with MLflow
            mlflow.pytorch.log_model(self.autoencoder, "model")

    def evaluate(self):
        """Evaluate the autoencoder on the test set.

        Returns:
            float: Average test loss.
        """
        logger.info("Evaluating the autoencoder...")
        self.autoencoder.eval()
        total_loss = 0
        with torch.no_grad():
            for inputs, targets in self.test_loader:
                inputs = inputs.to(self.device)
                outputs = self.autoencoder(inputs)
                loss = self.criterion(outputs, targets.to(self.device))
                total_loss += loss.item()
        avg_loss = total_loss / len(self.test_loader)
        logger.info(f"Test Loss: {avg_loss:.10f}")
        return avg_loss

    def save_model(self):
        """Save the trained autoencoder model."""
        torch.save(self.autoencoder.state_dict(), self.config.model_save_path)
        logger.info(f"Autoencoder model saved to {self.config.model_save_path}")

# -------------------------------
# Helper Function to Get Trainer Class
# -------------------------------

def get_trainer(use_out_of_core: bool) -> Type[AETrainer]:
    """Get the appropriate trainer class based on the use_out_of_core flag.

    Args:
        use_out_of_core (bool): Flag to decide trainer type.

    Returns:
        Type[AETrainer]: Trainer class.
    """
    if use_out_of_core:
        return OutOfCoreAETrainer
    else:
        return InMemoryAETrainer

# -------------------------------
# Main Function
# -------------------------------

def main():
    """Main function to run the autoencoder training process.

    This function parses command-line arguments and initiates the training process.
    """
    parser = argparse.ArgumentParser(description='Autoencoder Training Script')
    parser.add_argument('--input_path', type=str, required=True,
                        help='Path to the input data')
    parser.add_argument('--save_model_path', type=str, required=False,
                        help='Path to save the trained model')
    parser.add_argument('--config', type=str, required=False,
                        help='Path to configuration JSON file')
    parser.add_argument('--use_out_of_core', action='store_true',
                        help='Use out-of-core trainer for large datasets')
    parser.add_argument('--model_type', type=str, choices=['2312', '512'], default='2312',
                        help='Type of autoencoder model to train (default: 2312), choose between 2312 and 512')
    parser.add_argument('--isGAA', action='store_true',
                        help='Use GAA layers')
    args = parser.parse_args()

    # Define required_columns based on isGAA argument
    global required_columns
    if args.isGAA:
        required_columns = add_prefix_to_list(IL_layers_hardcoded_gaa)
    else:
        required_columns = add_prefix_to_list(IL_layers_hardcoded_1)

    # Get the configuration
    config = AutoencoderConfig()

    # Override model save path if provided
    if args.save_model_path:
        config.model_save_path = args.save_model_path

    # Load configurations from a JSON file if provided
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    logger.warning(f"Ignoring unknown configuration key: {key}")

    # Set the use_out_of_core flag
    use_out_of_core = args.use_out_of_core

    # Set the model type
    config.model_type = args.model_type

    # Initialize MLflow experiment
    mlflow.set_experiment("Autoencoder Training")

    # Create trainer instance
    TrainerClass = get_trainer(use_out_of_core)
    trainer = TrainerClass(config, args.input_path)

    # Run the training process
    trainer.run()

if __name__ == "__main__":
    main()