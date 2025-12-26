<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: 'AI监测' })

// 模块配置
const moduleConfig = {
  title: 'AI监测',
  description:
    'AI监测模块提供智能异常检测、健康评分、趋势预测等人工智能分析功能，帮助您实现预测性维护。',
  icon: 'material-symbols:psychology',
  basePath: '/ai-monitor',
}
</script>
