<template>
  <div class="system-management-page theme-management-page">
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

      <!-- 简化的合规性信息 -->
      <div class="compliance-section">
        <h2>主题合规性</h2>
        <div class="compliance-info">
          <n-button :loading="checking" type="primary" @click="checkCompliance">
            检查当前页面合规性
          </n-button>
          <div v-if="complianceResult" class="compliance-result">
            <p>检查状态: {{ complianceResult.status }}</p>
            <p v-if="complianceResult.summary">
              违规数量: {{ complianceResult.summary.totalViolations }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NButton, NSwitch } from 'naive-ui'
import { useThemeStore } from '@/store/theme'

defineOptions({ name: 'SystemTheme' })

const themeStore = useThemeStore()

// 响应式数据
const applyingPreset = ref(null)
const themeConfig = ref(null)
const checking = ref(false)
const complianceResult = ref(null)

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

const checkCompliance = async () => {
  checking.value = true
  try {
    complianceResult.value = await themeStore.checkThemeCompliance()
  } catch (error) {
    console.error('合规性检查失败:', error)
    complianceResult.value = { status: 'error', error: error.message }
  } finally {
    checking.value = false
  }
}

// 生命周期
onMounted(async () => {
  await loadThemeConfig()
})
</script>

<style scoped lang="scss">
.theme-management-page {
  padding: var(--spacing-lg, 24px);
  background: var(--background-color-light, #fafafa);
  min-height: 100vh;

  .page-header {
    margin-bottom: var(--spacing-lg, 24px);

    .page-title {
      font-size: var(--font-size-2xl, 24px);
      font-weight: var(--font-weight-bold, 700);
      color: var(--text-color-primary, #262626);
      margin-bottom: var(--spacing-sm, 8px);
    }

    .page-description {
      color: var(--text-color-secondary, #595959);
      font-size: var(--font-size-base, 16px);
    }
  }

  .page-content {
    background: var(--background-color-base, #ffffff);
    border-radius: var(--border-radius-lg, 8px);
    padding: var(--spacing-lg, 24px);
    box-shadow: var(--shadow-sm, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
  }

  .theme-presets-section {
    margin-bottom: var(--spacing-xl, 32px);

    h2 {
      font-size: var(--font-size-xl, 20px);
      font-weight: var(--font-weight-semibold, 600);
      color: var(--text-color-primary, #262626);
      margin-bottom: var(--spacing-lg, 24px);
    }

    .presets-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: var(--spacing-md, 16px);

      .preset-card {
        background: var(--background-color-base, #ffffff);
        border: 2px solid var(--border-color-light, #e8e8e8);
        border-radius: var(--border-radius-lg, 8px);
        padding: var(--spacing-lg, 24px);
        cursor: pointer;
        transition: all 0.15s ease-in-out;
        display: flex;
        align-items: center;
        gap: var(--spacing-md, 16px);

        &:hover {
          border-color: var(--primary-color-light, #737373);
          box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
        }

        &.active {
          border-color: var(--primary-color, #343434);
          box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
        }

        .preset-color {
          width: 48px;
          height: 48px;
          border-radius: var(--border-radius-base, 4px);
          border: 1px solid var(--border-color-light, #e8e8e8);
          flex-shrink: 0;
        }

        .preset-info {
          flex: 1;

          .preset-name {
            font-size: var(--font-size-base, 16px);
            font-weight: var(--font-weight-medium, 500);
            color: var(--text-color-primary, #262626);
            margin-bottom: var(--spacing-xs, 4px);
          }

          .preset-description {
            font-size: var(--font-size-sm, 14px);
            color: var(--text-color-secondary, #595959);
          }
        }

        .preset-actions {
          flex-shrink: 0;
        }
      }
    }
  }

  .theme-config-section {
    margin-bottom: var(--spacing-xl, 32px);

    h2 {
      font-size: var(--font-size-xl, 20px);
      font-weight: var(--font-weight-semibold, 600);
      color: var(--text-color-primary, #262626);
      margin-bottom: var(--spacing-lg, 24px);
    }

    .config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: var(--spacing-md, 16px);

      .config-item {
        background: var(--background-color-light, #fafafa);
        border: 1px solid var(--border-color-light, #e8e8e8);
        border-radius: var(--border-radius-base, 4px);
        padding: var(--spacing-md, 16px);

        label {
          display: block;
          font-size: var(--font-size-sm, 14px);
          font-weight: var(--font-weight-medium, 500);
          color: var(--text-color-secondary, #595959);
          margin-bottom: var(--spacing-xs, 4px);
        }

        .config-value {
          font-size: var(--font-size-base, 16px);
          color: var(--text-color-primary, #262626);

          &.color-value {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs, 4px);

            .color-preview {
              width: 20px;
              height: 20px;
              border-radius: var(--border-radius-sm, 2px);
              border: 1px solid var(--border-color-light, #e8e8e8);
            }
          }
        }
      }
    }
  }

  .compliance-section {
    h2 {
      font-size: var(--font-size-xl, 20px);
      font-weight: var(--font-weight-semibold, 600);
      color: var(--text-color-primary, #262626);
      margin-bottom: var(--spacing-lg, 24px);
    }

    .compliance-info {
      .compliance-result {
        margin-top: var(--spacing-md, 16px);
        padding: var(--spacing-md, 16px);
        background: var(--background-color-light, #fafafa);
        border-radius: var(--border-radius-base, 4px);
        border: 1px solid var(--border-color-light, #e8e8e8);

        p {
          margin: var(--spacing-xs, 4px) 0;
          color: var(--text-color-primary, #262626);
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .theme-management-page {
    padding: var(--spacing-md, 16px);

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
