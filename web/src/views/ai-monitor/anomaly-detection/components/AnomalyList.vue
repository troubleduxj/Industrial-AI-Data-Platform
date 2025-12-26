<template>
  <div class="anomaly-list">
    <n-data-table
      :columns="columns"
      :data="data"
      :loading="loading"
      :pagination="paginationReactive"
      :row-key="rowKey"
      :scroll-x="1200"
      striped
      size="small"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { NButton, NTag, NSpace, NPopconfirm, NTooltip, NIcon, NTime, useMessage } from 'naive-ui'
import {
  EyeOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  InformationCircleOutline,
  WarningOutline,
  AlertCircleOutline,
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['view-detail', 'handle-anomaly', 'ignore-anomaly'])

const message = useMessage()

// 分页配置
const paginationReactive = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
})

// 行键
const rowKey = (row) => row.id

// 获取异常类型图标
const getAnomalyTypeIcon = (type) => {
  const iconMap = {
    temperature: { icon: WarningOutline, color: '#ff6b6b' },
    pressure: { icon: AlertCircleOutline, color: '#ffa726' },
    vibration: { icon: InformationCircleOutline, color: '#42a5f5' },
    current: { icon: CheckmarkCircleOutline, color: '#ab47bc' },
  }
  return iconMap[type] || { icon: InformationCircleOutline, color: '#999' }
}

// 获取严重程度颜色
const getSeverityColor = (severity) => {
  const colorMap = {
    high: 'error',
    medium: 'warning',
    low: 'info',
  }
  return colorMap[severity] || 'default'
}

// 获取状态颜色
const getStatusColor = (status) => {
  const colorMap = {
    pending: 'warning',
    processing: 'info',
    resolved: 'success',
    ignored: 'default',
  }
  return colorMap[status] || 'default'
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 90) return '#18a058'
  if (confidence >= 70) return '#f0a020'
  return '#d03050'
}

// 表格列配置
const columns = [
  {
    title: '异常ID',
    key: 'id',
    width: 100,
    fixed: 'left',
    render: (row) => {
      return h(
        'span',
        {
          style: {
            fontFamily: 'monospace',
            fontSize: '12px',
            fontWeight: 'bold',
          },
        },
        row.id
      )
    },
  },
  {
    title: '设备信息',
    key: 'device',
    width: 180,
    render: (row) => {
      return h('div', [
        h(
          'div',
          {
            style: {
              fontWeight: '500',
              marginBottom: '2px',
            },
          },
          row.deviceName
        ),
        h(
          'div',
          {
            style: {
              fontSize: '11px',
              color: '#999',
              fontFamily: 'monospace',
            },
          },
          row.deviceId
        ),
      ])
    },
  },
  {
    title: '异常类型',
    key: 'type',
    width: 120,
    render: (row) => {
      const typeInfo = getAnomalyTypeIcon(row.type)
      return h(NSpace, { align: 'center', size: 4 }, [
        h(
          NIcon,
          {
            size: 14,
            color: typeInfo.color,
          },
          () => h(typeInfo.icon)
        ),
        h(
          'span',
          {
            style: { fontSize: '12px' },
          },
          row.typeName
        ),
      ])
    },
  },
  {
    title: '严重程度',
    key: 'severity',
    width: 100,
    render: (row) => {
      return h(
        NTag,
        {
          type: getSeverityColor(row.severity),
          size: 'small',
        },
        () => row.severityName
      )
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => {
      return h(
        NTag,
        {
          type: getStatusColor(row.status),
          size: 'small',
        },
        () => row.statusName
      )
    },
  },
  {
    title: '检测时间',
    key: 'detectedAt',
    width: 160,
    render: (row) => {
      return h(NTime, {
        time: new Date(row.detectedAt),
        format: 'yyyy-MM-dd HH:mm:ss',
        style: {
          fontSize: '12px',
        },
      })
    },
  },
  {
    title: 'AI置信度',
    key: 'confidence',
    width: 100,
    render: (row) => {
      return h(
        'div',
        {
          style: {
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          },
        },
        [
          h(
            'span',
            {
              style: {
                fontSize: '12px',
                fontWeight: '500',
                color: getConfidenceColor(row.confidence),
              },
            },
            `${row.confidence}%`
          ),
          h(
            'div',
            {
              style: {
                width: '40px',
                height: '4px',
                backgroundColor: '#f0f0f0',
                borderRadius: '2px',
                overflow: 'hidden',
              },
            },
            [
              h('div', {
                style: {
                  width: `${row.confidence}%`,
                  height: '100%',
                  backgroundColor: getConfidenceColor(row.confidence),
                  transition: 'width 0.3s ease',
                },
              }),
            ]
          ),
        ]
      )
    },
  },
  {
    title: '异常描述',
    key: 'description',
    width: 200,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => {
      return h(
        NTooltip,
        {
          trigger: 'hover',
        },
        {
          trigger: () =>
            h(
              'span',
              {
                style: {
                  fontSize: '12px',
                  cursor: 'pointer',
                },
              },
              row.description.length > 30
                ? row.description.substring(0, 30) + '...'
                : row.description
            ),
          default: () => row.description,
        }
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render: (row) => {
      return h(
        NSpace,
        { size: 4 },
        [
          h(
            NTooltip,
            {
              trigger: 'hover',
            },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'tiny',
                    type: 'primary',
                    ghost: true,
                    onClick: () => handleViewDetail(row),
                  },
                  {
                    icon: () => h(NIcon, { size: 14 }, () => h(EyeOutline)),
                  }
                ),
              default: () => '查看详情',
            }
          ),

          row.status === 'pending'
            ? h(
                NTooltip,
                {
                  trigger: 'hover',
                },
                {
                  trigger: () =>
                    h(
                      NButton,
                      {
                        size: 'tiny',
                        type: 'success',
                        ghost: true,
                        onClick: () => handleProcessAnomaly(row),
                      },
                      {
                        icon: () => h(NIcon, { size: 14 }, () => h(CheckmarkCircleOutline)),
                      }
                    ),
                  default: () => '标记处理',
                }
              )
            : null,

          row.status !== 'resolved' && row.status !== 'ignored'
            ? h(
                NPopconfirm,
                {
                  onPositiveClick: () => handleIgnoreAnomaly(row),
                },
                {
                  trigger: () =>
                    h(
                      NTooltip,
                      {
                        trigger: 'hover',
                      },
                      {
                        trigger: () =>
                          h(
                            NButton,
                            {
                              size: 'tiny',
                              type: 'error',
                              ghost: true,
                            },
                            {
                              icon: () => h(NIcon, { size: 14 }, () => h(CloseCircleOutline)),
                            }
                          ),
                        default: () => '忽略异常',
                      }
                    ),
                  default: () => '确定要忽略这个异常吗？',
                }
              )
            : null,
        ].filter(Boolean)
      )
    },
  },
]

// 方法
const handleViewDetail = (row) => {
  emit('view-detail', row)
}

const handleProcessAnomaly = (row) => {
  emit('handle-anomaly', row)
  message.success(`异常 ${row.id} 已标记为处理中`)
}

const handleIgnoreAnomaly = (row) => {
  emit('ignore-anomaly', row)
  message.info(`异常 ${row.id} 已忽略`)
}
</script>

<style scoped>
.anomaly-list {
  width: 100%;
}

:deep(.n-data-table-th) {
  font-weight: 600;
  background-color: #fafafa;
}

:deep(.n-data-table-td) {
  padding: 8px 12px;
}

:deep(.n-data-table-tr:hover) {
  background-color: #f8f9fa;
}

:deep(.n-button--tiny) {
  padding: 2px 6px;
  font-size: 11px;
}

:deep(.n-tag--small) {
  font-size: 11px;
  padding: 2px 6px;
}
</style>
