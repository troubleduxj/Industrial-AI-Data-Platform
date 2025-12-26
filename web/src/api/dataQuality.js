import { request } from '@/utils/http'

// 数据质量相关 API
export const dataQualityApi = {
  // 获取质量报告
  getReport() {
    return request({
      url: '/data-quality/report',
      method: 'GET',
    })
  },

  // 获取异常数据
  getAnomalies() {
    return request({
      url: '/data-quality/anomalies',
      method: 'GET',
    })
  },

  // 获取改进建议
  getSuggestions() {
    return request({
      url: '/data-quality/suggestions',
      method: 'GET',
    })
  },

  // 获取趋势数据
  getTrendData(timeRange) {
    return request({
      url: '/data-quality/trend',
      method: 'GET',
      params: { timeRange },
    })
  },

  // 处理异常
  handleAnomaly(id, action) {
    return request({
      url: `/data-quality/anomalies/${id}/handle`,
      method: 'POST',
      data: { action },
    })
  },

  // 应用建议
  applySuggestion(id) {
    return request({
      url: `/data-quality/suggestions/${id}/apply`,
      method: 'POST',
    })
  },

  // 忽略建议
  ignoreSuggestion(id) {
    return request({
      url: `/data-quality/suggestions/${id}/ignore`,
      method: 'POST',
    })
  },

  // 获取质量规则
  getRules() {
    return request({
      url: '/data-quality/rules',
      method: 'GET',
    })
  },

  // 创建质量规则
  createRule(data) {
    return request({
      url: '/data-quality/rules',
      method: 'POST',
      data,
    })
  },

  // 更新质量规则
  updateRule(id, data) {
    return request({
      url: `/data-quality/rules/${id}`,
      method: 'PUT',
      data,
    })
  },

  // 删除质量规则
  deleteRule(id) {
    return request({
      url: `/data-quality/rules/${id}`,
      method: 'DELETE',
    })
  },
}
