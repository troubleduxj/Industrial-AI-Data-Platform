/**
 * 批量删除错误处理器
 * 提供统一的批量删除错误处理、结果处理和确认对话框功能
 */

/**
 * 统一的批量删除错误处理函数
 * @param {Error} error 错误对象
 * @param {string} resourceName 资源名称
 * @param {Object} options 选项
 * @param {Object} context Vue组件上下文，包含message实例
 * @returns {Object} 处理后的错误信息
 */
export function handleBatchDeleteError(error, resourceName, options = {}, context = null) {
  const { silent = false, showDetails = true } = options

  // 如果没有传入context，尝试从全局获取或返回错误信息
  if (!context || !context.message) {
    console.error('批量删除错误:', error)
    return formatErrorForReturn(error, resourceName, '错误处理失败')
  }

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
 * 用户友好的批量删除结果处理函数
 * @param {Object} response API响应
 * @param {string} resourceName 资源名称
 * @param {Object} options 选项
 * @param {Object} context Vue组件上下文，包含message实例
 */
export function handleBatchDeleteResult(response, resourceName, options = {}, context = null) {
  const { showDetails = true, duration = 8000 } = options

  // 如果没有传入context，只返回不显示消息
  if (!context || !context.message) {
    console.warn('批量删除结果处理缺少message上下文')
    return
  }

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

/**
 * 增强的批量删除确认对话框
 * @param {Array} selectedItems 选中的项目
 * @param {string} resourceName 资源名称
 * @param {Function} excludeCondition 排除条件函数
 * @param {Object} options 选项
 * @param {Object} context Vue组件上下文，包含dialog和message实例
 * @returns {Promise<boolean>} 用户是否确认
 */
export function showBatchDeleteConfirmation(
  selectedItems,
  resourceName,
  excludeCondition,
  options = {},
  context = null
) {
  const {
    title = `批量删除${resourceName}`,
    showProtectedItems = true,
    maxDisplayItems = 5,
  } = options

  return new Promise((resolve) => {
    // 如果没有传入context，直接返回false
    if (!context || !context.dialog || !context.message) {
      console.error('批量删除确认对话框缺少必要的上下文')
      resolve(false)
      return
    }

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
 * 格式化验证错误消息
 */
function formatValidationError(data, resourceName) {
  if (data?.error?.details && Array.isArray(data.error.details)) {
    const messages = data.error.details.map((detail) => detail.message || '验证失败').join('；')
    return `参数验证失败：${messages}`
  }
  return `批量删除${resourceName}参数验证失败`
}

/**
 * 格式化业务错误消息
 */
function formatBusinessError(data, resourceName) {
  const message = data?.message || `批量删除${resourceName}失败`

  if (data?.error?.details && Array.isArray(data.error.details)) {
    const details = data.error.details.map((detail) => detail.message || '业务规则冲突').join('；')
    return `${message}：${details}`
  }

  return message
}

/**
 * 格式化全部失败消息
 */
function formatAllFailedMessage(failedItems, resourceName) {
  const errorsByType = categorizeFailedItems(failedItems)
  const summaries = []

  if (errorsByType.currentUser.length > 0) {
    summaries.push(`当前用户保护 ${errorsByType.currentUser.length}个`)
  }
  if (errorsByType.adminUser.length > 0) {
    summaries.push(`admin用户保护 ${errorsByType.adminUser.length}个`)
  }
  if (errorsByType.superUser.length > 0) {
    summaries.push(`超级管理员保护 ${errorsByType.superUser.length}个`)
  }
  if (errorsByType.systemProtected.length > 0) {
    summaries.push(`系统保护 ${errorsByType.systemProtected.length}个`)
  }
  if (errorsByType.hasRelations.length > 0) {
    summaries.push(`关联数据限制 ${errorsByType.hasRelations.length}个`)
  }
  if (errorsByType.notFound.length > 0) {
    summaries.push(`项目不存在 ${errorsByType.notFound.length}个`)
  }
  if (errorsByType.other.length > 0) {
    summaries.push(`其他原因 ${errorsByType.other.length}个`)
  }

  const totalCount = failedItems.length
  let message = `批量删除失败：${totalCount}个${resourceName}无法删除`

  if (summaries.length > 0) {
    message += `\n\n失败原因：${summaries.join('，')}`
  }

  return message
}

/**
 * 格式化部分成功消息
 */
function formatPartialSuccessMessage(
  successCount,
  failedCount,
  failedItems,
  resourceName,
  showDetails
) {
  let message = `批量删除完成：成功删除 ${successCount} 个，失败 ${failedCount} 个${resourceName}`

  if (showDetails && failedItems.length > 0) {
    const errorsByType = categorizeFailedItems(failedItems)
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
  }

  return message
}

/**
 * 格式化受保护项目消息
 */
function formatProtectedItemsMessage(protectedItems, resourceName) {
  const errorsByType = categorizeFailedItems(
    protectedItems.map((item) => ({
      id: item.id,
      name: item.name,
      reason: getProtectionReason(item),
    }))
  )

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
 * 格式化受保护项目摘要
 */
function formatProtectedItemsSummary(protectedItems, resourceName, maxDisplayItems) {
  const errorsByType = categorizeFailedItems(
    protectedItems.map((item) => ({
      id: item.id,
      name: item.name,
      reason: getProtectionReason(item),
    }))
  )

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
    const items = errorsByType.systemProtected.slice(0, maxDisplayItems)
    const itemNames = items.map((item) => item.name || `ID:${item.id}`).join('、')
    const moreText =
      errorsByType.systemProtected.length > maxDisplayItems
        ? `等${errorsByType.systemProtected.length}个`
        : ''
    summaries.push(`• 系统保护项（${itemNames}${moreText}）将被跳过`)
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
 * 按错误类型分类失败项目
 */
function categorizeFailedItems(failedItems) {
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
    } else if (reason.includes('admin管理员') || reason.includes('admin用户')) {
      categories.adminUser.push(item)
    } else if (reason.includes('超级管理员')) {
      categories.superUser.push(item)
    } else if (
      reason.includes('系统保护') ||
      reason.includes('系统内置') ||
      reason.includes('系统关键')
    ) {
      categories.systemProtected.push(item)
    } else if (reason.includes('不存在')) {
      categories.notFound.push(item)
    } else if (
      reason.includes('有') &&
      (reason.includes('个') || reason.includes('引用') || reason.includes('关联'))
    ) {
      categories.hasRelations.push(item)
    } else {
      categories.other.push(item)
    }
  })

  return categories
}

/**
 * 获取保护原因
 */
function getProtectionReason(item) {
  if (item.is_current_user) {
    return '当前登录用户'
  }
  if (item.username === 'admin') {
    return 'admin管理员'
  }
  if (item.is_super_admin) {
    return '超级管理员'
  }
  if (item.is_system || item.is_protected) {
    return '系统保护项'
  }
  return '其他原因'
}

/**
 * 格式化错误返回对象
 */
function formatErrorForReturn(error, resourceName, type = '未知错误') {
  return {
    success: false,
    error: error,
    type,
    message: error.message || `批量删除${resourceName}失败`,
    timestamp: new Date().toISOString(),
  }
}
