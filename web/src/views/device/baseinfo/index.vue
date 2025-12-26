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
  useMessage,
  useDialog,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import DeviceInfoSearchBar from '@/components/query-bar/DeviceInfoSearchBar.vue'
import { PermissionDataWrapper } from '@/components/Permission'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { renderIcon } from '@/utils'
import api from '@/api'
// ✅ Shared API 迁移 (2025-10-25)
import { deviceApi, deviceTypeApi } from '@/api/device-shared'
import { useRouter } from 'vue-router'

defineOptions({ name: '设备基础信息' })

// ==================== 类型定义 ====================

interface QueryItems {
  device_type: string
  [key: string]: any
}

interface DeviceType {
  type_code: string
  type_name: string
  [key: string]: any
}

interface DeviceInfo {
  id?: string | number
  device_code: string
  device_name: string
  device_type: string
  device_model: string
  manufacturer: string
  online_address: string
  status?: string
  [key: string]: any
}

const $table = ref<any>(null)
const queryItems = ref<QueryItems>({
  device_type: 'welding', // 默认选择焊机
})
const vPermission = resolveDirective('permission')
const $message = useMessage()
const dialog = useDialog()
const router = useRouter()

// 设备类型数据
const deviceTypes = ref<DeviceType[]>([])

// 表单初始化内容
const initForm = {
  device_name: '',
  manufacturer: '',
  device_code: '',
  device_type: 'welding',
  device_model: '',
  online_address: '',
}

// 设备数据
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
const viewMode = ref('card') // 'table' 或 'card'

// 计算属性：根据视图模式返回对应的数据
const devices = computed(() => {
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

// 选中行
const checkedRowKeys = ref([])

// 模态框状态
const modalVisible = ref(false)
const modalTitle = ref('')
const modalAction = ref('')
const modalLoading = ref(false)
const modalForm = ref({ ...initForm })
const modalFormRef = ref(null)

// 处理添加设备
const handleAdd = () => {
  modalAction.value = 'add'
  modalTitle.value = '新建设备'
  modalForm.value = { ...initForm }
  modalVisible.value = true
}

// 处理编辑设备
const handleEdit = (row: DeviceInfo) => {
  modalAction.value = 'edit'
  modalTitle.value = '编辑设备'
  modalForm.value = { ...row } as any
  modalVisible.value = true
}

// 处理删除设备
const handleDelete = async (ids) => {
  const idList = Array.isArray(ids) ? ids : [ids]
  if (idList.length === 0) return

  const executeDelete = async () => {
    try {
      if (idList.length > 1) {
        await deviceApi.batchDelete(idList)
      } else {
        await deviceApi.delete(idList[0])
      }
      $message?.success('删除设备成功')
      checkedRowKeys.value = [] // 清空选中
      // 刷新列表
      if (viewMode.value === 'table') {
        loadTableData()
      } else {
        // loadCardData() ? 
        // The original code called getDevices() which seems to be loadTableData alias?
        // Ah, original code called getDevices(). Let's check if getDevices exists.
        // Looking at original code: getDevices() // 统一刷新
        // But I didn't see getDevices definition in the snippet. 
        // Wait, loadTableData is passed to PermissionDataWrapper @refresh.
        // I will use loadTableData() assuming it handles both or viewMode logic handles it.
        // Actually PermissionDataWrapper uses loadTableData.
        loadTableData()
      }
    } catch (error) {
      console.error('删除设备失败:', error)
      $message?.error(`删除设备失败: ${error.message || '未知错误'}`)
    }
  }

  // 1. 单个删除：检查关联数据
  if (idList.length === 1) {
    try {
      const id = idList[0]
      // 尝试获取关联统计
      const { data: counts } = await deviceApi.getRelatedCounts(id)
      
      // 检查是否有关联数据
      // counts keys: repair_records, process_executions, etc.
      // Filter keys that have value > 0
      const hasRelations = Object.values(counts).some(v => v > 0)
      
      if (hasRelations) {
        // 构建提示详情
        const details = []
        if (counts.process_monitoring > 0) details.push(`工艺监控数据 (${counts.process_monitoring})`)
        if (counts.process_executions > 0) details.push(`工艺执行记录 (${counts.process_executions})`)
        if (counts.processes > 0) details.push(`工艺定义 (${counts.processes})`)
        if (counts.maintenance_reminders > 0) details.push(`维护提醒 (${counts.maintenance_reminders})`)
        if (counts.maintenance_plans > 0) details.push(`维护计划 (${counts.maintenance_plans})`)
        if (counts.repair_records > 0) details.push(`维修记录 (${counts.repair_records})`)
        if (counts.maintenance_records > 0) details.push(`维护记录 (${counts.maintenance_records})`)
        if (counts.alarm_history > 0) details.push(`报警历史 (${counts.alarm_history})`)
        
        dialog.warning({
          title: '关联数据删除确认',
          content: `检测到该设备包含以下关联数据：\n\n${details.join('、')}\n\n删除设备将自动清理这些数据且不可恢复，是否继续？`,
          positiveText: '确认删除',
          negativeText: '取消',
          onPositiveClick: executeDelete
        })
        return
      }
    } catch (e) {
      console.warn('获取关联统计失败，降级处理', e)
    }
  }

  // 2. 批量删除或无关联数据：普通确认
  dialog.warning({
    title: '删除确认',
    content: `确定删除选中的 ${idList.length} 台设备吗？此操作不可恢复。`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: executeDelete
  })
}

// 跳转到设备维修记录
const handleViewRepairRecords = (device) => {
  router.push({
    path: '/device-maintenance/repair-records',
    query: {
      device_id: device.id,
      device_name: device.device_name,
      device_code: device.device_code
    }
  })
}

// 卡片样式辅助函数
const getDeviceCardClass = (is_locked) => {
  const baseClass = 'device-card'
  return is_locked ? `${baseClass} device-card--locked` : `${baseClass} device-card--inuse`
}

const getStatusClass = (is_locked) => {
  return is_locked ? 'status-indicator--locked' : 'status-indicator--inuse'
}

const getStatusTagType = (is_locked) => {
  return is_locked ? 'error' : 'success'
}

const getStatusText = (is_locked) => {
  return is_locked ? '锁定' : '在用'
}

// 处理保存设备
const handleSave = async () => {
  try {
    await modalFormRef.value?.validate()
    modalLoading.value = true

    if (modalAction.value === 'add') {
      await deviceApi.create(modalForm.value)
      $message?.success('新建设备成功')
    } else {
      await deviceApi.update(modalForm.value.id!, modalForm.value)
      $message?.success('编辑设备成功')
    }

    modalVisible.value = false
    getDevices() // 统一刷新
  } catch (error) {
    console.error('保存设备失败:', error)
    $message?.error(`保存设备失败: ${error.message || '未知错误'}`)
  } finally {
    modalLoading.value = false
  }
}

// 统一获取数据
const getDevices = async () => {
  loading.value = true
  const params = {
    ...queryItems.value,
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  }
  try {
    const response = await deviceApi.list(params)
    console.log('设备列表API v2响应数据:', response)

    if (response && response.data) {
      console.log('设备列表API响应数据:', response)
      const dataItems = Array.isArray(response.data) ? response.data : response.data.items || []

      if (Array.isArray(dataItems)) {
        tableData.value = dataItems
        cardData.value = dataItems
        // 从API响应中正确获取总记录数
        pagination.value.itemCount =
          response.total || response.meta?.total || response.data.total || dataItems.length
        console.log('设备表格数据:', tableData.value)
        console.log('设备卡片数据:', cardData.value)
        console.log('设备分页信息:', {
          page: pagination.value.page,
          pageSize: pagination.value.pageSize,
          itemCount: pagination.value.itemCount,
          totalPages: Math.ceil(pagination.value.itemCount / pagination.value.pageSize),
        })
      } else {
        console.error('设备API返回数据格式不正确:', dataItems)
        $message?.error('获取设备数据失败: 数据格式不正确')
        tableData.value = []
        cardData.value = []
        pagination.value.itemCount = 0
      }
    } else {
      console.error('设备API返回数据格式不正确:', response)
      $message?.error('获取设备数据失败: 数据格式不正确')
      tableData.value = []
      cardData.value = []
      pagination.value.itemCount = 0
    }
  } catch (error) {
    console.error('获取设备列表失败:', error)
    $message?.error(`获取设备列表失败: ${error.message || '未知错误'}`)
    tableData.value = []
    cardData.value = []
    pagination.value.itemCount = 0
  } finally {
    loading.value = false
  }
}

// 添加loadTableData方法（模板中使用）
const loadTableData = () => {
  getDevices()
}

const handleSearch = (params) => {
  queryItems.value = { ...params }
  pagination.value.page = 1
  console.log('搜索参数:', queryItems.value)
  getDevices()
}

const handleReset = () => {
  queryItems.value = { device_type: 'welding' }
  pagination.value.page = 1
  console.log('重置搜索条件')
  getDevices()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  getDevices()
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  getDevices()
}

// 设备类型代码映射为中文名称
const getDeviceTypeName = (typeCode) => {
  if (deviceTypes.value && deviceTypes.value.length > 0) {
    const deviceType = deviceTypes.value.find((type) => type.type_code === typeCode)
    if (deviceType) {
      return deviceType.type_name
    }
  }

  // 降级处理：使用默认映射
  const defaultTypeMap = {
    welding: '焊机',
    cutting: '切割设备',
    assembly: '装配设备',
    server: '服务器',
    network: '网络设备',
    storage: '存储设备',
    security: '安全设备',
    other: '其他',
  }

  return defaultTypeMap[typeCode] || typeCode
}

// 获取设备类型图标
const getDeviceTypeIcon = (typeCode) => {
  if (deviceTypes.value && deviceTypes.value.length > 0) {
    const deviceType = deviceTypes.value.find((type) => type.type_code === typeCode)
    if (deviceType && deviceType.icon) {
      return deviceType.icon
    }
  }

  // 降级处理：使用默认图标映射
  const defaultIconMap = {
    welding: 'material-symbols:precision-manufacturing',
    cutting: 'material-symbols:content-cut',
    assembly: 'material-symbols:build',
    server: 'material-symbols:dns',
    network: 'material-symbols:router',
    storage: 'material-symbols:storage',
    security: 'material-symbols:security',
    other: 'material-symbols:devices',
  }

  return defaultIconMap[typeCode] || 'material-symbols:precision-manufacturing'
}

// 权限相关处理
const handleContactAdmin = () => {
  $message.info('请联系系统管理员获取设备信息查看权限')
}

// 加载设备类型数据
const loadDeviceTypes = async () => {
  try {
    const response = await deviceTypeApi.list()
    if (response && response.data) {
      const typeData = Array.isArray(response.data) ? response.data : response.data.items || []
      deviceTypes.value = typeData
      console.log('设备类型数据加载成功:', deviceTypes.value)
    }
  } catch (error) {
    console.warn('获取设备类型失败，使用默认选项:', error)
    $message.warning('获取设备类型失败，使用默认选项')
    // deviceTypes保持空数组，计算属性会自动使用降级选项
  }
}

onMounted(async () => {
  try {
    await loadDeviceTypes()
    await getDevices()
    console.log('设备数据加载完成:', devices.value)
  } catch (error) {
    console.error('设备数据加载失败:', error)
    $message?.error('设备数据加载失败')
  }
})

// 监听视图模式切换
const stopWatchViewMode = watch(viewMode, (newMode) => {
  // 切换视图时保持每页20条不变
  pagination.value.pageSize = 20
  pagination.value.page = 1 // 重置到第一页
  getDevices() // 重新获取数据
})

// 组件卸载时清理
onUnmounted(() => {
  // 停止watch监听器
  stopWatchViewMode()
  // 清理数据
  tableData.value = []
  cardData.value = []
})

// 设备类型选项 - 计算属性，支持动态获取和降级处理
const deviceTypeOptions = computed(() => {
  const baseOptions = [{ label: '全部设备', value: '' }]

  if (deviceTypes.value && deviceTypes.value.length > 0) {
    const dynamicOptions = deviceTypes.value.map((type) => ({
      label: type.type_name,
      value: type.type_code,
    }))
    return [...baseOptions, ...dynamicOptions]
  }

  // 降级处理：API调用失败时使用默认选项
  const defaultOptions = [
    { label: '焊机', value: 'welding' },
    { label: '切割设备', value: 'cutting' },
    { label: '装配设备', value: 'assembly' },
    { label: '服务器', value: 'server' },
    { label: '网络设备', value: 'network' },
    { label: '存储设备', value: 'storage' },
    { label: '安全设备', value: 'security' },
    { label: '其他', value: 'other' },
  ]
  return [...baseOptions, ...defaultOptions]
})

// 设备状态选项 (暂时注释，未来可能使用)
// const statusOptions = [
//   { label: '在线', value: 'active' },
//   { label: '离线', value: 'inactive' },
//   { label: '维护中', value: 'maintenance' },
//   { label: '故障', value: 'fault' },
// ]

const columns = [
  { type: 'selection' },
  {
    title: '设备名称',
    key: 'device_name',
    width: 150,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '设备厂家',
    key: 'manufacturer',
    width: 120,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '设备编码',
    key: 'device_code',
    width: 180,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '设备类型',
    key: 'device_type',
    width: 120,
    align: 'center',
    render(row: DeviceInfo) {
      return h(NTag, { type: 'info' }, { default: () => getDeviceTypeName(row.device_type) })
    },
  },
  {
    title: '设备型号',
    key: 'device_model',
    width: 150,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '在线地址',
    key: 'online_address',
    width: 140,
    ellipsis: { tooltip: true },
    align: 'center',
  },
  {
    title: '操作',
    key: 'actions',
    width: 360,
    align: 'center',
    fixed: 'right',
    hideInExcel: true,
    render(row: DeviceInfo) {
      return [
        h(PermissionButton, {
          permission: 'GET /api/v2/device/maintenance/repair-records',
          size: 'small',
          type: 'info',
          secondary: true,
          onClick: () => handleViewRepairRecords(row),
        }, {
          default: () => '维修记录',
          icon: renderIcon('mdi:clipboard-text-outline', { size: 14 }),
        }),
        h(PermissionButton, {
          permission: 'GET /api/v2/devices/{device_id}/history',
          size: 'small',
          type: 'info',
          secondary: true,
          style: 'margin-left: 8px;',
          onClick: () => {
            // 跳转到数据模型预览页面，查看该设备的数据模型
            router.push({
              path: '/data-model/preview',
              query: {
                device_code: row.device_code,
                device_name: row.device_name,
                device_type: row.device_type,
              },
            })
          },
        }, {
          default: () => '查看数据',
          icon: renderIcon('mdi:chart-line', { size: 14 }),
        }),
        h(PermissionButton, {
          permission: 'PUT /api/v2/devices/{id}',
          size: 'small',
          type: 'primary',
          secondary: true,
          style: 'margin-left: 8px;',
          onClick: () => handleEdit(row),
        }, {
          default: () => '编辑',
          icon: renderIcon('material-symbols:edit-outline', { size: 14 }),
        }),
        h(PermissionButton, {
          permission: 'DELETE /api/v2/devices/{id}',
          size: 'small',
          type: 'error',
          style: 'margin-left: 8px;',
          onClick: () => handleDelete([row.id!])
        }, {
          default: () => '删除',
          icon: renderIcon('material-symbols:delete-outline', { size: 14 }),
        }),
      ]
    },
  },
]

// 表单验证规则
const deviceRules = {
  device_name: [
    {
      required: true,
      message: '请输入设备名称',
      trigger: ['input', 'blur'],
    },
  ],
  manufacturer: [
    {
      required: true,
      message: '请输入设备厂家',
      trigger: ['input', 'blur'],
    },
  ],
  device_code: [
    {
      required: true,
      message: '请输入设备编码',
      trigger: ['input', 'blur'],
    },
  ],
  device_type: [
    {
      required: true,
      message: '请选择设备类型',
      trigger: ['change', 'blur'],
    },
  ],
  device_model: [
    {
      required: true,
      message: '请输入设备型号',
      trigger: ['input', 'blur'],
    },
  ],
  online_address: [
    {
      required: true,
      message: '请输入在线地址',
      trigger: ['input', 'blur'],
    },
    {
      pattern: /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/,
      message: '请输入正确的IP地址格式',
      trigger: ['input', 'blur'],
    },
  ],
}
</script>

<template>
  <CommonPage show-footer>
    <template #action>
      <div class="w-full flex items-center justify-end">
        <!-- 右侧操作区域：视图切换 + 新建设备按钮 -->
        <div class="flex items-center gap-10">
          <ViewToggle
            v-model="viewMode"
            :options="viewOptions"
            size="small"
            :show-label="false"
            :icon-size="16"
            align="right"
          />
          <PermissionButton
            v-if="viewMode === 'table'"
            permission="DELETE /api/v2/devices/{id}"
            type="error"
            :disabled="checkedRowKeys.length === 0"
            class="mr-4"
            @click="() => handleDelete(checkedRowKeys)"
          >
            <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-5" />批量删除
          </PermissionButton>
          <PermissionButton 
            permission="POST /api/v2/devices" 
            type="primary" 
            @click="handleAdd"
          >
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建设备
          </PermissionButton>
        </div>
      </div>
    </template>

    <!-- 表格视图 -->
    <div v-if="viewMode === 'table'" class="table-container">
      <DeviceInfoSearchBar
        :model-value="queryItems"
        :device-type-options="deviceTypeOptions"
        @update:model-value="(val) => (queryItems = val)"
        @search="handleSearch"
        @reset="handleReset"
      />

      <PermissionDataWrapper
        :data="tableData"
        :loading="loading"
        permission="GET /api/v2/devices"
        permission-name="设备信息查看"
        empty-title="暂无设备信息"
        empty-description="当前没有设备信息数据，您可以点击上方的【新建设备】按钮来创建第一台设备"
        loading-text="正在加载设备信息数据..."
        @refresh="loadTableData"
        @contact="handleContactAdmin"
        @create="handleAdd"
      >
        <template #default="{ data }">
          <n-data-table
            :columns="columns"
            :data="data"
            :loading="loading"
            :row-key="(row) => row.id"
            v-model:checked-row-keys="checkedRowKeys"
          />

          <div v-if="data.length > 0" class="mt-6 flex justify-center">
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
        </template>
      </PermissionDataWrapper>
    </div>

    <!-- 卡片视图 -->
    <div v-if="viewMode === 'card'" class="card-container">
      <DeviceInfoSearchBar
        :model-value="queryItems"
        :device-type-options="deviceTypeOptions"
        @update:model-value="(val) => (queryItems = val)"
        @search="handleSearch"
        @reset="handleReset"
      />

      <PermissionDataWrapper
        :data="cardData"
        :loading="loading"
        permission="GET /api/v2/devices"
        permission-name="设备信息查看"
        empty-title="暂无设备信息"
        empty-description="当前没有设备信息数据，您可以点击上方的【新建设备】按钮来创建第一台设备"
        loading-text="正在加载设备信息数据..."
        @refresh="loadTableData"
        @contact="handleContactAdmin"
        @create="handleAdd"
      >
        <template #default="{ data }">
          <!-- 卡片网格 -->
          <div class="device-grid">
            <NCard
              v-for="device in data"
              :key="device.id"
              class="device-card"
              :class="getDeviceCardClass(device.status)"
              hoverable
            >
          <!-- 设备状态指示器 -->
          <div class="status-indicator" :class="getStatusClass(device.status)"></div>

          <!-- 设备基本信息 -->
          <div class="device-header">
            <div class="device-info">
              <div class="device-name-row">
                <TheIcon :icon="getDeviceTypeIcon(device.device_type)" :size="20" class="device-type-icon mr-8" />
                <h3 class="device-name" :title="device.device_name">{{ device.device_name }}</h3>
              </div>
              <p class="device-id">{{ device.device_code }}</p>
            </div>
            <div class="device-type-status-row">
              <NTag type="info" size="small" class="device-type-tag">
                {{ getDeviceTypeName(device.device_type) }}
              </NTag>
              <NTag :type="getStatusTagType(device.status)" size="small" class="device-status-tag">
                {{ getStatusText(device.status) }}
              </NTag>
            </div>
          </div>

          <!-- 监控数据 -->
          <div class="monitoring-data">
            <div class="data-row">
              <span class="data-label">🏭 设备厂家:</span>
              <span class="data-value" :title="device.manufacturer || '--'">{{ device.manufacturer || '--' }}</span>
            </div>
            <div class="data-row">
              <span class="data-label">📦 设备型号:</span>
              <span class="data-value" :title="device.device_model || '--'">{{ device.device_model || '--' }}</span>
            </div>
            <div class="data-row">
              <span class="data-label">🌐 在线地址:</span>
              <span class="data-value" :title="device.online_address || '--'">{{ device.online_address || '--' }}</span>
            </div>
          </div>

          <!-- 设备操作 -->
          <div class="device-actions">
            <PermissionButton
              permission="GET /api/v2/device/maintenance/repair-records"
              size="small"
              type="info"
              class="mr-8"
              @click="handleViewRepairRecords(device)"
              title="维修记录"
            >
              <TheIcon icon="mdi:clipboard-text-outline" :size="14" />
            </PermissionButton>
            <PermissionButton
              permission="GET /api/v2/devices/{device_id}/history"
              size="small"
              type="info"
              class="mr-8"
              @click="router.push({
                path: '/data-model/preview',
                query: {
                  device_code: device.device_code,
                  device_name: device.device_name,
                  device_type: device.device_type,
                },
              })"
              title="查看数据"
            >
              <TheIcon icon="mdi:chart-line" :size="14" />
            </PermissionButton>
            <PermissionButton
              permission="PUT /api/v2/devices/{id}"
              size="small"
              type="primary"
              class="mr-8"
              @click="handleEdit(device)"
              title="编辑"
            >
              <TheIcon icon="mdi:pencil" :size="14" />
            </PermissionButton>
            <PermissionButton
              permission="DELETE /api/v2/devices/{id}"
              size="small"
              type="error"
              title="删除"
              @click="() => handleDelete([device.id])"
            >
              <TheIcon icon="mdi:delete" :size="14" />
            </PermissionButton>
          </div>
        </NCard>
      </div>

      <!-- 分页组件 -->
      <div v-if="data.length > 0" class="mt-6 flex justify-center">
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
        </template>
      </PermissionDataWrapper>
    </div>

    <!-- 新增/编辑弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="deviceRules"
        :disabled="modalAction === 'view'"
      >
        <NFormItem label="设备名称" path="device_name">
          <NInput v-model:value="modalForm.device_name" placeholder="请输入设备名称" />
        </NFormItem>
        <NFormItem label="设备厂家" path="manufacturer">
          <NInput v-model:value="modalForm.manufacturer" placeholder="请输入设备厂家" />
        </NFormItem>
        <NFormItem label="设备编码" path="device_code">
          <NInput v-model:value="modalForm.device_code" placeholder="请输入设备编码" />
        </NFormItem>
        <NFormItem label="设备类型" path="device_type">
          <NSelect
            v-model:value="modalForm.device_type"
            :options="deviceTypeOptions"
            placeholder="请选择设备类型"
          />
        </NFormItem>
        <NFormItem label="设备型号" path="device_model">
          <NInput v-model:value="modalForm.device_model" placeholder="请输入设备型号" />
        </NFormItem>
        <NFormItem label="在线地址" path="online_address">
          <NInput v-model:value="modalForm.online_address" placeholder="请输入在线地址" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
/* 设备网格布局 */
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 16px 0;
}

/* 设备卡片样式 */
.device-card {
  position: relative;
  border-radius: 12px;
  padding: 18px;
  border: 1px solid var(--n-color-primary);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
  min-height: 280px;
  display: flex;
  flex-direction: column;
}

.device-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--n-color-primary);
  opacity: 0.1;
  z-index: -1;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  border-color: var(--n-primary-color-hover);
}

.device-card--active {
  border-color: var(--n-success-color);
  background: var(--n-color-embedded);
}

.device-card--inactive {
  border-color: var(--n-border-color);
  background: var(--n-color-embedded);
}

.device-card--maintenance {
  border-color: var(--n-warning-color);
  background: var(--n-color-embedded);
}

.device-card--locked {
  border-color: var(--n-error-color);
  background: var(--n-color-embedded);
}

.device-card--inuse {
  border-color: var(--n-success-color);
  background: var(--n-color-embedded);
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  z-index: 1;
}

.status-indicator--active {
  background: var(--n-success-color);
  box-shadow: 0 0 0 4px var(--n-success-color-hover);
}

.status-indicator--inactive {
  background: var(--n-border-color);
  box-shadow: 0 0 0 4px var(--n-border-color-hover);
  animation: none;
}

.status-indicator--maintenance {
  background: var(--n-warning-color);
  box-shadow: 0 0 0 4px var(--n-warning-color-hover);
}

.status-indicator--locked {
  background: var(--n-error-color);
  box-shadow: 0 0 0 4px var(--n-error-color-hover);
}

.status-indicator--inuse {
  background: var(--n-success-color);
  box-shadow: 0 0 0 4px var(--n-success-color-hover);
}

/* 设备头部信息 */
.device-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
  padding-right: 30px;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.device-type-icon {
  color: var(--n-primary-color);
  flex-shrink: 0;
  margin-top: 3px;
}

.device-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0;
  line-height: 1.5;
  flex: 1;
  min-width: 0;
  letter-spacing: 0.3px;
  /* 限制显示长度 */
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-id {
  font-size: 13px;
  color: var(--n-secondary-text-color);
  margin: 0;
  padding-left: 28px;
  font-family: 'Monaco', 'Menlo', monospace;
  word-break: break-all;
  opacity: 0.85;
}

.device-type-status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 28px;
  flex-wrap: wrap;
}

.device-type-tag {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-status-tag {
  flex-shrink: 0;
}

/* 监控数据 */
.monitoring-data {
  margin-bottom: 16px;
  flex: 1;
}

.data-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
  font-size: 13px;
  gap: 6px;
}

.data-row:last-child {
  margin-bottom: 0;
}

.data-label {
  color: var(--n-secondary-text-color);
  min-width: 90px;
  font-weight: 500;
  flex-shrink: 0;
}

.data-value {
  color: var(--n-text-color);
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', monospace;
  flex: 1;
  min-width: 0;
  /* 限制显示长度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 设备位置 */
.device-location {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
}

/* 设备操作 */
.device-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 12px;
  margin-top: auto;
  border-top: 1px solid var(--n-divider-color);
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
}

@media (max-width: 768px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
    padding: 16px 0;
  }

  .device-card {
    padding: 16px;
    min-height: 260px;
  }

  .device-name {
    font-size: 15px;
  }

  .data-row {
    font-size: 12px;
  }

  .data-label {
    min-width: 85px;
  }
}

@media (max-width: 480px) {
  .device-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .device-card {
    min-height: auto;
  }

  .device-header {
    padding-right: 25px;
  }

  .device-id {
    padding-left: 30px;
  }

  .device-type-status-row {
    padding-left: 30px;
  }

  .data-label {
    min-width: 80px;
    font-size: 12px;
  }

  .data-value {
    font-size: 12px;
  }

  .device-actions {
    gap: 6px;
  }
}
</style>
