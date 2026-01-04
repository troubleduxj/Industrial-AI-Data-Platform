/**
 * 工业AI数据平台 API v4 - 信号定义管理
 */
import { request } from '@/utils/http'

const BASE_URL = '/api/v4/signals'

export const signalApi = {
  // 获取信号列表
  getList: (params = {}) => request.get(`${BASE_URL}`, { params }),

  // 获取单个信号
  getById: (id) => request.get(`${BASE_URL}/${id}`),

  // 创建信号
  create: (data) => request.post(`${BASE_URL}`, data),

  // 更新信号
  update: (id, data) => request.put(`${BASE_URL}/${id}`, data),

  // 删除信号
  delete: (id) => request.delete(`${BASE_URL}/${id}`),

  // 批量更新排序
  updateOrder: (orders) => request.put(`${BASE_URL}/order`, { orders }),
}
