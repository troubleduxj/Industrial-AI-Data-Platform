import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import { setupRouterGuard } from './guard'
import { basicRoutes, asyncRoutes, EMPTY_ROUTE, NOT_FOUND_ROUTE } from './routes'
import { getToken, isNullOrWhitespace } from '@/utils'
import { useUserStore, usePermissionStore } from '@/store'
import { smartPreloader } from './lazy-routes'
import { performanceMonitor } from '@/utils/performance'
import { dynamicRouteManager } from './dynamic-routes'

const isHash = import.meta.env.VITE_USE_HASH === 'true'
export const router = createRouter({
  history: isHash ? createWebHashHistory('/') : createWebHistory('/'),
  routes: basicRoutes,
  scrollBehavior: () => ({ left: 0, top: 0 }),
})

// 添加路由性能监控
router.beforeEach((to, from, next) => {
  // 记录路由访问
  if (to.path !== from.path) {
    smartPreloader.recordAccess(to.path)
    performanceMonitor.mark(`route-${to.name || to.path}`)
  }
  next()
})

router.afterEach((to, from) => {
  // 测量路由切换时间
  if (to.path !== from.path) {
    performanceMonitor.measure(`route-${to.name || to.path}`)

    // 预加载相关路由
    smartPreloader.preloadRelatedRoutes(to.path)
  }
})

export async function setupRouter(app) {
  console.log('🛣️ 开始设置路由系统...')

  try {
    console.log('🔧 设置动态路由管理器的router实例...')
    dynamicRouteManager.setRouter(router)
    console.log('✅ 动态路由管理器router实例设置完成')

    console.log('🚀 初始化动态路由管理器...')
    try {
      await dynamicRouteManager.initialize()
      console.log('✅ 动态路由管理器初始化成功')
    } catch (error) {
      console.error('❌ 动态路由初始化失败，使用备用方案:', error)
      console.log('🔄 启动备用路由方案...')
      await addDynamicRoutes() // 备用方案
      console.log('✅ 备用路由方案完成')
    }

    console.log('🛡️ 设置路由守卫...')
    setupRouterGuard(router)
    console.log('✅ 路由守卫设置完成')

    console.log('📱 注册路由到应用...')
    app.use(router)
    console.log('✅ 路由注册完成')
  } catch (error) {
    console.error('❌ 路由系统设置失败:', error)
    console.error('错误堆栈:', error.stack)
    throw error
  }
}

export async function resetRouter() {
  // 使用动态路由管理器重置路由
  dynamicRouteManager.resetDynamicRoutes()
}

export async function refreshRouter() {
  // 刷新动态路由
  await dynamicRouteManager.refreshDynamicRoutes()
}

export async function addDynamicRoutes() {
  // 开始性能监控
  performanceMonitor.mark('dynamic-routes')

  const token = getToken()

  // 没有token情况
  if (isNullOrWhitespace(token)) {
    router.addRoute(EMPTY_ROUTE)
    return
  }

  // 有token的情况
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  // 检查是否正在登出，如果是则跳过动态路由加载
  if (userStore.isLoggingOut) {
    console.log('正在登出，跳过动态路由加载')
    return
  }
  console.log('addDynamicRoutes: Before getUserInfo. userId:', userStore.userId)

  // 安全地获取用户信息，避免因为网络问题导致路由初始化失败
  if (!userStore.userId) {
    try {
      await userStore.getUserInfo()
      console.log('addDynamicRoutes: getUserInfo success. userId:', userStore.userId)
    } catch (error) {
      console.error('addDynamicRoutes: getUserInfo failed, but continue:', error)
      // 如果获取用户信息失败，但token存在，继续执行路由初始化
      // 这样可以避免因为网络问题导致应用无法使用
    }
  }

  console.log('addDynamicRoutes: After getUserInfo. userId:', userStore.userId)

  try {
    console.log('addDynamicRoutes: Before generateRoutes')
    const accessRoutes = await permissionStore.generateRoutes()
    console.log('addDynamicRoutes: After generateRoutes. accessRoutes:', accessRoutes)
    console.log('addDynamicRoutes: Before getAccessApis')
    try {
      await permissionStore.getAccessApis()
      console.log('addDynamicRoutes: getAccessApis success')
    } catch (error) {
      console.error('addDynamicRoutes: getAccessApis failed, but continue:', error)
      // 如果获取权限失败，继续执行，让权限指令自己处理
    }
    console.log('addDynamicRoutes: After getAccessApis')

    // 添加从后端获取的动态路由
    accessRoutes.forEach((route) => {
      try {
        // 验证父路由路径格式（应该以 '/' 开头）
        if (route.path && !route.path.startsWith('/')) {
          console.warn(
            `Parent route path should start with '/': "${route.path}" should be "/${route.path}"`
          )
          route.path = `/${route.path}`
        }

        // 验证子路由路径格式（应该是相对路径，不以 '/' 开头）
        if (route.children && route.children.length > 0) {
          route.children.forEach((child) => {
            // 子路由路径应该是相对路径，除了空字符串
            if (child.path && child.path.startsWith('/') && child.path !== '/') {
              console.warn(
                `Child route path should be relative: "${
                  child.path
                }" should be "${child.path.substring(1)}"`
              )
              child.path = child.path.substring(1)
            }
          })
        }

        !router.hasRoute(route.name) && router.addRoute(route)
      } catch (error) {
        console.error(`Error adding route ${route.name}:`, error)
        console.error('Route object:', route)
      }
    })

    // 添加静态定义的异步路由（如测试路由）
    console.log('Available async routes:', asyncRoutes.length)
    asyncRoutes.forEach((route) => {
      try {
        console.log('Adding async route:', route.name, route.path)
        !router.hasRoute(route.name) && router.addRoute(route)
        console.log('Route added successfully:', route.name)
      } catch (error) {
        console.error(`Error adding async route ${route.name}:`, error)
        console.error('Route object:', route)
      }
    })

    // 调试：打印所有已注册的路由
    console.log(
      'All registered routes:',
      router.getRoutes().map((r) => ({ name: r.name, path: r.path }))
    )

    router.hasRoute(EMPTY_ROUTE.name) && router.removeRoute(EMPTY_ROUTE.name)
    router.addRoute(NOT_FOUND_ROUTE)

    // 智能预加载用户可访问的路由
    smartPreloader.preloadByPermissions(accessRoutes)

    // 结束性能监控
    performanceMonitor.measure('dynamic-routes')
  } catch (error) {
    console.error('addDynamicRoutes error:', error)
    console.error('addDynamicRoutes error stack:', error.stack)
    const userStore = useUserStore()
    await userStore.logout()
  }
}

export function getRouteNames(routes) {
  return routes.map((route) => getRouteName(route)).flat(1)
}

function getRouteName(route) {
  const names = [route.name]
  if (route.children && route.children.length) {
    names.push(...route.children.map((item) => getRouteName(item)).flat(1))
  }
  return names
}
