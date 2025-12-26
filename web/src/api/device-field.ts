/**
 * 设备字段动态参数展示 API
 * 实现基于元数据驱动的设备类型参数动态展示功能
 */

import { request } from '@/utils/http'

/**
 * 设备字段接口定义
 */
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
    chart_type?: string
  }
  field_category?: string
  field_group?: string  // ✅ 添加字段分组
  is_default_visible?: boolean  // ✅ 添加默认显示
  group_order?: number  // ✅ 添加分组排序
  description?: string
  is_monitoring_key: boolean
  is_alarm_enabled: boolean // ✅ 是否允许配置报警
  is_active: boolean
}

/**
 * 设备实时数据及配置接口定义
 */
export interface DeviceRealtimeWithConfig {
  device_code: string
  device_name: string
  device_type: string
  monitoring_fields: DeviceField[]
  realtime_data: Record<string, any>
}

/**
 * 批量查询请求接口定义
 */
export interface BatchRealtimeDataRequest {
  device_codes: string[]
}

/**
 * 分页查询请求接口定义
 */
export interface PaginatedRealtimeDataRequest {
  page: number
  page_size: number
  device_type?: string
  status?: string
}

/**
 * 分页查询响应接口定义
 */
export interface PaginatedRealtimeDataResponse {
  items: DeviceRealtimeWithConfig[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 设备字段 API
 */
export const deviceFieldApi = {
  /**
   * 获取指定设备类型的监测关键字段
   * @param deviceTypeCode 设备类型代码
   * @returns 监测关键字段列表
   */
  getMonitoringKeys(deviceTypeCode: string): Promise<{ data: DeviceField[] }> {
    return request({
      url: `/v2/device-fields/monitoring-keys/${deviceTypeCode}`,
      method: 'GET'
    })
  },

  /**
   * 获取所有设备类型的监测关键字段
   * @returns 所有设备类型的监测关键字段
   */
  getAllMonitoringKeys(): Promise<{
    data: Record<
      string,
      {
        device_type_name: string
        device_type_code: string
        fields: DeviceField[]
      }
    >
  }> {
    return request({
      url: '/v2/device-fields/monitoring-keys',
      method: 'GET'
    })
  },

  /**
   * 获取设备实时数据及字段配置
   * @param deviceCode 设备编码
   * @returns 设备实时数据及配置
   */
  getRealtimeWithConfig(deviceCode: string): Promise<{ data: DeviceRealtimeWithConfig }> {
    return request({
      url: `/v2/devices/${deviceCode}/realtime-with-config`,
      method: 'GET'
    })
  },

  /**
   * 批量获取设备实时数据及配置
   * @param deviceCodes 设备编码列表
   * @returns 设备实时数据及配置列表
   */
  batchGetRealtimeWithConfig(
    deviceCodes: string[]
  ): Promise<{ data: DeviceRealtimeWithConfig[] }> {
    return request({
      url: '/v2/devices/batch-realtime-with-config',
      method: 'POST',
      data: deviceCodes
    })
  },

  /**
   * 分页获取设备实时数据及配置
   * @param params 分页查询参数
   * @returns 分页数据
   */
  getPaginatedRealtimeWithConfig(
    params: PaginatedRealtimeDataRequest
  ): Promise<{ data: PaginatedRealtimeDataResponse }> {
    return request({
      url: '/v2/devices/realtime-paginated',
      method: 'POST',
      data: params
    })
  },

  /**
   * 创建设备字段配置
   */
  create(data: Partial<DeviceField>) {
    return request({
      url: '/v2/device/config/device-fields',
      method: 'post',
      data
    })
  },

  /**
   * 更新设备字段配置
   */
  update(fieldId: number, data: Partial<DeviceField>) {
    return request({
      url: `/v2/device/config/device-fields/${fieldId}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除设备字段配置
   */
  delete(fieldId: number) {
    return request({
      url: `/v2/device/config/device-fields/${fieldId}`,
      method: 'delete'
    })
  },

  /**
   * 清除字段配置缓存
   */
  clearCache() {
    return request({
      url: '/v2/device/config/device-fields/cache/clear',
      method: 'post'
    })
  },

  /**
   * 从 TDengine 超级表获取字段列表
   */
  getTDengineFields(deviceTypeCode: string) {
    return request({
      url: `/v2/tdengine/stable-fields/${deviceTypeCode}`,
      method: 'get'
    })
  },

  /**
   * 获取字段配置建议
   */
  getFieldSuggestions(deviceTypeCode: string) {
    return request({
      url: `/v2/tdengine/field-suggestions/${deviceTypeCode}`,
      method: 'get'
    })
  },

  /**
   * 获取指定设备类型的所有字段配置（包括监测和非监测字段）
   * @param deviceTypeCode 设备类型代码
   * @returns 所有字段配置列表
   */
  getByDeviceType(deviceTypeCode: string): Promise<{ success: boolean; data: DeviceField[] }> {
    return request({
      url: `/v2/device/config/device-fields/${deviceTypeCode}`,
      method: 'GET'
    })
  }
}

export default deviceFieldApi
