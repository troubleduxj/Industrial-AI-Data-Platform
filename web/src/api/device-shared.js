/**
 * 设备管理 API - Shared 层适配器
 * 使用 shared API 层，保持与现有 API 接口兼容
 */

import sharedApi from './shared'

// ========== 设备类型 API ==========

export const deviceTypeApi = {
  // 获取设备类型列表
  list: async (params = {}) => {
    const result = await sharedApi.device.getDeviceTypes(params)
    // 透传 meta 和 total 信息，防止分页丢失
    return { 
      data: result.data,
      meta: result.meta,
      total: result.total ?? result.meta?.total
    }
  },

  // 获取设备类型详情
  get: async (typeCode, params = {}) => {
    const result = await sharedApi.device.getDeviceType(typeCode)
    return { data: result.data }
  },

  // 创建设备类型
  create: async (data = {}) => {
    const result = await sharedApi.device.createDeviceType(data)
    return { data: result.data }
  },

  // 更新设备类型
  update: async (typeCodeOrData, data = {}) => {
    let typeCode, updateData

    if (typeof typeCodeOrData === 'object' && typeCodeOrData.type_code) {
      typeCode = typeCodeOrData.type_code
      updateData = { ...typeCodeOrData }
      delete updateData.type_code
    } else {
      typeCode = typeCodeOrData
      updateData = data
    }

    const result = await sharedApi.device.updateDeviceType(typeCode, updateData)
    return { data: result.data }
  },

  // 删除设备类型
  delete: async (typeCodeOrData, params = {}) => {
    const typeCode =
      typeof typeCodeOrData === 'object' && typeCodeOrData.type_code
        ? typeCodeOrData.type_code
        : typeCodeOrData

    const result = await sharedApi.device.deleteDeviceType(typeCode, params)
    return { data: result.data }
  },

  // 批量操作
  batchCreate: async (items) => {
    const results = await Promise.all(items.map((item) => sharedApi.device.createDeviceType(item)))
    return { data: results.map((r) => r.data) }
  },

  batchUpdate: async (items) => {
    const results = await Promise.all(
      items.map((item) => sharedApi.device.updateDeviceType(item.type_code, item))
    )
    return { data: results.map((r) => r.data) }
  },

  batchDelete: async (items, params = {}) => {
    // 优先使用新版批量删除接口 (基于ID)
    const ids = items.map((item) => (typeof item === 'object' ? item.id : item))
    const result = await sharedApi.device.batchDeleteDeviceTypes(ids, params)
    return { data: result.data }
  },

  // 搜索
  search: async (params) => {
    const result = await sharedApi.device.searchDevices(params.keyword, params)
    return { data: result.data }
  },
}

// ========== 设备管理 API ==========

export const deviceApi = {
  // 获取设备列表
  list: async (params = {}) => {
    const result = await sharedApi.device.getDevices(params)
    // 透传 meta 和 total 信息，防止分页丢失
    return { 
      data: result.data,
      meta: result.meta,
      total: result.total ?? result.meta?.total
    }
  },

  // 获取设备详情
  get: async (id) => {
    const result = await sharedApi.device.getDevice(id)
    return { data: result.data }
  },

  // 根据设备编码获取
  getByCode: async (deviceCode) => {
    const result = await sharedApi.device.getDeviceByCode(deviceCode)
    return { data: result.data }
  },

  // 创建设备
  create: async (data) => {
    const result = await sharedApi.device.createDevice(data)
    return { data: result.data }
  },

  // 更新设备
  update: async (id, data) => {
    const result = await sharedApi.device.updateDevice(id, data)
    return { data: result.data }
  },

  // 删除设备
  delete: async (id) => {
    const result = await sharedApi.device.deleteDevice(id)
    return { data: result.data }
  },

  // 获取关联统计
  getRelatedCounts: async (id) => {
    const result = await sharedApi.device.getRelatedCounts(id)
    return { data: result.data }
  },

  // 批量删除
  batchDelete: async (ids) => {
    const result = await sharedApi.device.batchDeleteDevices(ids)
    return { data: result.data }
  },

  // 获取设备统计
  getStats: async () => {
    const result = await sharedApi.device.getDeviceStats()
    return { data: result.data }
  },

  // 搜索设备
  search: async (params) => {
    const result = await sharedApi.device.searchDevices(params.keyword, params)
    return { data: result.data }
  },
}

// ========== 默认导出（兼容现有代码） ==========

export default {
  deviceTypeApi,
  deviceApi,

  // 简化导出
  ...deviceApi,
}

/**
 * 使用说明：
 *
 * 旧方式（保持兼容）：
 * import { deviceTypeApi, deviceApi } from '@/api/device-v2';
 *
 * 新方式（推荐）：
 * import { deviceTypeApi, deviceApi } from '@/api/device-shared';
 *
 * 或直接使用 shared：
 * import sharedApi from '@/api/shared';
 * await sharedApi.device.getDevices({ page: 1 });
 */
