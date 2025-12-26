/**
 * 表单组件统一导出
 * 提供项目中可复用的表单相关组件
 */

// 同步导出 - 用于直接引用
export { default as CollectorForm } from './CollectorForm.vue'
export { default as DynamicFormGenerator } from './DynamicFormGenerator.vue'
export { default as FieldRenderer } from './FieldRenderer.vue'

// 异步导出 - 用于懒加载
export default {
  CollectorForm: () => import('./CollectorForm.vue'),
  DynamicFormGenerator: () => import('./DynamicFormGenerator.vue'),
  FieldRenderer: () => import('./FieldRenderer.vue'),
}

// 组件安装函数（用于全局注册）
export function installFormComponents(app) {
  const components = {
    CollectorForm: () => import('./CollectorForm.vue'),
    DynamicFormGenerator: () => import('./DynamicFormGenerator.vue'),
    FieldRenderer: () => import('./FieldRenderer.vue'),
  }

  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}
