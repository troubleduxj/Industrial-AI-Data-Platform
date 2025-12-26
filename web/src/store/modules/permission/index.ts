/**
 * 权限状态管理 Store
 * 迁移到 TypeScript + Shared 层类型定义
 */
import { defineStore } from 'pinia'
import type { Menu } from '@device-monitor/shared/types'
import { basicRoutes, vueModules } from '@/router/routes'
import api from '@/api'
import { apiV2 } from '@/api/v2'
import { authApi } from '@/api/system-v2'
import { useUserStore } from '@/store/modules/user'
import type { RouteRecordRaw } from 'vue-router'

// 使用动态导入Layout组件
const Layout = () => import('@/layout/index.vue')

/**
 * 后端菜单数据接口（与后端返回格式对应）
 */
interface BackendMenu {
  name: string
  path: string
  icon?: string
  order?: number
  is_hidden?: boolean
  keepalive?: boolean
  redirect?: string
  component?: string
  menuType?: string  // 菜单类型：catalog, menu, button
  type?: string      // 菜单类型（兼容字段）
  children?: BackendMenu[]
}

/**
 * Permission Store 状态接口
 */
interface PermissionState {
  accessRoutes: RouteRecordRaw[]
  accessApis: string[]
  isLoadingApis: boolean
}

/**
 * 查找组件函数
 */
function findComponent(path: string | undefined | null) {
  if (!path || typeof path !== 'string') {
    console.warn(`Invalid component path: ${path}`)
    return null
  }

  // 移除开头的 '/' 并清理路径
  let cleanPath = path.startsWith('/') ? path.substring(1) : path

  // 移除多余的斜杠并清理空段
  cleanPath = cleanPath
    .split('/')
    .filter((segment) => segment.trim() !== '')
    .join('/')

  if (!cleanPath) {
    console.warn(`Empty component path after cleaning: ${path}`)
    return null
  }

  // 构造多种可能的路径格式（兼容不同的 import.meta.glob 返回格式）
  const possiblePaths = [
    `/src/views/${cleanPath}/index.vue`,
    `/src/views/${cleanPath}.vue`,
    `@/views/${cleanPath}/index.vue`,
    `@/views/${cleanPath}.vue`,
    `../views/${cleanPath}/index.vue`,
    `../views/${cleanPath}.vue`,
  ]

  // 检查哪个路径存在于 vueModules 中
  for (const tryPath of possiblePaths) {
    if (vueModules[tryPath]) {
      console.log(`✅ Found component for path: ${path} -> ${tryPath}`)
      return vueModules[tryPath]
    }
  }

  // 尝试模糊匹配：遍历所有模块，查找包含 cleanPath 的路径
  const moduleKeys = Object.keys(vueModules)
  for (const moduleKey of moduleKeys) {
    // 检查模块路径是否以 cleanPath 结尾（忽略 /index.vue 后缀）
    const normalizedKey = moduleKey.replace('/index.vue', '').replace('.vue', '')
    if (normalizedKey.endsWith(cleanPath) || normalizedKey.endsWith(`/${cleanPath}`)) {
      console.log(`✅ Found component via fuzzy match for path: ${path} -> ${moduleKey}`)
      return vueModules[moduleKey]
    }
  }

  // 如果都找不到，打印警告并返回 null（包含可用的模块列表用于调试）
  const availableModules = Object.keys(vueModules).slice(0, 20)
  console.warn(
    `Component not found for path: ${path}. Cleaned path: ${cleanPath}. Tried paths:`, possiblePaths,
    `\nAvailable modules (first 20):`, availableModules
  )
  return null
}

/**
 * 根据后端传来数据构建出前端路由
 */
function buildRoutes(routes: BackendMenu[] = []): RouteRecordRaw[] {
  return routes.map((e) => {
    // 父路由路径：确保以 '/' 开头
    const normalizedPath = e.path && !e.path.startsWith('/') ? `/${e.path}` : e.path
    
    const route: RouteRecordRaw = {
      name: e.name,
      path: normalizedPath,
      component: Layout,
      meta: {
        title: e.name,
        icon: e.icon,
        order: e.order,
        keepAlive: e.keepalive,
        isHidden: e.is_hidden,
      },
      redirect: e.redirect,
      children: [],
    }

    if (e.children && e.children.length > 0) {
      // 有子菜单 - 过滤掉按钮类型的菜单项（button类型没有路由）
      const menuChildren = e.children.filter((child) => {
        // 过滤掉按钮类型（menu_type === 'button' 或 type === 'button'）
        const menuType = child.menuType || child.type
        if (menuType === 'button') {
          return false
        }
        // 过滤掉没有路径的菜单项
        if (!child.path) {
          return false
        }
        return true
      })

      route.children = menuChildren.map((e_child) => {
        const component = findComponent(e_child.component)
        // 子路由路径：应该是相对路径，移除前导斜杠
        let childPath = e_child.path
        if (childPath && childPath.startsWith('/')) {
          childPath = childPath.substring(1)
        }
        
        const routeInfo: RouteRecordRaw = {
          name: e_child.name,
          path: childPath,
          component: component || (() => import('@/views/error-page/404.vue')),
          meta: {
            title: e_child.name,
            icon: e_child.icon,
            order: e_child.order,
            keepAlive: e_child.keepalive,
            isHidden: e_child.is_hidden,
          },
        }

        // 强制为菜单管理页面开启 keepAlive 并同步 name
        if (e_child.name === '菜单管理') {
          routeInfo.name = 'SystemMenu'
          if (routeInfo.meta) {
            routeInfo.meta.keepAlive = true
          }
        }

        return routeInfo
      })
    } else {
      // 没有子菜单，创建一个默认的子路由
      const component = e.component === 'Layout' ? null : findComponent(e.component)
      route.children = [{
        name: `${e.name}Default`,
        path: '',
        component: component || (() => import('@/views/error-page/404.vue')),
        meta: {
          title: e.name,
          icon: e.icon,
          order: e.order,
          keepAlive: e.keepalive,
          isHidden: true,
        },
      }]
    }

    return route
  })
}

// 导出增强版权限Store
export { useEnhancedPermissionStore, PermissionType, PermissionMode } from './enhanced-permission-store'

/**
 * 权限 Store
 */
export const usePermissionStore = defineStore('permission', {
  state: (): PermissionState => ({
    accessRoutes: [],
    accessApis: [],
    isLoadingApis: false,
  }),

  getters: {
    /**
     * 所有路由（基础路由 + 权限路由）
     */
    routes(): RouteRecordRaw[] {
      return basicRoutes.concat(this.accessRoutes)
    },

    /**
     * 菜单列表（过滤隐藏菜单）
     */
    menus(): RouteRecordRaw[] {
      return this.routes.filter((route) => route.name && !route.meta?.isHidden)
    },

    /**
     * API 权限列表
     */
    apis(): string[] {
      return this.accessApis
    },
  },

  actions: {
    /**
     * 生成路由
     */
    async generateRoutes(): Promise<RouteRecordRaw[]> {
      console.log('✅ Shared API: permissionStore.generateRoutes() - 使用 Shared Menu 类型')
      console.log('permissionStore.generateRoutes: Calling apiV2.getUserMenu()')
      
      const res = await apiV2.getUserMenu() // 调用v2版本接口获取后端传来的菜单路由
      console.log('permissionStore.generateRoutes: Received response from apiV2.getUserMenu()', res)
      
      this.accessRoutes = buildRoutes(res.data) // 处理成前端路由格式
      return this.accessRoutes
    },

    /**
     * 获取用户 API 权限
     */
    async getAccessApis(): Promise<string[] | undefined> {
      try {
        // 首先检查是否正在登出，如果是则立即返回
        const userStore = useUserStore()
        if (userStore.isLoggingOut) {
          console.log('permissionStore.getAccessApis: 正在登出中，跳过权限API调用')
          return
        }
        
        // 检查token是否存在，如果不存在则不调用API
        if (!userStore.token) {
          console.log('permissionStore.getAccessApis: 无token，跳过权限API调用')
          return
        }
        
        this.isLoadingApis = true
        console.log('✅ Shared API: permissionStore.getAccessApis()')
        console.log('permissionStore.getAccessApis: Calling authApi.getUserApis()')
        
        // 在API调用前再次检查登出状态
        if (userStore.isLoggingOut) {
          console.log('permissionStore.getAccessApis: API调用前检测到登出状态，取消调用')
          return
        }
        
        const res = await authApi.getUserApis()
        
        // API调用完成后再次检查登出状态
        if (userStore.isLoggingOut) {
          console.log('permissionStore.getAccessApis: API调用完成后检测到登出状态，忽略结果')
          return
        }
        
        console.log('permissionStore.getAccessApis: Received response from authApi.getUserApis()', res)
        this.accessApis = res.data
        return this.accessApis
      } catch (error: any) {
        console.error('permissionStore.getAccessApis: Error loading APIs', error)
        
        // 检查是否是登出过程中的错误，如果是则不抛出异常
        const userStore = useUserStore()
        if (userStore.isLoggingOut) {
          console.log('permissionStore.getAccessApis: 登出过程中的API错误，忽略')
          return
        }
        
        // 如果是401错误且不在登出状态，记录但不抛出异常避免弹窗
        if (error.response?.status === 401) {
          console.log('permissionStore.getAccessApis: 401错误，可能需要重新登录')
          return
        }
        
        throw error
      } finally {
        this.isLoadingApis = false
      }
    },

    /**
     * 重置权限数据
     */
    resetPermission(): void {
      this.$reset()
    },
  },
})

