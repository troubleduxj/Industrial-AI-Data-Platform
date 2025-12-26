<template>
  <div class="device-selector">
    <n-select
      v-model:value="selectedValue"
      :options="deviceOptions"
      :loading="loading"
      :placeholder="placeholder"
      :multiple="multiple"
      :clearable="clearable"
      :filterable="filterable"
      :remote="remote"
      :show-checkmark="false"
      @update:value="handleChange"
      @search="handleSearch"
      @focus="handleFocus"
    >
      <template #empty>
        <div class="empty-content">
          <n-empty description="暂无设备数据" size="small" />
        </div>
      </template>

      <template v-if="showRefresh" #action>
        <div class="selector-action">
          <n-button text size="small" :loading="refreshing" @click="refreshDevices">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新设备列表
          </n-button>
        </div>
      </template>
    </n-select>

    <!-- 设备状态统计 -->
    <div v-if="showStats && deviceStats" class="device-stats">
      <n-space size="small">
        <n-tag size="small" type="success"> 在线: {{ deviceStats.online }} </n-tag>
        <n-tag size="small" type="error"> 离线: {{ deviceStats.offline }} </n-tag>
        <n-tag size="small" type="warning"> 异常: {{ deviceStats.abnormal }} </n-tag>
      </n-space>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { RefreshOutline } from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import { deviceApi } from '@/api/device-v2'

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
    default: '请选择设备',
  },
  // 是否可清空
  clearable: {
    type: Boolean,
    default: true,
  },
  // 是否可搜索
  filterable: {
    type: Boolean,
    default: false,
  },
  // 是否远程搜索
  remote: {
    type: Boolean,
    default: false,
  },
  // 设备类型过滤
  deviceType: {
    type: String,
    default: '',
  },
  // 设备状态过滤
  deviceStatus: {
    type: Array,
    default: () => [],
  },
  // 是否显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: true,
  },
  // 是否显示统计信息
  showStats: {
    type: Boolean,
    default: false,
  },
  // 自定义设备数据
  customDevices: {
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
const emit = defineEmits(['update:modelValue', 'change', 'search', 'refresh'])

// 响应式数据
const loading = ref(false)
const refreshing = ref(false)
const devices = ref([])
const searchKeyword = ref('')
const message = useMessage()

// 计算属性
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 设备选项
const deviceOptions = computed(() => {
  let options = props.customDevices.length > 0 ? props.customDevices : devices.value

  // 按设备类型过滤 (仅当使用自定义设备数据时在前端过滤，API加载的数据假定已由后端过滤)
  if (props.deviceType && props.customDevices.length > 0) {
    options = options.filter((device) => device.type === props.deviceType || device.device_type === props.deviceType)
  }

  // 按设备状态过滤
  if (props.deviceStatus.length > 0) {
    options = options.filter((device) => {
      if (!device.status) return true // 如果没有状态，不过滤
      return props.deviceStatus.includes(device.status)
    })
  }

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    options = options.filter((device) => {
      const name = device.label || device.device_name || device.name || ''
      const code = device.device_code || device.code || ''
      return name.toLowerCase().includes(keyword) || code.toLowerCase().includes(keyword)
    })
  }

  return options.map((device) => ({
    label: device.label || `${device.device_name || device.name} (${device.device_code || device.code})`,
    value: device.value || device.id,
    disabled: device.disabled || false,
    device: device, // 保留原始设备信息
  }))
})

// 设备状态统计
const deviceStats = computed(() => {
  if (!props.showStats || devices.value.length === 0) return null

  const stats = {
    online: 0,
    offline: 0,
    abnormal: 0,
    total: devices.value.length,
  }

  devices.value.forEach((device) => {
    if (device.status === 'online') stats.online++
    else if (device.status === 'offline') stats.offline++
    else if (device.status === 'abnormal') stats.abnormal++
  })

  return stats
})

// 加载设备列表
const loadDevices = async () => {
  if (props.customDevices.length > 0) return

  loading.value = true
  try {
    const params = {
      page_size: 1000, // 获取更多设备用于下拉选择，确保加载所有设备
    }
    if (props.deviceType) params.device_type = props.deviceType
    if (searchKeyword.value) params.search = searchKeyword.value // 支持后端通用搜索（名称或编号）

    const res = await deviceApi.list(params)
    if (res.data) {
      devices.value = res.data
    }
  } catch (error) {
    console.error('加载设备列表失败:', error)
    // message.error('加载设备列表失败') // 避免在组件加载时弹出错误干扰用户
  } finally {
    loading.value = false
  }
}

// 刷新设备列表
const refreshDevices = async () => {
  refreshing.value = true
  try {
    await loadDevices()
    message.success('设备列表已刷新')
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
  // 如果输入了关键字，触发后端搜索（防抖由用户输入速度决定，或者这里可以加简单的防抖）
  // 考虑到 loadDevices 内部没有防抖，且 n-select 的 search 事件通常在用户输入停止后触发（取决于 filterable/remote 配置）
  // 但这里为了确保能搜到未加载的设备，我们主动调用一次加载
  if (query) {
    loadDevices()
  }
}

// 处理获得焦点
const handleFocus = () => {
  if (devices.value.length === 0 && props.autoLoad) {
    loadDevices()
  }
}

// 监听设备类型变化
watch(
  () => props.deviceType,
  () => {
    if (props.autoLoad) {
      loadDevices()
    }
  }
)

// 监听设备状态变化
watch(
  () => props.deviceStatus,
  () => {
    if (props.autoLoad) {
      loadDevices()
    }
  },
  { deep: true }
)

// 生命周期
onMounted(() => {
  if (props.autoLoad) {
    loadDevices()
  }
})

// 暴露方法
defineExpose({
  loadDevices,
  refreshDevices,
  getDevices: () => devices.value,
  getStats: () => deviceStats.value,
})
</script>

<style scoped>
.device-selector {
  width: 100%;
}

.empty-content {
  padding: 20px;
  text-align: center;
}

.selector-action {
  padding: 8px 12px;
  border-top: 1px solid #f0f0f0;
}

.device-stats {
  margin-top: 8px;
  padding: 8px 0;
}
</style>
