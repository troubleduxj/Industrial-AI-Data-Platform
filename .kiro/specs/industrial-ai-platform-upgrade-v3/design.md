# 设计文档 - 工业AI数据平台升级 V3

## 概述

本文档描述V3升级的技术设计方案，重点解决代码整合、遗留清理和企业级能力增强。

## 架构设计

### 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端展示层 (web/)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ 资产监控    │ │ AI引擎管理  │ │ 特征工程    │ │ 系统管理   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      统一API层 (app/api/v4/)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ 资产API     │ │ AI API      │ │ 特征API     │ │ 系统API    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ platform_core │    │   ai_engine   │    │    plugins    │
│               │    │               │    │               │
│ ├─ asset/     │    │ ├─ model/     │    │ ├─ adapters/  │
│ ├─ signal/    │    │ ├─ inference/ │    │ ├─ algorithms/│
│ ├─ metadata/  │    │ ├─ feature/   │    │ ├─ notifiers/ │
│ ├─ timeseries/│    │ └─ decision/  │    │ └─ widgets/   │
│ └─ ingestion/ │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ PostgreSQL  │ │  TDengine   │ │    Redis    │ │   MinIO    │ │
│  │ (元数据)    │ │ (时序数据)  │ │ (缓存/队列) │ │ (模型文件) │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. platform_core 模块整合

#### 当前状态
```
platform_core/
├── ingestion/          # V2新增
│   ├── adapters/
│   ├── validator.py
│   └── dual_writer.py
└── realtime/           # V2新增
    ├── push_service.py
    └── websocket_server.py

platform_v2/            # 待整合
├── metadata/
├── timeseries/
└── ingestion/
```

#### 目标结构
```
platform_core/
├── asset/              # 资产管理
│   ├── __init__.py
│   ├── models.py       # Asset, AssetCategory
│   ├── service.py      # AssetService
│   └── repository.py   # AssetRepository
├── signal/             # 信号管理
│   ├── __init__.py
│   ├── models.py       # SignalDefinition
│   ├── service.py      # SignalService
│   └── repository.py   # SignalRepository
├── metadata/           # 元数据管理（从platform_v2迁移）
│   ├── __init__.py
│   ├── registry.py
│   └── schema_manager.py
├── timeseries/         # 时序数据（从platform_v2迁移）
│   ├── __init__.py
│   ├── tdengine_client.py
│   └── query_builder.py
├── ingestion/          # 数据采集（保留V2实现）
│   ├── __init__.py
│   ├── adapters/
│   ├── validator.py
│   └── dual_writer.py
└── realtime/           # 实时推送（保留V2实现）
    ├── __init__.py
    ├── push_service.py
    └── websocket_server.py
```

### 2. ai_engine 模块整合

#### 当前状态
```
ai_engine/
├── decision_engine/    # V2新增
├── feature_hub/        # V2新增
├── inference/          # V2新增
├── model_registry/     # V2新增
└── model_storage/      # V2新增
```

#### 目标结构
```
ai_engine/
├── model/              # 模型管理（整合model_registry + model_storage）
│   ├── __init__.py
│   ├── registry.py     # 模型注册
│   ├── storage.py      # 模型存储
│   ├── version.py      # 版本管理
│   └── loader.py       # 模型加载
├── inference/          # 推理服务
│   ├── __init__.py
│   ├── engine.py       # 推理引擎
│   ├── prediction_store.py
│   └── batch_inference.py
├── feature/            # 特征工程（从feature_hub重命名）
│   ├── __init__.py
│   ├── store.py        # 特征存储
│   ├── view.py         # 特征视图
│   ├── lineage.py      # 血缘追踪
│   └── stream.py       # 流计算
└── decision/           # 决策引擎（从decision_engine重命名）
    ├── __init__.py
    ├── rule_parser.py
    ├── rule_runtime.py
    ├── action_executor.py
    └── audit_logger.py
```

### 3. 统一API v4设计

#### API路由结构
```
/api/v4/
├── assets/                 # 资产管理
│   ├── GET /               # 列表
│   ├── POST /              # 创建
│   ├── GET /{id}           # 详情
│   ├── PUT /{id}           # 更新
│   ├── DELETE /{id}        # 删除
│   └── GET /{id}/signals   # 资产信号
├── categories/             # 资产类别
│   ├── GET /
│   ├── POST /
│   ├── GET /{id}
│   ├── PUT /{id}
│   └── GET /{id}/signals   # 类别信号定义
├── signals/                # 信号定义
│   ├── GET /
│   ├── POST /
│   ├── GET /{id}
│   └── PUT /{id}
├── timeseries/             # 时序数据
│   ├── GET /query          # 查询
│   ├── POST /write         # 写入
│   └── GET /latest/{asset_id}  # 最新值
├── models/                 # AI模型
│   ├── GET /
│   ├── POST /
│   ├── GET /{id}
│   ├── GET /{id}/versions
│   ├── POST /{id}/versions
│   └── POST /{id}/predict
├── features/               # 特征
│   ├── GET /views
│   ├── POST /views
│   ├── GET /views/{id}
│   └── GET /query
├── decisions/              # 决策规则
│   ├── GET /rules
│   ├── POST /rules
│   ├── GET /rules/{id}
│   ├── PUT /rules/{id}
│   ├── POST /rules/{id}/test
│   └── GET /audit
├── ingestion/              # 数据采集
│   ├── GET /sources
│   ├── POST /sources
│   ├── GET /status
│   └── POST /data
├── system/                 # 系统管理
│   ├── GET /health
│   ├── GET /metrics
│   ├── GET /config
│   └── POST /config
└── ws/                     # WebSocket
    └── /realtime           # 实时数据
```

#### 统一响应格式
```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "timestamp": "2025-12-28T10:00:00Z"
  }
}
```

### 4. 数据库Schema整合

#### 表重命名映射
| 旧表名 | 新表名 | 说明 |
|--------|--------|------|
| device_types | asset_categories | 资产类别 |
| device_fields | signal_definitions | 信号定义 |
| device_info | assets | 资产实例 |
| device_data_* | asset_data_* | 时序数据表 |
| ai_predictions | predictions | 预测结果 |

#### 迁移SQL示例
```sql
-- 重命名表
ALTER TABLE device_types RENAME TO asset_categories;
ALTER TABLE device_fields RENAME TO signal_definitions;
ALTER TABLE device_info RENAME TO assets;

-- 重命名列
ALTER TABLE asset_categories RENAME COLUMN device_type_code TO category_code;
ALTER TABLE signal_definitions RENAME COLUMN device_type_id TO category_id;
ALTER TABLE assets RENAME COLUMN device_type_id TO category_id;

-- 更新外键
ALTER TABLE signal_definitions 
  DROP CONSTRAINT fk_device_type,
  ADD CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES asset_categories(id);
```

### 5. 前端整合设计

#### 页面迁移映射
| 旧页面 | 新页面 | 处理方式 |
|--------|--------|----------|
| /device/list | /assets/list | 重构 |
| /device/monitor | /assets/monitor | 重构 |
| /device/types | /categories | 重构 |
| /ai/models | /ai-engine/models | 保留 |
| /ai/predictions | /ai-engine/predictions | 保留 |
| /ai/rules | /ai-engine/rules | 保留 |

#### 组件整合
```
web/src/
├── components/
│   ├── platform/           # 平台通用组件（保留）
│   ├── realtime/           # 实时监控组件（保留）
│   └── legacy/             # 遗留组件（归档）
├── views/
│   ├── assets/             # 资产管理（整合device相关）
│   ├── ai-engine/          # AI引擎（保留）
│   ├── feature-engine/     # 特征引擎（保留）
│   ├── system/             # 系统管理
│   └── legacy/             # 遗留页面（归档）
└── api/
    ├── v4/                 # 新版API
    └── legacy/             # 旧版API（兼容）
```

### 6. 可观测性设计

#### Prometheus指标
```python
# 业务指标
asset_count = Gauge('platform_asset_count', 'Total number of assets')
signal_count = Gauge('platform_signal_count', 'Total number of signals')
prediction_count = Counter('platform_prediction_total', 'Total predictions')
rule_trigger_count = Counter('platform_rule_trigger_total', 'Rule triggers')

# 性能指标
api_request_duration = Histogram('platform_api_duration_seconds', 'API latency')
inference_duration = Histogram('platform_inference_duration_seconds', 'Inference latency')
ingestion_rate = Gauge('platform_ingestion_rate', 'Data ingestion rate')
```

#### 健康检查端点
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "postgresql": await check_postgresql(),
            "tdengine": await check_tdengine(),
            "redis": await check_redis(),
            "minio": await check_minio()
        },
        "version": "3.0.0",
        "uptime": get_uptime()
    }
```

### 7. 多租户设计

#### 租户隔离策略
```python
class TenantMiddleware:
    """租户中间件"""
    
    async def __call__(self, request, call_next):
        # 从请求头或JWT中提取租户ID
        tenant_id = self.extract_tenant_id(request)
        
        # 设置租户上下文
        tenant_context.set(tenant_id)
        
        # 继续处理请求
        response = await call_next(request)
        
        return response

class TenantAwareRepository:
    """租户感知的数据仓库"""
    
    def get_query(self):
        tenant_id = tenant_context.get()
        return self.model.filter(tenant_id=tenant_id)
```

### 8. 插件系统设计

#### 插件接口定义
```python
from abc import ABC, abstractmethod

class AdapterPlugin(ABC):
    """数据采集适配器插件"""
    
    @abstractmethod
    def connect(self, config: dict) -> bool:
        pass
    
    @abstractmethod
    def read(self) -> dict:
        pass
    
    @abstractmethod
    def disconnect(self):
        pass

class AlgorithmPlugin(ABC):
    """AI算法插件"""
    
    @abstractmethod
    def train(self, data: pd.DataFrame, config: dict) -> Any:
        pass
    
    @abstractmethod
    def predict(self, model: Any, data: pd.DataFrame) -> pd.DataFrame:
        pass

class NotifierPlugin(ABC):
    """告警通知插件"""
    
    @abstractmethod
    def send(self, message: str, recipients: list, config: dict) -> bool:
        pass
```

#### 插件加载机制
```python
class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.adapters = {}
        self.algorithms = {}
        self.notifiers = {}
    
    def load_plugins(self, plugin_dir: str):
        """从目录加载插件"""
        for plugin_file in Path(plugin_dir).glob("*.py"):
            module = importlib.import_module(plugin_file.stem)
            self.register_plugin(module)
    
    def register_plugin(self, module):
        """注册插件"""
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, AdapterPlugin):
                self.adapters[name] = cls
            elif issubclass(cls, AlgorithmPlugin):
                self.algorithms[name] = cls
            elif issubclass(cls, NotifierPlugin):
                self.notifiers[name] = cls
```

## 实施计划

### 阶段1：代码整合（2-3周）
- 整合platform_v2到platform_core
- 重命名ai_engine子模块
- 清理重复代码

### 阶段2：数据库迁移（1-2周）
- 创建迁移脚本
- 执行表重命名
- 更新外键和索引

### 阶段3：API整合（2-3周）
- 创建v4 API
- 实现兼容层
- 更新API文档

### 阶段4：前端整合（2-3周）
- 迁移遗留页面
- 统一组件库
- 更新路由配置

### 阶段5：测试完善（1-2周）
- 补充单元测试
- 添加集成测试
- 配置CI/CD

### 阶段6：文档建设（1周）
- 更新README
- 编写架构文档
- 生成API文档

### 阶段7：可观测性（1-2周）
- 集成Prometheus
- 配置Grafana
- 添加链路追踪

### 阶段8：高级功能（2-4周）
- 多租户支持
- 插件系统
- 性能优化

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据迁移失败 | 高 | 提供回滚脚本，先在测试环境验证 |
| API兼容性问题 | 中 | 保留旧版API兼容层，逐步迁移 |
| 前端页面遗漏 | 低 | 建立页面清单，逐一验证 |
| 性能下降 | 中 | 建立性能基准，持续监控 |

