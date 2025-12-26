/**
 * 维修记录相关 API
 * 跨端通用接口封装
 */

import type { ApiClient } from './client';
import type {
  RepairRecord,
  RepairRecordCreateInput,
  RepairRecordUpdateInput,
  Paginated,
  PaginationParams,
} from '../types';

export class RepairApi {
  constructor(private client: ApiClient) {}

  /**
   * 获取维修记录列表
   */
  async getRepairRecords(
    params?: PaginationParams & {
      device_id?: number;
      repair_status?: string;
      start_date?: string;
      end_date?: string;
    }
  ) {
    return this.client.get<Paginated<RepairRecord>>('/device/maintenance/repair-records', params);
  }

  /**
   * 获取维修记录详情
   */
  async getRepairRecord(id: number) {
    return this.client.get<RepairRecord>(`/device/maintenance/repair-records/${id}`);
  }

  /**
   * 创建维修记录
   */
  async createRepairRecord(data: RepairRecordCreateInput) {
    return this.client.post<RepairRecord>('/device/maintenance/repair-records', data);
  }

  /**
   * 更新维修记录
   */
  async updateRepairRecord(id: number, data: Partial<RepairRecordUpdateInput>) {
    return this.client.put<RepairRecord>(`/device/maintenance/repair-records/${id}`, data);
  }

  /**
   * 删除维修记录
   */
  async deleteRepairRecord(id: number) {
    return this.client.delete(`/device/maintenance/repair-records/${id}`);
  }

  /**
   * 批量删除维修记录
   */
  async batchDeleteRepairRecords(ids: number[]) {
    return this.client.post('/device/maintenance/repair-records/batch-delete', { ids });
  }

  /**
   * 分配维修任务
   */
  async assignRepairTask(id: number, assignedTo: number) {
    return this.client.post<RepairRecord>(`/device/maintenance/repair-records/${id}/assign`, {
      assigned_to: assignedTo,
    });
  }

  /**
   * 开始维修
   */
  async startRepair(id: number) {
    return this.client.post<RepairRecord>(`/device/maintenance/repair-records/${id}/start`);
  }

  /**
   * 完成维修
   */
  async completeRepair(id: number, repairDescription: string, repairResult: string) {
    return this.client.post<RepairRecord>(`/device/maintenance/repair-records/${id}/complete`, {
      repair_description: repairDescription,
      repair_result: repairResult,
    });
  }

  /**
   * 取消维修
   */
  async cancelRepair(id: number, reason?: string) {
    return this.client.post<RepairRecord>(`/device/maintenance/repair-records/${id}/cancel`, { reason });
  }

  /**
   * 获取设备的维修历史
   */
  async getDeviceRepairHistory(deviceId: number, params?: PaginationParams) {
    return this.client.get<Paginated<RepairRecord>>(`/devices/${deviceId}/repair-history`, params);
  }
}

