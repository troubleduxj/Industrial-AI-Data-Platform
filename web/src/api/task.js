import { request } from '@/utils/http'

// 任务监控相关 API
export const taskApi = {
  // 获取监控数据
  getMonitorData() {
    return request({
      url: '/tasks/monitor',
      method: 'GET',
    })
  },

  // 获取任务列表
  getList(params) {
    return request({
      url: '/tasks',
      method: 'GET',
      params,
    })
  },

  // 获取任务详情
  getDetail(id) {
    return request({
      url: `/tasks/${id}`,
      method: 'GET',
    })
  },

  // 获取任务趋势数据
  getTrendData(timeRange) {
    return request({
      url: '/tasks/trend',
      method: 'GET',
      params: { timeRange },
    })
  },

  // 停止任务
  stopTask(id) {
    return request({
      url: `/tasks/${id}/stop`,
      method: 'POST',
    })
  },

  // 重试任务
  retryTask(id) {
    return request({
      url: `/tasks/${id}/retry`,
      method: 'POST',
    })
  },

  // 获取任务日志
  getLogs(id) {
    return request({
      url: `/tasks/${id}/logs`,
      method: 'GET',
    })
  },
}
