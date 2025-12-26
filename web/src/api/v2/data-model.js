/**
 * 数据模型管理 API (v2)
 * 
 * 功能：
 * - 数据模型管理（CRUD）
 * - 字段定义管理
 * - 字段映射管理
 * - 动态模型生成
 * - 数据查询（实时、统计）
 * - 执行日志查询
 */

import { requestV2 } from '@/utils/http/v2-interceptors'

/**
 * 数据模型 API
 */
export const dataModelApi = {
  // ==================== 模型管理 ====================
  
  /**
   * 获取数据模型列表
   * @param {Object} params - 查询参数
   * @param {string} params.search - 搜索关键词
   * @param {string} params.device_type_code - 设备类型代码
   * @param {string} params.model_type - 模型类型(realtime/statistics/ai_analysis)
   * @param {boolean} params.is_active - 是否激活
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise}
   */
  getModels: (params = {}) => requestV2.get('/metadata/models', { params }),
  
  /**
   * 获取数据模型详情
   * @param {number} id - 模型ID
   * @returns {Promise}
   */
  getModel: (id) => requestV2.get(`/metadata/models/${id}`),
  
  /**
   * 通过代码获取数据模型
   * @param {string} code - 模型代码
   * @returns {Promise}
   */
  getModelByCode: (code) => requestV2.get(`/metadata/models/code/${code}`),
  
  /**
   * 创建数据模型
   * @param {Object} data - 模型数据
   * @returns {Promise}
   */
  createModel: (data) => requestV2.post('/metadata/models', data),
  
  /**
   * 更新数据模型
   * @param {number} id - 模型ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateModel: (id, data) => requestV2.put(`/metadata/models/${id}`, data),
  
  /**
   * 删除数据模型
   * @param {number} id - 模型ID
   * @returns {Promise}
   */
  deleteModel: (id) => requestV2.delete(`/metadata/models/${id}`),
  
  /**
   * 激活/停用数据模型
   * @param {number} id - 模型ID
   * @param {boolean} isActive - 是否激活
   * @returns {Promise}
   */
  activateModel: (id, isActive = true) => 
    requestV2.post(`/metadata/models/${id}/activate`, { is_active: isActive }),
  
  // ==================== 字段定义管理 ====================
  
  /**
   * 获取字段定义列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getFields: (params = {}) => requestV2.get('/metadata/fields', { params }),
  
  /**
   * 获取字段定义详情
   * @param {number} id - 字段ID
   * @returns {Promise}
   */
  getField: (id) => requestV2.get(`/metadata/fields/${id}`),
  
  /**
   * 创建字段定义
   * @param {Object} data - 字段数据
   * @returns {Promise}
   */
  createField: (data) => requestV2.post('/metadata/fields', data),
  
  /**
   * 更新字段定义
   * @param {number} id - 字段ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateField: (id, data) => requestV2.put(`/metadata/fields/${id}`, data),
  
  /**
   * 删除字段定义
   * @param {number} id - 字段ID
   * @returns {Promise}
   */
  deleteField: (id) => requestV2.delete(`/metadata/fields/${id}`),

  /**
   * 批量删除设备类型字段
   * @param {string} deviceTypeCode - 设备类型代码
   * @returns {Promise}
   */
  batchDeleteFields: (deviceTypeCode) => requestV2.delete(`/metadata/fields/batch/${deviceTypeCode}`),

  /**
   * 批量删除选中字段
   * @param {Array} ids - 字段ID列表
   * @returns {Promise}
   */
  batchDeleteFieldsByIds: (ids) => requestV2.post('/metadata/fields/batch-delete', { ids }),
  
  // ==================== 字段映射管理 ====================
  
  /**
   * 获取字段映射列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getMappings: (params = {}) => requestV2.get('/metadata/mappings', { params }),
  
  /**
   * 获取字段映射详情
   * @param {number} id - 映射ID
   * @returns {Promise}
   */
  getMapping: (id) => requestV2.get(`/metadata/mappings/${id}`),
  
  /**
   * 创建字段映射
   * @param {Object} data - 映射数据
   * @returns {Promise}
   */
  createMapping: (data) => requestV2.post('/metadata/mappings', data),
  
  /**
   * 更新字段映射
   * @param {number} id - 映射ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateMapping: (id, data) => requestV2.put(`/metadata/mappings/${id}`, data),
  
  /**
   * 删除字段映射
   * @param {number} id - 映射ID
   * @returns {Promise}
   */
  deleteMapping: (id) => requestV2.delete(`/metadata/mappings/${id}`),

  /**
   * 批量删除字段映射
   * @param {Array} ids - 映射ID列表
   * @returns {Promise}
   */
  batchDeleteMappingsByIds: (ids) => requestV2.post('/metadata/mappings/batch-delete', { ids }),
  
  // ==================== 动态模型生成 ====================
  
  /**
   * 生成动态Pydantic模型
   * @param {string} deviceTypeCode - 设备类型代码
   * @param {string} modelType - 模型类型
   * @returns {Promise}
   */
  generateModel: (deviceTypeCode, modelType) => 
    requestV2.post('/dynamic-models/generate', null, {
      params: { device_type_code: deviceTypeCode, model_type: modelType }
    }),
  
  /**
   * 获取字段信息（用于动态模型）
   * @param {string} deviceTypeCode - 设备类型代码
   * @param {string} modelType - 模型类型
   * @returns {Promise}
   */
  getFieldsInfo: (deviceTypeCode, modelType) => 
    requestV2.get('/dynamic-models/fields-info', {
      params: { device_type_code: deviceTypeCode, model_type: modelType }
    }),
  
  /**
   * 验证数据
   * @param {string} modelCode - 模型代码
   * @param {Object} data - 要验证的数据
   * @returns {Promise}
   */
  validateData: (modelCode, data) => 
    requestV2.post('/dynamic-models/validate', data, {
      params: { model_code: modelCode }
    }),
  
  /**
   * 清除模型缓存
   * @param {string} deviceTypeCode - 设备类型代码（可选）
   * @param {string} modelType - 模型类型（可选）
   * @returns {Promise}
   */
  clearCache: (deviceTypeCode = null, modelType = null) => 
    requestV2.delete('/dynamic-models/cache', {
      params: { device_type_code: deviceTypeCode, model_type: modelType }
    }),
  
  /**
   * 获取缓存统计
   * @returns {Promise}
   */
  getCacheStats: () => requestV2.get('/dynamic-models/cache/stats'),
  
  /**
   * 预览TDengine字段
   * @param {Object} params - 参数
   * @param {string} params.device_type_code - 设备类型代码
   * @returns {Promise}
   */
  previewTDengineFields: async (params) => {
    try {
      const response = await requestV2.get(`/tdengine/field-suggestions/${params.device_type_code}`)
      if (response.success) {
        // 转换数据格式以适配前端组件
        const { matched_fields, missing_fields, extra_fields, statistics } = response.data
        
        const fields = [
          ...missing_fields.map(f => ({ ...f, status: 'new' })),
          ...matched_fields.map(f => ({ ...f, status: 'exist' })),
          ...extra_fields.map(f => ({ ...f, status: 'invalid' }))
        ]
        
        return {
          success: true,
          data: {
            fields,
            total_fields: statistics.total_tdengine_fields,
            new_fields: statistics.missing_count,
            skip_fields: statistics.matched_count
          }
        }
      }
      return response
    } catch (error) {
      return { success: false, message: error.message }
    }
  },

  /**
   * 从TDengine同步字段
   * @param {Object} data - 同步数据
   * @param {string} data.device_type_code - 设备类型代码
   * @param {Array} data.field_codes - 字段代码列表
   * @returns {Promise}
   */
  syncFromTDengine: (data) => requestV2.post('/tdengine/sync-fields', data),

  // ==================== 数据查询 ====================
  
  /**
   * 实时数据查询
   * @param {Object} queryParams - 查询参数
   * @param {string} queryParams.model_code - 模型代码
   * @param {string} queryParams.device_code - 设备编码（可选）
   * @param {Object} queryParams.filters - 筛选条件
   * @param {number} queryParams.page - 页码
   * @param {number} queryParams.page_size - 每页数量
   * @returns {Promise}
   */
  queryRealtimeData: (queryParams) => 
    requestV2.post('/data/query/realtime', queryParams),
  
  /**
   * 统计数据查询
   * @param {Object} queryParams - 查询参数
   * @param {string} queryParams.model_code - 模型代码
   * @param {string} queryParams.device_code - 设备编码（可选）
   * @param {Object} queryParams.filters - 筛选条件
   * @param {string} queryParams.interval - 时间间隔
   * @param {Array} queryParams.group_by - 分组字段
   * @returns {Promise}
   */
  queryStatisticsData: (queryParams) => 
    requestV2.post('/data/query/statistics', queryParams),
  
  /**
   * 预览数据模型（快速查询）
   * @param {string} modelCode - 模型代码
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  previewModel: (modelCode, params = {}) => 
    requestV2.get(`/data/models/${modelCode}/preview`, { params }),
  
  /**
   * 获取可用模型列表（用于数据查询）
   * @param {Object} params - 筛选参数
   * @returns {Promise}
   */
  getAvailableModels: (params = {}) => 
    requestV2.get('/data/models/list', { params }),
  
  // ==================== 执行日志 ====================
  
  /**
   * 获取执行日志列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getExecutionLogs: (params = {}) => 
    requestV2.get('/metadata/execution-logs', { params }),
  
  /**
   * 获取执行日志详情
   * @param {number} id - 日志ID
   * @returns {Promise}
   */
  getExecutionLog: (id) => 
    requestV2.get(`/metadata/execution-logs/${id}`),
  
  // ==================== 统计信息 ====================
  
  /**
   * 获取元数据统计信息
   * @returns {Promise}
   */
  getStatistics: () => requestV2.get('/metadata/statistics'),

  // ==================== 配置信息 ====================
  
  /**
   * 获取TDengine默认配置
   * @returns {Promise}
   */
  getTDengineDefaultConfig: () => requestV2.get('/metadata/config/tdengine-default'),

  /**
   * 获取TDengine结构差异
   * @param {string} deviceTypeCode - 设备类型代码
   * @returns {Promise}
   */
  getSchemaDiff: (deviceTypeCode) => requestV2.get('/metadata/schema/diff', {
    params: { device_type_code: deviceTypeCode }
  }),

  // ==================== TDengine 同步 ====================

  /**
   * 预览TDengine字段
   * @param {Object} params - 同步参数
   * @returns {Promise}
   */
  previewTDengineFields: (params) => requestV2.get('/metadata-sync/preview-tdengine-fields', { params }),

  /**
   * 执行TDengine同步
   * @param {Object} data - 同步数据
   * @returns {Promise}
   */
  syncFromTDengine: (data) => requestV2.post('/metadata-sync/sync-from-tdengine', data),
}

/**
 * 导出默认对象
 */
export default dataModelApi

