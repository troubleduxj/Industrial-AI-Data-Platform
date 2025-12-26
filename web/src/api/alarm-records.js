/**
 * 报警记录管理 API
 */

import { requestV2 } from '@/utils/http/v2-interceptors'

export const alarmRecordsApi = {
  // 获取报警记录列表
  list: (params = {}) => requestV2.get('/alarm-records', { params }),

  // 获取报警记录详情
  get: (id) => requestV2.get(`/alarm-records/${id}`),

  // 确认报警
  acknowledge: (id, data = {}) => requestV2.post(`/alarm-records/${id}/acknowledge`, data),

  // 解决报警
  resolve: (id, data = {}) => requestV2.post(`/alarm-records/${id}/resolve`, data),

  // 关闭报警
  close: (id, data = {}) => requestV2.post(`/alarm-records/${id}/close`, data),

  // 批量处理
  batchHandle: (data) => requestV2.post('/alarm-records/batch-handle', data),

  // 获取报警统计
  statistics: (params = {}) => requestV2.get('/alarm-records/statistics', { params }),
}

// 报警状态常量
export const AlarmStatus = {
  ACTIVE: 'active',
  ACKNOWLEDGED: 'acknowledged',
  RESOLVED: 'resolved',
  CLOSED: 'closed',
}

export const AlarmStatusOptions = [
  { label: '活跃', value: 'active', color: '#f56c6c' },
  { label: '已确认', value: 'acknowledged', color: '#e6a23c' },
  { label: '已解决', value: 'resolved', color: '#67c23a' },
  { label: '已关闭', value: 'closed', color: '#909399' },
]

// 报警级别常量（复用）
export { AlarmLevel, AlarmLevelOptions } from './alarm-rules'

export default alarmRecordsApi
