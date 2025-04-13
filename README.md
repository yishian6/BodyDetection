# README

第十六届中国大学生服务外包创新创业大赛：T2405446-火眼晶晶-A25浓烟环境人体目标判别-基于浓烟环境人体目标识别系统源码

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Server as Flask服务器
    participant TaskManager as 任务管理器
    participant Worker as 后台工作线程
    participant YOLO as YOLO模型

    Client->>+Server: POST /detect/videos {video_id}
    Server->>Server: 检查视频是否存在
    Server->>TaskManager: 创建任务 (create_task)
    Server->>Worker: 启动后台处理线程
    Server-->>-Client: 返回 task_id

    loop 任务状态轮询
        Client->>+Server: GET /task/status/{task_id}
        Server->>TaskManager: 获取任务状态
        Server-->>-Client: 返回当前状态和进度
    end

    Worker->>TaskManager: 更新状态为处理中
    Worker->>YOLO: 执行视频检测
    YOLO-->>Worker: 返回检测结果
    Worker->>TaskManager: 更新任务完成状态和结果

    Client->>+Server: GET /task/result/{task_id}
    Server->>TaskManager: 获取任务结果
    Server-->>-Client: 返回处理结果
```

## 测试数据集：test_data

本测试数据集包含以下五个部分，分别对应不同的处理和识别任务：

1. **dehaze**  
   图像去烟处理

2. **image_identify**  
   图像识别

3. **video_identify**  
   视频识别

4. **fusion**  
   融合识别（太大了，放不上去）

5. **val**  
   识别性能评估
