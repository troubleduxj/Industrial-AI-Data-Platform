/**
 * 设备管理 API v2
 */

import { request } from '@/utils/http'
import { deviceFieldApi } from './device-field'
import { formatDateTime } from '@/utils'

export interface DeviceType {
  id: number
  type_name: string
  type_code: string
  tdengine_stable_name?: string
  description?: string
  icon?: string
  is_active: boolean
  device_count?: number
}

export interface DeviceField {
  id: number
  device_type_code: string
  field_name: string
  field_code: string
  field_type: 'float' | 'int' | 'string' | 'boolean'
  unit?: string
  sort_order: number
  display_config?: {
    icon?: string
    color?: string
  }
  field_category?: string
  description?: string
  is_monitoring_key: boolean
  is_active: boolean
}

/**
 * 设备类型 API
 */
const deviceTypes = {
  /**
   * 获取设备类型列表
   */
  list(params?: { include_counts?: boolean }) {
    return request({
      url: '/api/v2/device-types',
      method: 'get',
      params
    })
  }
}

/**
 * 设备 API
 */
const devices = {
  /**
   * 获取设备列表
   */
  list(params?: {
    page?: number
    page_size?: number
    device_type?: string
    device_code?: string
    device_name?: string
    install_location?: string
  }) {
    return request({
      url: '/api/v2/devices',
      method: 'get',
      params
    })
  },

  /**
   * 获取实时监控数据
   */
  getRealtimeMonitoring(params?: {
    device_codes?: string[]
    device_type?: string
    status?: string
    page?: number
    page_size?: number
  }) {
    // 将 device_codes 数组转换为逗号分隔的字符串
    const requestParams = {
      ...params,
      device_codes: params?.device_codes?.join(',')
    }
    
    return request({
      url: '/api/v2/devices/monitoring/realtime',
      method: 'get',
      params: requestParams
    })
  },

  /**
   * 获取设备历史数据
   */
  getHistory(deviceId: number, params?: {
    start_time?: string
    end_time?: string
    status?: string
    page?: number
    page_size?: number
  }) {
    return request({
      url: `/api/v2/devices/${deviceId}/history`,
      method: 'get',
      params
    })
  },

  /**
   * 获取设备监控数据 (V2)
   */
  getMonitoring(deviceId: number, params?: {
    start_time?: string
    end_time?: string
    page?: number
    page_size?: number
  }) {
    return request({
      url: `/api/v2/devices/${deviceId}/monitoring`,
      method: 'get',
      params
    })
  },

  /**
   * 获取设备统计信息
   */
  getStatistics() {
    return request({
      url: '/api/v2/devices/statistics',
      method: 'get'
    })
  }
}

/**
 * 设备字段 API
 */
const deviceFields = {
  ...deviceFieldApi
}

/**
 * 兼容性API - 用于历史数据查询页面
 */
export const compatibilityApi = {
  /**
   * 获取设备历史数据（兼容旧接口）
   */
  async getDeviceHistoryData(params: {
    device_code: string
    start_time?: number
    end_time?: number
    limit?: number
    offset?: number
    page?: number
    page_size?: number
  }) {
    // 先通过device_code获取设备信息
    const devicesResponse = await devices.list({
      device_code: params.device_code,
      page: 1,
      page_size: 1
    })

    console.log('Device list response:', devicesResponse)
    
    if (!devicesResponse.data || devicesResponse.data.length === 0) {
      throw new Error('设备不存在')
    }

    const device = devicesResponse.data[0]
    console.log('Device object:', device)
    console.log('Device ID type:', typeof device.id, 'Value:', device.id)
    
    const deviceId = Number(device.id)
    console.log('Final deviceId:', deviceId)

    // 转换时间格式（从毫秒时间戳转为本地时间字符串）
    const queryParams: any = {}
    if (params.start_time) {
      queryParams.start_time = formatDateTime(params.start_time)
    }
    if (params.end_time) {
      queryParams.end_time = formatDateTime(params.end_time)
    }

    // 处理分页参数
    // 优先使用 page_size, 如果没有则使用 limit
    if (params.page_size !== undefined) {
      queryParams.page_size = params.page_size
    } else if (params.limit !== undefined) {
      queryParams.page_size = params.limit
    }

    // 优先使用 page, 如果没有则使用 offset 计算
    if (params.page !== undefined) {
      queryParams.page = params.page
    } else if (params.offset !== undefined) {
      const limit = queryParams.page_size || 20
      queryParams.page = Math.floor(params.offset / limit) + 1
    }

    // 调用历史数据API
    return devices.getHistory(deviceId, queryParams)
  }
}

/**
 * 导出 API
 */
export const deviceV2Api = {
  deviceTypes,
  devices,
  deviceFields
}

/**
 * 设备类型 API 导出
 */
export const deviceTypeApi = deviceTypes

/**
 * 兼容性导出 - 用于维护看板等页面
 */
export const deviceApi = devices

export default deviceV2Api
