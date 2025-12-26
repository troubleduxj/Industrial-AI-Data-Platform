<template>
  <div class="monitoring-data">
    <!-- 加载状态 -->
    <template v-if="loading">
      <div v-for="n in 4" :key="n" class="data-row">
        <NSkeleton text :repeat="1" style="width: 100%; height: 20px" />
      </div>
    </template>

    <!-- 动态渲染监测参数 -->
    <template v-else>
      <div v-for="field in sortedFields" :key="field.field_code" class="data-row">
        <span class="data-label">
          <span v-if="getFieldIcon(field)" class="field-icon">{{ getFieldIcon(field) }}</span>
          {{ field.field_name }}:
        </span>
        <span class="data-value" :style="{ color: getFieldColor(field) }">
          {{ formatValue(realtimeData[field.field_code], field) }}
        </span>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="!loading && sortedFields.length === 0" class="empty-state">
      <span class="empty-text">暂无监测数据</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NSkeleton } from 'naive-ui'

/**
 * 设备字段接口定义
 */
interface DeviceField {
  id: number
  device_type_code: string
  field_name: string
  field_code: string
  field_type: 'float' | 'int' | 'string' | 'boolean'
  unit?: string
  sort_order: number
  display_config?: {
    icon?: string
    color?: string
    chart_type?: string
  }
  field_category?: string
  description?: string
}

/**
 * 组件 Props
 */
interface Props {
  monitoringFields: DeviceField[]
  realtimeData: Record<string, any>
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

/**
 * 按 sort_order 排序的字段列表
 */
const sortedFields = computed(() => {
  return [...props.monitoringFields].sort((a, b) => a.sort_order - b.sort_order)
})

/**
 * 格式化数值显示
 * @param value 原始值
 * @param field 字段配置
 * @returns 格式化后的字符串
 */
function formatValue(value: any, field: DeviceField): string {
  // 空值处理
  if (value === null || value === undefined || value === '') {
    return '--'
  }

  // 根据字段类型格式化
  let formattedValue: string | number = value

  if (field.field_type === 'float') {
    // float 类型保留2位小数
    const numValue = Number(value)
    if (!isNaN(numValue)) {
      formattedValue = numValue.toFixed(2)
    }
  } else if (field.field_type === 'int') {
    // int 类型取整
    const numValue = Number(value)
    if (!isNaN(numValue)) {
      formattedValue = Math.round(numValue)
    }
  } else if (field.field_type === 'boolean') {
    // boolean 类型转换为中文
    formattedValue = value ? '是' : '否'
  } else {
    // string 类型直接显示
    formattedValue = String(value)
  }

  // 添加单位
  if (field.unit) {
    return `${formattedValue} ${field.unit}`
  }

  return String(formattedValue)
}

/**
 * 获取字段图标
 * @param field 字段配置
 * @returns 图标字符串
 */
function getFieldIcon(field: DeviceField): string {
  return field.display_config?.icon || ''
}

/**
 * 获取字段颜色
 * @param field 字段配置
 * @returns 颜色值
 */
function getFieldColor(field: DeviceField): string {
  return field.display_config?.color || '#333'
}
</script>

<style scoped lang="scss">
.monitoring-data {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 0;
  min-height: 80px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  line-height: 1.5;
  padding: 4px 0;

  &:hover {
    background-color: rgba(0, 0, 0, 0.02);
    border-radius: 4px;
    padding: 4px 8px;
    margin: 0 -8px;
  }
}

.data-label {
  color: #666;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;

  .field-icon {
    font-size: 14px;
    line-height: 1;
  }
}

.data-value {
  font-weight: 600;
  font-size: 14px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
  color: #999;
  font-size: 13px;

  .empty-text {
    opacity: 0.6;
  }
}

// 深色模式适配
:deep(.dark) {
  .data-row:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }

  .data-label {
    color: #aaa;
  }

  .data-value {
    color: #fff;
  }

  .empty-state {
    color: #666;
  }
}
</style>
