<template>
  <Page>
    <ActionBar title="设备监控系统" />
    
    <StackLayout class="login-container">
      <!-- Logo 区域 -->
      <StackLayout class="logo-section">
        <Label text="📱" class="logo-icon" />
        <Label text="设备监控系统" class="app-title" />
        <Label text="DeviceMonitor Mobile" class="app-subtitle" />
      </StackLayout>

      <!-- 登录表单 -->
      <StackLayout class="form-section">
        <Label text="欢迎登录" class="form-title" />
        
        <!-- 用户名 -->
        <StackLayout class="input-group">
          <Label text="用户名" class="input-label" />
          <TextField
            v-model="username"
            hint="请输入用户名"
            keyboardType="email"
            autocorrect="false"
            autocapitalizationType="none"
            class="input-field"
            :isEnabled="!loading"
          />
        </StackLayout>
        
        <!-- 密码 -->
        <StackLayout class="input-group">
          <Label text="密码" class="input-label" />
          <TextField
            v-model="password"
            hint="请输入密码"
            secure="true"
            class="input-field"
            :isEnabled="!loading"
            @returnPress="handleLogin"
          />
        </StackLayout>
        
        <!-- 记住密码 -->
        <GridLayout columns="auto, *" class="remember-row">
          <Switch
            col="0"
            v-model="rememberPassword"
            :isEnabled="!loading"
            class="remember-switch"
          />
          <Label
            col="1"
            text="记住密码"
            class="remember-label"
            @tap="toggleRemember"
          />
        </GridLayout>
        
        <!-- 登录按钮 -->
        <Button
          text="登录"
          @tap="handleLogin"
          :isEnabled="!loading && canLogin"
          class="btn-primary"
          :class="{ 'btn-disabled': loading || !canLogin }"
        />
        
        <!-- 加载指示器 -->
        <ActivityIndicator
          v-if="loading"
          :busy="loading"
          class="loading-indicator"
        />
        
        <!-- 错误提示 -->
        <Label
          v-if="errorMessage"
          :text="errorMessage"
          class="error-message"
        />
      </StackLayout>

      <!-- 版本信息 -->
      <StackLayout class="footer-section">
        <Label text="Version 1.0.0" class="version-text" />
      </StackLayout>
    </StackLayout>
  </Page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { $navigateTo } from 'nativescript-vue';
import HomePage from './HomePage.vue';
import { alert } from '@nativescript/core/ui/dialogs';
import { getString, setString, remove } from '@nativescript/core/application-settings';

// Store
const authStore = useAuthStore();

// 表单数据
const username = ref('');
const password = ref('');
const rememberPassword = ref(false);
const loading = ref(false);
const errorMessage = ref('');

// 存储键名
const STORAGE_KEY_USERNAME = 'saved_username';
const STORAGE_KEY_PASSWORD = 'saved_password';
const STORAGE_KEY_REMEMBER = 'remember_password';

// 计算属性
const canLogin = computed(() => {
  return username.value.trim() !== '' && password.value.trim() !== '';
});

/**
 * 处理登录
 */
async function handleLogin() {
  // 清除之前的错误信息
  errorMessage.value = '';
  
  // 验证输入
  if (!username.value.trim()) {
    errorMessage.value = '请输入用户名';
    return;
  }
  
  if (!password.value.trim()) {
    errorMessage.value = '请输入密码';
    return;
  }

  try {
    loading.value = true;
    
    // 调用登录
    await authStore.login(username.value.trim(), password.value);
    
    // 保存或清除凭据
    if (rememberPassword.value) {
      saveCredentials();
    } else {
      clearSavedCredentials();
    }
    
    // 登录成功，跳转到首页
    console.log('登录成功，跳转到首页');
    $navigateTo(HomePage, {
      clearHistory: true, // 清除历史记录，防止返回到登录页
    });
  } catch (error: any) {
    console.error('登录失败:', error);
    
    // 显示错误信息
    const message = error.message || '登录失败，请检查用户名和密码';
    errorMessage.value = message;
    
    // 显示弹窗
    await alert({
      title: '登录失败',
      message: message,
      okButtonText: '确定'
    });
  } finally {
    loading.value = false;
  }
}

/**
 * 保存凭据
 */
function saveCredentials() {
  setString(STORAGE_KEY_USERNAME, username.value.trim());
  setString(STORAGE_KEY_PASSWORD, password.value);
  setString(STORAGE_KEY_REMEMBER, 'true');
  console.log('凭据已保存');
}

/**
 * 清除保存的凭据
 */
function clearSavedCredentials() {
  remove(STORAGE_KEY_USERNAME);
  remove(STORAGE_KEY_PASSWORD);
  remove(STORAGE_KEY_REMEMBER);
  console.log('凭据已清除');
}

/**
 * 加载保存的凭据
 */
function loadSavedCredentials() {
  const remember = getString(STORAGE_KEY_REMEMBER, 'false');
  if (remember === 'true') {
    username.value = getString(STORAGE_KEY_USERNAME, '');
    password.value = getString(STORAGE_KEY_PASSWORD, '');
    rememberPassword.value = true;
    console.log('已加载保存的凭据');
  }
}

/**
 * 切换记住密码
 */
function toggleRemember() {
  rememberPassword.value = !rememberPassword.value;
}

/**
 * 组件挂载时加载保存的凭据
 */
onMounted(() => {
  loadSavedCredentials();
});
</script>

<style scoped>
.login-container {
  background: linear-gradient(180deg, #4A90E2 0%, #357ABD 100%);
  padding: 0;
  height: 100%;
}

/* Logo 区域 */
.logo-section {
  padding: 60 20 40 20;
  horizontal-align: center;
}

.logo-icon {
  font-size: 60;
  text-align: center;
  margin-bottom: 10;
}

.app-title {
  font-size: 28;
  font-weight: bold;
  color: #FFFFFF;
  text-align: center;
  margin-bottom: 5;
}

.app-subtitle {
  font-size: 14;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
}

/* 表单区域 */
.form-section {
  background-color: #FFFFFF;
  border-radius: 20 20 0 0;
  padding: 30 20 40 20;
  margin-top: 20;
}

.form-title {
  font-size: 24;
  font-weight: bold;
  color: #333333;
  text-align: center;
  margin-bottom: 30;
}

/* 输入组 */
.input-group {
  margin-bottom: 15;
}

/* 记住密码 */
.remember-row {
  margin-bottom: 20;
  vertical-align: center;
}

.remember-switch {
  margin-right: 10;
  vertical-align: center;
}

.remember-label {
  font-size: 14;
  color: #666666;
  vertical-align: center;
}

.input-label {
  font-size: 14;
  color: #666666;
  margin-bottom: 8;
}

.input-field {
  font-size: 16;
  color: #333333;
  padding: 15 15;
  background-color: #F5F5F5;
  border-radius: 8;
  border-width: 1;
  border-color: #E0E0E0;
}

/* 按钮 */
.btn-primary {
  font-size: 18;
  font-weight: bold;
  color: #FFFFFF;
  background-color: #4A90E2;
  padding: 16 0;
  border-radius: 8;
  margin-top: 10;
}

.btn-disabled {
  background-color: #CCCCCC;
}

/* 加载指示器 */
.loading-indicator {
  margin-top: 20;
  color: #4A90E2;
}

/* 错误信息 */
.error-message {
  font-size: 14;
  color: #F44336;
  text-align: center;
  margin-top: 15;
  padding: 10;
  background-color: #FFEBEE;
  border-radius: 5;
}

/* 页脚 */
.footer-section {
  padding: 20;
  horizontal-align: center;
}

.version-text {
  font-size: 12;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}
</style>

