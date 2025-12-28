<template>
  <div class="decision-audit-page">
    <n-card title="决策审计日志" :bordered="false">
      <!-- 统计卡片 -->
      <n-grid :cols="4" :x-gap="16" class="stats-grid">
        <n-gi>
          <n-statistic label="总触发次数" :value="statistics.total" />
        </n-gi>
        <n-gi>
          <n-statistic label="成功次数" :value="statistics.success">
            <template #suffix>
              <n-tag type="success" size="small">{{ successRate }}%</n-tag>
            </template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="部分成功" :value="statistics.partial" />
        </n-gi>
        <n-gi>
          <n-statistic label="失败次数" :value="statistics.failed" />
        </n-gi>
      </n-grid>

      <n-divider />

      <!-- 筛选条件 -->
      <n-space class="filter-bar" :wrap="true">
        <n-input v-model:value="filters.rule_id" placeholder="规则ID" clearable style="width: 150px;" />
        <n-select v-model:value="filters.result" :options="resultOptions" placeholder="执行结果" clearable style="width: 120px;" />
        <n-date-picker 
          v-model:value="filters.dateRange" 
          type="datetimerange" 
          clearable 
          :default-time="['00:00:00', '23:59:59']"
          style="width: 350px;"
        />
        <n-button @click="loadAuditLogs">查询</n-button>
        <n-button @click="handleRefreshStats">刷新统计</n-button>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="auditLogs"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetailModal" preset="dialog" title="审计日志详情" style="width: 800px;">
      <template v-if="currentLog">
        <n-descriptions :column="2" label-placement="left" bordered>
          <n-descriptions-item label="日志ID">{{ currentLog.id }}</n-descriptions-item>
          <n-descriptions-item label="规则ID">{{ currentLog.rule_id }}</n-descriptions-item>
          <n-descriptions-item label="规则名称">{{ currentLog.rule_name }}</n-descriptions-item>
          <n-descriptions-item label="执行结果">
            <n-tag :type="resultTypeMap[currentLog.result]">{{ resultTextMap[currentLog.result] }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="触发时间">{{ formatTime(currentLog.trigger_time) }}</n-descriptions-item>
          <n-descriptions-item label="执行耗时">{{ currentLog.execution_duration_ms || '-' }} ms</n-descriptions-item>
          <n-descriptions-item label="资产ID">{{ currentLog.asset_id || '-' }}</n-descriptions-item>
          <n-descriptions-item label="预测ID">{{ currentLog.prediction_id || '-' }}</n-descriptions-item>
        </n-descriptions>

        <n-divider />

        <n-tabs type="line">
          <n-tab-pane name="trigger_data" tab="触发数据">
            <pre class="json-preview">{{ formatJson(currentLog.trigger_data) }}</pre>
          </n-tab-pane>
          <n-tab-pane name="conditions" tab="条件快照">
            <pre class="json-preview">{{ formatJson(currentLog.conditions_snapshot) }}</pre>
          </n-tab-pane>
          <n-tab-pane name="actions" tab="执行动作">
            <pre class="json-preview">{{ formatJson(currentLog.actions_executed) }}</pre>
          </n-tab-pane>
          <n-tab-pane v-if="currentLog.error_message" name="error" tab="错误信息">
            <n-alert type="error" :bordered="false">
              {{ currentLog.error_message }}
            </n-alert>
          </n-tab-pane>
        </n-tabs>
      </template>
      <template #action>
        <n-button @click="showDetailModal = false">关闭</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import { decisionApi } from '@/api/v3/platform'

const message = useMessage()

// 状态
const loading = ref(false)
const showDetailModal = ref(false)
const auditLogs = ref([])
const currentLog = ref(null)
const statistics = ref({
  total: 0,
  success: 0,
  partial: 0,
  failed: 0,
  success_rate: 0
})

// 筛选条件
const filters = reactive({
  rule_id: '',
  result: null,
  dateRange: null
})

const resultOptions = [
  { label: '成功', value: 'success' },
  { label: '部分成功', value: 'partial' },
  { label: '失败', value: 'failed' }
]

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0
})

// 结果类型映射
const resultTypeMap = {
  success: 'success',
  partial: 'warning',
  failed: 'error'
}

const resultTextMap = {
  success: '成功',
  partial: '部分成功',
  failed: '失败'
}

// 成功率
const successRate = computed(() => {
  if (statistics.value.total === 0) return 0
  return Math.round(statistics.value.success_rate * 100)
})

// 表格列定义
const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '规则ID', key: 'rule_id', width: 150 },
  { title: '规则名称', key: 'rule_name', width: 180 },
  {
    title: '执行结果',
    key: 'result',
    width: 100,
    render: row => h(NTag, { type: resultTypeMap[row.result] }, () => resultTextMap[row.result])
  },
  { 
    title: '触发时间', 
    key: 'trigger_time', 
    width: 180,
    render: row => formatTime(row.trigger_time)
  },
  { 
    title: '执行耗时', 
    key: 'execution_duration_ms', 
    width: 100,
    render: row => row.execution_duration_ms ? `${row.execution_duration_ms}ms` : '-'
  },
  { title: '资产ID', key: 'asset_id', width: 100 },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: row => h(NButton, { size: 'small', onClick: () => handleViewDetail(row) }, () => '详情')
  }
]

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

// 格式化JSON
const formatJson = (data) => {
  if (!data) return '-'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

// 加载审计日志
const loadAuditLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      rule_id: filters.rule_id || undefined,
      result: filters.result || undefined
    }
    
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = new Date(filters.dateRange[0]).toISOString()
      params.end_time = new Date(filters.dateRange[1]).toISOString()
    }
    
    const res = await decisionApi.getAuditLogs(params)
    auditLogs.value = res.data || []
    pagination.itemCount = res.total || 0
  } catch (error) {
    message.error('加载审计日志失败')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const params = {}
    if (filters.rule_id) {
      params.rule_id = filters.rule_id
    }
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_time = new Date(filters.dateRange[0]).toISOString()
      params.end_time = new Date(filters.dateRange[1]).toISOString()
    }
    
    const res = await decisionApi.getAuditStatistics(params)
    statistics.value = res.data || {
      total: 0,
      success: 0,
      partial: 0,
      failed: 0,
      success_rate: 0
    }
  } catch (error) {
    console.error('加载统计信息失败', error)
  }
}

// 刷新统计
const handleRefreshStats = () => {
  loadStatistics()
  message.success('统计信息已刷新')
}

// 分页处理
const handlePageChange = (page) => {
  pagination.page = page
  loadAuditLogs()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadAuditLogs()
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const res = await decisionApi.getAuditLog(row.id)
    currentLog.value = res.data
    showDetailModal.value = true
  } catch (error) {
    message.error('加载详情失败')
  }
}

onMounted(() => {
  loadAuditLogs()
  loadStatistics()
})
</script>

<style scoped>
.decision-audit-page {
  padding: 16px;
}

.stats-grid {
  margin-bottom: 16px;
}

.filter-bar {
  margin-bottom: 16px;
}

.json-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  max-height: 300px;
}
</style>
