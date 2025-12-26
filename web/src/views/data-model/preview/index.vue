<template>
  <div class="data-preview">
    <n-layout has-sider>
      <!-- 左侧：查询配置 -->
      <n-layout-sider
        bordered
        :width="350"
        :collapsed-width="0"
        show-trigger="arrow-circle"
        collapse-mode="width"
        :native-scrollbar="false"
        :collapsed="siderCollapsed"
        @update:collapsed="siderCollapsed = $event"
      >
        <div class="sider-content">
          <!-- 模型选择 -->
          <n-card title="模型选择" size="small" class="mb-3">
            <n-select
              v-model:value="selectedModelCode"
              placeholder="选择数据模型"
              :options="modelOptions"
              filterable
              :loading="modelsLoading"
              @update:value="handleModelChange"
            />
            
            <!-- 模型信息 -->
            <n-descriptions 
              v-if="selectedModel" 
              :column="1" 
              bordered
              size="small"
              class="mt-3"
            >
              <n-descriptions-item label="模型名称">
                {{ selectedModel.model_name }}
              </n-descriptions-item>
              <n-descriptions-item label="模型类型">
                <n-tag :type="getModelTypeTag(selectedModel.model_type)" size="small">
                  {{ getModelTypeLabel(selectedModel.model_type) }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="字段数量">
                {{ selectedModel.selected_fields?.length || 0 }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>

          <!-- 查询参数 -->
          <n-card title="查询参数" size="small" class="mb-3">
            <n-form
              ref="queryFormRef"
              :model="queryParams"
              label-placement="top"
              size="small"
            >
              <n-form-item label="设备编码">
                <n-input 
                  v-model:value="queryParams.device_code" 
                  placeholder="可选，留空查询所有设备"
                  clearable
                />
              </n-form-item>
              
              <n-form-item label="时间范围">
                <n-date-picker
                  v-model:value="queryParams.timeRange"
                  type="datetimerange"
                  clearable
                  style="width: 100%"
                />
              </n-form-item>
              
              <!-- 统计查询专用参数 -->
              <template v-if="isStatisticsModel">
                <n-form-item label="时间间隔">
                  <n-select
                    v-model:value="queryParams.interval"
                    placeholder="选择时间间隔"
                    :options="intervalOptions"
                  />
                </n-form-item>
                
                <n-form-item label="分组字段">
                  <n-select
                    v-model:value="queryParams.group_by"
                    placeholder="选择分组字段"
                    multiple
                    :options="groupByOptions"
                  />
                </n-form-item>
              </template>
              
              <!-- 分页参数 -->
              <n-form-item label="每页记录数">
                <n-input-number
                  v-model:value="queryParams.page_size"
                  :min="10"
                  :max="1000"
                  :step="10"
                  style="width: 100%"
                />
              </n-form-item>
            </n-form>
            
            <n-button 
              type="primary" 
              block 
              @click="handleQuery"
              :loading="querying"
              :disabled="!selectedModelCode"
            >
              <template #icon>
                <n-icon :component="SearchOutline" />
              </template>
              执行查询
            </n-button>
          </n-card>

          <!-- SQL预览 -->
          <n-card title="生成的SQL" size="small">
            <n-collapse>
              <n-collapse-item title="查看SQL" name="sql">
                <n-scrollbar style="max-height: 200px">
                  <n-code 
                    :code="generatedSQL || '暂无SQL'" 
                    language="sql"
                    :hljs="hljs"
                    word-wrap
                  />
                </n-scrollbar>
                <n-button 
                  text 
                  type="primary"
                  @click="handleCopySQL"
                  class="mt-2"
                  :disabled="!generatedSQL"
                >
                  <template #icon>
                    <n-icon :component="CopyOutline" />
                  </template>
                  复制SQL
                </n-button>
              </n-collapse-item>
            </n-collapse>
          </n-card>
        </div>
      </n-layout-sider>

      <!-- 右侧：查询结果 -->
      <n-layout-content :native-scrollbar="false">
        <div class="content-wrapper">
          <n-tabs type="line" animated>
            <!-- 表格视图 -->
            <n-tab-pane name="table" tab="表格视图">
              <n-card :bordered="false">
                <template #header>
                  <n-space align="center" justify="space-between">
                    <n-space align="center">
                      <n-button 
                        v-if="siderCollapsed" 
                        size="small" 
                        @click="siderCollapsed = false"
                        type="primary"
                        secondary
                      >
                        <template #icon>
                          <n-icon :component="FilterOutline" />
                        </template>
                        查询条件
                      </n-button>
                      <span>查询结果</span>
                    </n-space>
                    <n-space>
                      <n-tag v-if="queryResult" type="info">
                        共 {{ queryResult.total || 0 }} 条记录
                      </n-tag>
                      <n-tag v-if="executionTime" type="success">
                        耗时 {{ executionTime }}ms
                      </n-tag>
                      <n-button 
                        size="small" 
                        @click="handleExport"
                        :disabled="!queryResult?.data?.length"
                      >
                        <template #icon>
                          <n-icon :component="DownloadOutline" />
                        </template>
                        导出
                      </n-button>
                    </n-space>
                  </n-space>
                </template>
                
                <!-- 空状态提示 -->
                <n-empty 
                  v-if="!resultData.length && !querying && selectedModelCode"
                  description="暂无数据，请调整查询条件后重试"
                  class="empty-state"
                >
                  <template #icon>
                    <n-icon :component="SearchOutline" size="48" />
                  </template>
                  <template #extra>
                    <n-button size="small" @click="handleQuery">
                      重新查询
                    </n-button>
                  </template>
                </n-empty>
                
                <!-- 未选择模型提示 -->
                <n-empty 
                  v-else-if="!selectedModelCode && !querying"
                  description="请先选择数据模型并执行查询"
                  class="empty-state"
                >
                  <template #icon>
                    <n-icon :component="SearchOutline" size="48" />
                  </template>
                </n-empty>
                
                <!-- 数据表格 -->
                <n-data-table
                  v-else
                  remote
                  :columns="resultColumns"
                  :data="resultData"
                  :loading="querying"
                  :pagination="resultPagination"
                  :scroll-x="1200"
                  :max-height="500"
                  virtual-scroll
                  striped
                />
              </n-card>
            </n-tab-pane>
            
            <!-- 图表视图 (仅统计类型) -->
            <n-tab-pane 
              v-if="isStatisticsModel" 
              name="chart" 
              tab="图表视图"
            >
              <n-card :bordered="false">
                <div ref="chartRef" style="height: 500px"></div>
              </n-card>
            </n-tab-pane>
            
            <!-- 执行日志 -->
            <n-tab-pane name="logs" tab="执行日志">
              <n-card :bordered="false">
                <n-data-table
                  remote
                  :columns="logColumns"
                  :data="executionLogs"
                  :loading="logsLoading"
                  :pagination="logsPagination"
                />
              </n-card>
            </n-tab-pane>
          </n-tabs>
        </div>
      </n-layout-content>
    </n-layout>
    <n-modal v-model:show="showLogDetail" preset="card" title="日志详情" style="width: 800px">
      <n-scrollbar style="max-height: 600px">
        <n-descriptions bordered :column="2" v-if="currentLog">
          <n-descriptions-item label="日志ID">{{ currentLog.id }}</n-descriptions-item>
          <n-descriptions-item label="执行状态">
            <n-tag :type="currentLog.status === 'success' ? 'success' : 'error'" size="small">
              {{ currentLog.status }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="执行时间">{{ currentLog.executed_at }}</n-descriptions-item>
          <n-descriptions-item label="耗时">{{ currentLog.execution_time_ms }}ms</n-descriptions-item>
          <n-descriptions-item label="数据量">{{ currentLog.data_volume || '-' }}</n-descriptions-item>
          <n-descriptions-item label="执行人">{{ currentLog.executed_by || '-' }}</n-descriptions-item>
          
          <n-descriptions-item label="输入参数" :span="2">
            <n-code :code="JSON.stringify(currentLog.input_params, null, 2)" language="json" />
          </n-descriptions-item>
          
          <n-descriptions-item label="结果摘要" :span="2">
            <n-code :code="JSON.stringify(currentLog.result_summary, null, 2)" language="json" />
          </n-descriptions-item>
          
          <n-descriptions-item label="生成的SQL" :span="2" v-if="currentLog.generated_sql">
            <n-code :code="currentLog.generated_sql" language="sql" />
          </n-descriptions-item>
          
          <n-descriptions-item label="错误信息" :span="2" v-if="currentLog.error_message">
            <n-tag type="error">{{ currentLog.error_message }}</n-tag>
          </n-descriptions-item>
        </n-descriptions>
      </n-scrollbar>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, h, watch, nextTick } from 'vue'
import { NTag, NButton, NIcon, NEmpty, NCollapse, NCollapseItem, NScrollbar, useMessage, NModal, NDescriptions, NDescriptionsItem, NCode } from 'naive-ui'
import { SearchOutline, CopyOutline, DownloadOutline, FilterOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'
import { useResizeObserver } from '@vueuse/core'
import * as echarts from 'echarts'
import hljs from 'highlight.js/lib/core'
import sql from 'highlight.js/lib/languages/sql'

hljs.registerLanguage('sql', sql)

const message = useMessage()

// 布局状态
const siderCollapsed = ref(false)

// 模型选择
const modelOptions = ref([])
const modelsLoading = ref(false)
const selectedModelCode = ref(null)
const selectedModel = ref(null)

// 查询参数
const queryFormRef = ref(null)
const queryParams = reactive({
  device_code: '',
  timeRange: null,
  interval: '1h',
  group_by: [],
  page: 1,
  page_size: 50
})

// 时间间隔选项
const intervalOptions = [
  { label: '1分钟', value: '1m' },
  { label: '5分钟', value: '5m' },
  { label: '10分钟', value: '10m' },
  { label: '30分钟', value: '30m' },
  { label: '1小时', value: '1h' },
  { label: '1天', value: '1d' },
]

// 查询状态
const querying = ref(false)
const queryResult = ref(null)
const generatedSQL = ref('')
const executionTime = ref(null)

// 结果数据
const resultColumns = ref([])
const resultData = ref([])
const resultPagination = reactive({
  page: 1,
  pageSize: 50,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page) => {
    resultPagination.page = page
  }
})

// 执行日志
const executionLogs = ref([])
const logsLoading = ref(false)
const logsPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: false,
  onChange: (page) => {
    logsPagination.page = page
    fetchExecutionLogs()
  }
})

const showLogDetail = ref(false)
const currentLog = ref(null)

// 日志列定义
const logColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '执行时间',
    key: 'executed_at',
    width: 180
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const type = row.status === 'success' ? 'success' : 'error'
      return h(NTag, { type, size: 'small' }, { default: () => row.status })
    }
  },
  {
    title: '耗时',
    key: 'execution_time_ms',
    width: 100,
    render(row) {
      if (row.execution_time_ms == null) return '-'
      return `${row.execution_time_ms}ms`
    }
  },
  {
    title: '记录数',
    key: 'result_summary',
    width: 100,
    render(row) {
      if (!row.result_summary) return '-'
      const summary = typeof row.result_summary === 'string' 
        ? JSON.parse(row.result_summary) 
        : row.result_summary
      return summary?.returned_rows ?? '-'
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      return h(NButton, {
        size: 'small',
        text: true,
        onClick: () => handleViewLog(row.id)
      }, { default: () => '查看详情' })
    }
  }
]

// 图表
const chartRef = ref(null)
let chartInstance = null

// 计算属性
const isStatisticsModel = computed(() => {
  return selectedModel.value?.model_type === 'statistics'
})

const groupByOptions = computed(() => {
  if (!selectedModel.value?.selected_fields) {
    return []
  }
  return selectedModel.value.selected_fields.map(field => ({
    label: field.field_name || field.field_code,
    value: field.field_code
  }))
})

// 方法
const fetchModelList = async () => {
  modelsLoading.value = true
  try {
    const response = await dataModelApi.getAvailableModels({
      is_active: true
    })
    
    if (response.success) {
      const models = response.data || []
      modelOptions.value = models.map(model => ({
        label: `${model.model_name} (${model.model_code})`,
        value: model.model_code,
        model: model
      }))
    }
  } catch (error) {
    message.error('获取模型列表失败')
  } finally {
    modelsLoading.value = false
  }
}

const handleModelChange = (modelCode) => {
  const option = modelOptions.value.find(opt => opt.value === modelCode)
  if (option) {
    selectedModel.value = option.model
    
    // 动态生成表格列
    generateTableColumns()
  }
}

const generateTableColumns = () => {
  if (!selectedModel.value?.selected_fields) {
    resultColumns.value = []
    return
  }
  
  resultColumns.value = selectedModel.value.selected_fields.map(field => ({
    title: field.field_name || field.field_code,
    key: field.field_code,
    width: 120,
    ellipsis: {
      tooltip: true
    }
  }))
}

const handleQuery = async () => {
  if (!selectedModelCode.value) {
    message.warning('请先选择数据模型')
    return
  }
  
  querying.value = true
  const startTime = Date.now()
  
  try {
    // 构建查询参数
    const params = {
      model_code: selectedModelCode.value,
      device_code: queryParams.device_code || undefined,
      filters: {},
      page: resultPagination.page,
      page_size: queryParams.page_size
    }
    
    // 处理时间范围
    if (queryParams.timeRange && queryParams.timeRange.length === 2) {
      params.filters.start_time = new Date(queryParams.timeRange[0]).toISOString()
      params.filters.end_time = new Date(queryParams.timeRange[1]).toISOString()
    }
    
    // 根据模型类型选择API
    let response
    if (isStatisticsModel.value) {
      params.interval = queryParams.interval
      params.group_by = queryParams.group_by
      response = await dataModelApi.queryStatisticsData(params)
    } else {
      response = await dataModelApi.queryRealtimeData(params)
    }
    
    if (response.success) {
      queryResult.value = response
      resultData.value = response.data || []
      resultPagination.itemCount = response.meta?.total || response.total || 0
      generatedSQL.value = response.generated_sql || ''
      executionTime.value = Date.now() - startTime
      
      message.success('查询成功')
      
      // 如果是统计模型，绘制图表
      if (isStatisticsModel.value && resultData.value.length > 0) {
        nextTick(() => {
          renderChart()
        })
      }
      
      // 刷新执行日志
      fetchExecutionLogs()
    } else {
      message.error(response.message || '查询失败')
    }
  } catch (error) {
    message.error('查询失败：' + (error.message || '未知错误'))
  } finally {
    querying.value = false
  }
}

const handleCopySQL = () => {
  if (generatedSQL.value) {
    navigator.clipboard.writeText(generatedSQL.value)
    message.success('SQL已复制到剪贴板')
  }
}

const handleExport = () => {
  if (!resultData.value || resultData.value.length === 0) {
    message.warning('没有数据可导出')
    return
  }
  
  // 简单的CSV导出
  const headers = resultColumns.value.map(col => col.title).join(',')
  const rows = resultData.value.map(row => {
    return resultColumns.value.map(col => row[col.key] || '').join(',')
  })
  
  const csv = [headers, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${selectedModelCode.value}_${Date.now()}.csv`
  link.click()
  
  message.success('导出成功')
}

const renderChart = () => {
  if (!chartRef.value || !resultData.value.length) {
    return
  }
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  // 简单的折线图示例
  const xData = resultData.value.map((row, index) => row.time || `Point ${index + 1}`)
  const series = resultColumns.value.slice(0, 5).map(col => ({
    name: col.title,
    type: 'line',
    data: resultData.value.map(row => row[col.key])
  }))
  
  const option = {
    title: {
      text: '数据趋势图'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: series.map(s => s.name)
    },
    xAxis: {
      type: 'category',
      data: xData
    },
    yAxis: {
      type: 'value'
    },
    series: series
  }
  
  chartInstance.setOption(option)
}

const fetchExecutionLogs = async () => {
  if (!selectedModelCode.value) {
    return
  }
  
  logsLoading.value = true
  try {
    const response = await dataModelApi.getExecutionLogs({
      model_code: selectedModelCode.value,
      page: logsPagination.page,
      page_size: logsPagination.pageSize
    })
    
    if (response.success) {
      executionLogs.value = response.data || []
      logsPagination.itemCount = response.total || 0
      console.log('Execution Logs:', executionLogs.value)
    }
  } catch (error) {
    console.error('获取执行日志失败:', error)
  } finally {
    logsLoading.value = false
  }
}

const handleViewLog = (logId) => {
  const log = executionLogs.value.find(l => l.id === logId)
  if (log) {
    currentLog.value = log
    showLogDetail.value = true
  }
}

const getModelTypeLabel = (type) => {
  const map = {
    realtime: '实时监控',
    statistics: '统计分析',
    ai_analysis: 'AI分析'
  }
  return map[type] || type
}

const getModelTypeTag = (type) => {
  const map = {
    realtime: 'info',
    statistics: 'success',
    ai_analysis: 'warning'
  }
  return map[type] || 'default'
}

// 生命周期
onMounted(() => {
  fetchModelList()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

// 监听图表容器大小变化，自动调整
useResizeObserver(chartRef, () => {
  if (chartInstance) {
    chartInstance.resize()
  }
})
</script>

<style scoped>
.data-preview {
  height: calc(100vh - 100px);
}

.sider-content {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.content-wrapper {
  padding: 16px;
}

.empty-state {
  padding: 60px 0;
}

.mb-3 {
  margin-bottom: 16px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-3 {
  margin-top: 12px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .data-preview {
    height: auto;
  }
  
  .empty-state {
    padding: 40px 0;
  }
}
</style>

