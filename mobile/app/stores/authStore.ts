/**
 * 认证状态管理
 * 复用 Shared 层 API，处理登录、登出、Token 管理
 */
import { defineStore } from 'pinia';
import { api, setToken as saveToken, removeToken, hasToken } from '../services/apiService';

interface User {
  id: number;
  username: string;
  nickname?: string;
  email?: string;
  is_superuser?: boolean;
}

interface AuthState {
  user: User | null;
  isLoggedIn: boolean;
  isLoading: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    isLoggedIn: false,
    isLoading: false,
  }),

  getters: {
    /**
     * 是否为超级管理员
     */
    isSuperUser(): boolean {
      return this.user?.is_superuser || false;
    },

    /**
     * 用户显示名称
     */
    displayName(): string {
      if (!this.user) return '';
      return this.user.nickname || this.user.username || '';
    },
  },

  actions: {
    /**
     * 登录
     */
    async login(username: string, password: string) {
      try {
        this.isLoading = true;
        
        const result = await api.auth.login({ username, password });
        
        // LoginResponse 直接包含 access_token 和 user，不需要 .data
        if (result.access_token && result.user) {
          // 保存 Token
          saveToken(result.access_token);
          
          // 更新用户信息
          this.user = result.user;
          this.isLoggedIn = true;
          
          console.log('登录成功:', this.user);
          return true;
        }
        
        throw new Error('登录失败：未获取到有效的 Token');
      } catch (error: any) {
        console.error('登录失败:', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * 退出登录
     */
    async logout() {
      try {
        this.isLoading = true;
        
        // 调用后端登出接口
        await api.auth.logout().catch(() => {
          // 忽略后端错误，继续清理本地数据
          console.warn('后端登出请求失败，继续清理本地数据');
        });
      } catch (error) {
        console.error('登出失败:', error);
      } finally {
        // 清除本地数据
        removeToken();
        this.user = null;
        this.isLoggedIn = false;
        this.isLoading = false;
      }
    },

    /**
     * 检查认证状态
     * 应用启动时调用，验证本地 Token 是否有效
     */
    async checkAuth() {
      try {
        // 检查是否有 Token
        if (!hasToken()) {
          this.isLoggedIn = false;
          return false;
        }

        this.isLoading = true;
        
        // 请求用户信息验证 Token
        const result = await api.auth.getCurrentUser();
        
        // getCurrentUser 返回的是 User 对象，不是包装的响应
        if (result) {
          this.user = result;
          this.isLoggedIn = true;
          console.log('Token 有效，用户:', this.user);
          return true;
        }
        
        // Token 无效，清除本地数据
        this.clearAuth();
        return false;
      } catch (error) {
        console.error('验证 Token 失败:', error);
        this.clearAuth();
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * 清除认证数据
     */
    clearAuth() {
      removeToken();
      this.user = null;
      this.isLoggedIn = false;
    },
  },
});

