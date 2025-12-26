<template>
  <div class="grouped-monitoring-data">
    <!-- 加载状态 -->
    <template v-if="loading">
      <div class="loading-skeleton">
        <NSkeleton text :repeat="3" style="margin-bottom: 8px" />
      </div>
    </template>

    <!-- 轮播图显示 -->
    <template v-else-if="carouselItems.length > 0">
      <!-- 分组标题和导航 -->
      <div class="carousel-header">
        <div class="group-navigation" @click.stop>
          <NButton
            text
            size="small"
            :disabled="currentIndex === 0"
            @click.stop="prevGroup"
            class="nav-btn"
          >
            <template #icon>
              <TheIcon icon="material-symbols:chevron-left" />
            </template>
          </NButton>
          
          <div class="group-info">
            <span v-if="currentGroup?.icon" class="group-icon">{{ currentGroup?.icon }}</span>
            <span class="group-title">{{ currentGroup?.title }}</span>
            <span class="group-count">({{ currentIndex + 1 }}/{{ carouselItems.length }})</span>
          </div>
          
          <NButton
            text
            size="small"
            :disabled="currentIndex === carouselItems.length - 1"
            @click.stop="nextGroup"
            class="nav-btn"
          >
            <template #icon>
              <TheIcon icon="material-symbols:chevron-right" />
            </template>
          </NButton>
        </div>
      </div>

      <!-- 轮播容器 -->
      <div class="carousel-container">
        <NCarousel
          ref="carouselRef"
          v-model:current-index="currentIndex"
          :show-dots="true"
          :show-arrow="false"
          :slides-per-view="1"
          :space-between="0"
          :autoplay="false"
          :touchable="true"
          dot-type="dot"
          dot-placement="bottom"
          class="monitoring-carousel"
        >
          <div
            v-for="item in carouselItems"
            :key="item.name"
            class="carousel-item"
          >
            <div class="field-list">
              <div v-for="field in item.fields" :key="field.field_code" class="data-row">
                <span class="data-label">
                  <span v-if="getFieldIcon(field)" class="field-icon">{{ getFieldIcon(field) }}</span>
                  {{ field.field_name }}:
                </span>
                <span 
                  class="data-value" 
                  :class="{ updated: fieldUpdateStatus[field.field_code] }"
                  :style="{ color: getFieldColor(field) }"
                >
                  {{ formatValue(realtimeData[field.field_code], field) }}
                </span>
              </div>
            </div>
          </div>
        </NCarousel>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <TheIcon icon="material-symbols:database-off-outline" :size="32" class="empty-icon" />
      <span class="empty-text">暂无监测数据</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NSkeleton, NButton, NCarousel } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

/**
 * 设备字段接口定义
 */
export interface DeviceField {
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
  field_group?: string
  is_default_visible?: boolean
  group_order?: number
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

// 字段更新状态，用于控制闪烁动画
const fieldUpdateStatus = ref<Record<string, boolean>>({})

// 监听实时数据变化，触发更新动画
watch(() => props.realtimeData, (newVal, oldVal) => {
  if (!oldVal) return
  
  // 遍历新数据，检查是否有变化
  Object.keys(newVal).forEach(key => {
    // 简单的值比较，如果是对象则忽略
    if (typeof newVal[key] !== 'object' && newVal[key] !== oldVal[key]) {
      // 标记为已更新
      fieldUpdateStatus.value[key] = true
      
      // 600ms后移除标记（对应CSS动画时间）
      setTimeout(() => {
        fieldUpdateStatus.value[key] = false
      }, 600)
    }
  })
}, { deep: true })

// 轮播相关
const carouselRef = ref()
const currentIndex = ref(0)

/**
 * 所有字段（按 sort_order 排序）
 */
const allFields = computed(() => {
  return [...props.monitoringFields].sort((a, b) => a.sort_order - b.sort_order)
})

/**
 * 按 field_group 分组所有字段
 * 优先使用 field_group 字段进行分组，如果没有则根据 is_default_visible 判断
 */
const groupedFields = computed(() => {
  const groups = new Map<string, { name: string; title: string; icon: string; fields: DeviceField[]; order: number }>()
  
  allFields.value.forEach(field => {
    // 1. 过滤：只展示监控关键字段
    if (!field.is_monitoring_key) return

    // 如果标记为不显示，直接跳过（兼容旧数据：undefined视为显示）
    if (field.is_default_visible === false) return

    // 2. 确定分组名称
    // 逻辑：如果设置了明确的分组（非default），则归入该分组；否则归入核心参数（Core）
    let groupName = 'core'
    
    if (field.field_group && field.field_group !== 'default') {
      groupName = field.field_group
    }
    
    if (!groups.has(groupName)) {
      groups.set(groupName, {
        name: groupName,
        title: getGroupTitle(groupName),
        icon: getGroupIcon(groupName),
        fields: [],
        order: groupName === 'core' ? 0 : (field.group_order || 999)
      })
    }
    groups.get(groupName)!.fields.push(field)
  })
  
  // 按 group_order 排序，核心参数始终在最前面
  return Array.from(groups.values())
    .sort((a, b) => {
      if (a.name === 'core') return -1
      if (b.name === 'core') return 1
      return a.order - b.order
    })
    .map(group => ({
      ...group,
      fields: group.fields.sort((a, b) => a.sort_order - b.sort_order)
    }))
})

/**
 * 轮播项目
 */
const carouselItems = computed(() => {
  return groupedFields.value.filter(group => group.fields.length > 0)
})

/**
 * 当前分组
 */
const currentGroup = computed(() => {
  return carouselItems.value[currentIndex.value]
})

/**
 * 上一个分组
 */
function prevGroup() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

/**
 * 下一个分组
 */
function nextGroup() {
  if (currentIndex.value < carouselItems.value.length - 1) {
    currentIndex.value++
  }
}

/**
 * 监听字段变化，重置到第一页
 */
watch(() => props.monitoringFields, () => {
  currentIndex.value = 0
}, { deep: true })

/**
 * 获取分组标题
 */
function getGroupTitle(groupName: string): string {
  const titles: Record<string, string> = {
    core: '核心参数',
    temperature: '温度参数',
    power: '功率参数',
    speed: '速度参数',
    dimension: '尺寸参数',
    other: '其他参数'
  }
  return titles[groupName] || groupName
}

/**
 * 获取分组图标
 * 注意：图标已从字典数据中移除，此处返回空字符串
 */
function getGroupIcon(groupName: string): string {
  // 不再使用硬编码图标，由字典数据控制
  return ''
}

/**
 * 格式化数值显示
 */
function formatValue(value: any, field: DeviceField): string {
  if (value === null || value === undefined || value === '') {
    return '--'
  }

  let formattedValue: string | number = value

  if (field.field_type === 'float') {
    const numValue = Number(value)
    if (!isNaN(numValue)) {
      formattedValue = numValue.toFixed(2)
    }
  } else if (field.field_type === 'int') {
    const numValue = Number(value)
    if (!isNaN(numValue)) {
      formattedValue = Math.round(numValue)
    }
  } else if (field.field_type === 'boolean') {
    formattedValue = value ? '是' : '否'
  } else {
    formattedValue = String(value)
  }

  if (field.unit) {
    return `${formattedValue} ${field.unit}`
  }

  return String(formattedValue)
}

/**
 * 获取字段图标
 */
function getFieldIcon(field: DeviceField): string {
  return field.display_config?.icon || ''
}

/**
 * 获取字段颜色
 */
function getFieldColor(field: DeviceField): string {
  return field.display_config?.color || '#333'
}
</script>

<style scoped lang="scss">
.grouped-monitoring-data {
  padding: 4px 0;
}

.loading-skeleton {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

// 轮播头部 - 紧凑版本 (60%高度)
.carousel-header {
  margin-bottom: 6px;
}

.group-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.nav-btn {
  padding: 4px !important;
  min-width: 24px !important;
  height: 24px !important;
  border-radius: 4px;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.8) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
  cursor: pointer;
  
  &:not(:disabled):hover {
    background: rgba(59, 130, 246, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
  }
  
  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
    background: rgba(0, 0, 0, 0.02) !important;
    border-color: transparent !important;
  }

  :deep(.n-icon) {
    font-size: 14px !important;
  }
}

.group-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  flex: 1;
  justify-content: center;

  .group-icon {
    font-size: 12px;
  }

  .group-title {
    font-weight: 600;
    color: #374151;
  }

  .group-count {
    font-size: 9px;
    color: #9ca3af;
    font-weight: 500;
  }
}

// 轮播容器 - 紧凑版本 (60%高度)
.carousel-container {
  position: relative;
  padding-bottom: 16px;
}

.monitoring-carousel {
  :deep(.n-carousel__dots) {
    bottom: 2px;
    gap: 4px;
  }
  
  :deep(.n-carousel__dot) {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.15);
    transition: all 0.2s ease;
  }
  
  :deep(.n-carousel__dot--active) {
    background: #3b82f6;
    width: 12px;
    border-radius: 2px;
  }

  :deep(.n-carousel__slides) {
    min-height: 60px;
  }
}

.carousel-item {
  padding: 6px 8px;
  background: #fafafa;
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  min-height: 50px;
  transition: all 0.2s ease;
  
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  line-height: 1.4;
  padding: 3px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
  background: transparent;

  &:hover {
    background: rgba(59, 130, 246, 0.05);
  }
}

.data-label {
  color: #6b7280;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;

  .field-icon {
    font-size: 11px;
    line-height: 1;
  }
}

.data-value {
  font-weight: 600;
  font-size: 11px;
  font-family: 'Monaco', 'Consolas', monospace;
  color: #1f2937;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 10px;
  color: #9ca3af;
  text-align: center;
  background: #f9fafb;
  border-radius: 6px;

  .empty-icon {
    margin-bottom: 6px;
    opacity: 0.4;
    color: #d1d5db;
    animation: emptyPulse 3s ease-in-out infinite;
  }

  .empty-text {
    font-size: 10px;
    font-weight: 500;
    opacity: 0.6;
  }
}

// 响应式设计 - 紧凑版本
@media (max-width: 768px) {
  .carousel-item {
    padding: 4px 6px;
  }

  .data-row {
    font-size: 9px;
    padding: 2px 4px;
  }

  .data-value {
    font-size: 10px;
  }
  
  .group-navigation {
    padding: 3px 6px;
  }
  
  .group-info {
    font-size: 10px;
    gap: 4px;
    
    .group-icon {
      font-size: 10px;
    }
  }
}

// 深色模式适配
:deep(.dark) {
  .group-navigation {
    background: linear-gradient(135deg, rgba(24, 144, 255, 0.12) 0%, rgba(24, 144, 255, 0.05) 100%);
    border-color: rgba(24, 144, 255, 0.25);
  }
  
  .group-info {
    color: #fff;
    
    .group-count {
      background: rgba(255, 255, 255, 0.1);
      color: #ccc;
    }
  }
  
  .carousel-item {
    background: rgba(255, 255, 255, 0.02);
    border-color: rgba(255, 255, 255, 0.1);
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      border-color: rgba(24, 144, 255, 0.4);
    }
  }

  .data-row {
    border-bottom-color: rgba(255, 255, 255, 0.05);
    
    &:hover {
      background: rgba(24, 144, 255, 0.08);
    }
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
  
  .monitoring-carousel {
    :deep(.n-carousel__dot) {
      background: rgba(255, 255, 255, 0.2);
    }
    
    :deep(.n-carousel__dot--active) {
      background: #1890ff;
    }
  }
}

// 动画效果 - 美化版本
.carousel-item {
  animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// 数据行入场动画
.data-row {
  animation: slideInRight 0.4s ease-out;
  animation-fill-mode: both;
  
  @for $i from 1 through 10 {
    &:nth-child(#{$i}) {
      animation-delay: #{$i * 0.05}s;
    }
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

// 数据值闪烁效果（数据更新时）
.data-value {
  transition: all 0.3s ease;
  
  &.updated {
    animation: valueFlash 0.6s ease;
  }
}

@keyframes valueFlash {
  0% {
    background: rgba(59, 130, 246, 0.3);
    transform: scale(1.05);
  }
  100% {
    background: rgba(0, 0, 0, 0.03);
    transform: scale(1);
  }
}

// 悬浮时的光效
.carousel-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 14px 14px 0 0;
}

.carousel-item:hover::before {
  opacity: 1;
}

.carousel-item {
  position: relative;
  overflow: hidden;
}
</style>
