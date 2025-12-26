<template>
  <n-config-provider
    wh-full
    :locale="zhCN"
    :date-locale="dateZhCN"
    :theme-overrides="themeStore.naiveThemeOverrides"
  >
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-message-provider>
            <slot></slot>
            <NaiveProviderContent />
          </n-message-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup>
import { defineComponent, h, onMounted, onUnmounted } from 'vue'
import { zhCN, dateZhCN, useLoadingBar, useDialog, useMessage, useNotification } from 'naive-ui'
import { setupMessage, setupDialog } from '@/utils'
import { useThemeStore } from '@/store'
import { safeCall } from '@/utils/vue-error-handler'

const themeStore = useThemeStore()

// 安全的naive工具设置
function setupNaiveTools() {
  try {
    // 使用安全调用包装
    const loadingBar = safeCall(() => useLoadingBar())
    const notification = safeCall(() => useNotification())
    const message = safeCall(() => useMessage())
    const dialog = safeCall(() => useDialog())

    if (loadingBar) {
      window.$loadingBar = loadingBar
    }

    if (notification) {
      window.$notification = notification
    }

    if (message) {
      window.$message = setupMessage(message)
    }

    if (dialog) {
      window.$dialog = setupDialog(dialog)
    }
  } catch (error) {
    console.warn('Setup naive tools error:', error)
  }
}

// 清理函数
function cleanupNaiveTools() {
  try {
    delete window.$loadingBar
    delete window.$notification
    delete window.$message
    delete window.$dialog
  } catch (error) {
    console.warn('Cleanup naive tools error:', error)
  }
}

const NaiveProviderContent = defineComponent({
  name: 'NaiveProviderContent',
  setup() {
    onMounted(() => {
      setupNaiveTools()
    })

    onUnmounted(() => {
      cleanupNaiveTools()
    })

    return () => h('div', { style: { display: 'none' } })
  },
})
</script>
