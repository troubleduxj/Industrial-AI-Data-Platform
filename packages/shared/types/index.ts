/*
  Shared TypeScript types for cross-platform reuse (web + NativeScript).
  Keep this layer UI-agnostic and free of browser/DOM dependencies.
*/

// ========== 通用工具类型 ==========

export type Maybe<T> = T | null | undefined;

export type Result<T, E = unknown> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

// ========== API 响应类型 ==========

export interface ApiResponse<T = unknown> {
  success: boolean;
  code: number;
  message: string;
  data: T;
  timestamp?: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  sortField?: string;
  sortOrder?: 'asc' | 'desc';
}

// ========== 用户与权限 ==========

export interface UserMinimal {
  id: number;
  username: string;
  isActive?: boolean;
  isSuperuser?: boolean;
}

export interface User extends UserMinimal {
  nickname?: string;
  email?: string;
  phone?: string;
  avatar?: string;
  status?: 'active' | 'inactive' | 'locked';
  roles?: Role[];
  departments?: Department[];
  created_at?: string;
  updated_at?: string;
}

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  permissions?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface Department {
  id: number;
  name: string;
  code?: string;
  parent_id?: number;
  level?: number;
  children?: Department[];
  created_at?: string;
  updated_at?: string;
}

export interface Menu {
  id: number;
  name: string;
  path?: string;
  icon?: string;
  parent_id?: number;
  order_num?: number;
  menu_type: 'menu' | 'button';
  permission?: string;
  component?: string;
  is_hidden?: boolean;
  children?: Menu[];
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  remember?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  user: User;
  permissions?: string[];
  menus?: Menu[];
}

// ========== 设备管理 ==========

export interface DeviceMinimal {
  id: number;
  name: string;
  status?: string;
}

export interface DeviceType {
  id?: number;
  type_code: string;
  type_name: string;
  description?: string;
  icon?: string;
  sort_order?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Device {
  id: number;
  device_name: string;
  device_code: string;
  device_type: string;
  device_model?: string;
  manufacturer?: string;
  online_address?: string;
  status?: 'online' | 'offline' | 'maintenance' | 'alarm';
  department_id?: number;
  department_name?: string;
  location?: string;
  installed_at?: string;
  last_online_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DeviceStatusStats {
  total: number;
  online: number;
  offline: number;
  maintenance: number;
  alarm: number;
}

export interface DeviceCreateInput {
  device_name: string;
  device_code: string;
  device_type: string;
  device_model?: string;
  manufacturer?: string;
  online_address?: string;
  department_id?: number;
  location?: string;
  installed_at?: string;
}

export interface DeviceUpdateInput extends Partial<DeviceCreateInput> {
  id: number;
}

// ========== 告警管理 ==========

export type AlarmLevel = 'info' | 'warning' | 'error' | 'critical';
export type AlarmStatus = 'pending' | 'acknowledged' | 'resolved' | 'closed';

export interface Alarm {
  id: number;
  title: string;
  level: AlarmLevel;
  status: AlarmStatus;
  device_id?: number;
  device_name?: string;
  device_code?: string;
  description?: string;
  occurred_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  handler_id?: number;
  handler_name?: string;
  remark?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AlarmStats {
  total: number;
  pending: number;
  acknowledged: number;
  resolved: number;
  by_level: {
    info: number;
    warning: number;
    error: number;
    critical: number;
  };
}

export interface AlarmCreateInput {
  title: string;
  level: AlarmLevel;
  device_id?: number;
  description?: string;
  occurred_at?: string;
}

export interface AlarmAcknowledgeInput {
  id: number;
  remark?: string;
}

export interface AlarmResolveInput {
  id: number;
  remark?: string;
}

// ========== 维修管理 ==========

export type RepairStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export interface RepairRecord {
  id: number;
  device_id: number;
  device_name?: string;
  device_code?: string;
  fault_description: string;
  repair_description?: string;
  repair_result?: string;
  repair_status: RepairStatus;
  reported_by?: number;
  reported_by_name?: string;
  assigned_to?: number;
  assigned_to_name?: string;
  reported_at: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RepairRecordCreateInput {
  device_id: number;
  fault_description: string;
  reported_at?: string;
}

export interface RepairRecordUpdateInput extends Partial<RepairRecordCreateInput> {
  id: number;
  repair_description?: string;
  repair_result?: string;
  repair_status?: RepairStatus;
  assigned_to?: number;
  started_at?: string;
  completed_at?: string;
}

// ========== 系统配置 ==========

export type ConfigType = 'string' | 'number' | 'boolean' | 'json';

export interface SystemConfig {
  id: number;
  config_key: string;
  config_value: string;
  config_type: ConfigType;
  description?: string;
  is_public: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SystemConfigCreateInput {
  config_key: string;
  config_value: string;
  config_type: ConfigType;
  description?: string;
  is_public?: boolean;
}

export interface SystemConfigUpdateInput extends Partial<SystemConfigCreateInput> {
  id: number;
}

// ========== 统计与报表 ==========

export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
  }[];
}

export interface DashboardStats {
  deviceStats: DeviceStatusStats;
  alarmStats: AlarmStats;
  repairStats: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
  };
}
