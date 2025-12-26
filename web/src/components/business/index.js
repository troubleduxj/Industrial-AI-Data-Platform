/**
 * 业务组件统一导出
 * 提供项目中特定业务领域的可复用组件
 */

// 设备相关组件
export { default as DeviceStatusCard } from './device/DeviceStatusCard.vue'

// 表格相关组件
export { default as StandardDataTable } from './table/StandardDataTable.vue'

// 表单相关组件
export { default as StandardForm } from './form/StandardForm.vue'

// 异步导出 - 用于懒加载
export default {
  // 设备组件
  DeviceStatusCard: () => import('./device/DeviceStatusCard.vue'),
  
  // 表格组件
  StandardDataTable: () => import('./table/StandardDataTable.vue'),
  
  // 表单组件
  StandardForm: () => import('./form/StandardForm.vue')
}

// 组件类型定义（用于TypeScript支持）
export interface BusinessComponentsMap {
  DeviceStatusCard: typeof import('./device/DeviceStatusCard.vue').default
  StandardDataTable: typeof import('./table/StandardDataTable.vue').default
  StandardForm: typeof import('./form/StandardForm.vue').default
}

// 组件安装函数（用于全局注册）
export function installBusinessComponents(app) {
  const components = {
    DeviceStatusCard: () => import('./device/DeviceStatusCard.vue'),
    StandardDataTable: () => import('./table/StandardDataTable.vue'),
    StandardForm: () => import('./form/StandardForm.vue')
  }
  
  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}

// 业务组件配置
export const BUSINESS_COMPONENT_CONFIG = {
  // 设备组件配置
  device: {
    statusCard: {
      defaultSize: 'medium',
      defaultMetrics: ['preset_current', 'preset_voltage', 'welding_current', 'welding_voltage'],
      maxMetrics: 4
    }
  },
  
  // 表格组件配置
  table: {
    standardDataTable: {
      defaultPageSize: 20,
      pageSizes: [10, 20, 50, 100],
      defaultSize: 'medium'
    }
  },
  
  // 表单组件配置
  form: {
    standardForm: {
      defaultSize: 'medium',
      defaultLabelWidth: '120px',
      defaultLabelPlacement: 'left'
    }
  }
}