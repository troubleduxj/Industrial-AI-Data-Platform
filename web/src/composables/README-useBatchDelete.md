# useBatchDelete 批量删除组合式函数

## 概述

`useBatchDelete` 是一个可复用的 Vue 3 组合式函数，提供统一的批量删除逻辑。它包含选择状态管理、确认对话框、API调用、错误处理和权限控制等完整功能。

## 特性

- ✅ **统一的批量删除逻辑** - 提供一致的用户体验
- ✅ **选择状态管理** - 自动管理选中项目和行键
- ✅ **权限控制** - 支持细粒度权限检查
- ✅ **数据验证** - 支持自定义验证规则和排除条件
- ✅ **错误处理** - 完善的错误处理和用户反馈
- ✅ **防抖处理** - 防止重复提交
- ✅ **操作审计** - 记录操作结果和失败详情
- ✅ **响应式设计** - 基于 Vue 3 Composition API

## 基本用法

```javascript
import { useBatchDelete } from '@/composables/useBatchDelete'

// 在组件中使用
const {
  selectedItems,
  selectedRowKeys,
  isLoading,
  selectedCount,
  canBatchDelete,
  setSelectedItems,
  handleBatchDelete,
  clearSelection
} = useBatchDelete({
  name: 'API',
  batchDeleteApi: (ids) => apiService.batchDelete(ids),
  refresh: () => loadData()
})
```

## API 参数

### 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 资源名称，用于显示消息，如 "API"、"字典类型" |
| `batchDeleteApi` | `Function` | 批量删除API函数，接收ids数组，返回Promise |
| `refresh` | `Function` | 刷新数据的函数 |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `validateItem` | `Function` | `undefined` | 验证单个项目的函数 |
| `permission` | `string` | `undefined` | 权限标识符 |
| `excludeCondition` | `Function` | `undefined` | 排除条件函数 |
| `maxBatchSize` | `number` | `100` | 最大批量删除数量 |
| `enableDebounce` | `boolean` | `true` | 是否启用防抖 |
| `debounceDelay` | `number` | `300` | 防抖延迟时间(ms) |

## 返回值

### 响应式状态

| 属性 | 类型 | 说明 |
|------|------|------|
| `selectedItems` | `Ref<Array>` | 选中的项目数组 |
| `selectedRowKeys` | `Ref<Array>` | 选中的行键数组 |
| `isLoading` | `Ref<boolean>` | 是否正在执行删除操作 |
| `lastOperation` | `Ref<Object>` | 最后一次操作的结果 |

### 计算属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `selectedCount` | `ComputedRef<number>` | 选中项目数量 |
| `hasSelection` | `ComputedRef<boolean>` | 是否有选中项目 |
| `canBatchDelete` | `ComputedRef<boolean>` | 是否可以执行批量删除 |
| `validItems` | `ComputedRef<Array>` | 有效的删除项目 |
| `invalidItems` | `ComputedRef<Array>` | 无效的删除项目 |

### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `setSelectedItems` | `(items, keys)` | 设置选中的项目 |
| `clearSelection` | `()` | 清除选择 |
| `handleBatchDelete` | `()` | 执行批量删除（包含确认流程） |
| `validateSelection` | `()` | 验证选中的项目 |
| `getOperationSummary` | `()` | 获取操作结果摘要 |
| `getFailedItemsDetails` | `()` | 获取失败项目详情 |
| `resetOperationState` | `()` | 重置操作状态 |

## 使用示例

### 1. 基本使用

```vue
<template>
  <div>
    <n-button 
      type="error" 
      :disabled="!canBatchDelete"
      :loading="isLoading"
      @click="handleBatchDelete"
    >
      批量删除 ({{ selectedCount }})
    </n-button>
    
    <n-data-table
      :data="tableData"
      :checked-row-keys="selectedRowKeys"
      @update:checked-row-keys="handleSelectionChange"
    />
  </div>
</template>

<script setup>
import { useBatchDelete } from '@/composables/useBatchDelete'
import { apiService } from '@/api'

const {
  selectedRowKeys,
  selectedCount,
  canBatchDelete,
  isLoading,
  setSelectedItems,
  handleBatchDelete
} = useBatchDelete({
  name: 'API',
  batchDeleteApi: apiService.batchDeleteApis,
  refresh: loadApiData
})

const handleSelectionChange = (keys) => {
  const items = tableData.value.filter(item => keys.includes(item.id))
  setSelectedItems(items, keys)
}
</script>
```

### 2. 带权限控制和验证

```javascript
const {
  // ... 其他返回值
} = useBatchDelete({
  name: '字典类型',
  batchDeleteApi: dictTypeService.batchDelete,
  refresh: loadDictTypes,
  permission: 'dict_type:batch_delete',
  excludeCondition: (item) => item.is_system, // 系统字典不能删除
  validateItem: (item) => {
    if (item.has_data) {
      return { valid: false, reason: '该字典类型下还有数据，无法删除' }
    }
    return { valid: true }
  },
  maxBatchSize: 50
})
```

### 3. 处理操作结果

```vue
<template>
  <n-alert 
    v-if="lastOperation" 
    :type="lastOperation.success ? 'success' : 'error'"
    :title="getOperationSummary()"
    closable
    @close="resetOperationState"
  >
    <div v-if="getFailedItemsDetails().length > 0">
      <n-text strong>失败详情：</n-text>
      <ul>
        <li v-for="item in getFailedItemsDetails()" :key="item.id">
          ID: {{ item.id }} - {{ item.reason }}
        </li>
      </ul>
    </div>
  </n-alert>
</template>

<script setup>
const {
  lastOperation,
  getOperationSummary,
  getFailedItemsDetails,
  resetOperationState
} = useBatchDelete({
  // ... 配置
})
</script>
```

## 预定义组合函数

为了方便使用，提供了一些预定义的批量删除组合函数：

```javascript
import { 
  useApiBatchDelete,
  useDictTypeBatchDelete,
  useDictDataBatchDelete,
  useSystemParamBatchDelete,
  useApiGroupBatchDelete,
  useDepartmentBatchDelete,
  useRoleBatchDelete,
  useUserBatchDelete,
  useMenuBatchDelete
} from '@/composables/useBatchDelete'

// 使用预定义的组合函数
const apiDelete = useApiBatchDelete({
  batchDeleteApi: apiService.batchDelete,
  refresh: loadApis
})
```

## API 响应格式

批量删除API应该返回符合以下格式的响应：

```javascript
// 成功响应
{
  success: true,
  message: "批量删除操作完成",
  data: {
    deleted_count: 3,
    failed_items: [
      {
        id: 4,
        reason: "该项目被其他资源引用，无法删除"
      }
    ],
    skipped_items: [
      {
        id: 5,
        reason: "系统内置项，不允许删除"
      }
    ]
  }
}

// 错误响应
{
  success: false,
  error: {
    code: "BATCH_DELETE_VALIDATION_ERROR",
    message: "批量删除请求验证失败"
  }
}
```

## 最佳实践

### 1. 权限控制

```javascript
// 在组件中检查权限
const { hasPermission } = usePermission()

const batchDelete = useBatchDelete({
  name: 'API',
  permission: 'api:batch_delete',
  // ...
})

// 在模板中使用权限控制
<n-button 
  v-if="hasPermission('api:batch_delete')"
  :disabled="!canBatchDelete"
  @click="handleBatchDelete"
>
  批量删除
</n-button>
```

### 2. 错误处理

```javascript
const batchDelete = useBatchDelete({
  name: 'API',
  batchDeleteApi: async (ids) => {
    try {
      return await apiService.batchDelete(ids)
    } catch (error) {
      // 转换错误格式
      throw new Error(error.response?.data?.message || '删除失败')
    }
  },
  // ...
})
```

### 3. 数据验证

```javascript
const batchDelete = useBatchDelete({
  name: '用户',
  validateItem: (user) => {
    if (user.is_super_admin) {
      return { valid: false, reason: '超级管理员不能删除' }
    }
    if (user.status === 'locked') {
      return { valid: false, reason: '用户已锁定' }
    }
    return { valid: true }
  },
  excludeCondition: (user) => user.is_system,
  // ...
})
```

## 注意事项

1. **API格式**: 确保批量删除API返回标准格式的响应
2. **权限检查**: 在前后端都要进行权限验证
3. **数据一致性**: 删除操作要保证数据一致性
4. **用户体验**: 提供清晰的操作反馈和错误信息
5. **性能考虑**: 对于大量数据，考虑分批处理或异步处理

## 故障排除

### 常见问题

1. **权限检查失败**: 确保权限标识符正确，用户有相应权限
2. **API调用失败**: 检查API接口是否正确实现
3. **选择状态不同步**: 确保正确调用 `setSelectedItems` 方法
4. **防抖不生效**: 检查 `enableDebounce` 配置

### 调试技巧

```javascript
// 启用调试模式
const batchDelete = useBatchDelete({
  name: 'API',
  batchDeleteApi: (ids) => {
    console.log('批量删除API调用:', ids)
    return apiService.batchDelete(ids)
  },
  refresh: () => {
    console.log('刷新数据')
    return loadData()
  }
})

// 监听操作结果
watch(lastOperation, (operation) => {
  if (operation) {
    console.log('批量删除操作结果:', operation)
  }
})
```