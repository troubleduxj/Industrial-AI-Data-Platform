import { defineStore } from 'pinia'
import { useDark } from '@vueuse/core'
import { nextTick } from 'vue'
import { lStorage } from '@/utils'
import i18n from '~/i18n'

const currentLocale = lStorage.get('locale')
const { locale } = i18n.global

const isDark = useDark()
export const useAppStore = defineStore('app', {
  state() {
    return {
      reloadFlag: true,
      collapsed: false,
      fullScreen: true,
      /** keepAlive路由的key，重新赋值可重置keepAlive */
      aliveKeys: {},
      isDark,
      locale: currentLocale || 'en',
    }
  },
  actions: {
    async reloadPage() {
      try {
        $loadingBar.start()
        this.reloadFlag = false

        // 使用单个nextTick确保DOM清理，避免过度延迟导致的DOM操作问题
        await nextTick()
        this.reloadFlag = true

        // 等待DOM重新渲染完成后再执行滚动和结束加载
        await nextTick()
        setTimeout(() => {
          document.documentElement.scrollTo({ left: 0, top: 0 })
          $loadingBar.finish()
        }, 100)
      } catch (error) {
        console.error('页面重载失败:', error)
        this.reloadFlag = true
        $loadingBar.error()
      }
    },
    switchCollapsed() {
      this.collapsed = !this.collapsed
    },
    setCollapsed(collapsed) {
      this.collapsed = collapsed
    },
    setFullScreen(fullScreen) {
      this.fullScreen = fullScreen
    },
    setAliveKeys(key, val) {
      this.aliveKeys[key] = val
    },
    /** 设置暗黑模式 */
    setDark(isDark) {
      this.isDark = isDark
    },
    /** 切换/关闭 暗黑模式 */
    toggleDark() {
      this.isDark = !this.isDark
    },
    setLocale(newLocale) {
      this.locale = newLocale
      locale.value = newLocale
      lStorage.set('locale', newLocale)
    },
  },
})
