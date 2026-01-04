# 设计文档 - V3系统优化整合

## 概述

本文档描述V3系统优化整合的技术设计方案，重点解决代码整合、模块重命名、命名规范统一和API整合。基于已有的V3设计文档，本设计聚焦于实际执行层面的技术细节。

## 架构设计

### 当前状态

```
├── platform_core/          # V2新增，部分实现
│   ├── ingestion/          # 数据采集（完整）
│   └── realtime/           # 实时推送（完整）
├── platform_v2/            # 待整合
│   ├── metadata/           # 元数据服务
│   ├── timeseries/         # 时序数据服务
│   └── ingestion/          # 空目录
├── ai_engine/              # V2新增，需重命名
│   ├── decision_engine/    # → decision
│   ├── feature_hub/        # → feature
│   ├── inference/          # 保留
│   ├── model_registry/     # → model (合并)
│   └── model_storage/      # → model (合并)
└── app/
    ├── api/v1/v2/v3/       # 需整合为v4
    ├── models/             # 保留
    └── services/           # 需清理重复
```

### 目标状态

```
├── platform_core/          # 整合后的核心平台
│   ├── asset/              # 资产管理（新建）
│   ├── signal/             # 信号管理（新建）
│   ├── metadata/           # 元数据（从platform_v2迁移）
│   ├── timeseries/         # 时序数据（从platform_v2迁移）
│   ├── ingestion/          # 数据采集（保留）
│   └── realtime/           # 实时推送（保留）
├── ai_engine/              # 重命名后的AI引擎
│   ├── model/              # 模型管理（合并registry+storage）
│   ├── inference/          # 推理服务（保留）
│   ├── feature/            # 特征工程（重命名）
│   └── decision/           # 决策引擎（重命名）
└── app/
    ├── api/v4/             # 统一API
    ├── models/             # 保留
    └── services/           # 薄封装层
```

## 组件设计

### 1. platform_core/asset 模块

```python
# platform_core/asset/__init__.py
from .models import Asset, AssetCategory
from .service import AssetService
from .repository import AssetRepository

__all__ = ["Asset", "AssetCategory", "AssetService", "AssetRepository"]
```

```python
# platform_core/asset/models.py
"""
资产模型定义

从app/models/platform_upgrade.py迁移Asset和AssetCategory模型的业务逻辑封装。
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AssetDTO:
    """资产数据传输对象"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    category_id: int = 0
    category_code: str = ""
    attributes: Dict[str, Any] = None
    location: Optional[str] = None
    status: str = "offline"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AssetCategoryDTO:
    """资产类别数据传输对象"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    description: Optional[str] = None
    tdengine_database: str = ""
    tdengine_stable_prefix: str = ""
    industry: Optional[str] = None
    config: Dict[str, Any] = None
    is_active: bool = True
    asset_count: int = 0
```

```python
# platform_core/asset/repository.py
"""
资产数据访问层

提供资产和资产类别的数据库操作。
"""
from typing import Optional, List, Tuple, Dict, Any

class AssetRepository:
    """资产数据仓库"""
    
    @staticmethod
    async def get_by_id(asset_id: int) -> Optional["Asset"]:
        from app.models.platform_upgrade import Asset
        return await Asset.get_or_none(id=asset_id)
    
    @staticmethod
    async def get_by_code(code: str) -> Optional["Asset"]:
        from app.models.platform_upgrade import Asset
        return await Asset.get_or_none(code=code)
    
    @staticmethod
    async def list_assets(
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List["Asset"], int]:
        from app.models.platform_upgrade import Asset
        query = Asset.all()
        if category_id:
            query = query.filter(category_id=category_id)
        if status:
            query = query.filter(status=status)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        total = await query.count()
        offset = (page - 1) * page_size
        assets = await query.offset(offset).limit(page_size)
        return assets, total

class AssetCategoryRepository:
    """资产类别数据仓库"""
    
    @staticmethod
    async def get_by_id(category_id: int) -> Optional["AssetCategory"]:
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(id=category_id)
    
    @staticmethod
    async def get_by_code(code: str) -> Optional["AssetCategory"]:
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(code=code)
```

```python
# platform_core/asset/service.py
"""
资产业务服务层

提供资产管理的核心业务逻辑。
"""
from typing import Optional, List, Tuple, Dict, Any
from .repository import AssetRepository, AssetCategoryRepository

class AssetService:
    """资产管理服务"""
    
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.category_repo = AssetCategoryRepository()
    
    async def get_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset:
            return None
        return self._to_dict(asset)
    
    async def list_assets(
        self,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        assets, total = await self.asset_repo.list_assets(
            category_id=category_id,
            status=status,
            page=page,
            page_size=page_size
        )
        return [self._to_dict(a) for a in assets], total
    
    def _to_dict(self, asset) -> Dict[str, Any]:
        return {
            "id": asset.id,
            "code": asset.code,
            "name": asset.name,
            "category_id": asset.category_id,
            "attributes": asset.attributes,
            "location": asset.location,
            "status": asset.status,
            "is_active": asset.is_active
        }
```

### 2. platform_core/signal 模块

```python
# platform_core/signal/__init__.py
from .models import SignalDefinitionDTO
from .service import SignalService
from .repository import SignalRepository

__all__ = ["SignalDefinitionDTO", "SignalService", "SignalRepository"]
```

```python
# platform_core/signal/models.py
"""信号模型定义"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SignalDefinitionDTO:
    """信号定义数据传输对象"""
    id: Optional[int] = None
    category_id: int = 0
    code: str = ""
    name: str = ""
    data_type: str = "float"
    unit: Optional[str] = None
    is_stored: bool = True
    is_realtime: bool = True
    is_feature: bool = False
    value_range: Optional[Dict[str, Any]] = None
    alarm_threshold: Optional[Dict[str, Any]] = None
    is_active: bool = True
```

```python
# platform_core/signal/repository.py
"""信号数据访问层"""
from typing import Optional, List

class SignalRepository:
    """信号定义数据仓库"""
    
    @staticmethod
    async def get_by_id(signal_id: int) -> Optional["SignalDefinition"]:
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.get_or_none(id=signal_id)
    
    @staticmethod
    async def get_by_category(category_id: int, is_active: bool = True) -> List["SignalDefinition"]:
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_active=is_active
        ).order_by("sort_order").all()
    
    @staticmethod
    async def get_stored_signals(category_id: int) -> List["SignalDefinition"]:
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_stored=True,
            is_active=True
        ).all()
    
    @staticmethod
    async def get_realtime_signals(category_id: int) -> List["SignalDefinition"]:
        from app.models.platform_upgrade import SignalDefinition
        return await SignalDefinition.filter(
            category_id=category_id,
            is_realtime=True,
            is_active=True
        ).all()
```

```python
# platform_core/signal/service.py
"""信号业务服务层"""
from typing import Optional, List, Dict, Any
from .repository import SignalRepository

class SignalService:
    """信号管理服务"""
    
    def __init__(self):
        self.repo = SignalRepository()
    
    async def get_signals_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        signals = await self.repo.get_by_category(category_id)
        return [self._to_dict(s) for s in signals]
    
    async def get_stored_signals(self, category_id: int) -> List[Dict[str, Any]]:
        signals = await self.repo.get_stored_signals(category_id)
        return [self._to_dict(s) for s in signals]
    
    def _to_dict(self, signal) -> Dict[str, Any]:
        return {
            "id": signal.id,
            "code": signal.code,
            "name": signal.name,
            "data_type": signal.data_type,
            "unit": signal.unit,
            "is_stored": signal.is_stored,
            "is_realtime": signal.is_realtime,
            "is_feature": signal.is_feature
        }
```

### 3. ai_engine/model 模块（合并registry+storage）

```python
# ai_engine/model/__init__.py
"""
模型管理模块

整合model_registry和model_storage的功能。
"""
from .registry import ModelRegistry
from .storage import ModelStorage
from .version import ModelVersionManager
from .loader import ModelLoader

__all__ = ["ModelRegistry", "ModelStorage", "ModelVersionManager", "ModelLoader"]
```

```python
# ai_engine/model/registry.py
"""
模型注册服务

从ai_engine/model_registry/registry.py迁移。
"""
# 保留原有实现，更新import路径
```

```python
# ai_engine/model/storage.py
"""
模型存储服务

整合ai_engine/model_storage的功能。
"""
from .backends.local import LocalStorage
from .backends.minio import MinIOStorage

class ModelStorage:
    """统一的模型存储接口"""
    
    def __init__(self, backend: str = "local"):
        if backend == "minio":
            self._backend = MinIOStorage()
        else:
            self._backend = LocalStorage()
    
    async def save(self, model_id: str, version: str, data: bytes) -> str:
        return await self._backend.save(model_id, version, data)
    
    async def load(self, path: str) -> bytes:
        return await self._backend.load(path)
    
    async def delete(self, path: str) -> bool:
        return await self._backend.delete(path)
```

### 4. 统一API v4设计

```python
# app/api/v4/__init__.py
"""
统一API v4

整合v2和v3的所有功能，提供统一的API接口。
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v4")

# 导入子路由
from .assets import router as assets_router
from .categories import router as categories_router
from .signals import router as signals_router
from .models import router as models_router
from .features import router as features_router
from .decisions import router as decisions_router
from .timeseries import router as timeseries_router
from .ingestion import router as ingestion_router
from .system import router as system_router

router.include_router(assets_router, prefix="/assets", tags=["资产管理"])
router.include_router(categories_router, prefix="/categories", tags=["资产类别"])
router.include_router(signals_router, prefix="/signals", tags=["信号定义"])
router.include_router(models_router, prefix="/models", tags=["AI模型"])
router.include_router(features_router, prefix="/features", tags=["特征工程"])
router.include_router(decisions_router, prefix="/decisions", tags=["决策引擎"])
router.include_router(timeseries_router, prefix="/timeseries", tags=["时序数据"])
router.include_router(ingestion_router, prefix="/ingestion", tags=["数据采集"])
router.include_router(system_router, prefix="/system", tags=["系统管理"])
```

```python
# app/api/v4/schemas.py
"""
统一响应格式
"""
from typing import TypeVar, Generic, Optional, Any, List
from pydantic import BaseModel
from datetime import datetime

T = TypeVar("T")

class PageMeta(BaseModel):
    """分页元数据"""
    page: int = 1
    page_size: int = 20
    total: int = 0
    timestamp: datetime = None
    
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        super().__init__(**data)

class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    meta: Optional[PageMeta] = None

class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    details: Optional[Any] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        super().__init__(**data)

# 错误码定义
class ErrorCodes:
    SUCCESS = 0
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    VALIDATION_ERROR = 422
    INTERNAL_ERROR = 500
```

### 5. 数据库迁移脚本设计

```sql
-- migrations/v3_schema_rename.sql
-- V3 Schema重命名迁移脚本

-- 开始事务
BEGIN;

-- 1. 重命名表（如果存在旧表名）
-- 注意：当前表名已经是新命名，此脚本用于处理可能存在的旧命名

-- 检查并重命名 device_types -> asset_categories (如果存在)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_types') THEN
        ALTER TABLE device_types RENAME TO t_asset_category;
    END IF;
END $$;

-- 检查并重命名 device_fields -> signal_definitions (如果存在)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_fields') THEN
        ALTER TABLE device_fields RENAME TO t_signal_definition;
    END IF;
END $$;

-- 检查并重命名 device_info -> assets (如果存在)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'device_info') THEN
        ALTER TABLE device_info RENAME TO t_asset;
    END IF;
END $$;

-- 2. 重命名列（如果存在旧列名）
-- device_type_id -> category_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_signal_definition' AND column_name = 'device_type_id'
    ) THEN
        ALTER TABLE t_signal_definition RENAME COLUMN device_type_id TO category_id;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 't_asset' AND column_name = 'device_type_id'
    ) THEN
        ALTER TABLE t_asset RENAME COLUMN device_type_id TO category_id;
    END IF;
END $$;

-- 3. 更新外键约束名称
-- 这里假设外键约束需要更新

-- 4. 创建迁移记录
INSERT INTO t_migration_record (
    migration_name,
    migration_type,
    source_table,
    target_table,
    status,
    started_at,
    completed_at
) VALUES (
    'v3_schema_rename',
    'schema_rename',
    'device_*',
    'asset_*/signal_*',
    'completed',
    NOW(),
    NOW()
);

COMMIT;
```

```sql
-- migrations/v3_schema_rollback.sql
-- V3 Schema回滚脚本

BEGIN;

-- 回滚表重命名
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset_category') THEN
        ALTER TABLE t_asset_category RENAME TO device_types;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_signal_definition') THEN
        ALTER TABLE t_signal_definition RENAME TO device_fields;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 't_asset') THEN
        ALTER TABLE t_asset RENAME TO device_info;
    END IF;
END $$;

-- 回滚列重命名
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'device_fields' AND column_name = 'category_id'
    ) THEN
        ALTER TABLE device_fields RENAME COLUMN category_id TO device_type_id;
    END IF;
END $$;

-- 更新迁移记录
UPDATE t_migration_record 
SET status = 'rolled_back', completed_at = NOW()
WHERE migration_name = 'v3_schema_rename';

COMMIT;
```

## 数据模型

### 模块依赖关系

```
platform_core/
├── asset/          # 依赖: app/models/platform_upgrade
├── signal/         # 依赖: app/models/platform_upgrade
├── metadata/       # 依赖: asset, signal
├── timeseries/     # 依赖: metadata
├── ingestion/      # 依赖: metadata, timeseries
└── realtime/       # 依赖: metadata

ai_engine/
├── model/          # 依赖: platform_core/asset
├── inference/      # 依赖: model
├── feature/        # 依赖: platform_core/signal
└── decision/       # 依赖: model, inference
```

### Import路径映射

| 旧路径 | 新路径 |
|--------|--------|
| `platform_v2.metadata` | `platform_core.metadata` |
| `platform_v2.timeseries` | `platform_core.timeseries` |
| `ai_engine.feature_hub` | `ai_engine.feature` |
| `ai_engine.decision_engine` | `ai_engine.decision` |
| `ai_engine.model_registry` | `ai_engine.model` |
| `ai_engine.model_storage` | `ai_engine.model` |



## 正确性属性

*正确性属性是系统在所有有效执行中应保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


基于验收标准分析，以下是本系统的正确性属性：

### Property 1: 无旧模块Import引用

*对于任意* Python源文件，不应存在对已废弃模块（platform_v2、feature_hub、decision_engine、model_registry、model_storage）的import语句。

**Validates: Requirements 1.4, 3.4**

### Property 2: 无旧命名残留

*对于任意* Python源文件（排除迁移脚本和注释），不应存在device_type、device_field、device_info、field_value等旧命名模式。

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 3: 数据库迁移往返一致性

*对于任意* 数据库状态，执行迁移脚本后再执行回滚脚本，数据库Schema应恢复到原始状态，数据完整性应保持不变。

**Validates: Requirements 5.6**

### Property 4: API响应格式一致性

*对于任意* v4 API端点的响应，应包含code、message、data字段，分页响应应额外包含meta字段（page、page_size、total、timestamp）。

**Validates: Requirements 6.2, 6.3, 6.4**

### Property 5: API向后兼容性

*对于任意* v2/v3 API的有效请求，通过兼容层转发到v4 API后，应返回语义等价的响应。

**Validates: Requirements 6.5**

### Property 6: AI引擎功能回归

*对于任意* AI引擎的现有测试用例，在模块重命名后应继续通过，功能行为应保持不变。

**Validates: Requirements 3.5**

### Property 7: 服务调用路径统一

*对于任意* 业务逻辑调用，应通过platform_core或ai_engine模块进行，app/services层应仅作为API适配器。

**Validates: Requirements 7.4**

## 错误处理

### 迁移错误处理

```python
class MigrationError(Exception):
    """迁移错误基类"""
    pass

class SchemaRenameError(MigrationError):
    """Schema重命名错误"""
    def __init__(self, table_name: str, message: str):
        self.table_name = table_name
        super().__init__(f"重命名表 {table_name} 失败: {message}")

class RollbackError(MigrationError):
    """回滚错误"""
    pass

class ImportPathError(Exception):
    """Import路径错误"""
    def __init__(self, old_path: str, new_path: str):
        super().__init__(f"发现旧import路径 {old_path}，应更新为 {new_path}")
```

### API错误处理

```python
from fastapi import HTTPException
from app.api.v4.schemas import ErrorCodes, ErrorResponse

class APIError(HTTPException):
    """API错误基类"""
    def __init__(self, code: int, message: str, details: Any = None):
        self.error_response = ErrorResponse(
            code=code,
            message=message,
            details=details
        )
        super().__init__(status_code=code, detail=self.error_response.dict())

class NotFoundError(APIError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code=ErrorCodes.NOT_FOUND,
            message=f"{resource} not found",
            details={"identifier": identifier}
        )

class ValidationError(APIError):
    def __init__(self, errors: List[Dict]):
        super().__init__(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Validation failed",
            details={"errors": errors}
        )
```

## 测试策略

### 双重测试方法

本项目采用单元测试和属性测试相结合的方法：

- **单元测试**: 验证具体示例、边界情况和错误条件
- **属性测试**: 验证跨所有输入的通用属性

### 属性测试配置

- 使用 **Hypothesis** 作为Python属性测试框架
- 每个属性测试最少运行 **100次** 迭代
- 每个测试用注释标注对应的设计文档属性

### 测试文件结构

```
tests/
├── unit/
│   ├── test_asset_service.py
│   ├── test_signal_service.py
│   ├── test_model_registry.py
│   └── test_api_v4.py
├── property/
│   ├── test_import_paths_property.py      # Property 1
│   ├── test_naming_convention_property.py # Property 2
│   ├── test_migration_roundtrip.py        # Property 3
│   ├── test_api_response_format.py        # Property 4
│   ├── test_api_compatibility.py          # Property 5
│   └── test_ai_engine_regression.py       # Property 6
└── integration/
    ├── test_platform_core_integration.py
    └── test_api_v4_integration.py
```

### 属性测试示例

```python
# tests/property/test_import_paths_property.py
"""
Property 1: 无旧模块Import引用
Feature: v3-system-optimization, Property 1: 无旧模块Import引用
Validates: Requirements 1.4, 3.4
"""
from hypothesis import given, strategies as st, settings
import ast
import os
from pathlib import Path

DEPRECATED_MODULES = [
    "platform_v2",
    "ai_engine.feature_hub",
    "ai_engine.decision_engine",
    "ai_engine.model_registry",
    "ai_engine.model_storage"
]

def get_python_files():
    """获取所有Python源文件"""
    root = Path(".")
    exclude_dirs = {".venv", "node_modules", "__pycache__", ".git"}
    for py_file in root.rglob("*.py"):
        if not any(excluded in py_file.parts for excluded in exclude_dirs):
            yield py_file

def extract_imports(file_path: Path) -> list:
    """提取文件中的所有import语句"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    except:
        return []

@settings(max_examples=1)  # 只需运行一次，检查所有文件
@given(st.just(None))
def test_no_deprecated_imports(_):
    """
    Property 1: 对于任意Python源文件，不应存在对已废弃模块的import语句
    """
    violations = []
    for py_file in get_python_files():
        imports = extract_imports(py_file)
        for imp in imports:
            for deprecated in DEPRECATED_MODULES:
                if imp.startswith(deprecated):
                    violations.append({
                        "file": str(py_file),
                        "import": imp,
                        "deprecated_module": deprecated
                    })
    
    assert len(violations) == 0, f"发现 {len(violations)} 处旧模块引用: {violations}"
```

```python
# tests/property/test_api_response_format.py
"""
Property 4: API响应格式一致性
Feature: v3-system-optimization, Property 4: API响应格式一致性
Validates: Requirements 6.2, 6.3, 6.4
"""
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

V4_ENDPOINTS = [
    "/api/v4/assets",
    "/api/v4/categories",
    "/api/v4/signals",
    "/api/v4/models",
    "/api/v4/system/health"
]

@given(endpoint=st.sampled_from(V4_ENDPOINTS))
@settings(max_examples=100)
def test_api_response_format(endpoint):
    """
    Property 4: 对于任意v4 API端点的响应，应包含code、message、data字段
    """
    response = client.get(endpoint)
    data = response.json()
    
    # 验证必需字段
    assert "code" in data, f"响应缺少code字段: {endpoint}"
    assert "message" in data, f"响应缺少message字段: {endpoint}"
    assert "data" in data or "error" in data, f"响应缺少data字段: {endpoint}"
    
    # 验证分页响应
    if isinstance(data.get("data"), list):
        assert "meta" in data, f"列表响应缺少meta字段: {endpoint}"
        meta = data["meta"]
        assert "page" in meta, "meta缺少page字段"
        assert "page_size" in meta, "meta缺少page_size字段"
        assert "total" in meta, "meta缺少total字段"
```

## 实施计划

### 阶段1: 代码整合 (1-2周)

1. 创建platform_core/asset模块
2. 创建platform_core/signal模块
3. 迁移platform_v2/metadata到platform_core/metadata
4. 迁移platform_v2/timeseries到platform_core/timeseries
5. 重命名ai_engine子模块
6. 更新所有import路径
7. 删除platform_v2目录

### 阶段2: 命名规范统一 (1周)

1. 全局搜索替换device→asset命名
2. 全局搜索替换field→signal命名
3. 更新数据库迁移脚本
4. 创建命名映射文档

### 阶段3: API整合 (1-2周)

1. 创建v4 API基础结构
2. 实现统一响应格式
3. 迁移v2/v3 API功能到v4
4. 创建兼容层
5. 生成OpenAPI文档

### 阶段4: 测试完善 (1周)

1. 编写属性测试
2. 补充单元测试
3. 运行回归测试
4. 验证代码覆盖率

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Import路径更新遗漏 | 高 | 使用属性测试自动检测，CI/CD集成 |
| 数据库迁移失败 | 高 | 提供回滚脚本，先在测试环境验证 |
| API兼容性问题 | 中 | 保留兼容层，逐步迁移 |
| 测试覆盖不足 | 中 | 设置覆盖率门槛，属性测试补充 |
