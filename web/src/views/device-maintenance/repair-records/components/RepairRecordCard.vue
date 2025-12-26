<template>
  <div class="repair-record-card">
    <!-- 搜索栏 -->
    <div class="search-bar mb-4">
      <NForm inline :model="searchForm" label-placement="left">
        <NFormItem label="设备编号">
          <NInput
            v-model:value="searchForm.device_code"
            placeholder="请输入设备编号"
            clearable
            style="width: 180px"
          />
        </NFormItem>
        <NFormItem label="设备类型">
          <NSelect
            v-model:value="searchForm.device_type"
            :options="deviceTypeOptions"
            placeholder="请选择设备类型"
            clearable
            style="width: 180px"
          />
        </NFormItem>
        <NFormItem label="维修状态">
          <NSelect
            v-model:value="searchForm.repair_status"
            :options="statusOptions"
            placeholder="请选择维修状态"
            clearable
            style="width: 150px"
          />
        </NFormItem>
        <NFormItem label="申请人">
          <NInput
            v-model:value="searchForm.applicant"
            placeholder="请输入申请人"
            clearable
            style="width: 120px"
          />
        </NFormItem>
      </NForm>
    </div>

    <!-- 卡片网格 -->
    <div v-if="!loading && data.length > 0" class="card-grid">
      <div
        v-for="record in data"
        :key="record.id"
        class="record-card"
        :class="getRecordCardClass(record)"
      >
        <!-- 状态指示器 -->
        <div class="status-indicator" :class="getStatusIndicatorClass(record.repair_status)"></div>

        <!-- 维修记录头部信息 -->
        <div class="record-header">
          <div class="record-info">
            <h3 class="record-title">{{ record.repair_code || record.device_code }}</h3>
            <p class="record-subtitle">{{ record.device_type }} - {{ record.device_code }}</p>
          </div>
          <div class="record-badges">
            <NTag :type="getStatusTagType(record.repair_status)" size="small">
              {{ getStatusText(record.repair_status) }}
            </NTag>
            <NTag :type="getPriorityTagType(record.priority)" size="small" class="ml-2">
              {{ getPriorityText(record.priority) }}
            </NTag>
          </div>
        </div>

        <!-- 核心信息 -->
        <div class="info-section">
          <div class="info-row">
            <span class="info-label">📅 报修日期:</span>
            <span class="info-value">{{ record.repair_date }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">👤 申请人:</span>
            <span class="info-value">{{ record.applicant }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">🏢 申请部门:</span>
            <span class="info-value">{{ record.applicant_dept || '--' }}</span>
          </div>
        </div>

        <!-- 故障信息（简化） -->
        <div v-if="record.is_fault && record.fault_content" class="info-section fault-section">
          <div class="info-row">
            <span class="info-label">⚡ 故障内容:</span>
            <span class="info-value fault-content">{{ record.fault_content }}</span>
          </div>
        </div>

        <!-- 维修信息（简化） -->
        <div class="info-section repair-section">
          <div v-if="record.repairer" class="info-row">
            <span class="info-label">👷‍♂️ 维修人员:</span>
            <span class="info-value">{{ record.repairer }}</span>
          </div>
          <div v-if="record.repair_completion_date" class="info-row">
            <span class="info-label">✅ 完成日期:</span>
            <span class="info-value">{{ record.repair_completion_date }}</span>
          </div>
          <div v-if="record.repair_cost" class="info-row">
            <span class="info-label">💰 维修成本:</span>
            <span class="info-value cost-value">¥{{ record.repair_cost }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="record-actions">
          <PermissionButton
            permission="PUT /api/v2/device/maintenance/repair-records/{id}"
            size="small"
            type="primary"
            class="mr-8"
            no-permission-text="您没有权限编辑维修记录"
            @click="emit('edit', record)"
          >
            <TheIcon icon="material-symbols:edit-outline" :size="14" class="mr-4" />
            编辑
          </PermissionButton>
          <PermissionButton
            permission="DELETE /api/v2/device/maintenance/repair-records/{id}"
            size="small"
            type="error"
            :need-confirm="true"
            confirm-title="删除确认"
            confirm-content="确定删除该维修记录吗？此操作不可恢复。"
            no-permission-text="您没有权限删除维修记录"
            @confirm="() => emit('delete', [record.id])"
          >
            <TheIcon icon="material-symbols:delete-outline" :size="14" class="mr-4" />
            删除
          </PermissionButton>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <NSpin size="large">
        <div class="loading-text">正在加载维修记录...</div>
      </NSpin>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && data.length === 0" class="empty-state">
      <NEmpty description="暂无维修记录数据">
        <template #icon>
          <TheIcon icon="material-symbols:build-circle" :size="64" />
        </template>
      </NEmpty>
    </div>

    <!-- 分页组件 -->
    <div v-if="data.length > 0" class="mt-6 flex justify-center">
      <NPagination
        :page="pagination.page"
        :page-size="pagination.pageSize"
        :item-count="pagination.itemCount"
        :page-sizes="pagination.pageSizes"
        :show-size-picker="pagination.showSizePicker"
        :show-quick-jumper="pagination.showQuickJumper"
        :prefix="pagination.prefix"
        :suffix="pagination.suffix"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  NPagination,
  NEmpty,
  NSpin,
  NTag,
  NPopconfirm,
} from 'naive-ui'

import TheIcon from '@/components/icon/TheIcon.vue'
import StatusIndicator from '@/components/common/StatusIndicator.vue'
import { PermissionButton } from '@/components/Permission'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  pagination: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['edit', 'delete', 'page-change', 'page-size-change', 'search'])

// 搜索表单
const searchForm = ref({
  device_code: '',
  device_type: '',
  repair_status: '',
  applicant: '',
})

// 选项数据
const deviceTypeOptions = [
  { label: '焊机设备', value: 'welding' },
  { label: '切割设备', value: 'cutting' },
  { label: '其他设备', value: 'other' },
]

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

// 样式和状态处理函数
const getRecordCardClass = (record) => {
  const baseClass = 'record-card'
  if (record.is_fault) {
    return `${baseClass} record-card--fault`
  }
  return `${baseClass} record-card--normal`
}

const getStatusIndicatorClass = (status) => {
  const statusMap = {
    pending: 'status-indicator--pending',
    in_progress: 'status-indicator--progress',
    completed: 'status-indicator--completed',
    cancelled: 'status-indicator--cancelled',
  }
  return statusMap[status] || 'status-indicator--pending'
}

const getStatusTagType = (status) => {
  const statusMap = {
    pending: 'warning',
    in_progress: 'info',
    completed: 'success',
    cancelled: 'error',
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消',
  }
  return statusMap[status] || '未知'
}

const getPriorityTagType = (priority) => {
  const priorityMap = {
    low: 'default',
    medium: 'info',
    high: 'warning',
    urgent: 'error',
  }
  return priorityMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急',
  }
  return priorityMap[priority] || '中'
}

// 搜索处理
const handleSearch = () => {
  emit('search', { ...searchForm.value })
}

// 重置搜索
const handleReset = () => {
  searchForm.value = {
    device_code: '',
    device_type: '',
    repair_status: '',
    applicant: '',
  }
  emit('search', {})
}

// 分页处理
const handlePageChange = (page) => {
  emit('page-change', page)
}

const handlePageSizeChange = (pageSize) => {
  emit('page-size-change', pageSize)
}
</script>

<style scoped>
.repair-record-card {
  background: var(--n-color);
}

.search-bar {
  padding: 16px;
  background: var(--n-color-embedded);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
}

/* 卡片网格布局 */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 20px;
  padding: 16px 0;
}

/* 维修记录卡片样式 */
.record-card {
  position: relative;
  border-radius: 12px;
  padding: 20px;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  transition: all 0.2s ease;
  cursor: pointer;
}

.record-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px var(--n-box-shadow-color);
}

.record-card--fault {
  border-left: 4px solid var(--n-error-color);
}

.record-card--normal {
  border-left: 4px solid var(--n-success-color);
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator--pending {
  background: var(--n-warning-color);
  box-shadow: 0 0 0 4px var(--n-warning-color-hover);
}

.status-indicator--progress {
  background: var(--n-info-color);
  box-shadow: 0 0 0 4px var(--n-info-color-hover);
}

.status-indicator--completed {
  background: var(--n-success-color);
  box-shadow: 0 0 0 4px var(--n-success-color-hover);
}

.status-indicator--cancelled {
  background: var(--n-error-color);
  box-shadow: 0 0 0 4px var(--n-error-color-hover);
}

/* 维修记录头部信息 */
.record-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-right: 30px;
}

.record-info {
  flex: 1;
}

.record-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.record-subtitle {
  font-size: 14px;
  color: var(--n-text-color-2);
  margin: 0;
}

.record-badges {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 信息区域 */
.info-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 8px;
}

.fault-section {
  border-left: 3px solid var(--n-error-color);
}

.repair-section {
  border-left: 3px solid var(--n-success-color);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.4;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  color: var(--n-text-color-2);
  margin-right: 8px;
  min-width: 90px;
  font-weight: 500;
  flex-shrink: 0;
}

.info-value {
  color: var(--n-text-color);
  font-weight: 600;
  flex: 1;
  word-break: break-word;
}

.cost-value {
  color: var(--n-success-color);
  font-weight: 700;
}

/* 操作按钮 */
.record-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--n-divider-color);
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  padding: 60px 0;
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  color: var(--n-text-color-2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .record-card {
    padding: 16px;
  }

  .record-header {
    flex-direction: column;
    gap: 12px;
    padding-right: 0;
  }

  .record-badges {
    align-self: flex-start;
  }

  .search-bar :deep(.n-form-item) {
    margin-bottom: 12px;
  }

  .record-actions {
    flex-direction: column;
    gap: 8px;
  }

  .record-actions .n-button {
    width: 100%;
  }
}
</style>
