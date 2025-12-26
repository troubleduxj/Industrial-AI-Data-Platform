/**
 * AI模块 API客户端 V2
 * 集成Week 3 Day 1-2完成的AI核心API
 * - 特征提取API
 * - 异常检测API
 * - 趋势预测API
 * - 健康评分API
 */
import { requestV2 } from '@/utils/http/v2-interceptors'

/**
 * AI模块系统API
 */
export const aiModuleApi = {
  /**
   * 获取系统健康状态（包含AI模块状态）
   * @returns {Promise} 系统健康状态
   */
  getHealth: () => requestV2.get('/system/health'),

  /**
   * 获取AI模块配置
   * @returns {Promise} AI模块配置信息
   */
  getConfig: () => requestV2.get('/system/modules/ai/config'),

  /**
   * 获取AI模块资源使用情况
   * @returns {Promise} AI模块资源使用统计
   */
  getResources: () => requestV2.get('/system/modules/ai/resources'),
}

/**
 * 特征提取API
 */
export const featureExtractionApi = {
  /**
   * 提取数据特征
   * @param {Object} data 请求数据
   * @param {Array<number>} data.data 设备数据时间序列
   * @param {Array<string>} data.feature_types 特征类型列表（可选）
   * @returns {Promise} 提取的特征
   */
  extract: (data) => requestV2.post('/ai/features/extract', data),

  /**
   * 批量提取特征
   * @param {Object} data 请求数据
   * @param {Object} data.dataset 设备数据集（key为设备ID，value为数据）
   * @param {Array<string>} data.feature_types 特征类型列表（可选）
   * @returns {Promise} 批量提取结果
   */
  extractBatch: (data) => requestV2.post('/ai/features/extract/batch', data),

  /**
   * 获取支持的特征类型
   * @returns {Promise} 特征类型列表
   */
  getTypes: () => requestV2.get('/ai/features/types'),
}

/**
 * 异常检测API
 */
export const anomalyDetectionApi = {
  /**
   * 检测数据异常
   * @param {Object} data 请求数据
   * @param {Array<number>} data.data 设备数据时间序列
   * @param {string} data.device_code 设备编码（可选）
   * @param {string} data.method 检测方法：statistical/isolation_forest/combined（可选，默认combined）
   * @param {number} data.threshold 统计阈值（可选，默认3.0）
   * @param {boolean} data.save_to_db 是否保存到数据库（可选）
   * @returns {Promise} 异常检测结果
   */
  detect: (data) => requestV2.post('/ai/anomalies/detect', data),

  /**
   * 批量异常检测
   * @param {Object} data 请求数据
   * @param {Object} data.dataset 设备数据集
   * @param {string} data.method 检测方法（可选）
   * @param {number} data.threshold 统计阈值（可选）
   * @returns {Promise} 批量检测结果
   */
  detectBatch: (data) => requestV2.post('/ai/anomalies/detect/batch', data),

  /**
   * 获取异常记录
   * @param {Object} params 查询参数
   * @param {string} params.device_code 设备编码（可选）
   * @param {string} params.severity 严重程度（可选）
   * @param {boolean} params.is_handled 是否已处理（可选）
   * @param {number} params.page 页码（可选，默认1）
   * @param {number} params.page_size 每页数量（可选，默认20）
   * @returns {Promise} 异常记录列表
   */
  getRecords: (params = {}) => requestV2.get('/ai/anomalies/records', { params }),

  /**
   * 获取已配置异常检测的设备列表
   * @param {Object} params 查询参数
   * @param {boolean} params.is_active 是否只返回启用的设备（可选）
   * @param {number} params.page 页码（可选，默认1）
   * @param {number} params.page_size 每页数量（可选，默认100）
   * @returns {Promise} 监控设备列表
   */
  getMonitoredDevices: (params = {}) => requestV2.get('/ai/anomalies/monitored-devices', { params }),

  /**
   * 处理异常记录
   * @param {number} recordId 记录ID
   * @param {string} handleNote 处理备注（可选）
   * @returns {Promise} 处理结果
   */
  handleRecord: (recordId, handleNote) =>
    requestV2.put(`/ai/anomalies/records/${recordId}/handle`, { handle_note: handleNote }),

  /**
   * 获取异常检测配置
   * @param {string} deviceCode 设备编码
   * @returns {Promise} 配置信息
   */
  getConfig: (deviceCode) => requestV2.get(`/ai/anomalies/config/${deviceCode}`),

  /**
   * 更新异常检测配置
   * @param {string} deviceCode 设备编码
   * @param {Object} config 配置数据
   * @returns {Promise} 更新结果
   */
  updateConfig: (deviceCode, config) => requestV2.put(`/ai/anomalies/config/${deviceCode}`, config),
}

/**
 * 模型管理API
 */
export const modelManagementApi = {
  /**
   * 获取模型列表
   * @param {Object} params 查询参数
   * @returns {Promise} 模型列表
   */
  getList: (params = {}) => requestV2.get('/ai/models', { params }),

  /**
   * 创建模型
   * @param {Object} data 模型数据
   * @returns {Promise} 创建结果
   */
  create: (data) => requestV2.post('/ai/models', data),

  /**
   * 更新模型
   * @param {number} id 模型ID
   * @param {Object} data 模型数据
   * @returns {Promise} 更新结果
   */
  update: (id, data) => requestV2.put(`/ai/models/${id}`, data),

  /**
   * 删除模型
   * @param {number} id 模型ID
   * @returns {Promise} 删除结果
   */
  delete: (id) => requestV2.delete(`/ai/models/${id}`),

  /**
   * 训练模型
   * @param {number} id 模型ID
   * @param {Object} data 训练配置
   * @returns {Promise} 训练任务信息
   */
  train: (id, data) => requestV2.post(`/ai/models/${id}/train`, data),

  /**
   * 部署模型
   * @param {number} id 模型ID
   * @param {Object} data 部署配置
   * @returns {Promise} 部署结果
   */
  deploy: (id, data) => requestV2.post(`/ai/models/${id}/deploy`, data),

  /**
   * 获取模型详情
   * @param {number} id 模型ID
   * @returns {Promise} 模型详情
   */
  getDetail: (id) => requestV2.get(`/ai/models/${id}`),
  
  /**
   * 获取模型指标
   * @param {number} id 模型ID
   * @returns {Promise} 模型指标
   */
  getMetrics: (id) => requestV2.get(`/ai/models/${id}/metrics`),

  /**
   * 获取模型训练日志
   * @param {number} id 模型ID
   * @returns {Promise} 模型日志
   */
  getLogs: (id) => requestV2.get(`/ai/models/${id}/logs`),
}

/**
 * 趋势预测API
 */
export const trendPredictionApi = {
  /**
   * 执行趋势预测
   * @param {Object} data 请求数据
   * @param {Array<number>} data.data 历史数据时间序列
   * @param {number} data.steps 预测步数
   * @param {string} data.method 预测方法：arima/ma/ema/lr/auto（可选，默认arima）
   * @param {number} data.confidence_level 置信水平（可选，默认0.95）
   * @returns {Promise} 预测结果
   */
  predict: (data) => requestV2.post('/ai/predictions/execute/predict', data),

  /**
   * 批量趋势预测
   * @param {Object} data 请求数据
   * @param {Object} data.dataset 设备数据集
   * @param {number} data.steps 预测步数
   * @param {string} data.method 预测方法（可选）
   * @param {number} data.confidence_level 置信水平（可选）
   * @returns {Promise} 批量预测结果
   */
  predictBatch: (data) => requestV2.post('/ai/predictions/execute/predict/batch', data),

  /**
   * 预测方法对比
   * @param {Object} data 请求数据
   * @param {Array<number>} data.data 历史数据
   * @param {number} data.steps 预测步数
   * @param {Array<string>} data.methods 要对比的方法列表（可选）
   * @returns {Promise} 方法对比结果
   */
  compare: (data) => requestV2.post('/ai/predictions/execute/compare', data),

  /**
   * 获取支持的预测方法
   * @returns {Promise} 预测方法列表
   */
  getMethods: () => requestV2.get('/ai/predictions/execute/methods'),
}

/**
 * 预测任务管理API（新增 - 阶段1核心完善）
 */
export const predictionManagementApi = {
  /**
   * 批量创建预测任务
   * @param {Object} data 请求数据
   * @param {Array<string>} data.device_codes 设备代码列表
   * @param {string} data.metric_name 指标名称（如temperature）
   * @param {number} data.prediction_horizon 预测时间范围（小时）
   * @param {string} data.model_type 预测模型类型（ARIMA/MA/ES/LR）
   * @returns {Promise} 批量预测任务创建结果
   */
  createBatch: (data) => requestV2.post('/ai/predictions/tasks/batch', data),

  /**
   * 查询设备的预测历史
   * @param {Object} params 查询参数
   * @param {string} params.device_code 设备代码（必填）
   * @param {string} params.metric_name 指标名称（可选）
   * @param {string} params.status 状态筛选（可选）
   * @param {number} params.page 页码（可选，默认1）
   * @param {number} params.page_size 每页大小（可选，默认20）
   * @returns {Promise} 预测历史记录
   */
  getHistory: (params) => requestV2.get('/ai/predictions/tasks/history', { params }),

  /**
   * 获取预测列表
   * @param {Object} params 查询参数
   * @param {string} params.status 状态过滤（可选）
   * @param {number} params.created_by 创建人过滤（可选）
   * @param {string} params.date_from 开始日期（可选）
   * @param {string} params.date_to 结束日期（可选）
   * @param {string} params.search 搜索关键词（可选）
   * @param {number} params.page 页码（可选，默认1）
   * @param {number} params.page_size 每页大小（可选，默认20）
   * @returns {Promise} 预测列表
   */
  getList: (params = {}) => requestV2.get('/ai/predictions/tasks', { params }),

  /**
   * 获取预测详情
   * @param {number} predictionId 预测ID
   * @returns {Promise} 预测详情
   */
  getDetail: (predictionId) => requestV2.get(`/ai/predictions/tasks/${predictionId}`),

  /**
   * 创建预测任务
   * @param {Object} data 预测数据
   * @returns {Promise} 创建结果
   */
  create: (data) => requestV2.post('/ai/predictions/tasks', data),

  /**
   * 更新预测配置
   * @param {number} predictionId 预测ID
   * @param {Object} data 更新数据
   * @returns {Promise} 更新结果
   */
  update: (predictionId, data) => requestV2.put(`/ai/predictions/tasks/${predictionId}`, data),

  /**
   * 删除预测
   * @param {number} predictionId 预测ID
   * @returns {Promise} 删除结果
   */
  delete: (predictionId) => requestV2.delete(`/ai/predictions/tasks/${predictionId}`),

  /**
   * 导出预测报告
   * @param {number} predictionId 预测ID
   * @param {string} format 导出格式（json/csv/excel）
   * @returns {Promise} 导出文件
   */
  export: (predictionId, format = 'json') =>
    requestV2.get(`/ai/predictions/tasks/${predictionId}/export`, {
      params: { format },
      responseType: 'blob',
    }),

  /**
   * 分享预测结果
   * @param {number} predictionId 预测ID
   * @param {Object} data 分享数据
   * @param {Array<number>} data.user_ids 分享给的用户ID列表
   * @param {boolean} data.is_public 是否公开
   * @param {string} data.message 分享消息（可选）
   * @returns {Promise} 分享结果
   */
  share: (predictionId, data) =>
    requestV2.post(`/ai/predictions/tasks/${predictionId}/share`, data),

  /**
   * 批量删除预测
   * @param {Array<number>} ids 预测ID列表
   * @returns {Promise} 批量删除结果
   */
  batchDelete: (ids) => requestV2.post('/ai/predictions/tasks/batch-delete', { ids }),
}

/**
 * 健康评分API
 */
export const healthScoringApi = {
  /**
   * 计算设备健康评分
   * @param {Object} data 请求数据
   * @param {string} data.device_code 设备编码
   * @param {string} data.device_name 设备名称（可选）
   * @param {Object} data.performance_data 性能指标数据
   * @param {number} data.anomaly_count 异常次数（可选，默认0）
   * @param {number} data.uptime_days 运行天数（可选，默认0）
   * @param {Array<number>} data.historical_data 历史数据（可选）
   * @param {Object} data.weights 自定义权重（可选）
   * @param {boolean} data.save_to_db 是否保存到数据库（可选）
   * @returns {Promise} 健康评分结果
   */
  score: (data) => requestV2.post('/ai/health-scoring/score', data),

  /**
   * 批量健康评分
   * @param {Object} data 请求数据
   * @param {Object} data.devices 设备数据集
   * @param {Object} data.weights 统一权重配置（可选）
   * @returns {Promise} 批量评分结果
   */
  scoreBatch: (data) => requestV2.post('/ai/health-scoring/score/batch', data),

  /**
   * 获取健康评分历史
   * @param {Object} params 查询参数
   * @param {string} params.device_code 设备编码（可选）
   * @param {string} params.health_grade 健康等级（可选）
   * @param {number} params.page 页码（可选，默认1）
   * @param {number} params.page_size 每页数量（可选，默认20）
   * @returns {Promise} 健康评分历史
   */
  getHistory: (params = {}) => requestV2.get('/ai/health-scoring/history', { params }),

  /**
   * 获取设备健康趋势
   * @param {string} deviceCode 设备编码
   * @param {number} days 查询天数（可选，默认30）
   * @returns {Promise} 健康趋势数据
   */
  getTrend: (deviceCode, days = 30) =>
    requestV2.get(`/ai/health-scoring/trend/${deviceCode}`, { params: { days } }),

  /**
   * 获取默认评分权重
   * @returns {Promise} 默认权重配置
   */
  getWeights: () => requestV2.get('/ai/health-scoring/weights'),
}

/**
 * AI功能集成API（旧版兼容）
 * 保留用于逐步迁移
 */
export const aiFeaturesApi = {
  /**
   * AI仪表盘数据
   */
  getDashboardData: () => requestV2.get('/ai/dashboard'),

  /**
   * AI异常检测（旧版，建议使用 anomalyDetectionApi）
   */
  getAnomalies: (params = {}) => requestV2.get('/ai/anomalies', { params }),

  /**
   * AI趋势预测（旧版，建议使用 trendPredictionApi）
   */
  getTrendPrediction: (params = {}) => requestV2.get('/ai/prediction', { params }),

  /**
   * AI健康评分（旧版，建议使用 healthScoringApi）
   */
  getHealthScore: (params = {}) => requestV2.get('/ai/health-score', { params }),

  /**
   * AI智能分析
   */
  getSmartAnalysis: (params = {}) => requestV2.get('/ai/analysis', { params }),
}

// 默认导出
export default {
  aiModuleApi,
  featureExtractionApi,
  anomalyDetectionApi,
  trendPredictionApi,
  predictionManagementApi, // 新增预测任务管理API
  modelManagementApi, // 新增模型管理API
  healthScoringApi,
  aiFeaturesApi,
}
