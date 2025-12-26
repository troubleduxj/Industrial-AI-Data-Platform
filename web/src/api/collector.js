/**
 * 采集器管理相关API
 */
import { request } from '@/utils/http'

// 采集器API
export const collectorApi = {
  // 获取仪表板数据
  getDashboard() {
    return request({
      url: '/api/v2/collector/dashboard',
      method: 'get',
    })
  },

  // 获取采集器列表
  getList(params) {
    return request({
      url: '/api/v2/collector/list',
      method: 'get',
      params,
    })
  },

  // 获取采集器配置列表
  getConfigs(params) {
    return request({
      url: '/api/v2/collector/configs',
      method: 'get',
      params,
    })
  },

  // 创建采集器
  create(data) {
    return request({
      url: '/api/v2/collector',
      method: 'post',
      data,
    })
  },

  // 更新采集器
  update(id, data) {
    return request({
      url: `/api/v2/collector/${id}`,
      method: 'put',
      data,
    })
  },

  // 删除采集器
  delete(id) {
    return request({
      url: `/api/v2/collector/${id}`,
      method: 'delete',
    })
  },

  // 启动采集器
  start(id) {
    return request({
      url: `/api/v2/collector/${id}/start`,
      method: 'post',
    })
  },

  // 停止采集器
  stop(id) {
    return request({
      url: `/api/v2/collector/${id}/stop`,
      method: 'post',
    })
  },

  // 获取采集器详情
  getDetail(id) {
    return request({
      url: `/api/v2/collector/${id}`,
      method: 'get',
    })
  },

  // 测试采集器连接
  testConnection(data) {
    return request({
      url: '/api/v2/collector/test-connection',
      method: 'post',
      data,
    })
  },

  // 获取配置模板列表
  getConfigTemplates(params) {
    return request({
      url: '/api/v2/collectors/config-templates',
      method: 'get',
      params,
    })
  },

  // 获取配置模板详情
  getConfigTemplate(id) {
    return request({
      url: `/api/v2/collectors/config-templates/${id}`,
      method: 'get',
    })
  },

  // 验证配置
  validateConfig(data) {
    return request({
      url: '/api/v2/collectors/config-validation/validate',
      method: 'post',
      data,
    })
  },

  // 合并配置
  mergeConfig(data) {
    return request({
      url: '/api/v2/collectors/config-merge/merge',
      method: 'post',
      data,
    })
  },
}

export default {
  collectorApi,
}
