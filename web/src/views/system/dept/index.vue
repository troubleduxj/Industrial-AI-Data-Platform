<script setup lang="ts">
import { h, onMounted, ref, resolveDirective, withDirectives, onActivated, computed } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NTreeSelect,
  NProgress,
  NModal,
  NCard,
  NList,
  NListItem,
  NTag,
  NSpace,
  NAlert,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import BatchDeleteButton from '@/components/common/BatchDeleteButton.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useDepartmentBatchDelete } from '@/composables/useBatchDelete'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'
import systemV2Api from '@/api/system-v2'

defineOptions({ name: '部门管理' })

const $table = ref<any>(null)
const queryItems = ref<Record<string, any>>({})
const vPermission = resolveDirective('permission')

// 批量操作相关状态
const selectedRowKeys = ref<(string | number)[]>([])
const expandedRowKeys = ref<(string | number)[]>([]) // 树形表格展开状态
const batchDeleteLoading = ref(false)
const singleDeleteLoading = ref(new Set()) // 存储正在删除的部门ID
const operationStatus = ref({
  isProcessing: false,
  currentStep: '',
  progress: 0,
  processedCount: 0,
  totalCount: 0,
})

// 操作结果状态
const operationResult = ref({
  visible: false,
  type: 'success', // 'success' | 'error' | 'warning'
  title: '',
  message: '',
  details: [],
  autoClose: true,
})

// 分页状态管理
const pagination = ref({
  page: 1,
  pageSize: 10,
})

// 分页事件处理函数
function handlePageChange(page) {
  pagination.value.page = page
}

function handlePageSizeChange(pageSize) {
  pagination.value.page = 1
  pagination.value.pageSize = pageSize
}

// 行选择处理函数
const handleRowSelection = (rowKeys, rows) => {
  // 手动更新 selectedRowKeys，确保与 CrudTable 的选择状态同步
  selectedRowKeys.value = [...rowKeys]
  // 同时更新标准化组合函数的选择状态
  setSelectedItems(rows || [], rowKeys || [])
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '部门',
  initForm: { order: 0 },
  doCreate: systemV2Api.createDept,
  doUpdate: systemV2Api.updateDept,
  doDelete: systemV2Api.deleteDept,
  refresh: () => $table.value?.handleSearch(),
})

// 标准化批量删除组合函数（用于选择状态管理）
const { selectedItems, setSelectedItems, clearSelection } = useDepartmentBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteDepts,
  refresh: () => $table.value?.handleSearch(),
  validateItem: (item) => {
    // 基本验证逻辑，复杂的层级关系检查在自定义函数中处理
    return { valid: true }
  },
})

const deptOption = ref([])
const isDisabled = ref(false)

// 构建部门树形结构
const buildDeptTree = (depts, parentId = 0) => {
  const tree = []
  for (const dept of depts) {
    if (dept.parent_id === parentId) {
      const children = buildDeptTree(depts, dept.id)
      if (children.length > 0) {
        dept.children = children
      }
      tree.push(dept)
    }
  }
  return tree.sort((a, b) => (a.order || 0) - (b.order || 0))
}

// 部门列表数据获取函数（树形显示）
const getDeptListData = async (params) => {
  try {
    console.log('调用部门树形API v2，参数:', params)
    const res = await systemV2Api.getDepts({ view: 'tree' })
    console.log('部门树形API v2原始响应:', res)

    if (res?.success !== false) {
      console.log('部门树形API v2返回数据:', res.data)
      // 处理树形视图的响应格式：{ tree: [...], stats: {...} }
      const rawData = res.data?.tree || res.data || []
      const processedData = rawData.map((item) => ({
        ...item,
        name: item.dept_name || item.name || '',
        desc: item.desc || item.description || '',
        parent_id: item.parent_id || 0,
        order: item.order_num || item.order || 0,
        created_at: item.created_at || new Date().toISOString(),
      }))

      console.log('部门处理后的数据:', processedData)

      // 构建树形结构
      const treeData = buildDeptTree(processedData)
      console.log('部门树形结构:', treeData)

      // 自动展开所有有子部门的父部门
      const getAllParentIds = (data) => {
        const parentIds = []
        const traverse = (nodes) => {
          nodes.forEach((node) => {
            if (node.children && node.children.length > 0) {
              parentIds.push(node.id)
              traverse(node.children)
            }
          })
        }
        traverse(data)
        return parentIds
      }

      // 设置展开状态
      expandedRowKeys.value = getAllParentIds(treeData)
      console.log('自动展开的部门ID:', expandedRowKeys.value)

      // 更新本地表格数据引用，用于批量操作
      tableData.value = processedData

      return {
        data: treeData,
        total: processedData.length,
      }
    }
    return { data: [], total: 0 }
  } catch (err) {
    console.error('部门树形API v2错误:', err)
    $message?.error('获取部门列表失败: ' + (err.message || '未知错误'))
    return { data: [], total: 0 }
  }
}

// 获取部门树形选择数据
const getDeptTreeData = async () => {
  try {
    console.log('获取部门树形选择数据')
    const res = await systemV2Api.getDepts({ page: 1, pageSize: 100 })
    console.log('部门树形数据响应:', res)

    deptOption.value = res.data || []
    console.log('部门树形选择数据处理完成:', deptOption.value)
  } catch (error) {
    console.error('获取部门树形数据失败:', error)
    $message?.error('获取部门数据失败: ' + (error.message || '未知错误'))
    deptOption.value = []
  }
}

onMounted(() => {
  $table.value?.handleSearch()
  getDeptTreeData()
})

onActivated(() => {
  $table.value?.handleSearch()
  getDeptTreeData()
})

const deptRules = {
  name: [
    {
      required: true,
      message: '请输入部门名称',
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

async function addDepts() {
  isDisabled.value = false
  handleAdd()
}

// 批量删除处理函数
async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    $message?.warning('请选择要删除的部门')
    return
  }

  // 在函数开始时定义 validIds，确保在 catch 块中也能访问
  let validIds = []

  try {
    // 开始操作状态
    batchDeleteLoading.value = true
    operationStatus.value = {
      isProcessing: true,
      currentStep: '准备删除操作...',
      progress: 10,
      processedCount: 0,
      totalCount: selectedRowKeys.value.length,
    }

    console.log('批量删除部门，IDs:', selectedRowKeys.value)

    // 验证ID有效性
    operationStatus.value.currentStep = '验证部门ID...'
    operationStatus.value.progress = 20
    await new Promise((resolve) => setTimeout(resolve, 300)) // 让用户看到进度变化

    validIds = selectedRowKeys.value.filter((id) => Number.isInteger(id) && id > 0)
    if (validIds.length !== selectedRowKeys.value.length) {
      console.warn(
        '发现无效的部门ID:',
        selectedRowKeys.value.filter((id) => !Number.isInteger(id) || id <= 0)
      )
      showOperationResult('error', '操作失败', '选择的部门ID无效，请重新选择')
      return
    }

    // 发送删除请求
    operationStatus.value.currentStep = '正在删除部门...'
    operationStatus.value.progress = 50
    await new Promise((resolve) => setTimeout(resolve, 200))

    try {
      const result = await systemV2Api.batchDeleteDepts(validIds, false)
      console.log('批量删除结果:', result)

      // 处理响应
      operationStatus.value.currentStep = '处理删除结果...'
      operationStatus.value.progress = 80
      await new Promise((resolve) => setTimeout(resolve, 200))

      // 处理成功响应
      if (result.success !== false) {
        operationStatus.value.currentStep = '删除完成'
        operationStatus.value.progress = 100
        await new Promise((resolve) => setTimeout(resolve, 300))
        handleBatchDeleteSuccess(result, validIds)
      } else {
        // 处理业务逻辑错误（success: false）
        const errorInfo = parseApiV2Error({ response: { data: result } })
        displayBatchDeleteError(errorInfo, validIds)
      }
    } catch (handledError) {
      console.error('批量删除部门失败:', handledError)

      // 简化错误处理：直接显示子部门提示
      window.$message?.error('删除失败：存在子部门，请先删除子部门后再删除父部门')

      // 清除选择状态
      handleClearSelection()
    }
  } finally {
    // 重置操作状态
    batchDeleteLoading.value = false
    setTimeout(() => {
      operationStatus.value = {
        isProcessing: false,
        currentStep: '',
        progress: 0,
        processedCount: 0,
        totalCount: 0,
      }
    }, 1500) // 延迟重置，让用户看到完成状态
  }
}

// 清空选择
function handleClearSelection() {
  selectedRowKeys.value = []
}

// 单个删除处理函数（与批量删除一致的验证逻辑和错误处理）
async function handleSingleDelete(deptId, deptName, force = false) {
  // 防止重复删除
  if (singleDeleteLoading.value.has(deptId)) {
    return
  }

  try {
    console.log('单个删除部门:', { deptId, deptName, force })

    // 设置加载状态
    singleDeleteLoading.value.add(deptId)

    const result = await systemV2Api.deleteDept({
      dept_id: deptId,
      force: force,
    })
    console.log('单个删除结果:', result)

    // 处理成功响应
    if (result.success !== false) {
      // 显示详细的成功反馈
      const deletionType = result.data?.summary?.deletion_type || (force ? 'permanent' : 'soft')
      const successMessage =
        deletionType === 'permanent' ? `部门"${deptName}"已永久删除` : `部门"${deptName}"已删除`

      showOperationResult(
        'success',
        '删除成功',
        successMessage,
        [
          {
            type: 'success',
            message: `删除类型: ${deletionType === 'permanent' ? '永久删除' : '软删除'}`,
          },
        ],
        true
      )

      $table.value?.handleSearch() // 刷新列表
    } else {
      // 处理业务逻辑错误（success: false）
      const errorInfo = parseApiV2Error({ response: { data: result } })
      displaySingleDeleteError(errorInfo, deptId, deptName)
    }
  } catch (error) {
    console.error('单个删除部门失败:', error)

    // 使用增强的错误处理逻辑
    const errorInfo = parseApiV2Error(error)
    displaySingleDeleteError(errorInfo, deptId, deptName, force)
  } finally {
    // 清除加载状态
    singleDeleteLoading.value.delete(deptId)
  }
}

// 显示单个删除错误信息
function displaySingleDeleteError(errorInfo, deptId, deptName, currentForce = false) {
  console.log('显示单个删除错误:', errorInfo)

  // 检查是否是验证错误（有子部门或用户）
  if (errorInfo.type === 'VALIDATION_ERROR' && errorInfo.details.length > 0) {
    const hasChildren = errorInfo.details.some((d) => d.code === 'HAS_CHILDREN')
    const hasUsers = errorInfo.details.some((d) => d.code === 'HAS_USERS')

    if ((hasChildren || hasUsers) && !currentForce) {
      // 显示确认对话框，询问是否强制删除
      showForceDeleteConfirm(deptId, deptName, errorInfo.details)
      return
    }
  }

  // 显示错误信息
  const details = errorInfo.details.map((detail) => ({
    type: 'error',
    message: detail.message || `${detail.field}: ${detail.code}`,
  }))

  showOperationResult(
    'error',
    '删除失败',
    `部门"${deptName}"删除失败: ${errorInfo.message}`,
    details,
    false
  )
}

// 显示强制删除确认对话框
function showForceDeleteConfirm(deptId, deptName, validationDetails) {
  const issues = validationDetails
    .map((detail) => {
      if (detail.code === 'HAS_CHILDREN') {
        return `• 包含子部门`
      } else if (detail.code === 'HAS_USERS') {
        return `• 包含用户`
      }
      return `• ${detail.message}`
    })
    .join('\n')

  $dialog?.warning({
    title: '删除确认',
    content: `部门"${deptName}"无法删除，原因：\n${issues}\n\n是否强制删除？（这将同时删除所有子部门和用户关联）`,
    positiveText: '强制删除',
    negativeText: '取消',
    onPositiveClick: () => {
      handleSingleDelete(deptId, deptName, true)
    },
  })
}

// 显示操作结果
function showOperationResult(type, title, message, details = [], autoClose = true) {
  operationResult.value = {
    visible: true,
    type,
    title,
    message,
    details: Array.isArray(details) ? details : [],
    autoClose,
  }

  // 自动关闭
  if (autoClose) {
    setTimeout(
      () => {
        operationResult.value.visible = false
      },
      type === 'success' ? 3000 : 5000
    )
  }
}

// 关闭操作结果对话框
function closeOperationResult() {
  operationResult.value.visible = false
}

// 获取详情图标
function getDetailIcon(type) {
  switch (type) {
    case 'success':
      return 'material-symbols:check-circle-outline'
    case 'warning':
      return 'material-symbols:warning-outline'
    case 'error':
      return 'material-symbols:error-outline'
    case 'info':
      return 'material-symbols:info-outline'
    default:
      return 'material-symbols:info-outline'
  }
}

// 获取详情图标样式类
function getDetailIconClass(type) {
  switch (type) {
    case 'success':
      return 'text-green-600'
    case 'warning':
      return 'text-orange-600'
    case 'error':
      return 'text-red-600'
    case 'info':
      return 'text-blue-600'
    default:
      return 'text-gray-600'
  }
}

// 获取选择摘要信息
function getSelectionSummary() {
  if (selectedRowKeys.value.length === 0) return ''

  const maxDisplay = 3
  const names = getSelectedDepartmentNames()

  if (names.length <= maxDisplay) {
    return names.join('、')
  } else {
    return `${names.slice(0, maxDisplay).join('、')} 等${names.length}个`
  }
}

// 获取选中部门的名称列表
function getSelectedDepartmentNames() {
  if (!tableData.value || selectedRowKeys.value.length === 0) return []

  return selectedRowKeys.value
    .map((id) => {
      const dept = tableData.value.find((item) => item.id === id)
      return dept ? dept.name : `部门${id}`
    })
    .filter(Boolean)
}

// 显示强制删除确认对话框
function showForceDeleteConfirmation(attemptedIds, errorMessage, details) {
  const departmentNames = attemptedIds.map((id) => {
    const dept = tableData.value.find((item) => item.id === id)
    return dept ? dept.name : `部门${id}`
  })

  const confirmMessage = `检测到以下部门包含子部门：\n\n${departmentNames.join(
    '、'
  )}\n\n是否要强制删除这些部门及其所有子部门？\n\n⚠️ 警告：强制删除将同时删除所有子部门，此操作不可撤销！`

  $dialog?.warning({
    title: '确认强制删除',
    content: confirmMessage,
    positiveText: '强制删除',
    negativeText: '取消',
    onPositiveClick: () => {
      handleForceDelete(attemptedIds)
    },
    onNegativeClick: () => {
      // 显示原始错误信息
      showOperationResult('error', '批量删除失败', errorMessage, details, false)
    },
  })
}

// 处理强制删除
async function handleForceDelete(deptIds) {
  try {
    batchDeleteLoading.value = true
    operationStatus.value = {
      isProcessing: true,
      currentStep: '正在强制删除部门...',
      progress: 50,
      processedCount: 0,
      totalCount: deptIds.length,
    }

    console.log('强制删除部门，IDs:', deptIds)

    // 调用API进行强制删除
    const result = await systemV2Api.batchDeleteDepts(deptIds, true) // force = true
    console.log('强制删除结果:', result)

    // 处理响应
    operationStatus.value.currentStep = '处理删除结果...'
    operationStatus.value.progress = 80
    await new Promise((resolve) => setTimeout(resolve, 200))

    // 处理成功响应
    if (result.success !== false) {
      operationStatus.value.currentStep = '强制删除完成'
      operationStatus.value.progress = 100
      await new Promise((resolve) => setTimeout(resolve, 300))
      handleBatchDeleteSuccess(result, deptIds)
    } else {
      // 处理业务逻辑错误
      const errorInfo = parseApiV2Error({ response: { data: result } })
      displayBatchDeleteError(errorInfo, deptIds)
    }
  } catch (error) {
    console.error('强制删除部门失败:', error)

    // 使用增强的错误处理逻辑
    const errorInfo = parseApiV2Error(error)
    showOperationResult('error', '强制删除失败', errorInfo.message, [], false)
  } finally {
    // 重置操作状态
    batchDeleteLoading.value = false
    setTimeout(() => {
      operationStatus.value = {
        isProcessing: false,
        currentStep: '',
        progress: 0,
        processedCount: 0,
        totalCount: 0,
      }
    }, 1000)
  }
}

// 表格数据引用（用于获取部门名称）
const tableData = ref([])

// 全选状态计算
const isAllSelected = computed(() => {
  return (
    tableData.value &&
    tableData.value.length > 0 &&
    selectedRowKeys.value.length === tableData.value.length
  )
})

// 切换全选状态
function handleToggleSelectAll() {
  if (!tableData.value || tableData.value.length === 0) return

  if (isAllSelected.value) {
    // 取消全选
    selectedRowKeys.value = []
  } else {
    // 全选
    selectedRowKeys.value = tableData.value.map((item) => item.id)
  }
}

// 解析API v2错误响应
function parseApiV2Error(error) {
  const errorInfo = {
    type: 'UNKNOWN_ERROR',
    message: '批量删除失败',
    details: [],
    validationErrors: {},
    suggestions: [],
  }

  try {
    // 检查是否是网络错误
    if (!error.response) {
      errorInfo.type = 'NETWORK_ERROR'
      errorInfo.message = '网络连接失败，请检查网络连接'
      errorInfo.suggestions.push('请检查网络连接后重试')
      return errorInfo
    }

    const responseData = error.response.data
    if (!responseData) {
      return errorInfo
    }

    // 提取基本错误信息
    errorInfo.message = responseData.message || responseData.msg || '批量删除失败'

    // 处理API v2格式的错误
    if (responseData.error) {
      const errorData = responseData.error
      errorInfo.type = errorData.code || 'VALIDATION_ERROR'

      // 处理验证错误详情（API v2格式）
      if (Array.isArray(errorData.details)) {
        errorData.details.forEach((detail) => {
          const fieldError = {
            field: detail.field,
            code: detail.code,
            message: detail.message,
            value: detail.value,
          }
          errorInfo.details.push(fieldError)

          // 按字段分组验证错误
          if (!errorInfo.validationErrors[detail.field]) {
            errorInfo.validationErrors[detail.field] = []
          }
          errorInfo.validationErrors[detail.field].push(fieldError)
        })
      }

      // 处理传统格式的验证错误
      else if (errorData.validation_errors) {
        Object.entries(errorData.validation_errors).forEach(([field, errors]) => {
          const errorList = Array.isArray(errors) ? errors : [errors]
          errorList.forEach((errorMsg) => {
            const fieldError = {
              field,
              code: 'VALIDATION_ERROR',
              message: typeof errorMsg === 'string' ? errorMsg : errorMsg.message || '验证失败',
              value: null,
            }
            errorInfo.details.push(fieldError)

            if (!errorInfo.validationErrors[field]) {
              errorInfo.validationErrors[field] = []
            }
            errorInfo.validationErrors[field].push(fieldError)
          })
        })
      }
    }

    // 生成用户友好的建议
    generateErrorSuggestions(errorInfo)
  } catch (parseError) {
    console.error('解析错误响应失败:', parseError)
    errorInfo.message = '系统错误，请联系管理员'
  }

  return errorInfo
}

// 生成错误建议
function generateErrorSuggestions(errorInfo) {
  errorInfo.details.forEach((detail) => {
    switch (detail.code) {
      case 'HAS_CHILDREN':
        errorInfo.suggestions.push('请先删除子部门，或使用强制删除选项')
        break
      case 'HAS_USERS':
        errorInfo.suggestions.push('请先将用户移动到其他部门')
        break
      case 'DEPARTMENTS_NOT_FOUND':
        errorInfo.suggestions.push('请刷新页面后重新选择部门')
        break
      case 'BATCH_SIZE_EXCEEDED':
        errorInfo.suggestions.push('请减少选择的部门数量（最多50个）')
        break
      case 'MISSING_FIELD':
        errorInfo.suggestions.push('请重新选择要删除的部门')
        break
      default:
        if (!errorInfo.suggestions.length) {
          errorInfo.suggestions.push('请检查选择的部门是否有效')
        }
    }
  })

  // 去重建议
  errorInfo.suggestions = [...new Set(errorInfo.suggestions)]
}

// 处理批量删除成功
function handleBatchDeleteSuccess(result, attemptedIds) {
  console.log('批量删除成功:', result)

  // 提取成功信息
  const data = result.data || {}
  const deletedDepartments = data.deleted_departments || []
  const summary = data.summary || {}
  const totalDeleted = summary.total_deleted || deletedDepartments.length || attemptedIds.length
  const deletionType = summary.deletion_type || 'soft'
  const failedIds = summary.failed_ids || []

  // 构建成功消息
  let successMessage = `成功删除 ${totalDeleted} 个部门`

  // 添加删除类型信息
  if (deletionType === 'soft') {
    successMessage += '（软删除）'
  } else if (deletionType === 'permanent') {
    successMessage += '（永久删除）'
  }

  // 准备详细信息
  const details = []

  // 成功删除的部门
  if (deletedDepartments.length > 0) {
    details.push({
      type: 'success',
      title: '成功删除的部门',
      items: deletedDepartments.map((dept) => ({
        name: dept.name,
        id: dept.id,
        type: dept.deletion_type || deletionType,
      })),
    })
  }

  // 如果有部分失败的情况
  if (failedIds.length > 0) {
    const failedDepts = failedIds.map((id) => {
      const dept = tableData.value.find((item) => item.id === id)
      return dept ? dept.name : `部门${id}`
    })

    details.push({
      type: 'warning',
      title: '删除失败的部门',
      items: failedDepts.map((name) => ({ name, reason: '可能包含子部门或关联用户' })),
    })

    // 显示警告类型的结果
    showOperationResult('warning', '批量删除部分成功', successMessage, details, false)
  } else {
    // 完全成功
    showOperationResult('success', '批量删除成功', successMessage, details, true)
  }

  // 清空选择并刷新列表
  selectedRowKeys.value = []
  $table.value?.handleSearch()
}

// 显示批量删除错误
function displayBatchDeleteError(errorInfo, attemptedIds) {
  console.error('批量删除错误详情:', errorInfo)

  // 构建详细的错误消息
  let errorMessage = errorInfo.message

  // 准备详细错误信息
  const details = []

  // 检查是否有HAS_CHILDREN错误，如果有则提供强制删除选项
  let hasChildrenError = false
  let hasUsersError = false

  // 添加具体的验证错误信息
  if (errorInfo.details.length > 0) {
    // 按错误类型分组显示
    const errorsByType = {}
    errorInfo.details.forEach((detail) => {
      if (!errorsByType[detail.code]) {
        errorsByType[detail.code] = []
      }
      errorsByType[detail.code].push(detail)

      // 检查错误类型
      if (detail.code === 'HAS_CHILDREN') {
        hasChildrenError = true
      }
      if (detail.code === 'HAS_USERS') {
        hasUsersError = true
      }
    })

    Object.entries(errorsByType).forEach(([code, errors]) => {
      let title = ''
      let items = []

      switch (code) {
        case 'HAS_CHILDREN':
          title = '包含子部门的部门'
          items = errors.map((error) => {
            const deptId = error.value
            const dept = tableData.value.find((item) => item.id === deptId)
            return {
              name: dept ? dept.name : `部门${deptId}`,
              reason: error.message || '该部门包含子部门',
            }
          })
          break
        case 'HAS_USERS':
          title = '包含用户的部门'
          items = errors.map((error) => {
            const deptId = error.value
            const dept = tableData.value.find((item) => item.id === deptId)
            return {
              name: dept ? dept.name : `部门${deptId}`,
              reason: error.message || '该部门包含用户，请先移动用户到其他部门',
            }
          })
          break
        case 'DEPARTMENTS_NOT_FOUND':
          title = '不存在的部门'
          items = errors.map((error) => ({
            name: `部门${error.value}`,
            reason: '部门不存在或已被删除',
          }))
          break
        default:
          title = '其他错误'
          items = errors.map((error) => ({
            name: error.field || '未知',
            reason: error.message || '未知错误',
          }))
      }

      if (items.length > 0) {
        details.push({
          type: 'error',
          title,
          items,
        })
      }
    })
  }

  // 添加建议
  if (errorInfo.suggestions.length > 0) {
    details.push({
      type: 'info',
      title: '建议',
      items: errorInfo.suggestions.map((suggestion) => ({ name: suggestion })),
    })
  }

  // 如果只有HAS_CHILDREN错误（没有HAS_USERS错误），提供强制删除选项
  if (hasChildrenError && !hasUsersError) {
    showForceDeleteConfirmation(attemptedIds, errorMessage, details)
  } else {
    // 显示错误结果对话框
    showOperationResult('error', '批量删除失败', errorMessage, details, false)
  }
}

const columns = [
  {
    type: 'selection',
    width: 40,
    align: 'center',
    fixed: 'left',
  },
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: '部门名称',
    key: 'name',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
    tree: true,
  },
  {
    title: '备注',
    key: 'desc',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '操作',
    key: 'actions',
    width: 'auto',
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        h(
          PermissionButton,
          {
            permission: 'PUT /api/v2/departments/{id}',
            size: 'small',
            type: 'primary',
            style: 'margin-left: 8px;',
            onClick: () => {
              console.log('row', row.parent_id)
              if (row.parent_id === 0) {
                isDisabled.value = true
              } else {
                isDisabled.value = false
              }
              handleEdit(row)
            },
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit', { size: 16 }),
          }
        ),
        h(
          PermissionButton,
          {
            permission: 'DELETE /api/v2/departments/{id}',
            size: 'small',
            type: 'error',
            style: 'margin-left: 8px;',
            loading: singleDeleteLoading.value.has(row.id),
            disabled: singleDeleteLoading.value.has(row.id),
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: `确定删除部门"${
              row.name || row.dept_name
            }"吗？删除后将无法恢复，请谨慎操作。`,
            onConfirm: () => handleSingleDelete(row.id, row.name || row.dept_name, false),
          },
          {
            default: () => (singleDeleteLoading.value.has(row.id) ? '删除中...' : '删除'),
            icon: singleDeleteLoading.value.has(row.id)
              ? undefined
              : renderIcon('material-symbols:delete-outline', { size: 16 }),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage
    show-footer
    title="部门列表"
    class="system-dept-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <BatchDeleteButton
          :selected-items="selectedItems"
          :selected-count="selectedRowKeys.length"
          resource-name="部门"
          permission="DELETE /api/v2/departments/batch"
          :exclude-condition="(dept) => dept.user_count > 0"
          :loading="batchDeleteLoading"
          @batch-delete="handleBatchDelete"
        />

        <PermissionButton permission="POST /api/v2/departments" type="primary" @click="addDepts">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />
          新建部门
        </PermissionButton>
      </div>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      v-model:expanded-row-keys="expandedRowKeys"
      :columns="columns"
      :get-data="getDeptListData"
      :is-pagination="false"
      :cascade="false"
      :children-key="'children'"
      :default-expand-all="true"
      :row-key="'id'"
      :indent="32"
      @on-checked="handleRowSelection"
    >
      <template #queryBar>
        <QueryBarItem label="部门名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入部门名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave(getDeptTreeData)"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="deptRules"
      >
        <NFormItem label="父级部门" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            :options="deptOption"
            key-field="id"
            label-field="name"
            placeholder="请选择父级部门"
            clearable
            default-expand-all
            :disabled="isDisabled"
          ></NTreeSelect>
        </NFormItem>
        <NFormItem label="部门名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入部门名称" />
        </NFormItem>
        <NFormItem label="备注" path="desc">
          <NInput v-model:value="modalForm.desc" type="textarea" clearable />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" min="0"></NInputNumber>
        </NFormItem>
      </NForm>
    </CrudModal>

    <!-- 操作结果对话框 -->
    <NModal
      v-model:show="operationResult.visible"
      :mask-closable="false"
      preset="card"
      :style="{ maxWidth: '600px', width: '90%' }"
      :title="operationResult.title"
      size="medium"
      :bordered="false"
      segmented
    >
      <template #header-extra>
        <NButton quaternary circle size="small" @click="closeOperationResult">
          <TheIcon icon="material-symbols:close" :size="18" />
        </NButton>
      </template>

      <!-- 操作结果内容 -->
      <div class="space-y-4">
        <!-- 主要消息 -->
        <NAlert :type="operationResult.type" :show-icon="true" :closable="false">
          {{ operationResult.message }}
        </NAlert>

        <!-- 详细信息 -->
        <div v-if="operationResult.details.length > 0" class="space-y-3">
          <div v-for="(detail, index) in operationResult.details" :key="index">
            <div class="mb-2 flex items-center">
              <TheIcon
                :icon="getDetailIcon(detail.type)"
                :size="16"
                :class="getDetailIconClass(detail.type)"
                class="mr-2"
              />
              <span class="text-gray-700 font-medium">{{ detail.title }}</span>
            </div>

            <NList bordered class="rounded-md">
              <NListItem v-for="(item, itemIndex) in detail.items" :key="itemIndex">
                <div class="w-full flex items-center justify-between">
                  <div class="flex items-center">
                    <span class="font-medium">{{ item.name }}</span>
                    <NTag
                      v-if="item.type"
                      :type="item.type === 'soft' ? 'warning' : 'error'"
                      size="small"
                      class="ml-2"
                    >
                      {{ item.type === 'soft' ? '软删除' : '永久删除' }}
                    </NTag>
                  </div>
                  <span v-if="item.reason" class="text-sm text-gray-500">{{ item.reason }}</span>
                </div>
              </NListItem>
            </NList>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <template #footer>
        <NSpace justify="end">
          <NButton @click="closeOperationResult"> 关闭 </NButton>
          <NButton
            v-if="operationResult.type === 'success'"
            type="primary"
            @click="closeOperationResult"
          >
            确定
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>

<style scoped>
/* 优化表格勾选框样式 */
:deep(.n-data-table .n-data-table-th--selection),
:deep(.n-data-table .n-data-table-td--selection) {
  padding: 12px 8px !important;
  width: 50px !important;
  min-width: 50px !important;
  max-width: 50px !important;
  text-align: center !important;
  vertical-align: middle !important;
}

:deep(.n-data-table .n-checkbox) {
  transform: scale(1.1) !important;
  display: inline-block !important;
  vertical-align: middle !important;
}

:deep(.n-data-table .n-checkbox .n-checkbox-box) {
  border-width: 1.5px !important;
  border-color: var(--border-color-base) !important;
  width: 16px !important;
  height: 16px !important;
  border-radius: var(--border-radius-sm) !important;
}

:deep(.n-data-table .n-checkbox:hover .n-checkbox-box) {
  border-color: var(--primary-color-hover) !important;
}

:deep(.n-data-table .n-checkbox--checked .n-checkbox-box) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
}

/* 移除可能的下划线或横杠 */
:deep(.n-data-table .n-data-table-td--selection::after),
:deep(.n-data-table .n-data-table-th--selection::after) {
  display: none !important;
}

:deep(.n-data-table .n-checkbox::after),
:deep(.n-data-table .n-checkbox::before) {
  display: none !important;
}
</style>
