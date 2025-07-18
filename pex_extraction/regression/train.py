"""Training Script for Regression Models.

This script provides classes and functions to train regression models such as Mixture of Experts (MoE)
and Graph Neural Networks (GNN) for predicting capacitance values. It supports hyperparameter optimization
using Optuna and integrates with MLflow for experiment tracking.

Example commands to run:

For MoE:
    python pex_extraction/regression/train.py --model moe --input_path pex_extraction/MUX21X1_metrics.csv --label_path pex_extraction/moe_label_example.csv

For GNN:
    python pex_extraction/regression/train.py --model gnn --input_path pex_extraction/MUX21X1_metrics.csv --label_path pex_extraction/gnn_label_example.csv

Please also review config settings prior to running the commands.
"""

import argparse
import random
import numpy as np
import pandas as pd
import sys
import os
import pickle
import json
import platform
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
from keras.models import Model
from keras.layers import Input, Dense, Concatenate, Lambda, Dropout
from keras.regularizers import l2
from keras.optimizers import Adam, SGD, RMSprop
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from optuna.integration import TFKerasPruningCallback

# PyTorch imports
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.loader import DataLoader
from optuna.exceptions import TrialPruned

# Optuna for hyperparameter optimization
import optuna
from optuna.integration import MLflowCallback

# Custom module imports
from pex_extraction.data_utils.utils import (
    IL_layers_hardcoded_1, add_prefix_to_list, IL_layers_hardcoded_gaa
)
from pex_extraction.data_utils.preprocessing_encoding import (
    preprocess_data_training_moe, preprocess_data_training_gnn, load_label_data
)
from pex_extraction.data_utils.preprocessing_regression import (
    gnn_train_preprocessing, load_csv_data, gnn_train_from_embeddings_preprocessing
)
from pex_extraction.encoders.autoencoder_model import Encoder2312, AutoencoderIncremental
from pex_extraction.regression.gnn_model import EdgeRegressionGNN,get_activation_function
from pex_extraction.encoders.encode_and_save import EncoderWrapper

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sivista_app')

# MLflow imports
import mlflow
import mlflow.keras
import mlflow.pytorch
from mlflow.models.signature import infer_signature

# -------------------------------
# Configuration Classes
# -------------------------------

@dataclass
class MoEConfig:
    """Configuration for Mixture of Experts (MoE) model training.

    Attributes:
        seed (int): Random seed for reproducibility.
        model_save_path (str): Path to save the trained MoE model.
        num_experts (int): Number of expert networks.
        reg (float): L2 regularization factor.
        dropout_rate (float): Dropout rate for regularization.
        learning_rate (float): Learning rate for optimizer.
        activation (str): Activation function name.
        units_layer1 (int): Number of units in the first hidden layer.
        units_layer2 (int): Number of units in the second hidden layer.
        units_layer3 (int): Number of units in the third hidden layer.
        batch_size (int): Batch size for training.
        epochs (int): Number of training epochs.
        n_trials (int): Number of trials for hyperparameter optimization.
        isGAA (bool): Flag indicating if using GAA layers.
    """
    seed: int = 42
    model_save_path: str = 'moe_model.keras'
    num_experts: int = 4
    reg: float = 1e-4
    dropout_rate: float = 0.3
    learning_rate: float = 1e-3
    activation: str = 'relu'
    units_layer1: int = 512
    units_layer2: int = 256
    units_layer3: int = 128
    batch_size: int = 32
    epochs: int = 50
    n_trials: int = 50
    isGAA: bool = False

@dataclass
class GNNConfig:
    """Configuration for Graph Neural Network (GNN) model training.

    Attributes:
        seed (int): Random seed for reproducibility.
        model_save_path (str): Path to save the trained GNN model.
        reg: L2 regularization factor.
        learning_rate (float): Learning rate for optimizer.
        epochs (int): Number of training epochs.
        n_trials (int): Number of trials for hyperparameter optimization.
        embedding_dim (int): Dimension of node embeddings.
        use_embeddings (bool): Flag indicating if using precomputed embeddings.
        batch_size (int): Batch size for training.
        isGAA (bool): Flag indicating if using GAA layers.
        best_params_path (str): Path to load or save the best parameters.
    """
    seed: int = 42
    model_save_path: str = 'gnn_model.pth'
    reg: float = 1e-4
    learning_rate: float = 1e-3
    epochs: int = 50
    n_trials: int = 50
    embedding_dim: int = 2312
    use_embeddings: bool = False
    batch_size: int = 32
    isGAA: bool = False
    best_params_path: str = 'best_params.pkl'  # Path to the best parameters

# -------------------------------
# Trainer Classes
# -------------------------------

class BaseTrainer(ABC):
    """Abstract Base Trainer Class.

    This class provides a template for different model trainers and ensures consistent methods
    across trainers.
    """

    @abstractmethod
    def run(self):
        """Run the training process."""
        pass

    @abstractmethod
    def load_data(self):
        """Load and preprocess data."""
        pass

    @abstractmethod
    def build_model(self, trial=None):
        """Build the model.

        Args:
            trial (optuna.Trial, optional): Optuna trial object for hyperparameter tuning.
        """
        pass

    @abstractmethod
    def train_model(self, trial=None):
        """Train the model.

        Args:
            trial (optuna.Trial, optional): Optuna trial object for hyperparameter tuning.
        """
        pass

    @abstractmethod
    def save_model(self):
        """Save the trained model to disk."""
        pass

    @abstractmethod
    def optimize_hyperparameters(self):
        """Optimize hyperparameters using Optuna."""
        pass

class MoETrainer(BaseTrainer):
    """Trainer for Mixture of Experts (MoE) model.

    This class handles loading data, building the MoE model, training, and saving the model.

    Args:
        config (MoEConfig): Configuration object.
        input_path (str): Path to the input data.
        label_path (str): Path to the label data.
    """

    def __init__(self, config: MoEConfig, input_path: str, label_path: str):
        self.config = config
        self.input_path = input_path
        self.label_path = label_path
        self.model = None
        self.scaler = None
        self.encoder = None
        self.history = None

        # Set random seed
        np.random.seed(self.config.seed)
        tf.random.set_seed(self.config.seed)

    def run(self):
        """Run the training process."""
        self.load_data()
        if self.config.n_trials > 0:
            self.optimize_hyperparameters()
        else:
            self.build_model()
            self.train_model()
            self.save_model()

    def load_data(self):
        """Load and preprocess data."""
        logger.info("Loading and preprocessing data for MoE model...")

        # Preprocess data
        (
            self.X_train,
            self.X_test,
            self.y_train,
            self.y_test,
            self.encoder,
            self.scaler
        ) = preprocess_data_training_moe(
            self.input_path,
            required_columns,
            self.label_path
        )
        logger.info("Data loading and preprocessing completed.")

    def build_model(self, trial=None):
        """Build the MoE model.

        Args:
            trial (optuna.Trial, optional): Optuna trial object for hyperparameter tuning.
        """
        reg = self.config.reg
        num_experts = self.config.num_experts
        dropout_rate = self.config.dropout_rate
        activation = self.config.activation
        units_layer1 = self.config.units_layer1
        units_layer2 = self.config.units_layer2
        units_layer3 = self.config.units_layer3
        learning_rate = self.config.learning_rate

        if trial is not None:
            # Suggest hyperparameters
            reg = trial.suggest_loguniform('reg', 1e-5, 1e-2)
            num_experts = trial.suggest_int('num_experts', 2, 10)
            dropout_rate = trial.suggest_uniform('dropout_rate', 0.0, 0.5)
            activation = trial.suggest_categorical('activation', ['relu', 'tanh', 'sigmoid'])
            units_layer1 = trial.suggest_int('units_layer1', 64, 512, step=64)
            units_layer2 = trial.suggest_int('units_layer2', 32, 256, step=32)
            units_layer3 = trial.suggest_int('units_layer3', 16, 128, step=16)
            learning_rate = trial.suggest_loguniform('learning_rate', 1e-5, 1e-2)

        # Build the MoE model
        input_shape = self.X_train.shape[1]
        inputs = Input(shape=(input_shape,))
        tower_outputs = []
        for _ in range(num_experts):
            x = Dense(units_layer1, activation=activation, kernel_regularizer=l2(reg))(inputs)
            x = Dropout(dropout_rate)(x)
            x = Dense(units_layer2, activation=activation, kernel_regularizer=l2(reg))(x)
            x = Dropout(dropout_rate)(x)
            x = Dense(units_layer3, activation=activation, kernel_regularizer=l2(reg))(x)
            tower_outputs.append(x)
        concatenated = Concatenate()(tower_outputs)
        outputs = Dense(1, activation='linear')(concatenated)
        self.model = Model(inputs=inputs, outputs=outputs)
        optimizer = Adam(learning_rate=learning_rate)
        self.model.compile(optimizer=optimizer, loss='mean_squared_error')
        logger.info("MoE model built.")

    def train_model(self, trial=None):
        """Train the MoE model.

        Args:
            trial (optuna.Trial, optional): Optuna trial object for hyperparameter tuning.
        """
        early_stopping = EarlyStopping(monitor='val_loss', patience=5)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', patience=3)
        callbacks = [early_stopping, reduce_lr]
        if trial is not None:
            callbacks.append(TFKerasPruningCallback(trial, 'val_loss'))

        self.history = self.model.fit(
            self.X_train,
            self.y_train,
            validation_data=(self.X_test, self.y_test),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=0
        )
        logger.info("MoE model training completed.")

    def save_model(self):
        """Save the trained MoE model to disk."""
        self.model.save(self.config.model_save_path)
        logger.info(f"MoE model saved to {self.config.model_save_path}")
        # Save encoder and scaler
        encoder_path = self.config.model_save_path.replace('.keras', '_encoder.pth')
        torch.save(self.encoder.state_dict(), encoder_path)
        scaler_path = self.config.model_save_path.replace('.keras', '_scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info("Encoder and scaler saved.")

    def optimize_hyperparameters(self):
        """Optimize hyperparameters using Optuna."""
        def objective(trial):
            self.build_model(trial)
            self.train_model(trial)
            val_loss = self.history.history['val_loss'][-1]
            return val_loss

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=self.config.n_trials)
        logger.info(f"Best trial: {study.best_trial.number}")
        logger.info(f"Best value (loss): {study.best_trial.value}")
        for key, value in study.best_trial.params.items():
            logger.info(f"  {key}: {value}")

        # Save best parameters
        best_params_path = 'best_params_moe.pkl'
        with open(best_params_path, 'wb') as f:
            pickle.dump(study.best_trial.params, f)
        logger.info(f"Best parameters saved to {best_params_path}")

class GNNTrainer(BaseTrainer):
    """Trainer for Graph Neural Network (GNN) model.

    This class handles loading data, building the GNN model, training, and saving the model.

    Args:
        config (GNNConfig): Configuration object.
        input_path (str): Path to the input data.
        label_path (str): Path to the label data.
        use_best_params (bool, optional): If True, use best_params.pkl to initialize the model when n_trials == 0.
    """

    def __init__(self, config: GNNConfig, input_path: str, label_path: str, use_best_params=False):
        self.config = config
        self.input_path = input_path
        self.label_path = label_path
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_dim = self.config.embedding_dim
        self.train_data_list = None
        self.test_data_list = None
        self.use_best_params = use_best_params

        # Set random seed
        np.random.seed(self.config.seed)
        torch.manual_seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config.seed)

    def run(self):
        """Run the training process."""
        self.load_data()
        if self.config.n_trials > 0:
            self.optimize_hyperparameters()
        else:
            if self.use_best_params and os.path.exists(self.config.best_params_path):
                with open(self.config.best_params_path, 'rb') as f:
                    best_params = pickle.load(f)
                self.build_model(best_params)
            else:
                self.build_model()
            self.train_model()
            self.save_model()

    def load_data(self):
        """Load and preprocess data."""
        logger.info("Loading and preprocessing data for GNN model...")

        if self.config.use_embeddings:
            # Load precomputed embeddings
            embeddings_df, y_dict = load_csv_data(self.input_path, self.label_path)
            # Use the preprocessing function to create training and test data
            (
                graph_data_dict_train,
                graph_data_dict_test,
            ) = gnn_train_from_embeddings_preprocessing(embeddings_df, y_dict)
            # Combine data from all keys into single lists
            self.train_data_list = []
            self.test_data_list = []
            for key in graph_data_dict_train:
                self.train_data_list.extend(graph_data_dict_train[key])
                self.test_data_list.extend(graph_data_dict_test[key])
            logger.info(
                "Data loading and preprocessing completed using encoded embeddings."
            )
        else:
            logger.info("Loading and preprocessing data for GNN model...")
            (
                spatial_features,
                target_variables,
                file_names_df,
            ) = preprocess_data_training_gnn(
                self.input_path, required_columns, self.label_path
            )
            # Initialize and load the encoder using EncoderWrapper
            autoencoder = AutoencoderIncremental()
            autoencoder.eval()
            encoder = EncoderWrapper(autoencoder)
            encoder.eval()
            with torch.no_grad():
                encoded_data = encoder(spatial_features)
            encoded_data_list = encoded_data.numpy().tolist()
            encoded_df = pd.DataFrame({"Encoded_Data": encoded_data_list})
            embeddings_df = pd.concat(
                [file_names_df.reset_index(drop=True), encoded_df], axis=1
            )
            embeddings_df["Encoded_Data"] = embeddings_df["Encoded_Data"].apply(tuple)
            self.train_data_list, self.test_data_list = gnn_train_preprocessing(
                embeddings_df, target_variables
            )
            logger.info("Data loading and preprocessing completed.")

    def build_model(self, best_params=None):
        """Build the GNN model.

        Args:
            best_params (dict, optional): Dictionary of best hyperparameters.
        """
        if best_params is None:
            # Use default parameters
            best_params = {
                'learning_rate': self.config.learning_rate,
                'optimizer': 'Adam',
                'hidden_channels': 128,
                'num_layers': 3,
                'dropout_rate': 0.0,
                'weight_decay': 0.0,
                'activation': 'relu',
                'conv_type': 'GraphSAGE',
                'use_batch_norm': True,
                'use_residual': False,
            }
        self.model_parameters = best_params

        # Select activation function
        activation = get_activation_function(best_params['activation'])

        # Initialize the model
        self.model = EdgeRegressionGNN(
            in_channels=self.embedding_dim,
            hidden_channels=best_params['hidden_channels'],
            num_layers=best_params['num_layers'],
            dropout=best_params['dropout_rate'],
            activation=activation,
            conv_type=best_params['conv_type'],
            use_batch_norm=best_params['use_batch_norm'],
            use_residual=best_params['use_residual'],
        ).to(self.device)
        logger.info("GNN model built.")

    def train_model(self, trial=None):
        """Train the GNN model.

        Args:
            trial (optuna.Trial, optional): Optuna trial object for hyperparameter tuning.
        """
        optimizer_name = self.model_parameters.get('optimizer', 'Adam')
        learning_rate = self.model_parameters.get('learning_rate', 0.001)
        weight_decay = self.model_parameters.get('weight_decay', 0.0)

        if optimizer_name == 'Adam':
            optimizer = optim.Adam(
                self.model.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
            )
        elif optimizer_name == 'SGD':
            optimizer = optim.SGD(
                self.model.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
            )
        else:
            optimizer = optim.Adam(
                self.model.parameters(),
                lr=learning_rate,
                weight_decay=weight_decay,
            )

        # Prepare DataLoaders
        train_loader = DataLoader(self.train_data_list, batch_size=self.config.batch_size, shuffle=True)
        test_loader = DataLoader(self.test_data_list, batch_size=self.config.batch_size, shuffle=False)

        criterion = nn.MSELoss()

        for epoch in range(self.config.epochs):
            self.model.train()
            for data in train_loader:
                data = data.to(self.device)
                optimizer.zero_grad()
                out = self.model(data)
                loss = criterion(out, data.y)
                loss.backward()
                optimizer.step()

            # Validation step can be added here

        logger.info("GNN model training completed.")

    def save_model(self):
        """Save the trained GNN model to disk."""
        torch.save(self.model.state_dict(), self.config.model_save_path)
        logger.info(f"GNN model saved to {self.config.model_save_path}")
        # Save best parameters
        best_params_path = 'best_params_gnn.pkl'
        with open(best_params_path, 'wb') as f:
            pickle.dump(self.model_parameters, f)
        logger.info(f"Best parameters saved to {best_params_path}")

    def optimize_hyperparameters(self):
        """Optimize hyperparameters using Optuna."""
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'learning_rate': trial.suggest_loguniform('learning_rate', 1e-5, 1e-2),
                'optimizer': trial.suggest_categorical('optimizer', ['Adam', 'SGD']),
                'hidden_channels': trial.suggest_int('hidden_channels', 64, 512, step=64),
                'num_layers': trial.suggest_int('num_layers', 2, 5),
                'dropout_rate': trial.suggest_uniform('dropout_rate', 0.0, 0.5),
                'weight_decay': trial.suggest_loguniform('weight_decay', 1e-6, 1e-3),
                'activation': trial.suggest_categorical('activation', ['relu', 'tanh', 'leaky_relu']),
                'conv_type': trial.suggest_categorical('conv_type', ['GraphSAGE', 'GAT', 'GCN']),
                'use_batch_norm': trial.suggest_categorical('use_batch_norm', [True, False]),
                'use_residual': trial.suggest_categorical('use_residual', [True, False]),
            }
            self.build_model(params)
            self.train_model(trial)
            # Compute validation loss
            val_loss = self.evaluate_model()
            return val_loss

        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=self.config.n_trials)
        logger.info(f"Best trial: {study.best_trial.number}")
        logger.info(f"Best value (loss): {study.best_trial.value}")
        for key, value in study.best_trial.params.items():
            logger.info(f"  {key}: {value}")

        # Save best parameters
        self.model_parameters = study.best_trial.params
        best_params_path = self.config.best_params_path
        with open(best_params_path, 'wb') as f:
            pickle.dump(self.model_parameters, f)
        logger.info(f"Best parameters saved to {best_params_path}")

    def evaluate_model(self):
        """Evaluate the model on the validation set.

        Returns:
            float: Validation loss.
        """
        self.model.eval()
        test_loader = DataLoader(self.test_data_list, batch_size=self.config.batch_size, shuffle=False)
        criterion = nn.MSELoss()
        total_loss = 0
        with torch.no_grad():
            for data in test_loader:
                data = data.to(self.device)
                out = self.model(data)
                loss = criterion(out, data.y)
                total_loss += loss.item() * data.num_graphs
        val_loss = total_loss / len(self.test_data_list)
        return val_loss

# -------------------------------
# Helper Functions
# -------------------------------

def get_config(model_name: str):
    """Get the configuration class based on the model name.

    Args:
        model_name (str): Name of the model ('moe' or 'gnn').

    Returns:
        Config class instance.

    Raises:
        ValueError: If the model name is unsupported.
    """
    configs = {
        'moe': MoEConfig,
        'gnn': GNNConfig
    }
    if model_name not in configs:
        raise ValueError(f"Unsupported model: {model_name}")
    return configs[model_name]()

def get_trainer(model_name: str) -> Type[BaseTrainer]:
    """Get the trainer class based on the model name.

    Args:
        model_name (str): Name of the model ('moe' or 'gnn').

    Returns:
        Trainer class.

    Raises:
        ValueError: If the model name is unsupported.
    """
    trainers = {
        'moe': MoETrainer,
        'gnn': GNNTrainer
    }
    if model_name not in trainers:
        raise ValueError(f"Unsupported model: {model_name}")
    return trainers[model_name]

# -------------------------------
# Main Function
# -------------------------------

def main():
    """
    Main function to run the training process.

    Recommended commands to run at SiVista main directory:

    For MoE:
    python pex_extraction/regression/train.py --model moe --input_path pex_extraction/MUX21X1_metrics.csv --label_path pex_extraction/moe_label_example.csv

    For GNN:
    python pex_extraction/regression/train.py --model gnn --input_path pex_extraction/MUX21X1_metrics.csv --label_path pex_extraction/gnn_label_example.csv

    Please also review config settings prior to running the commands.
    """
    parser = argparse.ArgumentParser(description='Model Training Script')
    parser.add_argument('--model', type=str, choices=['moe', 'gnn'], required=True,
                        help='Choose the model to train: "moe" or "gnn"')
    parser.add_argument('--input_path', type=str, required=True,
                        help='Path to the input data')
    parser.add_argument('--label_path', type=str, required=True,
                        help='Path to the label data')
    parser.add_argument('--save_model_path', type=str, required=False,
                        help='Path to save the trained model')
    # Additional arguments for configurations
    parser.add_argument('--config', type=str, required=False,
                        help='Path to configuration JSON file')
    # Added argument to specify using best_params.pkl
    parser.add_argument('--use_best_params', action='store_true',
                        help='Use best_params.pkl to initialize the model when n_trials == 0')
    # Added argument to specify the path to best_params.pkl
    parser.add_argument('--best_params_path', type=str, required=False,
                        help='Path to the best_params.pkl file')
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
    config = get_config(args.model)

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

    # Update best_params_path if provided
    if args.best_params_path:
        if hasattr(config, 'best_params_path'):
            config.best_params_path = args.best_params_path
        else:
            logger.warning("This model does not support best_params_path.")

    config.isGAA = args.isGAA

    # Create trainer instance
    TrainerClass = get_trainer(args.model)
    if args.model == 'gnn':
        trainer = TrainerClass(config, args.input_path, args.label_path, use_best_params=args.use_best_params)
    else:
        trainer = TrainerClass(config, args.input_path, args.label_path)

    # Run the training process
    trainer.run()

if __name__ == "__main__":
    main()
