import torch
import torch.nn.functional as F
import argparse
import yaml
from pathlib import Path
from torch_geometric.loader import DataLoader
from resistance_gnn import (
    ResistanceRGCN, FlexibleResistanceRGCN, ResistanceDataset, 
    train_model, evaluate_model, train_model_for_optuna, evaluate_model_for_optuna,
    find_resistance_range_raw, find_resistance_range
)
from torch.utils.tensorboard import SummaryWriter
import time
from typing import Dict, Any
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import io
from PIL import Image
import torchviz
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import json
import pickle
"""
Command:
python train_resistance_gnn.py --config config/default_config.yaml
python train_resistance_gnn.py --optuna --n_trials 50
"""
import logging
from tqdm import tqdm
import math

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('training.log')  # Also save to file
    ]
)
logger = logging.getLogger('sivista_app')

def parse_args():
    parser = argparse.ArgumentParser(description='Train Resistance GNN Model')
    
    # Training parameters
    parser.add_argument('--config', type=str, help='Path to config YAML file')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--hidden_channels', type=int, default=64, help='Hidden channels in GNN')
    parser.add_argument('--max_grad_norm', type=float, default=1.0, help='Maximum gradient norm for clipping')
    
    # Data parameters
    parser.add_argument('--data_dir', type=str, default='../resistance_graphs_for_gnn', 
                       help='Directory containing resistance graph data')
    parser.add_argument('--train_split', type=float, default=0.8, 
                       help='Fraction of data to use for training')
    
    # Model parameters
    parser.add_argument('--save_dir', type=str, default='./models', 
                       help='Directory to save models')
    parser.add_argument('--device', type=str, 
                       default='cuda' if torch.cuda.is_available() else 'cpu',
                       help='Device to use for training (cuda/cpu)')
    
    # Add tech file argument
    parser.add_argument('--tech_file', type=str, 
                       default='tech/monCFET/monCFET.tech',
                       help='Path to the technology file')
    
    # Add split method argument
    parser.add_argument('--split_method', type=str, default='cell_type',
                       choices=['random', 'cell_type'],
                       help='Method to split dataset (random or cell_type)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for dataset splitting')
    
    # Add SWA arguments
    parser.add_argument('--swa', action='store_true', help='Use Stochastic Weight Averaging')
    parser.add_argument('--swa_start', type=float, default=0.75, 
                       help='SWA start epoch ratio (default: 0.75)')
    parser.add_argument('--swa_lr', type=float, default=1e-4, 
                       help='SWA learning rate (default: 1e-4)')
    parser.add_argument('--swa_freq', type=int, default=5, 
                       help='SWA model collection frequency in epochs (default: 5)')

    # Add weighted_loss argument
    parser.add_argument('--weighted_loss', action='store_true',
                        help='Use weighted MSE loss during training')
                        
    # Add Optuna arguments
    parser.add_argument('--optuna', action='store_true',
                        help='Use Optuna for hyperparameter optimization')
    parser.add_argument('--n_trials', type=int, default=100,
                        help='Number of Optuna trials to run')
    parser.add_argument('--study_name', type=str, default='resistance_gnn_optimization',
                        help='Name for the Optuna study')
    parser.add_argument('--storage', type=str, default=None,
                        help='Database URL for Optuna storage (optional)')

    # Add loss function argument
    parser.add_argument('--loss_type', type=str, default='mse',
                        choices=['mse', 'mape', 'huber'],
                        help='Type of loss function to use for training')

    return parser.parse_args()

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class LossTracker:
    """Track and smooth loss values"""
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.reset()
    
    def reset(self):
        self.losses = []
        self.current_sum = 0
        self.current_count = 0
    
    def update(self, loss_value: float) -> float:
        """Update with new loss value and return smoothed loss"""
        self.losses.append(loss_value)
        self.current_sum += loss_value
        self.current_count += 1
        
        if len(self.losses) > self.window_size:
            self.current_sum -= self.losses.pop(0)
            self.current_count -= 1
        
        return self.current_sum / self.current_count

class ModelAnalyzer:
    def __init__(self, log_dir: str, model: ResistanceRGCN, dataset: ResistanceDataset):
        """Initialize the analyzer with TensorBoard writer and model details"""
        self.writer = SummaryWriter(log_dir)
        self.model = model
        self.dataset = dataset
        self.start_time = time.time()
        
        # Define resistance bands for analysis (in Ohms)
        self.resistance_bands = [
            (0, 1), (1, 10), (10, 100), (100, 1000),
            (1000, 10000), (10000, float('inf'))
        ]
        
        # Define layer types for analysis
        self.layer_types = ['M0', 'PMOSGate', 'NMOSGate', 'PMOSInterconnect', 'NMOSInterconnect', 'VIA']
        
        # Initialize performance tracking
        self.fold_metrics = []
        self.layer_metrics = {layer: [] for layer in self.layer_types}
        
        # Add loss trackers
        self.train_loss_tracker = LossTracker(window_size=100)
        self.val_loss_tracker = LossTracker(window_size=100)
        
    def log_metrics(self, metrics: Dict[str, Any], step: int, prefix: str = ''):
        """Log all metrics to TensorBoard"""
        for space in metrics:
            for metric_name, value in metrics[space].items():
                # Track and smooth loss values
                if metric_name == 'mse':
                    if prefix == 'train':
                        smoothed_value = self.train_loss_tracker.update(value)
                        self.writer.add_scalar(f'{prefix}/{space}/{metric_name}_smooth', 
                                             smoothed_value, step)
                    elif prefix == 'test':
                        smoothed_value = self.val_loss_tracker.update(value)
                        self.writer.add_scalar(f'{prefix}/{space}/{metric_name}_smooth', 
                                             smoothed_value, step)
                
                # Log original value
                self.writer.add_scalar(f'{prefix}/{space}/{metric_name}', value, step)
                
                # Add special handling for MAE to make it more visible
                if metric_name == 'mae':
                    # Log MAE in both ohms and kilohms for better readability
                    self.writer.add_scalar(f'{prefix}/{space}/mae_ohms', value, step)
                    self.writer.add_scalar(f'{prefix}/{space}/mae_kohms', value/1000, step)

    def log_learning_rate(self, optimizer: torch.optim.Optimizer, step: int):
        """Log the current learning rate"""
        for i, param_group in enumerate(optimizer.param_groups):
            self.writer.add_scalar(f'learning_rate/group_{i}', param_group['lr'], step)

    def log_gradient_stats(self, step: int):
        """Log gradient statistics for each parameter"""
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                self.writer.add_histogram(f'gradients/{name}', param.grad, step)
                self.writer.add_scalar(f'gradient_norm/{name}', param.grad.norm(), step)

    def log_weight_stats(self, step: int):
        """Log weight statistics for each parameter"""
        for name, param in self.model.named_parameters():
            self.writer.add_histogram(f'weights/{name}', param.data, step)
            self.writer.add_scalar(f'weight_norm/{name}', param.data.norm(), step)

    def log_memory_usage(self, step: int):
        """Log GPU memory usage if available"""
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                memory_allocated = torch.cuda.memory_allocated(i) / 1024**2  # MB
                memory_reserved = torch.cuda.memory_reserved(i) / 1024**2    # MB
                self.writer.add_scalar(f'memory/gpu_{i}/allocated_mb', memory_allocated, step)
                self.writer.add_scalar(f'memory/gpu_{i}/reserved_mb', memory_reserved, step)

    def log_timing_stats(self, batch_time: float, step: int):
        """Log timing statistics"""
        self.writer.add_scalar('timing/batch_seconds', batch_time, step)
        elapsed_time = time.time() - self.start_time
        self.writer.add_scalar('timing/total_minutes', elapsed_time / 60, step)

    def log_node_embeddings(self, batch, step: int):
        """Log node embedding visualizations using t-SNE"""
        if not hasattr(self.model, 'node_encoder'):
            return
            
        with torch.no_grad():
            # Get node embeddings
            embeddings = self.model.node_encoder(batch.x).cpu().numpy()
            
            # Perform t-SNE
            tsne = TSNE(n_components=2, random_state=42)
            embeddings_2d = tsne.fit_transform(embeddings)
            
            # Create scatter plot
            plt.figure(figsize=(10, 10))
            plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.5)
            plt.title('Node Embeddings t-SNE Visualization')
            
            # Convert plot to image
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            image = Image.open(buf)
            image_tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1)
            
            self.writer.add_image('node_embeddings/tsne', image_tensor, step)
            plt.close()

    def log_error_distribution(self, pred: torch.Tensor, target: torch.Tensor, 
                             mask: torch.Tensor, step: int):
        """Log error distribution statistics"""
        with torch.no_grad():
            errors = (pred[mask] - target[mask]).cpu().numpy()
            self.writer.add_histogram('errors/distribution', errors, step)
            
            # Log error quartiles
            quartiles = np.percentile(errors, [25, 50, 75])
            self.writer.add_scalar('errors/q1', quartiles[0], step)
            self.writer.add_scalar('errors/median', quartiles[1], step)
            self.writer.add_scalar('errors/q3', quartiles[2], step)

    def log_model_graph(self, batch):
        """Log model graph structure"""
        try:
            self.writer.add_graph(self.model, (batch.x, batch.edge_index, 
                                             batch.edge_attr, batch.batch))
        except Exception as e:
            logger.warning(f"Warning: Could not log model graph: {e}")

    def log_resistance_band_analysis(self, pred: torch.Tensor, target: torch.Tensor, 
                                   mask: torch.Tensor, step: int):
        """Analyze performance across different resistance bands"""
        with torch.no_grad():
            # Denormalize predictions and targets using the appropriate transformation
            if hasattr(self.dataset, 'transform_mean') and hasattr(self.dataset, 'transform_std'):
                # First denormalize to transformed space
                pred_norm = pred * self.dataset.transform_std + self.dataset.transform_mean
                target_norm = target * self.dataset.transform_std + self.dataset.transform_mean
                
                # Then inverse transform to original space
                pred_denorm = self.dataset._inverse_transform_values(pred_norm)
                target_denorm = self.dataset._inverse_transform_values(target_norm)
            else:
                # Fallback to log transform if the dataset doesn't have the new attributes
                pred_denorm = torch.exp(pred * self.dataset.log_std + self.dataset.log_mean)
                target_denorm = torch.exp(target * self.dataset.log_std + self.dataset.log_mean)
            
            # Calculate metrics for each resistance band
            for band_min, band_max in self.resistance_bands:
                band_mask = mask & (target_denorm >= band_min) & (target_denorm < band_max)
                if not band_mask.any():
                    continue
                
                # Calculate band-specific metrics
                mape = torch.mean(torch.abs((pred_denorm[band_mask] - target_denorm[band_mask]) / 
                                      target_denorm[band_mask])) * 100
                rmse = torch.sqrt(F.mse_loss(pred[band_mask], target[band_mask]))
                
                # Log metrics
                self.writer.add_scalar(f'resistance_bands/{band_min}-{band_max}/mape', mape, step)
                self.writer.add_scalar(f'resistance_bands/{band_min}-{band_max}/rmse', rmse, step)
                
                # Log error distribution for this band
                errors = (pred_denorm[band_mask] - target_denorm[band_mask]).cpu().numpy()
                self.writer.add_histogram(f'resistance_bands/{band_min}-{band_max}/errors', 
                                        errors, step)

    def log_layer_specific_analysis(self, batch, pred: torch.Tensor, target: torch.Tensor, 
                                  mask: torch.Tensor, step: int):
        """Analyze performance for different layer types"""
        with torch.no_grad():
            for layer_type in self.layer_types:
                # Convert float values to boolean using threshold
                layer_idx = self.layer_types.index(layer_type)
                source_mask = batch.x[:, layer_idx][batch.edge_index[0]] > 0.5
                target_mask = batch.x[:, layer_idx][batch.edge_index[1]] > 0.5
                
                # Use logical OR instead of bitwise OR
                layer_mask = torch.logical_or(source_mask, target_mask)
                combined_mask = mask & layer_mask
                
                if not combined_mask.any():
                    continue
                
                # Calculate layer-specific metrics
                mse = F.mse_loss(pred[combined_mask], target[combined_mask])
                self.writer.add_scalar(f'layers/{layer_type}/mse', mse, step)
                
                # Track metrics for stability analysis
                self.layer_metrics[layer_type].append(mse.item())

    def log_prediction_confidence(self, pred: torch.Tensor, target: torch.Tensor, 
                                mask: torch.Tensor, step: int):
        """Analyze prediction confidence and uncertainty"""
        with torch.no_grad():
            # Calculate absolute errors
            errors = torch.abs(pred[mask] - target[mask])
            
            # Identify high-error cases (>2 std from mean)
            error_mean = errors.mean()
            error_std = errors.std()
            high_error_mask = errors > (error_mean + 2 * error_std)
            
            # Log high-error case frequency
            high_error_rate = high_error_mask.float().mean()
            self.writer.add_scalar('confidence/high_error_rate', high_error_rate, step)
            
            # Log error distribution statistics
            self.writer.add_scalar('confidence/error_mean', error_mean, step)
            self.writer.add_scalar('confidence/error_std', error_std, step)

    def log_model_stability(self, metrics: Dict[str, Any], step: int):
        """Track model stability across training"""
        self.fold_metrics.append(metrics)
        
        if len(self.fold_metrics) > 1:
            # Calculate stability metrics
            metric_stability = {}
            for space in metrics:
                for metric_name in metrics[space]:
                    values = [fold[space][metric_name] for fold in self.fold_metrics[-10:]]
                    metric_stability[f'{space}/{metric_name}/std'] = np.std(values)
                    metric_stability[f'{space}/{metric_name}/range'] = max(values) - min(values)
            
            # Log stability metrics
            for name, value in metric_stability.items():
                self.writer.add_scalar(f'stability/{name}', value, step)

    def log_hyperparameter_impact(self, step: int):
        """Analyze impact of various hyperparameters"""
        # Log dropout impact
        if hasattr(self.model, 'edge_mlp'):
            for name, module in self.model.edge_mlp.named_modules():
                if isinstance(module, torch.nn.Dropout):
                    dropped_ratio = module.p * (module.training)
                    self.writer.add_scalar(f'hyperparameters/dropout/{name}', dropped_ratio, step)
        
        # Log layer-wise activation statistics
        for name, module in self.model.named_modules():
            if isinstance(module, (torch.nn.ReLU, torch.nn.LayerNorm)):
                if hasattr(module, 'weight'):
                    self.writer.add_histogram(f'hyperparameters/layer_stats/{name}/weight', 
                                           module.weight, step)
                if hasattr(module, 'bias'):
                    self.writer.add_histogram(f'hyperparameters/layer_stats/{name}/bias', 
                                           module.bias, step)

    def log_cross_validation_metrics(self, fold_metrics: Dict[str, Any], fold: int, step: int):
        """Log metrics for cross-validation analysis"""
        for space in fold_metrics:
            for metric_name, value in fold_metrics[space].items():
                self.writer.add_scalar(f'cross_validation/fold_{fold}/{space}/{metric_name}', 
                                     value, step)

    def log_batch_analysis(self, batch, pred: torch.Tensor, target: torch.Tensor, 
                          mask: torch.Tensor, step: int):
        """Comprehensive batch analysis"""
        self.log_resistance_band_analysis(pred, target, mask, step)
        self.log_layer_specific_analysis(batch, pred, target, mask, step)
        self.log_prediction_confidence(pred, target, mask, step)
        self.log_hyperparameter_impact(step)
        
        # Update stability metrics
        metrics = {
            'normalized': {
                'mse': F.mse_loss(pred[mask], target[mask]).item(),
                'rmse': torch.sqrt(F.mse_loss(pred[mask], target[mask])).item()
            }
        }
        self.log_model_stability(metrics, step)

    def close(self):
        """Close the TensorBoard writer"""
        self.writer.close()

class EarlyStopping:
    """Early stops the training if validation loss doesn't improve after a given patience."""
    def __init__(self, patience=15, min_delta=1e-4, min_epochs=30):
        """
        Args:
            patience (int): How many epochs to wait after last improvement
            min_delta (float): Minimum change in monitored value to qualify as an improvement
            min_epochs (int): Minimum number of epochs to train before allowing early stopping
        """
        self.patience = patience
        self.min_delta = min_delta
        self.min_epochs = min_epochs
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        self.best_epoch = 0
        
    def __call__(self, val_loss, epoch):
        """
        Args:
            val_loss (float): Validation loss (using denormalized MAE)
            epoch (int): Current epoch number
        """
        if epoch < self.min_epochs:
            return
            
        if self.best_loss is None:
            self.best_loss = val_loss
            self.best_epoch = epoch
        elif val_loss > self.best_loss - self.min_delta:  # No improvement
            self.counter += 1
            if self.counter >= self.patience:
                logger.info(f"Early stopping triggered. Best MAE: {self.best_loss:.4f} Ω at epoch {self.best_epoch}")
                self.early_stop = True
        else:  # Improvement
            self.best_loss = val_loss
            self.best_epoch = epoch
            self.counter = 0
            logger.info(f"Validation MAE improved to: {self.best_loss:.4f} Ω")

def split_dataset(dataset, train_split=0.8, split_method='random', seed=42):
    """
    Split dataset using either random split or cell-type-based split.
    
    Args:
        dataset: ResistanceDataset instance
        train_split (float): Fraction of data for training (default: 0.8)
        split_method (str): Either 'random' or 'cell_type'
        seed (int): Random seed for reproducibility
        
    Returns:
        train_dataset, test_dataset
    """
    if split_method == 'random':
        # Set seed for reproducibility
        torch.manual_seed(seed)
        
        # Simple random split
        train_size = int(len(dataset) * train_split)
        test_size = len(dataset) - train_size
        train_dataset, test_dataset = torch.utils.data.random_split(
            dataset, [train_size, test_size]
        )
        
        logger.info(f"\nRandom split:")
        logger.info(f"Training samples: {len(train_dataset)}")
        logger.info(f"Testing samples: {len(test_dataset)}")
        
    elif split_method == 'cell_type':
        # Group files by cell type
        cell_type_groups = {}
        total_samples = 0
        for idx in range(len(dataset)):
            file_path = dataset.graph_files[idx]
            cell_type = file_path.split('/')[-1].split('_')[0]
            if cell_type not in cell_type_groups:
                cell_type_groups[cell_type] = []
            cell_type_groups[cell_type].append(idx)
            total_samples += 1

        # Calculate target number of training samples
        target_train_samples = int(total_samples * train_split)
        
        # Sort cell types by size for better distribution
        sorted_cell_types = sorted(cell_type_groups.keys(), 
                                 key=lambda x: len(cell_type_groups[x]), 
                                 reverse=True)
        
        train_indices = []
        test_indices = []
        current_train_samples = 0
        
        # Distribute cell types to maintain approximate train_split ratio
        for cell_type in sorted_cell_types:
            cell_samples = len(cell_type_groups[cell_type])
            
            # If adding this cell type keeps us closer to target ratio, add to train
            if abs((current_train_samples + cell_samples) / total_samples - train_split) < \
               abs(current_train_samples / total_samples - train_split):
                train_indices.extend(cell_type_groups[cell_type])
                current_train_samples += cell_samples
            else:
                test_indices.extend(cell_type_groups[cell_type])
        
        # Log detailed split information
        logger.info(f"\nCell type split details:")
        logger.info(f"Total samples: {total_samples}")
        logger.info(f"Target train samples: {target_train_samples} ({train_split:.1%})")
        logger.info(f"Actual train samples: {len(train_indices)} ({len(train_indices)/total_samples:.1%})")
        logger.info(f"Test samples: {len(test_indices)} ({len(test_indices)/total_samples:.1%})")
        
        train_cell_types = {ct for ct in sorted_cell_types if any(i in train_indices for i in cell_type_groups[ct])}
        test_cell_types = {ct for ct in sorted_cell_types if any(i in test_indices for i in cell_type_groups[ct])}
        
        logger.info(f"\nTraining cell types ({len(train_cell_types)}):")
        for ct in train_cell_types:
            samples = len([i for i in train_indices if i in cell_type_groups[ct]])
            logger.info(f"  {ct}: {samples} samples")
            
        logger.info(f"\nTesting cell types ({len(test_cell_types)}):")
        for ct in test_cell_types:
            samples = len([i for i in test_indices if i in cell_type_groups[ct]])
            logger.info(f"  {ct}: {samples} samples")
        
        train_dataset = torch.utils.data.Subset(dataset, train_indices)
        test_dataset = torch.utils.data.Subset(dataset, test_indices)
    
    else:
        raise ValueError(f"Unknown split method: {split_method}. Use 'random' or 'cell_type'")
    
    return train_dataset, test_dataset

def huber_loss(pred, target, mask=None, dataset=None, delta=1.0):
    """Huber loss calculated in original resistance units"""
    if mask is None:
        mask = torch.ones_like(target, dtype=torch.bool)
    
    # Convert predictions and targets back to original units
    pred_orig = torch.exp(pred * dataset.log_std + dataset.log_mean)
    target_orig = torch.exp(target * dataset.log_std + dataset.log_mean)
    
    # Calculate Huber loss in original units
    diff = pred_orig[mask] - target_orig[mask]
    abs_diff = torch.abs(diff)
    quadratic = torch.min(abs_diff, torch.tensor(delta))
    linear = abs_diff - quadratic
    return torch.mean(0.5 * quadratic.pow(2) + delta * linear)

def objective(trial, dataset, train_dataset, test_dataset, device, config):
    """Optuna objective function for hyperparameter optimization"""
    # Sample hyperparameters
    # Model architecture parameters
    hidden_channels = trial.suggest_categorical('hidden_channels', [32, 64, 96, 128, 192, 256])
    num_layers = trial.suggest_int('num_layers', 2, 4)
    dropout_rate = trial.suggest_float('dropout_rate', 0.1, 0.5)
    
    # Optimization parameters
    learning_rate = trial.suggest_float('learning_rate', 1e-5, 5e-3, log=True)
    weight_decay = trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True)
    batch_size = trial.suggest_categorical('batch_size', [8, 16, 32, 64])
    
    # Learning rate schedule parameters
    use_warmup = trial.suggest_categorical('use_warmup', [True, False])
    
    if use_warmup:
        warmup_ratio = trial.suggest_float('warmup_ratio', 0.05, 0.2)
        scheduler_type = trial.suggest_categorical('scheduler_type', ['cosine', 'linear', 'constant'])
    
    # SWA parameters
    use_swa = trial.suggest_categorical('use_swa', [True, False])
    
    if use_swa:
        swa_start_ratio = trial.suggest_float('swa_start_ratio', 0.65, 0.8)
        swa_lr = trial.suggest_float('swa_lr', 5e-5, 5e-4, log=True)
    
    # Add loss type to hyperparameters
    loss_type = trial.suggest_categorical('loss_type', ['mse', 'mape', 'huber'])
    
    # Create data loaders with the sampled batch size
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True
    )
    test_loader = DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        shuffle=False
    )
    
    # Create model with sampled architecture parameters
    model = FlexibleResistanceRGCN(
        num_node_features=dataset.num_node_features,
        num_edge_features=dataset.num_edge_features,
        hidden_channels=hidden_channels,
        num_relations=4,  # Fixed value
        num_layers=num_layers,
        dropout_rate=dropout_rate
    ).to(device)
    
    # Create optimizer with sampled learning rate and weight decay
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
        betas=(0.9, 0.999)
    )
    
    # Use fewer epochs for Optuna trials (30 instead of config['epochs'])
    optuna_epochs = 30
    
    # Set up learning rate scheduler based on sampled parameters
    num_training_steps = optuna_epochs * len(train_loader)
    
    if use_warmup:
        num_warmup_steps = int(num_training_steps * warmup_ratio)
        
        def lr_lambda(current_step):
            if current_step < num_warmup_steps:
                return float(current_step) / float(max(1, num_warmup_steps))
            
            if scheduler_type == 'constant':
                return 1.0
            
            progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
            
            if scheduler_type == 'linear':
                return max(0.0, 1.0 - progress)
            elif scheduler_type == 'cosine':
                return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
        
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    else:
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5, verbose=False)
    
    # Set up SWA if enabled
    if use_swa:
        swa_start = int(optuna_epochs * swa_start_ratio)
        swa_scheduler = torch.optim.swa_utils.SWALR(optimizer, swa_lr=swa_lr)
        swa_model = torch.optim.swa_utils.AveragedModel(model)
    
    # Training loop
    best_score = float('-inf')
    best_metrics = None
    
    # Create progress bar for epochs
    pbar = tqdm(range(optuna_epochs), desc=f"Trial {trial.number}")
    
    for epoch in pbar:
        # Train for one epoch with selected loss type
        train_metrics = train_model_for_optuna(
            model, train_loader, device, optimizer, dataset,
            max_grad_norm=config.get('max_grad_norm', 1.0),
            weighted_loss=config.get('weighted_loss', False),
            loss_type=loss_type
        )
        
        # Update learning rate scheduler
        if use_warmup:
            scheduler.step()
        
        # Handle SWA if enabled
        if use_swa and epoch >= swa_start:
            if (epoch - swa_start) % config.get('swa_freq', 5) == 0:
                swa_model.update_parameters(model)
                swa_scheduler.step()
        
        # Evaluate periodically
        if epoch % 5 == 0 or epoch == optuna_epochs - 1:
            if use_swa and epoch >= swa_start:
                # Update SWA batch norm statistics
                torch.optim.swa_utils.update_bn(train_loader, swa_model, device=device)
                # Evaluate SWA model
                test_metrics = evaluate_model_for_optuna(swa_model, test_loader, device, dataset)
            else:
                # Regular evaluation
                test_metrics = evaluate_model_for_optuna(model, test_loader, device, dataset)
            
            # Calculate composite score (70% MAE, 30% R2)
            # For MAE, lower is better, so we negate it
            mae_score = -test_metrics['denormalized']['mae']
            r2_score = test_metrics['denormalized']['log_r2']
            
            # Normalize scores to [0, 1] range (approximately)
            # These bounds are based on typical values observed
            normalized_mae = (mae_score + 1000) / 1000  # Assuming MAE is typically 0-1000
            normalized_r2 = (r2_score + 1) / 2  # R2 is typically -1 to 1
            
            # Combine with weights
            composite_score = 0.7 * normalized_mae + 0.3 * normalized_r2
            
            # Report intermediate value to Optuna
            trial.report(composite_score, epoch)
            
            # Update progress bar with metrics
            pbar.set_postfix({
                'MAE': f"{test_metrics['denormalized']['mae']:.2f}Ω",
                'R2': f"{test_metrics['denormalized']['log_r2']:.3f}",
                'Score': f"{composite_score:.3f}"
            })
            
            # Handle pruning
            if trial.should_prune():
                pbar.close()
                raise optuna.exceptions.TrialPruned()
            
            # Track best score
            if composite_score > best_score:
                best_score = composite_score
                best_metrics = test_metrics
    
    pbar.close()
    
    # Log final metrics for this trial
    logger.info(f"Trial {trial.number} completed - "
               f"MAE: {best_metrics['denormalized']['mae']:.2f}Ω, "
               f"R2: {best_metrics['denormalized']['log_r2']:.3f}, "
               f"Score: {best_score:.3f}")
    
    # Return the best metrics for this trial
    return best_score, best_metrics

def run_optuna_study(dataset, train_dataset, test_dataset, device, config):
    """Run Optuna hyperparameter optimization study with improved performance"""
    study_name = config.get('study_name', 'resistance_gnn_optimization')
    n_trials = config.get('n_trials', 100)
    
    # Use in-memory storage by default for faster initialization
    storage = config.get('storage', None)
    
    # Create pruner with fewer startup trials for faster feedback
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=5)
    
    # Initialize with simpler configuration for better startup performance
    sampler = TPESampler(seed=config['seed'], n_startup_trials=5)
    
    # Print info to show initialization progress
    logger.info("Creating Optuna study...")
    
    # Create study with optimized configuration
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction='maximize',
        pruner=pruner,
        sampler=sampler,
        load_if_exists=True
    )
    
    # Add progress indicator
    logger.info(f"Starting Optuna study with {n_trials} trials")
    
    def objective_wrapper(trial):
        # Add progress indicator for each trial
        logger.info(f"Starting trial {trial.number + 1}/{n_trials}")
        score, metrics = objective(trial, dataset, train_dataset, test_dataset, device, config)
        
        # Log metrics for this trial
        logger.info(f"Trial {trial.number + 1} completed:")
        logger.info(f"  Score: {score:.4f}")
        logger.info(f"  Denormalized MAE: {metrics['denormalized']['mae']:.4f} Ω")
        logger.info(f"  Denormalized R2: {metrics['denormalized']['log_r2']:.4f}")
        
        return score
    
    study.optimize(objective_wrapper, n_trials=n_trials)
    
    # Get best trial
    best_trial = study.best_trial
    
    logger.info("Best trial:")
    logger.info(f"  Value: {best_trial.value:.4f}")
    logger.info("  Params:")
    for key, value in best_trial.params.items():
        logger.info(f"    {key}: {value}")
    
    # Run best trial again to get metrics
    trial = optuna.trial.FixedTrial(best_trial.params)
    _, best_metrics = objective(trial, dataset, train_dataset, test_dataset, device, config)
    
    logger.info("Best trial metrics:")
    logger.info(f"Normalized - MSE: {best_metrics['normalized']['mse']:.4f}, "
              f"RMSE: {best_metrics['normalized']['rmse']:.4f}, "
              f"R2: {best_metrics['normalized']['r2']:.4f}")
    logger.info(f"Denormalized - R2: {best_metrics['denormalized']['log_r2']:.4f}, "
              f"MAPE: {best_metrics['denormalized']['mape']:.2f}%, "
              f"MAE: {best_metrics['denormalized']['mae']:.4f} Ω")
    
    # Save best parameters as JSON file
    save_dir = Path(config['save_dir'])
    save_dir.mkdir(parents=True, exist_ok=True)
    
    with open(save_dir / 'best_params.json', 'w') as f:
        json.dump(best_trial.params, f, indent=2)
    
    # Train final model with best parameters
    train_final_model_with_best_params(best_trial.params, dataset, train_dataset, test_dataset, device, config)
    
    return best_trial.params, best_metrics

def train_final_model_with_best_params(best_params, dataset, train_dataset, test_dataset, device, config):
    """Train final model with the best parameters found by Optuna"""
    logger.info("Training final model with best parameters...")
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=best_params['batch_size'], 
        shuffle=True
    )
    test_loader = DataLoader(
        test_dataset, 
        batch_size=best_params['batch_size'], 
        shuffle=False
    )
    
    # Create model with fixed num_relations=4
    model = FlexibleResistanceRGCN(
        num_node_features=dataset.num_node_features,
        num_edge_features=dataset.num_edge_features,
        hidden_channels=best_params['hidden_channels'],
        num_relations=4,  # Fixed value
        num_layers=best_params['num_layers'],
        dropout_rate=best_params['dropout_rate']
    ).to(device)
    
    # Create optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=best_params['learning_rate'],
        weight_decay=best_params['weight_decay'],
        betas=(0.9, 0.999)
    )
    
    # Set up learning rate scheduler
    num_training_steps = config['epochs'] * len(train_loader)
    
    if best_params.get('use_warmup', False):
        warmup_ratio = best_params['warmup_ratio']
        scheduler_type = best_params['scheduler_type']
        num_warmup_steps = int(num_training_steps * warmup_ratio)
        
        def lr_lambda(current_step):
            if current_step < num_warmup_steps:
                return float(current_step) / float(max(1, num_warmup_steps))
            
            if scheduler_type == 'constant':
                return 1.0
            
            progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
            
            if scheduler_type == 'linear':
                return max(0.0, 1.0 - progress)
            elif scheduler_type == 'cosine':
                return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
        
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    else:
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10, verbose=True
        )
    
    # Set up SWA if enabled
    if best_params.get('use_swa', False):
        swa_start_ratio = best_params['swa_start_ratio']
        swa_lr = best_params['swa_lr']
        swa_start = int(config['epochs'] * swa_start_ratio)
        swa_scheduler = torch.optim.swa_utils.SWALR(optimizer, swa_lr=swa_lr)
        swa_model = torch.optim.swa_utils.AveragedModel(model)
        
        # Update config for train_with_analysis
        config['swa'] = True
        config['swa_start'] = swa_start_ratio
        config['swa_lr'] = swa_lr
    
    # Train with full analysis
    best_metrics = train_with_analysis(
        model=model,
        train_loader=train_loader,
        test_loader=test_loader,
        device=device,
        optimizer=optimizer,
        scheduler=scheduler,
        dataset=dataset,
        config=config,
        loss_type=best_params['loss_type']
    )
    
    # Save final model
    save_dir = Path(config['save_dir'])
    save_dict = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'test_metrics': best_metrics,
        'transform_mean': dataset.transform_mean,
        'transform_std': dataset.transform_std,
        'params': best_params
    }
    
    torch.save(save_dict, save_dir / 'final_model.pt')
    
    return best_metrics

def train_with_analysis(model: ResistanceRGCN, train_loader: DataLoader, 
                       test_loader: DataLoader, device: torch.device,
                       optimizer: torch.optim.Optimizer, scheduler,
                       dataset: ResistanceDataset, config: dict,
                       loss_type: str = 'mse'):
    """Enhanced training loop with analysis and optional SWA"""
    
    # Initialize SWA if enabled
    if config.get('swa', False):
        swa_start = int(config['epochs'] * config['swa_start'])
        swa_scheduler = torch.optim.swa_utils.SWALR(
            optimizer, swa_lr=config['swa_lr']
        )
        swa_model = torch.optim.swa_utils.AveragedModel(model)
        logger.info(f"SWA enabled - Starting at epoch {swa_start}")
    
    # Initialize analyzer
    analyzer = ModelAnalyzer(
        log_dir=Path(config['save_dir']) / 'tensorboard',
        model=model,
        dataset=dataset
    )
    
    early_stopping = EarlyStopping(
        patience=15,        # Increased patience
        min_delta=1e-4,    # Small threshold for improvement
        min_epochs=30      # Minimum training epochs
    )
    
    # Log model graph with first batch
    try:
        first_batch = next(iter(train_loader)).to(device)
        analyzer.log_model_graph(first_batch)
    except Exception as e:
        logger.warning(f"Failed to log model graph: {e}")
    
    best_test_metrics = {
        'normalized': {'mse': float('inf'), 'rmse': float('inf'), 'r2': float('-inf')},
        'denormalized': {'log_r2': float('-inf'), 'mape': float('inf')}
    }
    # Add cosine learning rate scheduler with warm-up
    num_training_steps = config['epochs'] * len(train_loader)
    num_warmup_steps = num_training_steps // 10  # 10% of total steps for warm-up
    
    def lr_lambda(current_step: int):
        # Warm-up phase
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        # Cosine decay phase
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
    
    # Create combined scheduler
    warmup_cosine_scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    for epoch in tqdm(range(config['epochs']), desc="Training"):
        batch_start_time = time.time()
        
        try:
            # Train epoch with selected loss type
            train_metrics = train_model(
                model, train_loader, device, optimizer, dataset,
                max_grad_norm=config['max_grad_norm'],
                weighted_loss=config['weighted_loss'],
                loss_type=loss_type
            )
            
            # Evaluate with appropriate model
            if config.get('swa', False) and epoch >= swa_start:
                if (epoch - swa_start) % config['swa_freq'] == 0:
                    swa_model.update_parameters(model)
                    swa_scheduler.step()
                # Update SWA batch norm statistics
                torch.optim.swa_utils.update_bn(
                    train_loader, swa_model, device=device
                )
                # Evaluate SWA model
                test_metrics = evaluate_model(swa_model, test_loader, device, dataset)
                analyzer.log_metrics(test_metrics, epoch, prefix='swa_test')
            else:
                # Regular evaluation
                test_metrics = evaluate_model(model, test_loader, device, dataset)
                analyzer.log_metrics(test_metrics, epoch, prefix='test')
                # Regular scheduling only if not in SWA phase
                warmup_cosine_scheduler.step()
                scheduler.step(test_metrics['denormalized']['mae'])
            
            # Use denormalized MAE for early stopping
            # early_stopping(test_metrics['denormalized']['mae'], epoch)
            # if early_stopping.early_stop:
            #     logger.info(f"Early stopping triggered at epoch {epoch}")
            #     break
            
            # Log training metrics
            analyzer.log_metrics(train_metrics, epoch, prefix='train')
            analyzer.log_learning_rate(optimizer, epoch)
            analyzer.log_gradient_stats(epoch)
            analyzer.log_weight_stats(epoch)
            analyzer.log_memory_usage(epoch)
            
            # Calculate batch time and log
            batch_time = time.time() - batch_start_time
            analyzer.log_timing_stats(batch_time, epoch)
            
            # Log node embeddings periodically
            if epoch % 10 == 0:
                analyzer.log_node_embeddings(first_batch, epoch)
            
            # Update best metrics and save model if improved
            if test_metrics['normalized']['mse'] < best_test_metrics['normalized']['mse']:
                best_test_metrics = test_metrics
                save_dict = {
                    'epoch': epoch,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                    'test_metrics': test_metrics,
                    'transform_mean': dataset.transform_mean,
                    'transform_std': dataset.transform_std
                }
                
                if config.get('swa', False) and epoch >= swa_start:
                    save_dict['model_state_dict'] = swa_model.state_dict()
                    save_dict['is_swa_model'] = True
                else:
                    save_dict['model_state_dict'] = model.state_dict()
                    save_dict['is_swa_model'] = False
                
                torch.save(save_dict, Path(config['save_dir']) / 'best_model.pt')
                
                # Also save normalization parameters separately for easier access
                torch.save({
                    'transform_mean': dataset.transform_mean,
                    'transform_std': dataset.transform_std,
                    'training_date': time.strftime('%Y-%m-%d %H:%M:%S')
                }, Path(config['save_dir']) / 'normalization_params.pt')
            
            # Print progress every 10 epochs
            if (epoch + 1) % 10 == 0:
                logger.info(f'Epoch {epoch+1:03d}')
                logger.info(f'Train Normalized - MSE: {train_metrics["normalized"]["mse"]:.4f}, '
                          f'RMSE: {train_metrics["normalized"]["rmse"]:.4f}, '
                          f'R2: {train_metrics["normalized"]["r2"]:.4f}')
                logger.info(f'Train Denormalized - R2: {train_metrics["denormalized"]["log_r2"]:.4f}, '
                          f'MAPE: {train_metrics["denormalized"]["mape"]:.2f}%, '
                          f'MAE: {train_metrics["denormalized"]["mae"]:.4f} Ω')
                logger.info(f'Test Normalized - MSE: {test_metrics["normalized"]["mse"]:.4f}, '
                          f'RMSE: {test_metrics["normalized"]["rmse"]:.4f}, '
                          f'R2: {test_metrics["normalized"]["r2"]:.4f}')
                logger.info(f'Test Denormalized - R2: {test_metrics["denormalized"]["log_r2"]:.4f}, '
                          f'MAPE: {test_metrics["denormalized"]["mape"]:.2f}%, '
                          f'MAE: {test_metrics["denormalized"]["mae"]:.4f} Ω\n')
                
            # Enhanced analysis for each batch
            for batch_idx, batch in enumerate(train_loader):
                batch = batch.to(device)
                pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
                analyzer.log_batch_analysis(batch, pred, batch.y.squeeze(), batch.edge_mask, 
                                         epoch * len(train_loader) + batch_idx)
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            raise
    
    # Final SWA update if enabled
    if config.get('swa', False):
        torch.optim.swa_utils.update_bn(train_loader, swa_model, device=device)
        final_swa_metrics = evaluate_model(swa_model, test_loader, device, dataset)
        logger.info("\nFinal SWA Model Metrics:")
        logger.info(f"Normalized - MSE: {final_swa_metrics['normalized']['mse']:.4f}, "
                   f"RMSE: {final_swa_metrics['normalized']['rmse']:.4f}, "
                   f"R2: {final_swa_metrics['normalized']['r2']:.4f}")
        logger.info(f"Denormalized - R2: {final_swa_metrics['denormalized']['log_r2']:.4f}, "
                   f"MAPE: {final_swa_metrics['denormalized']['mape']:.2f}%, "
                   f"MAE: {final_swa_metrics['denormalized']['mae']:.4f} Ω")
    
    # Close analyzer
    analyzer.close()
    
    return best_test_metrics

def main():
    args = parse_args()
    
    # Load config if provided, otherwise use command line args
    if args.config:
        config = load_config(args.config)
    else:
        config = vars(args)
    
    # Create save directory if it doesn't exist
    save_dir = Path(config['save_dir'])
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Set device
    device = torch.device(config['device'])
    
    # Create dataset with outlier removal enabled
    dataset = ResistanceDataset(
        config['data_dir'],
        remove_outliers=False,
        transform_type=config['transform_type'],
        outlier_z_threshold=3.0  # You can adjust this threshold as needed
    )
    
    # Find raw resistance range before log transform
    min_res_raw, max_res_raw = find_resistance_range_raw(dataset)
    logger.info(f"Raw resistance range: {min_res_raw:.4e} - {max_res_raw:.4e} ohms (span: {max_res_raw/min_res_raw:.2e}x)")
    
    # Find normalized resistance range after log transform
    min_res_norm, max_res_norm = find_resistance_range(dataset)
    logger.info(f"Normalized resistance range: {min_res_norm:.4f} - {max_res_norm:.4f} ({dataset.transform_type}-space)")
   
    # Split dataset using specified method
    train_dataset, test_dataset = split_dataset(
        dataset,
        train_split=config['train_split'],
        split_method=config['split_method'],
        seed=config['seed']
    )
    
    # Check if we should run Optuna
    if args.optuna or config.get('optuna', False):
        logger.info("Initializing dataset for Optuna...")
        logger.info("Dataset loading complete. Starting hyperparameter optimization...")
        best_params, _ = run_optuna_study(
            dataset, train_dataset, test_dataset, device, config
        )
        logger.info("Optuna optimization completed")
        return
    
    # Regular training without Optuna
    # Create data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config['batch_size'], 
        shuffle=True
    )
    test_loader = DataLoader(
        test_dataset, 
        batch_size=config['batch_size'], 
        shuffle=False
    )
    
    # Create model
    model = ResistanceRGCN(
        num_node_features=dataset.num_node_features,
        num_edge_features=dataset.num_edge_features,
        hidden_channels=config['hidden_channels'],
        num_relations=config['num_relations']
    ).to(device)
    
    # Create optimizer with momentum for better SWA performance
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config['learning_rate'],
        betas=(0.9, 0.999)  # Default AdamW momentum parameters
    )
    
    # Add learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=10,
        verbose=True
    )
    
    # Train with analysis and specified loss type
    best_metrics = train_with_analysis(
        model=model,
        train_loader=train_loader,
        test_loader=test_loader,
        device=device,
        optimizer=optimizer,
        scheduler=scheduler,
        dataset=dataset,
        config=config,
        loss_type=config.get('loss_type', 'mse')  # Use specified loss type
    )
    
    logger.info("Training completed. Best metrics:")
    logger.info(f"Normalized - MSE: {best_metrics['normalized']['mse']:.4f}, "
              f"RMSE: {best_metrics['normalized']['rmse']:.4f}, "
              f"R2: {best_metrics['normalized']['r2']:.4f}")
    logger.info(f"Denormalized - R2: {best_metrics['denormalized']['log_r2']:.4f}, "
              f"MAPE: {best_metrics['denormalized']['mape']:.2f}%, "
              f"MAE: {best_metrics['denormalized']['mae']:.4f} Ω")

if __name__ == '__main__':
    main() 