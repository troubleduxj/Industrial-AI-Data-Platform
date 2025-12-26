/**
 * 设备管理相关 API
 * 跨端通用接口封装
 */

import type { ApiClient } from './client';
import type {
  Device,
  DeviceType,
  DeviceCreateInput,
  DeviceUpdateInput,
  DeviceStatusStats,
  Paginated,
  PaginationParams,
} from '../types';

export class DeviceApi {
  constructor(private client: ApiClient) {}

  // ========== 设备类型 ==========

  /**
   * 获取设备类型列表
   */
  async getDeviceTypes(params?: PaginationParams) {
    return this.client.get<Paginated<DeviceType>>('/devices/types', params);
  }

  /**
   * 获取设备类型详情
   */
  async getDeviceType(typeCode: string) {
    return this.client.get<DeviceType>(`/devices/types/${typeCode}`);
  }

  /**
   * 创建设备类型
   */
  async createDeviceType(data: Omit<DeviceType, 'id'>) {
    return this.client.post<DeviceType>('/devices/types', data);
  }

  /**
   * 更新设备类型
   */
  async updateDeviceType(typeCode: string, data: Partial<DeviceType>) {
    return this.client.put<DeviceType>(`/devices/types/${typeCode}`, data);
  }

  /**
   * 删除设备类型
   */
  async deleteDeviceType(typeCode: string, params?: any) {
    return this.client.delete(`/devices/types/${typeCode}`, params);
  }

  // ========== 设备管理 ==========

  /**
   * 获取设备列表
   */
  async getDevices(params?: PaginationParams & { device_type?: string; status?: string }) {
    return this.client.get<Paginated<Device>>('/devices', params);
  }

  /**
   * 获取设备详情
   */
  async getDevice(id: number) {
    return this.client.get<Device>(`/devices/${id}`);
  }

  /**
   * 根据设备编码获取设备
   */
  async getDeviceByCode(deviceCode: string) {
    return this.client.get<Device>(`/devices/by-code/${deviceCode}`);
  }

  /**
   * 创建设备
   */
  async createDevice(data: DeviceCreateInput) {
    return this.client.post<Device>('/devices', data);
  }

  /**
   * 更新设备
   */
  async updateDevice(id: number, data: Partial<DeviceUpdateInput>) {
    return this.client.put<Device>(`/devices/${id}`, data);
  }

  /**
   * 删除设备
   */
  async deleteDevice(id: number) {
    return this.client.delete(`/devices/${id}`);
  }

  async getRelatedCounts(id: number) {
    return this.client.get(`/devices/${id}/related-counts`);
  }

  /**
   * 批量删除设备
   */
  async batchDeleteDevices(ids: number[]) {
    return this.client.post('/devices/batch-delete', { ids });
  }

  async batchDeleteDeviceTypes(ids: number[], params?: any) {
    let url = '/devices/types/batch-delete';
    if (params && params.cascade) {
        url += '?cascade=true';
    }
    return this.client.post(url, { ids });
  }

  /**
   * 获取设备状态统计
   */
  async getDeviceStats() {
    return this.client.get<DeviceStatusStats>('/devices/stats');
  }

  /**
   * 搜索设备
   */
  async searchDevices(keyword: string, params?: PaginationParams) {
    return this.client.get<Paginated<Device>>('/devices/search', {
      ...params,
      keyword,
    });
  }
}

