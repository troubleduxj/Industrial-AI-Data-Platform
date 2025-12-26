<template>
  <CommonPage
    show-footer
    title="组件管理"
    class="system-components-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <NButton type="primary" @click="refreshComponents">
          <TheIcon icon="material-symbols:refresh" :size="18" class="mr-1" />
          刷新组件
        </NButton>
        <NButton type="info" @click="checkComponentHealth">
          <TheIcon icon="material-symbols:health-and-safety" :size="18" class="mr-1" />
          健康检查
        </NButton>
      </div>
    </template>

    <!-- 组件统计卡片 -->
    <div class="stats-grid">
      <NCard class="stats-card">
        <div class="stats-content">
          <div class="stats-info">
            <div class="primary stats-number">{{ componentStats.total }}</div>
            <div class="stats-label">总组件数</div>
          </div>
          <TheIcon icon="material-symbols:widgets" :size="32" class="primary stats-icon" />
        </div>
      </NCard>

      <NCard class="stats-card">
        <div class="stats-content">
          <div class="stats-info">
            <div class="stats-number success">{{ componentStats.active }}</div>
            <div class="stats-label">活跃组件</div>
          </div>
          <TheIcon icon="material-symbols:check-circle" :size="32" class="stats-icon success" />
        </div>
      </NCard>

      <NCard class="stats-card">
        <div class="stats-content">
          <div class="stats-info">
            <div class="stats-number warning">{{ componentStats.deprecated }}</div>
            <div class="stats-label">已废弃</div>
          </div>
          <TheIcon icon="material-symbols:warning" :size="32" class="stats-icon warning" />
        </div>
      </NCard>

      <NCard class="stats-card">
        <div class="stats-content">
          <div class="stats-info">
            <div class="stats-number error">{{ componentStats.errors }}</div>
            <div class="stats-label">错误组件</div>
          </div>
          <TheIcon icon="material-symbols:error" :size="32" class="stats-icon error" />
        </div>
      </NCard>
    </div>

    <!-- 组件列表表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :data="filteredComponents"
      :loading="loading"
      :pagination="false"
    >
      <template #queryBar>
        <QueryBarItem label="组件名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入组件名称"
            @input="filterComponents"
          />
        </QueryBarItem>
        <QueryBarItem label="组件类型" :label-width="80">
          <NSelect
            v-model:value="queryItems.type"
            clearable
            placeholder="请选择类型"
            :options="typeOptions"
            @update:value="filterComponents"
          />
        </QueryBarItem>
        <QueryBarItem label="组件分类" :label-width="80">
          <NSelect
            v-model:value="queryItems.category"
            clearable
            placeholder="请选择分类"
            :options="categoryOptions"
            @update:value="filterComponents"
          />
        </QueryBarItem>
        <QueryBarItem label="组件状态" :label-width="80">
          <NSelect
            v-model:value="queryItems.status"
            clearable
            placeholder="请选择状态"
            :options="statusOptions"
            @update:value="filterComponents"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 组件详情抽屉 -->
    <NDrawer v-model:show="drawerVisible" :width="700" placement="right">
      <NDrawerContent title="组件详情">
        <div v-if="selectedComponent" class="component-detail">
          <!-- 基本信息 -->
          <NCard title="基本信息" size="small" class="detail-card">
            <div class="detail-grid">
              <div class="detail-item">
                <div class="detail-label">组件名称</div>
                <div class="detail-value">{{ selectedComponent.name }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">组件类型</div>
                <NTag :type="getComponentTypeColor(selectedComponent.type)">
                  {{ selectedComponent.type }}
                </NTag>
              </div>
              <div class="detail-item">
                <div class="detail-label">版本</div>
                <div class="detail-value">{{ selectedComponent.version }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">状态</div>
                <NTag :type="getStatusColor(selectedComponent.status)">
                  {{ getStatusText(selectedComponent.status) }}
                </NTag>
              </div>
              <div class="detail-item">
                <div class="detail-label">使用次数</div>
                <div class="detail-value">{{ selectedComponent.usageCount }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">分类</div>
                <div class="detail-value">{{ selectedComponent.category }}</div>
              </div>
            </div>
          </NCard>

          <!-- 组件描述 -->
          <NCard title="组件描述" size="small" class="detail-card">
            <p class="component-description">{{ selectedComponent.description }}</p>
          </NCard>

          <!-- 组件实时预览 -->
          <NCard title="组件预览" size="small" class="detail-card">
            <div class="component-preview">
              <div class="preview-container">
                <component
                  :is="getPreviewComponent(selectedComponent.name)"
                  v-bind="getPreviewProps(selectedComponent.name)"
                  class="preview-component"
                />
              </div>
              <div class="preview-info">
                <div class="preview-note">
                  <TheIcon icon="material-symbols:info" :size="16" />
                  <span>这是 {{ selectedComponent.name }} 组件的实时预览</span>
                </div>
              </div>
            </div>
          </NCard>

          <!-- 样式预览 -->
          <NCard title="样式信息" size="small" class="detail-card">
            <div class="style-preview">
              <div class="preview-item">
                <div class="preview-label">主色调</div>
                <div
                  class="color-swatch"
                  :style="{ backgroundColor: getComponentColor(selectedComponent.type) }"
                ></div>
              </div>
              <div class="preview-item">
                <div class="preview-label">图标</div>
                <TheIcon :icon="getComponentIcon(selectedComponent.type)" :size="24" />
              </div>
              <div class="preview-item">
                <div class="preview-label">标签样式</div>
                <NTag :type="getComponentTypeColor(selectedComponent.type)" size="medium">
                  {{ selectedComponent.type }}
                </NTag>
              </div>
            </div>
          </NCard>

          <!-- 使用统计 -->
          <NCard title="使用统计" size="small" class="detail-card">
            <div class="usage-stats">
              <div class="usage-item">
                <div class="usage-label">总使用次数</div>
                <div class="usage-value">{{ selectedComponent.usageCount }}</div>
              </div>
              <div class="usage-item">
                <div class="usage-label">最后更新</div>
                <div class="usage-value">{{ formatDate(selectedComponent.lastUpdated) }}</div>
              </div>
              <div class="usage-item">
                <div class="usage-label">文件大小</div>
                <div class="usage-value">{{ selectedComponent.fileSize || '未知' }}</div>
              </div>
            </div>
          </NCard>

          <!-- 依赖关系 -->
          <NCard title="依赖关系" size="small" class="detail-card">
            <div class="dependencies">
              <div class="dep-section">
                <div class="dep-title">依赖组件</div>
                <div class="dep-list">
                  <NTag
                    v-for="dep in selectedComponent.dependencies"
                    :key="dep"
                    size="small"
                    class="dep-tag"
                  >
                    {{ dep }}
                  </NTag>
                  <span v-if="!selectedComponent.dependencies?.length" class="no-deps">无依赖</span>
                </div>
              </div>
              <div class="dep-section">
                <div class="dep-title">被依赖组件</div>
                <div class="dep-list">
                  <NTag
                    v-for="dep in selectedComponent.dependents"
                    :key="dep"
                    size="small"
                    class="dep-tag"
                  >
                    {{ dep }}
                  </NTag>
                  <span v-if="!selectedComponent.dependents?.length" class="no-deps">无被依赖</span>
                </div>
              </div>
            </div>
          </NCard>
        </div>
      </NDrawerContent>
    </NDrawer>

    <!-- 健康检查结果模态框 -->
    <NModal
      v-model:show="healthCheckVisible"
      preset="card"
      title="组件健康检查报告"
      style="width: 900px"
    >
      <div v-if="healthCheckResults" class="health-check-report">
        <NAlert
          :type="healthCheckResults.overall === 'healthy' ? 'success' : 'warning'"
          :title="`整体状态: ${healthCheckResults.overall === 'healthy' ? '健康' : '需要关注'}`"
          class="mb-4"
        />

        <!-- 分类统计 -->
        <NCard title="分类统计" size="small" class="mb-4">
          <div class="category-stats">
            <div v-for="(count, category) in categoryStats" :key="category" class="category-item">
              <span class="category-name">{{ getCategoryLabel(category) }}</span>
              <span class="category-count">{{ count }} 个组件</span>
            </div>
          </div>
        </NCard>

        <!-- 使用频率分析 -->
        <NCard title="使用频率分析" size="small" class="mb-4">
          <div class="usage-analysis">
            <div class="usage-item">
              <span class="usage-label">高频使用 (>50次)</span>
              <span class="usage-value">{{ highUsageComponents.length }} 个</span>
            </div>
            <div class="usage-item">
              <span class="usage-label">中频使用 (20-50次)</span>
              <span class="usage-value">{{ mediumUsageComponents.length }} 个</span>
            </div>
            <div class="usage-item">
              <span class="usage-label">低频使用 (<20次)</span>
              <span class="usage-value">{{ lowUsageComponents.length }} 个</span>
            </div>
          </div>
        </NCard>

        <!-- 需要关注的组件 -->
        <NCard title="需要关注的组件" size="small">
          <div class="attention-components">
            <div v-if="deprecatedComponents.length > 0" class="attention-section">
              <h4>已废弃组件 ({{ deprecatedComponents.length }})</h4>
              <div class="component-list">
                <NTag
                  v-for="comp in deprecatedComponents"
                  :key="comp.id"
                  type="warning"
                  size="small"
                >
                  {{ comp.name }}
                </NTag>
              </div>
            </div>
            <div v-if="errorComponents.length > 0" class="attention-section">
              <h4>错误组件 ({{ errorComponents.length }})</h4>
              <div class="component-list">
                <NTag v-for="comp in errorComponents" :key="comp.id" type="error" size="small">
                  {{ comp.name }}
                </NTag>
              </div>
            </div>
            <div v-if="unusedComponents.length > 0" class="attention-section">
              <h4>未使用组件 ({{ unusedComponents.length }})</h4>
              <div class="component-list">
                <NTag v-for="comp in unusedComponents" :key="comp.id" type="default" size="small">
                  {{ comp.name }}
                </NTag>
              </div>
            </div>
          </div>
        </NCard>
      </div>
    </NModal>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, defineAsyncComponent } from 'vue'
import {
  NButton,
  NCard,
  NTag,
  NInput,
  NSelect,
  NDrawer,
  NDrawerContent,
  NModal,
  NAlert,
  NProgress,
  NStatistic,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import { generateComponentData, getComponentStats } from '@/utils/component-scanner.js'

// 预览组件映射
const PreviewComponents = {
  // 通用组件预览
  CommonPagePreview: defineAsyncComponent(() => import('@/components/page/CommonPage.vue')),
  CrudTablePreview: defineAsyncComponent(() => import('@/components/table/CrudTable.vue')),
  CrudModalPreview: defineAsyncComponent(() => import('@/components/table/CrudModal.vue')),
  BatchDeleteButtonPreview: BatchDeleteButton,
  TheIconPreview: TheIcon,
  QueryBarItemPreview: QueryBarItem,

  // 卡片组件预览
  BaseCardPreview: NCard,
  DeviceCardPreview: NCard,
  StatCardPreview: NCard,

  // 表单组件预览
  StandardFormPreview: defineAsyncComponent(() =>
    Promise.resolve({
      template: `
        <div class="form-preview">
          <n-form label-placement="left" :label-width="80">
            <n-form-item label="用户名">
              <n-input placeholder="请输入用户名" />
            </n-form-item>
            <n-form-item label="邮箱">
              <n-input placeholder="请输入邮箱" />
            </n-form-item>
            <n-form-item label="状态">
              <n-select placeholder="请选择状态" :options="[{label:'启用',value:'active'},{label:'禁用',value:'inactive'}]" />
            </n-form-item>
          </n-form>
        </div>
      `,
      components: {
        NForm: () => import('naive-ui').then((m) => m.NForm),
        NFormItem: () => import('naive-ui').then((m) => m.NFormItem),
        NInput: () => import('naive-ui').then((m) => m.NInput),
        NSelect: () => import('naive-ui').then((m) => m.NSelect),
      },
    })
  ),

  // 图表组件预览
  MetricsChartPreview: defineAsyncComponent(() =>
    Promise.resolve({
      template: `
        <div class="chart-preview">
          <n-card title="数据趋势" size="small">
            <div class="mock-chart">
              <div class="chart-bars">
                <div class="bar" style="height: 60%"></div>
                <div class="bar" style="height: 80%"></div>
                <div class="bar" style="height: 45%"></div>
                <div class="bar" style="height: 90%"></div>
                <div class="bar" style="height: 70%"></div>
              </div>
              <div class="chart-labels">
                <span>1月</span><span>2月</span><span>3月</span><span>4月</span><span>5月</span>
              </div>
            </div>
          </n-card>
        </div>
      `,
      components: { NCard },
    })
  ),

  // AI监控组件预览
  StatusIndicatorPreview: defineAsyncComponent(() =>
    Promise.resolve({
      template: `
        <div class="status-preview">
          <div class="status-item">
            <n-tag type="success" size="small">
              <template #icon><the-icon icon="material-symbols:check-circle" /></template>
              运行正常
            </n-tag>
          </div>
          <div class="status-item">
            <n-tag type="warning" size="small">
              <template #icon><the-icon icon="material-symbols:warning" /></template>
              需要关注
            </n-tag>
          </div>
          <div class="status-item">
            <n-tag type="error" size="small">
              <template #icon><the-icon icon="material-symbols:error" /></template>
              异常状态
            </n-tag>
          </div>
        </div>
      `,
      components: { NTag, TheIcon },
    })
  ),

  // 设备组件预览
  DeviceStatusCardPreview: defineAsyncComponent(() =>
    Promise.resolve({
      template: `
        <n-card title="设备状态" size="small" class="device-preview">
          <template #header-extra>
            <n-tag type="success" size="small">在线</n-tag>
          </template>
          <div class="device-info">
            <n-statistic label="CPU使用率" :value="75" suffix="%" />
            <n-statistic label="内存使用" :value="8.2" suffix="GB" />
            <n-statistic label="运行时间" :value="24" suffix="小时" />
          </div>
          <template #footer>
            <n-progress type="line" :percentage="75" status="success" />
          </template>
        </n-card>
      `,
      components: { NCard, NTag, NStatistic, NProgress },
    })
  ),
}

defineOptions({ name: 'ComponentManagement' })

const $message = useMessage()
const $table = ref(null)
const queryItems = ref({})
const loading = ref(false)
const drawerVisible = ref(false)
const healthCheckVisible = ref(false)
const selectedComponent = ref(null)
const healthCheckResults = ref(null)
// 组件数据
const components = ref([])

// 初始化组件数据
onMounted(() => {
  components.value = generateComponentData()
})

// 组件统计
const componentStats = computed(() => {
  const total = components.value.length
  const active = components.value.filter((c) => c.status === 'active').length
  const deprecated = components.value.filter((c) => c.status === 'deprecated').length
  const errors = components.value.filter((c) => c.status === 'error').length

  return { total, active, deprecated, errors }
})

// 过滤后的组件
const filteredComponents = computed(() => {
  let filtered = components.value

  if (queryItems.value.name) {
    filtered = filtered.filter(
      (c) =>
        c.name.toLowerCase().includes(queryItems.value.name.toLowerCase()) ||
        c.description.toLowerCase().includes(queryItems.value.name.toLowerCase())
    )
  }

  if (queryItems.value.type) {
    filtered = filtered.filter((c) => c.type === queryItems.value.type)
  }

  if (queryItems.value.category) {
    filtered = filtered.filter((c) => c.category === queryItems.value.category)
  }

  if (queryItems.value.status) {
    filtered = filtered.filter((c) => c.status === queryItems.value.status)
  }

  return filtered
})

// 动态生成选项
const typeOptions = computed(() => {
  const types = [...new Set(components.value.map((c) => c.type))]
  return types.map((type) => ({ label: type, value: type }))
})

const categoryOptions = computed(() => {
  const categories = [...new Set(components.value.map((c) => c.category))]
  return categories.map((category) => ({
    label: getCategoryLabel(category),
    value: category,
  }))
})

const statusOptions = [
  { label: '活跃', value: 'active' },
  { label: '已废弃', value: 'deprecated' },
  { label: '错误', value: 'error' },
]

// 分类标签映射
const getCategoryLabel = (category) => {
  const labelMap = {
    'ai-monitor': 'AI监控',
    business: '业务组件',
    card: '卡片组件',
    chart: '图表组件',
    'chat-widget': '聊天组件',
    common: '通用组件',
    form: '表单组件',
    icon: '图标组件',
    layout: '布局组件',
    page: '页面组件',
    table: '表格组件',
    theme: '主题组件',
    deprecated: '已废弃',
    error: '错误组件',
  }
  return labelMap[category] || category
}

// 表格列定义
const columns = [
  {
    title: '组件名称',
    key: 'name',
    width: 200,
    render: (row) => {
      return h('div', { class: 'flex items-center component-name-cell' }, [
        h(TheIcon, {
          icon: getComponentIcon(row.type),
          size: 18,
          class: 'component-icon',
          style: { color: getComponentColor(row.type) },
        }),
        h('div', { class: 'component-info' }, [
          h('div', { class: 'component-name' }, row.name),
          h('div', { class: 'component-category' }, row.category),
        ]),
      ])
    },
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
    render: (row) => {
      return h(
        NTag,
        {
          type: getComponentTypeColor(row.type),
          size: 'small',
        },
        { default: () => row.type }
      )
    },
  },
  {
    title: '版本',
    key: 'version',
    width: 100,
    align: 'center',
    render: (row) => {
      return h('span', { class: 'version-text' }, row.version)
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
        { default: () => getStatusText(row.status) }
      )
    },
  },
  {
    title: '使用次数',
    key: 'usageCount',
    width: 100,
    align: 'center',
    render: (row) => {
      return h(
        'span',
        {
          class: 'usage-count',
          style: {
            color:
              row.usageCount > 50
                ? 'var(--success-color)'
                : row.usageCount > 20
                ? 'var(--warning-color)'
                : 'var(--text-color-secondary)',
          },
        },
        row.usageCount
      )
    },
  },
  {
    title: '文件大小',
    key: 'fileSize',
    width: 100,
    align: 'center',
    render: (row) => {
      return h('span', { class: 'file-size' }, row.fileSize || '未知')
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    render: (row) => {
      return h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          onClick: () => viewComponent(row),
        },
        {
          default: () => '查看详情',
          icon: () => h(TheIcon, { icon: 'material-symbols:visibility', size: 14 }),
        }
      )
    },
  },
]

// 方法
const filterComponents = () => {
  // 触发重新计算过滤结果
}

const refreshComponents = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    $message.success('组件列表已刷新')
  }, 1000)
}

const checkComponentHealth = () => {
  const stats = componentStats.value
  const hasIssues = stats.deprecated > 0 || stats.errors > 0

  healthCheckResults.value = {
    overall: hasIssues ? 'warning' : 'healthy',
    timestamp: new Date().toISOString(),
  }
  healthCheckVisible.value = true
  $message.success('组件健康检查完成')
}

// 健康检查相关的计算属性
const categoryStats = computed(() => {
  const stats = {}
  components.value.forEach((comp) => {
    stats[comp.category] = (stats[comp.category] || 0) + 1
  })
  return stats
})

const highUsageComponents = computed(() => components.value.filter((c) => c.usageCount > 50))

const mediumUsageComponents = computed(() =>
  components.value.filter((c) => c.usageCount >= 20 && c.usageCount <= 50)
)

const lowUsageComponents = computed(() =>
  components.value.filter((c) => c.usageCount < 20 && c.usageCount > 0)
)

const deprecatedComponents = computed(() =>
  components.value.filter((c) => c.status === 'deprecated')
)

const errorComponents = computed(() => components.value.filter((c) => c.status === 'error'))

const unusedComponents = computed(() =>
  components.value.filter((c) => c.usageCount === 0 && c.status === 'active')
)

const viewComponent = (component) => {
  selectedComponent.value = component
  drawerVisible.value = true
}

// 辅助函数
const getComponentIcon = (type) => {
  const iconMap = {
    Layout: 'material-symbols:view-quilt',
    Data: 'material-symbols:table-chart',
    Feedback: 'material-symbols:feedback',
    Action: 'material-symbols:touch-app',
    Unknown: 'material-symbols:help',
  }
  return iconMap[type] || 'material-symbols:widgets'
}

const getComponentTypeColor = (type) => {
  const colorMap = {
    Layout: 'info',
    Data: 'success',
    Feedback: 'warning',
    Action: 'error',
    Unknown: 'default',
  }
  return colorMap[type] || 'default'
}

const getStatusColor = (status) => {
  const colorMap = {
    active: 'success',
    deprecated: 'warning',
    error: 'error',
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status) => {
  const textMap = {
    active: '活跃',
    deprecated: '已废弃',
    error: '错误',
  }
  return textMap[status] || status
}

const getComponentColor = (type) => {
  const colorMap = {
    Layout: 'var(--info-color)',
    Data: 'var(--success-color)',
    Feedback: 'var(--warning-color)',
    Action: 'var(--error-color)',
    Display: 'var(--primary-color)',
    Form: 'var(--info-color)',
    Unknown: 'var(--text-color-secondary)',
  }
  return colorMap[type] || 'var(--text-color-secondary)'
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    return '日期格式错误'
  }
}

// 获取预览组件
const getPreviewComponent = (componentName) => {
  const previewMap = {
    CommonPage: PreviewComponents.CommonPagePreview,
    CrudTable: PreviewComponents.CrudTablePreview,
    CrudModal: PreviewComponents.CrudModalPreview,
    BatchDeleteButton: PreviewComponents.BatchDeleteButtonPreview,
    TheIcon: PreviewComponents.TheIconPreview,
    QueryBarItem: PreviewComponents.QueryBarItemPreview,
    BaseCard: PreviewComponents.BaseCardPreview,
    DeviceCard: PreviewComponents.DeviceCardPreview,
    StatCard: PreviewComponents.StatCardPreview,
    StandardForm: PreviewComponents.StandardFormPreview,
    MetricsChart: PreviewComponents.MetricsChartPreview,
    StatusIndicator: PreviewComponents.StatusIndicatorPreview,
    DeviceStatusCard: PreviewComponents.DeviceStatusCardPreview,
    StandardDataTable: PreviewComponents.CrudTablePreview,
    DataChart: PreviewComponents.MetricsChartPreview,
    AIChart: PreviewComponents.MetricsChartPreview,
    ModelSelector: PreviewComponents.StandardFormPreview,
    TaskStatusCard: PreviewComponents.StatCardPreview,
    DeviceCardSkeleton: PreviewComponents.BaseCardPreview,
    ChatWidgetContainer: PreviewComponents.BaseCardPreview,
    FloatingChatWidget: PreviewComponents.BaseCardPreview,
    LoadingComponent: defineAsyncComponent(() =>
      Promise.resolve({
        template: `
          <div class="loading-preview">
            <n-spin size="medium">
              <template #description>加载中...</template>
            </n-spin>
          </div>
        `,
        components: { NSpin: () => import('naive-ui').then((m) => m.NSpin) },
      })
    ),
    PermissionButton: PreviewComponents.BatchDeleteButtonPreview,
    IconPicker: PreviewComponents.TheIconPreview,
    ThemeComplianceDashboard: PreviewComponents.DeviceStatusCardPreview,
    ResponsiveGrid: PreviewComponents.BaseCardPreview,
    // 废弃和错误组件的预览
    LegacyDataTable: () =>
      h('div', { class: 'deprecated-preview' }, [
        h('div', { class: 'deprecated-content' }, [
          h(TheIcon, {
            icon: 'material-symbols:warning',
            size: 24,
            style: { color: 'var(--warning-color)' },
          }),
          h('span', '已废弃的组件'),
        ]),
      ]),
    OldFormBuilder: () =>
      h('div', { class: 'deprecated-preview' }, [
        h('div', { class: 'deprecated-content' }, [
          h(TheIcon, {
            icon: 'material-symbols:warning',
            size: 24,
            style: { color: 'var(--warning-color)' },
          }),
          h('span', '已废弃的表单构建器'),
        ]),
      ]),
    BrokenComponent: () =>
      h('div', { class: 'error-preview' }, [
        h('div', { class: 'error-content' }, [
          h(TheIcon, {
            icon: 'material-symbols:error',
            size: 24,
            style: { color: 'var(--error-color)' },
          }),
          h('span', '组件存在错误'),
        ]),
      ]),
  }

  return (
    previewMap[componentName] ||
    (() =>
      h('div', { class: 'fallback-preview' }, [
        h('div', { class: 'fallback-content' }, [
          h(TheIcon, {
            icon: 'material-symbols:widgets',
            size: 32,
            style: { color: 'var(--text-color-secondary)' },
          }),
          h('span', `${componentName} 组件`),
          h('small', '暂无预览'),
        ]),
      ]))
  )
}

// 获取预览组件的属性
const getPreviewProps = (componentName) => {
  const propsMap = {
    CommonPage: {
      title: '页面标题示例',
      showFooter: true,
    },
    CrudTable: {
      columns: [
        { title: 'ID', key: 'id', width: 80 },
        { title: '名称', key: 'name', width: 120 },
        { title: '状态', key: 'status', width: 100 },
      ],
      data: [
        { id: 1, name: '示例数据1', status: '正常' },
        { id: 2, name: '示例数据2', status: '正常' },
      ],
      pagination: false,
    },
    BatchDeleteButton: {
      type: 'error',
      size: 'small',
      disabled: false,
    },
    TheIcon: {
      icon: getComponentIcon('Display'),
      size: 32,
    },
    BaseCard: {
      title: '基础卡片示例',
      size: 'small',
    },
    DeviceCard: {
      title: '设备卡片',
      size: 'small',
    },
    StatCard: {
      title: '统计卡片',
      size: 'small',
    },
    TaskStatusCard: {
      title: '任务状态',
      size: 'small',
    },
    ChatWidgetContainer: {
      title: '聊天组件',
      size: 'small',
    },
    FloatingChatWidget: {
      title: '浮动聊天',
      size: 'small',
    },
    ResponsiveGrid: {
      title: '响应式网格',
      size: 'small',
    },
    PermissionButton: {
      type: 'primary',
      size: 'small',
    },
    IconPicker: {
      icon: 'material-symbols:palette',
      size: 24,
    },
  }

  return propsMap[componentName] || { title: '组件预览', size: 'small' }
}
</script>

<style scoped>
/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 统计卡片样式 */
.stats-card {
  transition: all var(--transition-fast);
  border: var(--border-base);
  border-radius: var(--border-radius-base);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-color-light);
}

.stats-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
}

.stats-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stats-number {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
}

.stats-number.primary {
  color: var(--primary-color);
}
.stats-number.success {
  color: var(--success-color);
}
.stats-number.warning {
  color: var(--warning-color);
}
.stats-number.error {
  color: var(--error-color);
}

.stats-label {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
  font-weight: var(--font-weight-medium);
}

.stats-icon {
  opacity: 0.8;
  transition: opacity var(--transition-fast);
}

.stats-icon.primary {
  color: var(--primary-color);
}
.stats-icon.success {
  color: var(--success-color);
}
.stats-icon.warning {
  color: var(--warning-color);
}
.stats-icon.error {
  color: var(--error-color);
}

.stats-card:hover .stats-icon {
  opacity: 1;
}

/* 组件详情样式 */
.component-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.detail-card {
  border: var(--border-base);
  border-radius: var(--border-radius-base);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.detail-label {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
  font-weight: var(--font-weight-medium);
}

.detail-value {
  font-size: var(--font-size-base);
  color: var(--text-color-primary);
  font-weight: var(--font-weight-medium);
}

.component-description {
  font-size: var(--font-size-base);
  color: var(--text-color-primary);
  line-height: 1.6;
  margin: 0;
}

/* 样式预览 */
.style-preview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.preview-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.preview-label {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
  min-width: 80px;
}

.color-swatch {
  width: 24px;
  height: 24px;
  border-radius: var(--border-radius-small);
  border: var(--border-base);
}

/* 使用统计 */
.usage-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.usage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background-color: var(--background-color-light);
  border-radius: var(--border-radius-small);
}

.usage-label {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.usage-value {
  font-size: var(--font-size-base);
  color: var(--text-color-primary);
  font-weight: var(--font-weight-medium);
}

/* 依赖关系 */
.dependencies {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.dep-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.dep-title {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
  font-weight: var(--font-weight-medium);
}

.dep-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.dep-tag {
  font-size: var(--font-size-xs);
}

.no-deps {
  font-size: var(--font-size-sm);
  color: var(--text-color-placeholder);
  font-style: italic;
}

/* 表格样式 */
.component-name-cell {
  gap: var(--spacing-sm);
}

.component-icon {
  flex-shrink: 0;
}

.component-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.component-name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-color-primary);
}

.component-category {
  font-size: var(--font-size-xs);
  color: var(--text-color-secondary);
  text-transform: capitalize;
}

.version-text {
  font-family: var(--font-family-mono, 'Monaco', 'Consolas', monospace);
  font-size: var(--font-size-sm);
  color: var(--text-color-primary);
  background-color: var(--background-color-light);
  padding: 2px 6px;
  border-radius: var(--border-radius-small);
}

.usage-count {
  font-weight: var(--font-weight-medium);
}

.file-size {
  font-family: var(--font-family-mono, 'Monaco', 'Consolas', monospace);
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

/* 组件预览样式 */
.component-preview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.preview-container {
  min-height: 120px;
  padding: var(--spacing-md);
  background-color: var(--background-color-light);
  border: var(--border-base);
  border-radius: var(--border-radius-base);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.preview-component {
  max-width: 100%;
  max-height: 100%;
}

.preview-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.preview-note {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--info-color-light);
  border-radius: var(--border-radius-small);
}

/* 特定组件预览样式 */
.form-preview {
  width: 100%;
  max-width: 300px;
}

.chart-preview {
  width: 100%;
  max-width: 280px;
}

.mock-chart {
  height: 80px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.chart-bars {
  display: flex;
  align-items: end;
  gap: var(--spacing-xs);
  height: 60px;
  padding: 0 var(--spacing-sm);
}

.bar {
  flex: 1;
  background: linear-gradient(to top, var(--primary-color), var(--primary-color-light));
  border-radius: 2px 2px 0 0;
  min-height: 10px;
  transition: all var(--transition-fast);
}

.bar:hover {
  opacity: 0.8;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--text-color-secondary);
}

.status-preview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  width: 100%;
  max-width: 200px;
}

.status-item {
  display: flex;
  align-items: center;
}

.device-preview {
  width: 100%;
  max-width: 250px;
}

.device-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.loading-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
}

/* 特殊状态组件预览样式 */
.deprecated-preview,
.error-preview,
.fallback-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  min-height: 80px;
}

.deprecated-content,
.error-content,
.fallback-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  text-align: center;
}

.deprecated-content span,
.error-content span {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.deprecated-content span {
  color: var(--warning-color);
}

.error-content span {
  color: var(--error-color);
}

.fallback-content span {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-color-primary);
}

.fallback-content small {
  font-size: var(--font-size-xs);
  color: var(--text-color-secondary);
}

/* 健康检查报告样式 */
.health-check-report {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.mb-4 {
  margin-bottom: var(--spacing-md);
}

.category-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background-color: var(--background-color-light);
  border-radius: var(--border-radius-small);
}

.category-name {
  font-size: var(--font-size-sm);
  color: var(--text-color-primary);
}

.category-count {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--primary-color);
}

.usage-analysis {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.usage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  border-left: 3px solid var(--primary-color);
  background-color: var(--background-color-light);
}

.usage-label {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.usage-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-color-primary);
}

.attention-components {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.attention-section h4 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text-color-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.component-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

/* 通用样式 */
.mr-1 {
  margin-right: var(--spacing-xs);
}

.mr-2 {
  margin-right: var(--spacing-sm);
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}
</style>
