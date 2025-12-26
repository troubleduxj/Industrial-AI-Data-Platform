/**
 * 设备相关类型定义
 */

export interface DeviceType {
  id: number
  type_name: string
  type_code: string
  tdengine_stable_name?: string
  description?: string
  icon?: string
  is_active: boolean
  device_count?: number
  created_at?: string
  updated_at?: string
}

export interface DeviceField {
  id: number
  device_type_code: string
  field_name: string
  field_code: string
  field_type: 'float' | 'int' | 'string' | 'boolean'
  unit?: string | null
  sort_order: number
  display_config?: {
    icon?: string
    color?: string
    chart_type?: string
  } | null
  field_category?: string
  description?: string | null
  is_monitoring_key: boolean
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface Device {
  id: number | string
  device_code: string
  device_name: string
  device_type: string
  device_model?: string
  manufacturer?: string
  install_location?: string
  install_date?: string
  online_address?: string
  description?: string
  is_locked: boolean
  team_name?: string
  production_date?: string
  created_at?: string
  updated_at?: string
}
