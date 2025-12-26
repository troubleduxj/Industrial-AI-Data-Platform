# 统一批量删除服务层

## 概述

统一批量删除服务层为系统提供了一致的批量删除功能，包括事务管理、错误处理、审计日志记录和权限检查。该服务层遵循开闭原则，通过验证器和权限检查器提供可扩展的业务逻辑。

## 核心组件

### 1. BatchDeleteResult
批量删除结果数据类，用于跟踪删除操作的结果。

```python
result = BatchDeleteResult()
result.deleted_count = 5
result.add_failed_item(1, "删除失败原因")
result.add_skipped_item(2, "跳过原因")
```

### 2. BatchDeleteValidator
验证器抽象基类，用于实现业务规则验证。

```python
class CustomValidator(BatchDeleteValidator):
    async def validate_item(self, item, context):
        if item.is_protected:
            return False, "受保护的项目不能删除"
        return True, None
```

### 3. BatchDeletePermissionChecker
权限检查器抽象基类，用于实现权限控制。

```python
class CustomPermissionChecker(BatchDeletePermissionChecker):
    async def check_permission(self, user, resource_type, context):
        if not user.has_permission(f"{resource_type}:batch_delete"):
            return False, "权限不足"
        return True, None
```

### 4. BatchDeleteAuditor
审计日志记录器，自动记录批量删除操作的详细信息。

### 5. BaseBatchDeleteService
通用批量删除服务基类，提供完整的批量删除功能。

## 使用方法

### 基本使用

```python
from app.services.batch_delete_service import BaseBatchDeleteService
from app.models.system import TSysConfig

# 创建服务实例
service = BaseBatchDeleteService(
    model_class=TSysConfig,
    resource_name="系统参数",
    module_name="系统参数管理"
)

# 执行批量删除
result = await service.batch_delete(
    request=request,
    item_ids=[1, 2, 3],
    current_user=current_user
)
```

### 高级使用 - 自定义验证器

```python
class SystemParamValidator(BatchDeleteValidator):
    async def validate_item(self, item: TSysConfig, context: dict):
        # 系统内置参数不能删除
        if item.is_system:
            return False, "系统内置参数不允许删除"
        
        # 关键参数不能删除
        critical_keys = ['system.version', 'auth.jwt_secret']
        if item.param_key in critical_keys:
            return False, "关键系统参数不允许删除"
        
        return True, None

# 使用自定义验证器
service = BaseBatchDeleteService(
    model_class=TSysConfig,
    resource_name="系统参数",
    module_name="系统参数管理",
    validator=SystemParamValidator()
)
```

### 高级使用 - 自定义权限检查

```python
class AdminPermissionChecker(BatchDeletePermissionChecker):
    async def check_permission(self, user: User, resource_type: str, context: dict):
        # 只有管理员可以批量删除
        if not user.is_superuser:
            return False, "只有超级管理员可以执行批量删除操作"
        return True, None

service = BaseBatchDeleteService(
    model_class=TSysConfig,
    resource_name="系统参数",
    module_name="系统参数管理",
    permission_checker=AdminPermissionChecker()
)
```

### 软删除实现

```python
class SoftDeleteService(BaseBatchDeleteService[MyModel]):
    async def _delete_item(self, item: MyModel, context: dict):
        """重写删除方法实现软删除"""
        item.is_deleted = True
        item.deleted_at = datetime.now()
        await item.save()
```

## 预定义组件

### 系统保护验证器
```python
from app.services.batch_delete_service import SystemProtectedValidator

# 防止删除系统内置项
validator = SystemProtectedValidator("is_system")
```

### 引用检查验证器
```python
from app.services.batch_delete_service import ReferenceCheckValidator

async def check_has_children(item):
    return await ChildModel.filter(parent_id=item.id).exists()

validator = ReferenceCheckValidator([check_has_children])
```

## API 集成

### 在 FastAPI 端点中使用

```python
from app.services.system_batch_delete_services import batch_delete_system_params

@router.delete("/batch", summary="批量删除系统参数")
async def batch_delete_system_params_endpoint(
    request: Request,
    batch_data: SysConfigBatchDelete,
    current_user: User = DependAuth
):
    return await batch_delete_system_params(
        request=request,
        item_ids=batch_data.ids,
        current_user=current_user,
        context={"source": "api_v2"}
    )
```

## 响应格式

### 成功响应
```json
{
  "success": true,
  "message": "批量删除操作完成，成功删除 3 个系统参数",
  "data": {
    "deleted_count": 3,
    "failed_items": [],
    "skipped_items": []
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "v2",
    "requestId": "req-123456789"
  }
}
```

### 部分成功响应
```json
{
  "success": true,
  "message": "批量删除操作完成，成功: 2，失败: 1，跳过: 1",
  "data": {
    "deleted_count": 2,
    "failed_items": [
      {"id": 3, "reason": "系统参数不存在"}
    ],
    "skipped_items": [
      {"id": 4, "reason": "系统内置参数不允许删除"}
    ]
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "v2",
    "requestId": "req-123456789"
  }
}
```

### 失败响应
```json
{
  "success": false,
  "error": {
    "code": "BATCH_DELETE_FAILED",
    "message": "批量删除操作失败，没有系统参数被删除",
    "details": [
      {
        "field": "batch_operation",
        "code": "BATCH_DELETE_FAILED",
        "message": "所有 3 个系统参数都无法删除"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "v2",
    "requestId": "req-123456789"
  }
}
```

## 审计日志

服务会自动记录以下审计信息：
- 批量操作开始
- 每个项目的删除结果
- 批量操作完成统计

审计日志包含：
- 用户信息
- 操作时间
- 操作详情
- 结果统计

## 错误处理

### 输入验证错误
- 空ID列表
- 超出批量限制
- 无效的ID格式

### 权限错误
- 用户权限不足
- 资源级权限检查失败

### 业务规则错误
- 系统保护项
- 引用约束
- 自定义业务规则

### 系统错误
- 数据库连接错误
- 事务失败
- 未预期的异常

## 性能考虑

### 批量优化
- 使用事务减少数据库往返
- 批量查询减少N+1问题
- 合理的批量大小限制

### 内存管理
- 流式处理大批量数据
- 及时释放不需要的对象
- 避免加载不必要的关联数据

## 测试

### 单元测试
```python
# 测试验证器
@pytest.mark.asyncio
async def test_validator():
    validator = SystemProtectedValidator()
    item = MockItem(is_system=True)
    is_valid, reason = await validator.validate_item(item, {})
    assert not is_valid
    assert "系统内置项" in reason
```

### 集成测试
```python
# 测试完整流程
@pytest.mark.asyncio
async def test_batch_delete_flow():
    service = BaseBatchDeleteService(MockModel, "测试", "测试模块")
    result = await service.batch_delete(request, [1, 2, 3], user)
    assert result["success"] is True
```

## 最佳实践

### 1. 验证器设计
- 单一职责：每个验证器只负责一种验证逻辑
- 可组合：多个验证器可以组合使用
- 性能优化：避免在验证器中执行复杂查询

### 2. 权限检查
- 细粒度：实现资源级和操作级权限检查
- 缓存：缓存权限检查结果提高性能
- 审计：记录权限检查失败的详细信息

### 3. 错误处理
- 友好提示：提供用户友好的错误信息
- 详细日志：记录详细的错误信息用于调试
- 恢复建议：在错误响应中提供解决建议

### 4. 性能优化
- 批量限制：设置合理的批量操作限制
- 索引优化：确保相关字段有适当的数据库索引
- 监控：监控批量操作的性能指标

## 扩展指南

### 添加新的资源类型
1. 创建资源特定的验证器
2. 实现权限检查器（如需要）
3. 创建服务实例
4. 在API端点中集成

### 自定义删除逻辑
1. 继承 BaseBatchDeleteService
2. 重写 _delete_item 方法
3. 实现自定义删除逻辑（如软删除、级联删除等）

### 添加新的验证规则
1. 继承 BatchDeleteValidator
2. 实现 validate_item 方法
3. 在服务中使用新验证器