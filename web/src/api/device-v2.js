/**
 * 设备管理模块 API v2
 * 提供设备基础信息、设备类型、维护记录等的v2版本API接口
 */

import { createDeviceApis, apiV2Client } from '@/utils/api-v2-migration'
import { createSafeApiCall } from '@/utils/error-handler'
import { deviceFieldApi } from './device-field'

// 创建设备管理API实例
const deviceApis = createDeviceApis()

// 创建带错误处理的API包装函数
function wrapApiWithErrorHandler(apiFunction, options = {}) {
  return createSafeApiCall(apiFunction, {
    rethrow: true, // 允许页面组件处理特定错误
    ...options,
  })
}

// 设备类型API
export const deviceTypeApi = {
  // 获取设备类型列表
  list: wrapApiWithErrorHandler((params = {}) => deviceApis.deviceTypes.list(params)),

  // 获取设备类型详情
  get: wrapApiWithErrorHandler((typeCode, params = {}) =>
    deviceApis.deviceTypes.get(typeCode, params)
  ),

  // 创建设备类型
  create: wrapApiWithErrorHandler((data = {}) => deviceApis.deviceTypes.create(data)),

  // 更新设备类型 - 使用type_code作为标识符
  update: wrapApiWithErrorHandler((typeCodeOrData, data = {}) => {
    // 如果第一个参数是对象且包含type_code，则提取type_code
    if (typeof typeCodeOrData === 'object' && typeCodeOrData.type_code) {
      const typeCode = typeCodeOrData.type_code
      const updateData = { ...typeCodeOrData }
      delete updateData.type_code // 移除type_code，避免在请求体中重复
      return deviceApis.deviceTypes.update(typeCode, updateData)
    }
    // 否则按照标准方式处理
    return deviceApis.deviceTypes.update(typeCodeOrData, data)
  }),

  // 删除设备类型 - 使用type_code作为标识符
  delete: wrapApiWithErrorHandler((typeCodeOrData) => {
    // 如果参数是对象且包含type_code，则提取type_code
    if (typeof typeCodeOrData === 'object' && typeCodeOrData.type_code) {
      return deviceApis.deviceTypes.delete(typeCodeOrData.type_code)
    }
    // 否则直接使用参数作为type_code
    return deviceApis.deviceTypes.delete(typeCodeOrData)
  }),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => deviceApis.deviceTypes.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => deviceApis.deviceTypes.batchUpdate(items)),
  batchDelete: wrapApiWithErrorHandler((items) => deviceApis.deviceTypes.batchDelete(items)),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => deviceApis.deviceTypes.search(params)),
}

// 设备数据API (包含焊机日报等统计数据)
export const deviceDataApi = {
  // 焊机日报相关API
  getWeldingDailyReportSummary: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的焊机日报汇总API
    return deviceApis.devices.getWeldingDailyReportSummary(params)
  }),

  getWeldingDailyReportDetail: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的焊机日报详情API
    return deviceApis.devices.getWeldingDailyReportDetail(params)
  }),

  // 报警统计相关API
  getAlarmCategorySummary: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的报警类型分布统计API
    return deviceApis.devices.getAlarmCategorySummary(params)
  }),

  getAlarmRecordTop: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的报警记录Top排名统计API
    return deviceApis.devices.getAlarmRecordTop(params)
  }),

  // 在线率和焊接率统计API
  getOnlineWeldingRateStatistics: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的在线率和焊接率统计API
    return deviceApis.devices.getOnlineWeldingRateStatistics(params)
  }),

  // 实时设备状态API
  getRealtimeDeviceStatus: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的实时设备状态API
    return deviceApis.devices.getRealtimeDeviceStatus(params)
  }),
}

// 设备报警API (V2版本)
export const deviceAlarmApi = {
  // 获取报警列表
  getAlarmList: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的设备报警列表API
    return deviceApis.devices.getAlarms(params)
  }),

  // 获取报警统计信息
  getAlarmStatistics: wrapApiWithErrorHandler((params = {}) => {
    // 调用V2版本的报警统计API
    return deviceApis.alarms.getStatistics(params)
  }),

  // 处理报警
  handleAlarm: wrapApiWithErrorHandler((alarmId, data = {}) => {
    // 调用V2版本的报警处理API
    return deviceApis.alarms.handle(alarmId, data)
  }),

  // 确认报警
  acknowledgeAlarm: wrapApiWithErrorHandler((alarmId, data = {}) => {
    // 调用V2版本的报警确认API
    return deviceApis.alarms.acknowledge(alarmId, data)
  }),

  // 批量处理报警
  batchHandleAlarms: wrapApiWithErrorHandler((data = {}) => {
    // 调用V2版本的批量处理报警API
    return deviceApis.alarms.batchHandle(data)
  }),
}

// 设备API
export const deviceApi = {
  // 获取设备列表
  list: wrapApiWithErrorHandler((params = {}) => deviceApis.devices.list(params)),

  // 获取设备详情
  get: wrapApiWithErrorHandler((id, params = {}) => deviceApis.devices.get(id, params)),

  // 创建设备
  create: wrapApiWithErrorHandler((data = {}) => deviceApis.devices.create(data)),

  // 更新设备
  update: wrapApiWithErrorHandler((id, data = {}) => deviceApis.devices.update(id, data)),

  // 删除设备
  delete: wrapApiWithErrorHandler((id) => deviceApis.devices.delete(id)),

  // 获取设备数据
  getData: wrapApiWithErrorHandler((id, params = {}) => deviceApis.devices.getData({ id }, params)),

  // 获取设备状态
  getStatus: wrapApiWithErrorHandler((id, params = {}) =>
    deviceApis.devices.getStatus({ id }, params)
  ),

  // 获取设备监控数据
  getMonitoring: wrapApiWithErrorHandler((id, params = {}) =>
    deviceApis.devices.getMonitoring({ id }, params)
  ),

  // 获取设备统计
  getStatistics: wrapApiWithErrorHandler((params = {}) => deviceApis.devices.getStatistics(params)),

  // 获取设备历史数据
  getHistoryData: wrapApiWithErrorHandler((id, params = {}) =>
    deviceApis.devices.getHistoryData({ id }, params)
  ),

  // 获取实时监控数据
  getRealtimeMonitoring: wrapApiWithErrorHandler((params = {}) =>
    deviceApis.devices.getRealtimeMonitoring(params)
  ),

  // 获取监控数据汇总
  getMonitoringSummary: wrapApiWithErrorHandler((params = {}) =>
    deviceApis.devices.getMonitoringSummary(params)
  ),

  // 获取监控概览
  getMonitoringOverview: wrapApiWithErrorHandler((params = {}) =>
    deviceApis.devices.getMonitoringOverview(params)
  ),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => deviceApis.devices.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => deviceApis.devices.batchUpdate(items)),
  batchDelete: wrapApiWithErrorHandler((items) => deviceApis.devices.batchDelete(items)),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => deviceApis.devices.search(params)),

  // 获取设备实时数据及字段配置
  getRealtimeWithConfig: wrapApiWithErrorHandler((deviceCode, params = {}) =>
    deviceApis.devices.getRealtimeWithConfig(deviceCode, params)
  ),

  // 设备类型管理
  deviceTypes: deviceTypeApi,
}

// 设备维护API
export const maintenanceApi = {
  // 获取维护记录列表
  list: wrapApiWithErrorHandler((params = {}) => deviceApis.maintenance.list(params)),

  // 获取维护记录详情
  get: wrapApiWithErrorHandler((id, params = {}) => deviceApis.maintenance.get(id, params)),

  // 创建维护记录
  create: wrapApiWithErrorHandler((data = {}) => deviceApis.maintenance.create(data)),

  // 更新维护记录
  update: wrapApiWithErrorHandler((id, data = {}) => deviceApis.maintenance.update(id, data)),

  // 删除维护记录
  delete: wrapApiWithErrorHandler((id) => deviceApis.maintenance.delete(id)),

  // 获取维护计划
  getSchedule: wrapApiWithErrorHandler((params = {}) => deviceApis.maintenance.getSchedule(params)),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => deviceApis.maintenance.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => deviceApis.maintenance.batchUpdate(items)),
  batchDelete: wrapApiWithErrorHandler((items) => deviceApis.maintenance.batchDelete(items)),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => deviceApis.maintenance.search(params)),
}

// 设备维修记录API (扩展维护API)
export const repairRecordsApi = {
  // 获取维修记录列表
  list: wrapApiWithErrorHandler((params = {}) => {
    return apiV2Client.get('/device/maintenance/repair-records', params, { isList: true })
  }),

  // 获取维修记录详情
  get: wrapApiWithErrorHandler((id) => {
    return apiV2Client.get(`/device/maintenance/repair-records/${id}`)
  }),

  // 创建维修记录
  create: wrapApiWithErrorHandler((data) => {
    return apiV2Client.post('/device/maintenance/repair-records', data)
  }),

  // 更新维修记录
  update: wrapApiWithErrorHandler((id, data) => {
    return apiV2Client.put(`/device/maintenance/repair-records/${id}`, data)
  }),

  // 删除维修记录
  delete: wrapApiWithErrorHandler((id) => {
    return apiV2Client.delete(`/device/maintenance/repair-records/${id}`)
  }),

  // 批量删除维修记录
  batchDelete: wrapApiWithErrorHandler((ids) => {
    return apiV2Client.post('/device/maintenance/repair-records/batch-delete', { ids })
  }),

  // 获取设备字段配置
  getDeviceFields: wrapApiWithErrorHandler((deviceType) => {
    return apiV2Client.get(`/device/maintenance/device-fields/${deviceType}`)
  }),

  // 更新设备字段配置
  updateDeviceFields: wrapApiWithErrorHandler((deviceType, data) => {
    return apiV2Client.post(`/device/maintenance/device-fields/${deviceType}`, data)
  }),

  // 生成维修单号
  generateRepairCode: wrapApiWithErrorHandler(() => {
    return apiV2Client.post('/device/maintenance/repair-codes/generate')
  }),

  // 获取维修记录统计
  getStatistics: wrapApiWithErrorHandler((params = {}) => {
    return apiV2Client.get('/device/maintenance/repair-records/statistics', params)
  }),

  // 导出维修记录
  export: wrapApiWithErrorHandler((params = {}) => {
    return apiV2Client.get('/device/maintenance/repair-records/export', params, {
      responseType: 'blob',
    })
  }),

  // 获取维修记录模板
  getTemplate: wrapApiWithErrorHandler(() => {
    return apiV2Client.get(
      '/device/maintenance/repair-records/template',
      {},
      { responseType: 'blob' }
    )
  }),

  // 导入维修记录
  import: wrapApiWithErrorHandler((file) => {
    const formData = new FormData()
    formData.append('file', file)

    return apiV2Client.post('/device/maintenance/repair-records/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }),
}

// 设备字段动态参数展示API (TASK-7)
// 已从 device-field.ts 导入，不需要重复声明

// 设备工艺API
export const processApi = {
  // 获取工艺列表
  list: (params = {}) => deviceApis.processes.list(params),

  // 获取工艺详情
  get: (id, params = {}) => deviceApis.processes.get(id, params),

  // 创建工艺
  create: (data = {}) => deviceApis.processes.create(data),

  // 更新工艺
  update: (id, data = {}) => deviceApis.processes.update(id, data),

  // 删除工艺
  delete: (id) => deviceApis.processes.delete(id),

  // 执行工艺
  execute: (id, data = {}) => deviceApis.processes.execute({ id }, data),

  // 批量操作
  batchCreate: (items) => deviceApis.processes.batchCreate(items),
  batchUpdate: (items) => deviceApis.processes.batchUpdate(items),
  batchDelete: (items) => deviceApis.processes.batchDelete(items),

  // 高级搜索
  search: (params) => deviceApis.processes.search(params),
}

// 兼容性API - 保持与v1相同的接口名称
export const compatibilityApi = {
  // 设备基础信息 - v1兼容接口
  getDeviceList: (params = {}) => deviceApi.list(params),
  createDevice: (data = {}) => deviceApi.create(data),
  updateDevice: (id, data = {}) => deviceApi.update(id, data),
  deleteDevice: (id) => deviceApi.delete(id),
  batchDeleteDevices: (data = {}) => {
    const ids = data.ids || [data.id]
    return deviceApi.batchDelete(ids)
  },

  // 设备历史数据 - v1兼容接口
  getDeviceHistoryData: async (params = {}) => {
    // 从参数中提取device_id，如果没有则使用device_code查找
    const { device_id, device_code, ...otherParams } = params
    if (device_id) {
      return deviceApi.getHistoryData(device_id, otherParams)
    } else if (device_code) {
      // 如果只有device_code，先通过device_code获取设备信息
      try {
        const deviceList = await deviceApi.list({ device_code })
        if (deviceList.data && deviceList.data.length > 0) {
          const device = deviceList.data[0]
          console.log('Device object:', device)
          console.log('Device ID type:', typeof device.id, 'Value:', device.id)
          // 确保device.id是字符串或数字，而不是对象
          const deviceId = typeof device.id === 'object' ? JSON.stringify(device.id) : device.id
          console.log('Final deviceId:', deviceId)
          return deviceApi.getHistoryData(deviceId, otherParams)
        } else {
          throw new Error(`Device not found with code: ${device_code}`)
        }
      } catch (error) {
        throw new Error(`Failed to find device with code ${device_code}: ${error.message}`)
      }
    } else {
      throw new Error('device_id or device_code is required for v2 API')
    }
  },

  // 设备类型 - v1兼容接口
  getDeviceTypeList: (params = {}) => deviceTypeApi.list(params),
  getDeviceTypes: (params = {}) => deviceTypeApi.list(params),
  createDeviceType: (data = {}) => deviceTypeApi.create(data),
  updateDeviceType: (data = {}) => {
    const { id, type_code, ...updateData } = data
    return deviceTypeApi.update(id || type_code, updateData)
  },
  deleteDeviceType: (params = {}) => deviceTypeApi.delete(params.type_code || params.id),

  // 维护记录 - v1兼容接口
  getMaintenanceRecords: (params = {}) => maintenanceApi.list(params),
  createMaintenanceRecord: (data = {}) => maintenanceApi.create(data),
  updateMaintenanceRecord: (id, data = {}) => maintenanceApi.update(id, data),
  deleteMaintenanceRecord: (id) => maintenanceApi.delete(id),

  // 工艺管理 - v1兼容接口
  getProcessList: (params = {}) => processApi.list(params),
  createProcess: (data = {}) => processApi.create(data),
  updateProcess: (id, data = {}) => processApi.update(id, data),
  deleteProcess: (id) => processApi.delete(id),
  executeProcess: (id, data = {}) => processApi.execute(id, data),
}

// 默认导出
export default {
  // 设备基础信息API (包含deviceTypes)
  ...deviceApi,

  // 独立的API模块
  devices: deviceApi,
  deviceTypes: deviceTypeApi,
  deviceData: deviceDataApi,
  deviceAlarm: deviceAlarmApi,
  deviceField: deviceFieldApi, // 新增：设备字段动态参数展示
  deviceFields: deviceFieldApi, // 别名：设备字段配置管理（复数形式）
  maintenance: maintenanceApi,
  repairRecords: repairRecordsApi,
  processes: processApi,

  // v1兼容性接口
  ...compatibilityApi,
}
