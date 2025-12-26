<template>
  <div class="system-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 系统管理模块布局组件
defineOptions({ name: '系统管理' })
</script>

<style scoped>
.system-layout {
  height: 100%;
  width: 100%;
}
</style>
