<template>
  <CommonPage
    show-footer
    title="维修记录管理"
    class="repair-records-page"
    :class="getResponsiveClasses()"
    :style="getContainerStyle()"
  >
    <template #action>
      <div class="w-full flex items-center justify-between">
        <div class="flex items-center gap-2">
          <PermissionButton
            permission="POST /api/v2/device/maintenance/repair-records"
            type="primary"
            no-permission-text="您没有权限创建维修记录"
            @click="handleAdd"
          >
            <TheIcon icon="material-symbols:add" :size="16" class="mr-1" />
            新建维修记录
          </PermissionButton>
          <PermissionButton
            permission="GET /api/v2/device/maintenance/repair-records/export"
            :loading="exporting"
            no-permission-text="您没有权限导出维修记录数据"
            @click="handleExportClick"
          >
            <TheIcon icon="material-symbols:download" :size="16" class="mr-1" />
            导出数据
          </PermissionButton>
        </div>
      </div>
    </template>

    <!-- 搜索栏 -->
    <RepairRecordSearchBar
      :model-value="queryItems"
      :brand-options="brandOptions"
      :category-options="categoryOptions"
      :fault-status-options="faultStatusOptions"
      :fault-reason-options="faultReasonOptions"
      :damage-category-options="damageCategoryOptions"
      @update:model-value="(val) => Object.assign(queryItems, val)"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 表格容器 -->
    <div class="table-container">
      <PermissionDataWrapper
        :data="tableData"
        :loading="loading"
        permission="GET /api/v2/device/maintenance/repair-records"
        permission-name="维修记录查看"
        empty-title="暂无维修记录"
        empty-description="当前没有维修记录数据，您可以点击上方的【新建维修记录】按钮来创建第一条记录"
        loading-text="正在加载维修记录数据..."
        @refresh="loadTableData"
        @contact="handleContactAdmin"
        @create="handleAdd"
      >
        <template #default="{ data }">
          <RepairRecordTable
            :data="data"
            :loading="loading"
            :pagination="pagination"
            @edit="handleEdit"
            @delete="handleDelete"
            @refresh="loadTableData"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />

          <!-- 分页组件 -->
          <div v-if="data.length > 0" class="mt-6 flex justify-center">
            <NPagination
              v-model:page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :item-count="pagination.itemCount"
              :page-sizes="pagination.pageSizes"
              :show-size-picker="pagination.showSizePicker"
              :show-quick-jumper="pagination.showQuickJumper"
              :prefix="(info) => `共 ${info.itemCount} 条`"
              :suffix="(info) => `显示 ${info.startIndex}-${info.endIndex} 条`"
              @update:page="handlePageChange"
              @update:page-size="handlePageSizeChange"
            />
          </div>
        </template>
      </PermissionDataWrapper>
    </div>

    <!-- 新增/编辑弹窗 -->
    <NModal
      v-model:show="modalVisible"
      :title="modalTitle"
      preset="card"
      :style="{ width: formConfig.modal.width, maxWidth: formConfig.modal.maxWidth }"
      :mask-closable="false"
      @update:show="handleModalVisibilityChange"
    >
      <RepairRecordForm
        ref="repairFormRef"
        v-model="modalForm"
        :loading="modalLoading"
        :record-id="currentEditRecord"
        :original-data="originalRecordData"
        @cache-loaded="handleCacheLoaded"
      />

      <template #footer>
        <div class="flex justify-end gap-2">
          <NButton @click="handleModalClose">取消</NButton>
          <PermissionButton
            :permission="
              modalForm.id
                ? 'PUT /api/v2/device/maintenance/repair-records/{id}'
                : 'POST /api/v2/device/maintenance/repair-records'
            "
            type="primary"
            :loading="modalLoading"
            :hide-when-no-permission="false"
            :disable-when-no-permission="true"
            :no-permission-text="modalForm.id ? '您没有权限编辑维修记录' : '您没有权限创建维修记录'"
            @click="handleSave"
          >
            保存
          </PermissionButton>
        </div>
      </template>
    </NModal>

    <!-- 加载反馈组件 -->
    <LoadingFeedback
      ref="loadingFeedbackRef"
      :global-loading="loading"
      :loading-text="loadingText"
      :show-progress="showProgress"
      :progress="loadingProgress"
    />
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, reactive, h, onMounted } from 'vue'
import { NButton, NModal, NDropdown, NPagination, useMessage } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import RepairRecordForm from './components/RepairRecordForm.vue'
import RepairRecordTable from './components/RepairRecordTable.vue'
import RepairRecordSearchBar from '@/components/query-bar/RepairRecordSearchBar.vue'
import LoadingFeedback from './components/LoadingFeedback.vue'
import { PermissionDataWrapper, PermissionButton } from '@/components/Permission'
import { useDataExport } from './composables/useDataExport.js'
import { useResponsiveLayout } from './composables/useResponsiveLayout.js'
import { useRepairDictOptions } from './composables/useRepairDictOptions'

const message = useMessage()
const { exportToExcel, exportToCSV, exportToPDF, exportTemplate, exporting } = useDataExport()
const { formConfig, getResponsiveClasses, getContainerStyle } = useResponsiveLayout()

// 加载反馈
const loadingFeedbackRef = ref(null)

// 数据状态
const tableData = ref([])
const loading = ref(false)
const loadingText = ref('加载中...')
const showProgress = ref(false)
const loadingProgress = ref(0)

// 查询参数
const queryItems = reactive({
  device_number: '',
  applicant: '',
  brand: '',
  is_fault: null,
  repair_date_range: null,
  company: '',
  department: '',
  workshop: '',
  category: '',
  fault_reason: '',
  damage_category: '',
  repairer: '',
  construction_unit: '',
  phone: '',
})

// 选项数据 - 使用字典数据
const {
  categoryOptions,
  brandOptions,
  faultReasonOptions,
  damageCategoryOptions,
  loading: dictLoading,
} = useRepairDictOptions({ withAllOption: true })

// 故障状态选项（固定值，不需要字典）
const faultStatusOptions = ref([
  { label: '全部状态', value: null },
  { label: '故障', value: true },
  { label: '正常维护', value: false },
])

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [20, 50, 100, 200],
  showQuickJumper: true,
})

// 分页处理
const handlePageChange = (page) => {
  pagination.value.page = page
  loadTableData()
}

const handlePageSizeChange = (pageSize) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadTableData()
}

// 模态框状态
const modalVisible = ref(false)
const modalLoading = ref(false)
const modalTitle = ref('')
const repairFormRef = ref(null)

// 表单数据 - 现在由表单组件的缓存系统管理
const modalForm = reactive({
  repair_date: null,
  category: '',
  device_number: '',
  brand: '',
  model: '',
  pin_type: '',
  company: '',
  department: '',
  workshop: '',
  construction_unit: '',
  applicant: '',
  phone: '',
  is_fault: true,
  fault_reason: '',
  damage_category: '',
  fault_content: '',
  fault_location: '',
  repair_content: '',
  parts_name: '',
  repairer: '',
  repair_completion_date: null,
  remarks: '',
})

// 缓存加载处理
const handleCacheLoaded = (cacheInfo) => {
  console.log('[RepairRecords] 表单缓存已加载:', cacheInfo)

  // 更新modalForm以保持数据同步
  Object.assign(modalForm, cacheInfo.formData)

  // 只有真正有缓存且有变化时才显示提示
  if (cacheInfo.hasCache && cacheInfo.hasRealChanges) {
    const recordName = cacheInfo.recordId === 'new' ? '新建记录' : `记录 ${cacheInfo.recordId}`
    message.info(`已恢复编辑状态`)
    //    message.info(`已恢复${recordName}的编辑状态`)
    console.log(`[RepairRecords] 显示缓存恢复提示: ${recordName}`)
  } else {
    console.log(`[RepairRecords] 跳过缓存提示`, {
      hasCache: cacheInfo.hasCache,
      hasRealChanges: cacheInfo.hasRealChanges,
      recordId: cacheInfo.recordId,
    })
  }
}

// 方法
const handleSearch = (searchParams = null) => {
  if (searchParams) {
    Object.assign(queryItems, searchParams)
  }
  pagination.value.page = 1
  loadTableData()
}

const handleReset = () => {
  Object.assign(queryItems, {
    device_number: '',
    applicant: '',
    brand: '',
    is_fault: null,
    repair_date_range: null,
    company: '',
    department: '',
    workshop: '',
    category: '',
    fault_reason: '',
    damage_category: '',
    repairer: '',
    construction_unit: '',
    phone: '',
  })
  loadTableData()
}

const handleAdd = () => {
  console.log('[RepairRecords] 新建记录')

  modalTitle.value = '新建维修记录'

  // 设置为新建模式
  currentEditRecord.value = 'new'
  originalRecordData.value = null

  // 不再直接重置modalForm，让表单组件管理

  modalVisible.value = true
}

// 当前编辑的记录信息
const currentEditRecord = ref(null)
const originalRecordData = ref(null)

const handleEdit = (row) => {
  console.log('[RepairRecords] 编辑记录:', row.id)

  modalTitle.value = '编辑维修记录'

  // 设置当前编辑记录信息
  currentEditRecord.value = row.id
  originalRecordData.value = { ...row }

  // 不再直接赋值给modalForm，让表单组件通过缓存系统管理
  // Object.assign(modalForm, { ...row })

  modalVisible.value = true
}

const handleDelete = async (rowOrIds) => {
  try {
    loading.value = true
    loadingText.value = '正在删除维修记录...'

    // ✅ Shared API 迁移 (2025-10-25)
    const { repairApi: repairRecordsApi } = await import('@/api/repair-shared')

    // 处理不同类型的参数
    let idList = []
    if (Array.isArray(rowOrIds)) {
      // 如果是数组，可能是ID数组或row对象数组
      idList = rowOrIds.map((item) => (typeof item === 'object' ? item.id : item))
    } else if (typeof rowOrIds === 'object' && rowOrIds.id) {
      // 如果是单个row对象
      idList = [rowOrIds.id]
    } else {
      // 如果是单个ID
      idList = [rowOrIds]
    }

    console.log('准备删除的ID列表:', idList)

    let response
    if (idList.length > 1) {
      // 批量删除
      response = await repairRecordsApi.batchDelete(idList)
    } else {
      // 单个删除
      response = await repairRecordsApi.delete(idList[0])
    }

    console.log('删除维修记录API响应:', response)

    if (response && response.success) {
      message.success(`成功删除 ${idList.length} 条维修记录`)
      loadTableData() // 重新加载数据
    } else {
      throw new Error(response?.data?.message || response?.message || '删除失败')
    }
  } catch (error) {
    console.error('删除维修记录失败:', error)
    message.error(`删除失败: ${error.message || '请稍后重试'}`)
  } finally {
    loading.value = false
  }
}

// 导出选项
const exportOptions = [
  {
    label: '导出Excel',
    key: 'excel',
    icon: () => h(TheIcon, { icon: 'material-symbols:table-chart' }),
  },
  {
    label: '导出CSV',
    key: 'csv',
    icon: () => h(TheIcon, { icon: 'material-symbols:description' }),
  },
  {
    label: '导出PDF',
    key: 'pdf',
    icon: () => h(TheIcon, { icon: 'material-symbols:picture-as-pdf' }),
  },
  {
    type: 'divider',
  },
  {
    label: '下载Excel模板',
    key: 'template-excel',
    icon: () => h(TheIcon, { icon: 'material-symbols:download-for-offline' }),
  },
  {
    label: '下载CSV模板',
    key: 'template-csv',
    icon: () => h(TheIcon, { icon: 'material-symbols:download-for-offline' }),
  },
]

// 导出按钮点击处理 - 默认导出Excel
const handleExportClick = async () => {
  try {
    if (tableData.value.length === 0) {
      message.warning('没有数据可导出')
      return
    }

    // 默认导出Excel格式
    await exportToExcel(tableData.value, '维修记录')
  } catch (error) {
    console.error('Export failed:', error)
    loadingFeedbackRef.value?.showError('导出失败，请稍后重试')
  }
}

const handleExportSelect = async (key) => {
  try {
    if (key.startsWith('template-')) {
      // 模板下载不需要检查数据
      switch (key) {
        case 'template-excel':
          await exportTemplate('excel')
          break
        case 'template-csv':
          await exportTemplate('csv')
          break
        default:
          message.warning('未知的模板类型')
      }
      return
    }

    if (tableData.value.length === 0) {
      message.warning('没有数据可导出')
      return
    }

    switch (key) {
      case 'excel':
        await exportToExcel(tableData.value, '维修记录')
        break
      case 'csv':
        await exportToCSV(tableData.value, '维修记录')
        break
      case 'pdf':
        await exportToPDF(tableData.value, '维修记录')
        break
      default:
        message.warning('未知的导出类型')
    }
  } catch (error) {
    console.error('Export failed:', error)
    loadingFeedbackRef.value?.showError('导出失败，请稍后重试')
  }
}

const handleSave = async () => {
  try {
    const isValid = await repairFormRef.value?.validate()
    if (!isValid) return

    modalLoading.value = true
    loadingText.value = '正在保存维修记录...'
    showProgress.value = true

    // ✅ Shared API 迁移 (2025-10-25)
    const { repairApi: repairRecordsApi } = await import('@/api/repair-shared')

    loadingProgress.value = 20

    // 准备保存数据，转换为后端格式
    const saveData = {
      device_id: modalForm.device_id || null, // 需要通过设备编号获取设备ID
      device_type: modalForm.category,
      repair_date: modalForm.repair_date
        ? typeof modalForm.repair_date === 'number'
          ? new Date(modalForm.repair_date).toISOString().split('T')[0]
          : new Date(modalForm.repair_date).toISOString().split('T')[0]
        : null,
      repair_status: 'pending', // 默认状态
      priority: 'medium', // 默认优先级
      applicant: modalForm.applicant,
      applicant_phone: modalForm.phone,
      applicant_dept: modalForm.department,
      applicant_workshop: modalForm.workshop,
      construction_unit: modalForm.construction_unit,
      is_fault: modalForm.is_fault,
      fault_reason: modalForm.fault_reason,
      fault_content: modalForm.fault_content,
      fault_location: modalForm.fault_location,
      repair_content: modalForm.repair_content,
      parts_name: modalForm.parts_name,
      repairer: modalForm.repairer,
      repair_completion_date: modalForm.repair_completion_date
        ? typeof modalForm.repair_completion_date === 'number'
          ? new Date(modalForm.repair_completion_date).toISOString().split('T')[0]
          : new Date(modalForm.repair_completion_date).toISOString().split('T')[0]
        : null,
      repair_cost: 0, // 默认费用
      remarks: modalForm.remarks,
      frontend_specific_data: {
        device_number: modalForm.device_number,
        brand: modalForm.brand,
        model: modalForm.model,
        pin_type: modalForm.pin_type,
        company: modalForm.company,
        application_department: modalForm.department,
        workshop: modalForm.workshop,
        damage_category: modalForm.damage_category,
      },
    }

    loadingProgress.value = 40

    // 如果有设备编号但没有设备ID，先获取设备ID
    if (modalForm.device_number && !saveData.device_id) {
      try {
        // ✅ Shared API 迁移
        const { deviceApi: deviceV2Api } = await import('@/api/device-shared')
        const deviceResponse = await deviceV2Api.list({
          device_code: modalForm.device_number,
          page: 1,
          page_size: 1,
        })

        if (
          deviceResponse &&
          deviceResponse.success &&
          deviceResponse.data &&
          deviceResponse.data.success
        ) {
          const data = deviceResponse.data.data
          const devices = Array.isArray(data) ? data : (data && data.items) || []
          if (devices.length > 0) {
            saveData.device_id = devices[0].id
          }
        }
      } catch (error) {
        console.warn('获取设备ID失败:', error)
      }
    }

    loadingProgress.value = 60

    let response
    if (modalForm.id) {
      // 更新现有记录
      response = await repairRecordsApi.update(modalForm.id, saveData)
    } else {
      // 创建新记录
      response = await repairRecordsApi.create(saveData)
    }

    loadingProgress.value = 80

    console.log('保存维修记录API响应:', response)

    if (response && response.success) {
      loadingProgress.value = 100
      loadingFeedbackRef.value?.showSuccess(modalForm.id ? '维修记录更新成功' : '维修记录创建成功')
      modalVisible.value = false
      loadTableData() // 重新加载数据
    } else {
      throw new Error(response?.data?.message || response?.message || '保存失败')
    }
  } catch (error) {
    console.error('保存维修记录失败:', error)
    loadingFeedbackRef.value?.showError(`保存失败: ${error.message || '请稍后重试'}`)
  } finally {
    modalLoading.value = false
    showProgress.value = false
    loadingProgress.value = 0
  }
}

const loadTableData = async () => {
  loading.value = true
  loadingText.value = '正在加载维修记录数据...'

  try {
    showProgress.value = true
    loadingProgress.value = 20

    // ✅ Shared API 迁移 (2025-10-25)
    const { repairApi: repairRecordsApi } = await import('@/api/repair-shared')

    loadingProgress.value = 40

    // 构建查询参数
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      ...queryItems,
    }

    // 处理日期范围参数
    if (queryItems.repair_date_range && queryItems.repair_date_range.length === 2) {
      params.start_date = new Date(queryItems.repair_date_range[0]).toISOString().split('T')[0]
      params.end_date = new Date(queryItems.repair_date_range[1]).toISOString().split('T')[0]
      delete params.repair_date_range
    }

    // 清理空值参数
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    loadingProgress.value = 60

    // 调用API获取维修记录
    console.log('调用维修记录API，参数:', params)
    const response = await repairRecordsApi.list(params)

    loadingProgress.value = 80

    console.log('=== 维修记录API调试信息 ===')
    console.log('原始响应:', response)
    console.log('响应类型:', typeof response)
    console.log('响应结构:', Object.keys(response || {}))
    console.log('response.success:', response?.success)
    console.log('response.data类型:', typeof response?.data)
    console.log('response.data内容:', response?.data)
    console.log('response.meta:', response?.meta)
    console.log('=== 调试信息结束 ===')

    if (response && response.success) {
      // ResponseAdapter已经处理了响应格式，直接使用data字段
      // 注意：后端返回 {data: {records: [], pagination: {}}, meta: {}}
      const records = response.data?.records || response.data || []
      const pagination_info = response.data?.pagination || response.meta || {}

      console.log('处理后的记录数据:', records)
      console.log('分页信息:', pagination_info)

      // 处理维修记录数据，确保前端显示格式正确
      tableData.value = Array.isArray(records)
        ? records.map((record) => ({
            id: record.id,
            repair_date: record.repair_date,
            category: record.device_type || '',
            device_number: record.device_code || '',
            brand: record.frontend_specific_data?.brand || '',
            model: record.frontend_specific_data?.model || '',
            pin_type: record.frontend_specific_data?.pin_type || '',
            company: record.frontend_specific_data?.company || '',
            department: record.frontend_specific_data?.application_department || '',
            workshop: record.frontend_specific_data?.workshop || '',
            construction_unit: record.frontend_specific_data?.construction_unit || '',
            applicant: record.applicant,
            phone: record.applicant_phone || '',
            is_fault: record.is_fault,
            fault_reason: record.fault_reason || '',
            damage_category: record.frontend_specific_data?.damage_category || '',
            fault_content: record.fault_content || '',
            fault_location: record.fault_location || '',
            repair_content: record.repair_content || '',
            parts_name: record.parts_name || '',
            repairer: record.repairer || '',
            repair_completion_date: record.repair_completion_date,
            remarks: record.remarks || '',
          }))
        : []

      // 更新分页信息
      pagination.value.itemCount =
        pagination_info.total || (Array.isArray(records) ? records.length : 0)

      loadingProgress.value = 100

      // 显示加载完成反馈
      if (tableData.value.length > 0) {
        loadingFeedbackRef.value?.showSuccess(`成功加载 ${tableData.value.length} 条维修记录`)
      } else {
        message.info('暂无维修记录数据')
      }
    } else {
      throw new Error(response?.message || response?.msg || '获取维修记录失败')
    }
  } catch (error) {
    console.error('加载维修记录失败:', error)
    loadingFeedbackRef.value?.showError(`加载数据失败: ${error.message || '请稍后重试'}`)
    tableData.value = []
    pagination.value.itemCount = 0
  } finally {
    loading.value = false
    showProgress.value = false
    loadingProgress.value = 0
  }
}

// 模态框关闭处理
const handleModalClose = () => {
  // 保存当前表单状态到缓存
  if (repairFormRef.value && currentEditRecord.value) {
    repairFormRef.value.saveToCache()
    console.log(`[RepairRecords] 关闭表单前保存缓存: ${currentEditRecord.value}`)
  }

  modalVisible.value = false
}

const handleModalVisibilityChange = (visible) => {
  if (!visible) {
    // 模态框关闭时的清理工作
    setTimeout(() => {
      currentEditRecord.value = null
      originalRecordData.value = null
    }, 300) // 延迟清理，确保动画完成
  }
}

// 权限相关处理
const handleContactAdmin = () => {
  message.info('请联系系统管理员获取维修记录查看权限')
}

// 生命周期
onMounted(() => {
  loadTableData()
})
</script>

<style scoped>
/* 表格容器样式 */
.table-container {
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

/* 响应式布局 */
.repair-records-page.is-mobile {
  padding: 8px;
}

.repair-records-page.is-mobile :deep(.n-card) {
  margin-bottom: 8px;
}

.repair-records-page.is-tablet {
  padding: 12px;
}

.repair-records-page.is-desktop {
  padding: 16px;
}

/* 移动端优化 */
@media (max-width: 768px) {
  /* 分页器在移动端的优化 */
  :deep(.n-pagination) {
    justify-content: center;
  }

  :deep(.n-pagination-item) {
    min-width: 32px;
    height: 32px;
  }
}

/* 表格样式优化 - 参考设备信息管理 */
:deep(.n-data-table) {
  border-radius: 6px;
}

:deep(.n-data-table-th) {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e6;
  text-align: center;
}

:deep(.n-data-table-td) {
  border-bottom: 1px solid #f0f0f0;
  text-align: center;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background-color: #f8f9fa;
}

/* 分页样式 */
:deep(.n-pagination) {
  padding: 16px;
  border-top: 1px solid #e0e0e6;
  background-color: #fafafa;
}

/* 加载状态优化 */
.repair-records-page :deep(.n-spin-container) {
  min-height: 200px;
}

/* 模态框响应式 */
.is-mobile :deep(.n-modal) {
  margin: 16px;
}

.is-mobile :deep(.n-card) {
  border-radius: 8px;
}

/* 触摸设备优化 */
@media (hover: none) and (pointer: coarse) {
  :deep(.n-button) {
    min-height: 44px;
    padding: 0 16px;
  }

  :deep(.n-input) {
    min-height: 44px;
  }

  :deep(.n-select) {
    min-height: 44px;
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  :deep(.n-data-table-th) {
    background-color: #000;
    color: #fff;
    border: 2px solid #fff;
  }

  :deep(.n-data-table-td) {
    border: 1px solid #000;
  }
}

/* 减少动画模式支持 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
