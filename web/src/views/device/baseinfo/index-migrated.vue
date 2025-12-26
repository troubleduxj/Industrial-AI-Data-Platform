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
import { useRouter } from 'vue-router'

// ========== 🎯 迁移到 Shared API ==========
// 旧方式：import api, { deviceTypeApi } from '@/api'
// 旧方式：import deviceV2Api from '@/api/device-v2'
// 新方式：使用 Shared API 适配器
import { deviceApi, deviceTypeApi } from '@/api/device-shared'
// 或者使用统一导出：import api from '@/api/index-shared'
// ========================================

defineOptions({ name: '设备基础信息（Shared层迁移版）' })

const $table = ref(null)
const queryItems = ref({
  device_type: 'welding', // 默认选择焊机
})
const vPermission = resolveDirective('permission')
const message = useMessage()
const router = useRouter()

// 设备类型数据
const deviceTypes = ref([])

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
const handleEdit = (row) => {
  modalAction.value = 'edit'
  modalTitle.value = '编辑设备'
  modalForm.value = { ...row }
  modalVisible.value = true
}

// ========== 🎯 迁移改动：使用 Shared API ==========
// 处理删除设备
const handleDelete = async (ids) => {
  try {
    const idList = Array.isArray(ids) ? ids : [ids]

    // 新方式：使用 deviceApi（来自 device-shared.js）
    if (idList.length > 1) {
      await deviceApi.batchDelete(idList)
    } else {
      await deviceApi.delete(idList[0])
    }

    window.$message?.success('删除设备成功')
    getDevices() // 统一刷新
  } catch (error) {
    console.error('删除设备失败:', error)
    window.$message?.error(`删除设备失败: ${error.message || '未知错误'}`)
  }
}
// ==========================================

// 跳转到设备维修记录
const handleViewRepairRecords = (device) => {
  router.push({
    path: '/device-maintenance/repair-records',
    query: {
      device_id: device.id,
      device_name: device.device_name,
      device_code: device.device_code,
    },
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

// ========== 🎯 迁移改动：使用 Shared API ==========
// 处理保存设备
const handleSave = async () => {
  try {
    await modalFormRef.value?.validate()
    modalLoading.value = true

    // 新方式：使用 deviceApi（来自 device-shared.js）
    if (modalAction.value === 'add') {
      await deviceApi.create(modalForm.value)
      window.$message?.success('新建设备成功')
    } else {
      await deviceApi.update(modalForm.value.id, modalForm.value)
      window.$message?.success('编辑设备成功')
    }

    modalVisible.value = false
    getDevices() // 统一刷新
  } catch (error) {
    console.error('保存设备失败:', error)
    window.$message?.error(`保存设备失败: ${error.message || '未知错误'}`)
  } finally {
    modalLoading.value = false
  }
}
// ==========================================

// ========== 🎯 迁移改动：使用 Shared API ==========
// 统一获取数据
const getDevices = async () => {
  loading.value = true
  const params = {
    ...queryItems.value,
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  }

  try {
    // 新方式：使用 deviceApi.list()（来自 device-shared.js）
    const response = await deviceApi.list(params)
    console.log('✅ Shared API 响应数据:', response)

    if (response && response.data) {
      const dataItems = Array.isArray(response.data) ? response.data : response.data.items || []

      if (Array.isArray(dataItems)) {
        tableData.value = dataItems
        cardData.value = dataItems

        // 从API响应中正确获取总记录数
        pagination.value.itemCount =
          response.total || response.meta?.total || response.data.total || dataItems.length

        console.log('✅ 设备数据加载成功:', {
          count: dataItems.length,
          total: pagination.value.itemCount,
          page: pagination.value.page,
        })
      } else {
        console.error('❌ 数据格式错误:', response.data)
        tableData.value = []
        cardData.value = []
        pagination.value.itemCount = 0
        window.$message?.error('数据格式错误')
      }
    } else {
      console.error('❌ API响应为空')
      tableData.value = []
      cardData.value = []
      pagination.value.itemCount = 0
    }
  } catch (error) {
    console.error('❌ 获取设备列表失败:', error)
    window.$message?.error(`获取设备列表失败: ${error.message || '未知错误'}`)
    tableData.value = []
    cardData.value = []
    pagination.value.itemCount = 0
  } finally {
    loading.value = false
  }
}
// ==========================================

// ========== 🎯 迁移改动：使用 Shared API ==========
// 获取设备类型列表
const getDeviceTypes = async () => {
  try {
    // 新方式：使用 deviceTypeApi（来自 device-shared.js）
    const response = await deviceTypeApi.list()
    console.log('✅ 设备类型 API 响应:', response)

    if (response && response.data) {
      const items = Array.isArray(response.data) ? response.data : response.data.items || []
      deviceTypes.value = items.map((item) => ({
        label: item.type_name,
        value: item.type_code,
      }))
      console.log('✅ 设备类型加载成功:', deviceTypes.value.length, '个类型')
    }
  } catch (error) {
    console.error('❌ 获取设备类型失败:', error)
    window.$message?.error('获取设备类型失败')
  }
}
// ==========================================

// 处理查询
const handleQuery = (params) => {
  queryItems.value = { ...params }
  pagination.value.page = 1
  getDevices()
}

// 处理重置
const handleReset = () => {
  queryItems.value = {
    device_type: 'welding',
  }
  pagination.value.page = 1
  getDevices()
}

// 处理分页改变
const handlePageChange = (page) => {
  pagination.value.page = page
  getDevices()
}

// 处理每页大小改变
const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  getDevices()
}

// 组件挂载时加载数据
onMounted(() => {
  getDevices()
  getDeviceTypes()

  console.log('🎯 页面使用 Shared API 层，支持跨端复用')
})
</script>

<template>
  <CommonPage :title="`设备基础信息 ${viewMode === 'card' ? '(卡片视图)' : '(表格视图)'}`">
    <template #action>
      <n-space>
        <ViewToggle v-model:value="viewMode" :options="viewOptions" />
        <PermissionButton type="primary" permission="device:create" @click="handleAdd">
          <template #icon>
            <TheIcon icon="material-symbols:add" />
          </template>
          新建设备
        </PermissionButton>
      </n-space>
    </template>

    <!-- 搜索栏 -->
    <DeviceInfoSearchBar :device-types="deviceTypes" @query="handleQuery" @reset="handleReset" />

    <!-- 表格视图 -->
    <CrudTable
      v-if="viewMode === 'table'"
      ref="$table"
      v-model:query-items="queryItems"
      :loading="loading"
      :columns="tableColumns"
      :data="tableData"
      :pagination="pagination"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    />

    <!-- 卡片视图 -->
    <div v-else class="device-grid">
      <div
        v-for="device in cardData"
        :key="device.id"
        :class="getDeviceCardClass(device.is_locked)"
      >
        <div class="device-card__header">
          <div class="device-name">{{ device.device_name }}</div>
          <n-tag :type="getStatusTagType(device.is_locked)" size="small">
            {{ getStatusText(device.is_locked) }}
          </n-tag>
        </div>

        <div class="device-card__body">
          <div class="device-info">
            <span class="label">设备编码：</span>
            <span class="value">{{ device.device_code }}</span>
          </div>
          <div class="device-info">
            <span class="label">设备类型：</span>
            <span class="value">{{ device.device_type }}</span>
          </div>
          <div class="device-info">
            <span class="label">设备型号：</span>
            <span class="value">{{ device.device_model || '-' }}</span>
          </div>
          <div class="device-info">
            <span class="label">制造商：</span>
            <span class="value">{{ device.manufacturer || '-' }}</span>
          </div>
        </div>

        <div class="device-card__footer">
          <n-space>
            <PermissionButton size="small" permission="device:update" @click="handleEdit(device)">
              编辑
            </PermissionButton>
            <PermissionButton size="small" type="info" @click="handleViewRepairRecords(device)">
              维修记录
            </PermissionButton>
            <PermissionButton
              size="small"
              type="error"
              permission="device:delete"
              confirm-message="确定删除该设备吗？"
              @confirm="handleDelete(device.id)"
            >
              删除
            </PermissionButton>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="viewMode === 'card'" class="pagination-container">
      <n-pagination
        v-model:page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :item-count="pagination.itemCount"
        :page-sizes="pagination.pageSizes"
        :show-size-picker="pagination.showSizePicker"
        :show-quick-jumper="pagination.showQuickJumper"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      >
        <template #prefix="{ itemCount }">
          {{ pagination.prefix({ itemCount }) }}
        </template>
        <template #suffix="{ startIndex, endIndex }">
          {{ pagination.suffix({ startIndex, endIndex }) }}
        </template>
      </n-pagination>
    </div>

    <!-- 新建/编辑模态框 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @confirm="handleSave"
    >
      <n-form
        ref="modalFormRef"
        :model="modalForm"
        label-placement="left"
        label-width="100px"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="设备名称" path="device_name" required>
          <n-input v-model:value="modalForm.device_name" placeholder="请输入设备名称" />
        </n-form-item>

        <n-form-item label="设备编码" path="device_code" required>
          <n-input v-model:value="modalForm.device_code" placeholder="请输入设备编码" />
        </n-form-item>

        <n-form-item label="设备类型" path="device_type" required>
          <n-select
            v-model:value="modalForm.device_type"
            :options="deviceTypes"
            placeholder="请选择设备类型"
          />
        </n-form-item>

        <n-form-item label="设备型号" path="device_model">
          <n-input v-model:value="modalForm.device_model" placeholder="请输入设备型号" />
        </n-form-item>

        <n-form-item label="制造商" path="manufacturer">
          <n-input v-model:value="modalForm.manufacturer" placeholder="请输入制造商" />
        </n-form-item>

        <n-form-item label="在线地址" path="online_address">
          <n-input v-model:value="modalForm.online_address" placeholder="请输入设备在线地址" />
        </n-form-item>
      </n-form>
    </CrudModal>

    <!-- 迁移标记 -->
    <div class="migration-badge">
      <n-tag type="success" size="small"> ✅ 已迁移到 Shared API </n-tag>
    </div>
  </CommonPage>
</template>

<style scoped>
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.device-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s;
}

.device-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.device-card--inuse {
  border-left: 4px solid #18a058;
}

.device-card--locked {
  border-left: 4px solid #d03050;
}

.device-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.device-card__body {
  margin-bottom: 12px;
}

.device-info {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.device-info .label {
  color: #666;
  margin-right: 8px;
  min-width: 80px;
}

.device-info .value {
  color: #333;
  flex: 1;
}

.device-card__footer {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.migration-badge {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 999;
}
</style>
