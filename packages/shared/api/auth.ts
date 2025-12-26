/**
 * 认证相关 API
 * 跨端通用接口封装
 */

import type { ApiClient } from './client';
import type { LoginRequest, LoginResponse, User } from '../types';

export class AuthApi {
  constructor(private client: ApiClient) {}

  /**
   * 用户登录
   */
  async login(credentials: LoginRequest) {
    return this.client.post<LoginResponse>('/auth/login', credentials);
  }

  /**
   * 用户登出
   */
  async logout() {
    return this.client.post('/auth/logout');
  }

  /**
   * 刷新 Token
   */
  async refreshToken(refreshToken: string) {
    return this.client.post<{ access_token: string; refresh_token: string }>(
      '/auth/refresh',
      { refresh_token: refreshToken }
    );
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser() {
    return this.client.get<User>('/auth/me');
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string) {
    return this.client.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  /**
   * 获取用户权限列表
   */
  async getPermissions() {
    return this.client.get<string[]>('/auth/permissions');
  }
}

