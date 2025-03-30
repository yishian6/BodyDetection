import cv2
import numpy as np
from ultralytics import YOLO


class MultiModalVideoDetector:
    def __init__(
        self,
        ir_params: dict,
        tr_params: dict,
        model_path: str,
        output_path: str,
        conf_thres: float = 0.5,
        show_preview: bool = True,
    ):
        # 初始化视频捕获
        self.ir_cap = cv2.VideoCapture(ir_params["video_path"])
        self.tr_cap = cv2.VideoCapture(tr_params["video_path"])

        # 检查视频是否成功打开
        if not self.ir_cap.isOpened() or not self.tr_cap.isOpened():
            raise ValueError("无法打开视频文件")

        # 跳转到指定起始帧
        if "start_frame" in ir_params:
            self.ir_cap.set(cv2.CAP_PROP_POS_FRAMES, ir_params["start_frame"])
        if "start_frame" in tr_params:
            self.tr_cap.set(cv2.CAP_PROP_POS_FRAMES, tr_params["start_frame"])

        # 加载YOLO模型
        self.model = YOLO(model_path)

        # 设置参数
        self.ir_params = ir_params
        self.tr_params = tr_params
        self.conf_thres = conf_thres
        self.show_preview = show_preview

        # 创建输出视频写入器
        self.writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter.fourcc(*"mp4v"),
            25,  # 输出帧率
            ir_params["resolution"],
        )

        # 初始化帧计数器
        self.frame_count = 0

    def process_frame(self, frame: np.ndarray, params: dict) -> np.ndarray:
        """处理单帧图像"""
        if frame is None:
            return None

        x, y, w, h = map(int, params["crop_params"])
        frame = frame[y : y + h, x : x + w]
        return cv2.resize(frame, params["resolution"])

    def detect_and_draw(self, frame: np.ndarray) -> np.ndarray:
        """使用YOLO进行检测并绘制边界框"""
        results = self.model(
            frame,
            conf=self.conf_thres,
            classes=[0],
        )[0]
        annotated_frame = results.plot()
        return annotated_frame

    def run(self):
        """运行多模态视频检测"""
        while True:
            self.frame_count += 1

            # 每6帧丢弃一帧实现帧率同步
            if self.frame_count % 6 == 0:
                if not self.tr_cap.grab():
                    break
                continue

            # 获取两路视频帧
            if not (self.ir_cap.grab() and self.tr_cap.grab()):
                break

            ir_ret, ir_frame = self.ir_cap.retrieve()
            tr_ret, tr_frame = self.tr_cap.retrieve()

            if not (ir_ret and tr_ret):
                break

            # 处理帧
            ir_processed = self.process_frame(ir_frame, self.ir_params)
            tr_processed = self.process_frame(tr_frame, self.tr_params)

            # 显示原始帧
            if self.show_preview:
                cv2.imshow("IR Original", ir_frame)
                cv2.imshow("TR Original", tr_frame)

            # 融合两个模态，使用加权平均
            fused_frame = cv2.addWeighted(ir_processed, 0.3, tr_processed, 0.7, 0)

            # 目标检测和绘制
            output_frame = self.detect_and_draw(fused_frame)

            # 写入输出视频
            self.writer.write(output_frame)

            # 显示预览
            if self.show_preview:
                cv2.imshow("Detection", output_frame)
                key = cv2.waitKey(1)
                if key == 32:  # 空格暂停
                    while True:
                        if cv2.waitKey(0) == 32:  # 再次按空格继续
                            break
                elif key == 27:  # ESC退出
                    break

                if cv2.waitKey(1) == 27:  # ESC退出
                    break

        # 清理资源
        self.ir_cap.release()
        self.tr_cap.release()
        self.writer.release()
        if self.show_preview:
            cv2.destroyAllWindows()

    def gen(self):
        """生成实时视频流"""
        while True:
            self.frame_count += 1

            # 每6帧丢弃一帧实现帧率同步
            if self.frame_count % 6 == 0:
                if not self.tr_cap.grab():
                    break
                continue

            if not (self.ir_cap.grab() and self.tr_cap.grab()):
                break

            ir_ret, ir_frame = self.ir_cap.retrieve()
            tr_ret, tr_frame = self.tr_cap.retrieve()
            # 同时展示两路视频流
            cv2.imshow("IR", ir_frame)
            cv2.imshow("TR", tr_frame)

            if not (ir_ret and tr_ret):
                break

            # 处理帧
            ir_processed = self.process_frame(ir_frame, self.ir_params)
            tr_processed = self.process_frame(tr_frame, self.tr_params)

            # 融合两个模态
            fused_frame = cv2.addWeighted(ir_processed, 0.3, tr_processed, 0.7, 0)

            # 目标检测和绘制
            output_frame = self.detect_and_draw(fused_frame)

            # 转换图像格式用于流传输
            frame_bytes = cv2.imencode(".jpg", output_frame)[1].tobytes()
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )


def main():
    # IR视频参数
    ir_params = {
        "video_path": r"data/output_ir.mp4",
        "start_frame": int(138.8 * 25),
        "crop_params": (100, 0, int(640 * 2.5), int(512 * 2.5)),
        "resolution": (640, 512),
    }

    # TR视频参数
    tr_params = {
        "video_path": r"data/output_tr.mp4",
        "start_frame": 170 * 25,
        "crop_params": (0, 60, int(640 * 0.95), int(512 * 0.95)),
        "resolution": (640, 512),
    }

    # 创建检测器
    detector = MultiModalVideoDetector(
        ir_params=ir_params,
        tr_params=tr_params,
        model_path=r"model\yolo11n_merge_tr.pt",  # YOLO模型路径
        output_path="output_detection.mp4",
        conf_thres=0.6,
        show_preview=True,
    )

    # 运行检测
    detector.run()


if __name__ == "__main__":
    main()
