import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalNormalization(nn.Module):
    """
    Positional Normalization (PONO) module.
    """

    def __init__(self, epsilon=1e-5):
        super(PositionalNormalization, self).__init__()
        self.epsilon = epsilon

    def forward(self, x):
        mean = x.mean(dim=[2, 3], keepdim=True)
        std = x.std(dim=[2, 3], keepdim=True)
        return (x - mean) / (std + self.epsilon), mean, std


class PyramidSqueezeAttention(nn.Module):
    """
    Pyramid Squeeze Attention (PSA) module.
    """

    def __init__(self, in_channels, reduction=16):
        super(PyramidSqueezeAttention, self).__init__()
        # Correct the input channels for conv1 to handle 4 branches
        self.conv1 = nn.Conv2d(4 * in_channels, in_channels // reduction, kernel_size=1)
        self.conv2 = nn.Conv2d(in_channels // reduction, in_channels, kernel_size=1)
        self.softmax = nn.Softmax(dim=1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # Split into branches
        branches = [
            F.adaptive_avg_pool2d(x, output_size=(1, 1)),
            F.adaptive_avg_pool2d(x, output_size=(2, 2)),
            F.adaptive_avg_pool2d(x, output_size=(4, 4)),
            F.adaptive_avg_pool2d(x, output_size=(8, 8)),
        ]
        branches = [
            F.interpolate(b, size=x.shape[2:], mode="nearest") for b in branches
        ]

        # Concatenate branches
        concat = torch.cat(branches, dim=1)  # Concatenate along the channel dimension
        attention = self.conv1(concat)
        attention = self.conv2(attention)
        attention = self.sigmoid(attention)  # Use sigmoid for attention weights
        return x * attention


class DehazeNet(nn.Module):
    def __init__(self):
        super(DehazeNet, self).__init__()

        self.relu = nn.ReLU(inplace=True)
        self.pono = PositionalNormalization()

        # Define 9 convolutional layers (as per the article's design)
        self.e_conv1 = nn.Conv2d(3, 16, 3, 1, 1, bias=True)  # First Conv Layer
        self.e_conv2 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Second Conv Layer
        self.e_conv3 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Third Conv Layer
        self.e_conv4 = nn.Conv2d(
            48, 16, 3, 1, 1, bias=True
        )  # Fourth Conv Layer (Input channels = 48)
        self.e_conv5 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Fifth Conv Layer
        self.e_conv6 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Sixth Conv Layer
        self.e_conv7 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Seventh Conv Layer
        self.e_conv8 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Eighth Conv Layer
        self.e_conv9 = nn.Conv2d(
            16, 3, 3, 1, 1, bias=True
        )  # Ninth Conv Layer (Output Layer)

        # Attention module
        self.psa = PyramidSqueezeAttention(in_channels=16)

    def forward(self, x):
        # Initial feature extraction
        x1 = self.relu(self.e_conv1(x))
        x1, mean1, std1 = self.pono(x1)  # Apply PONO after first layer

        x2 = self.relu(self.e_conv2(x1))
        x3 = self.relu(self.e_conv3(x2))

        # Feature concatenation and further processing
        concat1 = torch.cat((x1, x2, x3), 1)  # Concatenate features from early layers
        x4 = self.relu(self.e_conv4(concat1))

        x5 = self.relu(self.e_conv5(x4))
        x6 = self.relu(self.e_conv6(x5))

        # Introduce attention mechanism in the middle of the network
        x6 = self.psa(x6)  # Apply Pyramid Squeeze Attention

        x7 = self.relu(self.e_conv7(x6))
        x8 = self.relu(self.e_conv8(x7))

        # Final feature integration and restoration
        x9 = self.e_conv9(x8)  # Output layer (no activation here)

        # Image restoration formula
        clean_image = self.relu(
            (x9 * x) - x9 + 1
        )  # Element-wise operations for restoration

        return clean_image


# Example usage
if __name__ == "__main__":
    model = DehazeNet()
    print(model)

    # Test with a random input tensor (batch_size=1, channels=3, height=64, width=64)
    input_tensor = torch.randn(1, 3, 256, 256)
    output = model(input_tensor)
    print("Output shape:", output.shape)
