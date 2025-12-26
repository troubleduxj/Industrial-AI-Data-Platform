/**
 * 告警管理 API - Shared 层适配器
 * 使用 shared API 层，保持与现有 API 接口兼容
 */

import sharedApi from './shared'

// ========== 告警管理 API ==========

export const alarmApi = {
  // 获取告警列表
  list: async (params = {}) => {
    const result = await sharedApi.alarm.getAlarms(params)
    // 保持完整的分页响应格式（包含 data, meta, links）
    return result
  },

  // 获取告警详情
  get: async (id) => {
    const result = await sharedApi.alarm.getAlarm(id)
    return { data: result.data }
  },

  // 创建告警
  create: async (data) => {
    const result = await sharedApi.alarm.createAlarm(data)
    return { data: result.data }
  },

  // 确认告警
  acknowledge: async (id, remark) => {
    const result = await sharedApi.alarm.acknowledgeAlarm({ id, remark })
    return { data: result.data }
  },

  // 解决告警
  resolve: async (id, remark) => {
    const result = await sharedApi.alarm.resolveAlarm({ id, remark })
    return { data: result.data }
  },

  // 关闭告警
  close: async (id, remark) => {
    const result = await sharedApi.alarm.closeAlarm(id, remark)
    return { data: result.data }
  },

  // 删除告警
  delete: async (id) => {
    const result = await sharedApi.alarm.deleteAlarm(id)
    return { data: result.data }
  },

  // 批量确认告警
  batchAcknowledge: async (ids, remark) => {
    const result = await sharedApi.alarm.batchAcknowledgeAlarms(ids, remark)
    return { data: result.data }
  },

  // 批量解决告警
  batchResolve: async (ids, remark) => {
    const result = await sharedApi.alarm.batchResolveAlarms(ids, remark)
    return { data: result.data }
  },

  // 获取告警统计
  getStats: async (params = {}) => {
    const result = await sharedApi.alarm.getAlarmStats(params)
    return { data: result.data }
  },

  // 获取实时告警
  getRealtime: async (limit = 10) => {
    const result = await sharedApi.alarm.getRealtimeAlarms(limit)
    return { data: result.data }
  },

  // 搜索告警
  search: async (params) => {
    const result = await sharedApi.alarm.getAlarms({
      ...params,
      keyword: params.keyword || params.search,
    })
    return { data: result.data }
  },
}

// ========== 告警级别常量 ==========

export const AlarmLevel = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
}

export const AlarmLevelText = {
  [AlarmLevel.INFO]: '信息',
  [AlarmLevel.WARNING]: '警告',
  [AlarmLevel.ERROR]: '错误',
  [AlarmLevel.CRITICAL]: '严重',
}

export const AlarmLevelColor = {
  [AlarmLevel.INFO]: 'info',
  [AlarmLevel.WARNING]: 'warning',
  [AlarmLevel.ERROR]: 'error',
  [AlarmLevel.CRITICAL]: 'error',
}

// ========== 告警状态常量 ==========

export const AlarmStatus = {
  PENDING: 'pending',
  ACKNOWLEDGED: 'acknowledged',
  RESOLVED: 'resolved',
  CLOSED: 'closed',
}

export const AlarmStatusText = {
  [AlarmStatus.PENDING]: '待处理',
  [AlarmStatus.ACKNOWLEDGED]: '已确认',
  [AlarmStatus.RESOLVED]: '已解决',
  [AlarmStatus.CLOSED]: '已关闭',
}

export const AlarmStatusColor = {
  [AlarmStatus.PENDING]: 'warning',
  [AlarmStatus.ACKNOWLEDGED]: 'info',
  [AlarmStatus.RESOLVED]: 'success',
  [AlarmStatus.CLOSED]: 'default',
}

// ========== 默认导出（兼容现有代码） ==========

export default {
  ...alarmApi,
  AlarmLevel,
  AlarmLevelText,
  AlarmLevelColor,
  AlarmStatus,
  AlarmStatusText,
  AlarmStatusColor,
}

/**
 * 使用说明：
 *
 * 旧方式（保持兼容）：
 * import { alarmApi } from '@/api/alarm';
 *
 * 新方式（推荐）：
 * import { alarmApi } from '@/api/alarm-shared';
 * await alarmApi.list({ page: 1, level: 'warning' });
 *
 * 或直接使用 shared：
 * import sharedApi from '@/api/shared';
 * await sharedApi.alarm.getAlarms({ page: 1, level: 'warning' });
 *
 * 使用常量：
 * import { AlarmLevel, AlarmStatus } from '@/api/alarm-shared';
 * const level = AlarmLevel.WARNING;
 * const status = AlarmStatus.PENDING;
 */
