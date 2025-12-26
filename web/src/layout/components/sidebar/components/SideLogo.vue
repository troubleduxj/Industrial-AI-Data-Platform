<template>
  <router-link h-60 f-c-c to="/" class="logo-container">
    <div class="logo-wrapper">
      <Icon icon="tdesign:system-sum" class="logo-icon" />
    </div>
    <div v-show="!appStore.collapsed" ml-3 mr-8 max-w-150 flex-shrink-0 class="title-container">
      <h2 class="main-title">DeviceMonitor</h2>
      <p class="sub-title">设备智能监测平台</p>
    </div>
  </router-link>
</template>

<script setup>
import { Icon } from '@iconify/vue'
import { useAppStore } from '@/store'
const title = import.meta.env.VITE_TITLE

const appStore = useAppStore()
</script>

<style scoped>
.logo-container {
  text-decoration: none;
  transition: all 0.3s ease;
}

.logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-color-dark, var(--primary-color))
  );
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.logo-wrapper:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  filter: brightness(1.1);
}

.logo-icon {
  width: 24px;
  height: 24px;
  color: white;
  transition: all 0.3s ease;
}

.title-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  line-height: 1.2;
}

.main-title {
  font-size: 16px;
  font-weight: bold;
  color: #000;
  margin: 0;
  line-height: 1.2;
}

.sub-title {
  font-size: 11px;
  color: #999;
  margin: 0;
  margin-top: 2px;
  line-height: 1.2;
  font-weight: normal;
}

/* 确保CSS变量能够传递到SVG */
.logo-icon :deep(svg) {
  --primary-color: var(--primary-color);
  --primary-color-dark: var(--primary-color-dark);
  --border-color: var(--border-color);
}
</style>
