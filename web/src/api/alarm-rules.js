/**
 * 报警规则管理 API
 */

import { requestV2 } from '@/utils/http/v2-interceptors'

export const alarmRulesApi = {
  // 获取报警规则列表
  list: (params = {}) => requestV2.get('/alarm-rules', { params }),

  // 获取报警规则详情
  get: (id) => requestV2.get(`/alarm-rules/${id}`),

  // 创建报警规则
  create: (data) => requestV2.post('/alarm-rules', data),

  // 更新报警规则
  update: (id, data) => requestV2.put(`/alarm-rules/${id}`, data),

  // 删除报警规则
  delete: (id) => requestV2.delete(`/alarm-rules/${id}`),

  // 启用/禁用规则
  toggle: (id) => requestV2.put(`/alarm-rules/${id}/toggle`),

  // 测试规则
  test: (id, testValue) => requestV2.post(`/alarm-rules/${id}/test`, null, { params: { test_value: testValue } }),

  // 获取可配置的设备类型
  getDeviceTypes: () => requestV2.get('/alarm-rules/device-types'),

  // 获取设备类型的可监测字段
  getFields: (deviceTypeCode) => requestV2.get(`/alarm-rules/fields/${deviceTypeCode}`),
}

// 报警级别常量
export const AlarmLevel = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
  EMERGENCY: 'emergency',
}

export const AlarmLevelOptions = [
  { label: '信息', value: 'info', color: '#909399' },
  { label: '警告', value: 'warning', color: '#e6a23c' },
  { label: '严重', value: 'critical', color: '#f56c6c' },
  { label: '紧急', value: 'emergency', color: '#c45656' },
]

// 阈值类型常量
export const ThresholdType = {
  RANGE: 'range',
  UPPER: 'upper',
  LOWER: 'lower',
  CHANGE_RATE: 'change_rate',
}

export const ThresholdTypeOptions = [
  { label: '范围检测', value: 'range', description: '检测值是否在指定范围内' },
  { label: '上限检测', value: 'upper', description: '检测值是否超过上限' },
  { label: '下限检测', value: 'lower', description: '检测值是否低于下限' },
  { label: '变化率检测', value: 'change_rate', description: '检测值的变化率' },
]

export default alarmRulesApi
