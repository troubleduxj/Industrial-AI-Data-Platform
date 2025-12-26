<template>
  <Page>
    <ActionBar title="设备列表">
      <NavigationButton
        text="返回"
        android.systemIcon="ic_menu_back"
        @tap="$navigateBack()"
      />
      <ActionItem
        text="刷新"
        @tap="loadDevices"
        ios.position="right"
        android.position="actionBar"
      />
    </ActionBar>
    
    <GridLayout rows="auto, *">
      <!-- 搜索栏 -->
      <StackLayout row="0" class="search-bar">
        <TextField
          v-model="searchQuery"
          hint="搜索设备名称或编号..."
          @textChange="handleSearch"
          class="search-input"
        />
      </StackLayout>

      <!-- 设备列表 -->
      <ScrollView row="1">
        <StackLayout class="device-list-container">
          <!-- 加载指示器 -->
          <StackLayout v-if="loading" class="loading-container">
            <ActivityIndicator :busy="loading" class="loading-indicator" />
            <Label text="加载中..." class="loading-text" />
          </StackLayout>

          <!-- 错误提示 -->
          <StackLayout v-else-if="error" class="error-container">
            <Label text="❌" class="error-icon" />
            <Label :text="error" class="error-text" />
            <Button text="重试" @tap="loadDevices" class="btn-retry" />
          </StackLayout>

          <!-- 空数据提示 -->
          <StackLayout v-else-if="filteredDevices.length === 0" class="empty-container">
            <Label text="📦" class="empty-icon" />
            <Label text="暂无设备数据" class="empty-text" />
          </StackLayout>

          <!-- 设备列表 -->
          <StackLayout v-else>
            <StackLayout
              v-for="device in filteredDevices"
              :key="device.id"
              class="device-item"
              @tap="navigateToDeviceDetail(device)"
            >
              <!-- 设备头部 -->
              <GridLayout columns="auto, *, auto" class="device-header">
                <Label col="0" :text="getDeviceIcon(device)" class="device-icon" />
                <StackLayout col="1" class="device-info">
                  <Label :text="device.name" class="device-name" />
                  <Label :text="device.device_code" class="device-code" />
                </StackLayout>
                <Label
                  col="2"
                  :text="getStatusText(device.status)"
                  :class="['status-badge', `status-${device.status}`]"
                />
              </GridLayout>

              <!-- 设备详情 -->
              <StackLayout class="device-details">
                <GridLayout columns="auto, *" class="detail-row">
                  <Label col="0" text="位置:" class="detail-label" />
                  <Label col="1" :text="device.location || '未设置'" class="detail-value" />
                </GridLayout>
                <GridLayout columns="auto, *" class="detail-row">
                  <Label col="0" text="类型:" class="detail-label" />
                  <Label col="1" :text="device.device_type || '未知'" class="detail-value" />
                </GridLayout>
                <GridLayout v-if="device.last_maintenance" columns="auto, *" class="detail-row">
                  <Label col="0" text="上次维护:" class="detail-label" />
                  <Label col="1" :text="formatDate(device.last_maintenance)" class="detail-value" />
                </GridLayout>
              </StackLayout>
            </StackLayout>
          </StackLayout>
        </StackLayout>
      </ScrollView>
    </GridLayout>
  </Page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { api } from '../services/apiService';
import { alert } from '@nativescript/core/ui/dialogs';
import { $navigateTo, $navigateBack } from 'nativescript-vue';
import DeviceDetailPage from './DeviceDetailPage.vue';

// 数据状态
const devices = ref<any[]>([]);
const loading = ref(false);
const error = ref('');
const searchQuery = ref('');

// 计算属性 - 过滤后的设备列表
const filteredDevices = computed(() => {
  if (!searchQuery.value.trim()) {
    return devices.value;
  }
  
  const query = searchQuery.value.toLowerCase();
  return devices.value.filter(device => 
    device.name?.toLowerCase().includes(query) ||
    device.device_code?.toLowerCase().includes(query)
  );
});

/**
 * 加载设备列表
 */
async function loadDevices() {
  try {
    loading.value = true;
    error.value = '';
    
    const result = await api.devices.getList({ page: 1, page_size: 100 });
    
    devices.value = result.items || [];
    console.log(`加载了 ${devices.value.length} 个设备`);
  } catch (err: any) {
    console.error('加载设备列表失败:', err);
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
 * 搜索处理
 */
function handleSearch() {
  // 搜索由 computed 自动处理
  console.log('搜索:', searchQuery.value);
}

/**
 * 导航到设备详情
 */
function navigateToDeviceDetail(device: any) {
  $navigateTo(DeviceDetailPage, {
    props: { deviceId: device.id }
  });
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
  return icons[device.device_type] || icons.default;
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
  if (!dateString) return '未知';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

// 组件挂载时加载数据
onMounted(() => {
  loadDevices();
});
</script>

<style scoped>
/* 搜索栏 */
.search-bar {
  background-color: #FFFFFF;
  padding: 10 15;
  border-bottom-width: 1;
  border-bottom-color: #E0E0E0;
}

.search-input {
  font-size: 14;
  padding: 10 15;
  background-color: #F5F5F5;
  border-radius: 8;
  border-width: 0;
}

/* 容器 */
.device-list-container {
  background-color: #F5F5F5;
  padding: 10 15;
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

/* 空数据状态 */
.empty-container {
  padding: 50 20;
  horizontal-align: center;
}

.empty-icon {
  font-size: 48;
  text-align: center;
  margin-bottom: 15;
}

.empty-text {
  font-size: 14;
  color: #999999;
  text-align: center;
}

/* 设备项 */
.device-item {
  background-color: #FFFFFF;
  border-radius: 8;
  padding: 15;
  margin-bottom: 10;
}

/* 设备头部 */
.device-header {
  margin-bottom: 10;
}

.device-icon {
  font-size: 32;
  width: 40;
  text-align: center;
  vertical-align: center;
}

.device-info {
  margin-left: 10;
  vertical-align: center;
}

.device-name {
  font-size: 16;
  font-weight: bold;
  color: #333333;
  margin-bottom: 3;
}

.device-code {
  font-size: 12;
  color: #999999;
}

/* 状态徽章 */
.status-badge {
  font-size: 11;
  padding: 3 10;
  border-radius: 10;
  vertical-align: center;
}

.status-online {
  color: #4CAF50;
  background-color: #E8F5E9;
}

.status-offline {
  color: #9E9E9E;
  background-color: #F5F5F5;
}

.status-alarm {
  color: #F44336;
  background-color: #FFEBEE;
}

.status-maintenance {
  color: #FF9800;
  background-color: #FFF3E0;
}

.status-fault {
  color: #E91E63;
  background-color: #FCE4EC;
}

/* 设备详情 */
.device-details {
  padding-top: 10;
  border-top-width: 1;
  border-top-color: #F0F0F0;
}

.detail-row {
  margin-bottom: 5;
}

.detail-label {
  font-size: 12;
  color: #999999;
  width: 70;
}

.detail-value {
  font-size: 12;
  color: #666666;
  margin-left: 10;
}
</style>

