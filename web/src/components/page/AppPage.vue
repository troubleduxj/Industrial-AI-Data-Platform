<template>
  <transition name="fade-slide" mode="out-in" appear>
    <section class="cus-scroll-y app-page-container flex-col bg-[#f5f6fb] p-15 dark:bg-hex-121212">
      <slot />
      <AppFooter v-if="showFooter" mt-15 />
      <n-back-top :bottom="20" />
    </section>
  </transition>
</template>

<script setup>
defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.app-page-container {
  width: 100%;
  min-height: 100vh;
  max-width: 100vw;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* 确保子元素不会超出容器宽度 */
.app-page-container :deep(*) {
  max-width: 100%;
  box-sizing: border-box;
}

/* 特别处理表格容器 */
.app-page-container :deep(.crud-table-container) {
  width: 100%;
  overflow: hidden;
}

.app-page-container :deep(.crud-table-container .n-card) {
  overflow: hidden;
}
</style>
