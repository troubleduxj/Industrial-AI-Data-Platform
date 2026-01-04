<template>
  <div class="asset-types-container">
    <Type v-if="componentType === 'type'" />
    <div v-else class="placeholder-content">
      <n-card title="资产类型 (Asset Types)">
        <template #header-extra>
          <n-tag type="info">V5 Module</n-tag>
        </template>
        <p>Manage Asset Classifications and Definitions.</p>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, defineAsyncComponent } from 'vue'

const Type = defineAsyncComponent({
  loader: () => import('@/views/device/type/index.vue').catch(() => ({ template: '<div>Legacy Type not found</div>' })),
  delay: 200,
  timeout: 3000
})

const componentType = ref('type')
</script>