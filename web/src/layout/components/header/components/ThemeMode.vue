<script setup>
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
</script>

<template>
  <n-icon size="18" @click="themeStore.toggleThemeMode">
    <icon-mdi-moon-waning-crescent v-if="themeStore.isDarkMode" />
    <icon-mdi-white-balance-sunny v-else />
  </n-icon>
</template>
