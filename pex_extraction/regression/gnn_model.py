"""Graph Neural Network (GNN) Models for Edge Regression.

This module defines the `EdgeRegressionGNN` class, which is used for predicting edge attributes (e.g., capacitance)
in a graph. It supports various GNN layers such as GraphSAGE, GAT, GIN, and others. Additionally, it provides utility
functions for initializing the model and setting random seeds for reproducibility.
"""

import random
import numpy as np
import torch
import torch.nn.functional as F
from torch.nn import (
    ModuleList, Linear, ReLU, BatchNorm1d, Dropout, Softplus, PReLU,
    LeakyReLU, GELU, Hardswish, Mish, Tanh
)
from torch_geometric.nn import (
    SAGEConv, GCNConv, GATConv, EdgeConv, GINConv, TransformerConv,
    NNConv, GATv2Conv
)
from torch_geometric.utils import negative_sampling
import logging

logger = logging.getLogger('sivista_app')

def set_seed(seed):
    """Set random seed for reproducibility.

    Args:
        seed (int): Seed value for random number generators.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class EdgeRegressionGNN(torch.nn.Module):
    """Graph Neural Network for Edge Regression Tasks.

    This model predicts edge attributes (e.g., capacitance) based on node embeddings and their relationships in the graph.

    Args:
        in_channels (int): Number of input features per node.
        hidden_channels (int): Number of hidden units in each layer.
        num_layers (int, optional): Number of GNN layers. Defaults to 2.
        dropout (float, optional): Dropout rate between layers. Defaults to 0.0.
        activation (nn.Module, optional): Activation function to use. Defaults to ReLU().
        conv_type (str, optional): Type of GNN convolution layer. Defaults to 'GraphSAGE'.
        use_batch_norm (bool, optional): Whether to use Batch Normalization. Defaults to False.
        use_residual (bool, optional): Whether to use residual connections. Defaults to False.
        **kwargs: Additional keyword arguments for specific convolution layers.
    """

    def __init__(
        self,
        in_channels,
        hidden_channels,
        num_layers=2,
        dropout=0.0,
        activation=ReLU(),
        conv_type='GraphSAGE',
        use_batch_norm=False,
        use_residual=False,
        **kwargs
    ):
        super(EdgeRegressionGNN, self).__init__()

        self.use_batch_norm = use_batch_norm
        self.use_residual = use_residual
        self.activation = activation
        self.dropout = Dropout(dropout)

        # Select convolutional layer type and initialize convolutional layers
        # Different GNN models have unique architectures and requirements, which is why they are set up differently.
        if conv_type == 'GraphSAGE':
            # GraphSAGE is designed to aggregate information from a node's neighbors, hence it uses SAGEConv.
            ConvLayer = SAGEConv
            conv_kwargs = {}
        elif conv_type == 'GAT':
            # GAT uses attention mechanisms to weigh the importance of neighboring nodes, requiring 'heads' for multi-head attention.
            ConvLayer = GATConv
            conv_kwargs = {'heads': kwargs.get('heads', 1)}
        elif conv_type == 'GATv2Conv':
            # GATv2Conv is an improved version of GAT, allowing for more flexible attention mechanisms.
            # It uses 'concat' to control output dimensions and 'dropout' for regularization.
            ConvLayer = GATv2Conv
            conv_kwargs = {
                'heads': kwargs.get('heads', 1),
                'concat': False,  # Set concat=False to keep output dimension consistent
                'dropout': dropout
            }
        elif conv_type == 'EdgeConv':
            # EdgeConv is used in dynamic graph construction, focusing on edge features.
            # It uses a custom lambda function to define the convolution operation.
            ConvLayer = lambda in_channels, out_channels: EdgeConv(
                nn=torch.nn.Sequential(
                    Linear(2 * in_channels, out_channels),
                    activation
                )
            )
            conv_kwargs = {}
        elif conv_type == 'GINConv':
            # GINConv is designed for powerful node representation learning, using a specific MLP structure.
            nn_module = torch.nn.Sequential(
                Linear(hidden_channels, hidden_channels),
                activation,
                Linear(hidden_channels, hidden_channels)
            )
            ConvLayer = lambda in_channels, out_channels: GINConv(nn_module)
            conv_kwargs = {}
        elif conv_type == 'TransformerConv':
            # TransformerConv incorporates transformer-like attention mechanisms into GNNs.
            # It uses 'heads' for multi-head attention and 'concat' for output dimension control.
            ConvLayer = TransformerConv
            conv_kwargs = {
                'heads': kwargs.get('heads', 1),
                'concat': False,  # Set concat=False to keep output dimension consistent
                'dropout': dropout
            }
        elif conv_type == 'NNConv':
            # NNConv uses neural networks to compute edge-specific weights, requiring edge attribute dimensions.
            edge_attr_dim = kwargs.get('edge_attr_dim', 1)  # Adjust based on your edge_attr dimension
            nn_module = torch.nn.Sequential(
                Linear(edge_attr_dim, hidden_channels * hidden_channels)
            )
            ConvLayer = lambda in_channels, out_channels: NNConv(
                in_channels, out_channels, nn=nn_module, aggr='mean'
            )
            conv_kwargs = {}
        else:
            raise ValueError(f"Unsupported conv_type: {conv_type}")

        self.convs = ModuleList()
        self.batch_norms = ModuleList() if use_batch_norm else None

        # Input projection to match dimensions for residual connection
        # This ensures that the input dimensions are compatible with the hidden layer dimensions.
        if in_channels != hidden_channels:
            self.input_proj = Linear(in_channels, hidden_channels)
        else:
            self.input_proj = None

        # Determine output channels after convolution
        # For certain convolution types, the output dimension depends on the number of attention heads.
        if conv_type in ['GAT', 'GATv2Conv', 'TransformerConv']:
            if conv_kwargs.get('concat', True):
                conv_out_channels = hidden_channels * conv_kwargs.get('heads', 1)
            else:
                conv_out_channels = hidden_channels
        else:
            conv_out_channels = hidden_channels


        # Build convolutional layers
        self.convs.append(ConvLayer(hidden_channels, hidden_channels, **conv_kwargs))
        if use_batch_norm:
            self.batch_norms.append(BatchNorm1d(conv_out_channels))

        for _ in range(num_layers - 1):
            self.convs.append(ConvLayer(conv_out_channels, hidden_channels, **conv_kwargs))
            if use_batch_norm:
                self.batch_norms.append(BatchNorm1d(conv_out_channels))

        # Edge predictor module for regression tasks
        self.edge_predictor = torch.nn.Sequential(
            Linear(2 * conv_out_channels, hidden_channels),
            activation,
            Linear(hidden_channels, 1),
            Softplus()  # Use Softplus activation for non-negative output
        )

    def forward(self, data):
        """Forward pass of the model.

        Args:
            data (torch_geometric.data.Data): Input graph data containing node features and edge indices.

        Returns:
            Tensor: Predicted edge attributes (e.g., capacitance values).
        """
        x, edge_index = data.x, data.edge_index

        # Apply input projection if needed
        if self.input_proj is not None:
            x = self.input_proj(x)

        if self.use_residual:
            residual = x
        else:
            residual = None

        for i, conv in enumerate(self.convs):
            if isinstance(conv, NNConv):
                edge_attr = data.edge_attr
                x_new = conv(x, edge_index, edge_attr)
            else:
                x_new = conv(x, edge_index)

            if self.use_batch_norm:
                x_new = self.batch_norms[i](x_new)
            x_new = self.activation(x_new)
            x_new = self.dropout(x_new)

            if self.use_residual:
                x_new = x_new + x  # Residual connection
            x = x_new  # Update x for next layer

        # Edge feature computation for regression
        row, col = edge_index
        edge_features = torch.cat([torch.abs(x[row] - x[col]), x[row] * x[col]], dim=1)

        # Predict edge values
        edge_predictions = self.edge_predictor(edge_features).squeeze()

        return edge_predictions

def get_activation_function(name):
    """Get activation function by name.

    Args:
        name (str): Name of the activation function.

    Returns:
        nn.Module: Activation function module.

    Raises:
        ValueError: If the activation function is not supported.
    """
    if name == 'relu':
        return ReLU()
    elif name == 'leaky_relu':
        return LeakyReLU()
    elif name == 'prelu':
        return PReLU()
    elif name == 'mish':
        return Mish()
    elif name == 'hardswish':
        return Hardswish()
    elif name == 'gelu':
        return GELU()
    elif name == 'tanh':
        return Tanh()
    else:
        raise ValueError(f"Unsupported activation: {name}")

def initGNN(embedding_dim, best_params, model_save_path, device):
    """Initialize and load the GNN model with best parameters.

    Args:
        embedding_dim (int): Dimension of the node embeddings.
        best_params (dict): Dictionary of best hyperparameters.
        model_save_path (str): Path to the saved model state dict.
        device (torch.device): Device to load the model onto.

    Returns:
        EdgeRegressionGNN: Initialized GNN model with loaded weights.
    """
    set_seed(42)

    # Extract hyperparameters with defaults
    learning_rate = best_params.get('learning_rate', 5.1105e-05)
    hidden_channels = best_params.get('hidden_channels', 471)
    batch_size = best_params.get('batch_size', 32)
    optimizer_name = best_params.get('optimizer', 'Adam')
    num_layers = best_params.get('num_layers', 5)
    dropout_rate = best_params.get('dropout_rate', 0.0)
    weight_decay = best_params.get('weight_decay', 0.00286885)
    activation_name = best_params.get('activation', 'relu')
    use_batch_norm = best_params.get('use_batch_norm', True)
    conv_type = best_params.get('conv_type', 'GraphSAGE')
    use_residual = best_params.get('use_residual', True)
    max_grad_norm = best_params.get('max_grad_norm', 0.0)
    scheduler_type = best_params.get('scheduler_type', 'CosineAnnealingLR')


    # Additional arguments for specific convolution layers
    conv_kwargs = {}
    if conv_type in ['GAT', 'GATv2Conv', 'TransformerConv']:
        conv_kwargs['heads'] = best_params.get('heads', 1)
    if conv_type == 'NNConv':
        conv_kwargs['edge_attr_dim'] = 1  # Adjust based on your edge attribute dimension

    # Select activation function
    activation = get_activation_function(activation_name)

    # Initialize the model
    best_model = EdgeRegressionGNN(
        in_channels=embedding_dim,
        hidden_channels=hidden_channels,
        num_layers=num_layers,
        dropout=dropout_rate,
        activation=activation,
        conv_type=conv_type,
        use_batch_norm=use_batch_norm,
        use_residual=use_residual,
        **conv_kwargs
    ).to(device)

    # Load state dictionary
    best_model.load_state_dict(torch.load(model_save_path, map_location=device))
    return best_model