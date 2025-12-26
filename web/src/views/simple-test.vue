<template>
  <div style="padding: 20px; text-align: center">
    <h1>简单测试页面</h1>
    <p>如果你能看到这个页面，说明路由工作正常！</p>
    <p>当前时间: {{ new Date().toLocaleString() }}</p>

    <div style="margin-top: 20px">
      <button
        style="
          padding: 10px 20px;
          margin: 5px;
          background: #1890ff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        "
        @click="goToTest"
      >
        跳转到权限测试
      </button>
      <button
        style="
          padding: 10px 20px;
          margin: 5px;
          background: #52c41a;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        "
        @click="goToComponents"
      >
        跳转到权限组件
      </button>
    </div>

    <div
      style="
        margin-top: 20px;
        text-align: left;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
      "
    >
      <h3>路由调试信息:</h3>
      <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto">{{
        routeDebugInfo
      }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const routeDebugInfo = ref('')

const goToTest = () => {
  router.push('/test/permission').catch((err) => {
    console.error('路由跳转失败:', err)
    alert('路由跳转失败: ' + err.message)
  })
}

const goToComponents = () => {
  router.push('/test/components').catch((err) => {
    console.error('路由跳转失败:', err)
    alert('路由跳转失败: ' + err.message)
  })
}

onMounted(() => {
  const routes = router.getRoutes()
  const testRoutes = routes.filter(
    (route) =>
      route.path.includes('/test') ||
      (route.name && route.name.toString().toLowerCase().includes('test'))
  )

  routeDebugInfo.value = JSON.stringify(
    {
      totalRoutes: routes.length,
      testRoutesCount: testRoutes.length,
      testRoutes: testRoutes.map((route) => ({
        name: route.name,
        path: route.path,
        hasComponent: !!route.component,
      })),
      currentRoute: {
        path: router.currentRoute.value.path,
        name: router.currentRoute.value.name,
      },
    },
    null,
    2
  )

  console.log('路由调试信息:', {
    allRoutes: routes,
    testRoutes: testRoutes,
  })
})
</script>
