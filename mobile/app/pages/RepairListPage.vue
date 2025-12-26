<template>
  <Page>
    <ActionBar title="维修记录">
      <NavigationButton
        text="返回"
        android.systemIcon="ic_menu_back"
        @tap="$navigateBack()"
      />
      <ActionItem
        text="刷新"
        @tap="loadRepairs"
        ios.position="right"
        android.position="actionBar"
      />
    </ActionBar>
    
    <GridLayout rows="auto, *">
      <!-- 状态过滤栏 -->
      <StackLayout row="0" class="filter-bar">
        <GridLayout columns="*, *, *">
          <Button
            col="0"
            :text="selectedStatus === 'all' ? '全部 ✓' : '全部'"
            @tap="filterByStatus('all')"
            :class="['filter-btn', selectedStatus === 'all' ? 'active' : '']"
          />
          <Button
            col="1"
            :text="selectedStatus === 'pending' ? '进行中 ✓' : '进行中'"
            @tap="filterByStatus('pending')"
            :class="['filter-btn', selectedStatus === 'pending' ? 'active' : '']"
          />
          <Button
            col="2"
            :text="selectedStatus === 'completed' ? '已完成 ✓' : '已完成'"
            @tap="filterByStatus('completed')"
            :class="['filter-btn', selectedStatus === 'completed' ? 'active' : '']"
          />
        </GridLayout>
      </StackLayout>

      <!-- 维修记录列表 -->
      <ScrollView row="1">
        <StackLayout class="repair-list-container">
          <!-- 加载指示器 -->
          <StackLayout v-if="loading" class="loading-container">
            <ActivityIndicator :busy="loading" class="loading-indicator" />
            <Label text="加载中..." class="loading-text" />
          </StackLayout>

          <!-- 错误提示 -->
          <StackLayout v-else-if="error" class="error-container">
            <Label text="❌" class="error-icon" />
            <Label :text="error" class="error-text" />
            <Button text="重试" @tap="loadRepairs" class="btn-retry" />
          </StackLayout>

          <!-- 空数据提示 -->
          <StackLayout v-else-if="filteredRepairs.length === 0" class="empty-container">
            <Label text="🔧" class="empty-icon" />
            <Label text="暂无维修记录" class="empty-text" />
          </StackLayout>

          <!-- 维修记录列表 -->
          <StackLayout v-else>
            <StackLayout
              v-for="repair in filteredRepairs"
              :key="repair.id"
              class="repair-item"
              @tap="handleRepairClick(repair)"
            >
              <!-- 维修头部 -->
              <GridLayout columns="auto, *, auto" class="repair-header">
                <Label col="0" text="🔧" class="repair-icon" />
                <StackLayout col="1" class="repair-info">
                  <Label :text="repair.device_name || '未知设备'" class="repair-device" />
                  <Label :text="'工单号: ' + repair.work_order_no" class="repair-order" />
                </StackLayout>
                <Label
                  col="2"
                  :text="getStatusText(repair.status)"
                  :class="['status-badge', `status-${repair.status}`]"
                />
              </GridLayout>

              <!-- 维修详情 -->
              <StackLayout class="repair-details">
                <GridLayout columns="auto, *" class="detail-row">
                  <Label col="0" text="故障类型:" class="detail-label" />
                  <Label col="1" :text="repair.fault_type || '未知'" class="detail-value" />
                </GridLayout>
                <GridLayout columns="auto, *" class="detail-row">
                  <Label col="0" text="负责人:" class="detail-label" />
                  <Label col="1" :text="repair.technician_name || '未分配'" class="detail-value" />
                </GridLayout>
                <GridLayout columns="auto, *" class="detail-row">
                  <Label col="0" text="报修时间:" class="detail-label" />
                  <Label col="1" :text="formatDateTime(repair.reported_at)" class="detail-value" />
                </GridLayout>
                <GridLayout v-if="repair.completed_at" columns="auto, *" class="detail-row">
                  <Label col="0" text="完成时间:" class="detail-label" />
                  <Label col="1" :text="formatDateTime(repair.completed_at)" class="detail-value" />
                </GridLayout>
              </StackLayout>

              <!-- 故障描述 -->
              <Label
                v-if="repair.fault_description"
                :text="'💬 ' + repair.fault_description"
                class="repair-description"
              />

              <!-- 维修进度 -->
              <GridLayout
                v-if="repair.status === 'in_progress'"
                columns="auto, *"
                class="progress-bar"
              >
                <Label col="0" text="进度:" class="progress-label" />
                <StackLayout col="1" class="progress-track">
                  <StackLayout
                    :width="(repair.progress || 0) + '%'"
                    class="progress-fill"
                  />
                </StackLayout>
              </GridLayout>
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
import { $navigateBack } from 'nativescript-vue';

// 数据状态
const repairs = ref<any[]>([]);
const loading = ref(false);
const error = ref('');
const selectedStatus = ref('all');

// 计算属性 - 过滤后的维修记录
const filteredRepairs = computed(() => {
  if (selectedStatus.value === 'all') {
    return repairs.value;
  }
  return repairs.value.filter(repair => repair.status === selectedStatus.value);
});

/**
 * 加载维修记录
 */
async function loadRepairs() {
  try {
    loading.value = true;
    error.value = '';
    
    const result = await api.maintenance.getList({ page: 1, page_size: 100 });
    
    repairs.value = result.items || [];
    console.log(`加载了 ${repairs.value.length} 条维修记录`);
  } catch (err: any) {
    console.error('加载维修记录失败:', err);
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
 * 按状态过滤
 */
function filterByStatus(status: string) {
  selectedStatus.value = status;
}

/**
 * 点击维修记录
 */
async function handleRepairClick(repair: any) {
  const message = [
    `设备: ${repair.device_name || '未知'}`,
    `工单号: ${repair.work_order_no}`,
    `故障类型: ${repair.fault_type || '未知'}`,
    `负责人: ${repair.technician_name || '未分配'}`,
    `状态: ${getStatusText(repair.status)}`,
    `\n${repair.fault_description || '无描述'}`
  ].join('\n');
  
  await alert({
    title: '维修详情',
    message: message,
    okButtonText: '确定'
  });
}

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': '待处理',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  };
  return statusMap[status] || '未知';
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// 组件挂载时加载数据
onMounted(() => {
  loadRepairs();
});
</script>

<style scoped>
/* 过滤栏 */
.filter-bar {
  background-color: #FFFFFF;
  padding: 8 15;
  border-bottom-width: 1;
  border-bottom-color: #E0E0E0;
}

.filter-btn {
  font-size: 13;
  color: #666666;
  background-color: #F5F5F5;
  margin: 0 3;
  padding: 8 0;
  border-radius: 5;
  border-width: 0;
}

.filter-btn.active {
  color: #FFFFFF;
  background-color: #4A90E2;
}

/* 容器 */
.repair-list-container {
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

/* 维修项 */
.repair-item {
  background-color: #FFFFFF;
  border-radius: 8;
  padding: 15;
  margin-bottom: 10;
}

/* 维修头部 */
.repair-header {
  margin-bottom: 10;
}

.repair-icon {
  font-size: 28;
  width: 35;
  text-align: center;
  vertical-align: center;
}

.repair-info {
  margin-left: 10;
  vertical-align: center;
}

.repair-device {
  font-size: 15;
  font-weight: bold;
  color: #333333;
  margin-bottom: 3;
}

.repair-order {
  font-size: 11;
  color: #999999;
}

/* 状态徽章 */
.status-badge {
  font-size: 11;
  padding: 3 10;
  border-radius: 10;
  vertical-align: center;
}

.status-pending {
  color: #FF9800;
  background-color: #FFF3E0;
}

.status-in_progress {
  color: #2196F3;
  background-color: #E3F2FD;
}

.status-completed {
  color: #4CAF50;
  background-color: #E8F5E9;
}

.status-cancelled {
  color: #9E9E9E;
  background-color: #F5F5F5;
}

/* 维修详情 */
.repair-details {
  padding: 10 0;
}

.detail-row {
  margin-bottom: 5;
}

.detail-label {
  font-size: 12;
  color: #999999;
  width: 75;
}

.detail-value {
  font-size: 12;
  color: #666666;
  margin-left: 10;
}

/* 故障描述 */
.repair-description {
  font-size: 12;
  color: #666666;
  padding: 10;
  background-color: #F9F9F9;
  border-radius: 5;
  margin-top: 5;
  line-height: 1.4;
}

/* 进度条 */
.progress-bar {
  margin-top: 10;
  padding-top: 10;
  border-top-width: 1;
  border-top-color: #F0F0F0;
}

.progress-label {
  font-size: 12;
  color: #999999;
  width: 45;
  vertical-align: center;
}

.progress-track {
  height: 8;
  background-color: #E0E0E0;
  border-radius: 4;
  margin-left: 10;
  vertical-align: center;
}

.progress-fill {
  height: 8;
  background-color: #4CAF50;
  border-radius: 4;
}
</style>

