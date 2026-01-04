/**
 * 工艺管理 API (V2)
 * 从 device-v2.js 迁移而来
 */
import { requestV2 } from '@/utils/http/v2-interceptors'

const basePath = '/devices/processes'

export const processApi = {
  // 获取工艺列表
  list: (params = {}) => requestV2.get(`${basePath}`, { params }),

  // 获取工艺详情
  get: (id, params = {}) => requestV2.get(`${basePath}/${id}`, { params }),

  // 创建工艺
  create: (data = {}) => requestV2.post(`${basePath}`, data),

  // 更新工艺
  update: (id, data = {}) => requestV2.put(`${basePath}/${id}`, data),

  // 删除工艺
  delete: (id) => requestV2.delete(`${basePath}/${id}`),

  // 执行工艺
  execute: (id, data = {}) => requestV2.post(`${basePath}/${id}/execute`, data),

  // 批量操作
  batchCreate: (items) => requestV2.post(`${basePath}/batch`, { items }),
  
  batchUpdate: (items) => requestV2.put(`${basePath}/batch`, { items }),
  
  batchDelete: (ids) => requestV2.delete(`${basePath}/batch`, { data: { ids } }),

  // 高级搜索
  search: (params) => requestV2.get(`${basePath}/search`, { params }),
}

export default processApi
