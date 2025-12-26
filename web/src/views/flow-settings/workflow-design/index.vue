<template>
  <div class="workflow-design-page">
    <SimpleWorkflowDesigner />
  </div>
</template>

<script setup lang="ts">
import SimpleWorkflowDesigner from './SimpleWorkflowDesigner.vue'
</script>

<style scoped>
.workflow-design-page {
  /* 使用视口高度减去header(60px)和tags(50px)高度来计算 */
  height: calc(100vh - 110px);
  width: 100%;
  overflow: hidden;
}
</style>
