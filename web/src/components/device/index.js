/**
 * 设备组件统一导出
 * 提供项目中可复用的设备相关组件
 */

// 同步导出 - 用于直接引用
export { default as DeviceSelector } from './DeviceSelector.vue'

// 异步导出 - 用于懒加载
export default {
  DeviceSelector: () => import('./DeviceSelector.vue'),
}

// 组件安装函数（用于全局注册）
export function installDeviceComponents(app) {
  const components = {
    DeviceSelector: () => import('./DeviceSelector.vue'),
  }

  Object.entries(components).forEach(([name, component]) => {
    app.component(name, component)
  })
}
