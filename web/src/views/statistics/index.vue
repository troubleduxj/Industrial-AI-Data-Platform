<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: '数据统计' })

// 模块配置
const moduleConfig = {
  title: '数据统计',
  description:
    '数据统计模块提供设备在线率、焊接时长、焊机日报等统计分析功能，帮助您深入了解设备运行效率。',
  icon: 'material-symbols:bar-chart',
  basePath: '/statistics',
}
</script>
