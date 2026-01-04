/**
 * 设备管理 API - Shared 层适配器
 * 使用 V4 API 层，保持与现有 API 接口兼容
 */

import { assetApi, categoryApi } from './v4'

// ========== 设备类型 API (映射到 V4 Category API) ==========

export const deviceTypeApi = {
  // 获取设备类型列表
  list: async (params = {}) => {
    // V4 categoryApi.getList 对应 deviceTypeApi.list
    const response = await categoryApi.getList(params)
    // 适配返回值结构
    return { 
      success: true,
      data: response.data || response.items || [],
      meta: response.meta || {},
      total: response.total ?? response.meta?.total ?? 0
    }
  },

  // 获取设备类型详情
  get: async (typeCode, params = {}) => {
    // V4 使用 ID 获取，这里假设 typeCode 可以作为 ID 或者需要通过 list 搜索
    // 如果 typeCode 是数字 ID，直接使用 getById
    // 否则可能需要搜索。暂时假设 typeCode 就是 ID
    const response = await categoryApi.getById(typeCode)
    return { success: true, data: response.data || response }
  },

  // 创建设备类型
  create: async (data = {}) => {
    const response = await categoryApi.create(data)
    return { success: true, data: response.data || response }
  },

  // 更新设备类型
  update: async (typeCodeOrData, data = {}) => {
    let id, updateData

    if (typeof typeCodeOrData === 'object' && (typeCodeOrData.id || typeCodeOrData.type_code)) {
      id = typeCodeOrData.id || typeCodeOrData.type_code
      updateData = { ...typeCodeOrData }
      delete updateData.type_code
      delete updateData.id
    } else {
      id = typeCodeOrData
      updateData = data
    }

    const response = await categoryApi.update(id, updateData)
    return { success: true, data: response.data || response }
  },

  // 删除设备类型
  delete: async (typeCodeOrData, params = {}) => {
    const id =
      typeof typeCodeOrData === 'object' && (typeCodeOrData.id || typeCodeOrData.type_code)
        ? (typeCodeOrData.id || typeCodeOrData.type_code)
        : typeCodeOrData

    const response = await categoryApi.delete(id)
    return { success: true, data: response.data || response }
  },

  // 批量操作 - V4 暂未完全对应，部分可能需要循环调用
  batchCreate: async (items) => {
    const results = await Promise.all(items.map((item) => categoryApi.create(item)))
    return { success: true, data: results.map((r) => r.data || r) }
  },

  batchUpdate: async (items) => {
    const results = await Promise.all(
      items.map((item) => categoryApi.update(item.id || item.type_code, item))
    )
    return { success: true, data: results.map((r) => r.data || r) }
  },

  batchDelete: async (items, params = {}) => {
    const ids = items.map((item) => (typeof item === 'object' ? (item.id || item.type_code) : item))
    // V4 暂无 batchDelete for categories，循环调用
    const results = await Promise.all(ids.map(id => categoryApi.delete(id)))
    return { success: true, data: results }
  },

  // 搜索 - V4 getList 支持 search 参数
  search: async (params) => {
    const response = await categoryApi.getList(params)
    return { success: true, data: response.data || response.items || [] }
  },
}

// ========== 设备管理 API (映射到 V4 Asset API) ==========

export const deviceApi = {
  // 获取设备列表
  list: async (params = {}) => {
    const response = await assetApi.getList(params)
    return { 
      data: response.data || response.items || [],
      meta: response.meta || {},
      total: response.total ?? response.meta?.total ?? 0
    }
  },

  // 获取设备详情
  get: async (id) => {
    const response = await assetApi.getById(id)
    return { data: response.data || response }
  },

  // 根据设备编码获取
  getByCode: async (deviceCode) => {
    const response = await assetApi.getByCode(deviceCode)
    return { data: response.data || response }
  },

  // 创建设备
  create: async (data) => {
    const response = await assetApi.create(data)
    return { data: response.data || response }
  },

  // 更新设备
  update: async (id, data) => {
    const response = await assetApi.update(id, data)
    return { data: response.data || response }
  },

  // 删除设备
  delete: async (id) => {
    const response = await assetApi.delete(id)
    return { data: response.data || response }
  },

  // 获取关联统计 - V4 可能暂无直接对应，先返回空或模拟
  getRelatedCounts: async (id) => {
    // 暂时返回空对象，避免报错
    return { data: {} }
  },

  // 批量删除
  batchDelete: async (ids) => {
    const response = await assetApi.batchDelete(ids)
    return { data: response.data || response }
  },

  // 获取设备统计 - V4 可能暂无直接对应
  getStats: async () => {
    return { data: {} }
  },

  // 搜索设备
  search: async (params) => {
    const response = await assetApi.getList({ ...params, search: params.keyword })
    return { data: response.data || response.items || [] }
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
