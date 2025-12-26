/**
 * 批量删除组合式函数
 * 提供统一的批量删除逻辑，包含选择状态管理、确认对话框、API调用和错误处理
 */
import { ref, computed, nextTick } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { debounce } from '@/utils'
import { usePermission } from '@/composables/usePermission'

/**
 * 批量删除组合式函数
 * @param {Object} options 配置选项
 * @param {string} options.name 资源名称，如 "API"、"字典类型"
 * @param {Function} options.batchDeleteApi 批量删除API函数，接收ids数组，返回Promise
 * @param {Function} options.refresh 刷新数据的函数
 * @param {Function} options.validateItem 验证单个项目的函数，返回 { valid: boolean, reason?: string }
 * @param {string} options.permission 权限标识符，用于权限检查
 * @param {Function} options.excludeCondition 排除条件函数，返回true表示该项目不能删除
 * @param {number} options.maxBatchSize 最大批量删除数量，默认100
 * @param {boolean} options.enableDebounce 是否启用防抖，默认true
 * @param {number} options.debounceDelay 防抖延迟时间，默认300ms
 * @returns {Object} 批量删除相关的响应式数据和方法
 */
export function useBatchDelete(options = {}) {
  const {
    name = '项目',
    batchDeleteApi,
    refresh,
    validateItem,
    permission,
    excludeCondition,
    maxBatchSize = 100,
    enableDebounce = true,
    debounceDelay = 300,
  } = options

  // 验证必需参数
  if (!batchDeleteApi || typeof batchDeleteApi !== 'function') {
    throw new Error('useBatchDelete: batchDeleteApi 参数是必需的，且必须是一个函数')
  }
  if (!refresh || typeof refresh !== 'function') {
    throw new Error('useBatchDelete: refresh 参数是必需的，且必须是一个函数')
  }

  const message = useMessage()
  const dialog = useDialog()
  const { hasPermission } = usePermission()

  // 响应式状态
  const selectedItems = ref([])
  const selectedRowKeys = ref([])
  const isLoading = ref(false)
  const showConfirmDialog = ref(false)
  const lastOperation = ref(null)

  // 计算属性
  const selectedCount = computed(() => selectedItems.value.length)
  const hasSelection = computed(() => selectedCount.value > 0)
  const canBatchDelete = computed(() => {
    if (!hasSelection.value) return false
    if (permission && !hasPermission(permission)) return false
    if (selectedCount.value > maxBatchSize) return false
    return true
  })

  // 获取有效的删除项目（排除不能删除的项目）
  const validItems = computed(() => {
    if (!excludeCondition) return selectedItems.value
    return selectedItems.value.filter((item) => !excludeCondition(item))
  })

  const invalidItems = computed(() => {
    if (!excludeCondition) return []
    return selectedItems.value.filter((item) => excludeCondition(item))
  })

  const validCount = computed(() => validItems.value.length)
  const invalidCount = computed(() => invalidItems.value.length)

  /**
   * 设置选中的项目
   * @param {Array} items 选中的项目数组
   * @param {Array} keys 选中的行键数组
   */
  function setSelectedItems(items, keys = []) {
    selectedItems.value = items || []
    selectedRowKeys.value = keys || []
  }

  /**
   * 清除选择
   */
  function clearSelection() {
    selectedItems.value = []
    selectedRowKeys.value = []
  }

  /**
   * 验证选中的项目
   * @returns {Object} 验证结果
   */
  function validateSelection() {
    const result = {
      valid: [],
      invalid: [],
      warnings: [],
    }

    if (!hasSelection.value) {
      result.warnings.push(`请选择要删除的${name}`)
      return result
    }

    if (selectedCount.value > maxBatchSize) {
      result.warnings.push(`一次最多只能删除 ${maxBatchSize} 个${name}`)
      return result
    }

    // 权限检查
    if (permission && !hasPermission(permission)) {
      result.warnings.push(`您没有批量删除${name}的权限`)
      return result
    }

    // 验证每个项目
    selectedItems.value.forEach((item) => {
      // 检查排除条件
      if (excludeCondition && excludeCondition(item)) {
        result.invalid.push({
          item,
          reason: '系统保护项，不允许删除',
        })
        return
      }

      // 自定义验证
      if (validateItem) {
        const validation = validateItem(item)
        if (!validation.valid) {
          result.invalid.push({
            item,
            reason: validation.reason || '验证失败',
          })
          return
        }
      }

      result.valid.push(item)
    })

    // 生成警告信息
    if (result.invalid.length > 0) {
      result.warnings.push(`${result.invalid.length} 个${name}无法删除`)
    }

    return result
  }

  /**
   * 显示确认对话框
   * @returns {Promise<boolean>} 用户是否确认
   */
  function showConfirmation() {
    return new Promise((resolve) => {
      const validItems = excludeCondition
        ? selectedItems.value.filter((item) => !excludeCondition(item))
        : selectedItems.value
      const invalidItems = excludeCondition
        ? selectedItems.value.filter((item) => excludeCondition(item))
        : []

      if (validItems.length === 0) {
        if (invalidItems.length > 0) {
          message.warning(`选中的项目中有 ${invalidItems.length} 个${name}受到保护，无法删除`, {
            duration: 6000,
          })
        } else {
          message.warning(`请选择要删除的${name}`)
        }
        resolve(false)
        return
      }

      let content = `确定要删除选中的 ${validItems.length} 个${name}吗？`

      if (invalidItems.length > 0) {
        content += `\n\n注意：${invalidItems.length} 个受保护项目将被跳过`
      }

      dialog.warning({
        title: `批量删除${name}`,
        content,
        positiveText: '确定删除',
        negativeText: '取消',
        onPositiveClick: () => resolve(true),
        onNegativeClick: () => resolve(false),
        onMaskClick: () => resolve(false),
      })
    })
  }

  /**
   * 执行批量删除
   * @returns {Promise<void>}
   */
  async function executeBatchDelete() {
    const validation = validateSelection()

    if (validation.valid.length === 0) {
      if (validation.warnings.length > 0) {
        // 使用统一的错误处理显示保护项目信息
        const protectedItems = validation.invalid.map((item) => ({
          ...item.item,
          reason: item.reason,
        }))

        const errorsByType = categorizeErrors(validation.invalid)
        const errorMessage = formatCategorizedErrors(errorsByType)
        message.warning(errorMessage, { duration: 6000 })
      }
      return
    }

    try {
      isLoading.value = true

      // 显示加载消息
      const loadingMsg = message.loading(`正在删除 ${validation.valid.length} 个${name}...`, {
        duration: 0,
      })

      // 提取ID数组
      const ids = validation.valid.map((item) => item.id)

      // 调用批量删除API
      const response = await batchDeleteApi(ids)

      // 清除加载消息
      loadingMsg.destroy()

      // 处理响应
      if (response && response.success) {
        const { data } = response
        const deletedCount = data?.deleted_count || validation.valid.length
        const failedItems = data?.failed || data?.failed_items || []
        const skippedItems = data?.skipped_items || []

        // 记录操作结果
        lastOperation.value = {
          success: true,
          deletedCount,
          failedItems,
          skippedItems,
          totalAttempted: validation.valid.length,
        }

        // 处理批量删除结果 - 使用已有的data变量
        const { deleted_count = 0, failed_count = 0, failed = [], skipped_items = [] } = data || {}

        const allFailedItems = [...failed, ...skipped_items]
        const totalFailedCount = allFailedItems.length

        if (totalFailedCount === 0) {
          message.success(`成功删除 ${deleted_count} 个${name}`, { duration: 4000 })
        } else if (deleted_count === 0) {
          message.error(`批量删除失败：${totalFailedCount}个${name}无法删除`, { duration: 8000 })
        } else {
          message.warning(
            `批量删除完成：成功删除 ${deleted_count} 个，失败 ${totalFailedCount} 个${name}`,
            { duration: 8000 }
          )
        }

        // 清除选择并刷新数据
        clearSelection()

        // 延迟刷新，确保UI状态更新完成
        await nextTick()
        if (refresh) {
          await refresh()
        }
      } else {
        throw new Error(response?.message || `批量删除${name}失败`)
      }
    } catch (error) {
      console.error('批量删除失败:', error)

      // 记录失败结果
      lastOperation.value = {
        success: false,
        error: error.message || '未知错误',
        totalAttempted: validation.valid.length,
      }

      // 处理批量删除错误
      if (error.response) {
        const { status, data } = error.response
        switch (status) {
          case 401:
            message.error('登录已过期，请重新登录', { duration: 5000 })
            break
          case 403:
            message.error(`权限不足，无法批量删除${name}`, { duration: 5000 })
            break
          case 422:
            message.error(`参数验证失败`, { duration: 6000 })
            break
          case 400:
            message.error(data?.message || `批量删除${name}失败`, { duration: 6000 })
            break
          default:
            message.error(data?.message || `批量删除${name}失败`, { duration: 5000 })
        }
      } else {
        message.error(error.message || `批量删除${name}失败：未知错误`, { duration: 5000 })
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 处理批量删除（包含确认流程）
   */
  async function handleBatchDelete() {
    if (!canBatchDelete.value) {
      return
    }

    const confirmed = await showConfirmation()
    if (confirmed) {
      await executeBatchDelete()
    }
  }

  // 创建防抖版本的批量删除函数
  const debouncedBatchDelete = enableDebounce
    ? debounce(handleBatchDelete, debounceDelay)
    : handleBatchDelete

  /**
   * 获取操作结果摘要
   * @returns {string} 结果摘要文本
   */
  function getOperationSummary() {
    if (!lastOperation.value) return ''

    const { success, deletedCount, failedItems, skippedItems, error, totalAttempted } =
      lastOperation.value

    if (!success) {
      return `删除失败：${error}`
    }

    const failedCount = (failedItems?.length || 0) + (skippedItems?.length || 0)

    if (failedCount > 0) {
      return `部分成功：删除了 ${deletedCount}/${totalAttempted} 个${name}`
    }

    return `全部成功：删除了 ${deletedCount} 个${name}`
  }

  /**
   * 获取失败项目详情
   * @returns {Array} 失败项目列表
   */
  function getFailedItemsDetails() {
    if (!lastOperation.value) return []

    const details = []

    if (lastOperation.value.failedItems) {
      details.push(
        ...lastOperation.value.failedItems.map((item) => ({
          ...item,
          type: 'failed',
        }))
      )
    }

    if (lastOperation.value.skippedItems) {
      details.push(
        ...lastOperation.value.skippedItems.map((item) => ({
          ...item,
          type: 'skipped',
        }))
      )
    }

    return details
  }

  /**
   * 重置操作状态
   */
  function resetOperationState() {
    lastOperation.value = null
    clearSelection()
    isLoading.value = false
  }

  /**
   * 按错误类型分类前端验证错误
   * @param {Array} invalidItems 无效项目列表
   * @returns {Object} 按类型分组的错误
   */
  function categorizeErrors(invalidItems) {
    const categories = {
      currentUser: [],
      adminUser: [],
      superUser: [],
      systemProtected: [],
      hasRelations: [],
      other: [],
    }

    invalidItems.forEach((item) => {
      const reason = item.reason || ''

      if (reason.includes('当前登录用户')) {
        categories.currentUser.push(item)
      } else if (reason.includes('admin管理员')) {
        categories.adminUser.push(item)
      } else if (reason.includes('超级管理员')) {
        categories.superUser.push(item)
      } else if (reason.includes('系统保护') || reason.includes('系统内置')) {
        categories.systemProtected.push(item)
      } else if (reason.includes('有') && (reason.includes('个') || reason.includes('引用'))) {
        categories.hasRelations.push(item)
      } else {
        categories.other.push(item)
      }
    })

    return categories
  }

  /**
   * 按错误类型分类后端返回的错误
   * @param {Array} failedItems 后端返回的失败项目列表
   * @returns {Object} 按类型分组的错误
   */
  function categorizeBackendErrors(failedItems) {
    const categories = {
      currentUser: [],
      adminUser: [],
      superUser: [],
      systemProtected: [],
      hasRelations: [],
      notFound: [],
      other: [],
    }

    failedItems.forEach((item) => {
      const reason = item.reason || ''

      if (reason.includes('当前登录用户')) {
        categories.currentUser.push(item)
      } else if (reason.includes('admin管理员')) {
        categories.adminUser.push(item)
      } else if (reason.includes('超级管理员')) {
        categories.superUser.push(item)
      } else if (reason.includes('系统保护') || reason.includes('系统内置')) {
        categories.systemProtected.push(item)
      } else if (reason.includes('不存在')) {
        categories.notFound.push(item)
      } else if (reason.includes('有') && (reason.includes('个') || reason.includes('引用'))) {
        categories.hasRelations.push(item)
      } else {
        categories.other.push(item)
      }
    })

    return categories
  }

  /**
   * 格式化分类错误消息
   * @param {Object} errorsByType 按类型分组的错误
   * @returns {string} 格式化的错误消息
   */
  function formatCategorizedErrors(errorsByType) {
    const messages = []

    if (errorsByType.currentUser.length > 0) {
      messages.push(`⚠️ 不能删除当前登录用户`)
    }

    if (errorsByType.adminUser.length > 0) {
      messages.push(`🚫 不能删除admin管理员账户`)
    }

    if (errorsByType.superUser.length > 0) {
      messages.push(`🔒 不能删除超级管理员`)
    }

    if (errorsByType.systemProtected.length > 0) {
      messages.push(`🛡️ ${errorsByType.systemProtected.length}个系统保护项不能删除`)
    }

    if (errorsByType.hasRelations.length > 0) {
      messages.push(`🔗 ${errorsByType.hasRelations.length}个项目有关联数据不能删除`)
    }

    if (errorsByType.other.length > 0) {
      messages.push(`❌ ${errorsByType.other.length}个项目因其他原因不能删除`)
    }

    return messages.join('\n')
  }

  /**
   * 格式化保护摘要信息
   * @param {Object} errorsByType 按类型分组的错误
   * @returns {string} 格式化的保护摘要
   */
  function formatProtectionSummary(errorsByType) {
    const summaries = []

    if (errorsByType.currentUser.length > 0) {
      summaries.push(`• 当前登录用户将被跳过`)
    }

    if (errorsByType.adminUser.length > 0) {
      summaries.push(`• admin管理员账户将被跳过`)
    }

    if (errorsByType.superUser.length > 0) {
      summaries.push(`• 超级管理员将被跳过`)
    }

    if (errorsByType.systemProtected.length > 0) {
      summaries.push(`• ${errorsByType.systemProtected.length}个系统保护项将被跳过`)
    }

    if (errorsByType.hasRelations.length > 0) {
      summaries.push(`• ${errorsByType.hasRelations.length}个有关联数据的项目将被跳过`)
    }

    if (errorsByType.other.length > 0) {
      summaries.push(`• ${errorsByType.other.length}个其他受保护项目将被跳过`)
    }

    return `注意：以下项目将被跳过：\n${summaries.join('\n')}`
  }

  /**
   * 格式化批量删除结果消息
   * @param {number} successCount 成功数量
   * @param {number} failedCount 失败数量
   * @param {Object} errorsByType 按类型分组的错误
   * @param {string} resourceName 资源名称
   * @returns {string} 格式化的结果消息
   */
  function formatBatchDeleteResult(successCount, failedCount, errorsByType, resourceName) {
    let message = `批量删除完成：成功删除 ${successCount} 个，失败 ${failedCount} 个${resourceName}`

    const failureReasons = []

    if (errorsByType.currentUser.length > 0) {
      failureReasons.push(`当前用户保护 ${errorsByType.currentUser.length}个`)
    }

    if (errorsByType.adminUser.length > 0) {
      failureReasons.push(`admin用户保护 ${errorsByType.adminUser.length}个`)
    }

    if (errorsByType.superUser.length > 0) {
      failureReasons.push(`超级管理员保护 ${errorsByType.superUser.length}个`)
    }

    if (errorsByType.systemProtected.length > 0) {
      failureReasons.push(`系统保护 ${errorsByType.systemProtected.length}个`)
    }

    if (errorsByType.hasRelations.length > 0) {
      failureReasons.push(`关联数据限制 ${errorsByType.hasRelations.length}个`)
    }

    if (errorsByType.notFound.length > 0) {
      failureReasons.push(`项目不存在 ${errorsByType.notFound.length}个`)
    }

    if (errorsByType.other.length > 0) {
      failureReasons.push(`其他原因 ${errorsByType.other.length}个`)
    }

    if (failureReasons.length > 0) {
      message += `\n\n失败原因：${failureReasons.join('，')}`
    }

    return message
  }

  /**
   * 格式化网络错误消息
   * @param {Error} error 错误对象
   * @param {string} resourceName 资源名称
   * @returns {string} 格式化的错误消息
   */
  function formatNetworkError(error, resourceName) {
    const errorMessage = error.message || '未知错误'

    if (errorMessage.includes('Network Error') || errorMessage.includes('网络')) {
      return `网络连接失败，请检查网络连接后重试`
    }

    if (errorMessage.includes('timeout') || errorMessage.includes('超时')) {
      return `请求超时，请稍后重试`
    }

    if (errorMessage.includes('403') || errorMessage.includes('权限')) {
      return `没有删除${resourceName}的权限`
    }

    if (errorMessage.includes('500')) {
      return `服务器内部错误，请联系管理员`
    }

    return `批量删除${resourceName}失败：${errorMessage}`
  }

  return {
    // 响应式状态
    selectedItems,
    selectedRowKeys,
    isLoading,
    showConfirmDialog,
    lastOperation,

    // 计算属性
    selectedCount,
    hasSelection,
    canBatchDelete,
    validItems,
    invalidItems,
    validCount,
    invalidCount,

    // 方法
    setSelectedItems,
    clearSelection,
    validateSelection,
    showConfirmation,
    executeBatchDelete,
    handleBatchDelete: debouncedBatchDelete,
    getOperationSummary,
    getFailedItemsDetails,
    resetOperationState,

    // 工具方法
    validateItem: validateSelection,

    // 配置信息
    config: {
      name,
      permission,
      maxBatchSize,
      enableDebounce,
      debounceDelay,
    },
  }
}

/**
 * 创建批量删除配置的工厂函数
 * @param {string} resourceName 资源名称
 * @param {string} permission 权限标识符
 * @returns {Function} 配置好的useBatchDelete函数
 */
export function createBatchDeleteComposable(resourceName, permission) {
  return (options = {}) => {
    return useBatchDelete({
      name: resourceName,
      permission,
      ...options,
    })
  }
}

// 预定义的批量删除组合函数
export const useApiBatchDelete = createBatchDeleteComposable('API', 'api:batch_delete')
export const useDictTypeBatchDelete = createBatchDeleteComposable(
  '字典类型',
  'dict_type:batch_delete'
)
export const useDictDataBatchDelete = createBatchDeleteComposable(
  '字典数据',
  'dict_data:batch_delete'
)
export const useSystemParamBatchDelete = createBatchDeleteComposable(
  '系统参数',
  'system_param:batch_delete'
)
export const useApiGroupBatchDelete = createBatchDeleteComposable(
  'API分组',
  'api_group:batch_delete'
)
export const useDepartmentBatchDelete = createBatchDeleteComposable(
  '部门',
  'department:batch_delete'
)
export const useRoleBatchDelete = createBatchDeleteComposable('角色', 'role:batch_delete')
export const useUserBatchDelete = createBatchDeleteComposable('用户', 'user:batch_delete')
export const useMenuBatchDelete = createBatchDeleteComposable('菜单', 'menu:batch_delete')
