<script setup lang="ts">
import { h, onMounted, ref, resolveDirective, withDirectives, watch, computed, type Ref } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NTag,
  NPopconfirm,
  NSpace,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NPagination,
  NTooltip,
  NColorPicker,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'

import { formatDate, formatDateTime, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'

defineOptions({ name: '工作流管理' })

const router = useRouter()
const message = useMessage()

function sanitizeHex(hex?: string): string {
  const v = (hex || '').trim()
  if (!v) return ''
  const m = v.match(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/)
  return m ? v : ''
}

const $table = ref<any>(null)
const queryItems = ref<{
  name?: string
  type?: string
  is_active?: string
}>({})
const vPermission = resolveDirective('permission')
const viewMode = ref('card') // 视图模式：'card' 或 'table'
const workflowList = ref<any[]>([]) // 卡片视图的工作流列表
const cardPagination = ref({
  page: 1,
  pageSize: 12,
  total: 0,
})

// 模板相关状态
const templateModalVisible = ref(false)
const templateLoading = ref(false)
const templateList = ref<any[]>([])
const selectedTemplate = ref<any>(null)
const newWorkflowName = ref('')

// 视图切换选项
const viewOptions = [
  {
    value: 'card',
    label: '卡片视图',
    icon: 'material-symbols:grid-view',
  },
  {
    value: 'table',
    label: '表格视图',
    icon: 'material-symbols:table-rows',
  },
]

// 工作流状态选项
const statusOptions = [
  { label: '启用', value: 'true' },
  { label: '禁用', value: 'false' },
]

// 工作流类型选项
const typeOptions = [
  { label: '设备监控流程', value: 'device_monitor' },
  { label: '报警处理流程', value: 'alarm_process' },
  { label: '数据采集流程', value: 'data_collection' },
  { label: '维护保养流程', value: 'maintenance' },
  { label: '自定义流程', value: 'custom' },
]

// 优先级选项
const priorityOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
  { label: '紧急', value: 'urgent' },
]

// 导入工作流API
import {
  getWorkflowList,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  toggleWorkflow,
  publishWorkflow,
  executeWorkflow,
  getWorkflowTemplates,
  useWorkflowTemplate,
} from '@/api/workflow'

// 工作流表单类型
interface WorkflowForm {
  id?: number
  name: string
  description: string
  type: string
  priority: string
  is_active: boolean
  trigger_type: string
  config: string
  trigger_config: Record<string, any>
  accent_color?: string
}

const crudResult = useCRUD({
  name: '工作流',
  initForm: {
    name: '',
    description: '',
    type: 'custom',
    priority: 'medium',
    is_active: true,
    trigger_type: 'manual',
    trigger_config: {},
    config: '',
    accent_color: '',
  },
  doCreate: async (data) => {
    const res = await createWorkflow(data)
    return res
  },
  doUpdate: async (data) => {
    const res = await updateWorkflow(data.id, data)
    return res
  },
  doDelete: async (data) => {
    const res = await deleteWorkflow(data.id)
    return res
  },
  refresh: () => {
    if (viewMode.value === 'table') {
      $table.value?.handleSearch()
    } else {
      loadWorkflowCards()
    }
  },
})

// 解构并添加类型
const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = crudResult
// modalForm 是一个 Ref，我们需要正确地使用它
const modalForm = crudResult.modalForm as Ref<WorkflowForm>

onMounted(() => {
  console.log('工作流管理页面已挂载')
  // 初始加载卡片数据
  if (viewMode.value === 'card') {
    loadWorkflowCards()
  }
})

watch(() => modalVisible.value, (visible) => {
  if (visible) {
    if (!modalForm.value.trigger_config || typeof modalForm.value.trigger_config !== 'object') {
      modalForm.value.trigger_config = {}
    }
    modalForm.value.trigger_type = (modalForm.value.trigger_type || 'manual').toString().trim().toLowerCase()
    modalForm.value.accent_color = sanitizeHex(modalForm.value.accent_color)
  }
})

watch(() => modalForm.value.trigger_type, (t) => {
  const tt = (t || '').toLowerCase()
  if (!modalForm.value.trigger_config || typeof modalForm.value.trigger_config !== 'object') {
    modalForm.value.trigger_config = {}
  }
  if (tt === 'webhook') {
    if (modalForm.value.trigger_config.webhook_path === undefined) modalForm.value.trigger_config.webhook_path = ''
    if (modalForm.value.trigger_config.webhook_secret === undefined) modalForm.value.trigger_config.webhook_secret = ''
  } else if (tt === 'schedule') {
    if (!modalForm.value.trigger_config.schedule_type) modalForm.value.trigger_config.schedule_type = 'cron'
  } else if (tt === 'event') {
    if (modalForm.value.trigger_config.event_type === undefined) modalForm.value.trigger_config.event_type = ''
    if (modalForm.value.trigger_config.event_source === undefined) modalForm.value.trigger_config.event_source = ''
    if (modalForm.value.trigger_config.event_filter === undefined) modalForm.value.trigger_config.event_filter = ''
  }
})

// 监听视图模式变化
watch(viewMode, (newMode) => {
  if (newMode === 'card') {
    loadWorkflowCards()
  }
})

// 归一化触发类型（用于模板条件展示）
const triggerTypeNormalized = computed(() => (modalForm.value.trigger_type || '').toString().trim().toLowerCase())

// 表格列配置
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '工作流名称',
    key: 'name',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        {
          style: {
            color: row.is_active ? 'var(--n-primary-color)' : 'var(--n-text-color-disabled)',
            fontWeight: '500',
            cursor: 'pointer',
            textDecoration: 'underline',
          },
          onClick: () => handleView(row),
        },
        row.name
      )
    },
  },
  {
    title: '描述',
    key: 'description',
    width: 200,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        {
          style: {
            color: row.is_active ? 'var(--n-text-color-2)' : 'var(--n-text-color-disabled)',
          },
        },
        row.description || '暂无描述'
      )
    },
  },
  {
    title: '类型',
    key: 'type',
    width: 120,
    align: 'center',
    render(row) {
      const typeMap = {
        device_monitor: { label: '设备监控', color: 'info' },
        alarm_process: { label: '报警处理', color: 'warning' },
        data_collection: { label: '数据采集', color: 'success' },
        maintenance: { label: '维护保养', color: 'default' },
        custom: { label: '自定义', color: 'primary' },
      }
      const config = typeMap[row.type] || { label: row.type, color: 'default' }
      return h(NTag, { type: config.color, size: 'small' }, { default: () => config.label })
    },
  },
  {
    title: '优先级',
    key: 'priority',
    width: 80,
    align: 'center',
    render(row) {
      const priorityMap = {
        low: { label: '低', color: 'default' },
        medium: { label: '中', color: 'info' },
        high: { label: '高', color: 'warning' },
        urgent: { label: '紧急', color: 'error' },
      }
      const config = priorityMap[row.priority] || { label: row.priority, color: 'default' }
      return h(NTag, { type: config.color, size: 'small' }, { default: () => config.label })
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        value: row.is_active,
        checkedValue: true,
        uncheckedValue: false,
        onUpdateValue: () => handleUpdateStatus(row),
      })
    },
  },
  {
    title: '发布',
    key: 'is_published',
    width: 80,
    align: 'center',
    render(row) {
      return h(NTag, { 
        type: row.is_published ? 'success' : 'default', 
        size: 'small' 
      }, { 
        default: () => row.is_published ? '已发布' : '未发布' 
      })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        { style: { fontSize: '12px', color: 'var(--n-text-color-3)' } },
        formatDate(row.created_at)
      )
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 150,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        'span',
        { style: { fontSize: '12px', color: 'var(--n-text-color-3)' } },
        formatDate(row.updated_at)
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    align: 'center',
    fixed: 'right',
    render(row) {
      return h(NSpace, { size: 4 }, () => [
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            onClick: () => handleDesign(row),
          },
          {
            default: () => '设计',
            icon: renderIcon('material-symbols:design-services', { size: 14 }),
          }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleEdit(row),
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit', { size: 14 }),
          }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                },
                {
                  default: () => '删除',
                  icon: renderIcon('material-symbols:delete-outline', { size: 14 }),
                }
              ),
            default: () => h('div', {}, '确定删除该工作流吗？'),
          }
        ),
      ])
    },
  },
]

// 修改工作流状态
async function handleUpdateStatus(row: any) {
  try {
    const res: any = await toggleWorkflow(row.id)
    if (res.code === 200) {
      row.is_active = res.data?.is_active ?? !row.is_active
      message.success(row.is_active ? '已启用该工作流' : '已禁用该工作流')
      if (viewMode.value === 'table') {
        $table.value?.handleSearch()
      } else {
        loadWorkflowCards()
      }
    } else {
      message.error(res.message || '状态更新失败')
    }
  } catch (err) {
    console.error('更新工作流状态失败:', err)
    message.error('状态更新失败')
  }
}

// 查看工作流详情 - 跳转到设计页面
function handleView(row) {
  console.log('查看工作流详情:', row)
  // 跳转到工作流设计页面
  router.push({
    path: '/flow-settings/workflow-design',
    query: { id: row.id }
  })
}

// 设计工作流 - 跳转到设计页面
function handleDesign(row: any) {
  console.log('设计工作流:', row)
  router.push({
    path: '/flow-settings/workflow-design',
    query: { id: row.id }
  })
}

// 发布工作流
async function handlePublish(row: any) {
  try {
    const res: any = await publishWorkflow(row.id)
    if (res.code === 200) {
      message.success('工作流发布成功')
      if (viewMode.value === 'table') {
        $table.value?.handleSearch()
      } else {
        loadWorkflowCards()
      }
    } else {
      message.error(res.message || '发布失败')
    }
  } catch (err) {
    console.error('发布工作流失败:', err)
    message.error('发布失败')
  }
}

// 执行工作流
async function handleExecute(row: any) {
  try {
    const res: any = await executeWorkflow(row.id, { async_mode: true })
    if (res.code === 200) {
      message.success('工作流已开始执行')
    } else {
      message.error(res.message || '执行失败')
    }
  } catch (err) {
    console.error('执行工作流失败:', err)
    message.error('执行失败')
  }
}

// 重置查询条件
function handleReset() {
  queryItems.value = {}
  if (viewMode.value === 'table') {
    $table.value?.handleSearch()
  } else {
    loadWorkflowCards()
  }
}

// =====================================================
// 模板相关方法
// =====================================================

// 显示模板选择弹窗
async function showTemplateModal() {
  templateModalVisible.value = true
  selectedTemplate.value = null
  newWorkflowName.value = ''
  await loadTemplates()
}

// 加载模板列表
async function loadTemplates() {
  templateLoading.value = true
  try {
    const res: any = await getWorkflowTemplates()
    if (res.code === 200) {
      templateList.value = res.data || []
    } else {
      message.error(res.message || '加载模板失败')
    }
  } catch (err) {
    console.error('加载模板失败:', err)
    message.error('加载模板失败')
  } finally {
    templateLoading.value = false
  }
}

// 选择模板
function selectTemplate(template: any) {
  selectedTemplate.value = template
  if (!newWorkflowName.value) {
    newWorkflowName.value = `${template.name} - 副本`
  }
}

// 从模板创建工作流
async function handleCreateFromTemplate() {
  if (!selectedTemplate.value) {
    message.warning('请选择一个模板')
    return
  }
  if (!newWorkflowName.value.trim()) {
    message.warning('请输入工作流名称')
    return
  }

  templateLoading.value = true
  try {
    const res: any = await useWorkflowTemplate(selectedTemplate.value.id, newWorkflowName.value)
    if (res.code === 200) {
      message.success('工作流创建成功')
      templateModalVisible.value = false
      
      // 刷新列表
      if (viewMode.value === 'table') {
        $table.value?.handleSearch()
      } else {
        loadWorkflowCards()
      }
      
      // 跳转到设计页面
      if (res.data?.id) {
        router.push({
          path: '/flow-settings/workflow-design',
          query: { id: res.data.id }
        })
      }
    } else {
      message.error(res.message || '创建失败')
    }
  } catch (err) {
    console.error('从模板创建工作流失败:', err)
    message.error('创建失败')
  } finally {
    templateLoading.value = false
  }
}

// 获取模板图标
function getTemplateIcon(type: string) {
  const iconMap: Record<string, string> = {
    device_monitor: 'material-symbols:monitor-heart',
    alarm_process: 'material-symbols:warning',
    data_collection: 'material-symbols:database',
    maintenance: 'material-symbols:build',
    custom: 'material-symbols:account-tree',
  }
  return iconMap[type] || 'material-symbols:account-tree'
}

// 获取类型标签颜色
function getTypeColor(type) {
  const typeMap = {
    device_monitor: 'info',
    alarm_process: 'warning',
    data_collection: 'success',
    maintenance: 'default',
    custom: 'primary',
  }
  return typeMap[type] || 'default'
}

// 颜色工具：将HEX颜色适度变亮
function lightenColor(hex, amount = 30) {
  try {
    const h = hex.replace('#', '')
    const bigint = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16)
    let r = (bigint >> 16) & 255
    let g = (bigint >> 8) & 255
    let b = bigint & 255
    r = Math.min(255, r + amount)
    g = Math.min(255, g + amount)
    b = Math.min(255, b + amount)
    const toHex = (n) => n.toString(16).padStart(2, '0')
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`
  } catch (e) {
    return hex
  }
}

// 获取强调色（优先使用后端 accent_color）
function getAccentColor(workflow) {
  return workflow.accent_color || ''
}

// 获取类型标签文本
function getTypeLabel(type) {
  const typeMap = {
    device_monitor: '设备监控',
    alarm_process: '报警处理',
    data_collection: '数据采集',
    maintenance: '维护保养',
    custom: '自定义',
  }
  return typeMap[type] || type
}

// 获取优先级标签颜色
function getPriorityColor(priority) {
  const priorityMap = {
    low: 'default',
    medium: 'info',
    high: 'warning',
    urgent: 'error',
  }
  return priorityMap[priority] || 'default'
}

// 获取优先级标签文本
function getPriorityLabel(priority) {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急',
  }
  return priorityMap[priority] || priority
}

// 加载卡片视图数据
async function loadWorkflowCards() {
  try {
    const params = {
      page: cardPagination.value.page,
      page_size: cardPagination.value.pageSize,
      ...queryItems.value,
    }
    const result = await getWorkflowListData(params)
    workflowList.value = result.data
    cardPagination.value.total = result.total
  } catch (error) {
    console.error('加载工作流卡片失败:', error)
    workflowList.value = []
  }
}

// 卡片视图分页变化
function handleCardPageChange(page) {
  cardPagination.value.page = page
  loadWorkflowCards()
}

// 卡片视图页面大小变化
function handleCardPageSizeChange(pageSize) {
  cardPagination.value.pageSize = pageSize
  cardPagination.value.page = 1
  loadWorkflowCards()
}

// 获取工作流列表数据
const getWorkflowListData = async (params: any) => {
  try {
    console.log('获取工作流列表，参数:', params)

    // 调用真实API
    const res: any = await getWorkflowList({
      page: params.page || 1,
      page_size: params.page_size || 10,
      search: params.name,
      type: params.type,
      is_active: params.is_active === 'true' ? true : params.is_active === 'false' ? false : undefined,
    })

    if (res.code === 200 && res.data) {
      return {
        data: res.data.items || res.data.data || [],
        total: res.data.total || 0,
      }
    }

    return {
      data: [],
      total: 0,
    }
  } catch (err) {
    console.error('获取工作流列表失败:', err)
    return { data: [], total: 0 }
  }
}

// 表单验证规则
const validateWorkflow = {
  name: [
    {
      required: true,
      message: '请输入工作流名称',
      trigger: ['input', 'blur'],
    },
  ],
  type: [
    {
      required: true,
      message: '请选择工作流类型',
      trigger: ['change', 'blur'],
    },
  ],
  priority: [
    {
      required: true,
      message: '请选择优先级',
      trigger: ['change', 'blur'],
    },
  ],
  accent_color: [
    {
      validator: (rule, value) => {
        if (!value) return true
        return /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value)
      },
      message: '请输入合法的HEX颜色，如 #667eea',
      trigger: ['input', 'blur'],
    },
  ],
  trigger_type: [
    {
      required: true,
      message: '请选择触发类型',
      trigger: ['change', 'blur'],
    },
  ],
  'trigger_config.webhook_path': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'webhook' && !value) {
          return new Error('请输入Webhook路径')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  'trigger_config.webhook_secret': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'webhook' && !value) {
          return new Error('请输入密钥')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  'trigger_config.cron_expression': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'schedule' && modalForm.value.trigger_config?.schedule_type === 'cron' && !value) {
          return new Error('请输入Cron表达式')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  'trigger_config.interval_seconds': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'schedule' && modalForm.value.trigger_config?.schedule_type === 'interval' && !value) {
          return new Error('请输入间隔秒数')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  'trigger_config.execute_at': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'schedule' && modalForm.value.trigger_config?.schedule_type === 'once' && !value) {
          return new Error('请输入执行时间')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
  'trigger_config.event_type': [
    {
      validator: (rule, value) => {
        if (modalForm.value.trigger_type === 'event' && !value) {
          return new Error('请输入事件类型')
        }
        return true
      },
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer title="工作流管理">
    <template #action>
      <div class="flex items-center gap-3">
        <ViewToggle
          v-model="viewMode"
          :options="viewOptions"
          size="small"
          :show-label="false"
          :icon-size="16"
          align="right"
        />
        <NButton type="default" @click="showTemplateModal">
          <TheIcon icon="material-symbols:content-copy" :size="18" class="mr-5" />从模板创建
        </NButton>
        <NButton type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建工作流
        </NButton>
      </div>
    </template>

    <!-- 查询条件 -->
    <div class="query-bar mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <QueryBarItem label="名称" :label-width="50">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入工作流名称"
            style="width: 200px"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="50">
          <NSelect
            v-model:value="queryItems.type"
            :options="typeOptions"
            clearable
            placeholder="请选择类型"
            style="width: 180px"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryItems.is_active"
            :options="statusOptions"
            clearable
            placeholder="请选择状态"
            style="width: 120px"
          />
        </QueryBarItem>
        <NButton type="primary" @click="$table?.handleSearch()">
          <TheIcon icon="material-symbols:search" :size="16" class="mr-1" />搜索
        </NButton>
        <NButton @click="handleReset">
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-1" />重置
        </NButton>
      </div>
    </div>

    <!-- 表格视图 -->
    <CrudTable
      v-if="viewMode === 'table'"
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="getWorkflowListData"
    />

    <!-- 卡片视图 -->
    <div v-else class="workflow-cards">
      <div class="workflow-grid">
        <div v-for="workflow in workflowList" :key="workflow.id" class="workflow-card-item">
          <NCard
            :class="['workflow-card', `workflow-type--${workflow.type}`]"
            :style="getAccentColor(workflow) ? { borderLeftColor: getAccentColor(workflow) } : {}"
            hoverable
            @click="handleView(workflow)"
          >
            <!-- 状态指示器 -->
            <div
              class="status-indicator"
              :class="`status-indicator--${workflow.is_active ? 'active' : 'inactive'}`"
            ></div>

            <div class="workflow-card-header">
              <div
                class="workflow-icon-wrapper"
                :style="getAccentColor(workflow)
                  ? { background: `linear-gradient(135deg, ${getAccentColor(workflow)} 0%, ${lightenColor(getAccentColor(workflow), 60)} 100%)` }
                  : {}"
              >
                <TheIcon icon="material-symbols:account-tree" :size="24" class="workflow-icon" />
              </div>
              <div class="workflow-info">
                <h3 class="workflow-title">{{ workflow.name }}</h3>
                <p class="workflow-description">{{ workflow.description || '暂无描述' }}</p>
              </div>
            </div>

            <!-- 工作流标签和状态 -->
            <div class="workflow-tags">
              <NTag :type="getTypeColor(workflow.type)" size="small" :bordered="false">
                {{ getTypeLabel(workflow.type) }}
              </NTag>
              <NTag :type="getPriorityColor(workflow.priority)" size="small" :bordered="false">
                {{ getPriorityLabel(workflow.priority) }}
              </NTag>
              <NTag 
                :type="workflow.is_published ? 'success' : 'default'" 
                size="small" 
                :bordered="false"
              >
                {{ workflow.is_published ? '已发布' : '未发布' }}
              </NTag>
            </div>

            <!-- 工作流统计信息 -->
            <div class="workflow-stats">
              <div class="stat-item">
                <TheIcon icon="material-symbols:play-circle" :size="16" class="stat-icon" />
                <span class="stat-value">{{ workflow.execution_count ?? 0 }}</span>
                <span class="stat-label">执行</span>
              </div>
              <div class="stat-item">
                <TheIcon icon="material-symbols:check-circle" :size="16" class="stat-icon success" />
                <span class="stat-value">{{ workflow.success_count ?? 0 }}</span>
                <span class="stat-label">成功</span>
              </div>
              <div class="stat-item">
                <TheIcon icon="material-symbols:cancel" :size="16" class="stat-icon failure" />
                <span class="stat-value">{{ workflow.failure_count ?? 0 }}</span>
                <span class="stat-label">失败</span>
              </div>
              <div class="stats-spacer"></div>
              <div class="stats-last-run">
                <TheIcon icon="material-symbols:schedule" :size="16" class="mr-2" />
                <span class="last-run-label">最近执行：</span>
                <template v-if="workflow.last_executed_at">
                  <NTooltip trigger="hover">
                    <template #trigger>
                      <span class="last-run-text">{{ formatDateTime(workflow.last_executed_at, 'YYYY-MM-DD HH:mm') }}</span>
                    </template>
                    {{ formatDateTime(workflow.last_executed_at, 'YYYY-MM-DD HH:mm:ss') }}
                  </NTooltip>
                </template>
                <span v-else class="last-run-text">—</span>
              </div>
            </div>

            <!-- 工作流操作按钮 -->
            <div class="workflow-actions">
              <NSpace :size="8">
                <NButton size="small" type="info" ghost @click.stop="handleDesign(workflow)">
                  <TheIcon icon="material-symbols:design-services" :size="14" class="mr-1" />
                  设计
                </NButton>
                <NButton size="small" type="primary" ghost @click.stop="handleEdit(workflow)">
                  <TheIcon icon="material-symbols:edit" :size="14" class="mr-1" />
                  编辑
                </NButton>
                <NButton 
                  v-if="workflow.is_active && !workflow.is_published" 
                  size="small" 
                  type="success" 
                  ghost 
                  @click.stop="handlePublish(workflow)"
                >
                  <TheIcon icon="material-symbols:publish" :size="14" class="mr-1" />
                  发布
                </NButton>
                <NButton 
                  v-if="workflow.is_active && workflow.is_published" 
                  size="small" 
                  type="warning" 
                  ghost 
                  @click.stop="handleExecute(workflow)"
                >
                  <TheIcon icon="material-symbols:play-arrow" :size="14" class="mr-1" />
                  执行
                </NButton>
              </NSpace>
              <NSwitch
                :value="workflow.is_active"
                size="small"
                @update:value="() => handleUpdateStatus(workflow)"
                @click.stop
              />
            </div>
          </NCard>
        </div>
      </div>

      <!-- 卡片视图分页 -->
      <div class="workflow-pagination">
        <NPagination
          v-model:page="cardPagination.page"
          :page-size="cardPagination.pageSize"
          :item-count="cardPagination.total"
          :show-size-picker="true"
          :page-sizes="[12, 24, 48]"
          @update:page="handleCardPageChange"
          @update:page-size="handleCardPageSizeChange"
        />
      </div>
    </div>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="600px"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="100"
        :model="modalForm"
        :rules="validateWorkflow"
      >
        <NFormItem label="工作流名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入工作流名称" />
        </NFormItem>
        <NFormItem label="描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            clearable
            placeholder="请输入工作流描述"
            :rows="3"
          />
        </NFormItem>
        <NFormItem label="类型" path="type">
          <NSelect
            v-model:value="modalForm.type"
            :options="typeOptions"
            placeholder="请选择工作流类型"
          />
        </NFormItem>
        <NFormItem label="优先级" path="priority">
          <NSelect
            v-model:value="modalForm.priority"
            :options="priorityOptions"
            placeholder="请选择优先级"
          />
        </NFormItem>
        <NFormItem label="状态" path="is_active">
          <NSwitch
            v-model:value="modalForm.is_active"
            :checked-value="true"
            :unchecked-value="false"
          >
            <template #checked>启用</template>
            <template #unchecked>禁用</template>
          </NSwitch>
        </NFormItem>
        <NFormItem label="触发类型" path="trigger_type">
          <NSelect
            v-model:value="modalForm.trigger_type"
            :options="[
              { label: '手动', value: 'manual' },
              { label: '定时', value: 'schedule' },
              { label: '事件', value: 'event' },
              { label: 'Webhook', value: 'webhook' },
            ]"
            placeholder="请选择触发类型"
            style="width: 180px"
          />
        </NFormItem>
        <div v-if="triggerTypeNormalized === 'schedule'" :key="'schedule-'+triggerTypeNormalized" class="flex flex-col gap-3">
          <NFormItem label="调度方式">
          <NSelect
              v-model:value="modalForm.trigger_config.schedule_type"
              :options="[
                { label: 'Cron', value: 'cron' },
                { label: '间隔', value: 'interval' },
                { label: '单次', value: 'once' },
                { label: '每日', value: 'daily' },
                { label: '每周', value: 'weekly' },
                { label: '每月', value: 'monthly' },
              ]"
              placeholder="选择调度方式"
              style="width: 180px"
            />
          </NFormItem>
          <div v-if="modalForm.trigger_config?.schedule_type === 'cron'" class="flex items-center gap-3">
            <NFormItem label="Cron表达式" path="trigger_config.cron_expression">
              <NInput v-model:value="modalForm.trigger_config.cron_expression" placeholder="*/5 * * * *" style="max-width: 220px" />
            </NFormItem>
          </div>
          <div v-if="modalForm.trigger_config?.schedule_type === 'interval'" class="flex items-center gap-3">
            <NFormItem label="间隔秒数" path="trigger_config.interval_seconds">
              <NInput v-model:value="modalForm.trigger_config.interval_seconds" placeholder="300" style="max-width: 160px" />
            </NFormItem>
          </div>
          <div v-if="modalForm.trigger_config?.schedule_type === 'once'" class="flex items-center gap-3">
            <NFormItem label="执行时间(ISO)" path="trigger_config.execute_at">
              <NInput v-model:value="modalForm.trigger_config.execute_at" placeholder="2025-01-01T08:00:00" style="max-width: 240px" />
            </NFormItem>
          </div>
          <div v-if="modalForm.trigger_config?.schedule_type === 'daily'" class="flex items-center gap-3">
            <NFormItem label="小时">
              <NInput v-model:value="modalForm.trigger_config.hour" placeholder="8" style="max-width: 100px" />
            </NFormItem>
            <NFormItem label="分钟">
              <NInput v-model:value="modalForm.trigger_config.minute" placeholder="0" style="max-width: 100px" />
            </NFormItem>
          </div>
          <div v-if="modalForm.trigger_config?.schedule_type === 'weekly'" class="flex items-center gap-3">
            <NFormItem label="周几">
              <NSelect v-model:value="modalForm.trigger_config.day_of_week" :options="[
                { label: '周一', value: 'mon' },
                { label: '周二', value: 'tue' },
                { label: '周三', value: 'wed' },
                { label: '周四', value: 'thu' },
                { label: '周五', value: 'fri' },
                { label: '周六', value: 'sat' },
                { label: '周日', value: 'sun' },
              ]" style="max-width: 140px" />
            </NFormItem>
            <NFormItem label="小时">
              <NInput v-model:value="modalForm.trigger_config.hour" placeholder="8" style="max-width: 100px" />
            </NFormItem>
            <NFormItem label="分钟">
              <NInput v-model:value="modalForm.trigger_config.minute" placeholder="0" style="max-width: 100px" />
            </NFormItem>
          </div>
          <div v-if="modalForm.trigger_config?.schedule_type === 'monthly'" class="flex items-center gap-3">
            <NFormItem label="日">
              <NInput v-model:value="modalForm.trigger_config.day" placeholder="1" style="max-width: 100px" />
            </NFormItem>
            <NFormItem label="小时">
              <NInput v-model:value="modalForm.trigger_config.hour" placeholder="8" style="max-width: 100px" />
            </NFormItem>
            <NFormItem label="分钟">
              <NInput v-model:value="modalForm.trigger_config.minute" placeholder="0" style="max-width: 100px" />
            </NFormItem>
          </div>
        </div>
        <div v-if="triggerTypeNormalized === 'event'" :key="'event-'+triggerTypeNormalized" class="flex flex-col gap-3">
          <NFormItem label="事件类型" path="trigger_config.event_type">
            <NInput v-model:value="modalForm.trigger_config.event_type" placeholder="alarm.raised" style="max-width: 220px" />
          </NFormItem>
          <NFormItem label="事件来源">
            <NInput v-model:value="modalForm.trigger_config.event_source" placeholder="device-service" style="max-width: 220px" />
          </NFormItem>
          <NFormItem label="事件过滤(JSON)">
            <NInput v-model:value="modalForm.trigger_config.event_filter" type="textarea" placeholder='{"level":"high"}' :rows="3" />
          </NFormItem>
        </div>
        <div v-if="triggerTypeNormalized === 'webhook'" :key="'webhook-'+triggerTypeNormalized" class="flex flex-col gap-3">
          <NFormItem label="Webhook路径" path="trigger_config.webhook_path">
            <NInput v-model:value="modalForm.trigger_config.webhook_path" placeholder="/hooks/workflows/exec" style="max-width: 240px" />
          </NFormItem>
          <NFormItem label="密钥" path="trigger_config.webhook_secret">
            <NInput v-model:value="modalForm.trigger_config.webhook_secret" placeholder="secret-token" style="max-width: 240px" />
          </NFormItem>
        </div>
        <NFormItem label="卡片颜色" path="accent_color">
          <div class="flex items-center gap-3">
            <NColorPicker v-model:value="modalForm.accent_color" size="small" :modes="['hex']" />
            <NInput v-model:value="modalForm.accent_color" placeholder="#667eea" style="max-width: 140px" />
          </div>
        </NFormItem>
        <NFormItem label="配置" path="config">
          <NInput
            v-model:value="modalForm.config"
            type="textarea"
            clearable
            placeholder="请输入JSON格式的配置信息"
            :rows="6"
          />
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 模板选择弹窗 -->
    <CrudModal
      v-model:visible="templateModalVisible"
      title="从模板创建工作流"
      :loading="templateLoading"
      width="800px"
      @save="handleCreateFromTemplate"
    >
      <div class="template-modal-content">
        <!-- 工作流名称输入 -->
        <NFormItem label="工作流名称" :label-width="100" required>
          <NInput
            v-model:value="newWorkflowName"
            placeholder="请输入新工作流名称"
            clearable
          />
        </NFormItem>

        <!-- 模板列表 -->
        <div class="template-list">
          <div class="template-list-header">
            <span>选择模板</span>
            <NTag v-if="selectedTemplate" type="success" size="small">
              已选择: {{ selectedTemplate.name }}
            </NTag>
          </div>
          
          <div v-if="templateList.length === 0" class="template-empty">
            <TheIcon icon="material-symbols:inbox" :size="48" class="empty-icon" />
            <p>暂无可用模板</p>
            <p class="empty-hint">请先执行数据库迁移导入模板数据</p>
          </div>
          
          <div v-else class="template-grid">
            <div
              v-for="template in templateList"
              :key="template.id"
              class="template-card"
              :class="{ selected: selectedTemplate?.id === template.id }"
              @click="selectTemplate(template)"
            >
              <div class="template-card-header">
                <TheIcon :icon="getTemplateIcon(template.type)" :size="24" />
                <span class="template-name">{{ template.name }}</span>
              </div>
              <p class="template-description">{{ template.description }}</p>
              <div class="template-meta">
                <NTag :type="getTypeColor(template.type)" size="small">
                  {{ getTypeLabel(template.type) }}
                </NTag>
                <span class="template-usage">使用 {{ template.usage_count || 0 }} 次</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
/* 查询条件样式 */
.query-bar {
  background: var(--n-card-color);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--n-border-color);
}

/* 卡片网格布局 */
.workflow-cards {
  margin-top: 16px;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.workflow-card-item {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.workflow-card-item:hover {
  transform: translateY(-2px);
}

/* 工作流卡片样式 - 现代化设计 */
.workflow-card {
  position: relative;
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
  background: var(--n-card-color);
  transition: all 0.3s ease;
  overflow: hidden;
  border-left: 4px solid #e0e0e0;
}

.workflow-card:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  z-index: 10;
}

.status-indicator--active {
  background-color: #18a058;
  animation: pulse-green 2s infinite;
}

.status-indicator--inactive {
  background-color: #909399;
  animation: none;
}

/* 绿色闪烁动画 */
@keyframes pulse-green {
  0% {
    box-shadow: 0 0 0 0 rgba(24, 160, 88, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(24, 160, 88, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(24, 160, 88, 0);
  }
}

/* 卡片头部 */
.workflow-card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.workflow-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  flex-shrink: 0;
}

.workflow-icon {
  color: white;
}

.workflow-info {
  flex: 1;
  min-width: 0;
}

.workflow-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color-1);
  margin: 0 0 6px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-description {
  font-size: 13px;
  color: var(--n-text-color-2);
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 工作流标签 */
.workflow-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

/* 工作流操作 */
.workflow-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--n-divider-color);
}

/* 工作流统计信息 */
.workflow-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.workflow-stats .stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--n-text-color-2);
}

.workflow-stats .stat-item .stat-value {
  font-weight: 600;
  color: var(--n-text-color-1);
}

.workflow-stats .stat-item .stat-icon {
  color: var(--n-text-color-3);
}

.workflow-stats .stat-item .stat-icon.success {
  color: #18a058;
}

.workflow-stats .stat-item .stat-icon.failure {
  color: #d03050;
}

.workflow-stats .stats-spacer {
  flex: 1;
}

.workflow-stats .stats-last-run {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--n-text-color-3);
}

.workflow-stats .stats-last-run .last-run-label {
  color: var(--n-text-color-3);
}

.workflow-stats .stats-last-run .last-run-text {
  display: inline-block;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .workflow-stats .stats-last-run .last-run-text {
    max-width: 120px;
  }
}

/* 类型配色：左边框与图标块联动 */
.workflow-type--device_monitor {
  border-left-color: #2f54eb;
}
.workflow-type--device_monitor .workflow-icon-wrapper {
  background: linear-gradient(135deg, #2f54eb 0%, #597ef7 100%);
}

.workflow-type--alarm_process {
  border-left-color: #722ed1;
}
.workflow-type--alarm_process .workflow-icon-wrapper {
  background: linear-gradient(135deg, #722ed1 0%, #9254de 100%);
}

.workflow-type--data_collection {
  border-left-color: #13c2c2;
}
.workflow-type--data_collection .workflow-icon-wrapper {
  background: linear-gradient(135deg, #13c2c2 0%, #36cfc9 100%);
}

.workflow-type--maintenance {
  border-left-color: #faad14;
}
.workflow-type--maintenance .workflow-icon-wrapper {
  background: linear-gradient(135deg, #faad14 0%, #ffd666 100%);
}

.workflow-type--custom {
  border-left-color: #1890ff;
}
.workflow-type--custom .workflow-icon-wrapper {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
}

/* 分页样式 */
.workflow-pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding: 24px 0;
  border-top: 1px solid var(--n-divider-color);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .workflow-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .workflow-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .workflow-card-header {
    gap: 10px;
  }

  .workflow-icon-wrapper {
    width: 36px;
    height: 36px;
  }

  .workflow-title {
    font-size: 15px;
  }

  .workflow-description {
    font-size: 12px;
  }

  .workflow-actions {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }

  .workflow-pagination {
    margin-top: 24px;
    padding: 16px 0;
  }

  .query-bar .flex {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .query-bar .flex > * {
    width: 100%;
  }
}

/* 暗色主题适配 */
.dark .workflow-card {
  background: var(--n-card-color);
  border-color: var(--n-border-color);
}

.dark .workflow-card:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
}

/* 加载状态 */
.workflow-cards.loading {
  opacity: 0.6;
  pointer-events: none;
}

/* 空状态 */
.workflow-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--n-text-color-3);
}

.workflow-empty .empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.workflow-empty .empty-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.workflow-empty .empty-description {
  font-size: 14px;
  opacity: 0.7;
}

/* 模板弹窗样式 */
.template-modal-content {
  padding: 8px 0;
}

.template-list {
  margin-top: 16px;
}

.template-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: var(--n-text-color-1);
}

.template-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--n-text-color-3);
}

.template-empty .empty-icon {
  color: var(--n-text-color-disabled);
  margin-bottom: 12px;
}

.template-empty .empty-hint {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.7;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.template-card {
  padding: 16px;
  border: 2px solid var(--n-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--n-card-color);
}

.template-card:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-card.selected {
  border-color: var(--n-primary-color);
  background: var(--n-primary-color-hover);
}

.template-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.template-card-header .template-name {
  font-weight: 600;
  color: var(--n-text-color-1);
  font-size: 14px;
}

.template-description {
  font-size: 12px;
  color: var(--n-text-color-2);
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-usage {
  font-size: 11px;
  color: var(--n-text-color-3);
}
</style>
function sanitizeHex(hex: string | undefined): string {
  const v = (hex || '').toString().trim()
  if (!v) return ''
  // allow #RGB or #RRGGBB
  const m = v.match(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/)
  return m ? v : ''
}
