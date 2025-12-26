<template>
  <AppProvider>
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
    <FloatingChatWidget />
  </AppProvider>
</template>

<script setup>
import { onMounted } from 'vue'
import AppProvider from '@/components/common/AppProvider.vue'
import FloatingChatWidget from '@/components/chat-widget/FloatingChatWidget.vue'
import { useThemeStore } from '@/store/theme'
import { initializeThemeSystem } from '@/utils/theme-variable-mapper.js'
import { initializeSystemThemeService } from '@/services/system-theme-service.js'

const themeStore = useThemeStore()

onMounted(async () => {
  try {
    // 初始化标准化主题系统
    initializeThemeSystem()

    // 初始化系统管理主题服务
    await initializeSystemThemeService()

    // 加载主题设置
    await themeStore.loadThemeFromStorage()

    console.log('主题系统初始化完成')
  } catch (error) {
    console.error('主题系统初始化失败:', error)
    // 降级到原有逻辑
    themeStore.loadThemeFromStorage()
  }
})

// 检查是否为开发环境
const isDev = import.meta.env.DEV

console.log('App.vue - 开发环境:', isDev)
</script>

<style></style>
