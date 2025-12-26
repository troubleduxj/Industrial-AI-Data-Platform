<template>
  <div class="model-management">
    <!-- 页面头部 -->
    <div v-permission="{ action: 'read', resource: 'model_management' }" class="page-header">
      <n-space justify="space-between" align="center">
        <div>
          <h2>模型管理</h2>
          <p class="page-description">管理AI模型的上传、部署、版本控制和性能监控</p>
        </div>
        <n-space>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/models"
            type="primary"
            @click="showTrainModal = true"
          >
            <template #icon>
              <n-icon><add-outline /></n-icon>
            </template>
            新建模型
          </PermissionButton>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/models"
            @click="showUploadModal = true"
          >
            <template #icon>
              <n-icon><cloud-upload-outline /></n-icon>
            </template>
            上传模型
          </PermissionButton>
          <PermissionButton permission="GET /api/v2/ai-monitor/models" @click="refreshData">
            <template #icon>
              <n-icon><refresh-outline /></n-icon>
            </template>
            刷新
          </PermissionButton>
        </n-space>
      </n-space>
    </div>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card title="模型概览" size="small">
          <n-statistic label="总模型数" :value="stats.totalModels">
            <template #prefix>
              <n-icon color="#18a058">
                <cube-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="运行状态" size="small">
          <n-statistic label="运行中" :value="stats.runningModels">
            <template #prefix>
              <n-icon color="#2080f0">
                <play-circle-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="训练任务" size="small">
          <n-statistic label="训练中" :value="stats.trainingModels">
            <template #prefix>
              <n-icon color="#f0a020">
                <time-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="模型质量" size="small">
          <n-statistic label="平均准确率" :value="stats.avgAccuracy" suffix="%">
            <template #prefix>
              <n-icon color="#18a058">
                <analytics-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 服务监控 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card title="系统负载 (CPU)" size="small">
          <n-statistic label="CPU使用率">
            <template #default>{{ stats.cpuUsage }}</template>
            <template #suffix v-if="stats.cpuUsage !== '-'">%</template>
            <template #prefix>
              <n-icon color="#d03050"><pulse-outline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="内存占用" size="small">
          <n-statistic label="内存使用率">
            <template #default>{{ stats.memoryUsage }}</template>
            <template #suffix v-if="stats.memoryUsage !== '-'">%</template>
            <template #prefix>
              <n-icon color="#f0a020"><server-outline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="服务并发 (QPS)" size="small">
          <n-statistic label="当前QPS">
            <template #default>{{ stats.qps }}</template>
            <template #prefix>
              <n-icon color="#2080f0"><flash-outline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="响应延迟" size="small">
          <n-statistic label="平均延迟">
            <template #default>{{ stats.avgLatency }}</template>
            <template #suffix v-if="stats.avgLatency !== '-'">ms</template>
            <template #prefix>
              <n-icon color="#18a058"><timer-outline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 筛选和搜索 -->
    <n-card class="filter-card">
      <n-space>
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索模型名称或描述"
          clearable
          style="width: 300px"
        >
          <template #prefix>
            <n-icon><search-outline /></n-icon>
          </template>
        </n-input>
        <n-select
          v-model:value="filterStatus"
          placeholder="状态筛选"
          clearable
          style="width: 150px"
          :options="statusOptions"
        />
        <n-select
          v-model:value="filterType"
          placeholder="模型类型"
          clearable
          style="width: 150px"
          :options="typeOptions"
        />
        <n-date-picker
          v-model:value="dateRange"
          type="daterange"
          clearable
          placeholder="创建时间范围"
        />
      </n-space>
    </n-card>

    <!-- 模型列表 -->
    <ModelList
      :models="filteredModels"
      :loading="loading"
      @deploy="handleDeploy"
      @stop="handleStop"
      @delete="handleDelete"
      @view-detail="handleViewDetail"
      @download="handleDownload"
    />

    <!-- 上传模型弹窗 -->
    <ModelUpload v-model:show="showUploadModal" @success="handleUploadSuccess" />

    <!-- 新建模型训练弹窗 -->
    <ModelTrain v-model:show="showTrainModal" @success="handleTrainSuccess" />

    <!-- 模型详情弹窗 -->
    <ModelDetail v-model:show="showDetailModal" :model="selectedModel" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace,
  NButton,
  NIcon,
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NInput,
  NSelect,
  NDatePicker,
  useMessage,
  useDialog,
} from 'naive-ui'
import {
  CloudUploadOutline,
  RefreshOutline,
  CubeOutline,
  PlayCircleOutline,
  TimeOutline,
  AnalyticsOutline,
  SearchOutline,
  AddOutline,
  PulseOutline,
  ServerOutline,
  FlashOutline,
  TimerOutline,
} from '@vicons/ionicons5'
import PermissionButton from '@/components/common/PermissionButton.vue'
import ModelList from './components/ModelList.vue'
import ModelUpload from './components/ModelUpload.vue'
import ModelTrain from './components/ModelTrain.vue'
import ModelDetail from './components/ModelDetail.vue'

import { modelManagementApi, aiModuleApi } from '@/api/v2/ai-module'

// 响应式数据
const loading = ref(false)
const showUploadModal = ref(false)
const showTrainModal = ref(false)
const showDetailModal = ref(false)
const selectedModel = ref(null)
const searchKeyword = ref('')
const filterStatus = ref(null)
const filterType = ref(null)
const dateRange = ref(null)

// 统计数据
const stats = ref({
  totalModels: 0,
  runningModels: 0,
  trainingModels: 0,
  avgAccuracy: 0,
  cpuUsage: '-',
  memoryUsage: '-',
  qps: '-',
  avgLatency: '-'
})

// 模型列表
const models = ref([])

// 筛选选项
const statusOptions = [
  { label: '已部署', value: 'deployed' },
  { label: '已停止', value: 'stopped' },
  { label: '训练中', value: 'training' },
  { label: '已训练', value: 'trained' },
  { label: '草稿', value: 'draft' },
  { label: '错误', value: 'error' },
  { label: '失败', value: 'failed' },
]

const typeOptions = [
  { label: '异常检测', value: 'anomaly_detection' },
  { label: '趋势预测', value: 'trend_prediction' },
  { label: '健康评分', value: 'health_scoring' },
  { label: '分类模型', value: 'classification' },
  { label: '回归模型', value: 'regression' },
]

// 监听筛选条件变化，自动刷新
import { watch } from 'vue'
watch([searchKeyword, filterStatus, filterType, dateRange], () => {
  refreshData()
})

// 计算属性 - 过滤后的模型列表 (现在由后端处理过滤，直接返回models)
const filteredModels = computed(() => models.value)

// 消息和对话框
const message = useMessage()
const dialog = useDialog()

// 计算统计数据
const calculateStats = () => {
  const totalModels = models.value.length
  const runningModels = models.value.filter((m) => m.status === 'deployed').length
  const trainingModels = models.value.filter((m) => m.status === 'training').length
  const avgAccuracy =
    totalModels > 0
      ? models.value.reduce((sum, m) => sum + (parseFloat(m.accuracy) || 0), 0) / totalModels
      : 0

  stats.value = {
    totalModels,
    runningModels,
    trainingModels,
    avgAccuracy: avgAccuracy.toFixed(1),
  }
}

import { onMounted, onUnmounted } from 'vue'

let pollingTimer = null

// 刷新数据
const refreshData = async (isPolling = false) => {
  if (!isPolling) loading.value = true
  try {
    const params = {
      page: 1,
      page_size: 100, // 暂时获取较多数据，后续可添加分页组件
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      model_type: filterType.value || undefined,
    }

    // 处理日期范围
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = new Date(dateRange.value[0]).toISOString()
      params.date_to = new Date(dateRange.value[1]).toISOString()
    }

    const res = await modelManagementApi.getList(params)
    
    // 映射后端数据格式到前端
    const newModels = (res.data.items || []).map(item => ({
      id: item.id,
      name: item.model_name,
      description: item.description,
      type: item.model_type,
      status: item.status,
      version: item.model_version,
      accuracy: item.accuracy ? parseFloat(item.accuracy).toFixed(2) : '0.00',
      size: item.model_file_size || '0MB',
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      author: item.created_by,
      deployedAt: item.deployed_at,
      progress: typeof item.progress === 'number' ? item.progress : parseFloat(item.progress || 0),
      metrics: {
        precision: item.precision ? parseFloat(item.precision).toFixed(2) : '0.00',
        recall: item.recall ? parseFloat(item.recall).toFixed(2) : '0.00',
        f1Score: item.f1_score ? parseFloat(item.f1_score).toFixed(2) : '0.00',
      }
    }))

    // 如果数据长度变化或ID不匹配，直接替换
    if (models.value.length !== newModels.length || !models.value.every((m, i) => m.id === newModels[i].id)) {
      models.value = newModels
    } else {
      // 否则进行增量更新，保持引用以避免闪烁
      newModels.forEach((newItem, index) => {
        const oldItem = models.value[index]
        // 仅更新变化字段
        if (oldItem.status !== newItem.status) oldItem.status = newItem.status
        if (oldItem.progress !== newItem.progress) oldItem.progress = newItem.progress
        if (oldItem.accuracy !== newItem.accuracy) oldItem.accuracy = newItem.accuracy
        if (oldItem.deployedAt !== newItem.deployedAt) oldItem.deployedAt = newItem.deployedAt
        // 更新其他可能变化的字段...
        Object.assign(oldItem.metrics, newItem.metrics)
      })
    }
    
    calculateStats()
    if (!isPolling) message.success('数据刷新成功')

    // 如果有训练中的任务，开启快速轮询
    const hasTrainingTask = models.value.some(m => m.status === 'training')
    startPolling(hasTrainingTask ? 5000 : 30000)

    // 获取系统资源状态
    try {
      const resourceRes = await aiModuleApi.getResources()
      if (resourceRes.data) {
        stats.value.cpuUsage = resourceRes.data.cpu_usage != null ? parseFloat(resourceRes.data.cpu_usage).toFixed(1) : '-'
        stats.value.memoryUsage = resourceRes.data.memory_usage != null ? parseFloat(resourceRes.data.memory_usage).toFixed(1) : '-'
        stats.value.qps = resourceRes.data.qps != null ? resourceRes.data.qps : '-'
        stats.value.avgLatency = resourceRes.data.avg_latency != null ? resourceRes.data.avg_latency : '-'
      }
    } catch (e) {
      stats.value.cpuUsage = '-'
      stats.value.memoryUsage = '-'
      stats.value.qps = '-'
      stats.value.avgLatency = '-'
    }

  } catch (error) {
    console.error(error)
    if (!isPolling) message.error('数据刷新失败')
  } finally {
    if (!isPolling) loading.value = false
  }
}

const startPolling = (interval) => {
  stopPolling()
  pollingTimer = setTimeout(() => {
    refreshData(true)
  }, interval)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
  }
}

onMounted(() => {
  refreshData()
})

onUnmounted(() => {
  stopPolling()
})

// 处理模型部署
const handleDeploy = async (model) => {
  try {
    message.loading('正在部署模型...')
    await modelManagementApi.deploy(model.id, {})
    message.success('模型部署成功')
    refreshData()
  } catch (error) {
    message.error('模型部署失败')
  }
}

// 处理模型停止
const handleStop = async (model) => {
  try {
    // await modelManagementApi.stop(model.id)
    message.warning('停止功能暂未开放')
    // refreshData()
  } catch (error) {
    message.error('停止模型失败')
  }
}

// 处理模型删除
const handleDelete = (model) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除模型 "${model.name}" 吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await modelManagementApi.delete(model.id)
        message.success('模型删除成功')
        refreshData()
      } catch (error) {
        message.error('删除模型失败')
      }
    },
  })
}

// 查看模型详情
const handleViewDetail = (model) => {
  selectedModel.value = model
  showDetailModal.value = true
}

// 下载模型
const handleDownload = (model) => {
  message.info(`开始下载模型: ${model.name}`)
  // 这里可以实现实际的下载逻辑
}

// 上传成功回调
const handleUploadSuccess = () => {
  refreshData()
  message.success('模型上传成功')
}

// 训练任务创建成功回调
const handleTrainSuccess = () => {
  refreshData()
  // message already shown in component
}

// 组件挂载时初始化数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.model-management {
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
}

.page-description {
  color: #666;
  margin: 4px 0 0 0;
  font-size: 14px;
}

.stats-grid {
  margin-bottom: 16px;
}

.filter-card {
  margin-bottom: 16px;
}
</style>
