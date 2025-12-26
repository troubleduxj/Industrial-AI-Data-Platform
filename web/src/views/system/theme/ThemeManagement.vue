<template>
  <div class="theme-management-page system-management-page">
    <div class="page-header">
      <h1 class="page-title">主题管理</h1>
      <p class="page-description">管理系统主题配置和合规性检查</p>
    </div>

    <div class="page-content">
      <!-- 主题预设选择 -->
      <div class="theme-presets-section">
        <h2>主题预设</h2>
        <div class="presets-grid">
          <div
            v-for="preset in themePresets"
            :key="preset.key"
            class="preset-card"
            :class="{ active: currentPreset?.key === preset.key }"
            @click="applyPreset(preset.key)"
          >
            <div class="preset-color" :style="{ backgroundColor: preset.primaryColor }"></div>
            <div class="preset-info">
              <div class="preset-name">{{ preset.name }}</div>
              <div class="preset-description">{{ preset.description }}</div>
            </div>
            <div class="preset-actions">
              <n-button
                v-if="currentPreset?.key === preset.key"
                type="success"
                size="small"
                class="standard-button"
              >
                已应用
              </n-button>
              <n-button
                v-else
                type="primary"
                size="small"
                :loading="applyingPreset === preset.key"
                class="standard-button"
                @click.stop="applyPreset(preset.key)"
              >
                应用
              </n-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 主题配置信息 -->
      <div v-if="themeConfig" class="theme-config-section">
        <h2>当前配置</h2>
        <div class="config-grid">
          <div class="config-item">
            <label>当前主题</label>
            <div class="config-value">
              {{ themeConfig.currentPreset?.name || '默认' }}
            </div>
          </div>
          <div class="config-item">
            <label>主色调</label>
            <div class="config-value color-value">
              <div
                class="color-preview"
                :style="{ backgroundColor: themeConfig.currentPreset?.primaryColor || '#343434' }"
              ></div>
              {{ themeConfig.currentPreset?.primaryColor || '#343434' }}
            </div>
          </div>
          <div class="config-item">
            <label>模式</label>
            <div class="config-value">
              <n-switch v-model:value="isDarkMode" @update:value="toggleDarkMode">
                <template #checked>暗色</template>
                <template #unchecked>亮色</template>
              </n-switch>
            </div>
          </div>
          <div class="config-item">
            <label>已应用变量</label>
            <div class="config-value">
              {{ Object.keys(themeConfig.appliedVariables || {}).length }} 个
            </div>
          </div>
        </div>
      </div>

      <!-- 合规性监控 -->
      <div class="compliance-section">
        <ThemeComplianceDashboard />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NButton, NSwitch } from 'naive-ui'
import { useThemeStore } from '@/store/theme'
import ThemeComplianceDashboard from '@/components/theme/ThemeComplianceDashboard.vue'

defineOptions({ name: 'ThemeManagement' })

const themeStore = useThemeStore()

// 响应式数据
const applyingPreset = ref(null)
const themeConfig = ref(null)

// 计算属性
const themePresets = computed(() => themeStore.themePresets)
const currentPreset = computed(() => themeStore.currentThemePreset)
const isDarkMode = computed({
  get: () => themeStore.isDarkMode,
  set: (value) => {
    themeStore.setThemeMode(value ? 'dark' : 'light')
  },
})

// 方法
const applyPreset = async (presetKey) => {
  if (applyingPreset.value) return

  applyingPreset.value = presetKey
  try {
    await themeStore.applyThemePreset(presetKey)
    await loadThemeConfig()
  } catch (error) {
    console.error('应用主题预设失败:', error)
  } finally {
    applyingPreset.value = null
  }
}

const toggleDarkMode = (value) => {
  themeStore.setThemeMode(value ? 'dark' : 'light')
}

const loadThemeConfig = async () => {
  try {
    themeConfig.value = await themeStore.getThemeConfiguration()
  } catch (error) {
    console.error('加载主题配置失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  await loadThemeConfig()
})
</script>

<style scoped lang="scss">
.theme-management-page {
  .theme-presets-section {
    margin-bottom: var(--spacing-xl);

    h2 {
      font-size: var(--font-size-xl);
      font-weight: var(--font-weight-semibold);
      color: var(--text-color-primary);
      margin-bottom: var(--spacing-lg);
    }

    .presets-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: var(--spacing-md);

      .preset-card {
        background: var(--background-color-base);
        border: 2px solid var(--border-color-light);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-lg);
        cursor: pointer;
        transition: all var(--transition-fast);
        display: flex;
        align-items: center;
        gap: var(--spacing-md);

        &:hover {
          border-color: var(--primary-color-light);
          box-shadow: var(--shadow-md);
        }

        &.active {
          border-color: var(--primary-color);
          box-shadow: var(--shadow-md);
          background: rgba(var(--primary-color), 0.05);
        }

        .preset-color {
          width: 48px;
          height: 48px;
          border-radius: var(--border-radius-base);
          border: 1px solid var(--border-color-light);
          flex-shrink: 0;
        }

        .preset-info {
          flex: 1;

          .preset-name {
            font-size: var(--font-size-base);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
            margin-bottom: var(--spacing-xs);
          }

          .preset-description {
            font-size: var(--font-size-sm);
            color: var(--text-color-secondary);
          }
        }

        .preset-actions {
          flex-shrink: 0;
        }
      }
    }
  }

  .theme-config-section {
    margin-bottom: var(--spacing-xl);

    h2 {
      font-size: var(--font-size-xl);
      font-weight: var(--font-weight-semibold);
      color: var(--text-color-primary);
      margin-bottom: var(--spacing-lg);
    }

    .config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: var(--spacing-md);

      .config-item {
        background: var(--background-color-light);
        border: 1px solid var(--border-color-light);
        border-radius: var(--border-radius-base);
        padding: var(--spacing-md);

        label {
          display: block;
          font-size: var(--font-size-sm);
          font-weight: var(--font-weight-medium);
          color: var(--text-color-secondary);
          margin-bottom: var(--spacing-xs);
        }

        .config-value {
          font-size: var(--font-size-base);
          color: var(--text-color-primary);

          &.color-value {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);

            .color-preview {
              width: 20px;
              height: 20px;
              border-radius: var(--border-radius-sm);
              border: 1px solid var(--border-color-light);
            }
          }
        }
      }
    }
  }

  .compliance-section {
    h2 {
      font-size: var(--font-size-xl);
      font-weight: var(--font-weight-semibold);
      color: var(--text-color-primary);
      margin-bottom: var(--spacing-lg);
    }
  }
}

@media (max-width: 768px) {
  .theme-management-page {
    .presets-grid {
      grid-template-columns: 1fr;
    }

    .config-grid {
      grid-template-columns: 1fr;
    }

    .preset-card {
      flex-direction: column;
      text-align: center;
    }
  }
}
</style>
