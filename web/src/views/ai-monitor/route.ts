import type { RouteRecordRaw } from 'vue-router'

const Layout = () => import('@/layout/index.vue')

const route: RouteRecordRaw = {
  name: 'AiMonitor',
  path: '/ai-monitor',
  component: Layout,
  redirect: '/ai-monitor/dashboard',
  meta: {
    title: 'AI监控',
    icon: 'mdi:robot-outline',
    order: 3,
  },
  children: [
    {
      name: 'AiMonitorDashboard',
      path: 'dashboard',
      component: () => import('./dashboard/index.vue'),
      meta: {
        title: 'AI监控总览',
        icon: 'mdi:view-dashboard-outline',
        keepAlive: true,
      },
    },
    {
      name: 'AnomalyDetection',
      path: 'anomaly-detection',
      component: () => import('./anomaly-detection/index.vue'),
      meta: {
        title: '异常检测',
        icon: 'mdi:alert-circle-outline',
        keepAlive: true,
      },
    },
    {
      name: 'TrendPrediction',
      path: 'trend-prediction',
      component: () => import('./trend-prediction/index.vue'),
      meta: {
        title: '趋势预测',
        icon: 'mdi:trending-up',
        keepAlive: true,
      },
    },
    {
      name: 'HealthScoring',
      path: 'health-scoring',
      component: () => import('./health-scoring/index.vue'),
      meta: {
        title: '健康评分',
        icon: 'mdi:heart-pulse',
        keepAlive: true,
      },
    },
    {
      name: 'ModelManagement',
      path: 'model-management',
      component: () => import('./model-management/index.vue'),
      meta: {
        title: '模型管理',
        icon: 'mdi:brain',
        keepAlive: true,
      },
    },
    {
      name: 'ModelTraining',
      path: 'model-training',
      component: () => import('./model-training/index.vue'),
      meta: {
        title: '模型训练',
        icon: 'mdi:school',
        keepAlive: true,
      },
    },
    {
      name: 'SmartAnalysis',
      path: 'smart-analysis',
      component: () => import('./smart-analysis/index.vue'),
      meta: {
        title: '智能分析',
        icon: 'mdi:lightbulb-outline',
        keepAlive: true,
      },
    },
    {
      name: 'DataAnnotation',
      path: 'data-annotation',
      component: () => import('./data-annotation/index.vue'),
      meta: {
        title: '数据标注',
        icon: 'mdi:tag-outline',
        keepAlive: true,
      },
    },
  ],
}

export default route

