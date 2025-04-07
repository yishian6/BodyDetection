import os
import zipfile
import uuid
import yaml
import shutil
import threading
import time
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from src.task_manager import task_manager, TaskStatus
from src.config import get_logger, VAL_FOLDER, UPLOAD_FOLDER, get_model_path
from ultralytics import YOLO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = get_logger()

val_bp = Blueprint("val", __name__, url_prefix="/val")


""" 
VAL_FOLDER 
- task_id
-- train
--- images
--- labels
-- val
--- images
--- labels
-- data.yaml
-- val_results
--- F1_curve.png
--- PR_curve.png
--- result.pdf
"""


def generate_validation_report(task_dir, metrics):
    """
    生成验证报告PDF

    Args:
        task_dir: 任务目录路径
        metrics: 验证指标
    """
    # 创建PDF文档
    doc = SimpleDocTemplate(
        os.path.join(task_dir, "val_results", "result.pdf"),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # 创建样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=16,
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=12,
    )

    # 创建内容
    story = []

    # 添加标题
    story.append(Paragraph("YOLO Model Validation Report", title_style))
    story.append(Spacer(1, 12))

    # 添加性能指标表格
    story.append(Paragraph("Performance Metrics", heading_style))
    story.append(Spacer(1, 12))

    # 准备表格数据
    data = [
        ["Metric", "Value"],
        ["mAP50", f"{metrics['mAP50']:.4f}"],
        ["mAP50-95", f"{metrics['mAP50-95']:.4f}"],
        ["Precision", f"{metrics['precision']:.4f}"],
        ["Recall", f"{metrics['recall']:.4f}"],
        ["F1 Score", f"{metrics['f1']:.4f}"],
        ["Inference Speed", f"{metrics['speed']:.2f} ms/image"],
    ]

    # 创建表格
    table = Table(data, colWidths=[2 * inch, 3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 20))

    # 添加PR曲线
    story.append(Paragraph("PR Curve", heading_style))
    story.append(Spacer(1, 12))
    pr_curve_path = os.path.join(task_dir, "val_results", "PR_curve.png")
    if os.path.exists(pr_curve_path):
        img = Image(pr_curve_path, width=6 * inch, height=4 * inch)
        story.append(img)
    story.append(Spacer(1, 20))

    # 添加F1曲线
    story.append(Paragraph("F1 Curve", heading_style))
    story.append(Spacer(1, 12))
    f1_curve_path = os.path.join(task_dir, "val_results", "F1_curve.png")
    if os.path.exists(f1_curve_path):
        img = Image(f1_curve_path, width=6 * inch, height=4 * inch)
        story.append(img)

    # 生成PDF
    doc.build(story)


def process_validation(task_id, zip_path, model_path):
    """
    异步处理验证任务

    Args:
        task_id: 任务ID
        zip_path: ZIP文件路径
        model_path: 模型路径
    """
    try:
        # 创建任务目录结构
        task_dir = os.path.join(VAL_FOLDER, task_id)
        train_dir = os.path.join(task_dir, "train")
        val_dir = os.path.join(task_dir, "val")
        os.makedirs(os.path.join(train_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(train_dir, "labels"), exist_ok=True)
        os.makedirs(os.path.join(val_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(val_dir, "labels"), exist_ok=True)

        # 解压文件到临时目录
        temp_extract_path = os.path.join(UPLOAD_FOLDER, "val", f"temp_{task_id}")
        os.makedirs(temp_extract_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_extract_path)

        # 验证数据集结构
        validation_result = validate_dataset(temp_extract_path)

        if validation_result["is_valid"]:
            # 将数据集移动到正确的目录结构
            move_dataset_to_structure(temp_extract_path, task_dir)
            
            # 创建data.yaml文件
            yaml_path = create_data_yaml(
                task_dir, validation_result["stats"]["classes"]
            )

            # 使用YOLO模型进行验证
            model_validation_result = validate_with_model(model_path, task_dir)
            
            # 生成验证报告
            generate_validation_report(
                task_dir, model_validation_result["model_stats"]["metrics"]
            )
            
            # 准备任务结果
            result = {
                "dataset_stats": validation_result["stats"],
                "model_stats": model_validation_result["model_stats"],
                "report_path": os.path.join(task_dir, "val_results", "result.pdf"),
            }
            
            logger.info(f"YOLO模型验证测试集完成，任务 {task_id} 验证成功")
            task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result=result,
            )
        else:
            task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=validation_result["error"],
            )
            logger.error(
                f"数据集验证失败，任务 {task_id} 失败: {validation_result['error']}"
            )

    except Exception as e:
        logger.error(f"验证数据集时出错: {str(e)}")
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=f"验证数据集时出错: {str(e)}",
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)


@val_bp.route("", methods=["POST"])
def upload_val_dataset():
    """
    上传并验证数据集，使用YOLO模型的val模式进行验证

    请求参数:
    - file: ZIP文件，包含验证数据集
    - model_name: 模型名称（可选）

    返回:
    {
        "task_id": "任务ID",
        "message": "数据集上传成功，正在验证"
    }
    """
    if "file" not in request.files:
        return jsonify({"error": "没有上传文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    if not file.filename.endswith(".zip"):
        return jsonify({"error": "只支持ZIP格式的文件"}), 400

    # 获取模型名称（如果有）
    model_name = request.form.get("model_name")
    model_path = get_model_path(model_name)

    # 生成任务ID
    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id)

    # 保存ZIP文件
    zip_filename = secure_filename(file.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, "val", zip_filename)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    file.save(zip_path)

    # 更新任务状态为处理中
    task_manager.update_task(
        task_id=task_id,
        status=TaskStatus.PROCESSING,
    )

    # 创建新线程处理验证任务
    thread = threading.Thread(
        target=process_validation,
        args=(task_id, zip_path, model_path),
    )
    thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
    thread.start()

    return jsonify({"task_id": task_id, "message": "数据集上传成功，正在验证"})


def move_dataset_to_structure(source_path, task_dir):
    """
    将数据集移动到正确的目录结构

    Args:
        source_path: 源数据集路径
        task_dir: 任务目录路径
    """
    # 移动训练集
    train_images = os.path.join(source_path, "images")
    train_labels = os.path.join(source_path, "labels")
    
    if os.path.exists(train_images):
        for file in os.listdir(train_images):
            if file.endswith((".jpg", ".jpeg", ".png")):
                shutil.copy2(
                    os.path.join(train_images, file),
                    os.path.join(task_dir, "train", "images", file),
                )
    
    if os.path.exists(train_labels):
        for file in os.listdir(train_labels):
            if file.endswith(".txt"):
                shutil.copy2(
                    os.path.join(train_labels, file),
                    os.path.join(task_dir, "train", "labels", file),
                )

    # 移动验证集（这里我们使用相同的图片作为验证集）
    val_images = os.path.join(task_dir, "train", "images")
    val_labels = os.path.join(task_dir, "train", "labels")
    
    for file in os.listdir(val_images):
        if file.endswith((".jpg", ".jpeg", ".png")):
            shutil.copy2(
                os.path.join(val_images, file),
                os.path.join(task_dir, "val", "images", file),
            )
    
    for file in os.listdir(val_labels):
        if file.endswith(".txt"):
            shutil.copy2(
                os.path.join(val_labels, file),
                os.path.join(task_dir, "val", "labels", file),
            )


def validate_dataset(dataset_path):
    """
    验证数据集的结构和内容

    Args:
        dataset_path: 数据集路径

    Returns:
        dict: 验证结果
    """
    result = {
        "is_valid": False,
        "error": None,
        "stats": {"total_images": 0, "total_labels": 0, "classes": set()},
    }

    try:
        # 检查必要的目录结构
        images_dir = os.path.join(dataset_path, "images")
        labels_dir = os.path.join(dataset_path, "labels")

        if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
            logger.error(
                f"数据集缺少必要的images或labels目录: {images_dir} or {labels_dir}"
            )
            result["error"] = "数据集缺少必要的images或labels目录"
            return result

        # 统计图片和标签文件
        image_files = [
            f for f in os.listdir(images_dir) if f.endswith((".jpg", ".jpeg", ".png"))
        ]
        label_files = [f for f in os.listdir(labels_dir) if f.endswith(".txt")]

        result["stats"]["total_images"] = len(image_files)
        result["stats"]["total_labels"] = len(label_files)

        # 验证标签文件格式
        for label_file in label_files:
            label_path = os.path.join(labels_dir, label_file)
            with open(label_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if (
                        len(parts) != 5
                    ):  # YOLO格式: class_id x_center y_center width height
                        logger.error(f"标签文件 {label_file} 格式错误")
                        result["error"] = f"标签文件 {label_file} 格式错误"
                        return result
                    class_id = int(parts[0])
                    result["stats"]["classes"].add(class_id)

        # 检查图片和标签是否一一对应
        image_names = {os.path.splitext(f)[0] for f in image_files}
        label_names = {os.path.splitext(f)[0] for f in label_files}

        if image_names != label_names:
            logger.error(f"图片和标签文件不匹配: {image_names} != {label_names}")
            result["error"] = "图片和标签文件不匹配"
            return result

        # 验证通过
        result["is_valid"] = True
        result["stats"]["classes"] = list(result["stats"]["classes"])

    except Exception as e:
        result["error"] = f"验证过程中出错: {str(e)}"

    return result


def create_data_yaml(dataset_path, classes):
    """
    创建YOLO验证所需的data.yaml文件

    Args:
        dataset_path: 数据集路径
        classes: 类别列表

    Returns:
        str: yaml文件路径
    """
    yaml_path = os.path.join(dataset_path, "data.yaml")
    data = {
        "path": dataset_path,
        "train": "train/images",  # 训练集路径（相对路径）
        "val": "val/images",  # 验证集路径（相对路径）
        "names": {i: f"class_{i}" for i in sorted(classes)},  # 类别名称
        "nc": len(classes),  # 类别数量
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

    return yaml_path


def validate_with_model(model_path, task_dir):
    """
    使用YOLO模型的val模式验证数据集

    Args:
        model_path: YOLO模型路径
        task_dir: 任务目录路径

    Returns:
        dict: 模型验证结果
    """
    result = {
        "model_stats": {
            "metrics": {},
            "validation_time": 0.0,
        }
    }

    try:
        # 加载YOLO模型
        model = YOLO(model_path)

        # 记录开始时间
        start_time = time.time()

        # 运行验证
        metrics = model.val(
            data=os.path.join(task_dir, "data.yaml"),
            conf=0.5,
            iou=0.5,
            verbose=False,
            save=False,
            save_json=True,
            save_hybrid=True,
            plots=True,
            project=task_dir,
            name="val_results",
        )

        # 计算验证时间
        validation_time = time.time() - start_time

        # 保存验证结果
        result["model_stats"]["metrics"] = {
            "mAP50": float(metrics.box.map50),
            "mAP50-95": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "f1": float(
                metrics.box.map50
                * 2
                * metrics.box.mp
                * metrics.box.mr
                / (metrics.box.mp + metrics.box.mr)
            )
            if (metrics.box.mp + metrics.box.mr) > 0
            else 0.0,
            "speed": float(metrics.speed["inference"]),
        }
        result["model_stats"]["validation_time"] = validation_time

    except Exception as e:
        logger.error(f"模型验证过程中出错: {str(e)}")
        raise

    return result
