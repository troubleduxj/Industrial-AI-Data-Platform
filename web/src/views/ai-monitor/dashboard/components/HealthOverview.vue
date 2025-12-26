<template>
  <div class="health-overview">
    <n-grid :cols="3" :x-gap="16">
      <n-grid-item>
        <n-card class="health-card healthy" hoverable @click="handleCardClick('healthy')">
          <div class="health-content">
            <div class="health-icon">
              <n-icon size="32" color="#18a058">
                <CheckmarkCircleOutline />
              </n-icon>
            </div>
            <div class="health-info">
              <div class="health-title">健康设备</div>
              <div class="health-count">{{ data.healthy }}</div>
              <div class="health-percentage">{{ healthyPercentage }}%</div>
            </div>
          </div>
          <div class="health-trend">
            <n-icon size="16" color="#18a058">
              <TrendingUpOutline />
            </n-icon>
            <span class="trend-text">较昨日 +2</span>
          </div>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card class="health-card warning" hoverable @click="handleCardClick('warning')">
          <div class="health-content">
            <div class="health-icon">
              <n-icon size="32" color="#f0a020">
                <WarningOutline />
              </n-icon>
            </div>
            <div class="health-info">
              <div class="health-title">预警设备</div>
              <div class="health-count">{{ data.warning }}</div>
              <div class="health-percentage">{{ warningPercentage }}%</div>
            </div>
          </div>
          <div class="health-trend">
            <n-icon size="16" color="#f0a020">
              <TrendingDownOutline />
            </n-icon>
            <span class="trend-text">较昨日 -1</span>
          </div>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card class="health-card error" hoverable @click="handleCardClick('error')">
          <div class="health-content">
            <div class="health-icon">
              <n-icon size="32" color="#d03050">
                <CloseCircleOutline />
              </n-icon>
            </div>
            <div class="health-info">
              <div class="health-title">异常设备</div>
              <div class="health-count">{{ data.error }}</div>
              <div class="health-percentage">{{ errorPercentage }}%</div>
            </div>
          </div>
          <div class="health-trend">
            <n-icon size="16" color="#d03050">
              <RemoveOutline />
            </n-icon>
            <span class="trend-text">较昨日 ±0</span>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 设备列表快速预览 -->
    <div v-if="showDeviceList" class="device-preview">
      <n-card title="设备状态详情" class="mt-4">
        <n-data-table
          :columns="deviceColumns"
          :data="deviceList"
          :pagination="false"
          size="small"
          max-height="300"
        />
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  CheckmarkCircleOutline,
  WarningOutline,
  CloseCircleOutline,
  TrendingUpOutline,
  TrendingDownOutline,
  RemoveOutline,
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({
      healthy: 0,
      warning: 0,
      error: 0,
    }),
  },
})

// Emits
const emit = defineEmits(['device-click'])

// 响应式数据
const showDeviceList = ref(false)

// 计算属性
const totalDevices = computed(() => {
  return props.data.healthy + props.data.warning + props.data.error
})

const healthyPercentage = computed(() => {
  if (totalDevices.value === 0) return 0
  return ((props.data.healthy / totalDevices.value) * 100).toFixed(1)
})

const warningPercentage = computed(() => {
  if (totalDevices.value === 0) return 0
  return ((props.data.warning / totalDevices.value) * 100).toFixed(1)
})

const errorPercentage = computed(() => {
  if (totalDevices.value === 0) return 0
  return ((props.data.error / totalDevices.value) * 100).toFixed(1)
})

// 模拟设备列表数据
const deviceList = ref([
  {
    id: 'WLD-001',
    name: '焊接设备01',
    status: 'healthy',
    location: '车间A',
    lastUpdate: '2024-01-15 14:30',
  },
  {
    id: 'WLD-002',
    name: '焊接设备02',
    status: 'warning',
    location: '车间A',
    lastUpdate: '2024-01-15 14:28',
  },
  {
    id: 'WLD-003',
    name: '焊接设备03',
    status: 'error',
    location: '车间B',
    lastUpdate: '2024-01-15 14:25',
  },
  {
    id: 'WLD-004',
    name: '焊接设备04',
    status: 'healthy',
    location: '车间B',
    lastUpdate: '2024-01-15 14:32',
  },
  {
    id: 'WLD-005',
    name: '焊接设备05',
    status: 'healthy',
    location: '车间C',
    lastUpdate: '2024-01-15 14:31',
  },
])

// 设备列表表格列配置
const deviceColumns = [
  { title: '设备ID', key: 'id', width: 100 },
  { title: '设备名称', key: 'name', width: 120 },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) => {
      const statusMap = {
        healthy: { type: 'success', text: '健康' },
        warning: { type: 'warning', text: '预警' },
        error: { type: 'error', text: '异常' },
      }
      const config = statusMap[row.status]
      return h('n-tag', { type: config.type, size: 'small' }, { default: () => config.text })
    },
  },
  { title: '位置', key: 'location', width: 100 },
  { title: '最后更新', key: 'lastUpdate', width: 140 },
]

// 方法
const handleCardClick = (type) => {
  showDeviceList.value = !showDeviceList.value
  emit('device-click', { type, count: props.data[type] })
}
</script>

<style scoped>
.health-overview {
  width: 100%;
}

.health-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
}

.health-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.health-content {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.health-icon {
  margin-right: 16px;
}

.health-info {
  flex: 1;
}

.health-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.health-count {
  font-size: 28px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 4px;
}

.health-percentage {
  font-size: 12px;
  color: #999;
}

.health-trend {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.trend-text {
  margin-left: 4px;
}

.healthy .health-count {
  color: #18a058;
}

.warning .health-count {
  color: #f0a020;
}

.error .health-count {
  color: #d03050;
}

.mt-4 {
  margin-top: 16px;
}

.device-preview {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
