<template>
  <div class="maintenance-dashboard">
    <!-- 页面标题 -->
    <div class="dashboard-header">
      <n-page-header title="设备维护看板" subtitle="实时监控设备维护状态和统计信息">
        <template #extra>
          <n-space>
            <n-button type="primary" @click="refreshData">
              <template #icon>
                <n-icon><RefreshIcon /></n-icon>
              </template>
              刷新数据
            </n-button>
            <n-button @click="exportReport">
              <template #icon>
                <n-icon><DownloadIcon /></n-icon>
              </template>
              导出报告
            </n-button>
          </n-space>
        </template>
      </n-page-header>
    </div>

    <!-- 统计卡片区域 -->
    <div class="stats-section">
      <n-grid :cols="4" :x-gap="16" :y-gap="16">
        <n-grid-item>
          <n-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <n-icon size="32"><DeviceIcon /></n-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ totalDevices }}</div>
                <div class="stat-label">设备总数</div>
              </div>
            </div>
          </n-card>
        </n-grid-item>

        <n-grid-item>
          <n-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon normal">
                <n-icon size="32"><CheckCircleIcon /></n-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ normalDevices }}</div>
                <div class="stat-label">正常设备</div>
              </div>
            </div>
          </n-card>
        </n-grid-item>

        <n-grid-item>
          <n-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon warning">
                <n-icon size="32"><WarningIcon /></n-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ warningDevices }}</div>
                <div class="stat-label">预警设备</div>
              </div>
            </div>
          </n-card>
        </n-grid-item>

        <n-grid-item>
          <n-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon error">
                <n-icon size="32"><CloseCircleIcon /></n-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ errorDevices }}</div>
                <div class="stat-label">故障设备</div>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 图表和数据展示区域 -->
    <div class="charts-section">
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <!-- 设备状态分布图 -->
        <n-grid-item>
          <n-card title="设备状态分布" class="chart-card">
            <div class="chart-container">
              <div class="pie-chart-placeholder">
                <div class="chart-legend">
                  <div class="legend-item">
                    <span class="legend-color normal"></span>
                    <span>正常 ({{ normalDevices }})</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color warning"></span>
                    <span>预警 ({{ warningDevices }})</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color error"></span>
                    <span>故障 ({{ errorDevices }})</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color maintenance"></span>
                    <span>维护中 ({{ maintenanceDevices }})</span>
                  </div>
                </div>
              </div>
            </div>
          </n-card>
        </n-grid-item>

        <!-- 维护趋势图 -->
        <n-grid-item>
          <n-card title="维护趋势" class="chart-card">
            <div class="chart-container">
              <div class="line-chart-placeholder">
                <div class="trend-data">
                  <div v-for="item in maintenanceTrend" :key="item.month" class="trend-item">
                    <div class="trend-bar" :style="{ height: item.height }"></div>
                    <div class="trend-label">{{ item.month }}</div>
                  </div>
                </div>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 维护记录和任务区域 -->
    <div class="records-section">
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <!-- 最近维护记录 -->
        <n-grid-item>
          <n-card title="最近维护记录" class="records-card">
            <template #header-extra>
              <n-button text @click="viewAllRecords">查看全部</n-button>
            </template>
            <n-list>
              <n-list-item v-for="record in recentRecords" :key="record.id">
                <div class="record-item">
                  <div class="record-header">
                    <span class="device-name">{{ record.deviceName }}</span>
                    <n-tag :type="getRecordType(record.status)" size="small">
                      {{ record.status }}
                    </n-tag>
                  </div>
                  <div class="record-details">
                    <div class="record-info">
                      <span class="record-type">{{ record.type }}</span>
                      <span class="record-date">{{ record.date }}</span>
                    </div>
                    <div class="record-description">{{ record.description }}</div>
                  </div>
                </div>
              </n-list-item>
            </n-list>
          </n-card>
        </n-grid-item>

        <!-- 待处理任务 -->
        <n-grid-item>
          <n-card title="待处理任务" class="tasks-card">
            <template #header-extra>
              <n-button text @click="viewAllTasks">查看全部</n-button>
            </template>
            <n-list>
              <n-list-item v-for="task in pendingTasks" :key="task.id">
                <div class="task-item">
                  <div class="task-header">
                    <span class="task-title">{{ task.title }}</span>
                    <n-tag :type="getPriorityType(task.priority)" size="small">
                      {{ task.priority }}
                    </n-tag>
                  </div>
                  <div class="task-details">
                    <div class="task-info">
                      <span class="task-device">{{ task.deviceName }}</span>
                      <span class="task-deadline">截止: {{ task.deadline }}</span>
                    </div>
                    <div class="task-assignee">负责人: {{ task.assignee }}</div>
                  </div>
                </div>
              </n-list-item>
            </n-list>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 设备健康度排行 -->
    <div class="health-section">
      <n-card title="设备健康度排行" class="health-card">
        <n-grid :cols="3" :x-gap="16">
          <n-grid-item>
            <div class="health-category">
              <h4>健康度最高</h4>
              <div class="health-list">
                <div v-for="device in topHealthDevices" :key="device.id" class="health-item">
                  <div class="device-info">
                    <span class="device-name">{{ device.name }}</span>
                    <span class="device-location">{{ device.location }}</span>
                  </div>
                  <div class="good health-score">{{ device.health }}%</div>
                </div>
              </div>
            </div>
          </n-grid-item>

          <n-grid-item>
            <div class="health-category">
              <h4>需要关注</h4>
              <div class="health-list">
                <div v-for="device in attentionDevices" :key="device.id" class="health-item">
                  <div class="device-info">
                    <span class="device-name">{{ device.name }}</span>
                    <span class="device-location">{{ device.location }}</span>
                  </div>
                  <div class="health-score warning">{{ device.health }}%</div>
                </div>
              </div>
            </div>
          </n-grid-item>

          <n-grid-item>
            <div class="health-category">
              <h4>紧急处理</h4>
              <div class="health-list">
                <div v-for="device in urgentDevices" :key="device.id" class="health-item">
                  <div class="device-info">
                    <span class="device-name">{{ device.name }}</span>
                    <span class="device-location">{{ device.location }}</span>
                  </div>
                  <div class="health-score error">{{ device.health }}%</div>
                </div>
              </div>
            </div>
          </n-grid-item>
        </n-grid>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPageHeader,
  NCard,
  NGrid,
  NGridItem,
  NButton,
  NSpace,
  NIcon,
  NList,
  NListItem,
  NTag,
  useMessage,
} from 'naive-ui'
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Desktop as DeviceIcon,
  CheckmarkCircle as CheckCircleIcon,
  Warning as WarningIcon,
  CloseCircle as CloseCircleIcon,
} from '@vicons/ionicons5'
import deviceMaintenanceApi from '@/api/device-maintenance'
import deviceV2Api from '@/api/device-v2'

// 使用正确的 API 导出
const deviceApi = deviceV2Api

const message = useMessage()
const router = useRouter()

// 数据加载状态
const loading = ref(false)

// 统计数据
const totalDevices = ref(0)
const normalDevices = ref(0)
const warningDevices = ref(0)
const errorDevices = ref(0)
const maintenanceDevices = ref(0)

// 维护趋势数据
const maintenanceTrend = ref([])

// 最近维护记录
const recentRecords = ref([])

// 待处理任务
const pendingTasks = ref([])

// 设备健康度数据
const topHealthDevices = ref([])
const attentionDevices = ref([])
const urgentDevices = ref([])

// 维修记录统计
const repairStatistics = ref({
  total_records: 0,
  status_statistics: {},
  priority_statistics: {},
  device_type_statistics: {},
  monthly_statistics: {}
})

// 加载设备统计数据
const loadDeviceStatistics = async () => {
  try {
    const response = await deviceApi.getStatistics()
    if (response && response.data) {
      const stats = response.data
      totalDevices.value = stats.total_devices || 0
      normalDevices.value = stats.online_devices || 0
      warningDevices.value = stats.warning_devices || 0
      errorDevices.value = stats.offline_devices || 0
      maintenanceDevices.value = stats.maintenance_devices || 0
    }
  } catch (error) {
    console.error('加载设备统计数据失败:', error)
  }
}

// 加载维护统计数据
const loadMaintenanceStatistics = async () => {
  try {
    const response = await deviceMaintenanceApi.getMaintenanceStatistics()
    if (response && response.data) {
      const stats = response.data
      
      // 处理维护趋势数据（最近6个月）
      if (stats.monthly_statistics) {
        const months = Object.keys(stats.monthly_statistics).slice(0, 6).reverse()
        const maxCount = Math.max(...Object.values(stats.monthly_statistics))
        
        maintenanceTrend.value = months.map(month => {
          const count = stats.monthly_statistics[month]
          return {
            month: month.split('-')[1] + '月',
            count,
            height: maxCount > 0 ? `${(count / maxCount) * 100}%` : '0%'
          }
        })
      }
    }
  } catch (error) {
    console.error('加载维护统计数据失败:', error)
  }
}

// 加载维修记录统计
const loadRepairStatistics = async () => {
  try {
    const response = await deviceMaintenanceApi.getRepairStatistics()
    if (response && response.data) {
      repairStatistics.value = response.data
    }
  } catch (error) {
    console.error('加载维修记录统计失败:', error)
  }
}

// 加载最近维护记录
const loadRecentRecords = async () => {
  try {
    const response = await deviceMaintenanceApi.getMaintenanceRecords({
      page: 1,
      page_size: 4
    })
    if (response && response.data) {
      const records = response.data.records || response.data.data || []
      recentRecords.value = records.map(record => ({
        id: record.id,
        deviceName: record.device_name || record.device_code,
        status: getStatusText(record.maintenance_status),
        type: getMaintenanceTypeText(record.maintenance_type),
        date: formatDate(record.planned_start_time || record.created_at),
        description: record.maintenance_description || record.maintenance_title || '-'
      }))
    }
  } catch (error) {
    console.error('加载最近维护记录失败:', error)
  }
}

// 加载待处理任务
const loadPendingTasks = async () => {
  try {
    const response = await deviceMaintenanceApi.getMaintenanceRecords({
      maintenance_status: 'planned',
      page: 1,
      page_size: 4
    })
    if (response && response.data) {
      const records = response.data.records || response.data.data || []
      pendingTasks.value = records.map(record => ({
        id: record.id,
        title: record.maintenance_title,
        deviceName: record.device_name || record.device_code,
        priority: getPriorityText(record.priority),
        deadline: formatDate(record.planned_end_time),
        assignee: record.assigned_to || '未分配'
      }))
    }
  } catch (error) {
    console.error('加载待处理任务失败:', error)
  }
}

// 加载设备健康度数据
const loadDeviceHealth = async () => {
  try {
    const response = await deviceApi.list({ page: 1, page_size: 50 })
    if (response && response.data) {
      const devices = response.data.records || response.data.data || []
      
      // 计算设备健康度（基于设备状态）
      const devicesWithHealth = devices.map(device => ({
        id: device.id,
        name: device.device_name || device.device_code,
        location: device.location || device.team_name || '-',
        health: calculateDeviceHealth(device)
      })).sort((a, b) => b.health - a.health)
      
      // 分类设备
      topHealthDevices.value = devicesWithHealth.filter(d => d.health >= 90).slice(0, 3)
      attentionDevices.value = devicesWithHealth.filter(d => d.health >= 60 && d.health < 90).slice(0, 3)
      urgentDevices.value = devicesWithHealth.filter(d => d.health < 60).slice(0, 3)
    }
  } catch (error) {
    console.error('加载设备健康度数据失败:', error)
  }
}

// 计算设备健康度
const calculateDeviceHealth = (device) => {
  // 基于设备状态计算健康度
  const statusMap = {
    'online': 95,
    'running': 98,
    'idle': 90,
    'warning': 70,
    'alarm': 50,
    'offline': 30,
    'fault': 20
  }
  return statusMap[device.device_status] || statusMap[device.status] || 85
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'planned': '待处理',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 获取维护类型文本
const getMaintenanceTypeText = (type) => {
  const typeMap = {
    'preventive': '预防性维护',
    'corrective': '故障维修',
    'routine': '定期保养',
    'upgrade': '升级维护'
  }
  return typeMap[type] || type
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const priorityMap = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'urgent': '紧急'
  }
  return priorityMap[priority] || priority
}

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadDeviceStatistics(),
      loadMaintenanceStatistics(),
      loadRepairStatistics(),
      loadRecentRecords(),
      loadPendingTasks(),
      loadDeviceHealth()
    ])
    message.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    message.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  message.info('正在导出维护报告...')
  // TODO: 实现导出功能
}

const viewAllRecords = () => {
  router.push('/device-maintenance/repair-records')
}

const viewAllTasks = () => {
  router.push('/device-maintenance/repair-records?status=planned')
}

const getRecordType = (status) => {
  const typeMap = {
    '已完成': 'success',
    '进行中': 'warning',
    '待处理': 'info',
    '已取消': 'default'
  }
  return typeMap[status] || 'default'
}

const getPriorityType = (priority) => {
  const typeMap = {
    '紧急': 'error',
    '高': 'warning',
    '中': 'info',
    '低': 'default'
  }
  return typeMap[priority] || 'default'
}

// 页面加载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.maintenance-dashboard {
  padding: 16px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 24px;
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.normal {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-icon.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.error {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card {
  height: 300px;
}

.chart-container {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-chart-placeholder {
  text-align: center;
}

.chart-legend {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.normal {
  background: #52c41a;
}

.legend-color.warning {
  background: #faad14;
}

.legend-color.error {
  background: #ff4d4f;
}

.legend-color.maintenance {
  background: #1890ff;
}

.line-chart-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trend-data {
  display: flex;
  align-items: end;
  gap: 20px;
  height: 150px;
}

.trend-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.trend-bar {
  width: 30px;
  background: linear-gradient(to top, #1890ff, #40a9ff);
  border-radius: 4px 4px 0 0;
  min-height: 20px;
}

.trend-label {
  font-size: 12px;
  color: #666;
}

.records-section {
  margin-bottom: 24px;
}

.records-card,
.tasks-card {
  height: 400px;
}

.record-item,
.task-item {
  width: 100%;
}

.record-header,
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.device-name,
.task-title {
  font-weight: 500;
  color: #333;
}

.record-details,
.task-details {
  color: #666;
  font-size: 14px;
}

.record-info,
.task-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.record-description,
.task-assignee {
  font-size: 13px;
  color: #999;
}

.health-section {
  margin-bottom: 24px;
}

.health-card {
  min-height: 300px;
}

.health-category h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
}

.health-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 4px solid #e0e0e0;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-name {
  font-weight: 500;
  color: #333;
}

.device-location {
  font-size: 12px;
  color: #999;
}

.health-score {
  font-weight: bold;
  font-size: 18px;
  padding: 4px 8px;
  border-radius: 4px;
}

.health-score.good {
  color: #52c41a;
  background: #f6ffed;
}

.health-score.warning {
  color: #faad14;
  background: #fffbe6;
}

.health-score.error {
  color: #ff4d4f;
  background: #fff2f0;
}
</style>
