<template>
  <CommonPage show-footer title="报警记录管理">
    <!-- 统计卡片 -->
    <div class="stats-row mb-15">
      <NCard size="small" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon active">
            <TheIcon icon="material-symbols:warning" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.by_status?.active || 0 }}</div>
            <div class="stat-label">活跃报警</div>
          </div>
        </div>
      </NCard>
      <NCard size="small" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon acknowledged">
            <TheIcon icon="material-symbols:check-circle" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.by_status?.acknowledged || 0 }}</div>
            <div class="stat-label">已确认</div>
          </div>
        </div>
      </NCard>
      <NCard size="small" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon resolved">
            <TheIcon icon="material-symbols:task-alt" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.by_status?.resolved || 0 }}</div>
            <div class="stat-label">已解决</div>
          </div>
        </div>
      </NCard>
      <NCard size="small" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total">
            <TheIcon icon="material-symbols:analytics" :size="24" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total || 0 }}</div>
            <div class="stat-label">总计</div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 搜索栏 -->
    <NCard class="mb-15" size="small">
      <div class="flex flex-wrap items-center gap-15">
        <QueryBarItem label="设备编码" :label-width="70">
          <NInput
            v-model:value="queryParams.device_code"
            placeholder="设备编码"
            clearable
            style="width: 140px"
          />
        </QueryBarItem>
        <QueryBarItem label="报警级别" :label-width="70">
          <NSelect
            v-model:value="queryParams.alarm_level"
            :options="alarmLevelOptions"
            placeholder="全部级别"
            clearable
            style="width: 120px"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryParams.status"
            :options="statusOptions"
            placeholder="全部状态"
            clearable
            style="width: 120px"
          />
        </QueryBarItem>
        <QueryBarItem label="时间范围" :label-width="70">
          <NDatePicker
            v-model:value="dateRange"
            type="daterange"
            clearable
            style="width: 260px"
          />
        </QueryBarItem>
        <NButton type="primary" @click="loadData">
          <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
          查询
        </NButton>
        <NButton @click="handleReset">
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
          重置
        </NButton>
      </div>
    </NCard>

    <!-- 报警记录列表 -->
    <NCard>
      <template #header>
        <div class="flex justify-between items-center">
          <span>报警记录列表</span>
          <div class="flex gap-10">
            <NButton
              v-if="selectedRows.length > 0"
              size="small"
              type="warning"
              @click="handleBatchAcknowledge"
            >
              批量确认 ({{ selectedRows.length }})
            </NButton>
            <NButton
              v-if="selectedRows.length > 0"
              size="small"
              type="success"
              @click="handleBatchResolve"
            >
              批量解决 ({{ selectedRows.length }})
            </NButton>
          </div>
        </div>
      </template>

      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="tableData"
          :pagination="pagination"
          :bordered="false"
          :single-line="false"
          :row-key="(row) => row.id"
          :checked-row-keys="selectedRowKeys"
          @update:checked-row-keys="handleSelectionChange"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </NSpin>
    </NCard>

    <!-- 详情弹窗 -->
    <NModal
      v-model:show="detailModalVisible"
      title="报警详情"
      preset="card"
      style="width: 700px"
    >
      <div v-if="currentRecord" class="alarm-detail">
        <NDescriptions :column="2" bordered>
          <NDescriptionsItem label="报警标题" :span="2">
            {{ currentRecord.alarm_title }}
          </NDescriptionsItem>
          <NDescriptionsItem label="设备编码">
            {{ currentRecord.device_code }}
          </NDescriptionsItem>
          <NDescriptionsItem label="设备名称">
            {{ currentRecord.device_name || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="报警级别">
            <NTag :type="getLevelTagType(currentRecord.alarm_level)" size="small">
              {{ getLevelLabel(currentRecord.alarm_level) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="状态">
            <NTag :type="getStatusTagType(currentRecord.status)" size="small">
              {{ getStatusLabel(currentRecord.status) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="触发字段">
            {{ currentRecord.field_name || currentRecord.field_code || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="触发值">
            {{ currentRecord.trigger_value ?? '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="触发时间">
            {{ formatTime(currentRecord.triggered_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="持续时间">
            {{ formatDuration(currentRecord.duration_seconds) }}
          </NDescriptionsItem>
          <NDescriptionsItem label="报警内容" :span="2">
            {{ currentRecord.alarm_content || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="currentRecord.acknowledged_at" label="确认时间">
            {{ formatTime(currentRecord.acknowledged_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="currentRecord.acknowledged_by_name" label="确认人">
            {{ currentRecord.acknowledged_by_name }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="currentRecord.resolved_at" label="解决时间">
            {{ formatTime(currentRecord.resolved_at) }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="currentRecord.resolved_by_name" label="解决人">
            {{ currentRecord.resolved_by_name }}
          </NDescriptionsItem>
          <NDescriptionsItem v-if="currentRecord.resolution_notes" label="解决备注" :span="2">
            {{ currentRecord.resolution_notes }}
          </NDescriptionsItem>
        </NDescriptions>
      </div>
      <template #footer>
        <div class="flex justify-end gap-10">
          <NButton @click="detailModalVisible = false">关闭</NButton>
          <NButton
            v-if="currentRecord?.status === 'active'"
            type="warning"
            @click="handleAcknowledge(currentRecord)"
          >
            确认报警
          </NButton>
          <NButton
            v-if="currentRecord?.status === 'active' || currentRecord?.status === 'acknowledged'"
            type="success"
            @click="handleResolve(currentRecord)"
          >
            解决报警
          </NButton>
        </div>
      </template>
    </NModal>

    <!-- 解决报警弹窗 -->
    <NModal
      v-model:show="resolveModalVisible"
      title="解决报警"
      preset="card"
      style="width: 500px"
    >
      <NForm>
        <NFormItem label="解决备注">
          <NInput
            v-model:value="resolveNotes"
            type="textarea"
            placeholder="请输入解决备注（可选）"
            :rows="3"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <div class="flex justify-end gap-10">
          <NButton @click="resolveModalVisible = false">取消</NButton>
          <NButton type="primary" :loading="resolving" @click="confirmResolve">确认解决</NButton>
        </div>
      </template>
    </NModal>
  </CommonPage>
</template>

<script setup>
import { ref, reactive, h, onMounted, computed } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NTag,
  NDatePicker,
  NDescriptions,
  NDescriptionsItem,
  NSpin,
  useMessage,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { alarmRecordsApi, AlarmStatusOptions } from '@/api/alarm-records'
import { AlarmLevelOptions } from '@/api/alarm-rules'
import { formatDate } from '@/utils'

const message = useMessage()

// 状态
const loading = ref(false)
const resolving = ref(false)
const tableData = ref([])
const statistics = ref({})
const detailModalVisible = ref(false)
const resolveModalVisible = ref(false)
const currentRecord = ref(null)
const resolveNotes = ref('')
const selectedRowKeys = ref([])
const selectedRows = ref([])
const dateRange = ref(null)

// 查询参数
const queryParams = reactive({
  device_code: '',
  alarm_level: null,
  status: null,
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

// 选项
const alarmLevelOptions = [
  { label: '全部', value: null },
  ...AlarmLevelOptions.map(item => ({ label: item.label, value: item.value }))
]

const statusOptions = [
  { label: '全部', value: null },
  ...AlarmStatusOptions.map(item => ({ label: item.label, value: item.value }))
]

// 表格列定义
const columns = [
  { type: 'selection' },
  { title: '报警标题', key: 'alarm_title', width: 200, ellipsis: { tooltip: true } },
  { title: '设备编码', key: 'device_code', width: 140 },
  {
    title: '报警级别',
    key: 'alarm_level',
    width: 90,
    render: (row) => h(NTag, { type: getLevelTagType(row.alarm_level), size: 'small' }, () => getLevelLabel(row.alarm_level))
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render: (row) => h(NTag, { type: getStatusTagType(row.status), size: 'small' }, () => getStatusLabel(row.status))
  },
  { title: '触发字段', key: 'field_name', width: 100 },
  { title: '触发值', key: 'trigger_value', width: 80 },
  {
    title: '触发时间',
    key: 'triggered_at',
    width: 160,
    render: (row) => formatTime(row.triggered_at)
  },
  {
    title: '持续时间',
    key: 'duration_seconds',
    width: 100,
    render: (row) => formatDuration(row.duration_seconds)
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render: (row) => h('div', { class: 'flex gap-5' }, [
      h(NButton, { size: 'small', onClick: () => handleViewDetail(row) }, () => '详情'),
      row.status === 'active' && h(NButton, { size: 'small', type: 'warning', onClick: () => handleAcknowledge(row) }, () => '确认'),
      (row.status === 'active' || row.status === 'acknowledged') && h(NButton, { size: 'small', type: 'success', onClick: () => handleResolve(row) }, () => '解决'),
    ].filter(Boolean))
  },
]

// 辅助方法
const getLevelTagType = (level) => {
  const map = { info: 'default', warning: 'warning', critical: 'error', emergency: 'error' }
  return map[level] || 'default'
}

const getLevelLabel = (level) => {
  const item = AlarmLevelOptions.find(l => l.value === level)
  return item?.label || level
}

const getStatusTagType = (status) => {
  const map = { active: 'error', acknowledged: 'warning', resolved: 'success', closed: 'default' }
  return map[status] || 'default'
}

const getStatusLabel = (status) => {
  const item = AlarmStatusOptions.find(s => s.value === status)
  return item?.label || status
}

const formatTime = (time) => {
  if (!time) return '-'
  return formatDate(time, 'YYYY-MM-DD HH:mm:ss')
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${mins}分`
}

// 数据加载
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryParams,
    }
    
    // 处理时间范围
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = new Date(dateRange.value[0]).toISOString()
      params.end_time = new Date(dateRange.value[1]).toISOString()
    }
    
    // 清理空值
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') delete params[key]
    })

    const res = await alarmRecordsApi.list(params)
    if (res.success && res.data) {
      tableData.value = res.data.items || res.data || []
      pagination.itemCount = res.data.total || tableData.value.length
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    const res = await alarmRecordsApi.statistics()
    if (res.success && res.data) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 事件处理
const handleReset = () => {
  queryParams.device_code = ''
  queryParams.alarm_level = null
  queryParams.status = null
  dateRange.value = null
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadData()
}

const handleSelectionChange = (keys) => {
  selectedRowKeys.value = keys
  selectedRows.value = tableData.value.filter(row => keys.includes(row.id))
}

const handleViewDetail = (row) => {
  currentRecord.value = row
  detailModalVisible.value = true
}

const handleAcknowledge = async (row) => {
  try {
    const res = await alarmRecordsApi.acknowledge(row.id)
    if (res.success) {
      message.success('报警已确认')
      loadData()
      loadStatistics()
      if (detailModalVisible.value) {
        detailModalVisible.value = false
      }
    }
  } catch (error) {
    console.error('确认失败:', error)
    message.error('确认失败')
  }
}

const handleResolve = (row) => {
  currentRecord.value = row
  resolveNotes.value = ''
  resolveModalVisible.value = true
}

const confirmResolve = async () => {
  resolving.value = true
  try {
    const res = await alarmRecordsApi.resolve(currentRecord.value.id, {
      resolution_notes: resolveNotes.value
    })
    if (res.success) {
      message.success('报警已解决')
      resolveModalVisible.value = false
      detailModalVisible.value = false
      loadData()
      loadStatistics()
    }
  } catch (error) {
    console.error('解决失败:', error)
    message.error('解决失败')
  } finally {
    resolving.value = false
  }
}

const handleBatchAcknowledge = async () => {
  try {
    const activeIds = selectedRows.value.filter(r => r.status === 'active').map(r => r.id)
    if (activeIds.length === 0) {
      message.warning('没有可确认的报警')
      return
    }
    const res = await alarmRecordsApi.batchHandle({
      record_ids: activeIds,
      action: 'acknowledge'
    })
    if (res.success) {
      message.success(res.message || '批量确认成功')
      selectedRowKeys.value = []
      selectedRows.value = []
      loadData()
      loadStatistics()
    }
  } catch (error) {
    console.error('批量确认失败:', error)
    message.error('批量确认失败')
  }
}

const handleBatchResolve = async () => {
  try {
    const validIds = selectedRows.value.filter(r => ['active', 'acknowledged'].includes(r.status)).map(r => r.id)
    if (validIds.length === 0) {
      message.warning('没有可解决的报警')
      return
    }
    const res = await alarmRecordsApi.batchHandle({
      record_ids: validIds,
      action: 'resolve'
    })
    if (res.success) {
      message.success(res.message || '批量解决成功')
      selectedRowKeys.value = []
      selectedRows.value = []
      loadData()
      loadStatistics()
    }
  } catch (error) {
    console.error('批量解决失败:', error)
    message.error('批量解决失败')
  }
}

// 初始化
onMounted(() => {
  loadData()
  loadStatistics()
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.active {
  background: linear-gradient(135deg, #f56c6c 0%, #c45656 100%);
}

.stat-icon.acknowledged {
  background: linear-gradient(135deg, #e6a23c 0%, #d48806 100%);
}

.stat-icon.resolved {
  background: linear-gradient(135deg, #67c23a 0%, #389e0d 100%);
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff 0%, #096dd9 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.alarm-detail {
  padding: 10px 0;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
