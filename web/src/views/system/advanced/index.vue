<template>
  <div class="advanced-settings-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'AdvancedSettings' })
</script>

<style scoped>
.advanced-settings-layout {
  height: 100%;
  width: 100%;
}
</style>
