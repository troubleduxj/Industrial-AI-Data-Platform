/**
 * 告警管理相关 API
 * 跨端通用接口封装
 */

import type { ApiClient } from './client';
import type {
  Alarm,
  AlarmStats,
  AlarmCreateInput,
  AlarmAcknowledgeInput,
  AlarmResolveInput,
  Paginated,
  PaginationParams,
} from '../types';

export class AlarmApi {
  constructor(private client: ApiClient) {}

  /**
   * 获取告警列表
   */
  async getAlarms(params?: PaginationParams & { level?: string; status?: string; device_id?: number }) {
    return this.client.get<Paginated<Alarm>>('/alarms', params);
  }

  /**
   * 获取告警详情
   */
  async getAlarm(id: number) {
    return this.client.get<Alarm>(`/alarms/${id}`);
  }

  /**
   * 创建告警
   */
  async createAlarm(data: AlarmCreateInput) {
    return this.client.post<Alarm>('/alarms', data);
  }

  /**
   * 确认告警
   */
  async acknowledgeAlarm(data: AlarmAcknowledgeInput) {
    return this.client.post<Alarm>(`/alarms/${data.id}/acknowledge`, {
      remark: data.remark,
    });
  }

  /**
   * 解决告警
   */
  async resolveAlarm(data: AlarmResolveInput) {
    return this.client.post<Alarm>(`/alarms/${data.id}/resolve`, {
      remark: data.remark,
    });
  }

  /**
   * 关闭告警
   */
  async closeAlarm(id: number, remark?: string) {
    return this.client.post<Alarm>(`/alarms/${id}/close`, { remark });
  }

  /**
   * 删除告警
   */
  async deleteAlarm(id: number) {
    return this.client.delete(`/alarms/${id}`);
  }

  /**
   * 批量确认告警
   */
  async batchAcknowledgeAlarms(ids: number[], remark?: string) {
    return this.client.post('/alarms/batch-acknowledge', { ids, remark });
  }

  /**
   * 批量解决告警
   */
  async batchResolveAlarms(ids: number[], remark?: string) {
    return this.client.post('/alarms/batch-resolve', { ids, remark });
  }

  /**
   * 获取告警统计
   */
  async getAlarmStats(params?: { start_date?: string; end_date?: string }) {
    return this.client.get<AlarmStats>('/alarms/statistics', params);
  }

  /**
   * 获取实时告警（最近N条）
   */
  async getRealtimeAlarms(limit = 10) {
    return this.client.get<Alarm[]>('/alarms/realtime', { limit });
  }
}

