<h1 align="center">Industrial AI Data Platform</h1>

[English](./README-en.md) | 简体中文

新一代工业AI数据平台，基于元数据驱动架构，集成了 **资产语义层**、**时序数据处理**、**工业AI引擎** 和 **实时监控** 功能。平台旨在解决工业数据孤岛问题，提供从数据采集、特征工程到模型训练、推理决策的全链路解决方案。

## ✨ 核心特性 (V3/V4)

### 🏭 平台核心 (Platform Core)
- **元数据驱动**: 基于 `Asset` (资产) 和 `Signal` (信号) 的通用抽象，支持任意设备接入。
- **动态 Schema**: 根据信号定义自动管理 TDengine 超级表结构，无需手动维护。
- **实时数据流**: 高性能 WebSocket 推送服务，支持大规模并发订阅。
- **数据采集**: 集成 MQTT/HTTP 多协议适配器，支持数据验证与清洗。

### 🧠 AI 引擎 (AI Engine)
- **Model Registry**: 完整的模型生命周期管理（注册、版本控制、部署、归档）。
- **Feature Store**: 工业特征工程，支持流式特征计算与存储。
- **Decision Engine**: 基于规则的决策运行时，支持复杂报警逻辑。
- **Inference Service**: 统一推理接口，支持多种算法框架 (Sklearn, PyTorch, etc.)。

### 🌐 现代化前端
- **统一 API (v4)**: 基于 RESTful 标准的 v4 API，提供一致的开发体验。
- **实时监控**: 基于 WebSocket 的实时数据可视化与告警通知。
- **资产管理**: 灵活的资产树与信号配置界面。
- **遗留兼容**: 平滑过渡旧版 DeviceMonitor 功能，保障业务连续性。

## 🚀 快速开始

### ⚡ 开发环境一键启动 (推荐)

直接运行项目根目录下的启动脚本：

```bash
# Windows
start_dev.bat
```

脚本会自动检测虚拟环境、启动后端API、Celery任务队列和前端开发服务器。

### 📦 离线部署

使用离线打包工具，支持版本管理和多环境部署：

```bash
# 1. 创建离线部署包
scripts\deployment\离线打包.bat

# 2. 管理历史版本
scripts\deployment\管理打包版本.bat
```

## 🛠️ 手动启动

如果您需要手动控制各个服务：

**1. 启动后端 API**
```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

**2. 启动 AI 任务队列**
```bash
celery -A app.celery_app worker --loglevel=info -P solo -Q celery,ai_training,ai_evaluation
```

**3. 启动前端**
```bash
cd web
pnpm dev
```

## 🌐 API 架构

平台采用多版本 API 共存策略，平滑演进：

- **API v4 (当前)**: `/api/v4` - 基于资产语义的新一代 API，推荐使用。
- **API v3 (过渡)**: `/api/v3` - V3 升级期间的过渡接口。
- **API v2 (遗留)**: `/api/v2` - 兼容旧版 DeviceMonitor 功能。

## 📁 项目结构

```
Industrial-AI-Data-Platform/
├── 📁 ai_engine/               # 🤖 AI引擎 (核心)
│   ├── 📁 model/               # 模型管理 (Registry + Storage)
│   ├── 📁 feature/             # 特征工程
│   ├── 📁 decision/            # 决策引擎
│   └── 📁 inference/           # 推理服务
├── 📁 platform_core/           # 🏭 平台核心 (核心)
│   ├── 📁 asset/               # 资产管理
│   ├── 📁 signal/              # 信号定义
│   ├── 📁 metadata/            # 元数据管理
│   ├── 📁 timeseries/          # 时序数据处理
│   └── 📁 ingestion/           # 数据采集
├── 📁 app/                     # 🐍 后端应用 (FastAPI)
│   ├── 📁 api/                 # API 路由 (v1/v2/v3/v4)
│   └── ...
├── 📁 web/                     # 🌐 前端应用 (Vue3)
│   ├── 📁 src/api/v4/          # v4 API 客户端
│   ├── 📁 src/views/assets/    # 新版资产管理页面
│   └── ...
└── ...
```

## 📚 文档

详细设计文档请参考 `docs/Industrial AI Data Platform/` 目录：
- `V3.MD`: V3 架构蓝图
- `V4.MD`: V4 演进方向
- `V3_UPGRADE_ANALYSIS.md`: 升级分析报告

---
**当前版本**: V3.0.0 (Release Candidate)
