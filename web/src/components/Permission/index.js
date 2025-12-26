/**
 * 权限组件入口文件
 */

import PermissionButton from './PermissionButton.vue'
import PermissionCheck from './PermissionCheck.vue'
import PermissionLink from './PermissionLink.vue'
import PermissionForm from './PermissionForm.vue'
import PermissionEmpty from './PermissionEmpty.vue'
import PermissionDataWrapper from './PermissionDataWrapper.vue'
import FastPermissionWrapper from './FastPermissionWrapper.vue'

// 导出组件
export {
  PermissionButton,
  PermissionCheck,
  PermissionLink,
  PermissionForm,
  PermissionEmpty,
  PermissionDataWrapper,
  FastPermissionWrapper,
}

// 权限组件插件
export default {
  install(app) {
    app.component('PermissionButton', PermissionButton)
    app.component('PermissionCheck', PermissionCheck)
    app.component('PermissionLink', PermissionLink)
    app.component('PermissionForm', PermissionForm)
    app.component('PermissionEmpty', PermissionEmpty)
    app.component('PermissionDataWrapper', PermissionDataWrapper)
  },
}

// 权限组件配置
export const PermissionConfig = {
  // 默认配置
  defaults: {
    hideWhenNoPermission: false,
    disableWhenNoPermission: true,
    showTooltipWhenNoPermission: true,
    showNoPermissionMessage: true,
    noPermissionText: '权限不足，无法访问此内容',
  },

  // 权限级别配置
  levels: {
    PUBLIC: 0, // 公开访问
    USER: 1, // 登录用户
    ADMIN: 2, // 管理员
    SUPERUSER: 3, // 超级用户
  },

  // 权限类型配置
  types: {
    MENU: 'menu',
    API: 'api',
    BUTTON: 'button',
    ROUTE: 'route',
    DATA: 'data',
  },
}
