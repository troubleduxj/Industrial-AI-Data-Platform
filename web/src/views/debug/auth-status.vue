<template>
  <div class="auth-status-page">
    <n-card title="认证状态诊断" class="mb-4">
      <template #header-extra>
        <n-space>
          <n-button :loading="loading" @click="refreshDiagnosis">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新诊断
          </n-button>
          <n-button type="info" @click="exportReport">
            <template #icon>
              <n-icon><DownloadIcon /></n-icon>
            </template>
            导出报告
          </n-button>
          <n-button type="warning" @click="clearAuth">
            <template #icon>
              <n-icon><TrashIcon /></n-icon>
            </template>
            清除认证
          </n-button>
        </n-space>
      </template>

      <n-alert v-if="diagnosis.hasToken && !diagnosis.tokenExpired" type="success" class="mb-4">
        ✅ 认证状态正常
      </n-alert>

      <n-alert v-else-if="diagnosis.hasToken && diagnosis.tokenExpired" type="error" class="mb-4">
        ❌ Token已过期，请重新登录
      </n-alert>

      <n-alert v-else type="warning" class="mb-4"> ⚠️ 未找到有效的认证信息 </n-alert>

      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="Token状态">
          <n-tag :type="diagnosis.hasToken ? 'success' : 'error'">
            {{ diagnosis.hasToken ? '存在' : '不存在' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="Token格式">
          <n-tag :type="diagnosis.tokenValid ? 'success' : 'error'">
            {{ diagnosis.tokenValid ? '有效' : '无效' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="过期状态">
          <n-tag :type="diagnosis.tokenExpired ? 'error' : 'success'">
            {{ diagnosis.tokenExpired ? '已过期' : '未过期' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="用户信息">
          <n-tag :type="diagnosis.hasUserInfo ? 'success' : 'warning'">
            {{ diagnosis.hasUserInfo ? '存在' : '不存在' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="调试信息">
          <n-tag :type="diagnosis.hasDebugInfo ? 'info' : 'warning'">
            {{ diagnosis.hasDebugInfo ? '存在' : '不存在' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="诊断时间">
          {{ formatTime(diagnosis.timestamp) }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- Token详细信息 -->
    <n-card v-if="diagnosis.tokenPayload" title="Token详细信息" class="mb-4">
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="用户名">
          {{ diagnosis.tokenPayload.username }}
        </n-descriptions-item>

        <n-descriptions-item label="用户ID">
          {{ diagnosis.tokenPayload.userId }}
        </n-descriptions-item>

        <n-descriptions-item label="签发时间">
          {{ formatTime(diagnosis.tokenPayload.issuedAt) }}
        </n-descriptions-item>

        <n-descriptions-item label="过期时间">
          {{ formatTime(diagnosis.tokenPayload.expiresAt) }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 过期检查 -->
    <n-card v-if="expiration.hasToken" title="过期检查" class="mb-4">
      <n-alert v-if="expiration.warning" type="warning" class="mb-4">
        ⚠️ Token将在 {{ expiration.minutesUntilExpiry }} 分钟后过期
      </n-alert>

      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="过期状态">
          <n-tag :type="expiration.expired ? 'error' : 'success'">
            {{ expiration.expired ? '已过期' : '未过期' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="过期警告">
          <n-tag :type="expiration.warning ? 'warning' : 'info'">
            {{ expiration.warning ? '即将过期' : '正常' }}
          </n-tag>
        </n-descriptions-item>

        <n-descriptions-item label="剩余时间">
          {{ expiration.minutesUntilExpiry }} 分钟
        </n-descriptions-item>

        <n-descriptions-item label="过期时间">
          {{ formatTime(expiration.expiresAt) }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 调试信息 -->
    <n-card v-if="diagnosis.debugInfo" title="调试信息" class="mb-4">
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="设置时间">
          {{ formatTime(diagnosis.debugInfo.setTime) }}
        </n-descriptions-item>

        <n-descriptions-item label="Token长度">
          {{ diagnosis.debugInfo.tokenLength }}
        </n-descriptions-item>

        <n-descriptions-item label="Token前缀">
          <n-code>{{ diagnosis.debugInfo.tokenPrefix }}</n-code>
        </n-descriptions-item>

        <n-descriptions-item label="设置页面">
          <n-ellipsis style="max-width: 300px">
            {{ diagnosis.debugInfo.url }}
          </n-ellipsis>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- LocalStorage信息 -->
    <n-card title="LocalStorage信息" class="mb-4">
      <n-descriptions :column="1" bordered>
        <n-descriptions-item label="存储的键">
          <n-space>
            <n-tag v-for="key in diagnosis.localStorage" :key="key" size="small">
              {{ key }}
            </n-tag>
          </n-space>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 操作建议 -->
    <n-card title="操作建议">
      <n-list>
        <n-list-item v-if="!diagnosis.hasToken">
          <n-thing>
            <template #header>重新登录</template>
            <template #description> 没有找到认证Token，请前往登录页面重新登录。 </template>
            <template #action>
              <n-button type="primary" @click="goToLogin">前往登录</n-button>
            </template>
          </n-thing>
        </n-list-item>

        <n-list-item v-if="diagnosis.hasToken && diagnosis.tokenExpired">
          <n-thing>
            <template #header>Token已过期</template>
            <template #description> 当前Token已过期，请重新登录获取新的Token。 </template>
            <template #action>
              <n-button type="primary" @click="goToLogin">重新登录</n-button>
            </template>
          </n-thing>
        </n-list-item>

        <n-list-item v-if="expiration.warning">
          <n-thing>
            <template #header>Token即将过期</template>
            <template #description>
              Token将在 {{ expiration.minutesUntilExpiry }} 分钟后过期，建议提前刷新。
            </template>
            <template #action>
              <n-button type="warning" @click="refreshToken">刷新Token</n-button>
            </template>
          </n-thing>
        </n-list-item>

        <n-list-item>
          <n-thing>
            <template #header>清除浏览器缓存</template>
            <template #description> 如果遇到认证问题，可以尝试清除浏览器缓存和Cookie。 </template>
            <template #action>
              <n-button type="info" @click="showClearCacheInstructions">查看说明</n-button>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  diagnoseAuthState,
  checkTokenExpiration,
  clearAuthStateEnhanced,
  exportDiagnosticReport,
} from '@/utils/auth-enhanced'
import {
  RefreshOutline as RefreshIcon,
  DownloadOutline as DownloadIcon,
  TrashOutline as TrashIcon,
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const diagnosis = ref({})
const expiration = ref({})

/**
 * 刷新诊断信息
 */
const refreshDiagnosis = async () => {
  loading.value = true
  try {
    diagnosis.value = diagnoseAuthState()
    expiration.value = checkTokenExpiration()
  } catch (error) {
    console.error('诊断失败', error)
    message.error('诊断失败：' + error.message)
  } finally {
    loading.value = false
  }
}

/**
 * 导出诊断报告
 */
const exportReport = () => {
  try {
    const report = exportDiagnosticReport()
    const blob = new Blob([report], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `auth-diagnosis-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    message.success('诊断报告已导出')
  } catch (error) {
    console.error('导出失败', error)
    message.error('导出失败：' + error.message)
  }
}

/**
 * 清除认证状态
 */
const clearAuth = () => {
  try {
    clearAuthStateEnhanced()
    message.success('认证状态已清除')
    refreshDiagnosis()
  } catch (error) {
    console.error('清除失败', error)
    message.error('清除失败：' + error.message)
  }
}

/**
 * 前往登录页面
 */
const goToLogin = () => {
  router.push('/login')
}

/**
 * 刷新Token（暂未实现）
 */
const refreshToken = () => {
  message.info('Token自动刷新功能暂未实现，请重新登录')
  goToLogin()
}

/**
 * 显示清除缓存说明
 */
const showClearCacheInstructions = () => {
  message.info('请按 Ctrl+Shift+Delete 打开清除浏览器数据对话框，选择清除缓存和Cookie')
}

/**
 * 格式化时间
 */
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 组件挂载时自动诊断
onMounted(() => {
  refreshDiagnosis()
})
</script>

<style scoped>
.auth-status-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
