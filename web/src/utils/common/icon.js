import { h } from 'vue'
import { Icon } from '@iconify/vue'
import { NIcon } from 'naive-ui'
import SvgIcon from '@/components/icon/SvgIcon.vue'
import { getOfflineIcon, isSupportedIcon } from './offlineIcons'

// 创建离线图标组件
function createOfflineIcon(iconName, props = {}) {
  const emoji = getOfflineIcon(iconName)
  return h(
    'span',
    {
      style: {
        fontSize: props.size ? `${props.size}px` : '12px',
        display: 'inline-block',
        lineHeight: '1',
        ...props.style,
      },
    },
    emoji
  )
}

export function renderIcon(icon, props = { size: 12 }) {
  return () =>
    h(NIcon, props, {
      default: () => {
        // 优先使用离线图标，避免网络请求
        if (isSupportedIcon(icon)) {
          return createOfflineIcon(icon, props)
        }
        // 如果不在离线图标列表中，尝试使用 @iconify/vue
        return h(Icon, { icon })
      },
    })
}

export function renderCustomIcon(icon, props = { size: 12 }) {
  return () => h(NIcon, props, { default: () => h(SvgIcon, { icon }) })
}
