/**
 * 通知管理 API
 */

import { requestV2 } from '@/utils/http/v2-interceptors'

// 管理员通知管理API
export const notificationApi = {
  // 获取通知列表
  list: (params = {}) => requestV2.get('/notifications', { params }),

  // 获取通知详情
  get: (id) => requestV2.get(`/notifications/${id}`),

  // 创建通知
  create: (data) => requestV2.post('/notifications', data),

  // 更新通知
  update: (id, data) => requestV2.put(`/notifications/${id}`, data),

  // 删除通知
  delete: (id) => requestV2.delete(`/notifications/${id}`),

  // 发布通知
  publish: (id) => requestV2.post(`/notifications/${id}/publish`),

  // 撤回通知
  unpublish: (id) => requestV2.post(`/notifications/${id}/unpublish`),
}

// 用户通知API
export const userNotificationApi = {
  // 获取我的通知
  list: (params = {}) => requestV2.get('/user/notifications', { params }),

  // 获取未读数量
  getUnreadCount: (userId) => requestV2.get('/user/notifications/unread-count', { params: { user_id: userId } }),

  // 标记已读
  markAsRead: (id, userId) => requestV2.post(`/user/notifications/${id}/read`, null, { params: { user_id: userId } }),

  // 全部标记已读
  markAllAsRead: (userId) => requestV2.post('/user/notifications/read-all', null, { params: { user_id: userId } }),

  // 删除通知
  delete: (id, userId) => requestV2.delete(`/user/notifications/${id}`, { params: { user_id: userId } }),
}

// 通知类型常量
export const NotificationType = {
  ANNOUNCEMENT: 'announcement',
  ALARM: 'alarm',
  TASK: 'task',
  SYSTEM: 'system',
}

export const NotificationTypeOptions = [
  { label: '系统公告', value: 'announcement' },
  { label: '报警通知', value: 'alarm' },
  { label: '任务提醒', value: 'task' },
  { label: '系统消息', value: 'system' },
]

// 通知级别常量
export const NotificationLevel = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
}

export const NotificationLevelOptions = [
  { label: '信息', value: 'info', color: '#909399' },
  { label: '警告', value: 'warning', color: '#e6a23c' },
  { label: '错误', value: 'error', color: '#f56c6c' },
]

// 发送范围常量
export const NotificationScope = {
  ALL: 'all',
  ROLE: 'role',
  USER: 'user',
}

export const NotificationScopeOptions = [
  { label: '全部用户', value: 'all' },
  { label: '指定角色', value: 'role' },
  { label: '指定用户', value: 'user' },
]

export default {
  notificationApi,
  userNotificationApi,
}
