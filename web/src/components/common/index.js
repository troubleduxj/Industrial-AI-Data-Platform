/**
 * 通用组件统一导出
 * 提供项目中可复用的通用组件
 */

// 同步导出 - 用于直接引用
export { default as AppProvider } from './AppProvider.vue'
export { default as AppFooter } from './AppFooter.vue'
export { default as LoadingEmptyWrapper } from './LoadingEmptyWrapper.vue'
export { default as PermissionButton } from './PermissionButton.vue'
export { default as ScrollX } from './ScrollX.vue'
export { default as ViewToggle } from './ViewToggle.vue'
export { default as BatchDeleteButton } from './BatchDeleteButton.vue'
export { default as BatchDeleteConfirmDialog } from './BatchDeleteConfirmDialog.vue'
export { default as StatusIndicator } from './StatusIndicator.vue'

// 视图切换选项配置
export * from './view-toggle-options.js'

// 异步导出 - 用于懒加载
export default {
  AppProvider: () => import('./AppProvider.vue'),
  AppFooter: () => import('./AppFooter.vue'),
  LoadingEmptyWrapper: () => import('./LoadingEmptyWrapper.vue'),
  PermissionButton: () => import('./PermissionButton.vue'),
  ScrollX: () => import('./ScrollX.vue'),
  ViewToggle: () => import('./ViewToggle.vue'),
  BatchDeleteButton: () => import('./BatchDeleteButton.vue'),
  BatchDeleteConfirmDialog: () => import('./BatchDeleteConfirmDialog.vue'),
  StatusIndicator: () => import('./StatusIndicator.vue')
}

// 组件类型定义（用于TypeScript支持）
export interface CommonComponentsMap {
  AppProvider: typeof import('./AppProvider.vue').default
  AppFooter: typeof import('./AppFooter.vue').default
  LoadingEmptyWrapper: typeof import('./LoadingEmptyWrapper.vue').default
  PermissionButton: typeof import('./PermissionButton.vue').default
  ScrollX: typeof import('./ScrollX.vue').default
  ViewToggle: typeof import('./ViewToggle.vue').default
  BatchDeleteButton: typeof import('./BatchDeleteButton.vue').default
  BatchDeleteConfirmDialog: typeof import('./BatchDeleteConfirmDialog.vue').default
}

// 组件安装函数（用于全局注册）
export function installCommonComponents(app) {
  const components = {
    AppProvider: () => import('./AppProvider.vue'),
    AppFooter: () => import('./AppFooter.vue'),
    LoadingEmptyWrapper: () => import('./LoadingEmptyWrapper.vue'),
    PermissionButton: () => import('./PermissionButton.vue'),
    ScrollX: () => import('./ScrollX.vue'),
    ViewToggle: () => import('./ViewToggle.vue'),
    BatchDeleteButton: () => import('./BatchDeleteButton.vue'),
    BatchDeleteConfirmDialog: () => import('./BatchDeleteConfirmDialog.vue')
  }
  
  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}
