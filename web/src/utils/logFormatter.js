// d:\Cursor\Project\DeviceMonitorV1\web\src\utils\logFormatter.js

// 获取日志状态类型
export const getLogStatusType = (status) => {
  const statusMap = {
    success: 'success',
    failed: 'error',
    running: 'warning',
    pending: 'info',
  }
  return statusMap[status] || 'info'
}

// 获取日志状态文本
export const getLogStatusText = (status) => {
  const statusMap = {
    success: '成功',
    failed: '失败',
    running: '运行中',
    pending: '等待中',
  }
  return statusMap[status] || status
}

// 格式化日期时间
export const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 格式化持续时间
export const formatDuration = (durationMs) => {
  if (!durationMs || durationMs === 0) return '0ms'

  if (durationMs < 1000) {
    return `${durationMs}ms`
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(1)}s`
  } else if (durationMs < 3600000) {
    const minutes = Math.floor(durationMs / 60000)
    const seconds = Math.floor((durationMs % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  } else {
    const hours = Math.floor(durationMs / 3600000)
    const minutes = Math.floor((durationMs % 3600000) / 60000)
    return `${hours}h ${minutes}m`
  }
}

// 格式化数据量
export const formatDataCount = (count) => {
  if (!count || count === 0) return '0'

  if (count < 1000) {
    return count.toString()
  } else if (count < 1000000) {
    return `${(count / 1000).toFixed(1)}K`
  } else {
    return `${(count / 1000000).toFixed(1)}M`
  }
}

// 格式化错误详情
export const formatErrorDetail = (errorDetail) => {
  if (!errorDetail) return null

  if (typeof errorDetail === 'string') {
    try {
      return JSON.parse(errorDetail)
    } catch {
      return { message: errorDetail }
    }
  }

  return errorDetail
}

// 格式化性能指标
export const formatPerformanceMetrics = (metrics) => {
  if (!metrics) return null

  if (typeof metrics === 'string') {
    try {
      return JSON.parse(metrics)
    } catch {
      return null
    }
  }

  return metrics
}
