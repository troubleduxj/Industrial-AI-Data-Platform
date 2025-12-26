<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: '监测看板' })

interface ModuleConfig {
  title: string
  description: string
  icon: string
  basePath: string
}

// 模块配置
const moduleConfig: ModuleConfig = {
  title: '监测看板',
  description:
    '监测看板模块提供焊机监测看板、切割机监测看板等实时监控界面，帮助您直观了解设备运行状态。',
  icon: 'material-symbols:dashboard',
  basePath: '/dashboard',
}
</script>
