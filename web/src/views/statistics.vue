<template>
  <div class="statistics-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
/**
 * 统计分析模块布局组件
 * 提供统计相关页面的布局容器
 */

defineOptions({
  name: 'StatisticsLayout',
})
</script>

<style scoped>
.statistics-layout {
  width: 100%;
  height: 100%;
}
</style>
