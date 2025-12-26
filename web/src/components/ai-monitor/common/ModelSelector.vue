<template>
  <div class="model-selector">
    <n-select
      v-model:value="selectedValue"
      :options="modelOptions"
      :loading="loading"
      :placeholder="placeholder"
      :multiple="multiple"
      :clearable="clearable"
      :filterable="filterable"
      :show-checkmark="false"
      @update:value="handleChange"
      @search="handleSearch"
      @focus="handleFocus"
    >
      <template #empty>
        <div class="empty-content">
          <n-empty description="暂无模型数据" size="small" />
        </div>
      </template>

      <template v-if="showActions" #action>
        <div class="selector-actions">
          <n-button text size="small" :loading="refreshing" @click="refreshModels">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新模型列表
          </n-button>

          <n-divider vertical />

          <n-button text size="small" @click="$emit('upload-model')">
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            上传新模型
          </n-button>
        </div>
      </template>

      <!-- 自定义选项渲染 -->
      <template #option="{ node, option }">
        <div class="model-option">
          <div class="model-info">
            <div class="model-name">{{ option.label }}</div>
            <div class="model-meta">
              <n-tag size="tiny" :type="getModelTypeColor(option.model?.type)">
                {{ getModelTypeLabel(option.model?.type) }}
              </n-tag>
              <span class="model-version">v{{ option.model?.version }}</span>
              <n-tag size="tiny" :type="getModelStatusColor(option.model?.status)">
                {{ getModelStatusLabel(option.model?.status) }}
              </n-tag>
            </div>
          </div>
          <div v-if="option.model?.accuracy" class="model-accuracy">
            {{ (option.model.accuracy * 100).toFixed(1) }}%
          </div>
        </div>
      </template>
    </n-select>

    <!-- 模型统计信息 -->
    <div v-if="showStats && modelStats" class="model-stats">
      <n-space size="small">
        <n-tag size="small" type="success"> 已部署: {{ modelStats.deployed }} </n-tag>
        <n-tag size="small" type="info"> 训练中: {{ modelStats.training }} </n-tag>
        <n-tag size="small" type="warning"> 待部署: {{ modelStats.pending }} </n-tag>
      </n-space>
    </div>

    <!-- 选中模型详情 -->
    <div v-if="showSelectedInfo && selectedModel" class="selected-model-info">
      <n-card size="small" title="模型信息">
        <n-descriptions :column="2" size="small">
          <n-descriptions-item label="模型名称">
            {{ selectedModel.name }}
          </n-descriptions-item>
          <n-descriptions-item label="模型类型">
            <n-tag size="small" :type="getModelTypeColor(selectedModel.type)">
              {{ getModelTypeLabel(selectedModel.type) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="版本"> v{{ selectedModel.version }} </n-descriptions-item>
          <n-descriptions-item label="准确率">
            {{ (selectedModel.accuracy * 100).toFixed(1) }}%
          </n-descriptions-item>
          <n-descriptions-item label="创建时间">
            {{ formatDate(selectedModel.createdAt) }}
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag size="small" :type="getModelStatusColor(selectedModel.status)">
              {{ getModelStatusLabel(selectedModel.status) }}
            </n-tag>
          </n-descriptions-item>
        </n-descriptions>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { RefreshOutline, CloudUploadOutline } from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import { format } from 'date-fns'
import { modelManagementApi } from '@/api/v2/ai-module'

// Props
const props = defineProps({
  // 当前选中值
  modelValue: {
    type: [String, Number, Array],
    default: null,
  },
  // 是否多选
  multiple: {
    type: Boolean,
    default: false,
  },
  // 占位符
  placeholder: {
    type: String,
    default: '请选择模型',
  },
  // 是否可清空
  clearable: {
    type: Boolean,
    default: true,
  },
  // 是否可搜索
  filterable: {
    type: Boolean,
    default: true,
  },
  // 模型类型过滤
  modelType: {
    type: String,
    default: '',
  },
  // 模型状态过滤
  modelStatus: {
    type: Array,
    default: () => ['deployed', 'training', 'pending'],
  },
  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: true,
  },
  // 是否显示统计信息
  showStats: {
    type: Boolean,
    default: false,
  },
  // 是否显示选中模型信息
  showSelectedInfo: {
    type: Boolean,
    default: false,
  },
  // 自定义模型数据
  customModels: {
    type: Array,
    default: () => [],
  },
  // 是否自动加载
  autoLoad: {
    type: Boolean,
    default: true,
  },
})

// Emits
const emit = defineEmits(['update:modelValue', 'change', 'search', 'refresh', 'upload-model'])

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const models = ref([])
const searchKeyword = ref('')
const message = useMessage()

// 计算属性
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 模型选项
const modelOptions = computed(() => {
  let options = props.customModels.length > 0 ? props.customModels : models.value

  // 按模型类型过滤
  if (props.modelType) {
    options = options.filter((model) => model.type === props.modelType)
  }

  // 按模型状态过滤
  if (props.modelStatus.length > 0) {
    options = options.filter((model) => props.modelStatus.includes(model.status))
  }

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    options = options.filter(
      (model) =>
        model.name.toLowerCase().includes(keyword) ||
        model.description?.toLowerCase().includes(keyword)
    )
  }

  return options.map((model) => ({
    label: `${model.name} (v${model.version})`,
    value: model.id,
    disabled: model.status === 'training',
    model: model, // 保留原始模型信息
  }))
})

// 选中的模型信息
const selectedModel = computed(() => {
  if (!props.modelValue) return null
  return models.value.find((model) => model.id === props.modelValue)
})

// 模型统计
const modelStats = computed(() => {
  if (!props.showStats || models.value.length === 0) return null

  const stats = {
    deployed: 0,
    training: 0,
    pending: 0,
    total: models.value.length,
  }

  models.value.forEach((model) => {
    if (model.status === 'deployed') stats.deployed++
    else if (model.status === 'training') stats.training++
    else if (model.status === 'pending') stats.pending++
  })

  return stats
})

// 获取模型类型颜色
const getModelTypeColor = (type) => {
  const colors = {
    'anomaly-detection': 'error',
    'trend-prediction': 'info',
    'health-scoring': 'success',
    classification: 'warning',
    regression: 'default',
  }
  return colors[type] || 'default'
}

// 获取模型类型标签
const getModelTypeLabel = (type) => {
  const labels = {
    'anomaly-detection': '异常检测',
    'trend-prediction': '趋势预测',
    'health-scoring': '健康评分',
    classification: '分类模型',
    regression: '回归模型',
  }
  return labels[type] || type
}

// 获取模型状态颜色
const getModelStatusColor = (status) => {
  const colors = {
    deployed: 'success',
    training: 'info',
    pending: 'warning',
    failed: 'error',
  }
  return colors[status] || 'default'
}

// 获取模型状态标签
const getModelStatusLabel = (status) => {
  const labels = {
    deployed: '已部署',
    training: '训练中',
    pending: '待部署',
    failed: '失败',
  }
  return labels[status] || status
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return format(new Date(date), 'yyyy-MM-dd HH:mm')
}

// 加载模型列表
const loadModels = async () => {
  if (props.customModels.length > 0) return

  loading.value = true
  try {
    const params = {
      page: 1,
      page_size: 100, // 获取足够多的模型以供选择
    }
    
    // 只有在有值时才添加参数
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (props.modelType) {
      params.model_type = props.modelType
    }

    const res = await modelManagementApi.getList(params)
    
    if (res.data && res.data.items) {
      models.value = res.data.items.map(item => ({
        id: item.id,
        name: item.model_name,
        type: item.model_type,
        version: item.model_version,
        status: item.status,
        accuracy: item.accuracy ? parseFloat(item.accuracy) : 0,
        description: item.description,
        createdAt: item.created_at,
        features: item.training_parameters?.features || [], // 从训练参数中提取特征
        trainingParameters: item.training_parameters || {},
        deploymentParameters: item.deployment_parameters || {},
      }))
    } else {
      models.value = []
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    // 不显示错误消息，静默处理，让用户可以继续使用其他功能
    models.value = []
  } finally {
    loading.value = false
  }
}

// 刷新模型列表
const refreshModels = async () => {
  refreshing.value = true
  try {
    await loadModels()
    message.success('模型列表已刷新')
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

// 处理选择变化
const handleChange = (value, option) => {
  emit('change', value, option)
}

// 处理搜索
const handleSearch = (query) => {
  searchKeyword.value = query
  emit('search', query)
}

// 处理获得焦点
const handleFocus = () => {
  if (models.value.length === 0 && props.autoLoad) {
    loadModels()
  }
}

// 监听模型类型变化
watch(
  () => props.modelType,
  () => {
    if (props.autoLoad) {
      loadModels()
    }
  }
)

// 监听模型状态变化
watch(
  () => props.modelStatus,
  () => {
    if (props.autoLoad) {
      loadModels()
    }
  },
  { deep: true }
)

// 生命周期
onMounted(() => {
  if (props.autoLoad) {
    loadModels()
  }
})

// 暴露方法
defineExpose({
  loadModels,
  refreshModels,
  getModels: () => models.value,
  getStats: () => modelStats.value,
})
</script>

<style scoped>
.model-selector {
  width: 100%;
}

.empty-content {
  padding: 20px;
  text-align: center;
}

.selector-actions {
  padding: 8px 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.model-info {
  flex: 1;
}

.model-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.model-version {
  color: #999;
}

.model-accuracy {
  font-weight: 500;
  color: #52c41a;
}

.model-stats {
  margin-top: 8px;
  padding: 8px 0;
}

.selected-model-info {
  margin-top: 12px;
}
</style>
