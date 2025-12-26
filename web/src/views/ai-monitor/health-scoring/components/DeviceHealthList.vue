<template>
  <div class="health-list">
    <n-card title="设备健康列表" size="small">
      <template #header-extra>
        <n-space>
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索设备名称或编号"
            size="small"
            clearable
            style="width: 200px"
            @input="handleSearch"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          <n-select
            v-model:value="selectedWorkshop"
            :options="workshopOptions"
            placeholder="选择车间"
            size="small"
            clearable
            style="width: 120px"
            @update:value="handleFilter"
          />
          <n-select
            v-model:value="selectedHealthLevel"
            :options="healthLevelOptions"
            placeholder="健康等级"
            size="small"
            clearable
            style="width: 100px"
            @update:value="handleFilter"
          />
          <n-button size="small" @click="refreshData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
          <n-button size="small" type="primary" @click="exportData">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            导出
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="filteredData"
        :pagination="pagination"
        :loading="loading"
        size="small"
        striped
        :row-key="(row) => row.id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import {
  SearchOutline,
  RefreshOutline,
  DownloadOutline,
  HeartOutline,
  WarningOutline,
  CloseCircleOutline,
  EyeOutline,
  SettingsOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
})

const message = useMessage()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const selectedWorkshop = ref(null)
const selectedHealthLevel = ref(null)
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
})

// 选项数据
const workshopOptions = [
  { label: '生产车间A', value: 'workshop_a' },
  { label: '生产车间B', value: 'workshop_b' },
  { label: '生产车间C', value: 'workshop_c' },
  { label: '包装车间', value: 'packaging' },
  { label: '质检车间', value: 'quality' },
]

const healthLevelOptions = [
  { label: '健康', value: 'healthy' },
  { label: '警告', value: 'warning' },
  { label: '故障', value: 'error' },
]

// 生成模拟数据
const generateMockData = () => {
  const devices = []
  const deviceTypes = ['压缩机', '泵', '电机', '传感器', '控制器']
  const workshops = ['workshop_a', 'workshop_b', 'workshop_c', 'packaging', 'quality']
  const workshopNames = ['生产车间A', '生产车间B', '生产车间C', '包装车间', '质检车间']

  for (let i = 1; i <= 50; i++) {
    const score = Math.floor(Math.random() * 100)
    let healthLevel, healthColor

    if (score >= 80) {
      healthLevel = 'healthy'
      healthColor = '#18a058'
    } else if (score >= 60) {
      healthLevel = 'warning'
      healthColor = '#f0a020'
    } else {
      healthLevel = 'error'
      healthColor = '#d03050'
    }

    const workshopIndex = Math.floor(Math.random() * workshops.length)

    devices.push({
      id: `DEV${String(i).padStart(3, '0')}`,
      name: `${deviceTypes[Math.floor(Math.random() * deviceTypes.length)]}-${i}`,
      type: deviceTypes[Math.floor(Math.random() * deviceTypes.length)],
      workshop: workshops[workshopIndex],
      workshopName: workshopNames[workshopIndex],
      healthScore: score,
      healthLevel,
      healthColor,
      lastUpdate: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0],
      status: Math.random() > 0.1 ? 'online' : 'offline',
      temperature: Math.floor(Math.random() * 50 + 20),
      pressure: Math.floor(Math.random() * 100 + 50),
      vibration: Math.floor(Math.random() * 10),
      trend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable',
    })
  }

  return devices
}

// 计算属性
const deviceData = computed(() => {
  if (props.data && props.data.length > 0) {
    return props.data
  }
  return generateMockData()
})

const filteredData = computed(() => {
  let filtered = deviceData.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(
      (item) =>
        item.name.toLowerCase().includes(keyword) ||
        item.id.toLowerCase().includes(keyword) ||
        item.type.toLowerCase().includes(keyword)
    )
  }

  // 车间过滤
  if (selectedWorkshop.value) {
    filtered = filtered.filter((item) => item.workshop === selectedWorkshop.value)
  }

  // 健康等级过滤
  if (selectedHealthLevel.value) {
    filtered = filtered.filter((item) => item.healthLevel === selectedHealthLevel.value)
  }

  return filtered
})

// 表格列定义
const columns = [
  {
    title: '设备编号',
    key: 'id',
    width: 100,
    fixed: 'left',
  },
  {
    title: '设备名称',
    key: 'name',
    width: 150,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '设备类型',
    key: 'type',
    width: 100,
  },
  {
    title: '所属车间',
    key: 'workshopName',
    width: 120,
  },
  {
    title: '健康评分',
    key: 'healthScore',
    width: 120,
    render: (row) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(
          'div',
          {
            style: {
              width: '60px',
              height: '6px',
              backgroundColor: '#f0f0f0',
              borderRadius: '3px',
              overflow: 'hidden',
            },
          },
          [
            h('div', {
              style: {
                width: `${row.healthScore}%`,
                height: '100%',
                backgroundColor: row.healthColor,
                transition: 'width 0.3s ease',
              },
            }),
          ]
        ),
        h('span', { style: { fontWeight: 'bold', color: row.healthColor } }, row.healthScore),
      ])
    },
  },
  {
    title: '健康状态',
    key: 'healthLevel',
    width: 100,
    render: (row) => {
      const getIcon = () => {
        switch (row.healthLevel) {
          case 'healthy':
            return HeartOutline
          case 'warning':
            return WarningOutline
          case 'error':
            return CloseCircleOutline
          default:
            return HeartOutline
        }
      }

      const getText = () => {
        switch (row.healthLevel) {
          case 'healthy':
            return '健康'
          case 'warning':
            return '警告'
          case 'error':
            return '故障'
          default:
            return '未知'
        }
      }

      return h('div', { style: 'display: flex; align-items: center; gap: 4px;' }, [
        h('n-icon', { color: row.healthColor, size: 16 }, { default: () => h(getIcon()) }),
        h('span', { style: { color: row.healthColor, fontWeight: 'bold' } }, getText()),
      ])
    },
  },
  {
    title: '运行状态',
    key: 'status',
    width: 100,
    render: (row) => {
      const isOnline = row.status === 'online'
      return h(
        'n-tag',
        {
          type: isOnline ? 'success' : 'error',
          size: 'small',
        },
        isOnline ? '在线' : '离线'
      )
    },
  },
  {
    title: '温度(°C)',
    key: 'temperature',
    width: 100,
    render: (row) => {
      const color = row.temperature > 40 ? '#d03050' : row.temperature > 35 ? '#f0a020' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.temperature)
    },
  },
  {
    title: '压力(kPa)',
    key: 'pressure',
    width: 100,
    render: (row) => {
      const color = row.pressure > 120 ? '#d03050' : row.pressure > 100 ? '#f0a020' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.pressure)
    },
  },
  {
    title: '振动(mm/s)',
    key: 'vibration',
    width: 100,
    render: (row) => {
      const color = row.vibration > 7 ? '#d03050' : row.vibration > 5 ? '#f0a020' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.vibration)
    },
  },
  {
    title: '更新时间',
    key: 'lastUpdate',
    width: 120,
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right',
    render: (row) => {
      return h('n-space', { size: 'small' }, [
        h(
          'n-button',
          {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => handleViewDetail(row),
          },
          {
            default: () => '详情',
            icon: () => h('n-icon', null, { default: () => h(EyeOutline) }),
          }
        ),
        h(
          'n-button',
          {
            size: 'small',
            type: 'warning',
            ghost: true,
            onClick: () => handleConfig(row),
          },
          {
            default: () => '配置',
            icon: () => h('n-icon', null, { default: () => h(SettingsOutline) }),
          }
        ),
      ])
    },
  },
]

// 方法
const handleSearch = () => {
  pagination.value.page = 1
}

const handleFilter = () => {
  pagination.value.page = 1
}

const handlePageChange = (page) => {
  pagination.value.page = page
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
}

const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    message.success('数据已刷新')
  }, 1000)
}

const exportData = () => {
  message.info('导出功能开发中...')
}

const handleViewDetail = (row) => {
  message.info(`查看设备 ${row.name} 的详细信息`)
}

const handleConfig = (row) => {
  message.info(`配置设备 ${row.name} 的参数`)
}

// 生命周期
onMounted(() => {
  pagination.value.itemCount = filteredData.value.length
})
</script>

<style scoped>
.health-list {
  height: 100%;
}

:deep(.n-data-table-th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background-color: #f8f9fa;
}
</style>
