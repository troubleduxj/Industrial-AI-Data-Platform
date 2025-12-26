/**
 * Mobile 端 API 服务
 * 使用 Shared 层的 API 客户端
 */
import { createApiServices } from '@shared/api';
import { getString, setString, remove, hasKey } from '@nativescript/core/application-settings';
import { isAndroid } from '@nativescript/core';

// Token 管理（使用 ApplicationSettings）
const TOKEN_KEY = 'access_token';

/**
 * 获取存储的 Token
 */
export const getToken = (): string => {
  return getString(TOKEN_KEY, '');
};

/**
 * 保存 Token
 */
export const setToken = (token: string): void => {
  setString(TOKEN_KEY, token);
};

/**
 * 移除 Token
 */
export const removeToken = (): void => {
  remove(TOKEN_KEY);
};

/**
 * 检查是否有 Token
 */
export const hasToken = (): boolean => {
  return hasKey(TOKEN_KEY);
};

/**
 * API 基础地址配置
 * 开发环境：
 *   - Android 模拟器使用 10.0.2.2 访问宿主机
 *   - iOS 模拟器使用 localhost
 * 生产环境：使用实际域名
 */
const getBaseURL = (): string => {
  // 判断是否为开发环境
  const isDev = true; // TODO: 从环境变量读取
  
  if (isDev) {
    // 开发环境
    return isAndroid
      ? 'http://10.0.2.2:8000/api/v2'  // Android 模拟器
      : 'http://localhost:8000/api/v2'; // iOS 模拟器
  } else {
    // 生产环境
    return 'https://your-production-api.com/api/v2';
  }
};

/**
 * 创建 API 服务实例
 * 使用 Shared 层的 createApiServices 工厂函数
 */
export const api = createApiServices({
  baseURL: getBaseURL(),
  getToken,
});

/**
 * 统一导出
 */
export default api;

