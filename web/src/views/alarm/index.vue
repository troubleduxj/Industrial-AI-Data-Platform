<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: '告警中心' })

// 模块配置
const moduleConfig = {
  title: '告警中心',
  description: '告警中心模块提供设备报警信息管理、报警分析等功能，帮助您及时发现和处理设备异常。',
  icon: 'material-symbols:warning',
  basePath: '/alarm',
}
</script>
