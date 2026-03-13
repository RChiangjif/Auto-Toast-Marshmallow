# 🔥 Auto-Toast Marshmallow

這是一個由 YTP 少年圖靈計畫培育製作的專案

自動烤棉花糖機器 - 使用 Raspberry Pi 5、舵機控制、YOLO 物體檢測和視覺熟度判定

## 🎯 專案概述

這是一個全自動烤棉花糖機器，集成了：
- **360° 旋轉舵機** - 在火源上持續旋轉棉花糖
- **180° 擺動舵機** - 熟度達標時自動收回
- **Picamera2** - 實時視頻捕捉
- **YOLO 物體檢測** - 偵測棉花糖位置
- **色彩分析** - 判定熟度等級
- **Web 介面** - 實時監控和控制

## 🏗️ 專案結構

```
marshmallow/
├── app.py                    # 主程式入口
├── toasting_controller.py    # 主控制邏輯
├── servo.py                  # 舵機控制 (PCA9685)
│
├── core/                     # 核心系統
│   ├── config.py            # 集中配置常數
│   └── state_manager.py     # 線程安全狀態管理
│
├── hardware/                 # 硬體控制模組
│   ├── servo_controller.py  # 舵機控制封裝
│   └── camera_controller.py # 相機控制封裝
│
├── vision/                   # 視覺處理（YOLO 整合）
│   ├── toast_detector.py    # YOLO + 熟度判定
│   └── image_processor.py   # 圖像處理工具
│
└── web/                      # Web 介面
    ├── routes.py            # Flask 路由
    ├── stream_manager.py    # 視頻串流管理
    └── templates.py         # HTML 模板
```

## 🚀 快速開始

### 環境要求

- Raspberry Pi 5（含 Picamera2）
- Python 3.9+
- PCA9685 舵機控制板
- YOLO NCNN 模型文件

### 1. 設定虛擬環境

```bash
cd ~/Desktop/marshmallow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 模型文件

將 YOLO NCNN 模型文件放在專案根目錄或 `model_ncnn_model/` 資料夾：

```
model.ncnn.param
model.ncnn.bin
```

或指定自訂路徑：

```bash
export YOLO_MODEL_PATH=/path/to/model.ncnn.param
```

### 3. 啟動應用

```bash
python app.py
```

開啟瀏覽器訪問：
- `http://localhost:8080` （本地）
- `http://<your-pi-ip>:8080` （網路）

## ⚙️ 配置調整

所有配置集中在 `core/config.py`：

```python
# 烤製參數
DONE_THRESHOLD     = 0.80    # 熟度判定閾值
DONE_STREAK        = 3       # 連續判定次數
BASE_SPEED         = 30      # 基礎旋轉速度
MAX_SPEED          = 100     # 最大旋轉速度

# YOLO 參數
YOLO_CONFIDENCE    = 0.1     # 檢測置信度
USE_YOLO_ROI       = True    # 使用 ROI 分析

# 相機參數
CAMERA_SIZE        = (1280, 720)
CHECK_INTERVAL     = 0.40    # 分析間隔（秒）
```

## 🔄 執行流程

1. **起動階段** - 初始化相機和 YOLO 模型
2. **定位階段** - 180° 舵機擺至火源位置
3. **校準階段** - 拍攝參考照片
4. **烤製階段** - 360° 舵機旋轉，實時監控熟度
5. **完成階段** - 自動收回舵機

## 📊 Web 介面功能

- **實時視頻** - 三種視圖：原始、處理後、YOLO 檢測框
- **熟度指示環** - 視覺化顯示烤製進度
- **控制面板** - 開始/停止按鈕
- **統計資訊** - YOLO 成功率、ROI 使用率
- **系統日誌** - 實時日誌輸出

## 🐛 常見問題

### 相機繁忙錯誤

```bash
pkill -f 'rpicam|libcamera|app.py'
sleep 1
rpicam-hello --list-cameras
python app.py
```

### YOLO 模型載入失敗

確認模型文件存在且路徑正確：

```bash
ls -la model.ncnn.param model.ncnn.bin
```

### 舵機無反應

檢查 I2C 連接和 PCA9685 地址：

```bash
i2cdetect -y 1
```

## 📝 許可證

MIT License
- If model fails to load, the stream still runs and status is shown on screen.
