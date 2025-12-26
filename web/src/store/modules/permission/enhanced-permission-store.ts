/**
 * 增强版权限Store
 * 基于Pinia实现的权限数据管理，支持权限数据获取、缓存、检查等功能
 * 迁移到 TypeScript + Shared 层类型定义
 */

import { defineStore } from 'pinia'
import { ref, computed, reactive, nextTick } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type { Menu, Role } from '@device-monitor/shared/types'
import { basicRoutes, vueModules } from '@/router/routes'
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
  perms?: string  // 权限标识（特别用于按钮权限）
  is_hidden?: boolean
  keepalive?: boolean
  redirect?: string
  component?: string
  type?: string  // 菜单类型：catalog, menu, button
  menuType?: string  // 菜单类型（驼峰格式）
  children?: BackendMenu[]
}

/**
 * 权限类型枚举
 */
export const PermissionType = {
  MENU: 'menu',
  API: 'api',
  BUTTON: 'button',
  ROUTE: 'route'
} as const

export type PermissionTypeValue = typeof PermissionType[keyof typeof PermissionType]

/**
 * 权限检查模式枚举
 */
export const PermissionMode = {
  ALL: 'all',        // 需要所有权限
  ANY: 'any',        // 需要任意一个权限
  EXACT: 'exact'     // 精确匹配权限
} as const

export type PermissionModeValue = typeof PermissionMode[keyof typeof PermissionMode]

/**
 * 缓存配置
 */
const CACHE_CONFIG = {
  MENU_TTL: 5 * 60 * 1000,      // 菜单缓存5分钟
  API_TTL: 3 * 60 * 1000,       // API权限缓存3分钟
  PERMISSION_TTL: 5 * 60 * 1000  // 权限缓存5分钟
}

/**
 * 缓存项接口
 */
interface CacheItem<T> {
  data: T | null
  timestamp: number
  ttl: number
}

/**
 * 缓存状态接口
 */
interface CacheState {
  menus: CacheItem<BackendMenu[]>
  apis: CacheItem<string[]>
  permissions: CacheItem<string[]>
}

/**
 * 权限统计接口
 */
interface PermissionStats {
  totalChecks: number
  cacheHits: number
  cacheMisses: number
  lastCheckTime: string | null
}

/**
 * 权限更新事件详情
 */
interface PermissionUpdateDetail {
  timestamp: number
  source: string
  type: string
}

/**
 * 组件查找函数
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
 * 构建路由函数
 */
function buildRoutes(routes: BackendMenu[] = []): RouteRecordRaw[] {
  return routes.map((e) => {
    // 父路由路径：确保以 '/' 开头
    const normalizedPath = e.path && !e.path.startsWith('/') ? `/${e.path}` : e.path

    const route: RouteRecordRaw = {
      name: e.name,
      path: normalizedPath,
      component: Layout,
      redirect: e.redirect,
      meta: {
        title: e.name,
        icon: e.icon,
        order: e.order,
        keepAlive: e.keepalive,
        permissions: e.perms ? [e.perms] : [],
        isHidden: e.is_hidden,
      },
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
            permissions: e_child.perms ? [e_child.perms] : [],
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
          permissions: e.perms ? [e.perms] : [],
          isHidden: true,
        },
      }]
    }

    return route
  })
}

/**
 * 增强版权限Store
 */
export const useEnhancedPermissionStore = defineStore('enhancedPermission', () => {
  // ===== 状态定义 =====

  // 路由相关
  const accessRoutes: Ref<RouteRecordRaw[]> = ref([])
  const isLoadingRoutes: Ref<boolean> = ref(false)

  // API权限相关
  const accessApis: Ref<string[]> = ref([])
  const isLoadingApis: Ref<boolean> = ref(false)

  // 菜单权限相关
  const userMenus: Ref<BackendMenu[]> = ref([])
  const menuPermissions: Ref<string[]> = ref([])
  const isLoadingMenus: Ref<boolean> = ref(false)

  // 按钮权限相关
  const buttonPermissions: Ref<string[]> = ref([])

  // 缓存相关
  const cache = reactive<CacheState>({
    menus: {
      data: null,
      timestamp: 0,
      ttl: CACHE_CONFIG.MENU_TTL
    },
    apis: {
      data: null,
      timestamp: 0,
      ttl: CACHE_CONFIG.API_TTL
    },
    permissions: {
      data: null,
      timestamp: 0,
      ttl: CACHE_CONFIG.PERMISSION_TTL
    }
  })

  // 权限检查统计
  const permissionStats = reactive<PermissionStats>({
    totalChecks: 0,
    cacheHits: 0,
    cacheMisses: 0,
    lastCheckTime: null
  })

  // ===== 计算属性 =====

  // 所有路由
  const routes: ComputedRef<RouteRecordRaw[]> = computed(() => {
    return basicRoutes.concat(accessRoutes.value)
  })

  // 菜单列表（过滤隐藏菜单）
  const menus: ComputedRef<RouteRecordRaw[]> = computed(() => {
    return routes.value.filter((route) => route.name && !route.meta?.isHidden)
  })

  // API权限列表
  const apis: ComputedRef<string[]> = computed(() => {
    return accessApis.value
  })

  // 所有权限标识
  const allPermissions: ComputedRef<string[]> = computed(() => {
    const permissions = new Set<string>()

    // 添加菜单权限
    menuPermissions.value.forEach(perm => permissions.add(perm))

    // 添加按钮权限
    buttonPermissions.value.forEach(perm => permissions.add(perm))

    // 添加API权限 - 后端返回的是字符串数组格式
    if (Array.isArray(accessApis.value)) {
      accessApis.value.forEach(api => {
        // 如果是字符串格式（后端返回格式）
        if (typeof api === 'string') {
          permissions.add(api)
        }
      })
    }

    return Array.from(permissions)
  })

  // 缓存命中率
  const cacheHitRate: ComputedRef<string> = computed(() => {
    const total = permissionStats.cacheHits + permissionStats.cacheMisses
    return total > 0 ? (permissionStats.cacheHits / total * 100).toFixed(2) : '0'
  })

  // 权限加载状态
  const isLoading: ComputedRef<boolean> = computed(() => {
    return isLoadingRoutes.value || isLoadingApis.value || isLoadingMenus.value
  })

  // ===== 缓存管理方法 =====

  /**
   * 检查缓存是否有效
   */
  const isCacheValid = (cacheKey: keyof CacheState): boolean => {
    const cacheItem = cache[cacheKey]
    if (!cacheItem || !cacheItem.data) return false

    const now = Date.now()
    return (now - cacheItem.timestamp) < cacheItem.ttl
  }

  /**
   * 设置缓存
   */
  const setCache = <T>(cacheKey: keyof CacheState, data: T): void => {
    const cacheItem = cache[cacheKey]
    cache[cacheKey] = {
      data: data as any,
      timestamp: Date.now(),
      ttl: cacheItem?.ttl || CACHE_CONFIG.PERMISSION_TTL
    }
  }

  /**
   * 获取缓存
   */
  const getCache = <T>(cacheKey: keyof CacheState): T | null => {
    if (isCacheValid(cacheKey)) {
      permissionStats.cacheHits++
      return cache[cacheKey].data as T
    }

    permissionStats.cacheMisses++
    return null
  }

  /**
   * 清除缓存
   */
  const clearCache = (cacheKey: keyof CacheState | null = null): void => {
    if (cacheKey) {
      cache[cacheKey] = {
        data: null,
        timestamp: 0,
        ttl: cache[cacheKey]?.ttl || CACHE_CONFIG.PERMISSION_TTL
      }
    } else {
      // 清除所有缓存
      (Object.keys(cache) as Array<keyof CacheState>).forEach(key => {
        cache[key] = {
          data: null,
          timestamp: 0,
          ttl: cache[key]?.ttl || CACHE_CONFIG.PERMISSION_TTL
        }
      })
    }
  }

  // ===== 数据获取方法 =====

  /**
   * 生成路由
   */
  const generateRoutes = async (): Promise<RouteRecordRaw[]> => {
    try {
      isLoadingRoutes.value = true
      console.log('✅ Shared API: enhancedPermissionStore.generateRoutes() - 使用 Shared Menu 类型')

      // 检查缓存
      const cachedMenus = getCache<BackendMenu[]>('menus')
      if (cachedMenus) {
        console.log('使用缓存的菜单数据生成路由')
        accessRoutes.value = buildRoutes(cachedMenus)
        return accessRoutes.value
      }

      console.log('从API获取菜单数据生成路由')
      const res = await apiV2.getUserMenu()

      if (res && res.data) {
        // 缓存菜单数据
        setCache('menus', res.data)

        // 构建路由
        accessRoutes.value = buildRoutes(res.data)

        // 提取菜单权限
        extractMenuPermissions(res.data)

        console.log('路由生成成功，共生成', accessRoutes.value.length, '个路由')
        return accessRoutes.value
      }

      throw new Error('获取菜单数据失败')

    } catch (error) {
      console.error('生成路由失败:', error)
      throw error
    } finally {
      isLoadingRoutes.value = false
    }
  }

  /**
   * 获取用户菜单
   */
  const getUserMenus = async (forceRefresh: boolean = false): Promise<BackendMenu[]> => {
    try {
      isLoadingMenus.value = true

      // 检查缓存
      if (!forceRefresh) {
        const cachedMenus = getCache<BackendMenu[]>('menus')
        if (cachedMenus) {
          console.log('使用缓存的菜单数据')
          userMenus.value = cachedMenus
          return cachedMenus
        }
      }

      console.log(`从API获取用户菜单 (强制刷新: ${forceRefresh})`)
      const res = await apiV2.getUserMenu()

      if (res && res.data) {
        userMenus.value = res.data

        // 缓存菜单数据
        setCache('menus', res.data)

        // 提取菜单权限
        extractMenuPermissions(res.data)

        // 发送菜单更新事件
        window.dispatchEvent(new CustomEvent<{ menus: BackendMenu[], timestamp: number, forceRefresh: boolean }>('user-menus-updated', {
          detail: {
            menus: res.data,
            timestamp: Date.now(),
            forceRefresh: forceRefresh
          }
        }))

        console.log('获取用户菜单成功，共', res.data.length, '个菜单')
        return res.data
      }

      throw new Error('获取用户菜单失败')

    } catch (error) {
      console.error('获取用户菜单失败:', error)
      throw error
    } finally {
      isLoadingMenus.value = false
    }
  }

  /**
   * 获取API权限
   */
  const getAccessApis = async (forceRefresh: boolean = false): Promise<string[] | undefined> => {
    try {
      // 检查用户登出状态
      const userStore = useUserStore()
      if (userStore.isLoggingOut) {
        console.log('正在登出中，跳过API权限获取')
        return
      }

      // 检查token
      if (!userStore.token) {
        console.log('无token，跳过API权限获取')
        return
      }

      isLoadingApis.value = true

      // 检查缓存
      if (!forceRefresh) {
        const cachedApis = getCache<string[]>('apis')
        if (cachedApis) {
          console.log('使用缓存的API权限数据')
          accessApis.value = cachedApis
          return cachedApis
        }
      }

      // 再次检查登出状态
      if (userStore.isLoggingOut) {
        console.log('API调用前检测到登出状态，取消调用')
        return
      }

      console.log('✅ Shared API: enhancedPermissionStore.getAccessApis()')
      console.log('从API获取用户API权限')
      const res = await authApi.getUserApis()

      // API调用完成后再次检查登出状态
      if (userStore.isLoggingOut) {
        console.log('API调用完成后检测到登出状态，忽略结果')
        return
      }

      if (res && res.data) {
        accessApis.value = res.data

        // 缓存API权限数据
        setCache('apis', res.data)

        console.log('获取API权限成功，共', res.data.length, '个API权限')
        return res.data
      }

      throw new Error('获取API权限失败')

    } catch (error: any) {
      console.error('获取API权限失败:', error)

      // 检查是否是登出过程中的错误
      const userStore = useUserStore()
      if (userStore.isLoggingOut) {
        console.log('登出过程中的API错误，忽略')
        return
      }

      // 如果是401错误且不在登出状态，记录但不抛出异常
      if (error.response?.status === 401) {
        console.log('401错误，可能需要重新登录')
        return
      }

      throw error
    } finally {
      isLoadingApis.value = false
    }
  }

  /**
   * 提取菜单权限
   */
  const extractMenuPermissions = (menus: BackendMenu[]): void => {
    const permissions = new Set<string>()

    const extractFromMenu = (menu: BackendMenu): void => {
      if (menu.perms) {
        permissions.add(menu.perms)
      }

      if (menu.children && menu.children.length > 0) {
        menu.children.forEach(extractFromMenu)
      }
    }

    menus.forEach(extractFromMenu)
    menuPermissions.value = Array.from(permissions)
  }

  // ===== 权限检查方法 =====

  /**
   * 检查是否有权限
   * @param permissions - 权限标识或权限标识数组
   * @param mode - 检查模式：all, any, exact
   * @returns 是否有权限
   */
  const hasPermission = (permissions: string | string[], mode: PermissionModeValue = PermissionMode.ANY): boolean => {
    try {
      // 检查用户是否为超级用户
      const userStore = useUserStore()
      
      console.group(`🔍 Store.hasPermission: 详细权限检查 - "${permissions}"`)
      console.log(`👤 用户信息:`, {
        username: userStore.userInfo?.username || userStore.name,
        isSuperUser: userStore.isSuperUser,
        token: !!userStore.token,
        isLoggingOut: userStore.isLoggingOut
      })
      
      if (userStore.isSuperUser) {
        console.log(`✅ 超级用户，直接通过`)
        console.groupEnd()
        return true
      }

      // 处理权限参数
      const permsToCheck = Array.isArray(permissions) ? permissions : [permissions]
      console.log(`📋 待检查权限:`, permsToCheck)
      console.log(`🔧 检查模式: ${mode}`)

      if (permsToCheck.length === 0) {
        console.log(`✅ 无权限要求，直接通过`)
        console.groupEnd()
        return true
      }

      // 获取用户所有权限
      const userPermissions = allPermissions.value
      console.log(`📊 用户权限总数: ${userPermissions.length}`)
      console.log(`📊 accessApis数据:`, {
        type: Array.isArray(accessApis.value) ? 'Array' : typeof accessApis.value,
        length: accessApis.value?.length || 0,
        sample: accessApis.value?.slice(0, 3) || []
      })
      
      // 显示维修相关权限
      const repairPermissions = userPermissions.filter(perm => 
        perm.includes('repair-records') || perm.includes('maintenance')
      )
      console.log(`🔧 用户的维修相关权限 (${repairPermissions.length}个):`, repairPermissions)

      // 权限检查函数 - 支持API路径参数匹配
      const checkSinglePermission = (permission: string): boolean => {
        console.log(`\n🎯 检查单个权限: "${permission}"`)
        
        // 1. 直接匹配
        const directMatch = userPermissions.includes(permission)
        console.log(`  1️⃣ 直接匹配: ${directMatch}`)
        if (directMatch) {
          return true
        }

        // 2. 如果是API权限格式 (METHOD /path)，进行路径参数匹配
        if (typeof permission === 'string' && permission.includes(' /api/')) {
          const parts = permission.split(' ')
          if (parts.length === 2) {
            const [method, path] = parts
            console.log(`  2️⃣ API权限格式检查: ${method} ${path}`)

            // 使用API权限检查方法
            const apiResult = hasApiPermission(path, method)
            console.log(`  2️⃣ API权限检查结果: ${apiResult}`)
            return apiResult
          }
        }

        console.log(`  ❌ 所有匹配方式都失败`)
        return false
      }

      // 根据模式检查权限
      let result = false
      console.log(`\n🔄 开始权限检查...`)
      
      switch (mode) {
        case PermissionMode.ALL:
          result = permsToCheck.every(checkSinglePermission)
          console.log(`📊 ALL模式结果: ${result}`)
          break

        case PermissionMode.ANY:
          result = permsToCheck.some(checkSinglePermission)
          console.log(`📊 ANY模式结果: ${result}`)
          break

        case PermissionMode.EXACT:
          result = permsToCheck.length === 1 && checkSinglePermission(permsToCheck[0])
          console.log(`📊 EXACT模式结果: ${result}`)
          break

        default:
          result = permsToCheck.some(checkSinglePermission)
          console.log(`📊 默认模式结果: ${result}`)
      }
      
      console.log(`\n🎉 最终结果: ${result ? '✅ 有权限' : '❌ 无权限'}`)
      console.groupEnd()

      // 异步更新统计，避免循环依赖
      nextTick(() => {
        permissionStats.totalChecks++
        permissionStats.lastCheckTime = new Date().toISOString()
      })

      return result
    } catch (error) {
      console.error('hasPermission error:', error)
      return false
    }
  }

  /**
   * 检查菜单权限
   */
  const hasMenuPermission = (permission: string): boolean => {
    const userStore = useUserStore()
    if (userStore.isSuperUser) {
      return true
    }

    return menuPermissions.value.includes(permission)
  }

  /**
   * 检查API权限
   */
  const hasApiPermission = (apiPath: string, method: string = 'GET'): boolean => {
    const userStore = useUserStore()
    const apiKey = `${method.toUpperCase()} ${apiPath}`
    
    console.group(`🌐 hasApiPermission: API权限检查 - "${apiKey}"`)
    
    if (userStore.isSuperUser) {
      console.log(`✅ 超级用户，直接通过`)
      console.groupEnd()
      return true
    }

    console.log(`📊 accessApis数据状态:`, {
      isArray: Array.isArray(accessApis.value),
      length: accessApis.value?.length || 0,
      type: typeof accessApis.value
    })

    // 后端返回的是字符串数组格式，需要适配
    if (!Array.isArray(accessApis.value)) {
      console.log(`❌ accessApis不是数组格式`)
      console.groupEnd()
      return false
    }

    console.log(`📋 所有API权限 (前10个):`, accessApis.value.slice(0, 10))
    
    // 查找相关权限
    const relatedPermissions = accessApis.value.filter(perm => 
      perm.includes(method.toUpperCase()) && 
      (perm.includes('repair-records') || perm.includes('maintenance'))
    )
    console.log(`🔧 相关的维修权限:`, relatedPermissions)

    // 1. 直接匹配字符串格式
    const directMatch = accessApis.value.includes(apiKey)
    console.log(`1️⃣ 直接匹配 "${apiKey}": ${directMatch}`)
    if (directMatch) {
      console.groupEnd()
      return true
    }

    // 2. 路径参数匹配 - 将 {id} 等参数替换为通配符
    const normalizedPath = apiPath.replace(/\/\{[^}]+\}/g, '/*')
    const normalizedApiKey = `${method.toUpperCase()} ${normalizedPath}`
    const paramMatch = accessApis.value.includes(normalizedApiKey)
    console.log(`2️⃣ 路径参数匹配 "${normalizedApiKey}": ${paramMatch}`)
    
    if (paramMatch) {
      console.groupEnd()
      return true
    }

    // 3. 精确的路径段匹配 - 只匹配相同路径深度的权限
    // 例如: /api/v2/devices/{id} 只匹配 /api/v2/devices/{id} 或 /api/v2/devices/*
    // 不匹配 /api/v2/devices/types/{id}
    const pathSegments = apiPath.split('/').filter(s => s)
    const matchingPermissions = accessApis.value.filter(permission => {
      if (typeof permission !== 'string') return false
      
      // 提取权限中的路径部分
      const permParts = permission.split(' ')
      if (permParts.length !== 2 || permParts[0] !== method.toUpperCase()) return false
      
      const permPath = permParts[1]
      const permSegments = permPath.split('/').filter(s => s)
      
      // 路径段数量必须相同
      if (pathSegments.length !== permSegments.length) return false
      
      // 逐段比较
      for (let i = 0; i < pathSegments.length; i++) {
        const apiSeg = pathSegments[i]
        const permSeg = permSegments[i]
        
        // 如果权限段是通配符，匹配任何内容
        if (permSeg === '*' || permSeg === '**') continue
        
        // 如果API段是参数（{xxx}），权限段也必须是参数或通配符
        if (apiSeg.startsWith('{') && apiSeg.endsWith('}')) {
          if (permSeg.startsWith('{') && permSeg.endsWith('}')) continue
          if (permSeg === '*' || permSeg === '**') continue
          return false
        }
        
        // 普通段必须完全匹配
        if (apiSeg !== permSeg) return false
      }
      
      return true
    })
    
    console.log(`3️⃣ 精确路径段匹配结果:`, matchingPermissions)
    const pathSegmentMatch = matchingPermissions.length > 0
    console.log(`3️⃣ 路径段匹配结果: ${pathSegmentMatch}`)

    console.log(`\n🎉 API权限检查最终结果: ${pathSegmentMatch ? '✅ 有权限' : '❌ 无权限'}`)
    console.groupEnd()
    
    return pathSegmentMatch
  }

  /**
   * 检查按钮权限
   */
  const hasButtonPermission = (permission: string): boolean => {
    const userStore = useUserStore()
    if (userStore.isSuperUser) {
      return true
    }

    return buttonPermissions.value.includes(permission) ||
      menuPermissions.value.includes(permission)
  }

  /**
   * 检查路由权限
   */
  const hasRoutePermission = (route: RouteRecordRaw): boolean => {
    const userStore = useUserStore()
    if (userStore.isSuperUser) {
      return true
    }

    // 如果路由没有权限要求，允许访问
    const permissions = route.meta?.permissions as string[] | undefined
    if (!permissions || permissions.length === 0) {
      return true
    }

    // 检查路由权限
    return hasPermission(permissions, PermissionMode.ANY)
  }

  // ===== 权限管理方法 =====

  /**
   * 刷新所有权限数据
   */
  const refreshPermissions = async (options: {
    clearCache?: boolean
    notifyUI?: boolean
    source?: string
  } = {}): Promise<void> => {
    try {
      const { 
        clearCache: shouldClearCache = true, 
        notifyUI = true,
        source = 'manual'
      } = options

      console.log(`开始刷新所有权限数据 (来源: ${source})`)

      // 清除缓存
      if (shouldClearCache) {
        clearCache()
      }

      // 并行获取所有权限数据
      await Promise.all([
        getUserMenus(true),
        getAccessApis(true)
      ])

      // 重新生成路由
      await generateRoutes()

      // 通知UI更新
      if (notifyUI) {
        await nextTick()
        
        // 发送权限更新事件
        window.dispatchEvent(new CustomEvent<PermissionUpdateDetail>('permission-data-updated', {
          detail: {
            timestamp: Date.now(),
            source: source,
            type: 'FULL_REFRESH'
          }
        }))

        // 强制Vue组件重新渲染
        if ((window as any).__VUE_APP__) {
          const app = (window as any).__VUE_APP__
          if (app.config.globalProperties.$forceUpdate) {
            app.config.globalProperties.$forceUpdate()
          }
        }
      }

      console.log('权限数据刷新完成')

    } catch (error) {
      console.error('刷新权限数据失败:', error)
      throw error
    }
  }

  /**
   * 重置权限数据
   */
  const resetPermission = (): void => {
    // 重置所有状态
    accessRoutes.value = []
    accessApis.value = []
    userMenus.value = []
    menuPermissions.value = []
    buttonPermissions.value = []

    // 重置加载状态
    isLoadingRoutes.value = false
    isLoadingApis.value = false
    isLoadingMenus.value = false

    // 清除缓存
    clearCache()

    // 重置统计
    permissionStats.totalChecks = 0
    permissionStats.cacheHits = 0
    permissionStats.cacheMisses = 0
    permissionStats.lastCheckTime = null

    console.log('权限数据已重置')
  }

  /**
   * 获取权限统计信息
   */
  const getPermissionStats = () => {
    return {
      ...permissionStats,
      cacheHitRate: cacheHitRate.value,
      totalPermissions: allPermissions.value.length,
      menuPermissions: menuPermissions.value.length,
      apiPermissions: accessApis.value.length,
      buttonPermissions: buttonPermissions.value.length,
      isLoading: isLoading.value
    }
  }

  // ===== 返回Store接口 =====

  return {
    // 状态
    accessRoutes,
    accessApis,
    userMenus,
    menuPermissions,
    buttonPermissions,
    isLoadingRoutes,
    isLoadingApis,
    isLoadingMenus,

    // 计算属性
    routes,
    menus,
    apis,
    allPermissions,
    cacheHitRate,
    isLoading,

    // 数据获取方法
    generateRoutes,
    getUserMenus,
    getAccessApis,

    // 权限检查方法
    hasPermission,
    hasMenuPermission,
    hasApiPermission,
    hasButtonPermission,
    hasRoutePermission,

    // 权限管理方法
    refreshPermissions,
    resetPermission,
    getPermissionStats,

    // 缓存管理方法
    clearCache,
    isCacheValid,

    // 常量
    PermissionType,
    PermissionMode
  }
})

/**
 * 权限检查器接口
 */
export interface PermissionChecker {
  check: (permissions: string | string[], mode?: PermissionModeValue) => boolean
  checkMenu: (permission: string) => boolean
  checkApi: (apiPath: string, method?: string) => boolean
  checkButton: (permission: string) => boolean
  checkRoute: (route: RouteRecordRaw) => boolean
}

/**
 * 创建权限检查器
 */
export const createPermissionChecker = (store: ReturnType<typeof useEnhancedPermissionStore>): PermissionChecker => {
  return {
    /**
     * 创建权限检查函数
     */
    check: (permissions: string | string[], mode: PermissionModeValue = PermissionMode.ANY) => {
      return store.hasPermission(permissions, mode)
    },

    /**
     * 创建菜单权限检查函数
     */
    checkMenu: (permission: string) => {
      return store.hasMenuPermission(permission)
    },

    /**
     * 创建API权限检查函数
     */
    checkApi: (apiPath: string, method: string = 'GET') => {
      return store.hasApiPermission(apiPath, method)
    },

    /**
     * 创建按钮权限检查函数
     */
    checkButton: (permission: string) => {
      return store.hasButtonPermission(permission)
    },

    /**
     * 创建路由权限检查函数
     */
    checkRoute: (route: RouteRecordRaw) => {
      return store.hasRoutePermission(route)
    }
  }
}

export default useEnhancedPermissionStore

