<template>
  <div style="padding: 20px">
    <h1>调试测试页面</h1>
    <p>如果你能看到这个页面，说明路由系统工作正常。</p>

    <n-card title="路由信息">
      <p><strong>当前路由:</strong> {{ $route.path }}</p>
      <p><strong>路由名称:</strong> {{ $route.name }}</p>
      <p><strong>查询参数:</strong> {{ JSON.stringify($route.query) }}</p>
    </n-card>

    <n-card title="测试链接" style="margin-top: 20px">
      <n-space>
        <n-button @click="$router.push('/test/permission')"> 跳转到权限测试页面 </n-button>
        <n-button @click="$router.push('/test/components')"> 跳转到权限组件页面 </n-button>
        <n-button @click="checkRoutes"> 检查路由 </n-button>
      </n-space>
    </n-card>

    <n-card v-if="routeInfo" title="路由调试信息" style="margin-top: 20px">
      <pre>{{ routeInfo }}</pre>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NButton, NSpace } from 'naive-ui'

const router = useRouter()
const routeInfo = ref('')

const checkRoutes = () => {
  const routes = router.getRoutes()
  const testRoutes = routes.filter(
    (route) => route.path.includes('/test') || route.name?.toString().toLowerCase().includes('test')
  )

  routeInfo.value = JSON.stringify(
    {
      totalRoutes: routes.length,
      testRoutes: testRoutes.map((route) => ({
        name: route.name,
        path: route.path,
        component: route.component?.name || 'Unknown',
      })),
      allRouteNames: routes.map((r) => r.name).filter(Boolean),
    },
    null,
    2
  )

  console.log('所有路由:', routes)
  console.log('测试相关路由:', testRoutes)
}
</script>
