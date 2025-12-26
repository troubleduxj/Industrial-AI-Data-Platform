

<h1 align="center">DeviceMonitorV2</h1>

[English](./README-en.md) | 简体中文

一个基于 FastAPI + Vue3 的现代化设备监控管理系统，集成了PostgreSQL和TDengine双数据库架构，提供实时设备监控、数据分析和智能告警功能。

## ✨ 特性

### 核心功能
- 🚀 **现代化技术栈**: FastAPI + Vue3 + TypeScript + Naive UI + UnoCSS
- 🔄 **跨端开发**: Web + Mobile (NativeScript) 共享核心业务逻辑
- 📦 **Shared 层架构**: 3,500+ 行跨端复用代码，类型安全保障
- 📊 **实时监控**: 设备状态实时监控和数据可视化（基于ECharts）
- 🗄️ **双数据库架构**: PostgreSQL（业务数据） + TDengine（时序数据）
- 🔐 **权限管理**: 基于 RBAC 的用户权限管理系统
- 📱 **响应式设计**: 支持桌面端和移动端访问
- 🌐 **国际化**: 支持多语言切换（Vue-i18n）
- 🎨 **主题切换**: 支持明暗主题切换
- 📈 **数据分析**: 设备数据统计和趋势分析
- 🔔 **告警系统**: 智能告警和通知推送
- ⚡ **高性能**: Redis缓存 + 异步处理 + 连接池优化
- 🧪 **完整测试**: 单元测试 + E2E测试 + API测试框架
- 💎 **类型安全**: 100% TypeScript 类型覆盖，编译时错误检测

### 🆕 AI智能监测 (NEW!)
- 🤖 **趋势预测**: 基于ARIMA/MA/ES/LR等算法的设备状态趋势预测
- 🔍 **异常检测**: 自动检测设备运行异常，支持多种检测算法
- 💯 **健康评分**: 设备健康度智能评估和风险预警
- 📊 **特征提取**: 自动提取设备运行特征，支持多维度分析
- 🎯 **批量预测**: 一键为多个设备批量创建预测任务
- 📜 **历史查询**: 高性能JSONB索引，快速查询预测历史（查询性能提升99.7%）
- 📈 **可视化分析**: 丰富的图表展示和趋势分析

### 🆕 元数据管理 (NEW!)
- 🧩 **统一配置管理**: 整合设备模型、字段定义、映射配置于一体的统一工作台
- 🔄 **双向同步引擎**: 自动比对并同步 PostgreSQL 元数据与 TDengine 超级表结构
- ⚡ **工作流集成**: 将元数据模型封装为标准原子节点，实现"采集-分析-告警"全链路自动化
- 🛠️ **版本控制**: 模型配置的版本化管理与历史回溯
- 📋 **简化菜单**: 优化侧边栏结构，提供更清晰的操作路径

## 🖥️ 系统界面

### 登录页
- 现代化的登录界面设计
- 用户名/密码认证（JWT Token）
- 记住登录状态功能
- 响应式设计适配各种设备

**注意**：登录页的加载图标已更新为科技主题，具体效果请运行项目后查看。

### 工作台
- 系统概览和关键指标展示
- 实时设备状态监控面板
- 快速操作入口和导航
- 个性化仪表板配置
- 数据可视化图表（ECharts集成）



## 🚀 快速开始

### ⚡ 开发环境一键启动 (推荐)

直接运行项目根目录下的启动脚本：

```bash
# Windows
start_dev.bat
```

脚本会自动检测虚拟环境、启动后端API、Celery任务队列和前端开发服务器。

### 📦 离线部署（推荐）

**使用离线打包工具，支持版本管理和多环境部署！**

```bash
# 1. 创建离线部署包
scripts\deployment\离线打包.bat

# 2. 管理历史版本
scripts\deployment\管理打包版本.bat
```

**特性**：
- ✅ 自动版本号管理（Git 标签）
- ✅ 时间戳标识
- ✅ 多版本并存
- ✅ 一键打包部署

📖 [查看离线打包说明 →](scripts/deployment/README-离线打包.md)  
📖 [查看快速开始指南 →](scripts/deployment/快速开始.md)  
📖 [查看版本号管理 →](scripts/deployment/版本号管理指南.md)

**当前版本**: v0.1.0 (开发阶段)

---

### 🆕 AI预测管理功能

**AI智能监测功能已集成，支持趋势预测和异常检测！**

📖 [查看快速开始指南 →](docs/device-data-model/阶段1核心完善-快速开始指南.md)  
📊 [查看实施总结 →](docs/device-data-model/阶段1核心完善-实施总结.md)

**主要功能**:
1. ✅ 趋势预测（ARIMA/MA/ES/LR）
2. ✅ 异常检测
3. ✅ 健康评分
4. ✅ 批量预测
5. ✅ 独立训练系统 (支持断点续训与实时进度)

---

### 🛠️ 手动启动开发环境

如果您需要手动控制各个服务，请按以下步骤操作：

**1. 启动后端 API**
```bash
# 激活虚拟环境 (可选)
# .venv\Scripts\activate

# 启动 FastAPI 服务
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

**2. 启动 AI 任务队列**
```bash
# Windows 下推荐使用 solo 模式以避免 asyncio 冲突
# 注意：必须启动此服务，AI 训练任务（进度条、日志）才能正常运行
celery -A app.celery_app worker --loglevel=info -P solo -Q celery,ai_training,ai_evaluation
```

**3. 启动前端**
```bash
cd web
npm run dev
```

### 开发环境要求

- **Python**: 3.11.9
- **Node.js**: 18+
- **PostgreSQL**: 15+
- **TDengine**: 3.0.4.0+
- **Redis**: 7+
- **包管理器**: pnpm 10.17.1+

### 项目类型

本项目采用 **pnpm workspace (monorepo)** 架构：
- 📦 **web/** - Web 前端应用
- 📱 **mobile/** - NativeScript 移动端应用
- 🔄 **packages/shared/** - 跨端共享代码

### 数据库配置

#### PostgreSQL 配置
```bash
# 数据库信息
地址: 127.0.0.1:5432
数据库: devicemonitor
用户名: postgres
密码: Hanatech@123
```

#### TDengine 配置
```bash
# 时序数据库信息
地址: 127.0.0.1:6041
数据库: devicemonitor
用户名: root
密码: taosdata
```

### 后端启动

1. **创建虚拟环境**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
# 初始化Tortoise ORM
aerych init -t app.settings.config.TORTOISE_ORM
aerych init-db
```

4. **启动后端服务**
```bash
python run.py
# 服务运行在: http://localhost:8001
```

### 前端启动

1. **进入前端目录**
```bash
cd web
```

2. **安装依赖**
```bash
pnpm install
# 或者 npm install
```

3. **启动开发服务器**
```bash
pnpm dev
# 服务运行在: http://localhost:3000
```

### 🔧 开发模式启动

#### 方式 1：使用启动脚本（推荐）

```bash
# 启动开发环境（前后端）
scripts\startup\start_dev.bat

# 停止所有服务
scripts\startup\stop_dev.bat

# 仅启动后端
scripts\startup\start_backend.bat

# 仅启动前端
scripts\startup\start_frontend_only.bat
```

#### 方式 2：手动启动

**终端1 - 后端服务：**
```bash
# 激活虚拟环境
.venv\Scripts\activate
# 启动后端
python run.py
```

# 终端3 - AI任务队列：
```bash
# 激活虚拟环境
.venv\Scripts\activate
# 启动 Celery 任务队列
# 注意：必须启动此服务，AI 训练任务（进度条、日志）才能正常运行
celery -A app.celery_app worker --loglevel=info -P solo -Q celery,ai_training,ai_evaluation
```

**终端2 - 前端服务：**
```bash
# 进入前端目录
cd web
# 启动前端
pnpm dev
```

📖 [查看更多启动脚本 →](scripts/startup/)


## 🌐 API架构与配置

### API版本管理

项目采用现代化的API版本管理策略：

- **API v2（推荐）**: `/api/v2` - 现代化架构，标准化响应格式
- **API v1（已废弃）**: `/api/v1` - 仅保留兼容性支持

**重要更新**：前端已全面升级至v2 API架构，享受以下优势：
- ✅ 标准化响应格式
- ✅ 增强的错误处理
- ✅ 更好的类型安全
- ✅ 统一的配置管理

### 环境配置

#### 生产环境配置
```bash
# web/.env.production
VITE_BASE_API = '/api/v2'  # 使用v2 API
VITE_USE_PROXY = true
```

#### 开发环境配置
```bash
# web/.env.development  
VITE_BASE_API = '/api/v2'  # 统一使用v2 API
VITE_USE_PROXY = true
```

### 跨域处理

项目已配置完整的 CORS 中间件和开发代理：

- **后端CORS**: FastAPI CORS中间件配置
- **前端代理**: Vite开发服务器代理配置
- **API路径**: `/api/v2` 自动代理到后端
- **WebSocket**: 支持WebSocket连接代理

### 服务配置

- **前端服务**: http://localhost:3000
- **后端服务**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **代理配置**: 通过 `vite.config.js` 和 `build/constant.js` 配置代理
- **后端中间件**: `init_app.py` 中包含必要的中间件
  - BackGroundTaskMiddleware
  - HttpAuditLogMiddleware
  - CORS中间件

## 📁 项目结构

```
DeviceMonitorV2/
├── 📁 app/                     # 🐍 后端应用（FastAPI）
│   ├── 📁 api/                # API路由模块
│   │   ├── 📁 v1/            # API v1版本
│   │   └── 📁 v2/            # API v2版本
│   ├── 📁 core/               # 核心功能模块
│   │   ├── auth.py           # 认证授权
│   │   ├── security.py       # 安全相关
│   │   └── middleware.py     # 中间件
│   ├── 📁 models/             # 数据模型（Tortoise ORM）
│   │   ├── admin.py          # 管理员模型
│   │   ├── device.py         # 设备模型
│   │   ├── system.py         # 系统模型
│   │   └── ai_monitoring.py  # AI监控模型
│   ├── 📁 schemas/            # Pydantic数据模式
│   ├── 📁 services/           # 业务逻辑服务
│   ├── 📁 settings/           # 配置管理
│   │   └── config.py         # 主配置文件
│   └── 📁 utils/              # 工具函数
├── 📁 packages/                # 🔄 跨端共享层
│   └── 📁 shared/            # Shared 层（Web + Mobile 复用）
│       ├── 📁 types/         # TypeScript 类型定义
│       ├── 📁 utils/         # 跨端工具函数
│       ├── 📁 api/           # HTTP 客户端和 API
│       └── README.md         # Shared 层文档
├── 📁 web/                     # 🌐 前端应用（Vue3）
│   ├── 📁 src/               # 源代码
│   │   ├── 📁 components/    # Vue组件
│   │   ├── 📁 views/         # 页面视图
│   │   ├── 📁 router/        # Vue Router路由
│   │   ├── 📁 store/         # Pinia状态管理（TypeScript）
│   │   ├── 📁 utils/         # 前端工具函数
│   │   ├── 📁 api/           # API 适配器（使用 Shared API）
│   │   ├── 📁 types/         # 类型适配层
│   │   └── 📁 assets/        # 静态资源
│   ├── 📁 public/            # 公共静态资源
│   ├── 📁 build/             # 构建配置
│   ├── 📁 i18n/              # 国际化配置
│   └── 📁 docs/              # 前端文档
├── 📁 mobile/                  # 📱 移动端应用（NativeScript + Vue3）
│   ├── 📁 app/               # 应用源代码
│   │   ├── 📁 pages/         # 页面组件
│   │   ├── 📁 components/    # 通用组件
│   │   ├── 📁 stores/        # Pinia状态管理
│   │   ├── 📁 services/      # 服务层（使用 Shared API）
│   │   └── app.ts            # 应用入口
│   ├── App_Resources/        # 原生资源
│   ├── package.json          # 依赖配置
│   └── nativescript.config.ts # NativeScript 配置
├── 📁 database/                # 🗄️ 数据库相关
│   ├── 📁 init-scripts/      # 数据库初始化脚本
│   ├── 📁 migrations/        # 数据库迁移文件
│   ├── 📁 archived/          # 归档文件（历史参考）
│   ├── config.json.example   # 配置模板
│   ├── validation_rules.json # 验证规则
│   └── README.md             # 数据库文档
├── 📁 docs/                    # 📚 项目文档
│   ├── 📁 device-data-model/ # 设备数据模型文档
│   ├── 📁 device_test/       # 设备测试文档
│   ├── 📁 archived/          # 归档文档
│   ├── api_documentation.md  # API文档
│   ├── deployment_guide.md   # 部署指南
│   ├── development_guide.md  # 开发指南
│   ├── Web端Shared层迁移进度.md  # Shared 层迁移进度
│   └── Shared层迁移最终总结-2025-10-28.md # 迁移总结
├── 📁 scripts/                 # 🛠️ 脚本工具
│   ├── 📁 startup/           # 启动脚本
│   ├── 📁 deployment/        # 部署工具
│   ├── 📁 database/          # 数据库脚本
│   ├── 📁 testing/           # 测试脚本
│   ├── 📁 mock/              # Mock 数据管理
│   └── README.md             # 脚本文档
├── 📁 test/                    # 🧪 测试框架
│   ├── 📁 scripts/           # 测试脚本
│   │   ├── 📁 utils/         # 测试工具类
│   │   └── 📁 users/         # 用户模块测试
│   ├── 📁 report/            # 测试报告
│   └── 📁 logs/              # 测试日志
├── 📄 requirements.txt         # Python依赖
├── 📄 .env.dev                # 开发环境配置
├── 📄 .env.prod               # 生产环境配置
├── 📄 pyproject.toml          # Python项目配置
└── 📄 run.py                  # 应用启动入口
```

## 🛠️ 技术栈详情

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 0.111.0 | Web框架，提供高性能异步API |
| **Python** | 3.8+ | 主要开发语言 |
| **Tortoise ORM** | - | 异步ORM，支持多数据库 |
| **PostgreSQL** | 12+ | 主数据库，存储业务数据 |
| **TDengine** | 3.0+ | 时序数据库，存储设备监控数据 |
| **Redis** | 6.0+ | 缓存和会话存储 |
| **Pydantic** | 2.10.5 | 数据验证和序列化 |
| **JWT** | 2.10.1 | 身份认证和授权 |
| **Aerich** | 0.8.1 | 数据库迁移工具 |
| **Loguru** | 0.7.3 | 日志管理 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue 3** | 3.3.4 | 前端框架，组合式API |
| **TypeScript** | 5.1.6 | 类型安全的JavaScript |
| **Vite** | - | 构建工具和开发服务器 |
| **Naive UI** | 2.34.4 | UI组件库 |
| **UnoCSS** | 0.58.0 | 原子化CSS框架 |
| **Pinia** | 2.1.6 | 状态管理 |
| **Vue Router** | 4.2.4 | 路由管理 |
| **Vue I18n** | 9 | 国际化支持 |
| **ECharts** | 5.6.0 | 数据可视化图表 |
| **Axios** | 1.4.0 | HTTP客户端 |
| **Day.js** | 1.11.9 | 日期时间处理 |

### 开发工具

| 工具 | 用途 |
|------|------|
| **ESLint** | 代码质量检查 |
| **Prettier** | 代码格式化 |
| **Vitest** | 单元测试框架 |
| **Playwright** | E2E测试框架 |
| **pnpm** | 包管理器（推荐） |

## 🔄 跨端开发架构

### Shared 层 (packages/shared)

本项目采用 **Shared 层架构**，实现 Web 端和 Mobile 端的代码复用。

#### 核心优势

- ✅ **代码复用率 85%+**：类型、工具、API 完全共享
- ✅ **类型安全 100%**：TypeScript 编译时错误检测
- ✅ **统一业务逻辑**：一次编写，双端受益
- ✅ **降低维护成本**：修复一处，全端生效

#### Shared 层结构

```
packages/shared/
├── types/         # 跨端类型定义（50+ 个接口）
│   ├── common.ts  # 通用类型
│   ├── user.ts    # 用户类型
│   ├── device.ts  # 设备类型
│   └── alarm.ts   # 告警类型
├── utils/         # 跨端工具函数（30+ 个）
│   ├── validators.ts  # 类型检查与验证
│   ├── datetime.ts    # 日期时间处理
│   ├── format.ts      # 数据格式化
│   └── helpers.ts     # 防抖、节流等
└── api/           # 跨端 API 客户端
    ├── client.ts  # HTTP 客户端基类
    ├── auth.ts    # 认证 API
    ├── device.ts  # 设备 API
    └── alarm.ts   # 告警 API
```

#### 使用示例

**Web 端**:
```typescript
// 使用 Shared 层类型
import type { User, Device } from '@/types/shared'

// 使用 Shared 层工具
import { formatDate, isEmpty } from '@/utils'

// 使用 Shared 层 API
import { deviceApi } from '@/api/device-shared'

const devices = await deviceApi.getList({ page: 1, pageSize: 20 })
```

**Mobile 端**:
```typescript
// 同样的导入方式
import type { User, Device } from '@shared/types'
import { formatDate, isEmpty } from '@shared/utils'
import { deviceApi } from '@shared/api'

// 完全相同的 API 调用
const devices = await deviceApi.getList({ page: 1, pageSize: 20 })
```

#### 迁移进度

- ✅ **基础设施**: 100%
- ✅ **工具函数**: 100%  
- ✅ **类型定义**: 100%
- ✅ **API 客户端**: 100%
- ✅ **Pinia Store**: 100% (Web 端)
- ✅ **组件迁移**: 40%

📊 **总体进度**: 95% | 📝 [查看详细进度 →](docs/Web端Shared层迁移进度.md)

---

## 📚 API文档

### 在线文档

启动后端服务后，可以访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### API版本

- **v1**: `/api/v1/*` - 向后兼容的API接口
- **v2**: `/api/v2/*` - 最新版本API接口（推荐使用）

### 主要API模块

- **认证模块**: `/api/v2/auth/*` - 用户登录、注册、JWT管理
- **用户管理**: `/api/v2/users/*` - 用户CRUD操作
- **设备管理**: `/api/v2/devices/*` - 设备监控和管理
- **系统管理**: `/api/v2/system/*` - 系统配置和监控
- **AI监控**: `/api/v2/ai-monitoring/*` - AI相关功能

## 🧪 测试框架

项目包含完整的测试框架，支持多种测试类型：

### 测试类型

1. **单元测试** - Vitest（前端）+ pytest（后端）
2. **E2E测试** - Playwright
3. **API测试** - 自定义测试框架

### 运行测试

```bash
# 前端测试
cd web
pnpm test          # 运行单元测试
pnpm test:e2e       # 运行E2E测试
pnpm test:coverage  # 生成覆盖率报告

# 后端API测试
cd test/scripts/users
python test_users_v2.py      # 完整用户模块测试
python quick_test_users_v2.py # 快速测试
```

### 测试报告

测试报告和日志文件位于：
- **测试报告**: `test/report/`
- **测试日志**: `test/logs/`

## �  项目管理工具

### Scripts 工具集

项目提供了完整的脚本工具集，涵盖开发、测试、部署等各个环节：

#### 启动脚本 (scripts/startup/)
```bash
start_dev.bat              # 启动开发环境
stop_dev.bat               # 停止所有服务
start_backend.bat          # 仅启动后端
start_frontend_only.bat    # 仅启动前端
```

#### 部署工具 (scripts/deployment/)
```bash
离线打包.bat               # 创建离线部署包
管理打包版本.bat           # 版本管理工具
```

**特性**：
- ✅ 版本号自动管理（Git 标签）
- ✅ 时间戳标识（YYYYMMDD_HHMMSS）
- ✅ 多版本并存
- ✅ 历史版本管理

**打包输出**：
```
releases/
├── offline_deploy_0.1.0_20251118_143052/
├── offline_deploy_0.1.1_20251118_150230/
└── offline_deploy_0.2.0_20251119_091500/
```

#### 数据库工具 (scripts/database/)
```bash
检查数据库连接.bat         # 检查数据库状态
启动PostgreSQL服务.bat     # 启动数据库服务
一键修复数据库连接.bat     # 修复连接问题
```

#### 测试工具 (scripts/testing/)
```bash
full_test.bat              # 运行完整测试
test_*.py                  # 各模块测试脚本
```

📖 [查看完整脚本文档 →](scripts/README.md)

---

## 🚀 部署指南

### 离线部署（推荐）

使用离线打包工具进行部署：

```bash
# 1. 创建部署包
scripts\deployment\离线打包.bat

# 2. 传输到目标服务器
# 将 releases/offline_deploy_x.x.x_xxxxxxxx_xxxxxx/ 目录复制到服务器

# 3. 在目标服务器运行
完整部署.bat
```

📖 [查看离线打包详细说明 →](scripts/deployment/README-离线打包.md)

### 手动部署

#### 生产环境配置

1. **环境变量配置**
```bash
# 复制生产环境配置
cp .env.prod .env
# 修改配置文件中的数据库连接等信息
```

2. **数据库初始化**
```bash
# PostgreSQL数据库初始化
aerych init -t app.settings.config.TORTOISE_ORM
aerych init-db

# TDengine数据库初始化
# 需要手动创建数据库和表结构
```

3. **前端构建**
```bash
cd web
pnpm build
# 构建产物在 web/dist/ 目录
```

4. **后端部署**
```bash
# 使用 gunicorn 部署
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker run:app
```

## 🔧 开发指南

### 代码规范

- **Python**: 遵循 PEP 8 规范
- **JavaScript/TypeScript**: 使用 ESLint + Prettier
- **Vue**: 遵循 Vue 3 组合式API最佳实践
- **Git**: 使用约定式提交（Conventional Commits）

### 开发流程

1. **创建功能分支**
```bash
git checkout -b feature/your-feature-name
```

2. **开发和测试**
```bash
# 运行开发服务器
# 后端
python run.py
# 前端
cd web && pnpm dev

# 运行测试
pnpm test
```

3. **提交代码**
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 环境切换

项目支持多环境配置：

- **开发环境**: `.env.dev`
- **生产环境**: `.env.prod`

通过修改 `app/settings/config.py` 中的 `DEFAULT_ENV` 变量来切换环境。

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 提交规范

使用约定式提交格式：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## � 版本信息

**当前版本**: v0.1.0 (开发阶段)  
**最后更新**: 2025-12-23

### 版本管理

项目使用 Git 标签进行版本管理，遵循语义化版本规范：

- **v0.x.x** - 开发阶段
- **v1.x.x** - 正式版本
- **v2.x.x** - 重大更新

📖 [查看版本号管理指南 →](scripts/deployment/版本号管理指南.md)

### 最近更新 (v0.1.0)

#### 🎯 项目结构优化
- ✅ 清理 database 目录（100+ → 8 个核心文件）
- ✅ 移除 deploy 目录（已过时）
- ✅ 移除 Docker 配置（使用离线打包）
- ✅ 保留 monorepo 结构（web + mobile + shared）

#### 📦 部署工具完善
- ✅ 离线打包工具（支持版本号和时间戳）
- ✅ 版本管理工具（列表/删除/清理/压缩）
- ✅ 自动化脚本集合
- ✅ 完整的文档体系

#### 🗄️ 数据库优化
- ✅ 归档历史文件（80+ 个）
- ✅ 保留核心文件（8 个）
- ✅ 清晰的目录结构
- ✅ 完善的初始化脚本

#### 📚 文档完善
- ✅ 更新主 README
- ✅ 新增部署文档
- ✅ 新增版本管理文档
- ✅ 新增快速开始指南

📖 [查看完整更新日志 →](CHANGELOG.md)

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/troubleduxj/DeviceMonitorV2/issues)
- 发起 [Discussion](https://github.com/troubleduxj/DeviceMonitorV2/discussions)
- 查看 [Wiki](https://github.com/troubleduxj/DeviceMonitorV2/wiki)

## �️ 相关文档

### 核心文档
- [快速开始](scripts/deployment/快速开始.md)
- [离线打包说明](scripts/deployment/README-离线打包.md)
- [版本号管理](scripts/deployment/版本号管理指南.md)
- [数据库文档](database/README.md)
- [Scripts 工具集](scripts/README.md)

### 开发文档
- [开发指南](docs/development_guide.md)
- [API 文档](docs/api_documentation.md)
- [Shared 层迁移](docs/Web端Shared层迁移进度.md)
- [设备测试指南](docs/device_test/新增设备类型与AI检测实现指南.md)

### 部署文档
- [部署指南](docs/deployment_guide.md)
- [离线部署](scripts/deployment/README-离线打包.md)
- [版本管理](scripts/deployment/版本管理说明.md)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和开源社区。

特别感谢：
- FastAPI 团队提供的优秀 Web 框架
- Vue.js 团队提供的前端框架
- NativeScript 团队提供的跨平台解决方案
- 所有开源组件的维护者

## 📊 项目统计

- **代码行数**: 50,000+ 行
- **提交次数**: 500+ 次
- **开发周期**: 6+ 个月
- **团队规模**: 1-5 人
- **技术栈**: 20+ 种技术

---

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

**🚀 DeviceMonitorV2 - 现代化设备监控管理系统**


