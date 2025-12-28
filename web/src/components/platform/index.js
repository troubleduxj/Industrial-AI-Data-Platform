/**
 * 工业AI数据平台 - 动态UI组件
 * 基于元数据驱动的配置化UI组件库
 * 
 * 功能特性：
 * - 基于信号定义自动生成表单字段
 * - 支持多种数据类型和验证规则
 * - 响应式设计，支持桌面和移动端
 * - 基于信号配置生成图表
 * - 支持实时数据更新
 * - 基于资产类别动态生成菜单
 * - 支持权限控制和面包屑导航
 */

// 动态表单组件
export { default as DynamicAssetForm } from './form/DynamicAssetForm.vue'
export { default as SignalFieldRenderer } from './form/SignalFieldRenderer.vue'

// 动态数据显示组件
export { default as DynamicDataDisplay } from './display/DynamicDataDisplay.vue'
export { default as SignalCard } from './display/SignalCard.vue'
export { default as SignalChart } from './display/SignalChart.vue'
export { default as RealtimeMonitor } from './display/RealtimeMonitor.vue'

// 导航组件
export { default as AssetCategoryMenu } from './navigation/AssetCategoryMenu.vue'
export { default as DynamicBreadcrumb } from './navigation/DynamicBreadcrumb.vue'

// 组合式函数
export { useSignalDefinitions } from './composables/useSignalDefinitions'
export { useAssetCategories } from './composables/useAssetCategories'
export { useDynamicForm } from './composables/useDynamicForm'

// 默认导出所有组件
export default {
  // 表单组件
  DynamicAssetForm: () => import('./form/DynamicAssetForm.vue'),
  SignalFieldRenderer: () => import('./form/SignalFieldRenderer.vue'),
  // 显示组件
  DynamicDataDisplay: () => import('./display/DynamicDataDisplay.vue'),
  SignalCard: () => import('./display/SignalCard.vue'),
  SignalChart: () => import('./display/SignalChart.vue'),
  RealtimeMonitor: () => import('./display/RealtimeMonitor.vue'),
  // 导航组件
  AssetCategoryMenu: () => import('./navigation/AssetCategoryMenu.vue'),
  DynamicBreadcrumb: () => import('./navigation/DynamicBreadcrumb.vue')
}
