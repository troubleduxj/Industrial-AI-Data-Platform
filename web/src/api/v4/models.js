/**
 * 工业AI数据平台 API v4 - AI模型管理
 */
import { request } from '@/utils/http'

const BASE_URL = '/api/v4/models'

export const modelApi = {
  // 获取模型列表
  getList: (params = {}) => request.get(`${BASE_URL}`, { params }),

  // 获取单个模型
  getById: (id) => request.get(`${BASE_URL}/${id}`),

  // 注册模型
  register: (data) => request.post(`${BASE_URL}`, data),

  // 更新模型
  update: (id, data) => request.put(`${BASE_URL}/${id}`, data),

  // 删除模型
  delete: (id) => request.delete(`${BASE_URL}/${id}`),

  // 部署模型
  deploy: (id) => request.post(`${BASE_URL}/${id}/deploy`),

  // 获取模型版本列表
  getVersions: (modelId) => request.get(`${BASE_URL}/${modelId}/versions`),

  // 创建模型版本
  createVersion: (data) => request.post(`/api/v4/versions`, data),

  // 激活模型版本
  activateVersion: (versionId) => request.post(`/api/v4/versions/${versionId}/activate`),

  // 验证模型版本
  validateVersion: (versionId) => request.post(`/api/v4/versions/${versionId}/validate`),

  // 归档模型版本
  archiveVersion: (versionId) => request.post(`/api/v4/versions/${versionId}/archive`),
}
