<template>
  <AppPage :show-footer="true" bg-cover :style="{ backgroundImage: `url(${bgImg})` }">
    <div
      style="transform: translateY(25px)"
      class="m-auto max-w-1500 min-w-345 f-c-c rounded-10 bg-white bg-opacity-60 p-15 card-shadow"
      dark:bg-dark
    >
      <div hidden w-380 bg-primary px-20 py-35 md:block>
        <icon-custom-front-page pt-10 text-300 color-primary></icon-custom-front-page>
      </div>

      <div w-320 flex-col px-20 py-35>
        <h5 f-c-c text-24 font-normal color="#6a6a6a">
          <icon-custom-logo mr-10 text-50 color-primary />{{ $t('app_name') }}
        </h5>
        <div mt-30>
          <n-input
            v-model:value="loginInfo.username"
            autofocus
            class="h-50 items-center pl-10 text-16"
            placeholder="请输入用户名"
            :maxlength="20"
          />
        </div>
        <div mt-30>
          <n-input
            v-model:value="loginInfo.password"
            class="h-50 items-center pl-10 text-16"
            type="password"
            show-password-on="mousedown"
            placeholder="请输入密码"
            :maxlength="20"
            @keypress.enter="handleLogin"
          />
        </div>

        <div mt-20>
          <n-button
            h-50
            w-full
            rounded-5
            text-16
            type="primary"
            :loading="loading"
            @click="handleLogin"
          >
            <template #loading>
              <icon-custom-logo class="animate-spin" />
            </template>
            {{ $t('views.login.text_login') }}
          </n-button>
        </div>
      </div>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { lStorage, setToken } from '@/utils'
import { setTokenEnhanced } from '@/utils/auth-enhanced'
import bgImg from '@/assets/images/login_bg.webp'
import { apiV2 } from '@/api/v2'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/store'

const router = useRouter()
const { query } = useRoute()
const { t } = useI18n({ useScope: 'global' })

interface LoginInfo {
  username: string
  password: string
}

const loginInfo = ref<LoginInfo>({
  username: '',
  password: '',
})

initLoginInfo()

function initLoginInfo() {
  const localLoginInfo = lStorage.get('loginInfo')
  if (localLoginInfo) {
    loginInfo.value.username = localLoginInfo.username || ''
    loginInfo.value.password = localLoginInfo.password || ''
  }
}

const loading = ref<boolean>(false)
async function handleLogin() {
  const { username, password } = loginInfo.value
  if (!username || !password) {
    $message.warning(t('views.login.message_input_username_password'))
    return
  }
  try {
    loading.value = true
    $message.loading(t('views.login.message_login_success'))
    const res = await apiV2.login({ username, password: password.toString() })
    $message.success(t('views.login.message_login_success'))

    // 清空旧的用户信息，确保每次登录都从干净状态开始
    const userStore = useUserStore()
    userStore.userInfo = {}

    // 使用增强版token管理
    const tokenSaved = setTokenEnhanced(res.data.access_token, res.data.user)
    if (!tokenSaved) {
      console.error('Token保存失败，但继续登录流程')
    }

    // 保持兼容性，同时调用原来的setToken
    setToken(res.data.access_token)
    await addDynamicRoutes()
    if (query.redirect) {
      const path = query.redirect
      console.log('path', { path, query })
      Reflect.deleteProperty(query, 'redirect')
      router.push({ path, query })
    } else {
      router.push('/')
    }
  } catch (e) {
    console.error('login error', e)

    // 检查错误是否已经被HTTP拦截器处理
    // 如果错误有 success 字段且为 false，说明已经被 ErrorHandler 处理过
    if (!(e && typeof e === 'object' && e.success === false)) {
      // 只有未被处理的错误才显示消息
      $message.error(e.response?.data?.detail || e.message || '登录失败，请检查用户名和密码')
    }
  }
  loading.value = false
}
</script>
