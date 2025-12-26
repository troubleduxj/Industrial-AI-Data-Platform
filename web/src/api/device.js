import { request } from '@/utils'
import { requestV2 } from '@/utils/http/v2-interceptors'

// 设备基础信息管理 API
export const deviceApi = {
  // 获取设备列表
  getDeviceList: (params = {}) =>
    request.get('/device/list', {
      params: {
        ...params,
        device_name: params.device_name,
        device_code: params.device_code,
        manufacturer: params.manufacturer,
        device_type: params.device_type,
        device_model: params.device_model,
        online_address: params.online_address,
      },
    }),

  // 根据ID获取设备详情
  getDeviceById: (id) => request.get(`/device/get?device_id=${id}`),

  // 创建设备
  createDevice: (data = {}) => request.post('/device/create', data),

  // 更新设备
  updateDevice: (id, data = {}) => request.post('/device/update', { id, ...data }),

  // 删除设备
  deleteDevice: (id) => request.delete('/device/delete', { params: { device_id: id } }),

  // 批量删除设备
  batchDeleteDevices: (ids = []) => request.delete('/device/batch', { data: { ids } }),
}

// 设备类型管理 API
export const deviceTypeApi = {
  // 获取设备类型列表
  getDeviceTypes: (params = {}) =>
    request.get('/device/types', {
      params: {
        include_counts: true, // 包含设备数量统计
        ...params,
      },
    }),

  // 获取设备类型列表（用于CRUD表格）
  getDeviceTypeList: (params = {}) =>
    request.get('/device/types', {
      params,
    }),

  // 根据类型代码获取设备类型详情
  getDeviceTypeByCode: (typeCode) => request.get(`/device/types/${typeCode}`),

  // 创建设备类型
  createDeviceType: (data = {}) => request.post('/device/types', data),

  // 更新设备类型
  updateDeviceType: (data = {}) => request.put(`/device/types/${data.type_code}`, data),

  // 删除设备类型
  deleteDeviceType: (params = {}) =>
    request.delete(`/device/types/${params.type_code}`, { params }),
}

// 设备实时数据 API
export const deviceDataApi = {
  // 创建设备实时数据
  createRealTimeData: (data = {}) => request.post('/device/data/realtime', data),

  // 根据设备ID获取最新实时数据
  getLatestDataByDeviceId: (deviceId) => request.get(`/device/data/latest/${deviceId}`),

  // 根据设备编号获取最新实时数据
  getLatestDataByDeviceCode: (deviceCode) => request.get(`/device/data/latest/code/${deviceCode}`),

  // 获取所有设备状态汇总
  getDevicesStatusSummary: (params = {}) => request.get('/device/data/status/summary', { params }),

  // 获取在线设备数量
  getOnlineDevicesCount: (params = {}) =>
    request.get('/device/data/status/online-count', { params }),

  // 查询设备历史数据
  getDeviceHistoryData: (params = {}) => {
    // 将前端的limit/offset参数转换为后端期望的page/page_size参数
    const { limit, offset, ...otherParams } = params
    const page = offset ? Math.floor(offset / (limit || 10)) + 1 : 1
    const page_size = limit || 10

    return request.get('/device/history', {
      params: {
        ...otherParams,
        page,
        page_size,
      },
    })
  },

  // 更新设备实时数据
  updateRealTimeData: (id, data = {}) => request.put(`/device/data/realtime/${id}`, data),

  // 批量更新设备实时数据
  batchUpdateRealTimeData: (data = []) => request.put('/device/data/realtime/batch', { data }),

  // 通用实时数据接口
  getRealtimeData: (params = {}) => {
    const typeCode = params.type_code || 'welding'
    return request.get(`/device/data/realtime/${typeCode}`, {
      params: { ...params, type_code: undefined },
    })
  },

  // 设备状态汇总
  getDeviceSummary: (params = {}) =>
    request.get('/device/data/universal/statistics/' + (params.type_code || 'welding'), {
      params: { ...params, type_code: undefined },
    }),

  // 获取设备状态统计（新增）
  getDeviceStatusStatistics: (params = {}) =>
    request.get('/device/data/status/statistics', { params }),

  // 获取设备实时状态统计数据 (使用v2 API)
  getRealtimeDeviceStatus: (params = {}) =>
    requestV2.get('/devices/statistics/realtime/device-status', { params }),

  // 获取设备在线率历史数据（新增）
  getDeviceOnlineRateHistory: (params = {}) =>
    request.get('/device/data/status/online_rate_history', { params }),

  // 获取在线率统计数据
  getOnlineRateStatistics: (params = {}) =>
    request.get('/device/data/statistics/online-rate', { params }),

  // 获取焊接时长统计数据
  getWeldTimeStatistics: (params = {}) =>
    request.get('/device/data/statistics/weld-time', { params }),

  // 获取在线率和焊接率统计数据 (使用v2 API)
  getOnlineWeldingRateStatistics: (params = {}) =>
    requestV2.get('/devices/statistics/dashboard/online-welding-rate', { params }),

  // 获取报警类型分布统计数据 (使用v2 API)
  getAlarmCategorySummary: (params = {}) =>
    requestV2.get('/devices/statistics/dashboard/alarm-category-summary', { params }),

  // 获取报警时长Top排名统计数据 (使用v2 API)
  getAlarmRecordTop: (params = {}) =>
    requestV2.get('/devices/statistics/dashboard/alarm-record-top', { params }),

  // 获取焊机日报汇总数据 (使用v2 API)
  getWeldingDailyReportSummary: (params = {}) =>
    requestV2.get('/devices/statistics/daily-report/summary', { params }),

  // 获取焊机日报详细数据
  getWeldingDailyReportDetail: (params = {}) =>
    request.get('/device/statistics/daily-report/detail', { params }),

  // 获取焊接记录列表
  getWeldingRecordList: (params = {}) =>
    request.get('/devices/statistics/use-record/list', { params }),
}

// 设备报警 API
export const deviceAlarmApi = {
  // 获取设备报警历史列表
  getAlarmList: (params = {}) =>
    request.get('/device/alarm/list', {
      params: {
        device_type: params.device_type,
        device_code: params.device_code,
        start_time: params.start_time,
        end_time: params.end_time,
        page: params.page || 1,
        page_size: params.page_size || 20,
      },
    }),

  // 获取设备报警统计信息
  getAlarmStatistics: (params = {}) =>
    request.get('/device/alarm/statistics', {
      params: {
        device_type: params.device_type,
        start_time: params.start_time,
        end_time: params.end_time,
      },
    }),
}

// 导出默认对象，包含所有设备相关API
export default {
  ...deviceApi,
  ...deviceTypeApi,
  ...deviceDataApi,
  ...deviceAlarmApi,
}
