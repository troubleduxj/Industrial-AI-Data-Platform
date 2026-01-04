/**
 * 工业AI数据平台 API v4 - 资产管理
 */
import { request } from '@/utils/http'

const BASE_URL = '/v4/assets'

export const assetApi = {
  // 获取资产列表
  getList: (params = {}) => request.get(`${BASE_URL}`, { params }),

  // 获取单个资产
  getById: (id) => request.get(`${BASE_URL}/${id}`),

  // 根据编码获取资产
  getByCode: (code) => request.get(`${BASE_URL}/code/${code}`),

  // 创建资产
  create: (data) => request.post(`${BASE_URL}`, data),

  // 更新资产
  update: (id, data) => request.put(`${BASE_URL}/${id}`, data),

  // 删除资产
  delete: (id) => request.delete(`${BASE_URL}/${id}`),

  // 批量删除资产
  batchDelete: (ids) => request.delete(`${BASE_URL}/batch`, { data: { ids } }),

  // 获取资产实时数据
  getRealtimeData: (id) => request.get(`${BASE_URL}/${id}/realtime`),

  // 获取资产历史数据
  getHistoryData: (id, params) => request.get(`${BASE_URL}/${id}/history`, { params }),
}
