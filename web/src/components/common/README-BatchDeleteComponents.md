# 批量删除UI组件使用指南

本文档介绍如何使用 `BatchDeleteButton` 和 `BatchDeleteConfirmDialog` 组件来实现统一的批量删除功能。

## 组件概述

### BatchDeleteButton 组件

批量删除按钮组件，提供统一的批量删除入口，支持：
- 显示选中数量
- 权限控制
- 禁用状态显示
- 选择验证
- 自定义样式

### BatchDeleteConfirmDialog 组件

批量删除确认对话框组件，提供统一的确认界面，支持：
- 显示删除项目详情
- 警告信息展示
- 无效项目提示
- 操作统计
- 自定义验证

## 基本使用

### 1. 导入组件

```vue
<script setup>
import { BatchDeleteButton, BatchDeleteConfirmDialog } from '@/components/common'
</script>
```

### 2. 基本模板

```vue
<template>
  <!-- 批量删除按钮 -->
  <batch-delete-button
    :selected-items="selectedItems"
    :selected-count="selectedCount"
    resource-name="用户"
    permission="user:batch_delete"
    @batch-delete="handleBatchDeleteClick"
  />

  <!-- 确认对话框 -->
  <batch-delete-confirm-dialog
    v-model:visible="showConfirmDialog"
    :items="selectedItems"
    resource-name="用户"
    @confirm="handleConfirmDelete"
    @cancel="handleCancelDelete"
  />
</template>
```

### 3. 基本逻辑

```vue
<script setup>
import { ref } from 'vue'

const selectedItems = ref([])
const selectedCount = computed(() => selectedItems.value.length)
const showConfirmDialog = ref(false)

const handleBatchDeleteClick = () => {
  showConfirmDialog.value = true
}

const handleConfirmDelete = async (data) => {
  // 执行批量删除逻辑
  console.log('确认删除:', data)
}

const handleCancelDelete = () => {
  showConfirmDialog.value = false
}
</script>
```

## 高级使用

### 1. 权限控制

```vue
<template>
  <batch-delete-button
    :selected-items="selectedItems"
    permission="user:batch_delete"
    resource="user"
    action="batch_delete"
    :hide-when-no-permission="true"
  />
</template>
```

### 2. 排除条件

```vue
<template>
  <batch-delete-button
    :selected-items="selectedItems"
    :exclude-condition="excludeSystemUsers"
  />
</template>

<script setup>
// 排除系统用户
const excludeSystemUsers = (user) => {
  return user.type === 'system' || user.is_built_in
}
</script>
```

### 3. 自定义验证

```vue
<template>
  <batch-delete-button
    :selected-items="selectedItems"
    :validate-selection="validateUserSelection"
    @validation-error="handleValidationError"
  />
</template>

<script setup>
const validateUserSelection = (items) => {
  // 检查是否包含当前用户
  const currentUserId = getCurrentUserId()
  const containsCurrentUser = items.some(user => user.id === currentUserId)
  
  if (containsCurrentUser) {
    return {
      valid: false,
      message: '不能删除当前登录用户'
    }
  }
  
  return { valid: true }
}

const handleValidationError = (error) => {
  message.warning(error.message)
}
</script>
```

### 4. 确认对话框高级配置

```vue
<template>
  <batch-delete-confirm-dialog
    v-model:visible="showConfirmDialog"
    :items="selectedItems"
    :invalid-items="invalidItems"
    :warnings="warnings"
    resource-name="用户"
    :show-statistics="true"
    :max-display-items="5"
    :item-display-field="getUserDisplayName"
    :before-confirm="beforeConfirmDelete"
    @confirm="handleConfirmDelete"
  />
</template>

<script setup>
// 无效项目（不能删除的）
const invalidItems = computed(() => {
  return selectedItems.value
    .filter(user => user.type === 'system')
    .map(user => ({
      item: user,
      reason: '系统用户不能删除'
    }))
})

// 警告信息
const warnings = computed(() => {
  const warnings = []
  
  if (selectedItems.value.length > 10) {
    warnings.push({
      type: 'warning',
      title: '注意',
      message: '批量删除大量用户可能影响系统性能'
    })
  }
  
  return warnings
})

// 自定义显示名称
const getUserDisplayName = (user) => {
  return `${user.username} (${user.email})`
}

// 确认前验证
const beforeConfirmDelete = async (data) => {
  // 可以在这里添加额外的异步验证
  if (data.validItems.length === 0) {
    message.warning('没有可删除的用户')
    return false
  }
  
  return true
}
</script>
```

## 与 useBatchDelete 组合使用

推荐与 `useBatchDelete` 组合式函数一起使用，获得完整的批量删除体验：

```vue
<template>
  <div>
    <!-- 数据表格 -->
    <n-data-table
      :columns="columns"
      :data="tableData"
      :checked-row-keys="selectedRowKeys"
      @update:checked-row-keys="handleSelectionChange"
    />

    <!-- 批量删除按钮 -->
    <batch-delete-button
      :selected-items="selectedItems"
      :selected-count="selectedCount"
      resource-name="用户"
      permission="user:batch_delete"
      :loading="isLoading"
      @batch-delete="handleBatchDelete"
    />

    <!-- 确认对话框 -->
    <batch-delete-confirm-dialog
      v-model:visible="showConfirmDialog"
      :items="validItems"
      :invalid-items="invalidItemsWithReasons"
      resource-name="用户"
      :confirm-loading="isLoading"
      @confirm="executeBatchDelete"
      @cancel="() => showConfirmDialog = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useBatchDelete } from '@/composables/useBatchDelete'
import { batchDeleteUsers } from '@/api/users'

const showConfirmDialog = ref(false)

// 使用批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading,
  validItems,
  invalidItems,
  setSelectedItems,
  executeBatchDelete: performBatchDelete
} = useBatchDelete({
  name: '用户',
  batchDeleteApi: batchDeleteUsers,
  refresh: refreshUserData,
  excludeCondition: (user) => user.type === 'system'
})

// 无效项目及原因
const invalidItemsWithReasons = computed(() => {
  return invalidItems.value.map(item => ({
    item,
    reason: '系统用户不能删除'
  }))
})

// 处理选择变化
const handleSelectionChange = (keys) => {
  const items = tableData.value.filter(item => keys.includes(item.id))
  setSelectedItems(items, keys)
}

// 处理批量删除按钮点击
const handleBatchDelete = () => {
  showConfirmDialog.value = true
}

// 执行批量删除
const executeBatchDelete = async () => {
  await performBatchDelete()
  showConfirmDialog.value = false
}
</script>
```

## API 参考

### BatchDeleteButton Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| selectedItems | Array | [] | 选中的项目数组 |
| selectedCount | Number | 0 | 选中项目数量 |
| resourceName | String | '项目' | 资源名称 |
| permission | String/Array | null | 权限标识符 |
| excludeCondition | Function | null | 排除条件函数 |
| hideWhenNoPermission | Boolean | true | 无权限时是否隐藏 |
| hideWhenNoSelection | Boolean | true | 无选择时是否隐藏 |
| showCount | Boolean | true | 是否显示数量 |
| maxBatchSize | Number | 100 | 最大批量删除数量 |
| validateSelection | Function | null | 选择验证函数 |

### BatchDeleteButton Events

| 事件 | 参数 | 说明 |
|------|------|------|
| batch-delete | { selectedItems, selectedCount, validCount, invalidCount } | 批量删除按钮点击 |
| validation-error | { message, selectedCount, validCount, invalidCount } | 验证错误 |
| permission-change | { hasPermission, previousState, permission, timestamp } | 权限状态变化 |

### BatchDeleteConfirmDialog Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| visible | Boolean | false | 对话框显示状态 |
| items | Array | [] | 要删除的项目数组 |
| resourceName | String | '项目' | 资源名称 |
| warnings | Array | [] | 警告信息数组 |
| invalidItems | Array | [] | 无效项目数组 |
| showItemDetails | Boolean | true | 是否显示项目详情 |
| showStatistics | Boolean | true | 是否显示统计信息 |
| maxDisplayItems | Number | 10 | 最大显示项目数量 |
| itemDisplayField | String/Function | 'name' | 项目显示字段 |
| beforeConfirm | Function | null | 确认前验证函数 |

### BatchDeleteConfirmDialog Events

| 事件 | 参数 | 说明 |
|------|------|------|
| confirm | { items, validCount, invalidCount, warnings } | 确认删除 |
| cancel | - | 取消删除 |
| close | - | 关闭对话框 |

## 最佳实践

1. **权限控制**：始终设置适当的权限标识符
2. **排除条件**：为系统保护项设置排除条件
3. **验证逻辑**：添加业务相关的验证逻辑
4. **错误处理**：妥善处理验证错误和操作失败
5. **用户体验**：提供清晰的反馈和进度提示
6. **性能优化**：大量数据时考虑分页和虚拟滚动

## 示例项目

查看 `BatchDeleteComponentsExample.vue` 文件获取完整的使用示例。