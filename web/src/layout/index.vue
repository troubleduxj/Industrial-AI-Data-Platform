<template>
  <n-layout has-sider wh-full>
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :native-scrollbar="false"
      :collapsed="appStore.collapsed"
    >
      <SideBar />
    </n-layout-sider>

    <article flex-col flex-1>
      <header
        class="header-with-shadow flex items-center border-b bg-white px-15 bc-eee"
        dark="bg-dark border-0"
        :style="`height: ${header.height}px`"
      >
        <AppHeader />
      </header>
      <section
        v-if="tags.visible"
        hidden
        border-b
        bc-eee
        sm:block
        dark:border-0
        class="tags-section"
      >
        <AppTags :style="{ height: `${tags.height}px` }" />
      </section>
      <section flex-1 bg-hex-f5f6fb dark:bg-hex-101014 class="main-content-section">
        <AppMain />
      </section>
    </article>
  </n-layout>
</template>

<script setup>
import AppHeader from './components/header/index.vue'
import SideBar from './components/sidebar/index.vue'
import AppMain from './components/AppMain.vue'
import AppTags from './components/tags/index.vue'
import { useAppStore } from '@/store'
import { header, tags } from '~/settings'

// 移动端适配
import { useBreakpoints } from '@vueuse/core'

const appStore = useAppStore()
const breakpointsEnum = {
  xl: 1600,
  lg: 1199,
  md: 991,
  sm: 666,
  xs: 575,
}
const breakpoints = reactive(useBreakpoints(breakpointsEnum))
const isMobile = breakpoints.smaller('sm')
const isPad = breakpoints.between('sm', 'md')
const isPC = breakpoints.greater('md')
watchEffect(() => {
  if (isMobile.value) {
    // Mobile
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }

  if (isPad.value) {
    // IPad
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }

  if (isPC.value) {
    // PC
    appStore.setCollapsed(false)
    appStore.setFullScreen(true)
  }
})
</script>

<style scoped>
/* 确保布局容器铺满整个屏幕 */
:deep(.n-layout) {
  height: 100vh;
  overflow: hidden;
}

/* 确保侧边栏铺满整个高度，固定定位防止滚动影响 */
:deep(.n-layout-sider) {
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  overflow: hidden;
  /* 添加侧边栏过渡动画 - 与主内容区域同步 */
  transition: width 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 为主内容区域添加左边距，避免被固定侧边栏遮挡 */
:deep(.n-layout-sider) ~ article {
  margin-left: 220px;
  /* 添加平滑过渡动画 - 使用更自然的缓动函数 */
  transition: margin-left 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94),
    width 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94),
    max-width 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  /* 确保主内容区域不会超出视口 */
  width: calc(100vw - 220px);
  max-width: calc(100vw - 220px);
  overflow: hidden;
}

/* 当侧边栏折叠时调整边距 */
:deep(.n-layout-sider--collapsed) ~ article {
  margin-left: 64px;
  width: calc(100vw - 64px);
  max-width: calc(100vw - 64px);
}

/* 侧边栏内容区域设置滚动 */
:deep(.n-layout-sider .n-layout-sider-scroll-container) {
  height: 100%;
  overflow-y: auto;
}

.tags-section {
  background: var(--n-color-target);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 10;
}

.tags-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent);
}

/* 深色模式适配 */
.dark .tags-section {
  background: var(--n-color-target);
  box-shadow: 0 1px 3px rgba(255, 255, 255, 0.1);
}

.dark .tags-section::before {
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
}

/* Header阴影效果 */
.header-with-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 20;
  /* 确保header不会超出容器 */
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
  /* 添加header过渡动画 - 与布局同步 */
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 深色模式下的header阴影 */
.dark .header-with-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* 主内容区域样式 */
.main-content-section {
  overflow: hidden;
  position: relative;
  width: 100%;
  max-width: calc(100vw - 220px);
  /* 添加平滑过渡动画 - 与其他元素同步 */
  transition: max-width 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 当侧边栏折叠时调整主内容区域最大宽度 */
:deep(.n-layout-sider--collapsed) ~ article .main-content-section {
  max-width: calc(100vw - 64px);
}

/* 主内容区域内的所有直接子元素 */
.main-content-section > * {
  width: 100%;
  height: 100%;
  overflow: auto;
}
</style>
