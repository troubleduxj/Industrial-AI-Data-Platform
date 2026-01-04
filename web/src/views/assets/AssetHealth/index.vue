<template>
  <div class="asset-health-container">
    <n-card title="资产健康 (Asset Health)">
      <template #header-extra>
        <n-tag type="info">Under Construction</n-tag>
      </template>
      <p>This module is under development.</p>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NCard, NTag } from 'naive-ui'
</script>

<style scoped>
.asset-health-container {
  padding: 16px;
}
</style>
