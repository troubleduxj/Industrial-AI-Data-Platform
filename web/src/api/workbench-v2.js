/**
 * 工作台 v2 API
 */
import { request } from '@/utils/http'

const workbenchV2Api = {
  // 获取工作台概览数据
  getOverview: () => {
    return request({
      url: '/api/v2/workbench/overview',
      method: 'GET',
    })
  },

  // 获取快捷操作
  getQuickActions: () => {
    return request({
      url: '/api/v2/workbench/quick-actions',
      method: 'GET',
    })
  },

  // 获取最近活动
  getRecentActivities: (params) => {
    return request({
      url: '/api/v2/workbench/recent-activities',
      method: 'GET',
      params,
    })
  },

  // 获取统计数据
  getStatistics: () => {
    return request({
      url: '/api/v2/workbench/statistics',
      method: 'GET',
    })
  },

  // 获取通知消息
  getNotifications: (params) => {
    return request({
      url: '/api/v2/workbench/notifications',
      method: 'GET',
      params,
    })
  },

  // 标记通知为已读
  markNotificationAsRead: (id) => {
    return request({
      url: `/api/v2/workbench/notifications/${id}/read`,
      method: 'PUT',
    })
  },

  // 获取待办事项
  getTodoItems: (params) => {
    return request({
      url: '/api/v2/workbench/todo-items',
      method: 'GET',
      params,
    })
  },

  // 创建待办事项
  createTodoItem: (data) => {
    return request({
      url: '/api/v2/workbench/todo-items',
      method: 'POST',
      data,
    })
  },

  // 更新待办事项
  updateTodoItem: (id, data) => {
    return request({
      url: `/api/v2/workbench/todo-items/${id}`,
      method: 'PUT',
      data,
    })
  },

  // 删除待办事项
  deleteTodoItem: (id) => {
    return request({
      url: `/api/v2/workbench/todo-items/${id}`,
      method: 'DELETE',
    })
  },

  // 获取个人设置
  getPersonalSettings: () => {
    return request({
      url: '/api/v2/workbench/personal-settings',
      method: 'GET',
    })
  },

  // 更新个人设置
  updatePersonalSettings: (data) => {
    return request({
      url: '/api/v2/workbench/personal-settings',
      method: 'PUT',
      data,
    })
  },
}

export default workbenchV2Api
