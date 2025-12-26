/**
 * 跨端 API 统一导出
 * 提供工厂函数创建 API 实例
 */

import { ApiClient, type ApiClientOptions } from './client';
import { AuthApi } from './auth';
import { DeviceApi } from './device';
import { AlarmApi } from './alarm';
import { RepairApi } from './repair';

/**
 * API 服务集合
 */
export interface ApiServices {
  auth: AuthApi;
  device: DeviceApi;
  alarm: AlarmApi;
  repair: RepairApi;
  client: ApiClient; // 原始客户端，用于自定义请求
}

/**
 * 创建 API 服务集合
 * @param options - ApiClient 配置项
 * @returns API 服务集合
 * 
 * @example
 * ```typescript
 * // Web 端
 * const api = createApiServices({
 *   baseURL: '/api/v2',
 *   getToken: () => localStorage.getItem('token'),
 * });
 * 
 * // NativeScript 端
 * import * as ApplicationSettings from '@nativescript/core/application-settings';
 * const api = createApiServices({
 *   baseURL: 'https://api.example.com/v2',
 *   getToken: () => ApplicationSettings.getString('token', ''),
 * });
 * ```
 */
export function createApiServices(options: ApiClientOptions): ApiServices {
  const client = new ApiClient(options);

  return {
    auth: new AuthApi(client),
    device: new DeviceApi(client),
    alarm: new AlarmApi(client),
    repair: new RepairApi(client),
    client, // 暴露原始客户端
  };
}

// 导出所有 API 类，供高级用法
export { ApiClient } from './client';
export { AuthApi } from './auth';
export { DeviceApi } from './device';
export { AlarmApi } from './alarm';
export { RepairApi } from './repair';

// 导出类型
export type { ApiClientOptions } from './client';

