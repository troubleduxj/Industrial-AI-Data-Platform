/**
 * API v2版本接口
 * 使用标准化响应格式和增强的错误处理
 */
import { requestV2 } from '@/utils/http/v2-interceptors'

// v2版本的基础API
export const apiV2 = {
  // 认证相关
  login: (data) => requestV2.post('/auth/login', data, { noNeedToken: true }),
  getUserInfo: () => requestV2.get('/auth/userinfo'),
  getUserMenu: () => requestV2.get('/base/usermenu'),
  getUserApi: () => requestV2.get('/base/userapi'),

  // 用户管理 - v2版本
  getUserList: (params = {}) => requestV2.get('/users', { params }),
  getUserById: (id) => requestV2.get(`/users/${id}`),
  createUser: (data = {}) => requestV2.post('/users', data),
  updateUser: (id, data = {}) => requestV2.put(`/users/${id}`, data),
  deleteUser: (id) => requestV2.delete(`/users/${id}`),

  // 健康检查 - v2版本
  healthCheck: () => requestV2.get('/health'),
  getVersionInfo: () => requestV2.get('/health/version'),

  // API文档相关
  getApiChangelog: (params = {}) => requestV2.get('/docs/changelog', { params }),
  getBreakingChanges: (params = {}) => requestV2.get('/docs/changelog/breaking', { params }),
  getApiVersions: () => requestV2.get('/docs/versions'),
  getApiSchema: () => requestV2.get('/docs/schema'),
  getApiExamples: () => requestV2.get('/docs/examples'),
}

// 兼容性包装器 - 将v2响应格式转换为v1格式
export function wrapV1Compatible(apiFunction) {
  return async (...args) => {
    try {
      const response = await apiFunction(...args)

      // 如果是v2格式的响应，转换为v1格式
      if (response.success !== undefined) {
        return {
          code: response.success ? 200 : response.code,
          msg: response.message,
          data: response.data,
          // 保留v2的额外信息
          _v2: {
            success: response.success,
            timestamp: response.timestamp,
            total: response.total,
            page: response.page,
            page_size: response.page_size,
            total_pages: response.total_pages,
          },
        }
      }

      return response
    } catch (error) {
      // 将v2错误格式转换为v1格式
      throw {
        code: error.code || 500,
        msg: error.message || 'Unknown error',
        data: null,
        _v2: {
          details: error.details,
        },
      }
    }
  }
}

// 创建兼容v1格式的API
export const apiV2Compatible = {
  getUserList: wrapV1Compatible(apiV2.getUserList),
  getUserById: wrapV1Compatible(apiV2.getUserById),
  createUser: wrapV1Compatible(apiV2.createUser),
  updateUser: wrapV1Compatible(apiV2.updateUser),
  deleteUser: wrapV1Compatible(apiV2.deleteUser),
  getUserApi: wrapV1Compatible(apiV2.getUserApi),
  healthCheck: wrapV1Compatible(apiV2.healthCheck),
}

export default apiV2
