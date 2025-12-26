<template>
  <Page>
    <ActionBar title="告警列表">
      <NavigationButton
        text="返回"
        android.systemIcon="ic_menu_back"
        @tap="$navigateBack()"
      />
      <ActionItem
        text="刷新"
        @tap="loadAlarms"
        ios.position="right"
        android.position="actionBar"
      />
    </ActionBar>
    
    <GridLayout rows="auto, *">
      <!-- 过滤栏 -->
      <StackLayout row="0" class="filter-bar">
        <GridLayout columns="*, *, *">
          <Button
            col="0"
            :text="selectedLevel === 'all' ? '全部 ✓' : '全部'"
            @tap="filterByLevel('all')"
            :class="['filter-btn', selectedLevel === 'all' ? 'active' : '']"
          />
          <Button
            col="1"
            :text="selectedLevel === 'high' ? '紧急 ✓' : '紧急'"
            @tap="filterByLevel('high')"
            :class="['filter-btn', selectedLevel === 'high' ? 'active' : '']"
          />
          <Button
            col="2"
            :text="selectedLevel === 'medium' ? '一般 ✓' : '一般'"
            @tap="filterByLevel('medium')"
            :class="['filter-btn', selectedLevel === 'medium' ? 'active' : '']"
          />
        </GridLayout>
      </StackLayout>

      <!-- 告警列表 -->
      <ScrollView row="1">
        <StackLayout class="alarm-list-container">
          <!-- 加载指示器 -->
          <StackLayout v-if="loading" class="loading-container">
            <ActivityIndicator :busy="loading" class="loading-indicator" />
            <Label text="加载中..." class="loading-text" />
          </StackLayout>

          <!-- 错误提示 -->
          <StackLayout v-else-if="error" class="error-container">
            <Label text="❌" class="error-icon" />
            <Label :text="error" class="error-text" />
            <Button text="重试" @tap="loadAlarms" class="btn-retry" />
          </StackLayout>

          <!-- 空数据提示 -->
          <StackLayout v-else-if="filteredAlarms.length === 0" class="empty-container">
            <Label text="🔔" class="empty-icon" />
            <Label text="暂无告警信息" class="empty-text" />
          </StackLayout>

          <!-- 告警列表 -->
          <StackLayout v-else>
            <StackLayout
              v-for="alarm in filteredAlarms"
              :key="alarm.id"
              class="alarm-item"
              @tap="handleAlarmClick(alarm)"
            >
              <!-- 告警头部 -->
              <GridLayout columns="auto, *, auto" class="alarm-header">
                <Label col="0" :text="getLevelIcon(alarm.level)" class="alarm-icon" />
                <StackLayout col="1" class="alarm-info">
                  <Label :text="alarm.title || '设备告警'" class="alarm-title" />
                  <Label :text="alarm.device_name || '未知设备'" class="alarm-device" />
                </StackLayout>
                <Label
                  col="2"
                  :text="getLevelText(alarm.level)"
                  :class="['level-badge', `level-${alarm.level}`]"
                />
              </GridLayout>

              <!-- 告警内容 -->
              <Label :text="alarm.message || '无详细信息'" class="alarm-message" />

              <!-- 告警时间 -->
              <GridLayout columns="auto, *, auto" class="alarm-footer">
                <Label col="0" :text="'🕐 ' + formatDateTime(alarm.created_at)" class="alarm-time" />
                <Label
                  col="2"
                  :text="alarm.status === 'resolved' ? '✓ 已处理' : '待处理'"
                  :class="['status-text', alarm.status === 'resolved' ? 'resolved' : 'pending']"
                />
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
const alarms = ref<any[]>([]);
const loading = ref(false);
const error = ref('');
const selectedLevel = ref('all');

// 计算属性 - 过滤后的告警列表
const filteredAlarms = computed(() => {
  if (selectedLevel.value === 'all') {
    return alarms.value;
  }
  return alarms.value.filter(alarm => alarm.level === selectedLevel.value);
});

/**
 * 加载告警列表
 */
async function loadAlarms() {
  try {
    loading.value = true;
    error.value = '';
    
    const result = await api.alarms.getList({ page: 1, page_size: 100 });
    
    alarms.value = result.items || [];
    console.log(`加载了 ${alarms.value.length} 条告警`);
  } catch (err: any) {
    console.error('加载告警列表失败:', err);
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
 * 按级别过滤
 */
function filterByLevel(level: string) {
  selectedLevel.value = level;
}

/**
 * 点击告警
 */
async function handleAlarmClick(alarm: any) {
  await alert({
    title: alarm.title || '设备告警',
    message: `设备: ${alarm.device_name || '未知'}\n级别: ${getLevelText(alarm.level)}\n时间: ${formatDateTime(alarm.created_at)}\n\n${alarm.message || '无详细信息'}`,
    okButtonText: '确定'
  });
}

/**
 * 获取级别图标
 */
function getLevelIcon(level: string): string {
  const icons: Record<string, string> = {
    'high': '🔴',
    'medium': '🟡',
    'low': '🟢',
    'info': '🔵'
  };
  return icons[level] || '⚪';
}

/**
 * 获取级别文本
 */
function getLevelText(level: string): string {
  const levelMap: Record<string, string> = {
    'high': '紧急',
    'medium': '一般',
    'low': '低',
    'info': '信息'
  };
  return levelMap[level] || '未知';
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// 组件挂载时加载数据
onMounted(() => {
  loadAlarms();
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
.alarm-list-container {
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

/* 告警项 */
.alarm-item {
  background-color: #FFFFFF;
  border-radius: 8;
  padding: 15;
  margin-bottom: 10;
  border-left-width: 4;
  border-left-color: #4A90E2;
}

/* 告警头部 */
.alarm-header {
  margin-bottom: 10;
}

.alarm-icon {
  font-size: 24;
  width: 30;
  text-align: center;
  vertical-align: center;
}

.alarm-info {
  margin-left: 10;
  vertical-align: center;
}

.alarm-title {
  font-size: 15;
  font-weight: bold;
  color: #333333;
  margin-bottom: 3;
}

.alarm-device {
  font-size: 12;
  color: #999999;
}

/* 级别徽章 */
.level-badge {
  font-size: 11;
  padding: 3 10;
  border-radius: 10;
  vertical-align: center;
}

.level-high {
  color: #F44336;
  background-color: #FFEBEE;
}

.level-medium {
  color: #FF9800;
  background-color: #FFF3E0;
}

.level-low {
  color: #4CAF50;
  background-color: #E8F5E9;
}

.level-info {
  color: #2196F3;
  background-color: #E3F2FD;
}

/* 告警内容 */
.alarm-message {
  font-size: 13;
  color: #666666;
  margin-bottom: 10;
  line-height: 1.4;
}

/* 告警页脚 */
.alarm-footer {
  padding-top: 8;
  border-top-width: 1;
  border-top-color: #F0F0F0;
}

.alarm-time {
  font-size: 11;
  color: #999999;
}

.status-text {
  font-size: 11;
  padding: 2 8;
  border-radius: 8;
}

.status-text.resolved {
  color: #4CAF50;
  background-color: #E8F5E9;
}

.status-text.pending {
  color: #FF9800;
  background-color: #FFF3E0;
}
</style>

