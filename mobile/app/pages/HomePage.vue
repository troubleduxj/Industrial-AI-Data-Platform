<template>
  <Page>
    <ActionBar title="首页">
      <ActionItem
        text="退出"
        @tap="handleLogout"
        ios.position="right"
        android.position="actionBar"
      />
    </ActionBar>
    
    <ScrollView>
      <StackLayout class="home-container">
        <!-- 用户信息卡片 -->
        <StackLayout class="user-card">
          <Label text="👤" class="user-avatar" />
          <Label :text="`欢迎回来，${displayName}`" class="user-greeting" />
          <Label
            v-if="isSuperUser"
            text="🔑 超级管理员"
            class="user-role super-admin"
          />
          <Label
            v-else
            text="👨‍💼 普通用户"
            class="user-role"
          />
        </StackLayout>

        <!-- 快捷菜单 -->
        <StackLayout class="menu-section">
          <Label text="快捷功能" class="section-title" />
          
          <!-- 设备管理 -->
          <StackLayout class="menu-item" @tap="navigateToDeviceList">
            <Label text="📱" class="menu-icon" />
            <StackLayout class="menu-content">
              <Label text="设备列表" class="menu-title" />
              <Label text="查看和管理所有设备" class="menu-desc" />
            </StackLayout>
            <Label text="›" class="menu-arrow" />
          </StackLayout>
          
          <!-- 告警管理 -->
          <StackLayout class="menu-item" @tap="navigateToAlarmList">
            <Label text="🔔" class="menu-icon" />
            <StackLayout class="menu-content">
              <Label text="告警列表" class="menu-title" />
              <Label text="查看设备告警信息" class="menu-desc" />
            </StackLayout>
            <Label text="›" class="menu-arrow" />
          </StackLayout>
          
          <!-- 维修记录 -->
          <StackLayout class="menu-item" @tap="navigateToRepairList">
            <Label text="🔧" class="menu-icon" />
            <StackLayout class="menu-content">
              <Label text="维修记录" class="menu-title" />
              <Label text="设备维修历史记录" class="menu-desc" />
            </StackLayout>
            <Label text="›" class="menu-arrow" />
          </StackLayout>
          
          <!-- 扫码功能 -->
          <StackLayout class="menu-item menu-item-highlight" @tap="handleScanQR">
            <Label text="📷" class="menu-icon" />
            <StackLayout class="menu-content">
              <Label text="扫码录入" class="menu-title" />
              <Label text="扫描设备二维码快速录入" class="menu-desc" />
            </StackLayout>
            <Label text="›" class="menu-arrow" />
          </StackLayout>
        </StackLayout>

        <!-- 系统信息 -->
        <StackLayout class="info-section">
          <Label text="系统信息" class="section-title" />
          <Label :text="`API 地址: ${apiBaseURL}`" class="info-text" />
          <Label text="版本: 1.0.0" class="info-text" />
        </StackLayout>
      </StackLayout>
    </ScrollView>
  </Page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { $navigateTo } from 'nativescript-vue';
import LoginPage from './LoginPage.vue';
import DeviceListPage from './DeviceListPage.vue';
import AlarmListPage from './AlarmListPage.vue';
import RepairListPage from './RepairListPage.vue';
import { confirm, alert } from '@nativescript/core/ui/dialogs';
import { isAndroid } from '@nativescript/core';

// Store
const authStore = useAuthStore();

// 计算属性
const displayName = computed(() => authStore.displayName);
const isSuperUser = computed(() => authStore.isSuperUser);

// API 地址显示
const apiBaseURL = computed(() => {
  const isDev = true; // TODO: 从环境变量读取
  if (isDev) {
    return isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
  }
  return 'https://your-api.com';
});

/**
 * 退出登录
 */
async function handleLogout() {
  const result = await confirm({
    title: '确认退出',
    message: '确定要退出登录吗？',
    okButtonText: '确定',
    cancelButtonText: '取消'
  });

  if (result) {
    await authStore.logout();
    
    // 跳转到登录页
    $navigateTo(LoginPage, {
      clearHistory: true,
    });
  }
}

/**
 * 导航到设备列表
 */
function navigateToDeviceList() {
  $navigateTo(DeviceListPage);
}

/**
 * 导航到告警列表
 */
function navigateToAlarmList() {
  $navigateTo(AlarmListPage);
}

/**
 * 导航到维修记录
 */
function navigateToRepairList() {
  $navigateTo(RepairListPage);
}

/**
 * 扫码功能（待实现）
 */
function handleScanQR() {
  alert({
    title: '功能开发中',
    message: '二维码扫描功能正在开发中...',
    okButtonText: '确定'
  });
}
</script>

<style scoped>
.home-container {
  background-color: #F5F5F5;
  padding: 0 0 20 0;
}

/* 用户信息卡片 */
.user-card {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  padding: 30 20;
  margin-bottom: 10;
}

.user-avatar {
  font-size: 60;
  text-align: center;
  margin-bottom: 10;
}

.user-greeting {
  font-size: 20;
  font-weight: bold;
  color: #FFFFFF;
  text-align: center;
  margin-bottom: 8;
}

.user-role {
  font-size: 14;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  padding: 5 15;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 12;
  horizontal-align: center;
}

.user-role.super-admin {
  background-color: rgba(255, 215, 0, 0.3);
  color: #FFD700;
}

/* 菜单区域 */
.menu-section {
  background-color: #FFFFFF;
  padding: 15 20;
  margin-bottom: 10;
}

.section-title {
  font-size: 16;
  font-weight: bold;
  color: #333333;
  margin-bottom: 15;
}

/* 菜单项 */
.menu-item {
  orientation: horizontal;
  padding: 15 0;
  border-bottom-width: 1;
  border-bottom-color: #F0F0F0;
  vertical-align: center;
}

.menu-item:last-child {
  border-bottom-width: 0;
}

.menu-item-highlight {
  background-color: #FFF9E6;
  margin: 10 -20;
  padding: 15 20;
  border-radius: 8;
  border-bottom-width: 0;
}

.menu-icon {
  font-size: 32;
  width: 50;
  text-align: center;
  vertical-align: center;
}

.menu-content {
  flex-grow: 1;
  margin-left: 10;
}

.menu-title {
  font-size: 16;
  font-weight: bold;
  color: #333333;
  margin-bottom: 4;
}

.menu-desc {
  font-size: 13;
  color: #999999;
}

.menu-arrow {
  font-size: 24;
  color: #CCCCCC;
  width: 30;
  text-align: right;
  vertical-align: center;
}

/* 系统信息 */
.info-section {
  background-color: #FFFFFF;
  padding: 15 20;
}

.info-text {
  font-size: 13;
  color: #666666;
  margin-bottom: 8;
}
</style>

