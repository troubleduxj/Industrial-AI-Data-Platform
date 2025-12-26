<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: '设备监测' })

// 模块配置
const moduleConfig = {
  title: '设备监测',
  description: '设备监测模块提供实时设备状态监控、历史数据查询等功能，帮助您及时了解设备运行状况。',
  icon: 'material-symbols:monitor-heart',
  basePath: '/device-monitor',
}
</script>
