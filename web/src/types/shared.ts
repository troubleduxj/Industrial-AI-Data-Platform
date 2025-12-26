/**
 * Web 端接入 Shared Types 层
 * 统一使用跨端类型定义
 */

// 导出所有共享类型
export type {
  Maybe,
  Result,
  HttpMethod,
  ApiResponse,
  Paginated,
  PaginationParams,
  UserMinimal,
  User,
  Role,
  Department,
  Menu,
  LoginRequest,
  LoginResponse,
  DeviceMinimal,
  DeviceType,
  Device,
  DeviceStatusStats,
  DeviceCreateInput,
  DeviceUpdateInput,
  AlarmLevel,
  AlarmStatus,
  Alarm,
  AlarmStats,
  AlarmCreateInput,
  AlarmAcknowledgeInput,
  AlarmResolveInput,
  RepairStatus,
  RepairRecord,
  RepairRecordCreateInput,
  RepairRecordUpdateInput,
  ConfigType,
  SystemConfig,
  SystemConfigCreateInput,
  SystemConfigUpdateInput,
  TimeSeriesData,
  ChartData,
  DashboardStats,
} from '@shared/types';

/**
 * 使用示例：
 * 
 * ```typescript
 * import type { User, Device, Paginated } from '@/types/shared';
 * 
 * // 定义变量类型
 * const user: User = {
 *   id: 1,
 *   username: 'admin',
 *   nickname: '管理员',
 *   status: 'active',
 * };
 * 
 * // 定义函数返回类型
 * async function getDevices(): Promise<Paginated<Device>> {
 *   // ...
 * }
 * ```
 */

