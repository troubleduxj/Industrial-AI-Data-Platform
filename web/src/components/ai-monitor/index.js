// AI监测组件统一导出

// 图表组件
export * from './charts'
import * as Charts from './charts'

// 表单组件
export * from './forms'
import * as Forms from './forms'

// 通用组件
export * from './common'
import * as Common from './common'

// 分类导出
export { Charts, Forms, Common }

// 默认导出
export default {
  Charts,
  Forms,
  Common,
}

// 便捷安装方法
export const install = (app) => {
  // 注册图表组件
  Object.keys(Charts).forEach((key) => {
    if (Charts[key].name) {
      app.component(Charts[key].name, Charts[key])
    }
  })

  // 注册表单组件
  Object.keys(Forms).forEach((key) => {
    if (Forms[key].name) {
      app.component(Forms[key].name, Forms[key])
    }
  })

  // 注册通用组件
  Object.keys(Common).forEach((key) => {
    if (Common[key].name) {
      app.component(Common[key].name, Common[key])
    }
  })
}
