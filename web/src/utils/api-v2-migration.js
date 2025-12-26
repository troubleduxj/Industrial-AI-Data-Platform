/**
 * API v2迁移工具
 * 帮助前端页面从v1 API平滑迁移到v2 API
 */

import { requestV2 } from '@/utils/http/v2-interceptors'

// v1到v2的API路径映射
const API_PATH_MAPPING = {
  // 认证管理
  'POST /auth/login': 'POST /api/v2/auth/login',
  'GET /auth/user': 'GET /api/v2/auth/user',
  'GET /auth/userinfo': 'GET /api/v2/auth/user',
  'GET /auth/user/apis': 'GET /api/v2/auth/user/apis',
  'GET /auth/user/menus': 'GET /api/v2/auth/user/menus',
  'POST /auth/logout': 'POST /api/v2/auth/logout',
  'POST /auth/change-password': 'POST /api/v2/auth/change-password',

  // 用户管理
  'GET /user/list': 'GET /api/v2/users',
  'GET /users': 'GET /api/v2/users',
  'POST /user/create': 'POST /api/v2/users/',
  'POST /users': 'POST /api/v2/users/',
  'PUT /user/update': 'PUT /api/v2/users/{id}',
  'PUT /users/{id}': 'PUT /api/v2/users/{id}',
  'DELETE /user/delete': 'DELETE /api/v2/users/{id}',
  'DELETE /users/{id}': 'DELETE /api/v2/users/{id}',
  'DELETE /users/batch': 'DELETE /api/v2/users/batch',
  'POST /user/reset_password': 'POST /api/v2/users/{id}/actions/reset-password',

  // 角色管理
  'GET /role/list': 'GET /api/v2/roles',
  'GET /roles': 'GET /api/v2/roles',
  'POST /role/create': 'POST /api/v2/roles',
  'POST /roles': 'POST /api/v2/roles',
  'PUT /role/update': 'PUT /api/v2/roles/{id}',
  'PUT /roles/{id}': 'PUT /api/v2/roles/{id}',
  'DELETE /role/delete': 'DELETE /api/v2/roles/{id}',
  'DELETE /roles/{id}': 'DELETE /api/v2/roles/{id}',
  'DELETE /roles/batch': 'DELETE /api/v2/roles/batch',

  // 菜单管理
  'GET /menu/list': 'GET /api/v2/menus',
  'GET /menus': 'GET /api/v2/menus',
  'POST /menu/create': 'POST /api/v2/menus',
  'POST /menus': 'POST /api/v2/menus',
  'PUT /menu/update': 'PUT /api/v2/menus/{id}',
  'PUT /menus/{id}': 'PUT /api/v2/menus/{id}',
  'DELETE /menu/delete': 'DELETE /api/v2/menus/{id}',
  'DELETE /menus/{id}': 'DELETE /api/v2/menus/{id}',
  'DELETE /menus/batch': 'DELETE /api/v2/menus/batch',

  // 部门管理
  'GET /dept/list': 'GET /api/v2/departments',
  'GET /departments': 'GET /api/v2/departments',
  'POST /dept/create': 'POST /api/v2/departments',
  'POST /departments': 'POST /api/v2/departments',
  'PUT /dept/update': 'PUT /api/v2/departments/{id}',
  'PUT /departments/{id}': 'PUT /api/v2/departments/{id}',
  'DELETE /dept/delete': 'DELETE /api/v2/departments/{id}',
  'DELETE /departments/{id}': 'DELETE /api/v2/departments/{id}',
  'DELETE /departments/batch': 'DELETE /api/v2/departments/batch',
}

/**
 * API路径转换器
 */
export class ApiPathConverter {
  constructor() {
    this.mapping = API_PATH_MAPPING
  }

  /**
   * 转换API路径到v2格式
   * @param {string} method - HTTP方法
   * @param {string} path - API路径
   * @param {Object} params - 路径参数
   * @returns {string} v2格式的API路径
   */
  convertPath(method, path, params = {}) {
    // 如果已经是v2路径，直接返回（避免重复转换）
    if (this.isV2Path(path)) {
      return this.replacePathParams(path, params)
    }

    const key = `${method.toUpperCase()} ${path}`
    let v2Path = this.mapping[key]

    if (!v2Path) {
      // 如果没有映射，尝试自动转换
      v2Path = this.autoConvertPath(path)
    }

    // 如果映射包含方法前缀，移除它
    if (v2Path && v2Path.includes(' ')) {
      v2Path = v2Path.split(' ')[1] || v2Path
    }

    // 替换路径参数
    return this.replacePathParams(v2Path, params)
  }

  /**
   * 自动转换路径
   * @param {string} path - 原始路径
   * @returns {string} 转换后的路径
   */
  autoConvertPath(path) {
    // 移除v1前缀并添加v2前缀
    let convertedPath = path.replace(/^\/api\/v1/, '/api/v2')

    // 如果路径不以/api/开头，添加v2前缀
    if (!convertedPath.startsWith('/api/')) {
      convertedPath = convertedPath.startsWith('/')
        ? `/api/v2${convertedPath}`
        : `/api/v2/${convertedPath}`
    }

    return convertedPath
  }

  /**
   * 替换路径参数
   * @param {string} path - 包含参数占位符的路径
   * @param {Object} params - 路径参数
   * @returns {string} 替换参数后的路径
   */
  replacePathParams(path, params = {}) {
    let resultPath = path

    // 替换路径参数
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        resultPath = resultPath.replace(`{${key}}`, encodeURIComponent(value))
      }
    })

    return resultPath
  }

  /**
   * 检查路径是否已经是v2格式
   * @param {string} path - API路径
   * @returns {boolean}
   */
  isV2Path(path) {
    return path && path.startsWith('/api/v2/')
  }
}

/**
 * 请求参数格式化器
 */
export class RequestFormatter {
  /**
   * 格式化分页参数
   * @param {Object} params - 原始参数
   * @returns {Object} 格式化后的参数
   */
  formatPagination(params) {
    const formatted = { ...params }

    // v2 API统一使用page和page_size
    if (params.page_num !== undefined) {
      formatted.page = params.page_num
      delete formatted.page_num
    }

    if (params.pageSize !== undefined) {
      formatted.page_size = params.pageSize
      delete formatted.pageSize
    }

    return formatted
  }

  /**
   * 格式化搜索参数
   * @param {Object} params - 原始参数
   * @returns {Object} 格式化后的参数
   */
  formatSearch(params) {
    const formatted = { ...params }

    if (params.keyword) {
      formatted.search = params.keyword
      delete formatted.keyword
    }

    return formatted
  }

  /**
   * 综合格式化请求参数
   * @param {Object} params - 原始参数
   * @returns {Object} 格式化后的参数
   */
  format(params) {
    let formatted = { ...params }
    formatted = this.formatPagination(formatted)
    formatted = this.formatSearch(formatted)
    return formatted
  }
}

/**
 * 响应数据适配器
 */
export class ResponseAdapter {
  /**
   * 适配列表响应数据
   * @param {Object} response - v2响应数据
   * @returns {Object} 适配后的数据
   */
  adaptListResponse(response) {
    if (!response || typeof response !== 'object') {
      return this.createEmptyListResponse()
    }

    const success = response.success !== undefined ? response.success : true
    const code = response.code || (success ? 200 : 500)
    const message = response.message || (success ? 'Success' : 'Error')
    const data = response.data || []
    const meta = response.meta || {}

    // 确保数据是数组格式
    let listData = []
    if (Array.isArray(data)) {
      listData = data
    } else if (data && typeof data === 'object') {
      // 检查多种可能的数据字段名
      if (Array.isArray(data.items)) {
        listData = data.items
      } else if (Array.isArray(data.records)) {
        listData = data.records
      } else if (Array.isArray(data.list)) {
        listData = data.list
      } else if (Array.isArray(data.data)) {
        listData = data.data
      }
    }

    // 提取分页信息
    let paginationInfo = {}
    if (data && typeof data === 'object' && data.pagination) {
      paginationInfo = data.pagination
    } else {
      paginationInfo = meta
    }

    const total = paginationInfo.total || listData.length
    const page = Math.max(1, paginationInfo.page || 1)
    const pageSize = Math.max(1, paginationInfo.page_size || paginationInfo.pageSize || 20)
    const totalPages = Math.max(
      1,
      paginationInfo.total_pages || paginationInfo.totalPages || Math.ceil(total / pageSize)
    )

    return {
      code,
      msg: message,
      data: listData,
      success,
      message,
      meta: {
        total,
        page,
        pageSize,
        totalPages,
        ...meta,
      },
      total,
      page,
      pageSize,
      totalPages,
    }
  }

  /**
   * 适配详情响应数据
   * @param {Object} response - v2响应数据
   * @returns {Object} 适配后的数据
   */
  adaptDetailResponse(response) {
    if (!response || typeof response !== 'object') {
      return this.createEmptyDetailResponse()
    }

    const success = response.success !== undefined ? response.success : true
    const code = response.code || (success ? 200 : 500)
    const message = response.message || (success ? 'Success' : 'Error')
    const data = response.data || {}

    return {
      code,
      msg: message,
      data,
      success,
      message,
    }
  }

  /**
   * 创建空的列表响应
   * @returns {Object}
   */
  createEmptyListResponse() {
    return {
      code: 200,
      msg: 'Success',
      data: [],
      success: true,
      message: 'Success',
      meta: {
        total: 0,
        page: 1,
        pageSize: 20,
        totalPages: 0,
      },
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    }
  }

  /**
   * 创建空的详情响应
   * @returns {Object}
   */
  createEmptyDetailResponse() {
    return {
      code: 200,
      msg: 'Success',
      data: {},
      success: true,
      message: 'Success',
    }
  }
}

/**
 * 页面API助手
 */
export class PageApiHelper {
  constructor() {
    this.pathConverter = new ApiPathConverter()
    this.requestFormatter = new RequestFormatter()
    this.responseAdapter = new ResponseAdapter()
  }

  /**
   * 创建系统管理API
   * @returns {Object} 系统API集合
   */
  createSystemApis() {
    return {
      users: this.createResourceApi('users'),
      roles: this.createResourceApi('roles'),
      menus: this.createResourceApi('menus'),
      departments: this.createResourceApi('departments'),
      apis: this.createResourceApi('apis'),
      auditLogs: this.createResourceApi('audit-logs'),
      dictTypes: this.createResourceApi('dict-types'),
      dictData: this.createResourceApi('dict-data'),
      systemParams: this.createResourceApi('system-params'),
      apiGroups: this.createResourceApi('api-groups'),
    }
  }

  /**
   * 创建认证API
   * @returns {Object} 认证API集合
   */
  createAuthApis() {
    return {
      login: (data) => requestV2.post('/auth/login', data),
      getUserInfo: () => requestV2.get('/auth/user'),
      changePassword: (data) => requestV2.post('/auth/change-password', data),
      logout: () => requestV2.post('/auth/logout'),
      getUserApis: () => requestV2.get('/auth/user/apis'),
      getUserMenus: () => requestV2.get('/auth/user/menus'),
    }
  }

  /**
   * 创建资源API
   * @param {string} resource - 资源名称
   * @returns {Object} 资源API集合
   */
  createResourceApi(resource) {
    const basePath = `/${resource}`

    return {
      list: async (params = {}) => {
        const formattedParams = this.requestFormatter.format(params)
        // 不添加斜杠，直接使用basePath匹配后端路由定义
        const response = await requestV2.get(`${basePath}`, { params: formattedParams })
        // 使用ResponseAdapter处理响应数据
        return this.responseAdapter.adaptListResponse(response)
      },

      get: (id, params = {}) => {
        const formattedParams = this.requestFormatter.format(params)
        return requestV2.get(`${basePath}/${id}`, { params: formattedParams })
      },

      create: (data = {}) => {
        // 不添加斜杠，直接使用basePath匹配后端路由定义
        return requestV2.post(`${basePath}`, data)
      },

      update: (id, data = {}) => {
        return requestV2.put(`${basePath}/${id}`, data)
      },

      delete: (id) => {
        return requestV2.delete(`${basePath}/${id}`)
      },

      batchCreate: (items) => {
        return requestV2.post(`${basePath}/batch`, { items })
      },

      batchUpdate: (items) => {
        return requestV2.put(`${basePath}/batch`, { items })
      },

      batchDelete: (ids) => {
        return requestV2.delete(`${basePath}/batch`, { data: { ids } })
      },

      search: (params) => {
        const formattedParams = this.requestFormatter.format(params)
        return requestV2.get(`${basePath}/search`, { params: formattedParams })
      },

      // 特殊方法
      getTree: (params = {}) => {
        const formattedParams = this.requestFormatter.format(params)
        return requestV2.get(`${basePath}/tree`, { params: formattedParams })
      },

      getPermissions: (id, params = {}) => {
        const formattedParams = this.requestFormatter.format(params)
        return requestV2.get(`${basePath}/${id}/permissions`, { params: formattedParams })
      },

      assignPermissions: (id, data = {}) => {
        return requestV2.put(`${basePath}/${id}/permissions`, data)
      },

      getUsers: (id, params = {}) => {
        const formattedParams = this.requestFormatter.format(params)
        return requestV2.get(`${basePath}/${id}/users`, { params: formattedParams })
      },

      resetPassword: (pathParams, data = {}) => {
        return requestV2.post(`${basePath}/${pathParams.id}/actions/reset-password`, data)
      },

      refresh: () => {
        return requestV2.post(`${basePath}/refresh`)
      },

      all: () => {
        return requestV2.get(`${basePath}/all`)
      },

      moveApis: (groupId, apiIds) => {
        return requestV2.post(`${basePath}/${groupId}/apis`, { api_ids: apiIds })
      },
    }
  }
}

/**
 * API v2客户端
 */
export class ApiV2Client {
  constructor() {
    this.pathConverter = new ApiPathConverter()
    this.requestFormatter = new RequestFormatter()
    this.responseAdapter = new ResponseAdapter()
  }

  /**
   * GET请求
   * @param {string} path - API路径
   * @param {Object} params - 查询参数
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async get(path, params = {}, options = {}) {
    const formattedParams = this.requestFormatter.format(params)
    // 如果路径以/开头但不是完整的API路径，直接使用；否则进行转换
    const finalPath =
      path.startsWith('/') && !path.startsWith('/api/')
        ? path
        : this.pathConverter.convertPath('GET', path)

    const response = await requestV2.get(finalPath, { params: formattedParams, ...options })

    if (options.isList) {
      return this.responseAdapter.adaptListResponse(response)
    } else {
      return this.responseAdapter.adaptDetailResponse(response)
    }
  }

  /**
   * POST请求
   * @param {string} path - API路径
   * @param {Object} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async post(path, data = {}, options = {}) {
    const finalPath =
      path.startsWith('/') && !path.startsWith('/api/')
        ? path
        : this.pathConverter.convertPath('POST', path)
    const response = await requestV2.post(finalPath, data, options)
    return this.responseAdapter.adaptDetailResponse(response)
  }

  /**
   * PUT请求
   * @param {string} path - API路径
   * @param {Object} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async put(path, data = {}, options = {}) {
    const finalPath =
      path.startsWith('/') && !path.startsWith('/api/')
        ? path
        : this.pathConverter.convertPath('PUT', path)
    const response = await requestV2.put(finalPath, data, options)
    return this.responseAdapter.adaptDetailResponse(response)
  }

  /**
   * DELETE请求
   * @param {string} path - API路径
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async delete(path, options = {}) {
    const finalPath =
      path.startsWith('/') && !path.startsWith('/api/')
        ? path
        : this.pathConverter.convertPath('DELETE', path)
    const response = await requestV2.delete(finalPath, options)
    return this.responseAdapter.adaptDetailResponse(response)
  }
}

/**
 * 创建系统管理API
 * @returns {Object} 系统API集合
 */
export function createSystemApis() {
  return {
    users: pageApiHelper.createResourceApi('users'),
    roles: pageApiHelper.createResourceApi('roles'),
    menus: pageApiHelper.createResourceApi('menus'),
    departments: pageApiHelper.createResourceApi('departments'),
    apis: pageApiHelper.createResourceApi('apis'),
    auditLogs: pageApiHelper.createResourceApi('audit-logs'),
    dictTypes: pageApiHelper.createResourceApi('dict-types'),
    dictData: pageApiHelper.createResourceApi('dict-data'),
    systemParams: pageApiHelper.createResourceApi('system-params'),
    apiGroups: pageApiHelper.createResourceApi('api-groups'),
  }
}

/**
 * 创建设备管理API
 * @returns {Object} 设备API集合
 */
export function createDeviceApis() {
  const basePath = '/devices'

  return {
    devices: {
      list: (params = {}) => requestV2.get(basePath, { params }),
      get: (id, params = {}) => requestV2.get(`${basePath}/${id}`, { params }),
      create: (data = {}) => requestV2.post(basePath, data),
      update: (id, data = {}) => requestV2.put(`${basePath}/${id}`, data),
      delete: (id) => requestV2.delete(`${basePath}/${id}`),
      getData: (pathParams, params = {}) =>
        requestV2.get(`${basePath}/${pathParams.id}/data`, { params }),
      getStatus: (pathParams, params = {}) =>
        requestV2.get(`${basePath}/${pathParams.id}/status`, { params }),
      getMonitoring: (pathParams, params = {}) =>
        requestV2.get(`${basePath}/${pathParams.id}/monitoring`, { params }),
      getStatistics: (params = {}) => requestV2.get(`${basePath}/statistics`, { params }),
      getHistoryData: (pathParams, params = {}) =>
        requestV2.get(`${basePath}/${pathParams.id}/history`, { params }),
      getRealtimeMonitoring: (params = {}) =>
        // 修正：后端对应接口为 /monitoring/realtime
        requestV2.get(`${basePath}/monitoring/realtime`, { params }),
      getMonitoringSummary: (params = {}) =>
        requestV2.get(`${basePath}/monitoring/summary`, { params }),
      getMonitoringOverview: (params = {}) =>
        requestV2.get(`${basePath}/monitoring/overview`, { params }),
      getWeldingDailyReportSummary: (params = {}) =>
        requestV2.get(`${basePath}/statistics/daily-report/summary`, { params }),
      getWeldingDailyReportDetail: (params = {}) =>
        requestV2.get(`${basePath}/statistics/daily-report/detail`, { params }),
      getAlarmCategorySummary: (params = {}) =>
        requestV2.get(`${basePath}/statistics/dashboard/alarm-category-summary`, { params }),
      getAlarmRecordTop: (params = {}) =>
        requestV2.get(`${basePath}/statistics/dashboard/alarm-record-top`, { params }),
      getOnlineWeldingRateStatistics: (params = {}) =>
        requestV2.get(`${basePath}/statistics/dashboard/online-welding-rate`, { params }),
      getRealtimeDeviceStatus: (params = {}) =>
        requestV2.get(`${basePath}/statistics/realtime/device-status`, { params }),
      getAlarms: (params = {}) => requestV2.get(`${basePath}/alarms`, { params }),
      getRealtimeWithConfig: (deviceCode, params = {}) =>
        requestV2.get(`${basePath}/${deviceCode}/realtime-with-config`, { params }),
      batchCreate: (items) => requestV2.post(`${basePath}/batch`, { items }),
      batchUpdate: (items) => requestV2.put(`${basePath}/batch`, { items }),
      batchDelete: (ids) => requestV2.delete(`${basePath}/batch`, { data: { ids } }),
      search: (params) => requestV2.get(`${basePath}/search`, { params }),
    },

    deviceTypes: {
      list: (params = {}) => requestV2.get(`${basePath}/types`, { params }),
      get: (typeCode, params = {}) => requestV2.get(`${basePath}/types/${typeCode}`, { params }),
      create: (data = {}) => requestV2.post(`${basePath}/types`, data),
      update: (typeCode, data = {}) => requestV2.put(`${basePath}/types/${typeCode}`, data),
      delete: (typeCode) => requestV2.delete(`${basePath}/types/${typeCode}`),
      batchCreate: (items) => requestV2.post(`${basePath}/types/batch`, { items }),
      batchUpdate: (items) => requestV2.put(`${basePath}/types/batch`, { items }),
      batchDelete: (ids) => requestV2.delete(`${basePath}/types/batch`, { data: { ids } }),
      search: (params) => requestV2.get(`${basePath}/types/search`, { params }),
    },

    maintenance: {
      list: (params = {}) => requestV2.get(`${basePath}/maintenance`, { params }),
      get: (id, params = {}) => requestV2.get(`${basePath}/maintenance/${id}`, { params }),
      create: (data = {}) => requestV2.post(`${basePath}/maintenance`, data),
      update: (id, data = {}) => requestV2.put(`${basePath}/maintenance/${id}`, data),
      delete: (id) => requestV2.delete(`${basePath}/maintenance/${id}`),
      getSchedule: (params = {}) => requestV2.get(`${basePath}/maintenance/schedule`, { params }),
      batchCreate: (items) => requestV2.post(`${basePath}/maintenance/batch`, { items }),
      batchUpdate: (items) => requestV2.put(`${basePath}/maintenance/batch`, { items }),
      batchDelete: (ids) => requestV2.delete(`${basePath}/maintenance/batch`, { data: { ids } }),
      search: (params) => requestV2.get(`${basePath}/maintenance/search`, { params }),
    },

    processes: {
      list: (params = {}) => requestV2.get(`${basePath}/processes`, { params }),
      get: (id, params = {}) => requestV2.get(`${basePath}/processes/${id}`, { params }),
      create: (data = {}) => requestV2.post(`${basePath}/processes`, data),
      update: (id, data = {}) => requestV2.put(`${basePath}/processes/${id}`, data),
      delete: (id) => requestV2.delete(`${basePath}/processes/${id}`),
      execute: (pathParams, data = {}) =>
        requestV2.post(`${basePath}/processes/${pathParams.id}/execute`, data),
      batchCreate: (items) => requestV2.post(`${basePath}/processes/batch`, { items }),
      batchUpdate: (items) => requestV2.put(`${basePath}/processes/batch`, { items }),
      batchDelete: (ids) => requestV2.delete(`${basePath}/processes/batch`, { data: { ids } }),
      search: (params) => requestV2.get(`${basePath}/processes/search`, { params }),
    },

    alarms: {
      getStatistics: (params = {}) => requestV2.get('/alarms/statistics', { params }),
      handle: (alarmId, data = {}) => requestV2.put(`/alarms/${alarmId}/handle`, data),
      acknowledge: (alarmId, data = {}) => requestV2.post(`/alarms/${alarmId}/acknowledge`, data),
      batchHandle: (data = {}) => requestV2.put('/alarms/batch-handle', data),
    },
  }
}

// 创建全局实例
export const pathConverter = new ApiPathConverter()
export const requestFormatter = new RequestFormatter()
export const responseAdapter = new ResponseAdapter()
export const pageApiHelper = new PageApiHelper()
export const apiV2Client = new ApiV2Client()

// 便捷函数
export function convertApiPath(method, path, params) {
  return pathConverter.convertPath(method, path, params)
}

export function formatRequest(params) {
  return requestFormatter.format(params)
}

export function adaptListResponse(response) {
  return responseAdapter.adaptListResponse(response)
}

export function adaptDetailResponse(response) {
  return responseAdapter.adaptDetailResponse(response)
}

export default {
  ApiPathConverter,
  RequestFormatter,
  ResponseAdapter,
  PageApiHelper,
  ApiV2Client,
  pathConverter,
  requestFormatter,
  responseAdapter,
  pageApiHelper,
  apiV2Client,
  createSystemApis,
  createDeviceApis,
  convertApiPath,
  formatRequest,
  adaptListResponse,
  adaptDetailResponse,
}
