<template>
  <n-menu
    ref="menu"
    class="side-menu"
    accordion
    :indent="18"
    :collapsed-icon-size="22"
    :collapsed-width="64"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup>
import { usePermissionStore, useAppStore } from '@/store'
import { renderCustomIcon, renderIcon, isExternal } from '@/utils'

const router = useRouter()
const curRoute = useRoute()
const permissionStore = usePermissionStore()
const appStore = useAppStore()

const activeKey = computed(() => curRoute.meta?.activeMenu || curRoute.name)

const menuOptions = computed(() => {
  return permissionStore.menus.map((item) => getMenuItem(item)).sort((a, b) => a.order - b.order)
})

const menu = ref(null)
watch(curRoute, async () => {
  await nextTick()
  menu.value?.showOption()
})

function resolvePath(basePath, path) {
  if (isExternal(path)) return path
  return (
    '/' +
    [basePath, path]
      .filter((path) => !!path && path !== '/')
      .map((path) => path.replace(/(^\/)|(\/$)/g, ''))
      .join('/')
  )
}

function getMenuItem(route, basePath = '') {
  let menuItem = {
    label: (route.meta && route.meta.title) || route.name,
    key: route.name,
    path: resolvePath(basePath, route.path),
    icon: getIcon(route.meta),
    order: route.meta?.order || 0,
  }

  const visibleChildren = route.children
    ? route.children.filter((item) => item.name && !item.meta?.isHidden)
    : []

  if (!visibleChildren.length) return menuItem

  if (visibleChildren.length === 1) {
    // 单个子路由处理
    const singleRoute = visibleChildren[0]
    menuItem = {
      ...menuItem,
      label: singleRoute.meta?.title || singleRoute.name,
      key: singleRoute.name,
      path: resolvePath(menuItem.path, singleRoute.path),
      icon: getIcon(singleRoute.meta),
    }
    const visibleItems = singleRoute.children
      ? singleRoute.children.filter((item) => item.name && !item.meta?.isHidden)
      : []

    if (visibleItems.length === 1) {
      menuItem = getMenuItem(visibleItems[0], menuItem.path)
    } else if (visibleItems.length > 1) {
      menuItem.children = visibleItems
        .map((item) => getMenuItem(item, menuItem.path))
        .sort((a, b) => a.order - b.order)
    }
  } else {
    menuItem.children = visibleChildren
      .map((item) => getMenuItem(item, menuItem.path))
      .sort((a, b) => a.order - b.order)
  }
  return menuItem
}

function getIcon(meta) {
  if (meta?.customIcon) return renderCustomIcon(meta.customIcon, { size: 18 })
  if (meta?.icon) return renderIcon(meta.icon, { size: 18 })
  return null
}

function handleMenuSelect(key, item) {
  if (isExternal(item.path)) {
    window.open(item.path)
  } else {
    if (item.path === curRoute.path) {
      appStore.reloadPage()
    } else {
      router.push(item.path)
    }
  }
}
</script>

<style lang="scss">
/* n-menu CSS变量覆盖 */
:deep(.n-menu) {
  --n-item-text-color-child-active-hover: var(--primary-color) !important;
  --n-item-text-color-child-active: var(--primary-color) !important;
  --n-item-icon-color-child-active-hover: var(--primary-color) !important;
  --n-item-icon-color-child-active: var(--primary-color) !important;
  --n-arrow-color-child-active-hover: var(--primary-color) !important;
  --n-arrow-color-child-active: var(--primary-color) !important;
}

.side-menu:not(.n-menu--collapsed) {
  .n-menu-item-content {
    margin: 4px 12px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    &::before {
      left: 0;
      right: 0;
      border-radius: 8px;
      border-left: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    // 激活状态：卡片式效果，背景色为主题色，文字为白色，轻微放大
    &.n-menu-item-content--selected {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      .n-menu-item-content-header {
        color: white !important;
        font-weight: 500;
      }

      // 激活状态悬停时保持白色文字
      &:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);

        &::before {
          background: var(--primary-color) !important;
        }

        .n-menu-item-content__icon {
          color: white !important;
        }

        .n-menu-item-content-header {
          color: white !important;
        }
      }
    }

    // 悬停状态：卡片式效果，背景色为主题色*10%，文字为主题色，轻微放大
    &:hover:not(.n-menu-item-content--selected) {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      &::before {
        background: color-mix(in srgb, var(--primary-color) 10%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }

      .n-menu-item-content-header {
        color: var(--primary-color) !important;
      }
    }
  }

  // 子菜单激活时父菜单样式
  .n-submenu.n-submenu--child-active > .n-menu-item-content {
    .n-menu-item-content__icon,
    .n-menu-item-content-header,
    .n-submenu-arrow {
      color: var(--primary-color) !important;
    }
  }

  // 子菜单项样式
  .n-submenu-children .n-menu-item-content {
    margin: 2px 12px 2px 18px;
    border-radius: 6px;

    &.n-menu-item-content--selected {
      transform: scale(1.03);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      .n-menu-item-content-header {
        color: white !important;
        font-weight: 500;
      }
    }

    &:hover:not(.n-menu-item-content--selected) {
      transform: scale(1.03);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

      &::before {
        background: color-mix(in srgb, var(--primary-color) 8%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }

      .n-menu-item-content-header {
        color: var(--primary-color) !important;
      }
    }
  }
}

// 收起状态的菜单样式
.side-menu.n-menu--collapsed {
  .n-menu-item-content {
    margin: 4px 8px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;

    // 确保图标容器居中
    .n-menu-item-content__icon {
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      position: relative !important;
      left: 0 !important;
      right: 0 !important;
      text-align: center !important;
    }

    // 确保图标元素本身也居中
    .n-menu-item-content__icon > * {
      margin: 0 auto !important;
      display: block !important;
    }

    &::before {
      left: 0;
      right: 0;
      border-radius: 8px;
      border-left: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    // 激活状态：保持主题色背景，白色图标，圆角效果
    &.n-menu-item-content--selected {
      &::before {
        background: var(--primary-color) !important;
      }

      .n-menu-item-content__icon {
        color: white !important;
      }

      // 激活状态悬停时保持样式
      &:hover {
        &::before {
          background: var(--primary-color) !important;
        }

        .n-menu-item-content__icon {
          color: white !important;
        }
      }
    }

    // 悬停状态：背景色为主题色*15%，图标为主题色
    &:hover:not(.n-menu-item-content--selected) {
      &::before {
        background: color-mix(in srgb, var(--primary-color) 15%, transparent) !important;
      }

      .n-menu-item-content__icon {
        color: var(--primary-color) !important;
      }
    }
  }
}
</style>
