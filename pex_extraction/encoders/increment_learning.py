"""Incremental Learning Trainer for Autoencoder Models.

This script trains an autoencoder model incrementally on datasets divided into increments based on unique 'File' entries.
It supports Elastic Weight Consolidation (EWC) to mitigate catastrophic forgetting during incremental learning.

Example commands to run:
For CFET:
python pex_extraction/encoders/increment_learning.py --metrics_folder metrics_folder_cfet --model_type AutoencoderIncremental --model_save_path AE_layers_with_0_CFET                              


For GAA:
python pex_extraction/encoders/increment_learning.py --metrics_folder metrics_folder_gaa --model_type AutoencoderIncremental --model_save_path AE_layers_with_0_GAA --isGAA

"""

import argparse
import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
import random
from dataclasses import dataclass
import sys
import pickle
import json
from sklearn.model_selection import train_test_split
from abc import ABC, abstractmethod
from typing import Type
import platform
from torch.utils.tensorboard import SummaryWriter  # Import TensorBoard writer
from torch.utils.data import ConcatDataset

# Determine the project root directory and append it to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# Import custom modules
from pex_extraction.encoders.autoencoder_model import (
    AutoencoderIncremental,
    EWC,
)
from pex_extraction.data_utils.preprocessing_encoding import (
    preprocess_data_training_incremental_ae,
)
from pex_extraction.data_utils.utils import (
    IL_layers_hardcoded_1,
    IL_layers_hardcoded_gaa,
)

# Setting up logging
import logging

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

# -------------------------------
# Incremental Learning Trainer Class
# -------------------------------

class IncrementalAETrainer:
    """Trainer for incremental learning with autoencoder models."""

    def __init__(self, config, metrics_folder):
        """Initialize the IncrementalAETrainer.

        Args:
            config: Configuration object.
            metrics_folder (str): Path to the folder containing metrics CSV files.
        """
        self.config = config
        set_seed(self.config.seed)
        self.metrics_folder = metrics_folder

        # Determine the device (GPU if available, otherwise CPU)
        if sys.platform == 'darwin' and platform.machine() == 'arm64' and torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Select common layers based on GAA configuration
        if self.config.isGAA:
            self.common_layers = IL_layers_hardcoded_gaa
        else:
            self.common_layers = IL_layers_hardcoded_1
        self.num_channels = len(self.common_layers)
        logger.info(f"Number of channels (common layers): {self.num_channels}")

        # Initialize the appropriate autoencoder model
        if self.config.model_type == 'AutoencoderIncremental':
            self.autoencoder = AutoencoderIncremental(num_channels=self.num_channels).to(self.device)
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")

        # Initialize the optimizer and scheduler
        self.optimizer = optim.Adam(self.autoencoder.parameters(), lr=self.config.learning_rate)
        self.scheduler = optim.lr_scheduler.ExponentialLR(
            self.optimizer,
            gamma=0.95  # Reduce LR by 5% after each epoch
        )
        self.criterion = nn.BCELoss()
        self.previous_datasets = []
        self.data_memory = []
        self.writer = SummaryWriter(log_dir=self.config.tensorboard_log_dir)  # Initialize TensorBoard writer
        
        # Compute common layers across all CSV files
        self.common_layers = required_columns
        # logger.info(f"Common layers across all CSV files: {self.common_layers}")
    
        # Early stopping parameters
        self.early_stopping_patience = self.config.early_stopping_patience

    def get_csv_files(self):
        """Get list of CSV files in the metrics folder.

        Returns:
            List[str]: List of CSV file paths.
        """
        csv_files = glob.glob(os.path.join(self.metrics_folder, '*.csv'))
        csv_files.sort()  # Ensure consistent order
        return csv_files

    def load_datasets_from_csv(self, csv_file):
        """Load datasets from a CSV file.

        Args:
            csv_file (str): Path to the CSV file.

        Returns:
            Tuple[Dataset, Dataset]: Training and validation datasets.
        """
        logger.info(f"Loading data from {csv_file}")
        data = pd.read_csv(csv_file)

        # Preprocess data
        spatial_features = preprocess_data_training_incremental_ae(data, self.common_layers, isGAA=self.config.isGAA)
        print(f"Spatial features shape: {spatial_features.shape}")  # Should be consistent across datasets

        # Convert the preprocessed features into a TensorDataset
        dataset = TensorDataset(spatial_features)

        # Split 20% into validation set
        val_size = int(0.2 * len(dataset))
        train_size = len(dataset) - val_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset,
            [train_size, val_size],
            generator=torch.Generator().manual_seed(self.config.seed)
        )

        return train_dataset, val_dataset

    def prepare_dataloader(self, dataset, batch_size):
        """Prepare a DataLoader for the given dataset.

        Args:
            dataset (Dataset): The dataset to load.
            batch_size (int): Batch size.

        Returns:
            DataLoader: The data loader.
        """
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        return dataloader

    def load_and_prepare_data(self):
        """Load all CSV files, concatenate them into one DataFrame,
        and prepare increments based on unique 'File' entries.

        This method creates increments for incremental learning by splitting the data
        based on unique 'File' entries.
        """
        logger.info("Loading and concatenating all CSV files.")
        # Load all CSV files and concatenate into one DataFrame
        csv_files = self.get_csv_files()
        dataframes = [pd.read_csv(csv_file) for csv_file in csv_files]
        combined_data = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined data shape: {combined_data.shape}")

        # Find unique 'File' entries
        unique_files = combined_data['File'].unique()
        logger.info(f"Total unique files: {len(unique_files)}")

        # Shuffle unique_files to randomize the order
        np.random.shuffle(unique_files)

        # Divide unique_files into increments
        num_increments = 26
        increments = np.array_split(unique_files, num_increments)
        logger.info(f"Divided unique files into {num_increments} increments.")

        # For each increment, create a DataFrame containing data from the 'File's in that increment
        self.increments_data = []
        for idx, increment_files in enumerate(increments):
            increment_data = combined_data[combined_data['File'].isin(increment_files)]
            self.increments_data.append(increment_data)
            logger.info(f"Increment {idx+1} data shape: {increment_data.shape}")

    def incremental_train(self):
        """Perform incremental training using data divided into increments
        based on unique 'File' entries.

        This method performs the main training loop, including optional EWC regularization
        and early stopping based on validation loss.
        """
        # Load and prepare data according to the new approach
        self.load_and_prepare_data()

        ewc_lambda = self.config.ewc_lambda  # Regularization strength
        previous_val_loaders = []

        num_increments = len(self.increments_data)

        for i, increment_data in enumerate(self.increments_data):
            logger.info(f"Starting increment {i+1}/{num_increments}")

            # Preprocess data
            spatial_features = preprocess_data_training_incremental_ae(increment_data, self.common_layers, isGAA=self.config.isGAA)
            logger.info(f"Spatial features shape: {spatial_features.shape}")

            # Convert the preprocessed features into a TensorDataset
            dataset = TensorDataset(spatial_features)

            # Split 20% into validation set
            val_size = int(0.2 * len(dataset))
            train_size = len(dataset) - val_size
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset,
                [train_size, val_size],
                generator=torch.Generator().manual_seed(self.config.seed)
            )

            # Take up to 1000 samples (or max available) for this increment from the training dataset
            max_rows = min(1000, len(train_dataset))
            train_subset, _ = torch.utils.data.random_split(
                train_dataset,
                [max_rows, len(train_dataset) - max_rows],
                generator=torch.Generator().manual_seed(self.config.seed)
            )

            # Include a subset of previous data (memory) during fine-tuning
            if len(self.data_memory) > 0:
                memory_size = min(100, len(self.data_memory))
                memory_data = random.sample(self.data_memory, memory_size)

                # Extract input tensors from memory_data
                memory_inputs = []
                for idx, data in enumerate(memory_data):
                    # Assuming each data is a tuple containing one tensor
                    input_tensor = data[0] if isinstance(data, tuple) else data
                    memory_inputs.append(input_tensor)

                # Create TensorDataset
                memory_dataset = torch.utils.data.TensorDataset(torch.stack(memory_inputs))

                # Combine datasets using ConcatDataset
                combined_dataset = ConcatDataset([train_subset, memory_dataset])
            else:
                combined_dataset = train_subset

            logger.info(f"Combined dataset size: {len(combined_dataset)}")

            # Create DataLoaders
            train_loader = self.prepare_dataloader(combined_dataset, self.config.batch_size)
            val_loader = self.prepare_dataloader(val_dataset, self.config.batch_size)

            previous_val_loaders.append((f"Task_{i+1}_Val", val_loader))

            # Instantiate EWC after the first task
            if i > 0 and len(self.previous_datasets) > 0:
                prev_task_dataset = self.previous_datasets[-1]
                ewc = EWC(self.autoencoder, prev_task_dataset, device=self.device)

            # Initialize early stopping variables
            best_val_loss = float('inf')
            patience_counter = 0

            # Training Loop
            self.autoencoder.train()
            for epoch in range(self.config.epochs_per_increment):
                # Get current learning rate
                current_lr = self.optimizer.param_groups[0]['lr']
                logger.info(f"Epoch {epoch+1} starting LR: {current_lr:.6f}")

                total_loss = 0
                total_reconstruction_loss = 0
                total_ewc_loss = 0

                for batch in train_loader:
                    inputs = batch[0].to(self.device)
                    self.optimizer.zero_grad()
                    outputs = self.autoencoder(inputs)
                    reconstruction_loss = self.criterion(outputs, inputs)

                    # Compute EWC penalty if applicable
                    if i > 0 and len(self.previous_datasets) > 0:
                        penalty = ewc.penalty(self.autoencoder)
                        loss = reconstruction_loss + ewc_lambda * penalty
                        total_ewc_loss += penalty.item()
                    else:
                        loss = reconstruction_loss

                    loss.backward()
                    self.optimizer.step()
                    total_loss += loss.item()
                    total_reconstruction_loss += reconstruction_loss.item()

                avg_loss = total_loss / len(train_loader)
                avg_reconstruction_loss = total_reconstruction_loss / len(train_loader)
                avg_ewc_loss = total_ewc_loss / len(train_loader) if i > 0 else 0

                logger.info(f"Increment {i+1}, Epoch [{epoch+1}/{self.config.epochs_per_increment}], "
                            f"Total Loss: {avg_loss:.10f}, Reconstruction Loss: {avg_reconstruction_loss:.10f}, "
                            f"EWC Loss: {avg_ewc_loss:.10f}, "
                            f"Learning Rate: {current_lr:.6f}")

                # Log metrics to TensorBoard
                global_epoch = i * self.config.epochs_per_increment + epoch + 1
                self.writer.add_scalar('Loss/Total', avg_loss, global_epoch)
                self.writer.add_scalar('Loss/Reconstruction', avg_reconstruction_loss, global_epoch)
                if i > 0:
                    self.writer.add_scalar('Loss/EWC', avg_ewc_loss, global_epoch)

                # Evaluate on validation set
                val_loss = self.evaluate(val_loader)
                self.writer.add_scalar('Validation_Loss/Current_Task', val_loss, global_epoch)
                logger.info(f"Validation Loss on Current Task: {val_loss:.10f}")

                # Evaluate on previous validation sets to monitor catastrophic forgetting
                if i > 0:
                    for task_name, prev_val_loader in previous_val_loaders[:-1]:
                        prev_val_loss = self.evaluate(prev_val_loader)
                        self.writer.add_scalar(f'Validation_Loss/{task_name}', prev_val_loss, global_epoch)
                        logger.info(f"Validation Loss on {task_name}: {prev_val_loss:.10f}")

                # Check for early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save the model checkpoint for the current best model
                    torch.save(self.autoencoder.state_dict(), f"{self.config.model_save_path}_best_increment_{i+1}.pth")
                else:
                    patience_counter += 1
                    logger.info(f"No improvement in validation loss for {patience_counter} epochs.")

                    if patience_counter >= self.early_stopping_patience:
                        logger.info(f"Early stopping triggered after {epoch+1} epochs for increment {i+1}.")
                        # Load the best model before stopping
                        self.autoencoder.load_state_dict(torch.load(f"{self.config.model_save_path}_best_increment_{i+1}.pth"))
                        break

            # Save current data for future increments
            self.data_memory.extend(train_subset)
            # Limit the size of data_memory
            if len(self.data_memory) > self.config.memory_size * 1000:
                self.data_memory = self.data_memory[-self.config.memory_size * 1000:]

            # Update previous datasets
            self.previous_datasets.append(train_subset)
            if len(self.previous_datasets) > self.config.memory_size:
                self.previous_datasets.pop(0)

            # Step the scheduler and log the new LR
            self.scheduler.step()
            new_lr = self.optimizer.param_groups[0]['lr']
            logger.info(f"Current Learning Rate: {new_lr:.6f}")
            self.writer.add_scalar('Learning_Rate', new_lr, global_epoch)

        self.writer.close()  # Close the TensorBoard writer

    def evaluate(self, val_loader):
        """Evaluate the model on the validation set.

        Args:
            val_loader (DataLoader): Validation data loader.

        Returns:
            float: Average validation loss.
        """
        self.autoencoder.eval()
        total_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                inputs = batch[0].to(self.device)
                outputs = self.autoencoder(inputs)
                loss = self.criterion(outputs, inputs)
                total_loss += loss.item()
        avg_loss = total_loss / len(val_loader)
        return avg_loss

    def save_model(self):
        """Save the trained autoencoder model."""
        torch.save(self.autoencoder.state_dict(), self.config.model_save_path)
        logger.info(f"Autoencoder model saved to {self.config.model_save_path}")

# -------------------------------
# Configuration Class
# -------------------------------

@dataclass
class IncrementalLearningConfig:
    """Configuration for Incremental Learning."""
    seed: int = 42
    learning_rate: float = 1e-3  # Start with a higher learning rate
    batch_size: int = 32
    epochs_per_increment: int = 150
    ewc_lambda: float = 0.4
    memory_size: int = 10
    model_save_path: str = None  # Will be set from command line
    tensorboard_log_dir: str = None  # Will be derived from model_save_path
    model_type: str = 'AutoencoderIncremental'
    early_stopping_patience: int = 10

# -------------------------------
# Main Function
# -------------------------------

def main():
    """Main function to initiate incremental learning training.

    Parses command-line arguments and starts the training process.
    """
    parser = argparse.ArgumentParser(description='Incremental Learning for Autoencoder')
    parser.add_argument('--metrics_folder', type=str, required=True, help='Path to the folder containing CSV metrics files')
    parser.add_argument('--model_save_path', type=str, default='AE_layers_with_0_CFET', help='Path to save the trained model')
    parser.add_argument('--model_type', type=str, default='AutoencoderIncremental', help='Type of model to use: AutoencoderIncremental')
    parser.add_argument('--isGAA', action='store_true', help='Use GAA layers')
    args = parser.parse_args()

    # Define required_columns based on isGAA argument without adding prefix
    global required_columns
    if args.isGAA:
        required_columns = IL_layers_hardcoded_gaa
    else:
        required_columns = IL_layers_hardcoded_1

    # Derive tensorboard_log_dir from model_save_path
    tensorboard_log_dir = 'runs/' + args.model_save_path.replace('.pth', '')
    
    config = IncrementalLearningConfig(
        model_type=args.model_type,
        model_save_path=args.model_save_path+'.pth',
        tensorboard_log_dir=tensorboard_log_dir
    )
    config.isGAA = args.isGAA

    trainer = IncrementalAETrainer(config, args.metrics_folder)
    trainer.incremental_train()
    trainer.save_model()

if __name__ == '__main__':
    main() 