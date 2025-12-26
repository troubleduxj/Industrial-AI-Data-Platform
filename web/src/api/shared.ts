/**
 * Web 端接入 Shared API 层
 * 统一使用跨端 API 客户端
 */

import { createApiServices } from '@shared/api';

// 获取 Token（从 localStorage）
const getToken = (): string => {
  // 注意：后端使用 'access_token' 作为 localStorage 键名
  return localStorage.getItem('access_token') || '';
};

// 获取 BASE URL（从环境变量）
// 确保baseURL是/api/v2，因为后端设备API在v2路径下
const baseURL = '/api/v2';

// 创建 API 服务实例
export const sharedApi = createApiServices({
  baseURL,
  getToken,
});

// 默认导出
export default sharedApi;

/**
 * 使用示例：
 * 
 * ```typescript
 * import sharedApi from '@/api/shared';
 * 
 * // 登录
 * const result = await sharedApi.auth.login({
 *   username: 'admin',
 *   password: '123456',
 * });
 * 
 * // 获取设备列表
 * const devices = await sharedApi.device.getDevices({
 *   page: 1,
 *   pageSize: 20,
 * });
 * 
 * // 获取告警统计
 * const stats = await sharedApi.alarm.getAlarmStats();
 * ```
 */

