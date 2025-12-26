<template>
  <n-card title="分析历史" class="history-card">
    <template #header-extra>
      <n-space>
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索分析记录"
          clearable
          style="width: 200px"
        >
          <template #prefix>
            <n-icon><search-outline /></n-icon>
          </template>
        </n-input>
        <n-select
          v-model:value="statusFilter"
          :options="statusOptions"
          placeholder="状态筛选"
          clearable
          style="width: 120px"
        />
      </n-space>
    </template>

    <n-data-table
      :columns="columns"
      :data="filteredAnalyses"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      size="small"
    />
  </n-card>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import {
  NCard,
  NSpace,
  NInput,
  NSelect,
  NDataTable,
  NIcon,
  NButton,
  NTag,
  NTime,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import { SearchOutline, EyeOutline, TrashOutline, DownloadOutline } from '@vicons/ionicons5'

// Props
const props = defineProps({
  analyses: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['view', 'delete', 'download'])

// 响应式数据
const searchKeyword = ref('')
const statusFilter = ref(null)
const message = useMessage()

// 状态筛选选项
const statusOptions = [
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '进行中', value: 'running' },
]

// 分页配置
const pagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
}

// 获取分析类型文本
const getAnalysisTypeText = (type) => {
  const typeMap = {
    comprehensive: '综合分析',
    performance: '性能分析',
    anomaly: '异常检测',
    trend: '趋势分析',
    comparison: '对比分析',
  }
  return typeMap[type] || type
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const statusMap = {
    completed: 'success',
    failed: 'error',
    running: 'info',
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    completed: '已完成',
    failed: '失败',
    running: '进行中',
  }
  return statusMap[status] || status
}

// 表格列配置
const columns = [
  {
    title: '分析名称',
    key: 'name',
    width: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '分析类型',
    key: 'type',
    width: 120,
    render: (row) => getAnalysisTypeText(row.type),
  },
  {
    title: '设备数量',
    key: 'deviceCount',
    width: 100,
    render: (row) => `${row.deviceCount} 台`,
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) =>
      h(
        NTag,
        {
          type: getStatusTagType(row.status),
          size: 'small',
        },
        { default: () => getStatusText(row.status) }
      ),
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: 160,
    render: (row) =>
      h(NTime, {
        time: new Date(row.createdAt),
        format: 'yyyy-MM-dd HH:mm',
      }),
  },
  {
    title: '耗时',
    key: 'duration',
    width: 80,
    render: (row) => (row.status === 'completed' ? `${row.duration}s` : '-'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) =>
      h(
        NSpace,
        { size: 'small' },
        {
          default: () =>
            [
              h(
                NButton,
                {
                  size: 'small',
                  type: 'primary',
                  ghost: true,
                  onClick: () => handleView(row),
                },
                {
                  icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
                  default: () => '查看',
                }
              ),
              row.status === 'completed' &&
                h(
                  NButton,
                  {
                    size: 'small',
                    onClick: () => handleDownload(row),
                  },
                  {
                    icon: () => h(NIcon, null, { default: () => h(DownloadOutline) }),
                  }
                ),
              h(
                NPopconfirm,
                {
                  onPositiveClick: () => handleDelete(row),
                },
                {
                  trigger: () =>
                    h(
                      NButton,
                      {
                        size: 'small',
                        type: 'error',
                        ghost: true,
                      },
                      {
                        icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
                      }
                    ),
                  default: () => '确定删除这条分析记录吗？',
                }
              ),
            ].filter(Boolean),
        }
      ),
  },
]

// 过滤后的分析数据
const filteredAnalyses = computed(() => {
  let filtered = props.analyses

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(
      (analysis) =>
        analysis.name.toLowerCase().includes(keyword) ||
        getAnalysisTypeText(analysis.type).toLowerCase().includes(keyword)
    )
  }

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter((analysis) => analysis.status === statusFilter.value)
  }

  return filtered
})

// 处理查看操作
const handleView = (analysis) => {
  emit('view', analysis)
}

// 处理下载操作
const handleDownload = (analysis) => {
  emit('download', analysis)
  message.info(`正在下载 ${analysis.name} 的分析报告...`)
}

// 处理删除操作
const handleDelete = (analysis) => {
  emit('delete', analysis)
}
</script>

<style scoped>
.history-card {
  margin-top: 16px;
}
</style>
