/**
 * 工业AI数据平台 API v4 - 资产类别管理
 */
import { request } from '@/utils/http'

const BASE_URL = '/v4/categories'

export const categoryApi = {
  // 获取类别列表
  getList: (params = {}) => request.get(`${BASE_URL}`, { params }),

  // 获取单个类别
  getById: (id) => request.get(`${BASE_URL}/${id}`),

  // 根据编码获取类别
  getByCode: (code) => request.get(`${BASE_URL}/code/${code}`),

  // 创建类别
  create: (data) => request.post(`${BASE_URL}`, data),

  // 更新类别
  update: (id, data) => request.put(`${BASE_URL}/${id}`, data),

  // 删除类别
  delete: (id) => request.delete(`${BASE_URL}/${id}`),

  // 获取类别的信号定义
  getSignals: (categoryId) => request.get(`${BASE_URL}/${categoryId}/signals`),
}
