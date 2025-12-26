<!--
批量删除确认对话框组件
提供统一的确认对话框，显示删除详情和警告信息
-->
<template>
  <n-modal
    v-model:show="dialogVisible"
    :mask-closable="maskClosable"
    :close-on-esc="closeOnEsc"
    :auto-focus="autoFocus"
    :trap-focus="trapFocus"
    preset="dialog"
    :title="dialogTitle"
    :positive-text="positiveText"
    :negative-text="negativeText"
    :loading="confirmLoading"
    :positive-button-props="positiveButtonProps"
    :negative-button-props="negativeButtonProps"
    @positive-click="handleConfirm"
    @negative-click="handleCancel"
    @mask-click="handleMaskClick"
    @esc="handleEsc"
    @close="handleClose"
  >
    <div class="batch-delete-confirm-content">
      <!-- 主要确认信息 -->
      <div class="confirm-message">
        <n-text :depth="2">
          {{ confirmMessage }}
        </n-text>
      </div>

      <!-- 选中项目详情 -->
      <div v-if="showItemDetails && items.length > 0" class="item-details">
        <n-divider title-placement="left">
          <n-text :depth="3" :style="{ fontSize: '12px' }"> 选中项目 ({{ items.length }}) </n-text>
        </n-divider>

        <div class="item-list">
          <div
            v-for="(item, index) in displayItems"
            :key="getItemKey(item, index)"
            class="item-row"
          >
            <n-tag :type="getItemTagType(item)" size="small" :bordered="false">
              {{ getItemDisplayText(item) }}
            </n-tag>
          </div>

          <!-- 显示更多按钮 -->
          <div v-if="items.length > maxDisplayItems" class="more-items">
            <n-button text size="small" @click="toggleShowAll">
              {{ showAllItems ? '收起' : `还有 ${items.length - maxDisplayItems} 项...` }}
            </n-button>
          </div>
        </div>
      </div>

      <!-- 警告信息 -->
      <div v-if="warnings.length > 0" class="warnings-section">
        <n-divider title-placement="left">
          <n-text :depth="3" :style="{ fontSize: '12px' }"> 注意事项 </n-text>
        </n-divider>

        <div class="warnings-list">
          <n-alert
            v-for="(warning, index) in warnings"
            :key="index"
            :type="getWarningType(warning)"
            :title="getWarningTitle(warning)"
            :closable="false"
            size="small"
            class="warning-item"
          >
            {{ getWarningMessage(warning) }}
          </n-alert>
        </div>
      </div>

      <!-- 无效项目信息 -->
      <div v-if="invalidItems.length > 0" class="invalid-items-section">
        <n-divider title-placement="left">
          <n-text :depth="3" :style="{ fontSize: '12px' }">
            将被跳过的项目 ({{ invalidItems.length }})
          </n-text>
        </n-divider>

        <div class="invalid-items-list">
          <div
            v-for="(item, index) in displayInvalidItems"
            :key="getItemKey(item.item || item, index)"
            class="invalid-item-row"
          >
            <n-tag type="warning" size="small" :bordered="false">
              {{ getItemDisplayText(item.item || item) }}
            </n-tag>
            <n-text :depth="3" :style="{ fontSize: '12px', marginLeft: '8px' }">
              {{ item.reason || '无法删除' }}
            </n-text>
          </div>

          <!-- 显示更多无效项目 -->
          <div v-if="invalidItems.length > maxDisplayItems" class="more-invalid-items">
            <n-button text size="small" @click="toggleShowAllInvalid">
              {{
                showAllInvalidItems ? '收起' : `还有 ${invalidItems.length - maxDisplayItems} 项...`
              }}
            </n-button>
          </div>
        </div>
      </div>

      <!-- 操作统计 -->
      <div v-if="showStatistics" class="statistics-section">
        <n-divider title-placement="left">
          <n-text :depth="3" :style="{ fontSize: '12px' }"> 操作统计 </n-text>
        </n-divider>

        <div class="statistics-content">
          <n-space>
            <n-tag type="info" size="small"> 总计: {{ totalCount }} </n-tag>
            <n-tag type="success" size="small"> 可删除: {{ validCount }} </n-tag>
            <n-tag v-if="invalidCount > 0" type="warning" size="small">
              跳过: {{ invalidCount }}
            </n-tag>
          </n-space>
        </div>
      </div>

      <!-- 自定义内容插槽 -->
      <div v-if="$slots.content" class="custom-content">
        <slot name="content" :items="items" :warnings="warnings" :invalid-items="invalidItems" />
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { NModal, NText, NDivider, NTag, NButton, NAlert, NSpace } from 'naive-ui'

const props = defineProps({
  // 对话框显示控制
  visible: {
    type: Boolean,
    default: false,
  },

  // 基本信息
  items: {
    type: Array,
    default: () => [],
  },
  resourceName: {
    type: String,
    default: '项目',
  },

  // 警告和无效项目
  warnings: {
    type: Array,
    default: () => [],
  },
  invalidItems: {
    type: Array,
    default: () => [],
  },

  // 对话框配置
  title: {
    type: String,
    default: null,
  },
  message: {
    type: String,
    default: null,
  },
  positiveText: {
    type: String,
    default: '确定删除',
  },
  negativeText: {
    type: String,
    default: '取消',
  },

  // 显示控制
  showItemDetails: {
    type: Boolean,
    default: true,
  },
  showStatistics: {
    type: Boolean,
    default: true,
  },
  maxDisplayItems: {
    type: Number,
    default: 10,
  },

  // 项目显示配置
  itemDisplayField: {
    type: [String, Function],
    default: 'name',
  },
  itemKeyField: {
    type: [String, Function],
    default: 'id',
  },
  itemTypeField: {
    type: [String, Function],
    default: null,
  },

  // 对话框行为
  maskClosable: {
    type: Boolean,
    default: false,
  },
  closeOnEsc: {
    type: Boolean,
    default: true,
  },
  autoFocus: {
    type: Boolean,
    default: true,
  },
  trapFocus: {
    type: Boolean,
    default: true,
  },

  // 按钮配置
  confirmLoading: {
    type: Boolean,
    default: false,
  },
  positiveButtonProps: {
    type: Object,
    default: () => ({ type: 'error' }),
  },
  negativeButtonProps: {
    type: Object,
    default: () => ({}),
  },

  // 自定义验证
  beforeConfirm: {
    type: Function,
    default: null,
  },
})

const emit = defineEmits(['update:visible', 'confirm', 'cancel', 'close', 'mask-click', 'esc'])

// 内部状态
const showAllItems = ref(false)
const showAllInvalidItems = ref(false)

// 对话框显示状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

// 对话框标题
const dialogTitle = computed(() => {
  return props.title || `批量删除${props.resourceName}`
})

// 确认消息
const confirmMessage = computed(() => {
  if (props.message) {
    return props.message
  }

  const validCount = props.items.length - props.invalidItems.length
  let message = `确定要删除选中的 ${validCount} 个${props.resourceName}吗？`

  if (props.invalidItems.length > 0) {
    message += `\n\n注意：${props.invalidItems.length} 个${props.resourceName}将被跳过。`
  }

  return message
})

// 统计信息
const totalCount = computed(() => props.items.length)
const validCount = computed(() => props.items.length - props.invalidItems.length)
const invalidCount = computed(() => props.invalidItems.length)

// 显示的项目列表
const displayItems = computed(() => {
  if (showAllItems.value || props.items.length <= props.maxDisplayItems) {
    return props.items
  }
  return props.items.slice(0, props.maxDisplayItems)
})

// 显示的无效项目列表
const displayInvalidItems = computed(() => {
  if (showAllInvalidItems.value || props.invalidItems.length <= props.maxDisplayItems) {
    return props.invalidItems
  }
  return props.invalidItems.slice(0, props.maxDisplayItems)
})

// 获取项目显示文本
const getItemDisplayText = (item) => {
  if (typeof props.itemDisplayField === 'function') {
    return props.itemDisplayField(item)
  }

  if (typeof props.itemDisplayField === 'string') {
    return item[props.itemDisplayField] || item.name || item.title || `项目 ${item.id || ''}`
  }

  return item.name || item.title || `项目 ${item.id || ''}`
}

// 获取项目键值
const getItemKey = (item, index) => {
  if (typeof props.itemKeyField === 'function') {
    return props.itemKeyField(item, index)
  }

  if (typeof props.itemKeyField === 'string') {
    return item[props.itemKeyField] || index
  }

  return item.id || index
}

// 获取项目标签类型
const getItemTagType = (item) => {
  if (typeof props.itemTypeField === 'function') {
    const type = props.itemTypeField(item)
    return getTagTypeByValue(type)
  }

  if (typeof props.itemTypeField === 'string') {
    const type = item[props.itemTypeField]
    return getTagTypeByValue(type)
  }

  return 'default'
}

// 根据值获取标签类型
const getTagTypeByValue = (value) => {
  const typeMap = {
    system: 'error',
    user: 'info',
    temp: 'warning',
    active: 'success',
    inactive: 'default',
    enabled: 'success',
    disabled: 'default',
  }

  return typeMap[value] || 'default'
}

// 获取警告类型
const getWarningType = (warning) => {
  if (typeof warning === 'object' && warning.type) {
    return warning.type
  }
  return 'warning'
}

// 获取警告标题
const getWarningTitle = (warning) => {
  if (typeof warning === 'object' && warning.title) {
    return warning.title
  }
  return '注意'
}

// 获取警告消息
const getWarningMessage = (warning) => {
  if (typeof warning === 'string') {
    return warning
  }
  if (typeof warning === 'object' && warning.message) {
    return warning.message
  }
  return '请注意相关风险'
}

// 切换显示所有项目
const toggleShowAll = () => {
  showAllItems.value = !showAllItems.value
}

// 切换显示所有无效项目
const toggleShowAllInvalid = () => {
  showAllInvalidItems.value = !showAllInvalidItems.value
}

// 处理确认
const handleConfirm = async () => {
  try {
    // 自定义确认前验证
    if (props.beforeConfirm) {
      const result = await props.beforeConfirm({
        items: props.items,
        validItems: props.items.filter(
          (item, index) =>
            !props.invalidItems.some(
              (invalid) => getItemKey(invalid.item || invalid, index) === getItemKey(item, index)
            )
        ),
        invalidItems: props.invalidItems,
        warnings: props.warnings,
      })

      if (result === false) {
        return
      }
    }

    emit('confirm', {
      items: props.items,
      validCount: validCount.value,
      invalidCount: invalidCount.value,
      warnings: props.warnings,
    })
  } catch (error) {
    console.error('确认删除时出错:', error)
  }
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理关闭
const handleClose = () => {
  emit('close')
}

// 处理遮罩点击
const handleMaskClick = () => {
  if (props.maskClosable) {
    emit('mask-click')
    emit('cancel')
  }
}

// 处理ESC键
const handleEsc = () => {
  if (props.closeOnEsc) {
    emit('esc')
    emit('cancel')
  }
}

// 监听对话框显示状态，重置内部状态
watch(dialogVisible, (newValue) => {
  if (newValue) {
    showAllItems.value = false
    showAllInvalidItems.value = false
  }
})

// 暴露组件方法和状态
defineExpose({
  dialogVisible,
  totalCount,
  validCount,
  invalidCount,
  displayItems,
  displayInvalidItems,
  getItemDisplayText,
  getItemKey,
  toggleShowAll,
  toggleShowAllInvalid,
})
</script>

<style scoped>
.batch-delete-confirm-content {
  max-height: 60vh;
  overflow-y: auto;
}

.confirm-message {
  margin-bottom: 16px;
  line-height: 1.6;
  white-space: pre-line;
}

.item-details,
.warnings-section,
.invalid-items-section,
.statistics-section,
.custom-content {
  margin-top: 16px;
}

.item-list,
.invalid-items-list {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px 0;
}

.item-row,
.invalid-item-row {
  display: flex;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid var(--n-divider-color);
}

.item-row:last-child,
.invalid-item-row:last-child {
  border-bottom: none;
}

.invalid-item-row {
  justify-content: space-between;
}

.warnings-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.warning-item {
  margin: 0;
}

.more-items,
.more-invalid-items {
  text-align: center;
  padding: 8px 0;
  border-top: 1px solid var(--n-divider-color);
}

.statistics-content {
  padding: 8px 0;
}

/* 滚动条样式 */
.item-list::-webkit-scrollbar,
.invalid-items-list::-webkit-scrollbar,
.batch-delete-confirm-content::-webkit-scrollbar {
  width: 6px;
}

.item-list::-webkit-scrollbar-track,
.invalid-items-list::-webkit-scrollbar-track,
.batch-delete-confirm-content::-webkit-scrollbar-track {
  background: var(--n-scrollbar-track-color);
  border-radius: 3px;
}

.item-list::-webkit-scrollbar-thumb,
.invalid-items-list::-webkit-scrollbar-thumb,
.batch-delete-confirm-content::-webkit-scrollbar-thumb {
  background: var(--n-scrollbar-color);
  border-radius: 3px;
}

.item-list::-webkit-scrollbar-thumb:hover,
.invalid-items-list::-webkit-scrollbar-thumb:hover,
.batch-delete-confirm-content::-webkit-scrollbar-thumb:hover {
  background: var(--n-scrollbar-color-hover);
}
</style>
