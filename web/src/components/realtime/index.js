/**
 * 实时监控组件
 * 
 * 需求: 7.1 - 7.6 前端实时监控增强
 */

export { default as RealtimeChart } from './RealtimeChart.vue'
export { default as AlertNotification } from './AlertNotification.vue'
export { default as PredictionDisplay } from './PredictionDisplay.vue'
export { default as ConnectionStatus } from './ConnectionStatus.vue'

// Composables
export { useRealtimeSettings, REFRESH_INTERVAL_OPTIONS, DISPLAY_PRECISION_OPTIONS } from './useRealtimeSettings'

// 默认导出所有组件
export default {
  RealtimeChart: () => import('./RealtimeChart.vue'),
  AlertNotification: () => import('./AlertNotification.vue'),
  PredictionDisplay: () => import('./PredictionDisplay.vue'),
  ConnectionStatus: () => import('./ConnectionStatus.vue')
}
