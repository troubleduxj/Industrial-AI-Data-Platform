<script setup lang="ts">
import {
  computed,
  h,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  resolveDirective,
  withDirectives,
  watch,
  type Ref,
} from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPagination,
  NPopconfirm,
  NSelect,
  NTag,
  NInputNumber,
  useMessage,
  type SelectOption,
  type DataTableColumns,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'

import { renderIcon } from '@/utils'
import { useRouter } from 'vue-router'
import deviceV2Api from '@/api/device-v2'

defineOptions({ name: '工艺卡片管理' })

// ==================== 类型定义 ====================

interface QueryItems {
  process_type: string
}

interface ProcessCard {
  process_name: string
  process_code: string
  process_type: string
  version: string
  description: string
  spec_type: string
  spec_status: string
  spec_version: string
  spec_code: string
  spec_description: string
  welding_control: string
  welding_method: string
  point_time: number
  output_control: string
  classification: string
  gas_type: string
  material: string
  wire_diameter: number
  welding_current_upper: number
  welding_voltage_lower: number
  welding_current_upper_limit: number
  welding_voltage_lower_limit: number
  alarm_current_upper: number
  alarm_voltage_lower: number
  alarm_current_upper_limit: number
  alarm_voltage_lower_limit: number
  alarm_mode: string
  start_delay_time: number
  arc_delay_time: number
  [key: string]: any
}

const router = useRouter()
const $table = ref<any>(null)
const queryItems = ref<QueryItems>({
  process_type: '', // 默认显示全部工艺
})
const vPermission = resolveDirective('permission')
const message = useMessage()

// 表单初始化内容
const initForm = {
  process_name: '',
  process_code: '',
  process_type: 'welding',
  version: '1.0',
  description: '',
  // 焊接规范信息
  spec_type: 'GMAW', // 熔化极气体保护焊
  spec_status: 'published', // 发布
  spec_version: '1',
  spec_code: 'HL002',
  spec_description: '',
  // 焊接参数
  welding_control: 'pulse', // 脉冲
  welding_method: 'pulse', // 脉冲
  point_time: 1, // 点焊时间
  output_control: 'voltage', // 输出控制
  classification: 'auto', // 分级
  gas_type: 'CO2', // 气体
  material: 'steel', // 材质
  wire_diameter: 1.2, // 丝径(mm)
  welding_current_upper: 35, // 焊接电流上限
  welding_voltage_lower: 30, // 焊接电压下限
  welding_current_upper_limit: 11, // 焊接电流上限
  welding_voltage_lower_limit: 10, // 焊接电压下限
  // 报警条件
  alarm_current_upper: 500, // 焊接电流上限
  alarm_voltage_lower: 30, // 焊接电压下限
  alarm_current_upper_limit: 48, // 焊接电流上限
  alarm_voltage_lower_limit: 10, // 焊接电压下限
  alarm_mode: 'disabled', // 报警模式
  start_delay_time: 3, // 起弧延时时间
  arc_delay_time: 3, // 报警延时时间
  stop_delay_time: 0, // 停机延时时间
}

// 工艺数据
const tableData = ref([]) // 用于表格视图
const cardData = ref([]) // 用于卡片视图
const loading = ref(false)

// 分页数据
const pagination = ref({
  page: 1,
  pageSize: 20, // 默认每页20个
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [20, 24, 48, 96],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  suffix: ({ startIndex, endIndex }) => `显示 ${startIndex}-${endIndex} 条`,
})

// 显示模式
const viewMode = ref('table') // 'table' 或 'card'

// 计算属性：根据视图模式返回对应的数据
const processes = computed(() => {
  return viewMode.value === 'table' ? tableData.value : cardData.value
})

// 视图切换选项
const viewOptions = [
  {
    value: 'table',
    label: '表格',
    icon: 'material-symbols:table-chart',
  },
  {
    value: 'card',
    label: '卡片',
    icon: 'material-symbols:grid-view',
  },
]

// 模态框状态
const modalVisible = ref(false)
const modalTitle = ref('')
const modalAction = ref('')
const modalLoading = ref(false)
const modalForm = ref({ ...initForm })
const modalFormRef = ref(null)

// 处理添加工艺
const handleAdd = () => {
  modalAction.value = 'add'
  modalTitle.value = '新建工艺'
  modalForm.value = { ...initForm }
  modalVisible.value = true
}

// 处理编辑工艺
const handleEdit = (row) => {
  modalAction.value = 'edit'
  modalTitle.value = '编辑工艺'
  modalForm.value = { ...row }
  modalVisible.value = true
}

// 处理查看工艺详情
const handleViewDetail = (row) => {
  // 跳转到工艺参数详细界面
  router.push({
    name: 'ProcessDetail',
    params: { id: row.id },
    query: { processCode: row.process_code },
  })
}

// 处理删除工艺
const handleDelete = async (ids) => {
  try {
    const idList = Array.isArray(ids) ? ids : [ids]
    if (idList.length > 1) {
      await deviceV2Api.processes.batchDelete(idList)
    } else {
      await deviceV2Api.processes.delete(idList[0])
    }
    window.$message?.success('删除工艺成功')
    getProcesses() // 统一刷新
  } catch (error) {
    console.error('删除工艺失败:', error)
    window.$message?.error(`删除工艺失败: ${error.message || '未知错误'}`)
  }
}

// 卡片样式辅助函数
const getProcessCardClass = (status) => {
  const baseClass = 'process-card'
  switch (status) {
    case 'published':
      return `${baseClass} process-card--published`
    case 'draft':
      return `${baseClass} process-card--draft`
    case 'archived':
      return `${baseClass} process-card--archived`
    default:
      return `${baseClass} process-card--draft`
  }
}

const getStatusClass = (status) => {
  switch (status) {
    case 'published':
      return 'status-indicator--published'
    case 'draft':
      return 'status-indicator--draft'
    case 'archived':
      return 'status-indicator--archived'
    default:
      return 'status-indicator--draft'
  }
}

const getStatusTagType = (status) => {
  switch (status) {
    case 'published':
      return 'success'
    case 'draft':
      return 'warning'
    case 'archived':
      return 'default'
    default:
      return 'warning'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'published':
      return '已发布'
    case 'draft':
      return '草稿'
    case 'archived':
      return '已归档'
    default:
      return '草稿'
  }
}

// 处理保存工艺
const handleSave = async () => {
  try {
    await modalFormRef.value?.validate()
    modalLoading.value = true

    if (modalAction.value === 'add') {
      await deviceV2Api.processes.create(modalForm.value)
      window.$message?.success('新建工艺成功')
    } else {
      await deviceV2Api.processes.update(modalForm.value.id, modalForm.value)
      window.$message?.success('编辑工艺成功')
    }

    modalVisible.value = false
    getProcesses() // 统一刷新
  } catch (error) {
    console.error('保存工艺失败:', error)
    window.$message?.error(`保存工艺失败: ${error.message || '未知错误'}`)
  } finally {
    modalLoading.value = false
  }
}

// 统一获取数据
const getProcesses = async () => {
  loading.value = true
  const params = {
    ...queryItems.value,
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  }
  try {
    const response = await deviceV2Api.processes.list(params)
    console.log('工艺列表API v2响应数据:', response)

    if (response && response.data) {
      const dataItems = Array.isArray(response.data) ? response.data : response.data.items || []

      if (Array.isArray(dataItems)) {
        tableData.value = dataItems
        cardData.value = dataItems
        // 从API响应中正确获取总记录数
        pagination.value.itemCount =
          response.total || response.meta?.total || response.data.total || dataItems.length
        console.log('工艺表格数据:', tableData.value)
        console.log('工艺卡片数据:', cardData.value)
        console.log('工艺分页信息:', {
          page: pagination.value.page,
          pageSize: pagination.value.pageSize,
          itemCount: pagination.value.itemCount,
          totalPages: Math.ceil(pagination.value.itemCount / pagination.value.pageSize),
        })
      } else {
        console.error('工艺API返回数据格式不正确:', dataItems)
        window.$message?.error('获取工艺数据失败: 数据格式不正确')
        tableData.value = []
        cardData.value = []
        pagination.value.itemCount = 0
      }
    } else {
      console.error('工艺API返回数据格式不正确:', response)
      window.$message?.error('获取工艺数据失败: 数据格式不正确')
      tableData.value = []
      cardData.value = []
      pagination.value.itemCount = 0
    }
  } catch (error) {
    console.error('获取工艺列表失败:', error)
    window.$message?.error(`获取工艺列表失败: ${error.message || '未知错误'}`)
    tableData.value = []
    cardData.value = []
    pagination.value.itemCount = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  queryItems.value = { ...params }
  pagination.value.page = 1
  console.log('搜索参数:', queryItems.value)
  getProcesses()
}

const handleReset = () => {
  queryItems.value = {}
  pagination.value.page = 1
  console.log('重置搜索条件')
  getProcesses()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  getProcesses()
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  getProcesses()
}

// 工艺类型代码映射为中文名称
const getProcessTypeName = (typeCode) => {
  const typeMap = {
    welding: '焊接工艺',
    cutting: '切割工艺',
    assembly: '装配工艺',
    inspection: '检测工艺',
    other: '其他工艺',
  }
  return typeMap[typeCode] || typeCode
}

// 工艺类型选项
const processTypeOptions = [
  { label: '全部工艺', value: '' },
  { label: '焊接工艺', value: 'welding' },
  { label: '切割工艺', value: 'cutting' },
  { label: '装配工艺', value: 'assembly' },
  { label: '检测工艺', value: 'inspection' },
  { label: '其他工艺', value: 'other' },
]

// 焊接规范类型选项
const specTypeOptions = [
  { label: '熔化极气体保护焊(GMAW)', value: 'GMAW' },
  { label: '钨极氩弧焊(GTAW)', value: 'GTAW' },
  { label: '手工电弧焊(SMAW)', value: 'SMAW' },
  { label: '埋弧焊(SAW)', value: 'SAW' },
]

// 焊接控制选项
const weldingControlOptions = [
  { label: '收弧', value: 'arc_end' },
  { label: '脉冲', value: 'pulse' },
  { label: '短路', value: 'short_circuit' },
]

// 气体类型选项
const gasTypeOptions = [
  { label: 'CO2', value: 'CO2' },
  { label: '密钢', value: 'steel' },
  { label: '氩气', value: 'argon' },
  { label: '混合气', value: 'mixed' },
]

// 材质选项
const materialOptions = [
  { label: '密钢', value: 'steel' },
  { label: '不锈钢', value: 'stainless_steel' },
  { label: '铝合金', value: 'aluminum' },
  { label: '铜合金', value: 'copper' },
]

onMounted(async () => {
  try {
    await getProcesses()
    console.log('工艺数据加载完成:', processes.value)
  } catch (error) {
    console.error('工艺数据加载失败:', error)
    window.$message?.error('工艺数据加载失败')
  }
})

// 监听视图模式切换
const stopWatchViewMode = watch(viewMode, (newMode) => {
  // 切换视图时保持每页20条不变
  pagination.value.pageSize = 20
  pagination.value.page = 1 // 重置到第一页
  getProcesses() // 重新获取数据
})

// 组件卸载时清理
onUnmounted(() => {
  // 停止watch监听器
  stopWatchViewMode()
  // 清理数据
  tableData.value = []
  cardData.value = []
})

const columns = [
  {
    title: '工艺名称',
    key: 'process_name',
    width: 150,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '工艺编码',
    key: 'process_code',
    width: 120,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '工艺类型',
    key: 'process_type',
    width: 120,
    align: 'center',
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => getProcessTypeName(row.process_type) })
    },
  },
  { title: '版本', key: 'version', width: 80, align: 'center' },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: getStatusTagType(row.status) },
        { default: () => getStatusText(row.status) }
      )
    },
  },
  { title: '描述', key: 'description', width: 200, ellipsis: { tooltip: true }, align: 'center' },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    align: 'center',
    fixed: 'right',
    hideInExcel: true,
    render(row) {
      return [
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            secondary: true,
            onClick: () => handleViewDetail(row),
          },
          {
            default: () => '详情',
            icon: renderIcon('material-symbols:visibility-outline', { size: 14 }),
          }
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              secondary: true,
              style: 'margin-left: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit-outline', { size: 14 }),
            }
          ),
          [[vPermission, 'put/api/v2/process/update']]
        ),
        withDirectives(
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete([row.id], false),
            },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    style: 'margin-left: 8px;',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 14 }),
                  }
                ),
              default: () => h('div', {}, '确定删除该工艺吗?'),
            }
          ),
          [[vPermission, 'delete/api/v2/process/delete']]
        ),
      ]
    },
  },
]

// 表单验证规则
const processRules = {
  process_name: [
    {
      required: true,
      message: '请输入工艺名称',
      trigger: ['input', 'blur'],
    },
  ],
  process_code: [
    {
      required: true,
      message: '请输入工艺编码',
      trigger: ['input', 'blur'],
    },
  ],
  process_type: [
    {
      required: true,
      message: '请选择工艺类型',
      trigger: ['change', 'blur'],
    },
  ],
  version: [
    {
      required: true,
      message: '请输入版本号',
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer>
    <template #action>
      <div class="w-full flex items-center justify-end">
        <!-- 右侧操作区域：视图切换 + 新建工艺按钮 -->
        <div class="flex items-center gap-10">
          <ViewToggle
            v-model="viewMode"
            :options="viewOptions"
            size="small"
            :show-label="false"
            :icon-size="16"
            align="right"
          />
          <NButton
            v-permission="'POST /api/v2/devices/{id}/processes'"
            type="primary"
            @click="handleAdd"
          >
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建工艺
          </NButton>
        </div>
      </div>
    </template>

    <!-- 表格视图 -->
    <div v-if="viewMode === 'table'" class="table-container">
      <!-- 搜索栏 -->
      <div class="mb-4">
        <n-card>
          <div class="flex flex-wrap items-center gap-4">
            <QueryBarItem label="工艺类型">
              <NSelect
                v-model:value="queryItems.process_type"
                :options="processTypeOptions"
                placeholder="请选择工艺类型"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <QueryBarItem label="工艺名称">
              <NInput
                v-model:value="queryItems.process_name"
                placeholder="请输入工艺名称"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <QueryBarItem label="工艺编码">
              <NInput
                v-model:value="queryItems.process_code"
                placeholder="请输入工艺编码"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <div class="flex items-center gap-2">
              <NButton type="primary" @click="handleSearch(queryItems)">
                <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
                查询
              </NButton>
              <NButton @click="handleReset">
                <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
                重置
              </NButton>
            </div>
          </div>
        </n-card>
      </div>

      <n-data-table :columns="columns" :data="tableData" :loading="loading" />

      <div v-if="tableData.length > 0" class="mt-6 flex justify-center">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          :show-size-picker="pagination.showSizePicker"
          :show-quick-jumper="pagination.showQuickJumper"
          :prefix="pagination.prefix"
          :suffix="pagination.suffix"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 卡片视图 -->
    <div v-if="viewMode === 'card'" class="card-container">
      <!-- 搜索栏 -->
      <div class="mb-4">
        <n-card>
          <div class="flex flex-wrap items-center gap-4">
            <QueryBarItem label="工艺类型">
              <NSelect
                v-model:value="queryItems.process_type"
                :options="processTypeOptions"
                placeholder="请选择工艺类型"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <QueryBarItem label="工艺名称">
              <NInput
                v-model:value="queryItems.process_name"
                placeholder="请输入工艺名称"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <QueryBarItem label="工艺编码">
              <NInput
                v-model:value="queryItems.process_code"
                placeholder="请输入工艺编码"
                clearable
                style="width: 200px"
              />
            </QueryBarItem>
            <div class="flex items-center gap-2">
              <NButton type="primary" @click="handleSearch(queryItems)">
                <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
                查询
              </NButton>
              <NButton @click="handleReset">
                <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
                重置
              </NButton>
            </div>
          </div>
        </n-card>
      </div>

      <!-- 卡片网格 -->
      <div class="process-grid">
        <NCard
          v-for="process in processes"
          :key="process.id"
          class="process-card"
          :class="getProcessCardClass(process.status)"
          hoverable
          @click="handleViewDetail(process)"
        >
          <!-- 工艺状态指示器 -->
          <div class="status-indicator" :class="getStatusClass(process.status)"></div>

          <!-- 工艺基本信息 -->
          <div class="process-header">
            <div class="process-info">
              <h3 class="process-name">{{ process.process_name }}</h3>
              <p class="process-id">{{ process.process_code }}</p>
            </div>
            <div class="process-type">
              <NTag type="info" size="small">
                {{ getProcessTypeName(process.process_type) }}
              </NTag>
            </div>
          </div>

          <!-- 工艺状态和版本 -->
          <div class="process-status-version">
            <NTag :type="getStatusTagType(process.status)" size="small">
              {{ getStatusText(process.status) }}
            </NTag>
            <span class="version-text">v{{ process.version }}</span>
          </div>

          <!-- 焊接规范信息 -->
          <div class="spec-info">
            <div class="spec-title">📋 焊接规范信息</div>
            <div class="spec-row">
              <span class="spec-label">规范类型:</span>
              <span class="spec-value">{{ process.spec_type || '--' }}</span>
            </div>
          </div>

          <!-- 焊接参数 -->
          <div class="welding-params">
            <div class="params-title">⚡ 焊接参数</div>
            <div class="params-grid">
              <div class="param-item">
                <span class="param-label">气体:</span>
                <span class="param-value">{{ process.gas_type || '--' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">丝径:</span>
                <span class="param-value">{{ process.wire_diameter || '--' }}mm</span>
              </div>
              <div class="param-item">
                <span class="param-label">电流上限:</span>
                <span class="param-value">{{ process.welding_current_upper || '--' }}A</span>
              </div>
              <div class="param-item">
                <span class="param-label">电压下限:</span>
                <span class="param-value">{{ process.welding_voltage_lower || '--' }}V</span>
              </div>
            </div>
          </div>

          <!-- 工艺描述 -->
          <div v-if="process.description" class="process-description">
            <div class="desc-title">📝 工艺描述</div>
            <p class="desc-text">{{ process.description }}</p>
          </div>

          <!-- 工艺操作 -->
          <div class="process-actions" @click.stop>
            <NButton size="small" type="info" class="mr-8" @click="handleViewDetail(process)">
              详情
            </NButton>
            <NButton
              v-permission="'PUT /api/v2/devices/processes/{id}'"
              size="small"
              type="primary"
              class="mr-8"
              @click="handleEdit(process)"
            >
              编辑
            </NButton>
            <NPopconfirm @positive-click="() => handleDelete([process.id])">
              <template #trigger>
                <NButton
                  v-permission="'DELETE /api/v2/devices/processes/{id}'"
                  size="small"
                  type="error"
                >
                  删除
                </NButton>
              </template>
              确定删除该工艺吗?
            </NPopconfirm>
          </div>
        </NCard>
      </div>

      <!-- 空状态 -->
      <div v-if="processes.length === 0" class="py-8 text-center">
        <div class="text-gray-500">暂无工艺数据</div>
      </div>

      <!-- 分页组件 -->
      <div v-if="processes.length > 0" class="mt-6 flex justify-center">
        <NPagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          :show-size-picker="pagination.showSizePicker"
          :show-quick-jumper="pagination.showQuickJumper"
          :prefix="pagination.prefix"
          :suffix="pagination.suffix"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      width="800px"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="120"
        :model="modalForm"
        :rules="processRules"
        :disabled="modalAction === 'view'"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h4 class="section-title">基本信息</h4>
          <div class="grid grid-cols-2 gap-4">
            <NFormItem label="工艺名称" path="process_name">
              <NInput v-model:value="modalForm.process_name" placeholder="请输入工艺名称" />
            </NFormItem>
            <NFormItem label="工艺编码" path="process_code">
              <NInput v-model:value="modalForm.process_code" placeholder="请输入工艺编码" />
            </NFormItem>
            <NFormItem label="工艺类型" path="process_type">
              <NSelect
                v-model:value="modalForm.process_type"
                :options="processTypeOptions.slice(1)"
                placeholder="请选择工艺类型"
              />
            </NFormItem>
            <NFormItem label="版本" path="version">
              <NInput v-model:value="modalForm.version" placeholder="请输入版本号" />
            </NFormItem>
          </div>
          <NFormItem label="工艺描述">
            <NInput
              v-model:value="modalForm.description"
              type="textarea"
              placeholder="请输入工艺描述"
              :rows="3"
            />
          </NFormItem>
        </div>

        <!-- 焊接规范信息 -->
        <div class="form-section">
          <h4 class="section-title">焊接规范信息</h4>
          <div class="grid grid-cols-2 gap-4">
            <NFormItem label="规范类型">
              <NSelect
                v-model:value="modalForm.spec_type"
                :options="specTypeOptions"
                placeholder="请选择规范类型"
              />
            </NFormItem>
            <NFormItem label="规范状态">
              <NSelect
                v-model:value="modalForm.spec_status"
                :options="[
                  { label: '发布', value: 'published' },
                  { label: '草稿', value: 'draft' },
                ]"
                placeholder="请选择规范状态"
              />
            </NFormItem>
            <NFormItem label="规范版本">
              <NInput v-model:value="modalForm.spec_version" placeholder="请输入规范版本" />
            </NFormItem>
            <NFormItem label="规范编码">
              <NInput v-model:value="modalForm.spec_code" placeholder="请输入规范编码" />
            </NFormItem>
          </div>
          <NFormItem label="规范说明">
            <NInput
              v-model:value="modalForm.spec_description"
              type="textarea"
              placeholder="请输入规范说明"
              :rows="2"
            />
          </NFormItem>
        </div>

        <!-- 焊接参数 -->
        <div class="form-section">
          <h4 class="section-title">焊接参数</h4>
          <div class="grid grid-cols-3 gap-4">
            <NFormItem label="焊接控制">
              <NSelect
                v-model:value="modalForm.welding_control"
                :options="weldingControlOptions"
                placeholder="请选择焊接控制"
              />
            </NFormItem>
            <NFormItem label="焊接方式">
              <NSelect
                v-model:value="modalForm.welding_method"
                :options="weldingControlOptions"
                placeholder="请选择焊接方式"
              />
            </NFormItem>
            <NFormItem label="点焊时间">
              <NInputNumber v-model:value="modalForm.point_time" placeholder="点焊时间" :min="0" />
            </NFormItem>
            <NFormItem label="输出控制">
              <NSelect
                v-model:value="modalForm.output_control"
                :options="[
                  { label: '电压', value: 'voltage' },
                  { label: '电流', value: 'current' },
                ]"
                placeholder="请选择输出控制"
              />
            </NFormItem>
            <NFormItem label="分级">
              <NSelect
                v-model:value="modalForm.classification"
                :options="[
                  { label: '自动', value: 'auto' },
                  { label: '手动', value: 'manual' },
                ]"
                placeholder="请选择分级"
              />
            </NFormItem>
            <NFormItem label="气体">
              <NSelect
                v-model:value="modalForm.gas_type"
                :options="gasTypeOptions"
                placeholder="请选择气体类型"
              />
            </NFormItem>
            <NFormItem label="材质">
              <NSelect
                v-model:value="modalForm.material"
                :options="materialOptions"
                placeholder="请选择材质"
              />
            </NFormItem>
            <NFormItem label="丝径(mm)">
              <NInputNumber
                v-model:value="modalForm.wire_diameter"
                placeholder="丝径"
                :min="0"
                :step="0.1"
              />
            </NFormItem>
            <NFormItem label="焊接电流上限">
              <NInputNumber
                v-model:value="modalForm.welding_current_upper"
                placeholder="焊接电流上限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电压下限">
              <NInputNumber
                v-model:value="modalForm.welding_voltage_lower"
                placeholder="焊接电压下限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电流上限">
              <NInputNumber
                v-model:value="modalForm.welding_current_upper_limit"
                placeholder="焊接电流上限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电压下限">
              <NInputNumber
                v-model:value="modalForm.welding_voltage_lower_limit"
                placeholder="焊接电压下限"
                :min="0"
              />
            </NFormItem>
          </div>
        </div>

        <!-- 报警条件 -->
        <div class="form-section">
          <h4 class="section-title">报警条件</h4>
          <div class="grid grid-cols-3 gap-4">
            <NFormItem label="焊接电流上限">
              <NInputNumber
                v-model:value="modalForm.alarm_current_upper"
                placeholder="焊接电流上限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电压下限">
              <NInputNumber
                v-model:value="modalForm.alarm_voltage_lower"
                placeholder="焊接电压下限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电流上限">
              <NInputNumber
                v-model:value="modalForm.alarm_current_upper_limit"
                placeholder="焊接电流上限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="焊接电压下限">
              <NInputNumber
                v-model:value="modalForm.alarm_voltage_lower_limit"
                placeholder="焊接电压下限"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="报警模式">
              <NSelect
                v-model:value="modalForm.alarm_mode"
                :options="[
                  { label: '不启用', value: 'disabled' },
                  { label: '启用', value: 'enabled' },
                ]"
                placeholder="请选择报警模式"
              />
            </NFormItem>
            <NFormItem label="起弧延时时间">
              <NInputNumber
                v-model:value="modalForm.start_delay_time"
                placeholder="起弧延时时间"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="报警延时时间">
              <NInputNumber
                v-model:value="modalForm.arc_delay_time"
                placeholder="报警延时时间"
                :min="0"
              />
            </NFormItem>
            <NFormItem label="停机延时时间">
              <NInputNumber
                v-model:value="modalForm.stop_delay_time"
                placeholder="停机延时时间"
                :min="0"
              />
            </NFormItem>
          </div>
        </div>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
/* 工艺网格布局 */
.process-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 16px 0;
}

/* 工艺卡片样式 */
.process-card {
  position: relative;
  border-radius: 12px;
  padding: 20px;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 280px;
}

.process-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px var(--n-box-shadow-color);
}

.process-card--published {
  border-color: var(--n-success-color);
  background: var(--n-color-embedded);
}

.process-card--draft {
  border-color: var(--n-warning-color);
  background: var(--n-color-embedded);
}

.process-card--archived {
  border-color: var(--n-border-color);
  background: var(--n-color-embedded);
  opacity: 0.8;
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator--published {
  background: var(--n-success-color);
  box-shadow: 0 0 0 4px var(--n-success-color-hover);
  animation: pulse 2s infinite;
}

.status-indicator--draft {
  background: var(--n-warning-color);
  box-shadow: 0 0 0 4px var(--n-warning-color-hover);
}

.status-indicator--archived {
  background: var(--n-border-color);
  box-shadow: 0 0 0 4px var(--n-border-color-hover);
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 工艺头部信息 */
.process-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-right: 30px;
}

.process-info {
  flex: 1;
}

.process-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 6px 0;
  line-height: 1.3;
}

.process-id {
  font-size: 14px;
  color: var(--n-secondary-text-color);
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
}

.process-type {
  margin-left: 12px;
}

/* 工艺状态和版本 */
.process-status-version {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.version-text {
  font-size: 12px;
  color: var(--n-secondary-text-color);
  font-weight: 500;
  background: var(--n-color-embedded);
  padding: 2px 8px;
  border-radius: 4px;
}

/* 焊接规范信息 */
.spec-info {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 8px;
  border-left: 4px solid var(--n-info-color);
}

.spec-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin-bottom: 8px;
}

.spec-row {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.spec-label {
  color: var(--n-secondary-text-color);
  margin-right: 8px;
  min-width: 70px;
  font-weight: 500;
}

.spec-value {
  color: var(--n-text-color);
  font-weight: 600;
}

/* 焊接参数 */
.welding-params {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 8px;
  border-left: 4px solid var(--n-warning-color);
}

.params-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin-bottom: 10px;
}

.params-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.param-item {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.param-label {
  color: var(--n-secondary-text-color);
  margin-right: 6px;
  min-width: 50px;
  font-weight: 500;
}

.param-value {
  color: var(--n-text-color);
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
}

/* 工艺描述 */
.process-description {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--n-color-embedded);
  border-radius: 8px;
  border-left: 4px solid var(--n-primary-color);
}

.desc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin-bottom: 8px;
}

.desc-text {
  font-size: 13px;
  color: var(--n-text-color);
  line-height: 1.5;
  margin: 0;
}

/* 工艺操作 */
.process-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--n-divider-color);
}

/* 表单分组样式 */
.form-section {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--n-color-embedded);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--n-primary-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .process-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px 0;
  }

  .process-card {
    padding: 16px;
    min-height: auto;
  }

  .process-name {
    font-size: 16px;
  }

  .params-grid {
    grid-template-columns: 1fr;
  }

  .param-item {
    font-size: 13px;
  }

  .param-label {
    min-width: 60px;
  }
}

@media (max-width: 480px) {
  .process-header {
    flex-direction: column;
    gap: 10px;
    padding-right: 20px;
  }

  .process-type {
    margin-left: 0;
  }

  .process-actions {
    flex-direction: column;
  }

  .form-section {
    padding: 12px;
  }

  .section-title {
    font-size: 14px;
  }
}
</style>
