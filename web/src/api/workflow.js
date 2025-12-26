/**
 * 工作流管理 API
 */
import { request } from '@/utils/http'

const BASE_URL = '/v2/workflows'

// =====================================================
// 工作流 CRUD
// =====================================================

/**
 * 获取工作流列表
 */
export function getWorkflowList(params) {
  return request({
    url: BASE_URL,
    method: 'get',
    params
  })
}

/**
 * 获取工作流详情
 */
export function getWorkflowDetail(id) {
  return request({
    url: `${BASE_URL}/${id}`,
    method: 'get'
  })
}

/**
 * 创建工作流
 */
export function createWorkflow(data) {
  return request({
    url: BASE_URL,
    method: 'post',
    data
  })
}

/**
 * 更新工作流
 */
export function updateWorkflow(id, data) {
  return request({
    url: `${BASE_URL}/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除工作流
 */
export function deleteWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}`,
    method: 'delete'
  })
}


// =====================================================
// 工作流状态操作
// =====================================================

/**
 * 切换工作流启用状态
 */
export function toggleWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/toggle`,
    method: 'put'
  })
}

/**
 * 发布工作流
 */
export function publishWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/publish`,
    method: 'post'
  })
}

/**
 * 取消发布工作流
 */
export function unpublishWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/unpublish`,
    method: 'post'
  })
}

/**
 * 复制工作流
 */
export function duplicateWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/duplicate`,
    method: 'post'
  })
}

// =====================================================
// 工作流设计
// =====================================================

/**
 * 保存工作流设计
 */
export function saveWorkflowDesign(id, data) {
  return request({
    url: `${BASE_URL}/${id}/design`,
    method: 'put',
    data
  })
}

/**
 * 验证工作流
 */
export function validateWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/validate`,
    method: 'post'
  })
}

// =====================================================
// 工作流执行
// =====================================================

/**
 * 执行工作流
 */
export function executeWorkflow(id, data = {}) {
  return request({
    url: `${BASE_URL}/${id}/execute`,
    method: 'post',
    data
  })
}

/**
 * 获取工作流执行记录
 */
export function getWorkflowExecutions(workflowId, params) {
  return request({
    url: `${BASE_URL}/${workflowId}/executions`,
    method: 'get',
    params
  })
}

/**
 * 获取执行详情
 */
export function getExecutionDetail(executionId) {
  return request({
    url: `${BASE_URL}/executions/${executionId}`,
    method: 'get'
  })
}

/**
 * 取消执行
 */
export function cancelExecution(executionId) {
  return request({
    url: `${BASE_URL}/executions/${executionId}/cancel`,
    method: 'post'
  })
}

// =====================================================
// 工作流模板
// =====================================================

/**
 * 获取模板列表
 */
export function getWorkflowTemplates(params) {
  return request({
    url: `${BASE_URL}/templates`,
    method: 'get',
    params
  })
}

/**
 * 获取模板详情
 */
export function getWorkflowTemplate(id) {
  return request({
    url: `${BASE_URL}/templates/${id}`,
    method: 'get'
  })
}

/**
 * 使用模板创建工作流
 */
export function useWorkflowTemplate(templateId, name) {
  return request({
    url: `${BASE_URL}/templates/${templateId}/use`,
    method: 'post',
    params: { name }
  })
}

/**
 * 创建模板
 */
export function createWorkflowTemplate(data) {
  return request({
    url: `${BASE_URL}/templates`,
    method: 'post',
    data
  })
}

/**
 * 将工作流保存为模板
 */
export function saveAsTemplate(workflowId, name, description) {
  return request({
    url: `${BASE_URL}/${workflowId}/save-as-template`,
    method: 'post',
    params: { name, description }
  })
}

// =====================================================
// 导入导出
// =====================================================

/**
 * 导出工作流
 */
export function exportWorkflow(id) {
  return request({
    url: `${BASE_URL}/${id}/export`,
    method: 'get'
  })
}

/**
 * 导入工作流
 */
export function importWorkflow(data) {
  return request({
    url: `${BASE_URL}/import`,
    method: 'post',
    data
  })
}

// =====================================================
// 辅助数据
// =====================================================

/**
 * 获取工作流类型列表
 */
export function getWorkflowTypes() {
  return request({
    url: `${BASE_URL}/types`,
    method: 'get'
  })
}

/**
 * 获取优先级列表
 */
export function getWorkflowPriorities() {
  return request({
    url: `${BASE_URL}/priorities`,
    method: 'get'
  })
}

/**
 * 获取触发类型列表
 */
export function getTriggerTypes() {
  return request({
    url: `${BASE_URL}/trigger-types`,
    method: 'get'
  })
}

/**
 * 获取工作流统计信息
 */
export function getWorkflowStats() {
  return request({
    url: `${BASE_URL}/stats`,
    method: 'get'
  })
}

// =====================================================
// 版本管理
// =====================================================

/**
 * 获取工作流版本历史
 */
export function getWorkflowVersions(workflowId, params) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions`,
    method: 'get',
    params
  })
}

/**
 * 获取版本详情
 */
export function getWorkflowVersionDetail(workflowId, versionId) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions/${versionId}`,
    method: 'get'
  })
}

/**
 * 创建版本快照
 */
export function createWorkflowVersion(workflowId, data) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions`,
    method: 'post',
    data
  })
}

/**
 * 回滚到指定版本
 */
export function rollbackWorkflowVersion(workflowId, versionId) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions/${versionId}/rollback`,
    method: 'post'
  })
}

/**
 * 对比两个版本
 */
export function compareWorkflowVersions(workflowId, version1Id, version2Id) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions/compare`,
    method: 'get',
    params: {
      version1_id: version1Id,
      version2_id: version2Id
    }
  })
}

/**
 * 删除版本
 */
export function deleteWorkflowVersion(workflowId, versionId) {
  return request({
    url: `${BASE_URL}/${workflowId}/versions/${versionId}`,
    method: 'delete'
  })
}
