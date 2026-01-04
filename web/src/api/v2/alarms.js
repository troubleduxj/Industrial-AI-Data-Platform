/**
 * 报警管理 API (V2)
 * 从 device-v2.js 迁移而来
 */
import { requestV2 } from '@/utils/http/v2-interceptors'

export const deviceAlarmApi = {
  // 获取报警列表 (对应 deviceApis.devices.getAlarms)
  getAlarmList: (params = {}) => requestV2.get('/devices/alarms', { params }),

  // 获取报警统计信息 (对应 deviceApis.alarms.getStatistics)
  getAlarmStatistics: (params = {}) => requestV2.get('/alarms/statistics', { params }),

  // 处理报警
  handleAlarm: (alarmId, data = {}) => requestV2.put(`/alarms/${alarmId}/handle`, data),

  // 确认报警
  acknowledgeAlarm: (alarmId, data = {}) => requestV2.post(`/alarms/${alarmId}/acknowledge`, data),

  // 批量处理报警
  batchHandleAlarms: (data = {}) => requestV2.put('/alarms/batch-handle', data),
}

export default deviceAlarmApi
