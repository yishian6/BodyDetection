import torch
import torchvision
import torch.optim
import time
import model as net
import numpy as np
from PIL import Image
import glob
from pathlib import Path


def dehaze_image(image_path, dehaze_net, save_path):
    data_hazy = Image.open(image_path)
    start = time.time()
    data_hazy = np.asarray(data_hazy) / 255.0

    data_hazy = torch.from_numpy(data_hazy).float()
    data_hazy = data_hazy.permute(2, 0, 1)
    data_hazy = data_hazy.cuda().unsqueeze(0)

    clean_image = dehaze_net(data_hazy)
    end = time.time()
    filename = image_path.split("\\")[-1]
    torchvision.utils.save_image(clean_image, Path(save_path) / filename)
    return end - start


if __name__ == "__main__":
    try:
        test_list = glob.glob(r"data\ir_align.png")
        dehaze_net = net.dehaze_net().cuda()
        dehaze_net.load_state_dict(torch.load(r"model\dehazer.pth"))
        all_time = 0
        for image in test_list:
            use_time = dehaze_image(image, dehaze_net, "./results")
            print(f"{image} 完成!  耗时：{use_time}秒")
            all_time += use_time if use_time < 0.1 else 0
        print("平均耗时: ", all_time / len(test_list))
    except ZeroDivisionError:
        print("没有图片")