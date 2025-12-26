<template>
  <AppPage>
    <n-result m-auto status="403">
      <template #icon>
        <icon-custom-forbidden text-400px text-primary></icon-custom-forbidden>
      </template>

      <template #default>
        <div class="error-content">
          <h2>权限不足</h2>
          <p class="error-description">抱歉，您没有权限访问此页面。请联系管理员获取相应权限。</p>

          <!-- 权限信息 -->
          <div v-if="showPermissionInfo" class="permission-info">
            <n-card title="权限信息" size="small" class="mt-4">
              <n-descriptions :column="1" size="small">
                <n-descriptions-item label="当前用户">
                  {{ userInfo?.username || '未知' }}
                </n-descriptions-item>
                <n-descriptions-item label="用户角色">
                  <n-space>
                    <n-tag v-for="role in userRoles" :key="role.id" size="small" type="info">
                      {{ role.role_name }}
                    </n-tag>
                    <span v-if="userRoles.length === 0" class="text-gray-400"> 无角色 </span>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="尝试访问">
                  {{ attemptedRoute }}
                </n-descriptions-item>
                <n-descriptions-item label="所需权限">
                  <n-space>
                    <n-tag
                      v-for="permission in requiredPermissions"
                      :key="permission"
                      size="small"
                      type="warning"
                    >
                      {{ permission }}
                    </n-tag>
                    <span v-if="requiredPermissions.length === 0" class="text-gray-400">
                      未知
                    </span>
                  </n-space>
                </n-descriptions-item>
              </n-descriptions>
            </n-card>
          </div>

          <!-- 建议操作 -->
          <div class="suggestions mt-4">
            <n-alert type="info" title="建议操作" class="mb-4">
              <ul class="suggestion-list">
                <li>检查您是否已登录正确的账户</li>
                <li>联系系统管理员申请相应权限</li>
                <li>返回首页查看您可以访问的功能</li>
                <li v-if="canRefreshPermissions">尝试刷新权限数据</li>
              </ul>
            </n-alert>
          </div>
        </div>
      </template>

      <template #footer>
        <n-space>
          <n-button type="primary" @click="goHome"> 返回首页 </n-button>
          <n-button @click="goBack"> 返回上页 </n-button>
          <n-button
            v-if="canRefreshPermissions"
            type="info"
            :loading="isRefreshing"
            @click="refreshPermissions"
          >
            刷新权限
          </n-button>
          <n-button type="default" @click="showPermissionInfo = !showPermissionInfo">
            {{ showPermissionInfo ? '隐藏' : '显示' }}权限信息
          </n-button>
        </n-space>
      </template>
    </n-result>
  </AppPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { useEnhancedPermissionStore } from '@/store/modules/permission'
import { useRoutePermission } from '@/composables/useRoutePermission'
import { NSpace, NButton, NCard, NDescriptions, NDescriptionsItem, NTag, NAlert } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const permissionStore = useEnhancedPermissionStore()
const { getHomeRoute, refreshRoutes } = useRoutePermission()

// 响应式状态
const showPermissionInfo = ref(false)
const isRefreshing = ref(false)

// 计算属性
const userInfo = computed(() => userStore.userInfo)
const userRoles = computed(() => userStore.userInfo?.roles || [])
const attemptedRoute = computed(() => route.query.redirect || route.path)
const canRefreshPermissions = computed(() => !userStore.isLoggingOut && userStore.token)

// 获取所需权限（从路由元信息或查询参数）
const requiredPermissions = computed(() => {
  const permissions = route.query.permissions
  if (permissions) {
    return Array.isArray(permissions) ? permissions : [permissions]
  }

  // 尝试从路由配置获取
  const targetRoute = router.getRoutes().find((r) => r.path === attemptedRoute.value)
  return targetRoute?.meta?.permissions || []
})

// 方法
const goHome = async () => {
  try {
    const homeRoute = getHomeRoute()
    await router.replace(homeRoute)
  } catch (error) {
    console.error('返回首页失败:', error)
    await router.replace('/')
  }
}

const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    goHome()
  }
}

const refreshPermissions = async () => {
  try {
    isRefreshing.value = true

    // 刷新权限数据
    await permissionStore.refreshPermissions()

    // 刷新路由
    await refreshRoutes()

    // 重新检查当前路由权限
    const hasPermission = permissionStore.hasRoutePermission(route)
    if (hasPermission) {
      // 如果现在有权限了，重新导航到目标页面
      const targetPath = attemptedRoute.value
      if (targetPath && targetPath !== route.path) {
        await router.replace(targetPath)
      } else {
        await goHome()
      }
    } else {
      // 仍然没有权限，显示提示
      window.$message?.warning('权限刷新完成，但您仍然没有访问此页面的权限')
    }
  } catch (error) {
    console.error('刷新权限失败:', error)
    window.$message?.error('刷新权限失败，请稍后重试')
  } finally {
    isRefreshing.value = false
  }
}

// 生命周期
onMounted(() => {
  // 记录403访问日志
  console.log('403 Forbidden Access:', {
    user: userInfo.value?.username,
    attemptedRoute: attemptedRoute.value,
    requiredPermissions: requiredPermissions.value,
    userRoles: userRoles.value.map((r) => r.role_name),
    timestamp: new Date().toISOString(),
  })
})
</script>

<style scoped>
.error-content {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.error-description {
  color: #666;
  font-size: 16px;
  margin: 16px 0;
  line-height: 1.6;
}

.permission-info {
  text-align: left;
}

.suggestion-list {
  text-align: left;
  padding-left: 20px;
  margin: 0;
}

.suggestion-list li {
  margin: 8px 0;
  line-height: 1.5;
}

.mt-4 {
  margin-top: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.text-gray-400 {
  color: #9ca3af;
}
</style>
