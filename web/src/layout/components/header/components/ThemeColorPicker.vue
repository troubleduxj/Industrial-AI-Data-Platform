<template>
  <div class="theme-color-picker">
    <n-popover trigger="click" placement="bottom-end" :style="{ padding: '8px' }">
      <template #trigger>
        <n-icon
          :component="ColorPaletteIcon"
          size="18"
          class="color-picker-btn"
          title="主题色设置"
        />
      </template>
      <div class="color-palette">
        <div class="palette-title">选择主题</div>
        <div class="color-grid">
          <div
            v-for="theme in themeStore.themePresets"
            :key="theme.name"
            class="color-cell"
            :style="{ backgroundColor: theme.primaryColor }"
            :title="theme.name"
            @click="themeStore.setPrimaryColor(theme.primaryColor)"
          >
            <n-icon
              v-if="themeStore.primaryColor === theme.primaryColor"
              :component="CheckmarkIcon"
              size="14"
              color="#fff"
            />
          </div>
        </div>
      </div>
    </n-popover>
  </div>
</template>

<script setup>
import { NPopover, NIcon } from 'naive-ui'
import {
  ColorPaletteOutline as ColorPaletteIcon,
  CheckmarkOutline as CheckmarkIcon,
} from '@vicons/ionicons5'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
</script>

<style scoped>
.color-picker-btn {
  cursor: pointer;
  transition: color 0.2s ease;
}
.color-picker-btn:hover {
  color: var(--primary);
}

.color-palette {
  width: 180px;
}

.palette-title {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 8px;
  margin-bottom: 8px;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 0 8px 8px;
}

.color-cell {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.color-cell:hover {
  transform: scale(1.1);
}
</style>
