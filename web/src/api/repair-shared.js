/**
 * 维修记录 API - Shared 层适配器
 * 使用 shared API 层，保持与现有 API 接口兼容
 */

import sharedApi from './shared'

// ========== 维修记录 API ==========

export const repairApi = {
  // 获取维修记录列表
  list: async (params = {}) => {
    const result = await sharedApi.repair.getRepairRecords(params)
    // 保持完整的分页响应格式（包含 data, meta, links）
    return result
  },

  // 获取维修记录详情
  get: async (id) => {
    const result = await sharedApi.repair.getRepairRecord(id)
    return { data: result.data }
  },

  // 创建维修记录
  create: async (data) => {
    const result = await sharedApi.repair.createRepairRecord(data)
    return { data: result.data }
  },

  // 更新维修记录
  update: async (id, data) => {
    const result = await sharedApi.repair.updateRepairRecord(id, data)
    return { data: result.data }
  },

  // 删除维修记录
  delete: async (id) => {
    const result = await sharedApi.repair.deleteRepairRecord(id)
    return { data: result.data }
  },

  // 批量删除维修记录
  batchDelete: async (ids) => {
    const result = await sharedApi.repair.batchDeleteRepairRecords(ids)
    return { data: result.data }
  },

  // 分配维修任务
  assign: async (id, assignedTo) => {
    const result = await sharedApi.repair.assignRepairTask(id, assignedTo)
    return { data: result.data }
  },

  // 开始维修
  start: async (id) => {
    const result = await sharedApi.repair.startRepair(id)
    return { data: result.data }
  },

  // 完成维修
  complete: async (id, repairDescription, repairResult) => {
    const result = await sharedApi.repair.completeRepair(id, repairDescription, repairResult)
    return { data: result.data }
  },

  // 取消维修
  cancel: async (id, reason) => {
    const result = await sharedApi.repair.cancelRepair(id, reason)
    return { data: result.data }
  },

  // 获取设备的维修历史
  getDeviceHistory: async (deviceId, params = {}) => {
    const result = await sharedApi.repair.getDeviceRepairHistory(deviceId, params)
    return { data: result.data }
  },

  // 搜索维修记录
  search: async (params) => {
    const result = await sharedApi.repair.getRepairRecords({
      ...params,
      keyword: params.keyword || params.search,
    })
    return { data: result.data }
  },
}

// ========== 维修状态常量 ==========

export const RepairStatus = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
}

export const RepairStatusText = {
  [RepairStatus.PENDING]: '待处理',
  [RepairStatus.IN_PROGRESS]: '进行中',
  [RepairStatus.COMPLETED]: '已完成',
  [RepairStatus.CANCELLED]: '已取消',
}

export const RepairStatusColor = {
  [RepairStatus.PENDING]: 'warning',
  [RepairStatus.IN_PROGRESS]: 'info',
  [RepairStatus.COMPLETED]: 'success',
  [RepairStatus.CANCELLED]: 'default',
}

// ========== 工具函数 ==========

/**
 * 计算维修耗时（分钟）
 */
export function calculateRepairDuration(startTime, endTime) {
  if (!startTime || !endTime) return null
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  return Math.round((end - start) / 1000 / 60)
}

/**
 * 格式化维修耗时
 */
export function formatRepairDuration(minutes) {
  if (!minutes || minutes < 0) return '-'

  if (minutes < 60) {
    return `${minutes}分钟`
  }

  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  if (hours < 24) {
    return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
  }

  const days = Math.floor(hours / 24)
  const remainHours = hours % 24

  return remainHours > 0 ? `${days}天${remainHours}小时` : `${days}天`
}

/**
 * 判断维修是否超时
 */
export function isRepairOverdue(reportedAt, status, timeoutHours = 24) {
  if (status === RepairStatus.COMPLETED || status === RepairStatus.CANCELLED) {
    return false
  }

  const reported = new Date(reportedAt).getTime()
  const now = Date.now()
  const elapsed = (now - reported) / 1000 / 3600

  return elapsed > timeoutHours
}

// ========== 默认导出（兼容现有代码） ==========

export default {
  ...repairApi,
  RepairStatus,
  RepairStatusText,
  RepairStatusColor,
  calculateRepairDuration,
  formatRepairDuration,
  isRepairOverdue,
}

/**
 * 使用说明：
 *
 * 旧方式（保持兼容）：
 * import { repairApi } from '@/api/repair';
 *
 * 新方式（推荐）：
 * import { repairApi, RepairStatus } from '@/api/repair-shared';
 * await repairApi.list({ page: 1, repair_status: RepairStatus.PENDING });
 *
 * 或直接使用 shared：
 * import sharedApi from '@/api/shared';
 * await sharedApi.repair.getRepairRecords({ page: 1 });
 *
 * 使用工具函数：
 * import { formatRepairDuration, isRepairOverdue } from '@/api/repair-shared';
 * const duration = formatRepairDuration(125); // "2小时5分钟"
 * const overdue = isRepairOverdue('2025-10-24 10:00:00', 'pending'); // true/false
 */
