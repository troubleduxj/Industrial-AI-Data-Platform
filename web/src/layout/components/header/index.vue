<template>
  <div class="layout-header">
    <div class="layout-header-left">
      <MenuCollapse />
      <BreadCrumb ml-15 hidden sm:block />
    </div>
    <div class="layout-header-center">
      <!-- 搜索框 -->
      <SearchBox />
    </div>
    <div class="layout-header-right">
      <!-- 多语言切换，带占位符 -->
      <div class="icon-placeholder">
        <Languages v-if="showGlobalization" />
      </div>
      <!-- 主题切换，带占位符 -->
      <div class="icon-placeholder">
        <ThemeMode v-if="showThemeSwitcher" />
      </div>
      <!-- 主题色选择器 -->
      <div class="icon-placeholder">
        <div v-if="showThemeSwitcher" class="layout-header-trigger layout-header-trigger-min">
          <ThemeColorPicker />
        </div>
      </div>
      <!-- 通知铃铛 -->
      <NotificationBell />
      <!-- 全屏切换 -->
      <FullScreen />
      <!-- 用户头像 -->
      <UserAvatar />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BreadCrumb from './components/BreadCrumb.vue'
import MenuCollapse from './components/MenuCollapse.vue'
import FullScreen from './components/FullScreen.vue'
import UserAvatar from './components/UserAvatar.vue'
import ThemeMode from './components/ThemeMode.vue'
import Languages from './components/Languages.vue'
import SearchBox from './components/SearchBox.vue'
import ThemeColorPicker from './components/ThemeColorPicker.vue'
import NotificationBell from '@/components/common/NotificationBell.vue'
import { getCachedConfig } from '@/api'

// 控制按钮显示的响应式变量
const showGlobalization = ref(true)
const showThemeSwitcher = ref(true)

// 获取系统配置
const loadSystemConfig = async () => {
  try {
    // 获取全球化按钮配置
    const globalizationRes = await getCachedConfig('GLOBALIZATION_ENABLED')
    if (
      globalizationRes &&
      globalizationRes.data &&
      globalizationRes.data.param_value !== undefined
    ) {
      showGlobalization.value = globalizationRes.data.param_value === 'true'
    }

    // 获取主题切换按钮配置
    const themeSwitcherRes = await getCachedConfig('THEME_SWITCHER_ENABLED')
    if (
      themeSwitcherRes &&
      themeSwitcherRes.data &&
      themeSwitcherRes.data.param_value !== undefined
    ) {
      showThemeSwitcher.value = themeSwitcherRes.data.param_value === 'true'
    }
  } catch (error) {
    console.warn('获取系统配置失败:', error)
    // 如果获取配置失败，保持默认显示
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadSystemConfig()
})
</script>

<style lang="scss" scoped>
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  padding: 0 16px;
  /* 确保header内容不会超出容器 */
  max-width: 100%;
  overflow: hidden;
  box-sizing: border-box;
  /* 添加平滑过渡动画 - 与布局同步 */
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);

  .layout-header-left {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    min-width: 0;
    /* 添加过渡动画 - 与布局同步 */
    transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  .layout-header-center {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    max-width: 600px;
    margin: 0 20px;
    min-width: 0;
    /* 添加过渡动画 - 与布局同步 */
    transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);

    @media (max-width: 768px) {
      max-width: 300px;
      margin: 0 10px;
    }

    @media (max-width: 480px) {
      display: none;
    }
  }

  .layout-header-right {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    gap: 12px;
    min-width: 0;
    /* 确保右侧区域不会超出 */
    max-width: 50%;
    overflow: visible; /* 允许dropdown显示 */
    /* 添加过渡动画 - 与布局同步 */
    transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);

    // 统一所有图标按钮的样式和对齐
    > * {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      // 排除UserAvatar的尺寸控制
      &:not(.avatar-container) {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;

        &:hover {
          background-color: var(--hover-color, rgba(0, 0, 0, 0.05));
        }
      }
    }

    // 占位符样式，保持空间即使内容不显示
    .icon-placeholder {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;

      // 确保内部图标垂直居中
      :deep(.n-icon) {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 !important;
      }

      // 悬浮效果
      &:hover {
        background-color: var(--hover-color, rgba(0, 0, 0, 0.05));
      }

      // 当内容为空时不显示hover效果
      &:empty {
        cursor: default;

        &:hover {
          background-color: transparent;
        }
      }
    }

    // 移除子组件的margin
    :deep(.n-icon) {
      margin: 0 !important;
    }
  }

  .layout-header-trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--hover-color, rgba(0, 0, 0, 0.05));
    }

    &.layout-header-trigger-min {
      width: 32px;
      height: 32px;
      border-radius: 6px;
    }
  }
}

// 响应式调整
@media (max-width: 1024px) {
  .layout-header {
    .layout-header-center {
      max-width: 400px;
    }
  }
}

@media (max-width: 768px) {
  .layout-header {
    padding: 0 12px;

    .layout-header-right {
      gap: 4px;
    }
  }
}

// 小屏幕下进一步优化
@media (max-width: 480px) {
  .layout-header {
    padding: 0 8px;

    .layout-header-right {
      gap: 2px;

      .icon-placeholder {
        width: 28px;
        height: 28px;
      }
    }
  }
}
</style>
