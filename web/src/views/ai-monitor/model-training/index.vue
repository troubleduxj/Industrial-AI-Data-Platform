<template>
  <div class="model-training-lab">
    <n-card>
      <n-tabs v-model:value="activeTab" type="line" animated>
        <!-- 训练任务列表 -->
        <n-tab-pane name="tasks" tab="训练任务">
          <n-space vertical>
            <n-space justify="space-between">
              <n-input placeholder="搜索任务ID或模型名称" style="width: 300px">
                <template #prefix>
                  <n-icon><SearchOutline /></n-icon>
                </template>
              </n-input>
              <n-button type="primary" @click="activeTab = 'create'">
                <template #icon>
                  <n-icon><AddOutline /></n-icon>
                </template>
                新建训练任务
              </n-button>
            </n-space>

            <n-data-table
              :columns="columns"
              :data="tasks"
              :loading="loading"
              :pagination="pagination"
            />
          </n-space>
        </n-tab-pane>

        <!-- 新建训练向导 -->
        <n-tab-pane name="create" tab="新建训练">
          <n-steps :current="currentStep" status="process">
            <n-step title="选择数据" description="选择设备与时间范围" />
            <n-step title="配置算法" description="选择算法与超参数" />
            <n-step title="开始训练" description="启动与监控" />
          </n-steps>

          <div class="step-content">
            <!-- 步骤1: 数据选择 -->
            <div v-if="currentStep === 1">
              <n-form label-placement="left" label-width="100px" style="max-width: 600px; margin: 0 auto">
                <n-form-item label="设备类型">
                  <n-select 
                    v-model:value="trainConfig.deviceType" 
                    :options="deviceTypeOptions" 
                    placeholder="请选择设备类型" 
                    @update:value="handleDeviceTypeChange"
                  />
                </n-form-item>
                <n-form-item label="设备">
                  <n-select 
                    v-model:value="trainConfig.device" 
                    :options="deviceOptions" 
                    placeholder="请选择设备" 
                    filterable
                    :disabled="!trainConfig.deviceType"
                  />
                </n-form-item>
                <n-form-item label="时间范围">
                  <n-date-picker 
                    v-model:value="trainConfig.dateRange" 
                    type="datetimerange" 
                    clearable 
                    @update:value="handleDateRangeChange"
                  />
                </n-form-item>
                <n-form-item label="数据预览">
                  <n-card size="small" title="数据分布概览" style="width: 100%">
                    <template #header-extra>
                      <n-button size="small" type="primary" secondary @click="fetchPreviewData" :disabled="!canPreview">
                        <template #icon><n-icon><BarChartOutline /></n-icon></template>
                        加载数据
                      </n-button>
                    </template>
                    <div style="height: 300px; width: 100%">
                      <AIChart
                        v-if="chartOption"
                        :option="chartOption"
                        :data="chartData"
                        :loading="previewLoading"
                        :height="280"
                        title=""
                      />
                      <div v-else-if="previewLoading" style="height: 100%; display: flex; justify-content: center; align-items: center;">
                        <n-spin description="加载中..." />
                      </div>
                      <div v-else style="height: 100%; display: flex; justify-content: center; align-items: center; color: #999">
                        <n-empty description="请选择设备和时间范围后点击加载" />
                      </div>
                    </div>
                  </n-card>
                </n-form-item>
              </n-form>
              <n-space justify="center" style="margin-top: 24px">
                <n-button type="primary" @click="nextStep">下一步</n-button>
              </n-space>
            </div>

            <!-- 步骤2: 算法配置 -->
            <div v-if="currentStep === 2">
              <n-form label-placement="left" label-width="120px" style="max-width: 600px; margin: 0 auto">
                <n-form-item label="模型名称" required>
                  <n-input v-model:value="trainConfig.modelName" placeholder="请输入模型名称" />
                </n-form-item>
                <n-form-item label="任务类型">
                  <n-select v-model:value="trainConfig.type" :options="typeOptions" />
                </n-form-item>
                <n-form-item label="算法选择">
                  <n-select v-model:value="trainConfig.algorithm" :options="algorithmOptions" filterable tag />
                </n-form-item>
                <n-form-item label="框架">
                  <n-select v-model:value="trainConfig.framework" :options="frameworkOptions" filterable tag />
                </n-form-item>
                <n-divider>超参数配置</n-divider>
                <n-dynamic-input v-model:value="trainConfig.parameters" preset="pair" key-placeholder="参数名" value-placeholder="参数值" />
              </n-form>
              <n-space justify="center" style="margin-top: 24px">
                <n-button @click="prevStep">上一步</n-button>
                <n-button type="primary" @click="nextStep">下一步</n-button>
              </n-space>
            </div>

            <!-- 步骤3: 确认与启动 -->
            <div v-if="currentStep === 3">
              <n-result status="info" title="准备就绪" description="请确认以下训练配置信息">
                <template #footer>
                  <n-descriptions label-placement="left" bordered :column="1" style="max-width: 500px; margin: 0 auto; text-align: left">
                    <n-descriptions-item label="设备">{{ selectedDeviceName }}</n-descriptions-item>
                    <n-descriptions-item label="算法">{{ trainConfig.algorithm }} ({{ trainConfig.framework }})</n-descriptions-item>
                    <n-descriptions-item label="参数数量">{{ trainConfig.parameters.length }}</n-descriptions-item>
                  </n-descriptions>
                  <n-space justify="center" style="margin-top: 24px">
                    <n-button @click="prevStep">上一步</n-button>
                    <n-button type="primary" :loading="starting" @click="startTraining">启动训练</n-button>
                  </n-space>
                </template>
              </n-result>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
  
  <!-- 任务详情抽屉 -->
  <n-drawer v-model:show="showDetails" width="500">
    <n-drawer-content title="训练任务详情">
      <div v-if="currentTask">
        <n-descriptions bordered :column="1" label-placement="left">
          <n-descriptions-item label="任务ID">{{ currentTask.id }}</n-descriptions-item>
          <n-descriptions-item label="模型名称">{{ currentTask.model_name }}</n-descriptions-item>
          <n-descriptions-item label="算法">{{ currentTask.algorithm }}</n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="currentTask.status === 'running' ? 'success' : (currentTask.status === 'completed' ? 'info' : 'default')">
              {{ currentTask.status }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="开始时间">{{ currentTask.start_time }}</n-descriptions-item>
          <n-descriptions-item label="耗时">{{ currentTask.duration }}</n-descriptions-item>
        </n-descriptions>

        <n-divider title-placement="left">训练日志</n-divider>
        
        <div class="log-container" style="background: #1e1e1e; padding: 12px; border-radius: 4px; height: 300px; overflow: hidden;">
          <n-log
            :log="currentTaskLogs"
            :loading="loadingLogs"
            trim
            language="log"
            :rows="20"
          />
        </div>
        <n-space justify="end" style="margin-top: 8px">
          <n-button size="small" @click="fetchTaskLogs">刷新日志</n-button>
        </n-space>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { ref, h, onMounted, onUnmounted, computed, watch } from 'vue'
import {
  NCard, NTabs, NTabPane, NSpace, NInput, NButton, NIcon, NDataTable, NTag,
  NSteps, NStep, NForm, NFormItem, NSelect, NDatePicker, NDivider, NDynamicInput,
  NResult, NDescriptions, NDescriptionsItem, useMessage, NSpin, NEmpty,
  NDrawer, NDrawerContent, NTimeline, NTimelineItem, NProgress, NPopconfirm, NLog
} from 'naive-ui'
import { SearchOutline, AddOutline, PlayCircleOutline, StopCircleOutline, BarChartOutline } from '@vicons/ionicons5'
import { modelManagementApi } from '@/api/v2/ai-module'
import { deviceTypeApi, deviceApi, compatibilityApi } from '@/api/device-v2'
import AIChart from '@/components/ai-monitor/charts/AIChart.vue'

const message = useMessage()
const activeTab = ref('tasks')
const loading = ref(false)
const tasks = ref([])
const showDetails = ref(false)
const currentTask = ref(null)
const currentTaskLogs = ref('')
const loadingLogs = ref(false)
let logTimer = null

watch(showDetails, (val) => {
  if (val) {
    fetchTaskLogs()
    logTimer = setInterval(fetchTaskLogs, 3000)
  } else {
    if (logTimer) {
      clearInterval(logTimer)
      logTimer = null
    }
  }
})

const fetchTaskLogs = async () => {
  if (!currentTask.value?.id) return
  
  // Don't show loading spinner for background updates
  if (!logTimer) loadingLogs.value = true
  
  try {
    const res = await modelManagementApi.getLogs(currentTask.value.id)
    currentTaskLogs.value = res.data.logs || '暂无日志'
  } catch (error) {
    console.error('获取日志失败:', error)
    // Don't overwrite logs with error message during polling to avoid flickering
    if (!logTimer) currentTaskLogs.value = '获取日志失败: ' + (error.message || '未知错误')
  } finally {
    loadingLogs.value = false
  }
}

// 查看任务详情
const viewTaskDetails = (task) => {
  currentTask.value = task
  showDetails.value = true
  fetchTaskLogs()
}

const handleRetrain = async (row) => {
  try {
    message.loading('正在启动重新训练...')
    
    const payload = {
      training_dataset: row.training_dataset,
      training_parameters: row.training_parameters || {}
    }
    
    await modelManagementApi.train(row.id, payload)
    
    message.success('重新训练任务已启动')
    fetchTasks()
  } catch (error) {
    console.error('重新训练失败', error)
    message.error('重新训练失败: ' + (error.message || '未知错误'))
  }
}

// 表格列定义
const columns = [
  { title: '任务ID', key: 'id', width: 100 },
  { title: '模型名称', key: 'model_name' },
  { title: '算法', key: 'algorithm' },
  { 
    title: '进度', 
    key: 'progress',
    width: 150,
    render(row) {
      if (row.status === 'training' || row.status === 'pending') {
        return h(NProgress, {
          type: 'line',
          percentage: row.progress || 0,
          processing: row.status === 'training',
          indicatorPlacement: 'inside'
        })
      }
      return '-'
    }
  },
  { 
    title: '状态', 
    key: 'status',
    render(row) {
      const type = row.status === 'training' ? 'info' : (row.status === 'trained' || row.status === 'deployed' ? 'success' : (row.status === 'error' ? 'error' : 'default'))
      const label = {
        'draft': '草稿',
        'training': '训练中',
        'trained': '已训练',
        'deployed': '已部署',
        'error': '失败',
        'archived': '归档'
      }[row.status] || row.status
      return h(NTag, { type }, { default: () => label })
    }
  },
  { title: '开始时间', key: 'start_time' },
  { title: '耗时', key: 'duration' },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { 
            size: 'small', 
            onClick: () => viewTaskDetails(row) 
          }, { default: () => '详情' }),
          h(NPopconfirm, {
            onPositiveClick: () => handleRetrain(row)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'warning',
              disabled: row.status === 'training'
            }, { default: () => '重新训练' }),
            default: () => '确定要重新训练该模型吗？这将覆盖之前的训练结果。'
          })
        ]
      })
    }
  }
]

const pagination = { pageSize: 10 }

// 向导相关
const currentStep = ref(1)
const starting = ref(false)
const trainConfig = ref({
  deviceType: null,
  device: null,
  dateRange: null,
  modelName: '',
  type: 'anomaly_detection',
  algorithm: 'IsolationForest',
  framework: 'Scikit-learn',
  parameters: [
    { key: 'contamination', value: '0.1' },
    { key: 'n_estimators', value: '100' }
  ]
})

// 选项数据
const deviceTypeOptions = ref([])
const deviceOptions = ref([])
const previewLoading = ref(false)
const chartOption = ref(null)
const chartData = ref([])

const canPreview = computed(() => {
  return trainConfig.value.device && trainConfig.value.dateRange && trainConfig.value.dateRange.length === 2
})

const selectedDeviceName = computed(() => {
  const device = deviceOptions.value.find(d => d.value === trainConfig.value.device)
  return device ? device.label : trainConfig.value.device
})

const typeOptions = [
  { label: '异常检测', value: 'anomaly_detection' },
  { label: '趋势预测', value: 'trend_prediction' },
]

const algorithmOptions = [
  { label: 'Random Forest', value: 'RandomForest' },
  { label: 'Isolation Forest', value: 'IsolationForest' },
  { label: 'LSTM', value: 'LSTM' },
  { label: 'ARIMA', value: 'ARIMA' }
]

const frameworkOptions = [
  { label: 'Scikit-learn', value: 'Scikit-learn' },
  { label: 'PyTorch', value: 'PyTorch' },
  { label: 'TensorFlow', value: 'TensorFlow' },
  { label: 'Statsmodels', value: 'Statsmodels' }
]

// 获取设备类型
const fetchDeviceTypes = async () => {
  try {
    const res = await deviceTypeApi.list()
    if (res?.data) {
      // 适配不同的响应结构
      const list = Array.isArray(res.data) ? res.data : (res.data.items || [])
      deviceTypeOptions.value = list.map((item: any) => ({
        label: item.type_name,
        value: item.type_code
      }))
    }
  } catch (error) {
    console.error('获取设备类型失败', error)
    message.error('获取设备类型失败')
  }
}

// 根据类型获取设备列表
const fetchDevices = async (typeCode: string) => {
  try {
    const res = await deviceApi.list({ device_type: typeCode })
    if (res?.data) {
      const list = Array.isArray(res.data) ? res.data : (res.data.items || [])
      deviceOptions.value = list.map((item: any) => ({
        label: `${item.device_name} (${item.device_code})`,
        value: item.id
      }))
    } else {
      deviceOptions.value = []
    }
  } catch (error) {
    console.error('获取设备列表失败', error)
    message.error('获取设备列表失败')
    deviceOptions.value = []
  }
}

// 处理设备类型变更
const handleDeviceTypeChange = (val: string) => {
  trainConfig.value.device = null
  chartOption.value = null
  fetchDevices(val)
}

const handleDateRangeChange = () => {
  chartOption.value = null
}

// 获取预览数据
const fetchPreviewData = async () => {
  if (!canPreview.value) return
  
  previewLoading.value = true
  chartOption.value = null
  chartData.value = []
  
  try {
    const [startTime, endTime] = trainConfig.value.dateRange
    
    // 调用 deviceApi.getMonitoring (V2) 获取历史数据，解决60s超时问题
    const res = await deviceApi.getMonitoring(trainConfig.value.device, {
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      page_size: 1000 // 获取足够多的点用于绘图
    })
    
    console.log('[DEBUG] Preview API Response:', res)

    // 兼容 V2 API 响应格式 (res.data 可能直接是数据数组，也可能是包含 items 的对象)
    // 根据用户日志: [API v2 Response] ... success: true, data: { items: [...], ... } 
    // 但拦截器 resResolve 返回的是 response.data
    // 如果 response.data 是 { code: 200, data: { items: [...] }, success: true }
    // 拦截器返回 resResolve(response.data) -> 即上述对象
    // 所以 res = 上述对象
    // rawData 应该从 res.data.items 取
    
    let rawData = []
    
    // 尝试多种路径获取数据数组
    if (Array.isArray(res)) {
      rawData = res
    } else if (Array.isArray(res.data)) {
      rawData = res.data
    } else if (res.data && Array.isArray(res.data.items)) {
      rawData = res.data.items
    } else if (res.items && Array.isArray(res.items)) {
       rawData = res.items
    } else if (res.data && res.data.list && Array.isArray(res.data.list)) {
       rawData = res.data.list
    }
    
    console.log('[DEBUG] Extracted rawData length:', rawData.length)

    if (rawData.length > 0) {
      // 处理数据
      // 注意：如果是 TDengine 返回的，通常已经是按时间排序的，但也可能需要反转
      // V2 API 的 get_device_history_data 默认可能是倒序(最新在前)？需检查后端
      // 假设是倒序，我们需要正序绘图
      const data = [...rawData].sort((a, b) => {
         const t1 = new Date(a.data_timestamp || a.ts || a.created_at).getTime()
         const t2 = new Date(b.data_timestamp || b.ts || b.created_at).getTime()
         return t1 - t2
      })
      
      // 更新 chartData，确保 AIChart 组件能正确初始化
      chartData.value = data
      
      // V2 API 返回的字段可能是 data_timestamp 或 ts
      const timestamps = data.map(item => item.data_timestamp || item.ts || item.created_at)
      
      // 自动识别数值型字段
      // 增强识别逻辑：排除非数值和特定字段
      const excludeFields = ['ts', 'created_at', 'id', 'device_code', 'device_name', 'device_type', 'device_model', 'status', 'data_timestamp']
      const numericFields = Object.keys(data[0]).filter(key => 
        !excludeFields.includes(key) && 
        (typeof data[0][key] === 'number' || !isNaN(parseFloat(data[0][key])))
      ).slice(0, 5) // 最多显示5个字段
      
      console.log('[DEBUG] Numeric Fields:', numericFields)
      
      const series = numericFields.map(field => ({
        name: field,
        type: 'line',
        showSymbol: false,
        data: data.map(item => item[field])
      }))
      
      chartOption.value = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: numericFields
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: timestamps.map(t => new Date(t).toLocaleString())
        },
        yAxis: {
          type: 'value'
        },
        series: series
      }
    } else {
      message.warning('该时间段内无数据')
    }
  } catch (error) {
    console.error('获取预览数据失败', error)
    message.error('获取预览数据失败')
  } finally {
    previewLoading.value = false
  }
}

// 步骤控制
const nextStep = () => {
  if (currentStep.value === 1) {
    if (!trainConfig.value.device || !trainConfig.value.dateRange) {
      message.warning('请先完成数据选择')
      return
    }
    // 自动生成默认名称（如果为空）
    if (!trainConfig.value.modelName) {
      trainConfig.value.modelName = `${trainConfig.value.type}_${trainConfig.value.algorithm}_${Date.now()}`
    }
  } else if (currentStep.value === 2) {
    if (!trainConfig.value.modelName) {
      message.warning('请输入模型名称')
      return
    }
  }
  
  if (currentStep.value < 3) currentStep.value++
}
const prevStep = () => {
  if (currentStep.value > 1) currentStep.value--
}

const fetchTasks = async () => {
  // loading.value = true // Polling shouldn't trigger full table loading state
  try {
    const res = await modelManagementApi.getList({ page: 1, page_size: 20 })
    if (res && res.data && Array.isArray(res.data.items)) {
      // 创建新数据列表
      const newTasks = res.data.items.map(item => ({
        id: item.id,
        model_name: item.model_name,
        algorithm: item.algorithm,
        status: item.status,
        // 确保进度是数字类型
        progress: typeof item.progress === 'number' ? item.progress : parseFloat(item.progress || 0),
        start_time: new Date(item.created_at).toLocaleString(),
        duration: item.training_metrics?.duration || '-',
        training_dataset: item.training_dataset,
        training_parameters: item.training_parameters,
        logs: [] // 暂不处理日志
      }))

      // 直接替换列表，确保响应式更新
      tasks.value = newTasks
    }
  } catch (error) {
    console.error('获取任务列表失败', error)
    // message.error('获取任务列表失败') // Don't spam errors on polling
  } finally {
    loading.value = false
  }
}

const startTraining = async () => {
  starting.value = true
  try {
    // 1. 构建模型参数
    const paramsDict = {}
    if (trainConfig.value.parameters) {
      trainConfig.value.parameters.forEach(p => {
        if (p.key) paramsDict[p.key] = p.value
      })
    }

    const modelPayload = {
      model_name: trainConfig.value.modelName || `${trainConfig.value.type}_${trainConfig.value.algorithm}_${Date.now()}`,
      model_version: "v1.0.0",
      description: `Training on device ${trainConfig.value.device}`,
      model_type: trainConfig.value.type,
      algorithm: trainConfig.value.algorithm,
      framework: trainConfig.value.framework,
      training_dataset: JSON.stringify({
        device_id: trainConfig.value.device,
        date_range: trainConfig.value.dateRange
      }),
      training_parameters: paramsDict
    }

    // 2. 调用API创建模型
    const createRes = await modelManagementApi.create(modelPayload)
    const modelData = createRes.data || createRes
    
    if (!modelData || !modelData.id) {
      throw new Error('创建模型失败: 未返回ID')
    }

    // 3. 调用API启动训练
    await modelManagementApi.train(modelData.id, {
      training_dataset: modelPayload.training_dataset,
      training_parameters: modelPayload.training_parameters
    })
    
    message.success('训练任务已启动')
    
    // 4. 刷新列表
    await fetchTasks()
    
    // 重置并切换回列表
    currentStep.value = 1
    activeTab.value = 'tasks'
  } catch (error) {
    console.error(error)
    message.error('启动失败: ' + (error.message || '未知错误'))
  } finally {
    starting.value = false
  }
}

let timer = null

onMounted(() => {
  fetchDeviceTypes()
  loading.value = true
  fetchTasks()
  
  // 开启轮询，每3秒刷新一次
  timer = setInterval(() => {
    if (activeTab.value === 'tasks') {
      fetchTasks()
    }
  }, 3000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (logTimer) clearInterval(logTimer)
})
</script>

<style scoped>
.model-training-lab {
  padding: 16px;
}
.step-content {
  margin-top: 24px;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fff;
}
</style>
