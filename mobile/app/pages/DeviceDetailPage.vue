<template>
  <Page>
    <ActionBar :title="device?.name || '设备详情'">
      <NavigationButton
        text="返回"
        android.systemIcon="ic_menu_back"
        @tap="$navigateBack()"
      />
    </ActionBar>
    
    <ScrollView>
      <StackLayout class="detail-container">
        <!-- 加载指示器 -->
        <StackLayout v-if="loading" class="loading-container">
          <ActivityIndicator :busy="loading" class="loading-indicator" />
          <Label text="加载中..." class="loading-text" />
        </StackLayout>

        <!-- 错误提示 -->
        <StackLayout v-else-if="error" class="error-container">
          <Label text="❌" class="error-icon" />
          <Label :text="error" class="error-text" />
          <Button text="重试" @tap="loadDeviceDetail" class="btn-retry" />
        </StackLayout>

        <!-- 设备详情内容 -->
        <StackLayout v-else-if="device">
          <!-- 设备头部卡片 -->
          <StackLayout class="device-header-card">
            <Label :text="getDeviceIcon(device)" class="device-big-icon" />
            <Label :text="device.name" class="device-name" />
            <Label :text="device.device_code" class="device-code" />
            <Label
              :text="getStatusText(device.status)"
              :class="['status-badge', `status-${device.status}`]"
            />
          </StackLayout>

          <!-- 基本信息 -->
          <StackLayout class="info-section">
            <Label text="基本信息" class="section-title" />
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="设备编号:" class="info-label" />
              <Label col="1" :text="device.device_code || '-'" class="info-value" />
            </GridLayout>
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="设备类型:" class="info-label" />
              <Label col="1" :text="device.device_type || '-'" class="info-value" />
            </GridLayout>
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="设备型号:" class="info-label" />
              <Label col="1" :text="device.model || '-'" class="info-value" />
            </GridLayout>
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="制造商:" class="info-label" />
              <Label col="1" :text="device.manufacturer || '-'" class="info-value" />
            </GridLayout>
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="安装位置:" class="info-label" />
              <Label col="1" :text="device.location || '-'" class="info-value" />
            </GridLayout>
          </StackLayout>

          <!-- 运行状态 -->
          <StackLayout class="info-section">
            <Label text="运行状态" class="section-title" />
            <GridLayout columns="120, *" class="info-row">
              <Label col="0" text="当前状态:" class="info-label" />
              <Label col="1" :text="getStatusText(device.status)" class="info-value info-value-bold" />
            </GridLayout>
            <GridLayout v-if="device.last_online_time" columns="120, *" class="info-row">
              <Label col="0" text="最后在线:" class="info-label" />
              <Label col="1" :text="formatDateTime(device.last_online_time)" class="info-value" />
            </GridLayout>
            <GridLayout v-if="device.uptime" columns="120, *" class="info-row">
              <Label col="0" text="运行时长:" class="info-label" />
              <Label col="1" :text="formatUptime(device.uptime)" class="info-value" />
            </GridLayout>
          </StackLayout>

          <!-- 维护信息 -->
          <StackLayout class="info-section">
            <Label text="维护信息" class="section-title" />
            <GridLayout v-if="device.last_maintenance" columns="120, *" class="info-row">
              <Label col="0" text="上次维护:" class="info-label" />
              <Label col="1" :text="formatDateTime(device.last_maintenance)" class="info-value" />
            </GridLayout>
            <GridLayout v-if="device.next_maintenance" columns="120, *" class="info-row">
              <Label col="0" text="下次维护:" class="info-label" />
              <Label col="1" :text="formatDateTime(device.next_maintenance)" class="info-value" />
            </GridLayout>
            <GridLayout v-if="device.maintenance_interval" columns="120, *" class="info-row">
              <Label col="0" text="维护周期:" class="info-label" />
              <Label col="1" :text="device.maintenance_interval + ' 天'" class="info-value" />
            </GridLayout>
          </StackLayout>

          <!-- 其他信息 -->
          <StackLayout class="info-section">
            <Label text="其他信息" class="section-title" />
            <GridLayout v-if="device.installation_date" columns="120, *" class="info-row">
              <Label col="0" text="安装日期:" class="info-label" />
              <Label col="1" :text="formatDate(device.installation_date)" class="info-value" />
            </GridLayout>
            <GridLayout v-if="device.warranty_expiry" columns="120, *" class="info-row">
              <Label col="0" text="保修期至:" class="info-label" />
              <Label col="1" :text="formatDate(device.warranty_expiry)" class="info-value" />
            </GridLayout>
            <GridLayout v-if="device.description" columns="120, *" class="info-row">
              <Label col="0" text="备注:" class="info-label" />
              <Label col="1" :text="device.description" class="info-value" textWrap="true" />
            </GridLayout>
          </StackLayout>

          <!-- 操作按钮 -->
          <StackLayout class="action-section">
            <Button
              text="查看告警记录"
              @tap="viewAlarms"
              class="btn-action btn-alarm"
            />
            <Button
              text="查看维修记录"
              @tap="viewRepairs"
              class="btn-action btn-repair"
            />
          </StackLayout>
        </StackLayout>
      </StackLayout>
    </ScrollView>
  </Page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../services/apiService';
import { alert } from '@nativescript/core/ui/dialogs';
import { $navigateBack } from 'nativescript-vue';

// Props
const props = defineProps<{
  deviceId: number;
}>();

// 数据状态
const device = ref<any>(null);
const loading = ref(false);
const error = ref('');

/**
 * 加载设备详情
 */
async function loadDeviceDetail() {
  try {
    loading.value = true;
    error.value = '';
    
    const result = await api.devices.getById(props.deviceId);
    device.value = result;
    
    console.log('设备详情:', device.value);
  } catch (err: any) {
    console.error('加载设备详情失败:', err);
    error.value = err.message || '加载失败';
    
    await alert({
      title: '加载失败',
      message: error.value,
      okButtonText: '确定'
    });
  } finally {
    loading.value = false;
  }
}

/**
 * 查看告警记录
 */
async function viewAlarms() {
  await alert({
    title: '告警记录',
    message: `查看设备 ${device.value?.name} 的告警记录`,
    okButtonText: '确定'
  });
  // TODO: 导航到告警列表，过滤当前设备
}

/**
 * 查看维修记录
 */
async function viewRepairs() {
  await alert({
    title: '维修记录',
    message: `查看设备 ${device.value?.name} 的维修记录`,
    okButtonText: '确定'
  });
  // TODO: 导航到维修列表，过滤当前设备
}

/**
 * 获取设备图标
 */
function getDeviceIcon(device: any): string {
  const icons: Record<string, string> = {
    'sensor': '🌡️',
    'motor': '⚙️',
    'pump': '💧',
    'valve': '🔧',
    'default': '📱'
  };
  return icons[device?.device_type] || icons.default;
}

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'online': '在线',
    'offline': '离线',
    'alarm': '告警',
    'maintenance': '维护中',
    'fault': '故障'
  };
  return statusMap[status] || '未知';
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

/**
 * 格式化运行时长
 */
function formatUptime(seconds: number): string {
  if (!seconds) return '-';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  const parts = [];
  if (days > 0) parts.push(`${days}天`);
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  
  return parts.join(' ') || '-';
}

// 组件挂载时加载数据
onMounted(() => {
  loadDeviceDetail();
});
</script>

<style scoped>
.detail-container {
  background-color: #F5F5F5;
  padding: 0 0 20 0;
}

/* 加载状态 */
.loading-container {
  padding: 50 20;
  horizontal-align: center;
}

.loading-indicator {
  color: #4A90E2;
}

.loading-text {
  font-size: 14;
  color: #999999;
  text-align: center;
  margin-top: 10;
}

/* 错误状态 */
.error-container {
  padding: 50 20;
  horizontal-align: center;
}

.error-icon {
  font-size: 48;
  text-align: center;
  margin-bottom: 15;
}

.error-text {
  font-size: 14;
  color: #F44336;
  text-align: center;
  margin-bottom: 20;
}

.btn-retry {
  font-size: 14;
  color: #FFFFFF;
  background-color: #4A90E2;
  padding: 10 30;
  border-radius: 5;
}

/* 设备头部卡片 */
.device-header-card {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  padding: 30 20;
  horizontal-align: center;
  margin-bottom: 10;
}

.device-big-icon {
  font-size: 80;
  text-align: center;
  margin-bottom: 15;
}

.device-name {
  font-size: 24;
  font-weight: bold;
  color: #FFFFFF;
  text-align: center;
  margin-bottom: 5;
}

.device-code {
  font-size: 14;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  margin-bottom: 15;
}

/* 状态徽章 */
.status-badge {
  font-size: 14;
  padding: 8 20;
  border-radius: 15;
  horizontal-align: center;
}

.status-online {
  color: #4CAF50;
  background-color: rgba(255, 255, 255, 0.9);
}

.status-offline {
  color: #9E9E9E;
  background-color: rgba(255, 255, 255, 0.9);
}

.status-alarm {
  color: #F44336;
  background-color: rgba(255, 255, 255, 0.9);
}

.status-maintenance {
  color: #FF9800;
  background-color: rgba(255, 255, 255, 0.9);
}

.status-fault {
  color: #E91E63;
  background-color: rgba(255, 255, 255, 0.9);
}

/* 信息区域 */
.info-section {
  background-color: #FFFFFF;
  padding: 15 20;
  margin-bottom: 10;
}

.section-title {
  font-size: 16;
  font-weight: bold;
  color: #333333;
  margin-bottom: 15;
  padding-bottom: 10;
  border-bottom-width: 2;
  border-bottom-color: #4A90E2;
}

.info-row {
  margin-bottom: 12;
}

.info-label {
  font-size: 14;
  color: #999999;
}

.info-value {
  font-size: 14;
  color: #333333;
}

.info-value-bold {
  font-weight: bold;
  color: #4A90E2;
}

/* 操作按钮区域 */
.action-section {
  padding: 0 20;
  margin-top: 10;
}

.btn-action {
  font-size: 16;
  font-weight: bold;
  color: #FFFFFF;
  padding: 15 0;
  border-radius: 8;
  margin-bottom: 10;
}

.btn-alarm {
  background-color: #F44336;
}

.btn-repair {
  background-color: #FF9800;
}
</style>

