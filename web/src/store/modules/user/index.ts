/**
 * 用户状态管理 Store
 * 迁移到 TypeScript + Shared 层类型定义
 */
import { defineStore } from 'pinia'
import type { User } from '@device-monitor/shared/types'
import { resetRouter } from '@/router'
import { useTagsStore, usePermissionStore } from '@/store'
import { removeToken, toLogin, getToken } from '@/utils'
import { authApi } from '@/api/system-v2'

/**
 * User Store 状态接口
 */
interface UserState {
  userInfo: Partial<User>
  isLoggingOut: boolean
}

/**
 * 用户 Store
 */
export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userInfo: {},
    isLoggingOut: false
  }),

  getters: {
    /**
     * 用户 ID
     */
    userId(): number | undefined {
      return this.userInfo?.id
    },

    /**
     * 用户名
     */
    name(): string | undefined {
      return this.userInfo?.username
    },

    /**
     * 邮箱
     */
    email(): string | undefined {
      return this.userInfo?.email
    },

    /**
     * 头像
     */
    avatar(): string | undefined {
      return this.userInfo?.avatar
    },

    /**
     * 角色列表
     */
    role(): User['roles'] {
      return this.userInfo?.roles || []
    },

    /**
     * 是否为超级用户
     */
    isSuperUser(): boolean {
      return this.userInfo?.isSuperuser || false
    },

    /**
     * 是否激活
     */
    isActive(): boolean {
      return this.userInfo?.isActive !== false
    },

    /**
     * Token
     */
    token(): string | null {
      return getToken()
    },
  },

  actions: {
    /**
     * 获取用户信息
     */
    async getUserInfo(): Promise<User | undefined> {
      console.log('✅ Shared API: userStore.getUserInfo() - 使用 Shared 类型')
      
      try {
        const res = await authApi.getUserInfo()
        console.log('userStore.getUserInfo: Received response from authApi.getUserInfo()', res)
        
        // 检查响应格式，避免因为格式问题导致错误判断
        if (res && res.data) {
          const userData = res.data as User
          const { id, username, email, avatar, roles, isSuperuser, isActive } = userData
          
          // 使用 Shared User 类型
          this.userInfo = { 
            id, 
            username, 
            email, 
            avatar, 
            roles, 
            isSuperuser, 
            isActive 
          }
          
          return userData
        } else if (res && res.code === 401) {
          console.warn('userStore.getUserInfo: 401 Unauthorized, but not auto-logout to prevent loop')
          throw new Error('Unauthorized')
        } else {
          throw new Error('Invalid response format')
        }
      } catch (error) {
        console.error('userStore.getUserInfo: Error fetching user info', error)
        // 不要自动logout，避免循环调用
        throw error
      }
    },

    /**
     * 退出登录
     */
    async logout(): Promise<void> {
      try {
        // 立即设置登出状态，防止权限检查和API调用
        this.isLoggingOut = true
        console.log('开始登出流程，设置isLoggingOut=true')
        
        // 短暂延迟，让权限指令和其他组件有时间响应登出状态
        await new Promise(resolve => setTimeout(resolve, 100))
        
        const { resetTags } = useTagsStore()
        const { resetPermission } = usePermissionStore()
        
        // 先清理token和权限数据
        removeToken()
        resetTags()
        resetPermission()
        resetRouter()
        
        // 保存登出状态，因为$reset会重置所有state
        const wasLoggingOut = this.isLoggingOut
        this.$reset()
        
        // 重新设置登出状态，确保在跳转期间保持
        this.isLoggingOut = wasLoggingOut
        
        console.log('登出清理完成，准备跳转登录页')
        toLogin()
        
        // 跳转完成后再重置登出状态
        setTimeout(() => {
          this.isLoggingOut = false
          console.log('登出流程完成，重置isLoggingOut=false')
        }, 200)
        
      } catch (error) {
        console.error('Logout error:', error)
        // 即使出错也要重置登出状态
        this.isLoggingOut = false
        throw error
      }
    },

    /**
     * 设置用户信息
     */
    setUserInfo(userInfo: Partial<User> = {}): void {
      this.userInfo = { ...this.userInfo, ...userInfo }
    },
  },
})

