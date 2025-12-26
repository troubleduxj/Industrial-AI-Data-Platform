/**
 * 批量删除功能修复工具
 * 解决Vue组合式API上下文问题和权限检查问题
 */

/**
 * 创建安全的批量删除错误处理器
 * 解决useMessage和useDialog在非组件上下文中的问题
 */
export function createSafeBatchDeleteHandler() {
  // 检查是否在Vue组件上下文中
  let message = null
  let dialog = null

  try {
    // 尝试获取全局的message和dialog实例
    if (window.$message) {
      message = window.$message
    }
    if (window.$dialog) {
      dialog = window.$dialog
    }
  } catch (error) {
    console.warn('无法获取naive-ui上下文，使用fallback处理器')
  }

  return {
    message: message || createFallbackMessage(),
    dialog: dialog || createFallbackDialog(),
  }
}

/**
 * 创建fallback消息处理器
 */
function createFallbackMessage() {
  return {
    success: (msg, options) => {
      console.log('✅ Success:', msg)
      // 可以在这里添加自定义的消息显示逻辑
    },
    error: (msg, options) => {
      console.error('❌ Error:', msg)
      // 可以在这里添加自定义的错误显示逻辑
    },
    warning: (msg, options) => {
      console.warn('⚠️ Warning:', msg)
      // 可以在这里添加自定义的警告显示逻辑
    },
    loading: (msg, options) => {
      console.log('🔄 Loading:', msg)
      return { destroy: () => console.log('Loading destroyed') }
    },
  }
}

/**
 * 创建fallback对话框处理器
 */
function createFallbackDialog() {
  return {
    warning: (options) => {
      console.log('🔔 Dialog:', options)
      // 使用原生confirm作为fallback
      const confirmed = confirm(`${options.title}\n\n${options.content}`)
      if (confirmed && options.onPositiveClick) {
        options.onPositiveClick()
      } else if (!confirmed && options.onNegativeClick) {
        options.onNegativeClick()
      }
    },
  }
}

/**
 * 安全的权限检查函数
 * 解决权限检查返回undefined的问题
 */
export function safeHasPermission(permission, hasPermissionFn) {
  try {
    if (!permission) return true // 如果没有指定权限，默认允许
    if (!hasPermissionFn || typeof hasPermissionFn !== 'function') {
      console.warn('权限检查函数不可用，默认允许访问')
      return true
    }

    const result = hasPermissionFn(permission)

    // 确保返回布尔值
    if (typeof result === 'boolean') {
      return result
    }

    // 如果返回undefined或其他值，根据具体情况处理
    if (result === undefined || result === null) {
      console.warn('权限检查返回undefined，默认拒绝访问')
      return false
    }

    // 转换为布尔值
    return Boolean(result)
  } catch (error) {
    console.error('权限检查出错:', error)
    return false // 出错时默认拒绝访问
  }
}

/**
 * 修复批量删除确认对话框
 */
export function fixedShowBatchDeleteConfirmation(
  selectedItems,
  resourceName,
  excludeCondition,
  options = {}
) {
  const {
    title = `批量删除${resourceName}`,
    showProtectedItems = true,
    maxDisplayItems = 5,
  } = options

  return new Promise((resolve) => {
    const context = createSafeBatchDeleteHandler()
    const { dialog, message } = context

    const validItems = excludeCondition
      ? selectedItems.filter((item) => !excludeCondition(item))
      : selectedItems
    const invalidItems = excludeCondition
      ? selectedItems.filter((item) => excludeCondition(item))
      : []

    if (validItems.length === 0) {
      if (invalidItems.length > 0) {
        const protectedMessage = formatProtectedItemsMessage(invalidItems, resourceName)
        message.warning(protectedMessage, { duration: 6000 })
      } else {
        message.warning(`请选择要删除的${resourceName}`)
      }
      resolve(false)
      return
    }

    let content = `确定要删除选中的 ${validItems.length} 个${resourceName}吗？`

    if (showProtectedItems && invalidItems.length > 0) {
      const protectedSummary = formatProtectedItemsSummary(
        invalidItems,
        resourceName,
        maxDisplayItems
      )
      content += `\n\n${protectedSummary}`
    }

    dialog.warning({
      title,
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
 * 修复批量删除错误处理
 */
export function fixedHandleBatchDeleteError(error, resourceName, options = {}) {
  const { silent = false, showDetails = true } = options
  const context = createSafeBatchDeleteHandler()
  const { message } = context

  if (silent) {
    return formatErrorForReturn(error, resourceName)
  }

  if (error.response) {
    const { status, data } = error.response

    switch (status) {
      case 401:
        message.error('登录已过期，请重新登录', { duration: 5000 })
        return formatErrorForReturn(error, resourceName, '认证失败')

      case 403:
        message.error(`权限不足，无法批量删除${resourceName}`, { duration: 5000 })
        return formatErrorForReturn(error, resourceName, '权限不足')

      case 422:
        const validationMessage = formatValidationError(data, resourceName)
        message.error(validationMessage, { duration: 6000 })
        return formatErrorForReturn(error, resourceName, '参数验证失败')

      case 400:
        const businessMessage = formatBusinessError(data, resourceName)
        message.error(businessMessage, { duration: 6000 })
        return formatErrorForReturn(error, resourceName, '业务规则冲突')

      case 500:
      case 502:
      case 503:
      case 504:
        message.error(`服务器错误，批量删除${resourceName}失败，请稍后重试`, { duration: 6000 })
        return formatErrorForReturn(error, resourceName, '服务器错误')

      default:
        const defaultMessage = data?.message || `批量删除${resourceName}失败`
        message.error(defaultMessage, { duration: 5000 })
        return formatErrorForReturn(error, resourceName, '请求失败')
    }
  } else if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
    message.error(`网络连接失败，请检查网络连接后重试`, { duration: 6000 })
    return formatErrorForReturn(error, resourceName, '网络错误')
  } else if (error.code === 'TIMEOUT_ERROR' || error.message?.includes('timeout')) {
    message.error(`请求超时，请稍后重试`, { duration: 6000 })
    return formatErrorForReturn(error, resourceName, '请求超时')
  } else {
    const errorMessage = error.message || `批量删除${resourceName}失败：未知错误`
    message.error(errorMessage, { duration: 5000 })
    return formatErrorForReturn(error, resourceName, '未知错误')
  }
}

/**
 * 修复批量删除结果处理
 */
export function fixedHandleBatchDeleteResult(response, resourceName, options = {}) {
  const { showDetails = true, duration = 8000 } = options
  const context = createSafeBatchDeleteHandler()
  const { message } = context

  if (!response || !response.data) {
    message.error(`批量删除${resourceName}响应格式错误`)
    return
  }

  const { data } = response
  const { deleted_count = 0, failed_count = 0, failed = [], skipped_items = [] } = data

  const allFailedItems = [...failed, ...skipped_items]
  const totalFailedCount = allFailedItems.length

  if (totalFailedCount === 0) {
    // 全部成功
    message.success(`成功删除 ${deleted_count} 个${resourceName}`, { duration: 4000 })
  } else if (deleted_count === 0) {
    // 全部失败
    const failureMessage = formatAllFailedMessage(allFailedItems, resourceName)
    message.error(failureMessage, { duration })
  } else {
    // 部分成功
    const partialMessage = formatPartialSuccessMessage(
      deleted_count,
      totalFailedCount,
      allFailedItems,
      resourceName,
      showDetails
    )
    message.warning(partialMessage, { duration })
  }
}

// 辅助函数
function formatProtectedItemsMessage(protectedItems, resourceName) {
  return `选中的项目中有 ${protectedItems.length} 个${resourceName}受到保护，无法删除`
}

function formatProtectedItemsSummary(protectedItems, resourceName, maxDisplayItems) {
  const displayItems = protectedItems.slice(0, maxDisplayItems)
  const itemNames = displayItems.map((item) => item.name || `ID:${item.id}`).join('、')
  const moreText = protectedItems.length > maxDisplayItems ? `等${protectedItems.length}个` : ''

  return `注意：以下项目将被跳过：\n• 受保护项目（${itemNames}${moreText}）`
}

function formatValidationError(data, resourceName) {
  if (data?.error?.details && Array.isArray(data.error.details)) {
    const messages = data.error.details.map((detail) => detail.message || '验证失败').join('；')
    return `参数验证失败：${messages}`
  }
  return `批量删除${resourceName}参数验证失败`
}

function formatBusinessError(data, resourceName) {
  const message = data?.message || `批量删除${resourceName}失败`

  if (data?.error?.details && Array.isArray(data.error.details)) {
    const details = data.error.details.map((detail) => detail.message || '业务规则冲突').join('；')
    return `${message}：${details}`
  }

  return message
}

function formatAllFailedMessage(failedItems, resourceName) {
  return `批量删除失败：${failedItems.length}个${resourceName}无法删除`
}

function formatPartialSuccessMessage(
  successCount,
  failedCount,
  failedItems,
  resourceName,
  showDetails
) {
  let message = `批量删除完成：成功删除 ${successCount} 个，失败 ${failedCount} 个${resourceName}`

  if (showDetails && failedItems.length > 0) {
    const reasons = failedItems.map((item) => item.reason || '未知原因').join('，')
    message += `\n\n失败原因：${reasons}`
  }

  return message
}

function formatErrorForReturn(error, resourceName, type = '未知错误') {
  return {
    success: false,
    error: error,
    type,
    message: error.message || `批量删除${resourceName}失败`,
    timestamp: new Date().toISOString(),
  }
}
