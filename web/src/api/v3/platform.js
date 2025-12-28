/**
 * 工业AI数据平台 API v3
 * 资产类别、信号定义、资产管理、AI引擎、特征工程、迁移等接口
 */
import { request } from '@/utils/http'

const BASE_URL = '/api/v3'

/**
 * 资产类别 API
 */
export const assetCategoryApi = {
  // 获取资产类别列表
  getList: (params = {}) => request.get(`${BASE_URL}/asset-categories`, { params }),
  
  // 获取单个资产类别
  getById: (id) => request.get(`${BASE_URL}/asset-categories/${id}`),
  
  // 根据编码获取资产类别
  getByCode: (code) => request.get(`${BASE_URL}/asset-categories/code/${code}`),
  
  // 创建资产类别
  create: (data) => request.post(`${BASE_URL}/asset-categories`, data),
  
  // 更新资产类别
  update: (id, data) => request.put(`${BASE_URL}/asset-categories/${id}`, data),
  
  // 删除资产类别
  delete: (id) => request.delete(`${BASE_URL}/asset-categories/${id}`),
  
  // 获取资产类别的信号定义
  getSignals: (categoryId) => request.get(`${BASE_URL}/asset-categories/${categoryId}/signals`),
  
  // 添加信号定义
  addSignal: (categoryId, data) => request.post(`${BASE_URL}/asset-categories/${categoryId}/signals`, data),
  
  // 更新信号定义
  updateSignal: (categoryId, signalId, data) => 
    request.put(`${BASE_URL}/asset-categories/${categoryId}/signals/${signalId}`, data),
  
  // 删除信号定义
  deleteSignal: (categoryId, signalId) => 
    request.delete(`${BASE_URL}/asset-categories/${categoryId}/signals/${signalId}`),
  
  // 批量更新信号定义排序
  updateSignalOrder: (categoryId, signalOrders) => 
    request.put(`${BASE_URL}/asset-categories/${categoryId}/signals/order`, { orders: signalOrders }),
}

/**
 * 资产 API
 */
export const assetApi = {
  // 获取资产列表
  getList: (params = {}) => request.get(`${BASE_URL}/assets`, { params }),
  
  // 获取单个资产
  getById: (id) => request.get(`${BASE_URL}/assets/${id}`),
  
  // 根据编码获取资产
  getByCode: (code) => request.get(`${BASE_URL}/assets/code/${code}`),
  
  // 创建资产
  create: (data) => request.post(`${BASE_URL}/assets`, data),
  
  // 更新资产
  update: (id, data) => request.put(`${BASE_URL}/assets/${id}`, data),
  
  // 删除资产
  delete: (id) => request.delete(`${BASE_URL}/assets/${id}`),
  
  // 获取资产实时数据
  getRealtimeData: (id) => request.get(`${BASE_URL}/assets/${id}/realtime-data`),
  
  // 获取资产历史数据
  getHistoricalData: (id, params = {}) => 
    request.get(`${BASE_URL}/assets/${id}/historical-data`, { params }),
  
  // 批量获取资产实时数据
  getBatchRealtimeData: (assetIds) => 
    request.post(`${BASE_URL}/assets/batch/realtime-data`, { asset_ids: assetIds }),
}

/**
 * 信号定义 API
 */
export const signalApi = {
  // 获取信号定义列表
  getList: (params = {}) => request.get(`${BASE_URL}/signals`, { params }),
  
  // 获取单个信号定义
  getById: (id) => request.get(`${BASE_URL}/signals/${id}`),
  
  // 根据类别获取信号定义
  getByCategory: (categoryId, params = {}) => 
    request.get(`${BASE_URL}/signals/category/${categoryId}`, { params }),
  
  // 获取信号分组配置
  getGroups: (categoryId) => request.get(`${BASE_URL}/signals/category/${categoryId}/groups`),
}

/**
 * AI模型 API
 */
export const aiModelApi = {
  // 获取模型列表
  getList: (params = {}) => request.get(`${BASE_URL}/ai/models`, { params }),
  
  // 获取单个模型
  getById: (id) => request.get(`${BASE_URL}/ai/models/${id}`),
  
  // 注册模型
  register: (data) => request.post(`${BASE_URL}/ai/models`, data),
  
  // 更新模型
  update: (id, data) => request.put(`${BASE_URL}/ai/models/${id}`, data),
  
  // 删除模型
  delete: (id) => request.delete(`${BASE_URL}/ai/models/${id}`),
  
  // 部署模型
  deploy: (id) => request.post(`${BASE_URL}/ai/models/${id}/deploy`),
  
  // 获取模型版本列表
  getVersions: (modelId) => request.get(`${BASE_URL}/ai/models/${modelId}/versions`),
  
  // 创建模型版本
  createVersion: (data) => request.post(`${BASE_URL}/ai/versions`, data),
  
  // 激活模型版本
  activateVersion: (versionId) => request.post(`${BASE_URL}/ai/versions/${versionId}/activate`),
  
  // 验证模型版本
  validateVersion: (versionId) => request.post(`${BASE_URL}/ai/versions/${versionId}/validate`),
  
  // 归档模型版本
  archiveVersion: (versionId) => request.post(`${BASE_URL}/ai/versions/${versionId}/archive`),
}

/**
 * 预测 API
 */
export const predictionApi = {
  // 执行预测
  predict: (data) => request.post(`${BASE_URL}/predictions`, data),
  
  // 获取预测历史
  getHistory: (params = {}) => request.get(`${BASE_URL}/predictions/history`, { params }),
  
  // 获取批量预测任务列表
  getBatchJobs: () => request.get(`${BASE_URL}/predictions/batch`),
  
  // 创建批量预测任务
  createBatchJob: (data) => request.post(`${BASE_URL}/predictions/batch`, data),
}

/**
 * 特征工程 API
 */
export const featureApi = {
  // 获取特征定义列表
  getDefinitions: (params = {}) => request.get(`${BASE_URL}/features/definitions`, { params }),
  
  // 创建特征定义
  createDefinition: (data) => request.post(`${BASE_URL}/features/definitions`, data),
  
  // 更新特征定义
  updateDefinition: (id, data) => request.put(`${BASE_URL}/features/definitions/${id}`, data),
  
  // 删除特征定义
  deleteDefinition: (id) => request.delete(`${BASE_URL}/features/definitions/${id}`),
  
  // 验证特征DSL
  validateDSL: (data) => request.post(`${BASE_URL}/features/validate-dsl`, data),
  
  // 获取特征视图列表
  getViews: (params = {}) => request.get(`${BASE_URL}/features/views`, { params }),
  
  // 创建特征视图
  createView: (data) => request.post(`${BASE_URL}/features/views`, data),
  
  // 更新特征视图
  updateView: (id, data) => request.put(`${BASE_URL}/features/views/${id}`, data),
  
  // 删除特征视图
  deleteView: (id) => request.delete(`${BASE_URL}/features/views/${id}`),
  
  // 获取特征视图数据
  getViewData: (viewId, params = {}) => request.get(`${BASE_URL}/features/views/${viewId}/data`, { params }),
  
  // 获取流计算任务列表
  getStreamTasks: (params = {}) => request.get(`${BASE_URL}/features/streams`, { params }),
  
  // 创建流计算任务
  createStreamTask: (data) => request.post(`${BASE_URL}/features/streams`, data),
  
  // 更新流计算任务
  updateStreamTask: (id, data) => request.put(`${BASE_URL}/features/streams/${id}`, data),
  
  // 删除流计算任务
  deleteStreamTask: (id) => request.delete(`${BASE_URL}/features/streams/${id}`),
  
  // 启动流计算任务
  startStreamTask: (id) => request.post(`${BASE_URL}/features/streams/${id}/start`),
  
  // 暂停流计算任务
  pauseStreamTask: (id) => request.post(`${BASE_URL}/features/streams/${id}/pause`),
  
  // 获取流计算任务日志
  getStreamTaskLogs: (id) => request.get(`${BASE_URL}/features/streams/${id}/logs`),
  
  // 生成流计算SQL
  generateStreamSQL: (data) => request.post(`${BASE_URL}/features/generate-sql`, data),
}

/**
 * 迁移 API
 */
export const migrationApi = {
  // 获取迁移状态
  getStatus: () => request.get(`${BASE_URL}/migration/status`),
  
  // 获取迁移记录列表
  getRecords: (params = {}) => request.get(`${BASE_URL}/migration/records`, { params }),
  
  // 获取迁移记录详情
  getRecordDetail: (id) => request.get(`${BASE_URL}/migration/records/${id}`),
  
  // 执行迁移
  execute: (data) => request.post(`${BASE_URL}/migration/execute`, data),
  
  // 验证迁移
  validate: () => request.post(`${BASE_URL}/migration/validate`),
  
  // 回滚迁移
  rollback: () => request.post(`${BASE_URL}/migration/rollback`),
  
  // 回滚单条迁移记录
  rollbackRecord: (id) => request.post(`${BASE_URL}/migration/records/${id}/rollback`),
  
  // 切换架构
  switchArchitecture: (data) => request.post(`${BASE_URL}/migration/switch-architecture`, data),
  
  // 获取数据对比
  getDataComparison: () => request.get(`${BASE_URL}/migration/data-comparison`),
  
  // 获取迁移日志
  getLogs: () => request.get(`${BASE_URL}/migration/logs`),
  
  // 导出迁移记录
  exportRecords: (params = {}) => request.get(`${BASE_URL}/migration/records/export`, { params, responseType: 'blob' }),
}

/**
 * 决策引擎 API
 */
export const decisionApi = {
  // 规则管理
  getRules: (params = {}) => request.get(`${BASE_URL}/decision/rules`, { params }),
  getRule: (ruleId) => request.get(`${BASE_URL}/decision/rules/${ruleId}`),
  createRule: (data) => request.post(`${BASE_URL}/decision/rules`, data),
  updateRule: (ruleId, data) => request.put(`${BASE_URL}/decision/rules/${ruleId}`, data),
  deleteRule: (ruleId) => request.delete(`${BASE_URL}/decision/rules/${ruleId}`),
  
  // 规则启用/禁用
  enableRule: (ruleId) => request.post(`${BASE_URL}/decision/rules/${ruleId}/enable`),
  disableRule: (ruleId) => request.post(`${BASE_URL}/decision/rules/${ruleId}/disable`),
  clearCooldown: (ruleId) => request.post(`${BASE_URL}/decision/rules/${ruleId}/clear-cooldown`),
  
  // 规则测试和验证
  testRule: (ruleId, data) => request.post(`${BASE_URL}/decision/rules/${ruleId}/test`, data),
  validateRuleDSL: (data) => request.post(`${BASE_URL}/decision/rules/validate`, data),
  
  // 运行时状态
  getRuntimeStatus: () => request.get(`${BASE_URL}/decision/runtime/status`),
  reloadRules: () => request.post(`${BASE_URL}/decision/runtime/reload`),
  
  // 审计日志
  getAuditLogs: (params = {}) => request.get(`${BASE_URL}/decision/audit-logs`, { params }),
  getAuditLog: (logId) => request.get(`${BASE_URL}/decision/audit-logs/${logId}`),
  getAuditStatistics: (params = {}) => request.get(`${BASE_URL}/decision/audit-logs/statistics`, { params }),
  getRuleAuditLogs: (ruleId, params = {}) => request.get(`${BASE_URL}/decision/audit-logs/rules/${ruleId}`, { params }),
}

/**
 * 动态菜单 API
 */
export const dynamicMenuApi = {
  // 获取基于资产类别的动态菜单
  getAssetCategoryMenus: () => request.get(`${BASE_URL}/menus/asset-categories`),
  
  // 获取用户可访问的资产类别菜单
  getUserAssetMenus: () => request.get(`${BASE_URL}/menus/user-assets`),
}

/**
 * 统一平台API（便捷方法）
 */
export const platformApi = {
  // 资产类别
  getAssetCategories: (params) => assetCategoryApi.getList(params),
  createAssetCategory: (data) => assetCategoryApi.create(data),
  updateAssetCategory: (id, data) => assetCategoryApi.update(id, data),
  deleteAssetCategory: (id) => assetCategoryApi.delete(id),
  
  // 资产
  getAssets: (params) => assetApi.getList(params),
  createAsset: (data) => assetApi.create(data),
  updateAsset: (id, data) => assetApi.update(id, data),
  deleteAsset: (id) => assetApi.delete(id),
  getAssetRealtimeData: (id) => assetApi.getRealtimeData(id),
  
  // AI模型
  getAIModels: (params) => aiModelApi.getList(params),
  registerAIModel: (data) => aiModelApi.register(data),
  updateAIModel: (id, data) => aiModelApi.update(id, data),
  deleteAIModel: (id) => aiModelApi.delete(id),
  deployAIModel: (id) => aiModelApi.deploy(id),
  getModelVersions: (modelId) => aiModelApi.getVersions(modelId),
  createModelVersion: (data) => aiModelApi.createVersion(data),
  activateModelVersion: (id) => aiModelApi.activateVersion(id),
  validateModelVersion: (id) => aiModelApi.validateVersion(id),
  archiveModelVersion: (id) => aiModelApi.archiveVersion(id),
  
  // 预测
  predict: (data) => predictionApi.predict(data),
  getPredictionHistory: (params) => predictionApi.getHistory(params),
  getBatchPredictionJobs: () => predictionApi.getBatchJobs(),
  
  // 特征工程
  getFeatureDefinitions: (params) => featureApi.getDefinitions(params),
  createFeatureDefinition: (data) => featureApi.createDefinition(data),
  updateFeatureDefinition: (id, data) => featureApi.updateDefinition(id, data),
  deleteFeatureDefinition: (id) => featureApi.deleteDefinition(id),
  validateFeatureDSL: (data) => featureApi.validateDSL(data),
  getFeatureViews: (params) => featureApi.getViews(params),
  createFeatureView: (data) => featureApi.createView(data),
  updateFeatureView: (id, data) => featureApi.updateView(id, data),
  deleteFeatureView: (id) => featureApi.deleteView(id),
  getFeatureViewData: (viewId, params) => featureApi.getViewData(viewId, params),
  getStreamTasks: (params) => featureApi.getStreamTasks(params),
  createStreamTask: (data) => featureApi.createStreamTask(data),
  updateStreamTask: (id, data) => featureApi.updateStreamTask(id, data),
  deleteStreamTask: (id) => featureApi.deleteStreamTask(id),
  startStreamTask: (id) => featureApi.startStreamTask(id),
  pauseStreamTask: (id) => featureApi.pauseStreamTask(id),
  getStreamTaskLogs: (id) => featureApi.getStreamTaskLogs(id),
  generateStreamSQL: (data) => featureApi.generateStreamSQL(data),
  
  // 迁移
  getMigrationStatus: () => migrationApi.getStatus(),
  getMigrationRecords: (params) => migrationApi.getRecords(params),
  getMigrationRecordDetail: (id) => migrationApi.getRecordDetail(id),
  executeMigration: (data) => migrationApi.execute(data),
  validateMigration: () => migrationApi.validate(),
  rollbackMigration: () => migrationApi.rollback(),
  rollbackMigrationRecord: (id) => migrationApi.rollbackRecord(id),
  switchArchitecture: (data) => migrationApi.switchArchitecture(data),
  getDataComparison: () => migrationApi.getDataComparison(),
  getMigrationLogs: () => migrationApi.getLogs(),
  exportMigrationRecords: (params) => migrationApi.exportRecords(params),
  
  // 决策引擎
  getDecisionRules: (params) => decisionApi.getRules(params),
  getDecisionRule: (ruleId) => decisionApi.getRule(ruleId),
  createDecisionRule: (data) => decisionApi.createRule(data),
  updateDecisionRule: (ruleId, data) => decisionApi.updateRule(ruleId, data),
  deleteDecisionRule: (ruleId) => decisionApi.deleteRule(ruleId),
  enableDecisionRule: (ruleId) => decisionApi.enableRule(ruleId),
  disableDecisionRule: (ruleId) => decisionApi.disableRule(ruleId),
  clearRuleCooldown: (ruleId) => decisionApi.clearCooldown(ruleId),
  testDecisionRule: (ruleId, data) => decisionApi.testRule(ruleId, data),
  validateRuleDSL: (data) => decisionApi.validateRuleDSL(data),
  getDecisionRuntimeStatus: () => decisionApi.getRuntimeStatus(),
  reloadDecisionRules: () => decisionApi.reloadRules(),
  getDecisionAuditLogs: (params) => decisionApi.getAuditLogs(params),
  getDecisionAuditLog: (logId) => decisionApi.getAuditLog(logId),
  getDecisionAuditStatistics: (params) => decisionApi.getAuditStatistics(params),
  getRuleAuditLogs: (ruleId, params) => decisionApi.getRuleAuditLogs(ruleId, params),
}

export default {
  assetCategory: assetCategoryApi,
  asset: assetApi,
  signal: signalApi,
  aiModel: aiModelApi,
  prediction: predictionApi,
  feature: featureApi,
  migration: migrationApi,
  decision: decisionApi,
  dynamicMenu: dynamicMenuApi,
  platform: platformApi,
}
