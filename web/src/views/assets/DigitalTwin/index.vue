<template>
  <div class="digital-twin-container">
    <Monitor v-if="componentType === 'monitor'" />
    <div v-else class="placeholder-content">
      <n-card title="数字孪生 (Digital Twin)">
        <template #header-extra>
          <n-tag type="info">V5 Module</n-tag>
        </template>
        <p>Real-time monitoring and 3D visualization of assets.</p>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, defineAsyncComponent } from 'vue'

const Monitor = defineAsyncComponent({
  loader: () => import('@/views/device-monitor/monitor/index.vue').catch(() => ({ template: '<div>Legacy Monitor not found</div>' })),
  delay: 200,
  timeout: 3000
})

const componentType = ref('monitor')
</script>