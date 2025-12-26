<template>
  <ModuleNavigation :module-config="moduleConfig" :auto-generate-from-routes="true" />
</template>

<script setup lang="ts">
import ModuleNavigation from '@/components/navigation/ModuleNavigation.vue'

defineOptions({ name: '系统管理' })

// 模块配置
const moduleConfig = {
  title: '系统管理',
  description:
    '系统管理模块提供用户管理、角色管理、菜单管理、API管理等系统配置功能，帮助您管理系统权限和配置。',
  icon: 'material-symbols:settings',
  basePath: '/system',
}
</script>
