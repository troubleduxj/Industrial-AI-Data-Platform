/**
 * 权限调试工具
 */

import { useUserStore } from '@/store/modules/user'
import { useEnhancedPermissionStore } from '@/store/modules/permission'

export class PermissionDebugger {
  constructor() {
    this.userStore = useUserStore()
    this.permissionStore = useEnhancedPermissionStore()
  }

  /**
   * 调试用户权限信息
   */
  debugUserPermissions() {
    console.group('🔍 用户权限调试信息')

    // 用户基本信息
    console.log('👤 用户信息:', {
      id: this.userStore.userId,
      username: this.userStore.username,
      isSuperUser: this.userStore.isSuperUser,
      isLoggingOut: this.userStore.isLoggingOut,
      token: this.userStore.token ? `${this.userStore.token.substring(0, 20)}...` : 'null',
    })

    // 权限加载状态
    console.log('⏳ 权限加载状态:', {
      isLoadingRoutes: this.permissionStore.isLoadingRoutes,
      isLoadingApis: this.permissionStore.isLoadingApis,
      isLoadingMenus: this.permissionStore.isLoadingMenus,
      isLoading: this.permissionStore.isLoading,
    })

    // 权限数据统计
    console.log('📊 权限数据统计:', this.permissionStore.getPermissionStats())

    // 菜单权限
    console.log('🍽️ 菜单权限:', {
      userMenus: this.permissionStore.userMenus,
      menuPermissions: this.permissionStore.menuPermissions,
      accessRoutes: this.permissionStore.accessRoutes,
    })

    // API权限
    console.log('🔌 API权限:', {
      accessApis: this.permissionStore.accessApis,
      count: this.permissionStore.accessApis.length,
    })

    console.groupEnd()
  }

  /**
   * 调试菜单生成过程
   */
  async debugMenuGeneration() {
    console.group('🏗️ 菜单生成调试')

    try {
      console.log('开始生成菜单...')

      // 强制刷新菜单
      await this.permissionStore.getUserMenus(true)

      console.log('菜单生成完成:', {
        userMenus: this.permissionStore.userMenus,
        menuCount: this.permissionStore.userMenus.length,
      })

      // 检查维修记录相关菜单
      const repairMenus = this.findRepairMenus(this.permissionStore.userMenus)
      console.log('🔧 维修记录相关菜单:', repairMenus)
    } catch (error) {
      console.error('菜单生成失败:', error)
    }

    console.groupEnd()
  }

  /**
   * 查找维修记录相关菜单
   */
  findRepairMenus(menus) {
    const repairMenus = []

    const searchMenus = (menuList, parentPath = '') => {
      menuList.forEach((menu) => {
        const menuName = menu.name || ''
        const menuPath = menu.path || ''
        const fullPath = parentPath + menuPath

        // 检查是否是维修相关菜单
        if (
          menuName.includes('维修') ||
          menuName.includes('维护') ||
          menuPath.includes('repair') ||
          menuPath.includes('maintenance')
        ) {
          repairMenus.push({
            ...menu,
            fullPath,
            parentPath,
          })
        }

        // 递归检查子菜单
        if (menu.children && menu.children.length > 0) {
          searchMenus(menu.children, fullPath + '/')
        }
      })
    }

    searchMenus(menus)
    return repairMenus
  }

  /**
   * 检查特定权限
   */
  checkPermission(permission) {
    console.group(`🔐 权限检查: ${permission}`)

    const hasPermission = this.permissionStore.hasPermission(permission)
    console.log('权限检查结果:', hasPermission)

    // 检查权限来源
    const allPermissions = this.permissionStore.allPermissions
    const menuPermissions = this.permissionStore.menuPermissions
    const apiPermissions = this.permissionStore.accessApis
      .map((api) => api.permission)
      .filter(Boolean)

    console.log('权限来源分析:', {
      inAllPermissions: allPermissions.includes(permission),
      inMenuPermissions: menuPermissions.includes(permission),
      inApiPermissions: apiPermissions.includes(permission),
    })

    console.groupEnd()
    return hasPermission
  }

  /**
   * 模拟菜单权限问题
   */
  simulateMenuIssue() {
    console.group('🧪 模拟菜单权限问题')

    // 检查常见问题
    const issues = []

    // 1. 检查token
    if (!this.userStore.token) {
      issues.push('❌ 用户未登录或token已过期')
    }

    // 2. 检查用户信息
    if (!this.userStore.userId) {
      issues.push('❌ 用户信息未加载')
    }

    // 3. 检查菜单数据
    if (this.permissionStore.userMenus.length === 0) {
      issues.push('❌ 菜单数据为空')
    }

    // 4. 检查权限加载状态
    if (this.permissionStore.isLoading) {
      issues.push('⏳ 权限数据仍在加载中')
    }

    // 5. 检查缓存
    const cacheHitRate = this.permissionStore.cacheHitRate
    if (cacheHitRate < 50) {
      issues.push(`⚠️ 缓存命中率较低: ${cacheHitRate}%`)
    }

    console.log('问题检查结果:', issues.length > 0 ? issues : ['✅ 未发现明显问题'])

    console.groupEnd()
    return issues
  }

  /**
   * 生成权限报告
   */
  generatePermissionReport() {
    const report = {
      timestamp: new Date().toISOString(),
      user: {
        id: this.userStore.userId,
        username: this.userStore.username,
        isSuperUser: this.userStore.isSuperUser,
      },
      permissions: {
        total: this.permissionStore.allPermissions.length,
        menu: this.permissionStore.menuPermissions.length,
        api: this.permissionStore.accessApis.length,
      },
      menus: {
        total: this.permissionStore.userMenus.length,
        repair: this.findRepairMenus(this.permissionStore.userMenus).length,
      },
      cache: {
        hitRate: this.permissionStore.cacheHitRate,
        stats: this.permissionStore.getPermissionStats(),
      },
      issues: this.simulateMenuIssue(),
    }

    console.log('📋 权限系统报告:', report)
    return report
  }
}

// 创建全局调试实例
export const permissionDebugger = new PermissionDebugger()

// 在开发环境下暴露到全局
if (import.meta.env.DEV) {
  window.permissionDebugger = permissionDebugger
}

// 权限调试快捷方法
export const debugPermissions = () => {
  permissionDebugger.debugUserPermissions()
}

export const debugMenus = () => {
  permissionDebugger.debugMenuGeneration()
}

export const checkPermission = (permission) => {
  return permissionDebugger.checkPermission(permission)
}

export const generateReport = () => {
  return permissionDebugger.generatePermissionReport()
}
