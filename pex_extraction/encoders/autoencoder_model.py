"""Autoencoder Models and Related Classes.

This module defines various autoencoder architectures and related utility classes,
such as Residual Blocks and Elastic Weight Consolidation (EWC) for incremental learning.
"""

import torch
import torch.nn as nn
import numpy as np

# Global variable for the number of polygon columns (used in only 2312 and 512 models, not used in incremental models)
polygons_columns_len = 26


class ResidualBlock(nn.Module):
    """Residual Block with optional convolutional shortcut.

    Implements a residual block with two convolutional layers and an optional
    convolutional shortcut connection.

    Args:
        in_channels (int): Number of input channels.
        out_channels (int): Number of output channels.
        kernel_size (int, optional): Size of the convolutional kernels. Default is 5.
        stride (int, optional): Stride of the convolution. Default is 1.
        conv_shortcut (bool, optional): If True, use convolution in the shortcut connection.
            If False, use identity shortcut. Default is True.
        regularization_factor (float, optional): Regularization factor for any regularization applied.
            Default is 0.001.

    Attributes:
        conv_shortcut (bool): Indicates if convolutional shortcut is used.
        regularization_factor (float): Regularization factor.
        shortcut (nn.Module): Convolutional layer for shortcut connection if conv_shortcut is True.
        conv1 (nn.Module): First convolutional layer in the block.
        conv2 (nn.Module): Second convolutional layer in the block.
        relu (nn.Module): ReLU activation function.
    """

    def __init__(self, in_channels, out_channels, kernel_size=5, stride=1,
                 conv_shortcut=True, regularization_factor=0.001):
        super(ResidualBlock, self).__init__()
        self.conv_shortcut = conv_shortcut
        self.regularization_factor = regularization_factor

        if conv_shortcut:
            # Define the convolutional shortcut layer
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride)

        # Define convolutional layers with padding to maintain spatial dimensions
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size,
                               stride=stride, padding='same')
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size,
                               padding='same')
        self.relu = nn.ReLU()

    def forward(self, x):
        """Forward pass of the Residual Block.

        Args:
            x (Tensor): Input tensor.

        Returns:
            Tensor: Output tensor after passing through the residual block.
        """
        # Apply shortcut connection
        shortcut = self.shortcut(x) if self.conv_shortcut else x

        # Convolutional layers with ReLU activations
        x = self.conv1(x)
        x = self.relu(x)
        x = self.conv2(x)

        # Add the shortcut connection
        x += shortcut
        return self.relu(x)


class AutoencoderIncremental(nn.Module):
    """Autoencoder Model for Incremental Learning.

    This autoencoder uses residual blocks in its architecture and is designed for incremental learning scenarios.

    Args:
        grid_size (int, optional): Size of the input grid. Default is 64.
        num_channels (int): Number of input channels.
        regularization_factor (float, optional): Regularization factor for regularization layers. Default is 0.001.

    Attributes:
        num_channels (int): Number of input channels.
        res_block1 (ResidualBlock): First residual block in the encoder.
        pool1 (nn.Module): First pooling layer in the encoder.
        res_block2 (ResidualBlock): Second residual block in the encoder.
        pool2 (nn.Module): Second pooling layer in the encoder.
        flatten (nn.Module): Flattening layer for encoded features.
        fc (nn.Module): Fully connected layer in the decoder.
        upsample1 (nn.Module): First upsampling layer in the decoder.
        res_block3 (ResidualBlock): Residual block in the decoder.
        upsample2 (nn.Module): Second upsampling layer in the decoder.
        spatial_output_conv (nn.Module): Final convolutional layer producing the output.
        spatial_output_activation (nn.Module): Activation function applied to the output (Sigmoid).
        dropout (nn.Module): Dropout layer for regularization.
    """

    def __init__(self, grid_size=64, num_channels=None, regularization_factor=0.001):
        super(AutoencoderIncremental, self).__init__()

        if num_channels is None:
            raise ValueError("Number of channels must be specified.")
        self.num_channels = num_channels

        # Encoder
        self.res_block1 = ResidualBlock(self.num_channels, 16,
                                        regularization_factor=regularization_factor)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.res_block2 = ResidualBlock(16, 8, regularization_factor=regularization_factor)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.flatten = nn.Flatten()

        # Decoder
        encoded_size = 2312  # Calculate the correct encoded size based on your architecture
        self.fc = nn.Linear(encoded_size, 16 * 16 * 8)
        self.upsample1 = nn.Upsample(scale_factor=2, mode='nearest')
        self.res_block3 = ResidualBlock(8, 16, regularization_factor=regularization_factor)
        self.upsample2 = nn.Upsample(scale_factor=2, mode='nearest')
        self.spatial_output_conv = nn.Conv2d(16, num_channels, kernel_size=5, padding='same')
        self.spatial_output_activation = nn.Sigmoid()

        self.dropout = nn.Dropout(0.5)

    def forward(self, spatial_input):
        """Forward pass of the autoencoder.

        Args:
            spatial_input (Tensor): Input tensor with shape (batch_size, num_channels, grid_size, grid_size).

        Returns:
            Tensor: Reconstructed output tensor.
        """
        # Encode spatial input
        x = self.res_block1(spatial_input)
        x = self.pool1(x)
        x = self.res_block2(x)
        x = self.pool2(x)
        spatial_encoded = self.flatten(x)

        # Decode spatial output
        x = self.fc(spatial_encoded)
        x = x.view(-1, 8, 16, 16)
        x = self.upsample1(x)
        x = self.res_block3(x)
        x = self.upsample2(x)
        x = self.spatial_output_conv(x)
        spatial_decoded = self.spatial_output_activation(x)

        return spatial_decoded


class EncoderIncremental(nn.Module):
    """Encoder Part of the Incremental Autoencoder.

    This class extracts the encoder part of the AutoencoderIncremental for standalone encoding purposes.
    Although in the main code, we developed a wrapper for direct extraction of the encoder,
    this class is kept for completeness and future reference.

    Args:
        num_channels (int): Number of input channels.

    Attributes:
        num_channels (int): Number of input channels.
        res_block1 (ResidualBlock): First residual block in the encoder.
        pool1 (nn.Module): First pooling layer.
        res_block2 (ResidualBlock): Second residual block in the encoder.
        pool2 (nn.Module): Second pooling layer.
        flatten (nn.Module): Flattening layer for encoded features.
    """

    def __init__(self, num_channels=None):
        super(EncoderIncremental, self).__init__()
        if num_channels is None:
            raise ValueError("Number of channels must be specified.")
        self.num_channels = num_channels

        # Encoder layers
        self.res_block1 = ResidualBlock(self.num_channels, 16)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.res_block2 = ResidualBlock(16, 8)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.flatten = nn.Flatten()

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


class Autoencoder2312(nn.Module):
    """Autoencoder Model with Encoded Size of 2312.

    This autoencoder is designed with an encoded size of 2312 based on the architecture.

    Args:
        grid_size (int, optional): Size of the input grid. Default is 64.
        polygons_columns_len (int, optional): Number of polygon columns. Default is 26.
        regularization_factor (float, optional): Regularization factor. Default is 0.001.

    Attributes:
        res_block1 (ResidualBlock): First residual block in the encoder.
        pool1 (nn.Module): First pooling layer.
        res_block2 (ResidualBlock): Second residual block in the encoder.
        pool2 (nn.Module): Second pooling layer.
        flatten (nn.Module): Flattening layer.
        fc (nn.Module): Fully connected layer in the decoder.
        upsample1 (nn.Module): First upsampling layer.
        res_block3 (ResidualBlock): Residual block in the decoder.
        upsample2 (nn.Module): Second upsampling layer.
        spatial_output_conv (nn.Module): Final convolutional layer.
        spatial_output_activation (nn.Module): Sigmoid activation for output.
        dropout (nn.Module): Dropout layer.
    """

    def __init__(self, grid_size=64, polygons_columns_len=polygons_columns_len,
                 regularization_factor=0.001):
        super(Autoencoder2312, self).__init__()

        # Encoder
        self.res_block1 = ResidualBlock(polygons_columns_len, 16,
                                        regularization_factor=regularization_factor)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.res_block2 = ResidualBlock(16, 8, regularization_factor=regularization_factor)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.flatten = nn.Flatten()

        # Decoder
        encoded_size = 2312  # This should be calculated based on the architecture
        self.fc = nn.Linear(encoded_size, 16 * 16 * 8)
        self.upsample1 = nn.Upsample(scale_factor=2, mode='nearest')
        self.res_block3 = ResidualBlock(8, 16, regularization_factor=regularization_factor)
        self.upsample2 = nn.Upsample(scale_factor=2, mode='nearest')
        self.spatial_output_conv = nn.Conv2d(16, polygons_columns_len,
                                             kernel_size=5, padding='same')
        self.spatial_output_activation = nn.Sigmoid()

        self.dropout = nn.Dropout(0.5)

    def forward(self, spatial_input):
        """Forward pass of the autoencoder.

        Args:
            spatial_input (Tensor): Input tensor.

        Returns:
            Tensor: Reconstructed output tensor.
        """
        # Encode spatial input
        x = self.res_block1(spatial_input)
        x = self.pool1(x)
        x = self.res_block2(x)
        x = self.pool2(x)
        spatial_encoded = self.flatten(x)

        # Decode spatial output
        x = self.fc(spatial_encoded)
        x = x.view(-1, 8, 16, 16)
        x = self.upsample1(x)
        x = self.res_block3(x)
        x = self.upsample2(x)
        x = self.spatial_output_conv(x)
        spatial_decoded = self.spatial_output_activation(x)

        return spatial_decoded


class Encoder2312(nn.Module):
    """Encoder Part of the Autoencoder2312 Model.

    This class extracts the encoder part of the Autoencoder2312.

    Attributes:
        res_block1 (ResidualBlock): First residual block in the encoder.
        pool1 (nn.Module): First pooling layer.
        res_block2 (ResidualBlock): Second residual block in the encoder.
        pool2 (nn.Module): Second pooling layer.
        flatten (nn.Module): Flattening layer.
    """

    def __init__(self):
        super(Encoder2312, self).__init__()
        self.res_block1 = ResidualBlock(polygons_columns_len, 16)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.res_block2 = ResidualBlock(16, 8)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=(1, 1))
        self.flatten = nn.Flatten()

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


class Autoencoder512(nn.Module):
    """Autoencoder Model with Encoded Size of 512.

    This autoencoder is designed with an encoded size of 512 based on the architecture.

    Args:
        grid_size (int, optional): Size of the input grid. Default is 64.
        polygons_columns_len (int, optional): Number of polygon columns. Default is 26.
        regularization_factor (float, optional): Regularization factor. Default is 0.001.

    Attributes:
        res_block1 (ResidualBlock): First residual block in the encoder.
        pool1 (nn.Module): First pooling layer.
        res_block2 (ResidualBlock): Second residual block in the encoder.
        pool2 (nn.Module): Second pooling layer.
        res_block3 (ResidualBlock): Third residual block in the encoder.
        pool3 (nn.Module): Third pooling layer.
        flatten (nn.Module): Flattening layer.
        fc (nn.Module): Fully connected layer in the decoder.
        upsample1 (nn.Module): First upsampling layer.
        res_block4 (ResidualBlock): Fourth residual block in the decoder.
        upsample2 (nn.Module): Second upsampling layer.
        res_block5 (ResidualBlock): Fifth residual block in the decoder.
        upsample3 (nn.Module): Third upsampling layer.
        spatial_output_conv (nn.Module): Final convolutional layer.
        spatial_output_activation (nn.Module): Activation function for output.
        dropout (nn.Module): Dropout layer.
    """

    def __init__(self, grid_size=64, polygons_columns_len=26, regularization_factor=0.001):
        super(Autoencoder512, self).__init__()

        # Encoder
        self.res_block1 = ResidualBlock(polygons_columns_len, 16,
                                        regularization_factor=regularization_factor)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.res_block2 = ResidualBlock(16, 8, regularization_factor=regularization_factor)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.res_block3 = ResidualBlock(8, 8, regularization_factor=regularization_factor)
        self.pool3 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.flatten = nn.Flatten()

        # Decoder
        encoded_size = 8 * 8 * 8  # 512
        self.fc = nn.Linear(encoded_size, 8 * 8 * 8)
        self.upsample1 = nn.Upsample(scale_factor=2, mode='nearest')
        self.res_block4 = ResidualBlock(8, 8, regularization_factor=regularization_factor)
        self.upsample2 = nn.Upsample(scale_factor=2, mode='nearest')
        self.res_block5 = ResidualBlock(8, 16, regularization_factor=regularization_factor)
        self.upsample3 = nn.Upsample(scale_factor=2, mode='nearest')
        self.spatial_output_conv = nn.Conv2d(16, polygons_columns_len,
                                             kernel_size=5, padding='same')
        self.spatial_output_activation = nn.Sigmoid()

        self.dropout = nn.Dropout(0.5)

    def forward(self, spatial_input):
        """Forward pass of the autoencoder.

        Args:
            spatial_input (Tensor): Input tensor.

        Returns:
            Tensor: Reconstructed output tensor.
        """
        # Encode spatial input
        x = self.res_block1(spatial_input)
        x = self.pool1(x)
        x = self.res_block2(x)
        x = self.pool2(x)
        x = self.res_block3(x)
        x = self.pool3(x)
        spatial_encoded = self.flatten(x)

        # Decode spatial output
        x = self.fc(spatial_encoded)
        x = x.view(-1, 8, 8, 8)  # Reshape for upsampling
        x = self.upsample1(x)
        x = self.res_block4(x)
        x = self.upsample2(x)
        x = self.res_block5(x)
        x = self.upsample3(x)
        x = self.spatial_output_conv(x)
        spatial_decoded = self.spatial_output_activation(x)

        return spatial_decoded


class Encoder512(nn.Module):
    """Encoder Part of the Autoencoder512 Model.

    This class extracts the encoder part of the Autoencoder512.

    Args:
        grid_size (int, optional): Size of the input grid. Default is 64.
        polygons_columns_len (int, optional): Number of polygon columns. Default is 26.
        regularization_factor (float, optional): Regularization factor. Default is 0.001.

    Attributes:
        res_block1 (ResidualBlock): First residual block.
        pool1 (nn.Module): First pooling layer.
        res_block2 (ResidualBlock): Second residual block.
        pool2 (nn.Module): Second pooling layer.
        res_block3 (ResidualBlock): Third residual block.
        pool3 (nn.Module): Third pooling layer.
        flatten (nn.Module): Flattening layer.
    """

    def __init__(self, grid_size=64, polygons_columns_len=26, regularization_factor=0.001):
        super(Encoder512, self).__init__()

        # Encoder layers from the Autoencoder
        self.res_block1 = ResidualBlock(polygons_columns_len, 16,
                                        regularization_factor=regularization_factor)
        self.pool1 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.res_block2 = ResidualBlock(16, 8, regularization_factor=regularization_factor)
        self.pool2 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.res_block3 = ResidualBlock(8, 8, regularization_factor=regularization_factor)
        self.pool3 = nn.MaxPool2d(kernel_size=2, padding=0)
        self.flatten = nn.Flatten()

    def forward(self, spatial_input):
        """Forward pass through the encoder.

        Args:
            spatial_input (Tensor): Input tensor.

        Returns:
            Tensor: Encoded representation.
        """
        x = self.res_block1(spatial_input)
        x = self.pool1(x)
        x = self.res_block2(x)
        x = self.pool2(x)
        x = self.res_block3(x)
        x = self.pool3(x)
        x = self.flatten(x)
        return x


class EWC(object):
    """Elastic Weight Consolidation (EWC) for Incremental Learning.

    A utility class to implement EWC in order to alleviate catastrophic forgetting
    in neural networks during incremental learning.

    Args:
        model (nn.Module): Neural network model.
        dataset (torch.utils.data.Dataset): Dataset for the model.
        device (torch.device): Device to perform computations on.
    """

    def __init__(self, model, dataset, device):
        self.model = model
        self.dataset = dataset
        self.device = device

        # Initialize the precision matrices
        self.params = {n: p.clone().detach() for n, p in self.model.named_parameters() if p.requires_grad}
        self._precision_matrices = self._diag_fisher()

        for n, p in self.params.items():
            self._precision_matrices[n] = self._precision_matrices[n] + 0 * p

    def _diag_fisher(self):
        """Compute the diagonal of the Fisher Information matrix.

        Returns:
            dict: Dictionary containing the precision matrices for parameters.
        """
        self.model.eval()
        precision_matrices = {}
        for n, p in self.model.named_parameters():
            if p.requires_grad:
                precision_matrices[n] = torch.zeros_like(p).to(self.device)

        # Create data loader
        data_loader = torch.utils.data.DataLoader(self.dataset, batch_size=1, shuffle=True)
        for input_batch in data_loader:
            self.model.zero_grad()
            # Unpack the input tensor from the tuple/list
            if isinstance(input_batch, (list, tuple)):
                input = input_batch[0].to(self.device)
            else:
                input = input_batch.to(self.device)
            output = self.model(input)
            loss = nn.functional.binary_cross_entropy(output, input)
            loss.backward()
            for n, p in self.model.named_parameters():
                if p.requires_grad:
                    precision_matrices[n] += p.grad.detach() ** 2

        # Average the precision matrices
        for n in precision_matrices:
            precision_matrices[n] = precision_matrices[n] / len(self.dataset)

        return precision_matrices

    def penalty(self, model):
        """Calculate the EWC penalty.

        Args:
            model (nn.Module): Current neural network model.

        Returns:
            Tensor: Scalar tensor representing the EWC penalty.
        """
        loss = 0
        for n, p in model.named_parameters():
            if p.requires_grad:
                _loss = self._precision_matrices[n] * (p - self.params[n]) ** 2
                loss += _loss.sum()
        return loss