import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from torch_geometric.data import Data, Dataset, DataLoader
import networkx as nx
import numpy as np
from typing import List, Dict, Optional, Literal
from pathlib import Path
import pickle
import glob
import os
import math
from sklearn.metrics import r2_score
from scipy import stats

from torch_geometric.nn import RGCNConv, LayerNorm
from torch_geometric.nn import GlobalAttention
import torch.nn.functional as F
import warnings
warnings.filterwarnings("ignore")

class EdgeAttention(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.attention = torch.nn.Sequential(
            torch.nn.Linear(in_channels, hidden_channels),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_channels, 1),
            torch.nn.Sigmoid()
        )
        
        self.transform = torch.nn.Sequential(
            torch.nn.Linear(in_channels, hidden_channels),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels)
        )
        
    def forward(self, edge_features):
        # Calculate attention scores
        attention_scores = self.attention(edge_features)
        
        # Apply attention to transformed features
        transformed = self.transform(edge_features)
        attended_features = transformed * attention_scores
        
        return attended_features, attention_scores

class ResistanceRGCN(torch.nn.Module):
    def __init__(self, num_node_features, num_edge_features, hidden_channels=64, num_relations=4):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.num_relations = num_relations
        
        # Node embedding layers (same as before)
        self.node_encoder = torch.nn.Sequential(
            torch.nn.Linear(num_node_features, hidden_channels),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels)
        )
        
        # Relational GCN layers (same as before)
        self.conv1 = RGCNConv(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            num_relations=num_relations
        )
        self.conv2 = RGCNConv(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            num_relations=num_relations
        )
        self.conv3 = RGCNConv(
            in_channels=hidden_channels,
            out_channels=hidden_channels,
            num_relations=num_relations
        )
        
        # Layer norms (same as before)
        self.layer_norm1 = LayerNorm(hidden_channels)
        self.layer_norm2 = LayerNorm(hidden_channels)
        self.layer_norm3 = LayerNorm(hidden_channels)
        
        # Edge feature processing (same as before)
        self.edge_encoder = torch.nn.Sequential(
            torch.nn.Linear(num_edge_features, hidden_channels),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels)
        )
        
        # Attention-based global pooling (same as before)
        self.att_pool = GlobalAttention(
            gate_nn=torch.nn.Sequential(
                torch.nn.Linear(hidden_channels, 1)
            )
        )
        
        # Add the new edge attention layer
        self.edge_attention = EdgeAttention(
            in_channels=4 * hidden_channels,
            hidden_channels=hidden_channels
        )
        
        # Edge-level MLP (modified to take attended features)
        self.edge_mlp = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels, hidden_channels // 2),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels // 2),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(hidden_channels // 2, 1)
        )

    def forward(self, x, edge_index, edge_attr, batch):
        # 1) Encode node features
        x = self.node_encoder(x)
        
        # 2) Convert one-hot edge type to integer
        edge_type_indices = edge_attr[:, :4].argmax(dim=1)  # first 4 dims = one-hot for connection types
        
        # 3) Apply RGCN layers with residual connections
        x1 = self.conv1(x, edge_index, edge_type_indices)
        x1 = F.relu(self.layer_norm1(x1))
        x1 = F.dropout(x1, p=0.2, training=self.training)
        x = x + x1
        
        x2 = self.conv2(x, edge_index, edge_type_indices)
        x2 = F.relu(self.layer_norm2(x2))
        x2 = F.dropout(x2, p=0.2, training=self.training)
        x = x + x2
        
        x3 = self.conv3(x, edge_index, edge_type_indices)
        x3 = F.relu(self.layer_norm3(x3))
        x3 = F.dropout(x3, p=0.2, training=self.training)
        node_embeddings = x + x3
        graph_embedding = self.att_pool(node_embeddings, batch)

        # 4) Encode edge features
        edge_embeddings = self.edge_encoder(edge_attr)
        
        # 5) Concatenate node+node+edge embeddings for edge-level regression
        edge_src, edge_dst = edge_index
        edge_features = torch.cat([
            node_embeddings[edge_src],
            node_embeddings[edge_dst],
            edge_embeddings,
            graph_embedding[batch[edge_src]]
        ], dim=1)
        
        # 6) Apply edge attention
        attended_edge_features, attention_scores = self.edge_attention(edge_features)
        
        # 7) Predict resistance with attended features
        resistance_pred = self.edge_mlp(attended_edge_features).squeeze(-1)
        
        return resistance_pred

class FlexibleResistanceRGCN(torch.nn.Module):
    def __init__(self, num_node_features, num_edge_features, hidden_channels=64, 
                 num_relations=4, num_layers=3, dropout_rate=0.2):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.num_relations = num_relations
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        
        # Node embedding layers
        self.node_encoder = torch.nn.Sequential(
            torch.nn.Linear(num_node_features, hidden_channels),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels)
        )
        
        # Dynamic number of RGCN layers with corresponding layer norms
        self.convs = torch.nn.ModuleList()
        self.layer_norms = torch.nn.ModuleList()
        
        for i in range(num_layers):
            self.convs.append(RGCNConv(
                in_channels=hidden_channels,
                out_channels=hidden_channels,
                num_relations=num_relations
            ))
            self.layer_norms.append(LayerNorm(hidden_channels))
        
        # Edge feature processing
        self.edge_encoder = torch.nn.Sequential(
            torch.nn.Linear(num_edge_features, hidden_channels),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels)
        )
        
        # Global attention pooling
        self.att_pool = GlobalAttention(
            gate_nn=torch.nn.Sequential(
                torch.nn.Linear(hidden_channels, 1)
            )
        )
        
        # Add edge attention layer
        self.edge_attention = EdgeAttention(
            in_channels=4 * hidden_channels,
            hidden_channels=hidden_channels
        )
        
        # Edge-level MLP (modified to take attended features)
        self.edge_mlp = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels, hidden_channels // 2),
            torch.nn.ReLU(),
            LayerNorm(hidden_channels // 2),
            torch.nn.Dropout(dropout_rate),
            torch.nn.Linear(hidden_channels // 2, 1)
        )
        
    def forward(self, x, edge_index, edge_attr, batch):
        # 1) Encode node features
        x = self.node_encoder(x)
        
        # 2) Convert one-hot edge type to integer
        edge_type_indices = edge_attr[:, :4].argmax(dim=1)
        
        # 3) Apply RGCN layers with residual connections
        x_original = x
        for i in range(self.num_layers):
            x1 = self.convs[i](x, edge_index, edge_type_indices)
            x1 = F.relu(self.layer_norms[i](x1))
            x1 = F.dropout(x1, p=self.dropout_rate, training=self.training)
            x = x + x1
        
        node_embeddings = x
        graph_embedding = self.att_pool(node_embeddings, batch)

        # 4) Encode edge features
        edge_embeddings = self.edge_encoder(edge_attr)
        
        # 5) Concatenate node+node+edge embeddings for edge-level regression
        edge_src, edge_dst = edge_index
        edge_features = torch.cat([
            node_embeddings[edge_src],
            node_embeddings[edge_dst],
            edge_embeddings,
            graph_embedding[batch[edge_src]]
        ], dim=1)
        
        # 6) Apply edge attention
        attended_edge_features, attention_scores = self.edge_attention(edge_features)
        
        # 7) Predict resistance with attended features
        resistance_pred = self.edge_mlp(attended_edge_features).squeeze(-1)
        
        return resistance_pred

def asinh_transform(x: torch.Tensor) -> torch.Tensor:
    """Apply inverse hyperbolic sine transformation"""
    return torch.asinh(x)

def asinh_inverse(x: torch.Tensor) -> torch.Tensor:
    """Inverse of asinh transformation"""
    return torch.sinh(x)

def yeo_johnson_transform(x: torch.Tensor, lmbda: float) -> torch.Tensor:
    """Apply Yeo-Johnson transformation with parameter lambda"""
    x_numpy = x.detach().cpu().numpy()
    transformed = stats.yeojohnson(x_numpy, lmbda)
    return torch.tensor(transformed, dtype=x.dtype, device=x.device)

def yeo_johnson_inverse(x: torch.Tensor, lmbda: float) -> torch.Tensor:
    """Inverse of Yeo-Johnson transformation"""
    x_numpy = x.detach().cpu().numpy()
    if lmbda == 0:
        transformed = np.exp(x_numpy) - 1
    elif lmbda == 2:
        transformed = np.sqrt(x_numpy + 1) - 1
    else:
        transformed = np.power(x_numpy * lmbda + 1, 1/lmbda) - 1
    return torch.tensor(transformed, dtype=x.dtype, device=x.device)

def box_cox_transform(x: torch.Tensor, lmbda: float) -> torch.Tensor:
    """Apply Box-Cox transformation with parameter lambda"""
    x_numpy = x.detach().cpu().numpy()
    transformed = stats.boxcox(x_numpy, lmbda)
    return torch.tensor(transformed, dtype=x.dtype, device=x.device)

def box_cox_inverse(x: torch.Tensor, lmbda: float) -> torch.Tensor:
    """Inverse of Box-Cox transformation"""
    x_numpy = x.detach().cpu().numpy()
    if lmbda == 0:
        transformed = np.exp(x_numpy)
    else:
        transformed = np.power(x_numpy * lmbda + 1, 1/lmbda)
    return torch.tensor(transformed, dtype=x.dtype, device=x.device)

class ResistanceDataset(Dataset):
    """Dataset class for resistance graphs"""
    def __init__(self, graphs_dir: str = '../resistance_graphs_for_gnn', transform=None, pos_encoding_dim: int = 4, 
                 inference_mode: bool = False, num_node_features: int = None, num_edge_features: int = None,
                 remove_outliers: bool = False, outlier_z_threshold: float = 3.0,
                 transform_type: Literal['log', 'asinh', 'yeo_johnson', 'box_cox'] = 'log',
                 transform_param: float = None):
        super().__init__()
        self.transform = transform
        self.pos_encoding_dim = pos_encoding_dim  # Dimension of positional encoding
        self.inference_mode = inference_mode
        self._num_node_features = num_node_features
        self._num_edge_features = num_edge_features
        self.remove_outliers = remove_outliers
        self.outlier_z_threshold = outlier_z_threshold
        self.transform_type = transform_type
        self.transform_param = transform_param

        # Default normalization values
        self.transform_mean = None
        self.transform_std = None
        self.transform_lambda = None  # For Yeo-Johnson and Box-Cox

        if not inference_mode:
            if not os.path.exists(graphs_dir):
                raise ValueError(f"Graphs directory '{graphs_dir}' does not exist")
            
            # Load all pickle files from the graphs directory
            self.graph_files = []
            for cell_dir in glob.glob(os.path.join(graphs_dir, '*')):
                if os.path.isdir(cell_dir):
                    self.graph_files.extend(glob.glob(os.path.join(cell_dir, '*_graph.pkl')))
            
            if not self.graph_files:
                raise ValueError(f"No graph files (*_graph.pkl) found in '{graphs_dir}' or its subdirectories")
                
            # Load first graph to get feature dimensions if not provided
            if self._num_node_features is None or self._num_edge_features is None:
                with open(self.graph_files[0], 'rb') as f:
                    sample_data = pickle.load(f)
                self._num_node_features = sample_data.x.size(1)
                self._num_edge_features = sample_data.edge_attr.size(1)
                print(f"Number of node features: {self._num_node_features}")
                print(f"Number of edge features: {self._num_edge_features}")

            self._compute_resistance_statistics()

    def _transform_values(self, values: torch.Tensor) -> torch.Tensor:
        """Apply the selected transformation to values"""
        if self.transform_type == 'log':
            return torch.log(values)
        elif self.transform_type == 'asinh':
            return asinh_transform(values)
        elif self.transform_type == 'yeo_johnson':
            return yeo_johnson_transform(values, self.transform_lambda)
        elif self.transform_type == 'box_cox':
            return box_cox_transform(values, self.transform_lambda)
        else:
            raise ValueError(f"Unknown transform type: {self.transform_type}")

    def _inverse_transform_values(self, values: torch.Tensor) -> torch.Tensor:
        """Apply the inverse of the selected transformation"""
        if self.transform_type == 'log':
            return torch.exp(values)
        elif self.transform_type == 'asinh':
            return asinh_inverse(values)
        elif self.transform_type == 'yeo_johnson':
            return yeo_johnson_inverse(values, self.transform_lambda)
        elif self.transform_type == 'box_cox':
            return box_cox_inverse(values, self.transform_lambda)
        else:
            raise ValueError(f"Unknown transform type: {self.transform_type}")

    def _positional_encoding(self, z_index: float) -> List[float]:
        """
        Generate positional encoding for a given value using sine and cosine functions.
        Produces self.pos_encoding_dim values (assumed even).
        """
        encoding = []
        for i in range(self.pos_encoding_dim // 2):
            freq = 1.0 / (10000 ** (2 * i / self.pos_encoding_dim))
            encoding.append(math.sin(z_index * freq))
            encoding.append(math.cos(z_index * freq))
        return encoding

    def _get_node_features(self, node_data) -> List[float]:
        """
        Extract numerical features from a node to match our PyG object.
        Feature vector composition:
          - Layer one-hot encoding for 13 layer types,
          - Positional encoding of z-index (4 dimensions),
          - Polygon width and height (2 dimensions),
          - Nanosheet flag (1 dimension) and nanosheet index (1 dimension).
        Total dimension: 13 + 4 + 2 + 2 = 21.
        """
        _, data = node_data
        features = []
        layer_types = [
            'M0', 'M1', 'BSPowerRail',
            'PMOSGate', 'NMOSGate',
            'PMOSInterconnect', 'NMOSInterconnect',
            'VIA_M0_M1', 'VIA_M1_M2', 'VIA_Interconnect',
            'PmosNanoSheet', 'NmosNanoSheet',
            'Unused'
        ]
        layer = data.get('layer', '')
        features.extend([1.0 if layer_type.lower() in layer.lower() else 0.0 for layer_type in layer_types])
        
        # Add 4-D positional encoding for the z-index.
        z_index = float(data.get('z_index', 0))
        z_pos_encoding = self._positional_encoding(z_index)
        features.extend(z_pos_encoding)
        
        # Add polygon dimensions (width and height) if available.
        try:
            bounds = data.get('polygon_bounds', None)
            if bounds is None or len(bounds) < 4:
                raise ValueError("Invalid or missing polygon bounds")
            width = float(bounds[2] - bounds[0])
            height = float(bounds[3] - bounds[1])
            features.extend([width, height])
        except Exception as e:
            features.extend([0.0, 0.0])
        
        # Add nanosheet-specific features.
        # It is assumed the node's data dictionary may contain a flag and an index.
        is_nanosheet = float(data.get('nanosheet', 0))  # 1.0 if nanosheet, else 0.0
        features.append(is_nanosheet)
        nanosheet_index = float(data.get('nanosheet_index', 0))
        features.append(nanosheet_index)
        
        return features

    def _get_edge_features(self, edge_data) -> List[float]:
        """
        Extract numerical features from edge data to match our PyG object.
        Feature vector composition:
          - Connection type label encoding (1 dimension),
          - Euclidean distance (1 dimension),
          - Z-distance positional encoding (4 dimensions).
        Total dimension: 1 + 1 + 4 = 6.
        """
        _, _, data = edge_data
        features = []
        
        # Label encoding for connection types
        connection_types = {'GATE': 1, 'INTERCONNECT': 2, 'VIA': 3, 'NANOSHEET': 4}
        conn_type_value = data.get('connection_type', '')
        # Default to 0 if connection type not found
        label = 0
        for ct, value in connection_types.items():
            if ct in conn_type_value:
                label = value
                break
        features.append(float(label))
        
        features.append(float(data.get('euclidean_distance', 0.0)))
        
        src_z = float(data.get('source_z_index', 0))
        tgt_z = float(data.get('target_z_index', 0))
        z_distance = abs(src_z - tgt_z)
        z_dist_encoding = self._positional_encoding(z_distance)
        features.extend(z_dist_encoding)
        
        return features

    def len(self):
        if self.inference_mode:
            return 1  # Only one graph in inference mode
        return len(self.graph_files)

    def _compute_resistance_statistics(self):
        """Compute statistics of transformed resistance values"""
        if self.inference_mode:
            return
        
        # First pass: collect all raw resistances
        all_raw_resistances = []
        for idx, graph_file in enumerate(self.graph_files):
            with open(graph_file, 'rb') as f:
                data = pickle.load(f)
                valid_mask = data.edge_mask
                resistances = data.y[valid_mask].numpy()
                if len(resistances) > 0:
                    all_raw_resistances.extend(resistances)
        
        if not all_raw_resistances:
            raise ValueError("No valid resistance values found in the dataset")
        
        all_raw_resistances = np.array(all_raw_resistances)
        
        # Only compute outlier masks if remove_outliers is True
        if self.remove_outliers:
            # Convert to log space only for outlier detection
            log_resistances = np.log10(all_raw_resistances)
            log_mean = np.mean(log_resistances)
            log_std = np.std(log_resistances)
            
            filtered_raw_resistances = []
            self.updated_masks = {}
            total_edges = 0
            total_outliers = 0
            
            # Identify outliers using log-space z-scores but keep original values
            for idx, graph_file in enumerate(self.graph_files):
                with open(graph_file, 'rb') as f:
                    data = pickle.load(f)
                    original_mask = data.edge_mask
                    updated_mask = torch.zeros_like(original_mask)
                    valid_edges = torch.where(original_mask)[0]
                    total_edges += len(valid_edges)
                    
                    if len(valid_edges) > 0:
                        raw_resistances = data.y[valid_edges].numpy()
                        # Convert to log space only for z-score calculation
                        log_vals = np.log10(raw_resistances)
                        z_scores = np.abs((log_vals - log_mean) / log_std)
                        
                        for i, edge_idx in enumerate(valid_edges):
                            if z_scores[i] <= self.outlier_z_threshold:
                                updated_mask[edge_idx] = True
                                # Store original raw value, not log-transformed
                                filtered_raw_resistances.append(raw_resistances[i])
                            else:
                                total_outliers += 1
                
                self.updated_masks[idx] = updated_mask
            
            # Print outlier statistics
            print(f"\nOutlier Statistics (detected using log-space z-scores):")
            print(f"Total values: {total_edges}")
            print(f"Outliers removed: {total_outliers} ({(total_outliers/total_edges)*100:.2f}%)")
            if filtered_raw_resistances:
                print(f"Raw resistance range after outlier removal:")
                print(f"Min: {float(np.min(filtered_raw_resistances)):.4e} ohms")
                print(f"Max: {float(np.max(filtered_raw_resistances)):.4e} ohms")
                print(f"Span: {float(np.max(filtered_raw_resistances)/np.min(filtered_raw_resistances)):.2e}x")
            
            # Convert filtered values to tensor for further processing
            filtered_resistances_tensor = torch.tensor(filtered_raw_resistances)
        else:
            # If not removing outliers, use all values
            filtered_resistances_tensor = torch.tensor(all_raw_resistances)
        
        # Now proceed with the specified transformation on the filtered raw values
        transformed_resistances = self._transform_values(filtered_resistances_tensor)
        transformed_resistances = transformed_resistances.numpy()
        
        # Compute statistics on transformed values
        self.transform_mean = float(np.mean(transformed_resistances))
        self.transform_std = float(np.std(transformed_resistances))
        
        # For Yeo-Johnson and Box-Cox, find optimal lambda if not provided
        if self.transform_type in ['yeo_johnson', 'box_cox'] and self.transform_param is None:
            if self.transform_type == 'yeo_johnson':
                self.transform_lambda, _ = stats.yeojohnson_normmax(transformed_resistances)
            else:  # box_cox
                self.transform_lambda, _ = stats.boxcox_normmax(transformed_resistances)
        else:
            self.transform_lambda = self.transform_param
        
        print(f"\nResistance statistics after {self.transform_type} transform:")
        print(f"Transform mean: {self.transform_mean:.4f}")
        print(f"Transform std: {self.transform_std:.4f}")
        if self.transform_lambda is not None:
            print(f"Transform lambda: {self.transform_lambda:.4f}")

    def get(self, idx):
        """Get a graph with proper outlier removal and normalization"""
        if self.inference_mode:
            return None
        
        with open(self.graph_files[idx], 'rb') as f:
            data = pickle.load(f)
            
            # Only apply outlier mask if remove_outliers is True AND we have computed masks
            if self.remove_outliers and self.updated_masks is not None:
                data.edge_mask = self.updated_masks[idx]
            
            # Apply normalization to valid edges
            if self.transform_mean is not None and self.transform_std is not None:
                valid_edges = data.edge_mask
                if valid_edges.any():
                    original_values = data.y.clone()
                    transformed_resistance = self._transform_values(data.y[valid_edges])
                    data.y[valid_edges] = (transformed_resistance - self.transform_mean) / self.transform_std
                    data.y[~valid_edges] = original_values[~valid_edges]
            
            if self.transform:
                data = self.transform(data)
            
            return data

    def process_inference_graph(self, data):
        """Process a single graph during inference"""
        if not self.inference_mode:
            raise ValueError("This method should only be called in inference mode")
        if self._num_node_features is None:
            self._num_node_features = data.x.size(1)
        if self._num_edge_features is None:
            self._num_edge_features = data.edge_attr.size(1)
        return data

def calculate_metrics(pred, target, mask=None, dataset=None):
    """
    Calculate metrics in both normalized and denormalized spaces
    """
    if mask is not None:
        pred = pred[mask]
        target = target[mask]
    
    # Calculate metrics in normalized space
    mse_tensor = F.mse_loss(pred, target)
    norm_mse = mse_tensor.item()
    norm_rmse = np.sqrt(norm_mse)
    
    # Convert to numpy for R2 calculation in normalized space
    pred_np = pred.detach().cpu().numpy()
    target_np = target.detach().cpu().numpy()
    norm_r2 = r2_score(target_np, pred_np)
    
    # Calculate metrics in original resistance space if dataset is provided
    if dataset is not None and hasattr(dataset, 'transform_mean') and hasattr(dataset, 'transform_std'):
        # Denormalize predictions and targets
        pred_norm = pred * dataset.transform_std + dataset.transform_mean
        target_norm = target * dataset.transform_std + dataset.transform_mean
        
        # Inverse transform to get back to original space using the correct transformation
        pred_denorm = dataset._inverse_transform_values(pred_norm)
        target_denorm = dataset._inverse_transform_values(target_norm)
        
        # Calculate relative error metrics
        rel_error = torch.abs(pred_denorm - target_denorm) / target_denorm
        # Clip MAPE to reasonable values and convert to percentage
        mape = torch.mean(torch.clamp(rel_error, 0, 10)) * 100  # Clip at 1000%
        
        # Calculate MAE in denormalized space
        mae = torch.mean(torch.abs(pred_denorm - target_denorm)).item()
        
        # For R2, always use log10 space regardless of the original transformation
        # This is a standard approach for values spanning many orders of magnitude
        log_pred = torch.log10(torch.clamp(pred_denorm, min=1e-20))
        log_target = torch.log10(torch.clamp(target_denorm, min=1e-20))
        
        log_pred_np = log_pred.detach().cpu().numpy()
        log_target_np = log_target.detach().cpu().numpy()
        log_r2 = r2_score(log_target_np, log_pred_np)
        
        return mse_tensor, {
            'normalized': {
                'mse': norm_mse,
                'rmse': norm_rmse,
                'r2': norm_r2
            },
            'denormalized': {
                'log_r2': log_r2,  # R2 in log10 space of denormalized values
                'mape': mape.item(),
                'mae': mae
            }
        }
    
    return mse_tensor, {
        'normalized': {
            'mse': norm_mse,
            'rmse': norm_rmse,
            'r2': norm_r2
        }
    }

def mape_loss(pred, target, mask=None, dataset=None, epsilon=1e-10, max_clip=10.0):
    """
    Calculate Mean Absolute Percentage Error (MAPE) loss
    
    Args:
        pred: Predicted values in normalized space
        target: Target values in normalized space
        mask: Optional mask for valid values
        dataset: Dataset containing normalization parameters
        epsilon: Small constant to avoid division by zero
        max_clip: Maximum value to clip MAPE (to avoid extreme outliers)
        
    Returns:
        MAPE loss tensor
    """
    if mask is not None:
        pred = pred[mask]
        target = target[mask]
    
    # Denormalize predictions and targets
    if dataset is not None and hasattr(dataset, 'transform_mean') and hasattr(dataset, 'transform_std'):
        # First denormalize to transformed space
        pred_norm = pred * dataset.transform_std + dataset.transform_mean
        target_norm = target * dataset.transform_std + dataset.transform_mean
        
        # Then inverse transform to original space
        pred_denorm = dataset._inverse_transform_values(pred_norm)
        target_denorm = dataset._inverse_transform_values(target_norm)
        
        # Calculate MAPE with epsilon to avoid division by zero
        percentage_error = torch.abs(pred_denorm - target_denorm) / (target_denorm + epsilon)
        
        # Clip to avoid extreme values dominating the loss
        percentage_error = torch.clamp(percentage_error, 0, max_clip)
        
        # Return mean as the loss
        return torch.mean(percentage_error)
    else:
        # Fallback to MSE if dataset not provided
        return F.mse_loss(pred, target)

def train_model(model: ResistanceRGCN, train_loader: DataLoader, device: torch.device, 
                optimizer: torch.optim.Optimizer, dataset: ResistanceDataset, max_grad_norm: float = 1.0,
                weighted_loss: bool = False, loss_type: str = 'mse',
                use_original_units: bool = False):
    """Train the GNN model

    Args:
        model: The GNN model.
        train_loader: DataLoader for training data.
        device: Computation device.
        optimizer: Optimizer used for training.
        dataset: ResistanceDataset (must have transform_mean and transform_std attributes).
        max_grad_norm: Maximum gradient norm.
        weighted_loss: Boolean flag for using weighted losses.
        loss_type: Loss type ('mse', 'mape', etc.).
        use_original_units: If True, compute loss and metrics in the original (denormalized) units.
    """
    model.train()
    
    # Initialize metrics accumulators with the new structure
    metrics_sum = {
        'normalized': {'mse': 0.0, 'rmse': 0.0, 'r2': 0.0},
        'denormalized': {'log_r2': 0.0, 'mape': 0.0, 'mae': 0.0}
    }
    num_valid_batches = 0
    if weighted_loss:
        print("Training with Weighted Loss")
    for batch in train_loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        valid_mask = batch.edge_mask
        
        if not valid_mask.any():
            continue
        
        target = batch.y.squeeze()
        
        # Optionally compute everything in original (denormalized) units
        if use_original_units:
            # Denormalize predictions and targets using the stored transform statistics
            pred_norm = pred * dataset.transform_std + dataset.transform_mean
            target_norm = target * dataset.transform_std + dataset.transform_mean
            
            # Apply inverse transform based on the transformation type
            pred = dataset._inverse_transform_values(pred_norm)
            target = dataset._inverse_transform_values(target_norm)
        
        # Calculate loss based on specified loss type
        if loss_type == 'mse':
            if use_original_units:
                loss_tensor = F.mse_loss(pred, target)
                # For metrics, we merely pass the denormalized values as "denormalized"
                mse_val = loss_tensor.item()
                rmse_val = np.sqrt(mse_val)
                # Compute R2 using numpy arrays
                pred_np = pred.detach().cpu().numpy()
                target_np = target.detach().cpu().numpy()
                
                # Use log10 for R2 calculation
                log_pred_np = np.log10(np.clip(pred_np, 1e-20, None))
                log_target_np = np.log10(np.clip(target_np, 1e-20, None))
                log_r2_val = r2_score(log_target_np, log_pred_np)
                
                batch_metrics = {
                    'denormalized': {'mse': mse_val, 'rmse': rmse_val, 'log_r2': log_r2_val}
                }
            else:
                # Standard MSE loss computed in normalized space.
                loss_tensor, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
            
            if weighted_loss and not use_original_units:
                # Compute weighted MSE loss only on normalized values.
                pred_f = pred[valid_mask]
                target_f = target[valid_mask]
                weights = torch.abs(target_f) + 1e-4
                loss_tensor = F.mse_loss(pred_f, target_f, reduction='none')
                loss_tensor = (loss_tensor * weights).mean()
        
        elif loss_type == 'mape':
            # MAPE loss already denormalizes if dataset provided.
            loss_tensor = mape_loss(pred, target, valid_mask, dataset)
            _, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
        else:
            loss_tensor, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
        
        # Backward pass & optimization
        loss_tensor.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        
        # Accumulate metrics
        for space in batch_metrics:
            for metric, value in batch_metrics[space].items():
                metrics_sum[space][metric] += value
        
        num_valid_batches += 1
    
    # Average metrics over valid batches
    if num_valid_batches > 0:
        return {
            space: {
                metric: value / num_valid_batches 
                for metric, value in space_metrics.items()
            }
            for space, space_metrics in metrics_sum.items()
        }
    
    return {
        'normalized': {'mse': float('inf'), 'rmse': float('inf'), 'r2': float('-inf')},
        'denormalized': {'log_r2': float('-inf'), 'mape': float('inf'), 'mae': float('inf')}
    }

def evaluate_model(model: ResistanceRGCN, test_loader: DataLoader, device: torch.device, dataset: ResistanceDataset):
    """Evaluate the GNN model"""
    model.eval()
    
    metrics_sum = {
        'normalized': {'mse': 0.0, 'rmse': 0.0, 'r2': 0.0},
        'denormalized': {'log_r2': 0.0, 'mape': 0.0, 'mae': 0.0}
    }
    num_valid_batches = 0
    
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            valid_mask = batch.edge_mask
            
            if not valid_mask.any():
                continue
            
            target = batch.y.squeeze()
            _, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
            
            # Accumulate metrics
            for space in batch_metrics:
                for metric, value in batch_metrics[space].items():
                    metrics_sum[space][metric] += value
            
            num_valid_batches += 1
    
    # Average metrics
    if num_valid_batches > 0:
        return {
            space: {
                metric: value / num_valid_batches 
                for metric, value in space_metrics.items()
            }
            for space, space_metrics in metrics_sum.items()
        }
    
    # Return default metrics if no valid batches
    return {
        'normalized': {'mse': float('inf'), 'rmse': float('inf'), 'r2': float('-inf')},
        'denormalized': {'log_r2': float('-inf'), 'mape': float('inf'), 'mae': float('inf')}
    }

def print_pyg_data_debug_info(data, pos_encoding_dim: int, verbose: bool = True):
    """
    Print detailed debug information about a PyG Data object
    
    Args:
        data: PyTorch Geometric Data object
        pos_encoding_dim: Dimension of positional encoding
        verbose: If True, prints detailed feature information
    """
    # Basic statistics (always print these)
    stats = {
        "Graph Statistics": {
            "Number of nodes": data.x.shape[0],
            "Number of edges": data.edge_index.shape[1]//2,  # Divide by 2 because edges are bidirectional
            "Node feature dimension": data.x.shape[1],
            "Edge feature dimension": data.edge_attr.shape[1]
        }
    }
    
    print("\nGraph Statistics:")
    for key, value in stats["Graph Statistics"].items():
        print(f"{key}: {value}")
    
    if not verbose:
        return
        
    # Detailed feature information
    layer_types = ['M0', 'PMOSGate', 'NMOSGate', 'PMOSInterconnect', 'NMOSInterconnect', 'VIA']
    connection_types = ['GATE', 'INTERCONNECT', 'VIA']
    
    # Node Features
    print("\nNode Features:")
    for node_idx in range(min(5, data.x.shape[0])):
        node_name = data.node_names[node_idx] if hasattr(data, 'node_names') else f"Node {node_idx}"
        print(f"\n{node_name}:")
        features = data.x[node_idx]
        
        # Layer type one-hot encoding
        print("Layer type encoding:")
        for i, layer_type in enumerate(layer_types):
            print(f"  {layer_type}: {features[i].item():.1f}")
        
        # Positional encoding
        print("Z-index positional encoding:")
        pos_enc = features[len(layer_types):].numpy()
        for i in range(0, pos_encoding_dim, 2):
            print(f"  sin/cos pair {i//2}: {pos_enc[i]:.3f}, {pos_enc[i+1]:.3f}")
    
    # Edge Features
    print("\nEdge Features:")
    for edge_idx in range(min(5, data.edge_attr.shape[0])):
        print(f"\nEdge {edge_idx}:")
        features = data.edge_attr[edge_idx]
        
        # Connection type one-hot encoding
        print("Connection type encoding:")
        for i, conn_type in enumerate(connection_types):
            print(f"  {conn_type}: {features[i].item():.1f}")
        
        # Euclidean distance
        print(f"Euclidean distance: {features[3].item():.3f}")
        
        # Z-distance positional encoding
        print("Z-distance positional encoding:")
        pos_enc = features[4:].numpy()
        for i in range(0, pos_encoding_dim, 2):
            print(f"  sin/cos pair {i//2}: {pos_enc[i]:.3f}, {pos_enc[i+1]:.3f}")
    
    # Add statistics about known vs unknown resistances
    total_edges = data.y.shape[0]
    known_edges = data.edge_mask.sum().item()
    print(f"\nResistance Statistics:")
    print(f"Total edges: {total_edges}")
    print(f"Edges with known resistance: {known_edges}")
    print(f"Edges with unknown resistance: {total_edges - known_edges}")
    
    # Print resistance values for valid edges only
    print("\nValid Resistance Values:")
    valid_edges_shown = 0
    for edge_idx in range(data.y.shape[0]):
        if data.edge_mask[edge_idx]:
            resistance = data.y[edge_idx].item()
            src = data.edge_index[0, edge_idx].item()
            dst = data.edge_index[1, edge_idx].item()
            src_name = data.node_names[src] if hasattr(data, 'node_names') else f"Node {src}"
            dst_name = data.node_names[dst] if hasattr(data, 'node_names') else f"Node {dst}"
            print(f"Edge {edge_idx} ({src_name} -> {dst_name}): {resistance:.3f} Ohms")
            valid_edges_shown += 1
            if valid_edges_shown >= 5:  # Show at most 5 valid edges
                break
                
    # Print invalid resistance values
    print("\nInvalid Resistance Values:")
    invalid_edges_shown = 0
    for edge_idx in range(data.y.shape[0]):
        if not data.edge_mask[edge_idx]:
            resistance = data.y[edge_idx].item()
            src = data.edge_index[0, edge_idx].item()
            dst = data.edge_index[1, edge_idx].item()
            src_name = data.node_names[src] if hasattr(data, 'node_names') else f"Node {src}"
            dst_name = data.node_names[dst] if hasattr(data, 'node_names') else f"Node {dst}"
            print(f"Edge {edge_idx} ({src_name} -> {dst_name}): {resistance:.3f} Ohms (Unknown)")
            invalid_edges_shown += 1
            if invalid_edges_shown >= 5:  # Show at most 5 invalid edges
                break

def train_model_for_optuna(model, 
                           train_loader, 
                           device, 
                           optimizer, 
                           dataset, 
                           max_grad_norm=1.0, 
                           weighted_loss=False, 
                           loss_type='mse',
                           use_original_units: bool = False):
    """Simplified training function for Optuna trials without logging.
    
    Args:
        model: The GNN model.
        train_loader: DataLoader for training.
        device: Computation device.
        optimizer: Optimizer.
        dataset: ResistanceDataset instance.
        max_grad_norm: Gradient clipping value.
        weighted_loss: Whether to use weighted losses.
        loss_type: Which loss function to use.
        use_original_units: If True, all loss computations use original units.
    """
    model.train()
    
    metrics_sum = {
        'normalized': {'mse': 0.0, 'rmse': 0.0, 'r2': 0.0},
        'denormalized': {'log_r2': 0.0, 'mape': 0.0, 'mae': 0.0}
    }
    num_valid_batches = 0
    
    for batch in train_loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        valid_mask = batch.edge_mask
        
        if not valid_mask.any():
            continue
        
        target = batch.y.squeeze()
        if use_original_units:
            # Denormalize predictions and targets using the stored transform statistics
            pred_norm = pred * dataset.transform_std + dataset.transform_mean
            target_norm = target * dataset.transform_std + dataset.transform_mean
            
            # Apply inverse transform based on the transformation type
            pred = dataset._inverse_transform_values(pred_norm)
            target = dataset._inverse_transform_values(target_norm)
        
        if loss_type == 'mse':
            loss_tensor = F.mse_loss(pred, target)
            if use_original_units:
                mse_val = loss_tensor.item()
                rmse_val = np.sqrt(mse_val)
                pred_np = pred.detach().cpu().numpy()
                target_np = target.detach().cpu().numpy()
                
                # Use log10 for R2 calculation
                log_pred_np = np.log10(np.clip(pred_np, 1e-20, None))
                log_target_np = np.log10(np.clip(target_np, 1e-20, None))
                log_r2_val = r2_score(log_target_np, log_pred_np)
                
                batch_metrics = {
                    'denormalized': {'mse': mse_val, 'rmse': rmse_val, 'log_r2': log_r2_val}
                }
            else:
                loss_tensor, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
            
            if weighted_loss and not use_original_units:
                pred_f = pred[valid_mask]
                target_f = target[valid_mask]
                weights = torch.abs(target_f) + 1e-4
                loss_tensor = F.mse_loss(pred_f, target_f, reduction='none')
                loss_tensor = (loss_tensor * weights).mean()
        elif loss_type == 'mape':
            loss_tensor = mape_loss(pred, target, valid_mask, dataset)
            _, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
        else:
            loss_tensor, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
        
        loss_tensor.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        
        for space in batch_metrics:
            for metric, value in batch_metrics[space].items():
                metrics_sum[space][metric] += value
        
        num_valid_batches += 1
    
    if num_valid_batches > 0:
        return {
            space: {
                metric: value / num_valid_batches 
                for metric, value in space_metrics.items()
            }
            for space, space_metrics in metrics_sum.items()
        }
    
    return {
        'normalized': {'mse': float('inf'), 'rmse': float('inf'), 'r2': float('-inf')},
        'denormalized': {'log_r2': float('-inf'), 'mape': float('inf'), 'mae': float('inf')}
    }

def evaluate_model_for_optuna(model, test_loader, device, dataset):
    """Simplified evaluation function for Optuna trials without logging"""
    model.eval()
    
    metrics_sum = {
        'normalized': {'mse': 0.0, 'rmse': 0.0, 'r2': 0.0},
        'denormalized': {'log_r2': 0.0, 'mape': 0.0, 'mae': 0.0}
    }
    num_valid_batches = 0
    
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            valid_mask = batch.edge_mask
            
            if not valid_mask.any():
                continue
            
            target = batch.y.squeeze()
            _, batch_metrics = calculate_metrics(pred, target, valid_mask, dataset)
            
            for space in batch_metrics:
                for metric, value in batch_metrics[space].items():
                    metrics_sum[space][metric] += value
            
            num_valid_batches += 1
    
    if num_valid_batches > 0:
        return {
            space: {
                metric: value / num_valid_batches 
                for metric, value in space_metrics.items()
            }
            for space, space_metrics in metrics_sum.items()
        }
    
    return {
        'normalized': {'mse': float('inf'), 'rmse': float('inf'), 'r2': float('-inf')},
        'denormalized': {'log_r2': float('-inf'), 'mape': float('inf'), 'mae': float('inf')}
    }

def find_resistance_range(dataset):
    """
    Find the minimum and maximum resistance values in the dataset after normalization.
    
    Args:
        dataset: ResistanceDataset object
        
    Returns:
        min_resistance: Minimum normalized resistance value (in log-space)
        max_resistance: Maximum normalized resistance value (in log-space)
    """
    if dataset.inference_mode:
        print("Cannot find resistance range in inference mode")
        return None, None
        
    all_valid_resistances = []
    
    for idx in range(len(dataset)):
        data = dataset[idx]
        # Get only valid resistances (those within the edge mask)
        valid_resistances = data.y[data.edge_mask].numpy()
        if len(valid_resistances) > 0:
            all_valid_resistances.extend(valid_resistances)
    
    if not all_valid_resistances:
        print("No valid resistance values found in the dataset")
        return None, None
    
    # These values are already normalized in log-space
    min_resistance = float(np.min(all_valid_resistances))
    max_resistance = float(np.max(all_valid_resistances))
    
    print(f"Normalized resistance range:")
    print(f"Min: {min_resistance:.4f} (log-space)")
    print(f"Max: {max_resistance:.4f} (log-space)")
    print(f"Range span: {max_resistance - min_resistance:.4f} (log units)")
    
    return min_resistance, max_resistance

def find_resistance_range_raw(dataset):
    """
    Find the minimum and maximum resistance values in the dataset before log transformation.
    """
    if dataset.inference_mode:
        print("Cannot find resistance range in inference mode")
        return None, None
        
    all_valid_resistances = []
    
    # Use the dataset's get method to respect outlier masks
    for idx in range(len(dataset)):
        # Load data through dataset to get proper masking
        data = dataset[idx]
        
        # Get the original pickle file to access raw values
        with open(dataset.graph_files[idx], 'rb') as f:
            raw_data = pickle.load(f)
            
        # Use the masked edges from processed data but raw resistance values
        valid_resistances = raw_data.y[data.edge_mask].numpy()
        if len(valid_resistances) > 0:
            all_valid_resistances.extend(valid_resistances)
    
    if not all_valid_resistances:
        print("No valid resistance values found in the dataset")
        return None, None
    
    min_resistance = float(np.min(all_valid_resistances))
    max_resistance = float(np.max(all_valid_resistances))
    
    print(f"Raw resistance range (before transform):")
    print(f"Min: {min_resistance:.4e} ohms")
    print(f"Max: {max_resistance:.4e} ohms")
    print(f"Range span: {max_resistance/min_resistance:.2e}x")
    
    return min_resistance, max_resistance

# Additional helper function to get raw resistance range by edge types
def find_resistance_range_by_edge_type(dataset):
    """
    Find the minimum and maximum raw resistance values for each edge type in the dataset.
    Assumes the first 4 dimensions of edge_attr are a one-hot encoding for edge types.
    Mapping:
        Index 0: 'GATE'
        Index 1: 'INTERCONNECT'
        Index 2: 'VIA'
        Index 3: 'NANOSHEET'
    """
    edge_type_mapping = {0: 'GATE', 1: 'INTERCONNECT', 2: 'VIA', 3: 'NANOSHEET'}
    type_resistances = {etype: [] for etype in edge_type_mapping.values()}
    
    for idx in range(len(dataset.graph_files)):
        with open(dataset.graph_files[idx], 'rb') as f:
            raw_data = pickle.load(f)
        if not hasattr(raw_data, 'edge_mask'):
            continue
        valid_mask = raw_data.edge_mask
        if valid_mask.sum().item() == 0:
            continue
        edge_attrs = raw_data.edge_attr
        resistances = raw_data.y
        valid_indices = torch.where(valid_mask)[0]
        for i in valid_indices:
            one_hot = edge_attrs[i, :4]
            edge_type_index = int(torch.argmax(one_hot).item())
            etype = edge_type_mapping.get(edge_type_index, 'Unknown')
            type_resistances[etype].append(resistances[i].item())
    
    print("\nRaw resistance range by edge types:")
    for etype, values in type_resistances.items():
        if values:
            min_val = min(values)
            max_val = max(values)
            print(f"{etype}: min = {min_val:.4e} ohms, max = {max_val:.4e} ohms, span = {max_val/min_val:.2e}x")
        else:
            print(f"{etype}: No valid resistance values found")
    return type_resistances

# Additional helper function to get raw resistance range by layer types (from node features)
def find_resistance_range_by_layer_type(dataset):
    """
    For each layer type (as defined in the node features' first 13 dimensions),
    find the minimum and maximum raw resistance values for edges where the source node
    is of that layer type.
    
    Assumes that the first 13 features in the node feature vector are a one-hot 
    encoding for the following layer types:
        Index 0: 'M0'
        Index 1: 'M1'
        Index 2: 'BSPowerRail'
        Index 3: 'PMOSGate'
        Index 4: 'NMOSGate'
        Index 5: 'PMOSInterconnect'
        Index 6: 'NMOSInterconnect'
        Index 7: 'VIA_M0_M1'
        Index 8: 'VIA_M1_M2'
        Index 9: 'VIA_Interconnect'
        Index 10: 'PmosNanoSheet'
        Index 11: 'NmosNanoSheet'
        Index 12: 'Unused'
    """
    # define the mapping for node layer types (first 13 features)
    layer_types = ['M0', 'M1', 'BSPowerRail', 'PMOSGate', 'NMOSGate', 
                   'PMOSInterconnect', 'NMOSInterconnect', 'VIA_M0_M1', 
                   'VIA_M1_M2', 'VIA_Interconnect', 'PmosNanoSheet', 
                   'NmosNanoSheet', 'Unused']
    type_resistances = {ltype: [] for ltype in layer_types}
    
    for file in dataset.graph_files:
        with open(file, 'rb') as f:
            raw_data = pickle.load(f)
        
        # Check that the raw_data contains node features and edge info
        if not hasattr(raw_data, 'x') or not hasattr(raw_data, 'edge_mask'):
            continue
        
        # Determine layer type for each node by taking argmax of first 13 features
        # raw_data.x should be a tensor of shape (num_nodes, feature_dim)
        node_layer = []
        for i in range(raw_data.x.shape[0]):
            # Get the one-hot slice and find the argmax index
            one_hot = raw_data.x[i, :13]
            idx = int(torch.argmax(one_hot).item())
            ltype = layer_types[idx]
            node_layer.append(ltype)
            
        # Loop over valid edges
        valid_mask = raw_data.edge_mask
        if valid_mask.sum().item() == 0:
            continue
        valid_indices = torch.where(valid_mask)[0]
        # raw_data.edge_index shape is [2, num_edges]
        for i in valid_indices:
            edge_idx = int(i.item())
            src = int(raw_data.edge_index[0, edge_idx].item())
            # use the source node's layer type
            ltype = node_layer[src]
            type_resistances[ltype].append(raw_data.y[edge_idx].item())
    
    print("\nRaw resistance range by layer types (using source node layer):")
    for ltype, values in type_resistances.items():
        if values:
            min_val = min(values)
            max_val = max(values)
            print(f"{ltype}: min = {min_val:.4e} ohms, max = {max_val:.4e} ohms, span = {max_val/min_val:.2e}x")
        else:
            print(f"{ltype}: No valid resistance values found")
    
    return type_resistances

# Example usage:
if __name__ == "__main__":
    # Create dataset
    transform_type = 'asinh'
    dataset = ResistanceDataset(remove_outliers=False, transform_type=transform_type)

    
    # Create data loader
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Create model
    model = ResistanceRGCN(
        num_node_features=dataset.num_node_features,
        num_edge_features=dataset.num_edge_features,
        num_relations=4
    )
    
    # Get a sample graph and print debug info
    data = dataset[1]
    # print_pyg_data_debug_info(data, dataset.pos_encoding_dim, verbose=True)
    
    # Find resistance range
    print(f"Transform type: {dataset.transform_type}")
    min_res, max_res = find_resistance_range(dataset)
    min_res_raw, max_res_raw = find_resistance_range_raw(dataset)
    
    # Find and print the raw resistance range categorized by edge types
    find_resistance_range_by_edge_type(dataset)
    
    # Find and print the raw resistance range categorized by layer type (source node)
    find_resistance_range_by_layer_type(dataset)