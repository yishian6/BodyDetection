import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalNormalizationMS(nn.Module):
    """
    位置归一化（PONO）和矩连接（MS）模块。
    """

    def __init__(self, epsilon=1e-5):
        super(PositionalNormalizationMS, self).__init__()
        self.epsilon = epsilon

    def forward(self, x):
        mean = x.mean(dim=[2, 3], keepdim=True)  # 计算均值
        std = x.std(dim=[2, 3], keepdim=True)  # 计算标准差
        normalized = (x - mean) / (std + self.epsilon)  # 归一化
        return normalized, mean, std


class PyramidSqueezeAttention(nn.Module):
    """
    金字塔注意力模块（PSA）。
    """

    def __init__(self, in_channels, reduction=4):  # 将reduction改为4
        super(PyramidSqueezeAttention, self).__init__()
        self.conv1 = nn.Conv2d(
            in_channels * 4, max(in_channels // reduction, 1), kernel_size=1
        )
        self.conv2 = nn.Conv2d(
            max(in_channels // reduction, 1), in_channels, kernel_size=1
        )
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        branches = [
            F.adaptive_avg_pool2d(x, output_size=(1, 1)),
            F.adaptive_avg_pool2d(x, output_size=(2, 2)),
            F.adaptive_avg_pool2d(x, output_size=(4, 4)),
            F.adaptive_avg_pool2d(x, output_size=(8, 8)),
        ]
        branches = [
            F.interpolate(b, size=x.shape[2:], mode="nearest") for b in branches
        ]
        concat = torch.cat(branches, dim=1)
        attention = self.conv1(concat)
        attention = self.conv2(attention)
        attention = self.softmax(attention)
        return x * attention


class dehaze_net(nn.Module):
    def __init__(self):
        super(dehaze_net, self).__init__()

        self.relu = nn.ReLU(inplace=True)
        self.pono_ms = PositionalNormalizationMS()

        # Feature extraction layers
        self.e_conv1 = nn.Conv2d(3, 3, 1, 1, 0, bias=True)  # Increased channels
        self.e_conv2 = nn.Conv2d(3, 3, 3, 1, 1, bias=True)
        self.e_conv3 = nn.Conv2d(6, 3, 7, 1, 3, bias=True)  # Increased channels
        self.e_conv4 = nn.Conv2d(6, 6, 7, 1, 3, bias=True)  # Increased channels
        self.e_conv5 = nn.Conv2d(15, 12, 3, 1, 1, bias=True)  # Increased channels
        self.e_conv6 = nn.Conv2d(12, 16, 3, 1, 1, bias=True)  # Additional convolution
        self.e_conv7 = nn.Conv2d(16, 16, 3, 1, 1, bias=True)  # Additional convolution
        self.e_conv8 = nn.Conv2d(16, 3, 3, 1, 1, bias=True)  # Additional convolution
        self.e_conv9 = nn.Conv2d(47, 3, 3, 1, 1, bias=True)  # Output layer

        self.psa = PyramidSqueezeAttention(in_channels=16)

    def forward(self, x):
        # Feature extraction with PONO-MS
        x1 = self.relu(self.e_conv1(x))
        x1_pm, mean1, std1 = self.pono_ms(x1)  # PONO-MS

        x2 = self.relu(self.e_conv2(x1))
        x2_pm, mean2, std2 = self.pono_ms(x2)  # PONO-MS

        concat1 = torch.cat((x1, x2), 1)
        x3 = self.relu(self.e_conv3(concat1))
        # 重构变换
        x3 = std1 * x3 + mean1

        concat2 = torch.cat((x2, x3), 1)
        x4 = self.relu(self.e_conv4(concat2))
        # 重构变换
        # 复制 mean2 和 std2 以匹配 x4 的通道数
        mean2 = mean2.repeat(1, x4.size(1) // mean2.size(1), 1, 1)
        std2 = std2.repeat(1, x4.size(1) // std2.size(1), 1, 1)
        x4 = std2 * x4 + mean2

        concat3 = torch.cat((x1, x2, x3, x4), 1)
        x5 = self.relu(self.e_conv5(concat3))

        # Additional feature extraction
        x6 = self.relu(self.e_conv6(x5))

        psa = self.psa(x6)

        x7 = self.relu(self.e_conv7(psa))
        x8 = self.relu(self.e_conv8(x7))

        # Final feature integration and restoration
        k = self.e_conv9(
            torch.cat((x5, x6, x7, x8), 1)
        )  # Output layer (K value estimation)

        # Image restoration formula
        clean_image = self.relu(
            k * x - k + 1
        )  # Based on the improved atmospheric scattering model

        return clean_image


# 测试样例
if __name__ == "__main__":
    model = dehaze_net()
    print(model)

    # 使用随机输入张量（batch_size=1、通道=3、高度=64、宽度=64）进行测试
    input_tensor = torch.randn(1, 3, 64, 64)
    output = model(input_tensor)
    print("Output shape:", output.shape)
