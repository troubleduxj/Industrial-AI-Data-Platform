<template>
  <NSelect
    :value="modelValue"
    :options="deviceOptions"
    :loading="loading"
    placeholder="请选择设备"
    clearable
    filterable
    remote
    :disabled="disabled"
    :clear-filter-after-select="false"
    @search="handleSearch"
    @update:value="handleSelect"
  >
    <template #empty>
      <div class="py-4 text-center">
        <div v-if="loading">正在搜索设备...</div>
        <div v-else-if="searchKeyword">未找到相关设备</div>
        <div v-else>请输入设备编号或名称进行搜索</div>
      </div>
    </template>

    <template #option="{ node, option }">
      <div class="device-option">
        <div class="device-info">
          <div class="device-code">{{ option.device_code }}</div>
          <div class="device-name">{{ option.device_name }}</div>
        </div>
        <div class="device-meta">
          <NTag size="small" type="info">{{ option.device_type_name }}</NTag>
          <StatusIndicator :status="option.status" type="device" size="small" />
        </div>
      </div>
    </template>
  </NSelect>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { NSelect, NTag, useMessage } from 'naive-ui'
import StatusIndicator from '@/components/common/StatusIndicator.vue'
import deviceV2Api from '@/api/device-v2'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null,
  },
  deviceType: {
    type: String,
    default: '', // 可以限制设备类型
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: '请选择设备',
  },
  // 是否显示设备状态
  showStatus: {
    type: Boolean,
    default: true,
  },
  // 是否只显示在线设备
  onlineOnly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'device-change'])

const message = useMessage()

// 状态数据
const loading = ref(false)
const devices = ref([])
const searchKeyword = ref('')

// 设备选项
const deviceOptions = computed(() => {
  let filteredDevices = devices.value

  // 按设备类型过滤
  if (props.deviceType) {
    filteredDevices = filteredDevices.filter((device) => device.device_type === props.deviceType)
  }

  // 只显示在线设备
  if (props.onlineOnly) {
    filteredDevices = filteredDevices.filter((device) => device.status === 'online')
  }

  return filteredDevices.map((device) => ({
    label: `${device.device_code} - ${device.device_name}`,
    value: device.id,
    device_code: device.device_code,
    device_name: device.device_name,
    device_type: device.device_type,
    device_type_name: device.device_type_name,
    status: device.status,
    ...device,
  }))
})

// 搜索设备
const handleSearch = async (query) => {
  if (!query || query.length < 2) {
    devices.value = []
    return
  }

  searchKeyword.value = query
  loading.value = true

  try {
    const params = {
      search: query,
      page: 1,
      page_size: 20,
    }

    // 添加设备类型过滤
    if (props.deviceType) {
      params.device_type = props.deviceType
    }

    // 添加状态过滤
    if (props.onlineOnly) {
      params.status = 'online'
    }

    const response = await deviceV2Api.list(params)

    if (response && response.data) {
      devices.value = response.data.items || response.data || []
    } else {
      devices.value = []
    }
  } catch (error) {
    console.error('搜索设备失败:', error)
    message.error('搜索设备失败')
    devices.value = []
  } finally {
    loading.value = false
  }
}

// 选择设备
const handleSelect = (value) => {
  emit('update:modelValue', value)

  if (value) {
    const selectedDevice = devices.value.find((device) => device.id === value)
    if (selectedDevice) {
      emit('device-change', selectedDevice)
    }
  } else {
    emit('device-change', null)
  }
}

// 组件挂载时加载常用设备
onMounted(async () => {
  try {
    const params = {
      page: 1,
      page_size: 10,
      order_by: 'updated_at',
      order: 'desc',
    }

    // 添加设备类型过滤
    if (props.deviceType) {
      params.device_type = props.deviceType
    }

    // 添加状态过滤
    if (props.onlineOnly) {
      params.status = 'online'
    }

    const response = await deviceV2Api.list(params)

    if (response && response.data) {
      devices.value = response.data.items || response.data || []
    }
  } catch (error) {
    console.error('加载设备列表失败:', error)
  }
})
</script>

<style scoped>
.device-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.device-info {
  flex: 1;
}

.device-code {
  font-weight: 600;
  color: var(--n-text-color-1);
  font-size: 14px;
}

.device-name {
  color: var(--n-text-color-2);
  font-size: 12px;
  margin-top: 2px;
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
