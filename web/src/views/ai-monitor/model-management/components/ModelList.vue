<template>
  <n-card title="模型列表">
    <n-data-table
      :columns="columns"
      :data="models"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      size="small"
    />
  </n-card>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import {
  NCard,
  NDataTable,
  NButton,
  NButtonGroup,
  NTag,
  NIcon,
  NTooltip,
  NSpace,
  NProgress,
  useMessage,
} from 'naive-ui'
import {
  PlayOutline,
  StopOutline,
  TrashOutline,
  EyeOutline,
  DownloadOutline,
  InformationCircleOutline,
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  models: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

// Emits
const emit = defineEmits(['deploy', 'stop', 'delete', 'view-detail', 'download'])

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 个模型`,
})

// 获取状态标签类型
const getStatusType = (status) => {
  const statusMap = {
    deployed: 'success', // 对应 running/deployed
    stopped: 'default',
    training: 'warning',
    draft: 'default', // 草稿
    trained: 'info', // 已训练
    error: 'error',
    failed: 'error',
    archived: 'default'
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    deployed: '已部署',
    stopped: '已停止',
    training: '训练中',
    draft: '草稿',
    trained: '已训练',
    error: '错误',
    failed: '失败',
    archived: '已归档'
  }
  return statusMap[status] || status
}

// 获取模型类型文本
const getTypeText = (type) => {
  const typeMap = {
    anomaly_detection: '异常检测',
    trend_prediction: '趋势预测',
    health_scoring: '健康评分',
    classification: '分类模型',
    regression: '回归模型',
  }
  return typeMap[type] || type
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 表格列配置
const columns = [
  {
    title: '模型名称',
    key: 'name',
    width: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '版本',
    key: 'version',
    width: 80,
    align: 'center',
  },
  {
    title: '类型',
    key: 'type',
    width: 120,
    render: (row) => {
      return h(
        NTag,
        {
          type: 'info',
          size: 'small',
        },
        {
          default: () => getTypeText(row.type),
        }
      )
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 150,
    render: (row) => {
      const tag = h(
        NTag,
        {
          type: getStatusType(row.status),
          size: 'small',
        },
        {
          default: () => getStatusText(row.status),
        }
      )

      if (row.status === 'training') {
        return h(
          NSpace,
          { vertical: true, size: 'small' },
          {
            default: () => [
              tag,
              h(NProgress, {
                type: 'line',
                percentage: row.progress || 0,
                showIndicator: true,
                height: 4,
                processing: true
              })
            ]
          }
        )
      }

      return tag
    },
  },
  {
    title: '准确率',
    key: 'accuracy',
    width: 120,
    render: (row) => {
      const accuracy = parseFloat(row.accuracy)
      let status = 'success'
      if (accuracy < 80) status = 'error'
      else if (accuracy < 90) status = 'warning'

      return h(
        NSpace,
        { align: 'center' },
        {
          default: () => [
            h(NProgress, {
              type: 'line',
              percentage: accuracy,
              status,
              showIndicator: false,
              height: 6,
              style: { width: '60px' },
            }),
            h('span', { style: { fontSize: '12px' } }, `${accuracy}%`),
          ],
        }
      )
    },
  },
  {
    title: '大小',
    key: 'size',
    width: 80,
    align: 'center',
  },
  {
    title: '作者',
    key: 'author',
    width: 100,
    align: 'center',
  },
  {
    title: '创建时间',
    key: 'createdAt',
    width: 160,
    render: (row) => formatDate(row.createdAt),
  },
  {
    title: '部署时间',
    key: 'deployedAt',
    width: 160,
    render: (row) => formatDate(row.deployedAt),
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render: (row) => {
      return h(
        NButtonGroup,
        { size: 'small' },
        {
          default: () => [
            // 查看详情
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
                      size: 'small',
                      quaternary: true,
                      onClick: () => emit('view-detail', row),
                    },
                    {
                      icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
                    }
                  ),
                default: () => '查看详情',
              }
            ),

            // 部署/停止
            row.status === 'deployed'
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
                          size: 'small',
                          quaternary: true,
                          type: 'warning',
                          onClick: () => emit('stop', row),
                        },
                        {
                          icon: () => h(NIcon, null, { default: () => h(StopOutline) }),
                        }
                      ),
                    default: () => '停止模型',
                  }
                )
              : h(
                  NTooltip,
                  {
                    trigger: 'hover',
                  },
                  {
                    trigger: () =>
                      h(
                        NButton,
                        {
                          size: 'small',
                          quaternary: true,
                          type: 'success',
                          disabled: row.status !== 'trained',
                          onClick: () => emit('deploy', row),
                        },
                        {
                          icon: () => h(NIcon, null, { default: () => h(PlayOutline) }),
                        }
                      ),
                    default: () => '部署模型',
                  }
                ),

            // 下载
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
                      size: 'small',
                      quaternary: true,
                      type: 'info',
                      onClick: () => emit('download', row),
                    },
                    {
                      icon: () => h(NIcon, null, { default: () => h(DownloadOutline) }),
                    }
                  ),
                default: () => '下载模型',
              }
            ),

            // 删除
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
                      size: 'small',
                      quaternary: true,
                      type: 'error',
                      disabled: row.status === 'running',
                      onClick: () => emit('delete', row),
                    },
                    {
                      icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
                    }
                  ),
                default: () => '删除模型',
              }
            ),
          ],
        }
      )
    },
  },
]
</script>

<style scoped>
/* 表格样式可以在这里自定义 */
</style>
