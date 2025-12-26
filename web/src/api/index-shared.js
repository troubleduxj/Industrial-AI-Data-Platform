/**
 * Shared API 统一导出
 * 提供所有 API 适配器的统一访问入口
 */

// 导入所有 API 适配器
import authModule from './auth-shared'
import deviceModule from './device-shared'
import alarmModule from './alarm-shared'
import repairModule from './repair-shared'

// 导入原始 shared API
import sharedApi from './shared'

// ========== 统一导出 ==========

// 认证相关
export const authApi = authModule
export const {
  clearAuthData,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  isSuperAdmin,
  getToken,
  setToken,
  isTokenExpiringSoon,
  autoRefreshToken,
} = authModule

// 设备相关
export const { deviceApi, deviceTypeApi } = deviceModule

// 告警相关
export const { alarmApi } = alarmModule
export const {
  AlarmLevel,
  AlarmLevelText,
  AlarmLevelColor,
  AlarmStatus,
  AlarmStatusText,
  AlarmStatusColor,
} = alarmModule

// 维修相关
export const { repairApi } = repairModule
export const {
  RepairStatus,
  RepairStatusText,
  RepairStatusColor,
  calculateRepairDuration,
  formatRepairDuration,
  isRepairOverdue,
} = repairModule

// ========== 默认导出 ==========

export default {
  // API 模块
  auth: authApi,
  device: deviceApi,
  deviceType: deviceTypeApi,
  alarm: alarmApi,
  repair: repairApi,

  // 原始 shared API（用于扩展）
  shared: sharedApi,

  // 认证工具
  clearAuthData,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  isSuperAdmin,
  getToken,
  setToken,

  // 告警常量
  AlarmLevel,
  AlarmStatus,

  // 维修常量
  RepairStatus,

  // 工具函数
  calculateRepairDuration,
  formatRepairDuration,
  isRepairOverdue,
}

/**
 * 使用说明：
 *
 * 方式1：按需导入（推荐）
 * import { authApi, deviceApi, alarmApi } from '@/api/index-shared';
 * await authApi.login({ username, password });
 * await deviceApi.list({ page: 1 });
 *
 * 方式2：默认导入
 * import api from '@/api/index-shared';
 * await api.auth.login({ username, password });
 * await api.device.list({ page: 1 });
 *
 * 方式3：直接使用原始 shared（最灵活）
 * import sharedApi from '@/api/shared';
 * await sharedApi.auth.login({ username, password });
 * await sharedApi.device.getDevices({ page: 1 });
 *
 * 常量使用：
 * import { AlarmLevel, RepairStatus } from '@/api/index-shared';
 * const level = AlarmLevel.WARNING;
 * const status = RepairStatus.PENDING;
 *
 * 权限检查：
 * import { hasPermission, isSuperAdmin } from '@/api/index-shared';
 * if (hasPermission('device:create')) {
 *   // 有权限
 * }
 */
