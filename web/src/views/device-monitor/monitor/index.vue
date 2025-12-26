<template>
  <CommonPage show-footer>
    <!-- 页面标题和操作区 -->
    <template #action>
      <div class="w-full flex items-center justify-end">
        <!-- 右侧操作区域：连接状态 + 视图切换 + 刷新数据按钮 -->
        <div class="flex items-center gap-10">
          <!-- WebSocket连接状态 -->
          <div class="flex items-center gap-5">
            <NTooltip trigger="hover">
              <template #trigger>
                <div
                  class="connection-indicator"
                  :class="{
                    'connection-indicator--connected': isConnected,
                    'connection-indicator--connecting': isConnecting,
                    'connection-indicator--disconnected': !isConnected && !isConnecting,
                  }"
                ></div>
              </template>
              <span>{{ getWebSocketStatusText() }}</span>
            </NTooltip>
          </div>

          <ViewToggle
            v-model="viewMode"
            :options="viewOptions"
            size="small"
            :show-label="false"
            :icon-size="16"
            align="right"
          />
          <PermissionButton
            permission="GET /api/v2/devices"
            type="primary"
            :loading="loading"
            @click="refreshData"
          >
            <TheIcon icon="material-symbols:refresh" :size="18" class="mr-5" />刷新数据
          </PermissionButton>

          <!-- API连接状态指示器 -->
          <div class="flex items-center gap-5">
            <NTooltip trigger="hover">
              <template #trigger>
                <div
                  class="connection-indicator"
                  :class="{
                    'connection-indicator--connected': connectionStatus === 'connected',
                    'connection-indicator--connecting': connectionStatus === 'connecting',
                    'connection-indicator--disconnected': connectionStatus === 'disconnected',
                  }"
                ></div>
              </template>
              <span>{{ getConnectionStatusText() }}</span>
            </NTooltip>
            <PermissionButton
              v-if="connectionStatus === 'disconnected'"
              permission="GET /api/v2/devices/connection"
              size="small"
              type="primary"
              :loading="loading"
              style="margin-left: 8px"
              @click="retryConnection"
            >
              重试连接
            </PermissionButton>
          </div>
        </div>
      </div>
    </template>

    <!-- 筛选条件 -->
    <NCard class="filter-card mb-15" rounded-10>
      <div flex flex-wrap items-center gap-15>
        <QueryBarItem label="设备类型" :label-width="70">
          <NSelect
            v-model:value="filterType"
            style="width: 180px"
            :options="deviceTypeOptions"
            clearable
            placeholder="全部类型"
            @update:value="handleFilterChange"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="40">
          <NSelect
            v-model:value="filterStatus"
            style="width: 120px"
            :options="statusOptions"
            clearable
            placeholder="全部状态"
            @update:value="handleFilterChange"
          />
        </QueryBarItem>
        <QueryBarItem label="设备编码" :label-width="70">
          <NInput
            v-model:value="filterDeviceCode"
            clearable
            type="text"
            placeholder="请输入设备编码"
            style="width: 150px"
            @keypress.enter="handleFilterChange"
          />
        </QueryBarItem>
        <QueryBarItem label="设备名称" :label-width="70">
          <NInput
            v-model:value="filterDeviceName"
            clearable
            type="text"
            placeholder="请输入设备名称"
            style="width: 150px"
            @keypress.enter="handleFilterChange"
          />
        </QueryBarItem>
        <QueryBarItem label="位置" :label-width="40">
          <NInput
            v-model:value="filterLocation"
            clearable
            type="text"
            placeholder="请输入位置"
            style="width: 150px"
            @keypress.enter="handleFilterChange"
          />
        </QueryBarItem>

        <!-- 查询操作按钮 -->
        <div class="ml-20 flex items-center gap-10">
          <PermissionButton
            permission="GET /api/v2/devices"
            type="primary"
            @click="handleFilterChange"
          >
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
          </PermissionButton>
          <PermissionButton permission="GET /api/v2/devices" @click="resetFilters">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
          </PermissionButton>
        </div>
      </div>
    </NCard>

    <!-- 卡片视图 -->
    <div v-if="viewMode === 'card'">
      <FastPermissionWrapper
        :data="filteredDevices"
        :loading="loading"
        permission="GET /api/v2/devices"
        permission-name="设备监测数据"
        empty-description="当前没有设备监测数据，请检查设备连接状态或联系管理员"
        loading-text="正在加载设备监测数据..."
        :show-create="false"
        @refresh="refreshData"
        @contact="handleContactAdmin"
      >
        <template #default="{ data, loading: dataLoading }">
          <!-- 加载进度提示 -->
          <div v-if="loadingProgress && dataLoading" class="mb-4 text-center">
            <NSpin size="small" class="mr-2" />
            <span class="text-gray-600">{{ loadingProgress }}</span>
          </div>
          
          <!-- 设备网格容器 -->
          <div class="device-grid">
            <!-- 骨架屏加载状态 -->
            <template v-if="dataLoading">
              <DeviceCardSkeleton v-for="n in skeletonCount" :key="n" />
            </template>

            <!-- 真实设备卡片 -->
            <template v-else>
              <DeviceCard
                v-for="device in filteredDevices"
                :key="device.id"
                :device="device"
                :monitoring-fields="getDeviceFields(device.device_type)"
                @click="showDeviceDetails(device)"
              >
                <template #actions="{ device }">
                  <div class="flex flex-col gap-2 w-full">
                    <PermissionButton
                      permission="GET /api/v2/devices/{device_id}/charts"
                      class="w-full"
                      type="default"
                      size="small"
                      @click.stop="showDeviceCharts(device)"
                    >
                      <TheIcon icon="material-symbols:history" :size="14" class="mr-5" />
                      查看历史
                    </PermissionButton>
                    <PermissionButton
                      permission="GET /api/v2/devices/{device_id}"
                      class="w-full analyze-device-btn"
                      type="primary"
                      size="small"
                      secondary
                      @click.stop="showDeviceDetails(device)"
                    >
                      <TheIcon icon="material-symbols:analytics" :size="14" class="mr-5" />
                      分析设备
                    </PermissionButton>
                  </div>
                </template>
              </DeviceCard>
            </template>
          </div>
        </template>
      </FastPermissionWrapper>
    </div>

    <!-- 表格视图 -->
    <div v-else-if="viewMode === 'table'">
      <FastPermissionWrapper
        :data="filteredDevices"
        :loading="loading"
        permission="GET /api/v2/devices"
        permission-name="设备监测数据"
        empty-description="当前没有设备监测数据，请检查设备连接状态或联系管理员"
        loading-text="正在加载设备监测数据..."
        :show-create="false"
        @refresh="refreshData"
        @contact="handleContactAdmin"
      >
        <template #default="{ data, loading: dataLoading }">
          <!-- 表格加载状态 -->
          <div v-if="dataLoading" class="py-20 text-center">
            <NSpin size="large" />
            <p class="mt-10 text-gray-500">{{ loadingProgress || '正在加载设备数据...' }}</p>
          </div>

          <!-- 数据表格 -->
          <NDataTable
            v-else
            :columns="tableColumns"
            :data="data"
            :pagination="false"
            :bordered="false"
            striped
            size="medium"
            @row-click="showDeviceDetails"
          />
        </template>
      </FastPermissionWrapper>
    </div>

    <!-- 设备详情弹窗 -->
    <NModal
      v-model:show="detailModalVisible"
      preset="card"
      :title="
        selectedDevice ? `${selectedDevice.name || selectedDevice.id} - 设备详情` : '设备详情'
      "
      size="huge"
      :mask-closable="false"
      class="device-detail-modal"
    >
      <div v-if="selectedDevice" class="device-detail">
        <!-- 设备状态概览卡片 -->
        <div class="device-overview mb-16">
          <div class="overview-header">
            <div class="device-title">
              <TheIcon
                icon="material-symbols:precision-manufacturing"
                :size="24"
                class="device-icon"
              />
              <div class="title-info">
                <h3 class="device-name">{{ selectedDevice.name || selectedDevice.id }}</h3>
                <p class="device-subtitle">
                  {{ getDeviceTypeText(selectedDevice.device_type) }} · ID: {{ selectedDevice.id }}
                </p>
              </div>
            </div>
            <div class="header-right">
              <div class="status-badge">
                <NTag
                  :type="getStatusTagType(selectedDevice.device_status)"
                  size="large"
                  :bordered="false"
                >
                  <template #icon>
                    <TheIcon
                      :icon="
                        selectedDevice.device_status === 1
                          ? 'material-symbols:play-circle'
                          : 'material-symbols:pause-circle'
                      "
                    />
                  </template>
                  {{ getStatusText(selectedDevice.device_status) }}
                </NTag>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-content">
          <!-- 2x2 网格布局 -->
          <div class="detail-grid">
            <!-- 基本信息 -->
            <NCard title="基本信息" class="info-card basic-info">
              <template #header-extra>
                <TheIcon icon="material-symbols:info" :size="16" class="text-blue-500" />
              </template>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:badge" :size="14" />
                    设备名称
                  </div>
                  <div class="info-value">{{ selectedDevice.name || selectedDevice.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:tag" :size="14" />
                    设备编码
                  </div>
                  <div class="info-value">{{ selectedDevice.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:category" :size="14" />
                    设备类型
                  </div>
                  <div class="info-value">
                    <NTag :type="getDeviceTypeTagType(selectedDevice.device_type)" size="small">
                      {{ getDeviceTypeText(selectedDevice.device_type) }}
                    </NTag>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 设备状态 -->
            <NCard title="设备状态" class="info-card status-info">
              <template #header-extra>
                <TheIcon icon="material-symbols:timeline" :size="16" class="text-orange-500" />
              </template>
              <div class="status-content">
                <div class="status-main">
                  <div class="status-indicator">
                    <div
                      class="status-dot"
                      :class="getStatusClass(selectedDevice.device_status)"
                    ></div>
                    <div class="status-info">
                      <div class="status-time">{{ formatDate(new Date()) }}</div>
                      <NTag :type="getStatusTagType(selectedDevice.device_status)" size="medium">
                        {{ getStatusText(selectedDevice.device_status) }}
                      </NTag>
                      <div class="status-description">
                        {{ getDeviceStatusDescription(selectedDevice.device_status) }}
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 实时监控数据 -->
                <div class="status-metrics">
                  <div class="status-metric current">
                    <div class="metric-label">
                      <TheIcon icon="material-symbols:electric-bolt" :size="14" />
                      电流
                    </div>
                    <div class="metric-values">
                      <span class="preset">{{ selectedDevice.preset_current ?? '--' }}A</span>
                      <span class="separator">/</span>
                      <span class="actual">{{ selectedDevice.welding_current ?? '--' }}A</span>
                    </div>
                  </div>
                  <div class="status-metric voltage">
                    <div class="metric-label">
                      <TheIcon icon="material-symbols:flash-on" :size="14" />
                      电压
                    </div>
                    <div class="metric-values">
                      <span class="preset">{{ selectedDevice.preset_voltage ?? '--' }}V</span>
                      <span class="separator">/</span>
                      <span class="actual">{{ selectedDevice.welding_voltage ?? '--' }}V</span>
                    </div>
                  </div>
                </div>
                <div class="status-meta">
                  <div class="update-time">
                    <TheIcon icon="material-symbols:schedule" :size="14" />
                    <span
                      >数据更新：{{
                        selectedDevice.timestamp ? formatDate(selectedDevice.timestamp) : '暂无数据'
                      }}</span
                    >
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 工作信息 -->
            <NCard title="工作信息" class="info-card work-info">
              <template #header-extra>
                <TheIcon icon="material-symbols:work" :size="16" class="text-green-500" />
              </template>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:group" :size="14" />
                    所属班组
                  </div>
                  <div class="info-value">{{ selectedDevice.team_name || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:person" :size="14" />
                    操作员
                  </div>
                  <div class="info-value">{{ selectedDevice.operator || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:badge" :size="14" />
                    员工ID
                  </div>
                  <div class="info-value">{{ selectedDevice.staff_id || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:inventory-2" :size="14" />
                    工件ID
                  </div>
                  <div class="info-value">{{ selectedDevice.workpiece_id || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:lock" :size="14" />
                    锁定状态
                  </div>
                  <div class="info-value">
                    <NTag
                      :type="selectedDevice.lock_status === 1 ? 'error' : 'success'"
                      size="small"
                    >
                      <template #icon>
                        <TheIcon
                          :icon="
                            selectedDevice.lock_status === 1
                              ? 'material-symbols:lock'
                              : 'material-symbols:lock-open'
                          "
                        />
                      </template>
                      {{ selectedDevice.lock_status === 1 ? '已锁定' : '未锁定' }}
                    </NTag>
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 动态监控参数 -->
            <NCard
              v-if="getDeviceFields(selectedDevice.device_type).length > 0"
              title="监控参数"
              class="info-card process-info"
            >
              <template #header-extra>
                <TheIcon icon="material-symbols:settings" :size="16" class="text-purple-500" />
              </template>
              <div class="info-grid">
                <div
                  v-for="field in getDeviceFields(selectedDevice.device_type)"
                  :key="field.field_code"
                  class="info-item"
                  v-show="field.is_default_visible !== false"
                >
                  <div class="info-label">
                    <TheIcon
                      :icon="field.display_config?.icon || 'material-symbols:circle'"
                      :size="14"
                    />
                    {{ field.field_name }}
                  </div>
                  <div class="info-value">
                    {{ formatFieldValue(selectedDevice[field.field_code], field) }}
                  </div>
                </div>
              </div>
            </NCard>

            <!-- 降级显示：工艺参数 -->
            <NCard v-else title="工艺参数" class="info-card process-info">
              <template #header-extra>
                <TheIcon icon="material-symbols:settings" :size="16" class="text-purple-500" />
              </template>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:science" :size="14" />
                    材料
                  </div>
                  <div class="info-value">{{ selectedDevice.material || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:linear-scale" :size="14" />
                    焊丝直径
                  </div>
                  <div class="info-value">
                    {{ selectedDevice.wire_diameter ? `${selectedDevice.wire_diameter} mm` : '--' }}
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:air" :size="14" />
                    气体类型
                  </div>
                  <div class="info-value">{{ selectedDevice.gas_type || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:build" :size="14" />
                    焊接方法
                  </div>
                  <div class="info-value">{{ selectedDevice.weld_method || '--' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <TheIcon icon="material-symbols:tune" :size="14" />
                    焊接控制
                  </div>
                  <div class="info-value">{{ selectedDevice.weld_control || '--' }}</div>
                </div>
              </div>
            </NCard>
          </div>
        </div>
      </div>

      <template #action>
        <div class="modal-actions">
          <NButton quaternary @click="detailModalVisible = false">
            <template #icon>
              <TheIcon icon="material-symbols:close" />
            </template>
            关闭
          </NButton>
          <PermissionButton
            permission="GET /api/v2/devices/{device_id}"
            type="primary"
            @click="refreshDeviceDetail"
          >
            <template #icon>
              <TheIcon icon="material-symbols:refresh" />
            </template>
            刷新数据
          </PermissionButton>
        </div>
      </template>
    </NModal>

    <!-- 分页组件 - 服务端分页 -->
    <div v-if="!loading && pagination.itemCount > 0" class="pagination-container">
      <NPagination
        v-model:page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :item-count="pagination.itemCount"
        :page-sizes="pagination.pageSizes"
        :show-size-picker="pagination.showSizePicker"
        :show-quick-jumper="pagination.showQuickJumper"
        :prefix="pagination.prefix"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, h, watch, type Ref, type ComputedRef } from 'vue'
import {
  NButton,
  NCard,
  NSelect,
  NInput,
  NTag,
  NModal,
  NSpin,
  NDataTable,
  NPagination,
  NSkeleton,
  useMessage,
  type PaginationProps,
  type SelectOption,
} from 'naive-ui'
import { useRouter } from 'vue-router'
import { useUserStore, usePermissionStore } from '@/store'

import PermissionButton from '@/components/common/PermissionButton.vue'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import DeviceCard from '@/components/card/DeviceCard.vue'
import DeviceCardSkeleton from '@/components/card/DeviceCardSkeleton.vue'
import FastPermissionWrapper from '@/components/Permission/FastPermissionWrapper.vue'
import DynamicMonitoringData from '@/components/device/DynamicMonitoringData.vue'
import GroupedMonitoringData from '@/components/device/GroupedMonitoringData.vue'
import { useDeviceWebSocket } from '@/composables/useWebSocket'
import { useDeviceFieldStore } from '@/store/modules/device-field'
import {
  statusOptions,
  viewOptions,
  getDeviceTypeText,
  getDeviceTypeTagType,
  normalizeDeviceStatus,
  getStatusText,
  getStatusTagType,
  getDeviceCardClass,
  getStatusClass,
} from '@/utils/device-helpers'

import { formatDate } from '@/utils'
import api, { deviceApi } from '@/api'
import deviceV2Api from '@/api/device-v2'

defineOptions({ name: '设备实时监测' })

// ==================== 类型定义 ====================

interface DeviceInfo {
  id: string | number
  device_code: string
  device_name?: string
  device_type?: string
  status?: string
  location?: string
  realtime_data?: RealtimeData
  [key: string]: any
}

interface RealtimeData {
  current?: number
  voltage?: number
  power?: number
  temperature?: number
  [key: string]: any
}

interface DeviceType {
  type_code: string
  type_name: string
}

interface DeviceSummary {
  total?: number
  online?: number
  offline?: number
  alarm?: number
  [key: string]: any
}

interface PaginationInfo {
  page: number
  pageSize: number
  itemCount: number
  showSizePicker: boolean
  pageSizes: number[]
  showQuickJumper: boolean
  prefix: (info: { itemCount: number }) => string
  suffix: (info: { startIndex: number; endIndex: number }) => string
}

type ViewMode = 'card' | 'table'
type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'unknown'

// 消息提示
const message = useMessage()

// 路由
const router = useRouter()

// Store
const userStore = useUserStore()
const permissionStore = usePermissionStore()
const deviceFieldStore = useDeviceFieldStore()

// 响应式数据
const devices = ref<DeviceInfo[]>([])
const allDevices = ref<DeviceInfo[]>([]) // 存储所有设备数据
const loading = ref<boolean>(false)
const loadingProgress = ref<string>('') // 加载进度提示
// 设备字段配置缓存（用于动态参数展示）
const deviceFieldsCache = ref<Map<string, any[]>>(new Map())
const deviceRealtimeDataCache = ref<Map<string, any>>(new Map())
// 移除设备列表缓存相关变量 - 现在直接从WebSocket数据构建设备对象
const REALTIME_CACHE_DURATION = 2 * 60 * 1000 // 实时数据缓存2分钟
const realtimeDataCache = ref<Map<string, RealtimeData>>(new Map()) // 实时数据缓存
const realtimeCacheTimestamps = ref<Map<string, number>>(new Map()) // 实时数据缓存时间戳
const preloadedPages = ref<Set<number>>(new Set()) // 已预加载的页面
const realtimeDataLoading = ref<boolean>(false) // 实时数据加载状态

// Mock模式检测
const isMockMode = ref<boolean>(false) // 是否启用Mock模式
const checkMockMode = () => {
  // 检查window.__mockInterceptor是否存在并启用
  if ((window as any).__mockInterceptor) {
    const stats = (window as any).__mockInterceptor.getStats()
    isMockMode.value = stats.enabled
    console.log('🔍 Mock模式检测:', isMockMode.value ? '已启用' : '已禁用', stats)
    return isMockMode.value
  }
  return false
}
const filterType = ref<string>('welding') // 默认选择焊接设备类型
const filterStatus = ref<string | null>(null)
const filterLocation = ref<string>('')
const filterDeviceCode = ref<string>('') // 设备编码筛选
const filterDeviceName = ref<string>('') // 设备名称筛选
const searchKeyword = ref<string>('')
const detailModalVisible = ref<boolean>(false)
const selectedDevice = ref<DeviceInfo | null>(null)
const viewMode = ref<ViewMode>('card') // 视图模式：'card' 或 'table'
const deviceTypes = ref<DeviceType[]>([]) // 设备类型列表
const deviceSummary = ref<DeviceSummary>({}) // 设备状态汇总
const error = ref<Error | null>(null) // 错误信息
const connectionStatus = ref<ConnectionStatus>('unknown') // 连接状态
const retryCount = ref<number>(0) // 重试次数
const maxRetries = 3 // 最大重试次数
const deviceCount = ref<number>(0) // 当前筛选条件下的设备总数
const skeletonCount = ref<number>(20) // 骨架屏数量，默认20个

// 分页数据
const pagination = ref<PaginationInfo>({
  page: 1,
  pageSize: 20, // 每页显示20条记录
  itemCount: 0, // 总设备数
  showSizePicker: true,
  pageSizes: [20, 50, 100], // 服务端分页推荐的页面大小
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 个设备`,
  suffix: ({ startIndex, endIndex }) => `${startIndex + 1}-${endIndex + 1}`,
})

// 设备类型选项 - 只从API获取，不使用硬编码
const deviceTypeOptions = computed(() => {
  // 添加"全部"选项
  const allOption = { label: '全部设备类型', value: '' }
  const typeOptions = deviceTypes.value.map((type) => ({
    label: type.type_name,
    value: type.type_code,
  }))
  return [allOption, ...typeOptions]
})

// 过滤后的设备列表（用于分页计算）
const filteredAllDevices = computed(() => {
  return allDevices.value.filter((device) => {
    if (filterType.value && device.device_type !== filterType.value) return false
    if (filterStatus.value && normalizeDeviceStatus(device.device_status) !== filterStatus.value)
      return false
    if (filterLocation.value && !device.location?.includes(filterLocation.value)) return false
    if (filterDeviceCode.value && !device.id?.toString().includes(filterDeviceCode.value))
      return false
    if (filterDeviceName.value && !device.name?.includes(filterDeviceName.value)) return false
    return true
  })
})

// 当前页显示的设备列表
const filteredDevices = computed(() => {
  // ⚠️ 服务端分页模式：devices.value已经是当前页的数据，直接返回即可
  // 不需要再进行前端分页切片
  return devices.value
})

// 表格列配置
const tableColumns = [
  {
    title: '设备名称',
    key: 'name',
    width: 150,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '设备ID',
    key: 'id',
    width: 120,
  },
  {
    title: '设备类型',
    key: 'device_type',
    width: 120,
    render(row) {
      return h(
        NTag,
        {
          type: getDeviceTypeTagType(row.device_type),
          size: 'small',
        },
        {
          default: () => getDeviceTypeText(row.device_type),
        }
      )
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(
        NTag,
        {
          type: getStatusTagType(row.device_status),
          size: 'small',
        },
        {
          default: () => getStatusText(row.device_status),
        }
      )
    },
  },
  {
    title: '预设电流',
    key: 'preset_current',
    width: 100,
    render(row) {
      return `${row.preset_current ?? '--'} A`
    },
  },
  {
    title: '预设电压',
    key: 'preset_voltage',
    width: 100,
    render(row) {
      return `${row.preset_voltage ?? '--'} V`
    },
  },
  {
    title: '焊接电流',
    key: 'welding_current',
    width: 100,
    render(row) {
      return `${row.welding_current ?? '--'} A`
    },
  },
  {
    title: '焊接电压',
    key: 'welding_voltage',
    width: 100,
    render(row) {
      return `${row.welding_voltage ?? '--'} V`
    },
  },
  {
    title: '车间班组',
    key: 'team_name',
    width: 120,
    ellipsis: {
      tooltip: true,
    },
    render(row) {
      return row.team_name || '--'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right',
    render(row) {
      return h(
        PermissionButton,
        {
          resource: 'device',
          action: 'read',
          size: 'small',
          type: 'primary',
          secondary: true,
          onClick: (e) => {
            e.stopPropagation()
            showDeviceDetails(row)
          },
        },
        {
          default: () => '查看详情',
        }
      )
    },
  },
]

// 计算当前页设备编码列表（用于WebSocket订阅）
const currentPageDeviceCodes = computed(() => {
  // 确保设备编码始终为字符串类型，并过滤掉无效值
  return devices.value
    .map((device) => {
      const deviceCode = device.id || device.device_code
      return deviceCode ? String(deviceCode) : null
    })
    .filter((code) => code !== null)
})

// 缓存WebSocket数据，用于设备列表加载完成后处理
let cachedWebSocketData = null

// 处理WebSocket数据的核心逻辑 - 重构版本：直接从实时数据构建设备对象
function processWebSocketData(data) {
  // 调试：检查WebSocket数据的字段结构
  if (data.length > 0) {
    console.log('WebSocket数据样本:', data[0])
    console.log('WebSocket数据字段:', Object.keys(data[0]))
  }

  // 直接从WebSocket数据构建设备对象数组
  let processedCount = 0
  const deviceList = data
    .map((item) => {
      // 只输出前3个设备的调试信息
      if (processedCount < 3) {
        console.log('WebSocket原始数据项:', item)
        console.log('设备名称相关字段:', {
          device_name: item.device_name,
          name: item.name,
          device_code: item.device_code,
        })
        console.log('关键字段检查:', {
          device_code: item.device_code,
          preset_current: item.preset_current,
          preset_voltage: item.preset_voltage,
          weld_current: item.weld_current,
          weld_voltage: item.weld_voltage,
          device_status: item.device_status,
          team_name: item.team_name,
          operator: item.operator,
          material: item.material,
        })
      }

      if (!item.device_code) {
        console.warn('WebSocket数据项缺少device_code字段:', item)
        return null
      }

      // 从实时数据构建完整的设备对象
      // 注意：后端返回的字段是 type_code，不是 device_type
      const deviceType = item.type_code || item.device_type || filterType.value || 'welding'
      
      const device = {
        // 保留所有原始字段（包括动态字段）
        ...item,
        // 展平realtime_data中的字段，以便GroupedMonitoringData可以直接访问
        ...(item.realtime_data || {}),
        
        // 基础标识信息
        id: item.device_code, // 使用设备编码作为主要标识符
        name: item.device_name || item.name || '', // 优先使用device_name，其次使用name
        device_type: deviceType, // 设备类型（统一使用device_type字段）
        type_code: deviceType, // 保留type_code字段以兼容
        ip_address: item.ip_address || '未知', // IP地址
        location: item.location || item.team_name || '未设置', // 位置信息

        // 动态字段直接映射
        // 我们不再硬编码映射特定字段（如welding_current），而是依赖GroupedMonitoringData组件
        // 根据设备类型的字段配置（DeviceField）来动态读取数据
        
        // 时间戳
        timestamp: item.ts,
        created_at: item.ts || new Date().toISOString(),
        updated_at: item.ts || new Date().toISOString(),
      }
      
      // 调试：输出设备类型信息（只输出前3个）
      if (processedCount < 3) {
        console.log('设备类型设置:', {
          device_code: device.id,
          from_item_type_code: item.type_code,
          from_item_device_type: item.device_type,
          from_filterType: filterType.value,
          final_device_type: device.device_type
        })
      }

      // 设置设备状态
      device.status = getDeviceStatus(device)
      if (!device.device_status) {
        device.device_status = device.status
      }

      processedCount++
      return device
    })
    .filter((device) => device !== null) // 过滤掉无效的设备对象

  // 调试日志：打印第一台设备的实时数据，确认是否在更新
  if (deviceList.length > 0) {
    const first = deviceList[0]
    console.log(`[${new Date().toLocaleTimeString()}] WebSocket数据更新 (共${deviceList.length}条):`, {
      device_code: first.id,
      timestamp: first.timestamp,
      device_type: first.device_type,
      // 动态打印所有字段，不局限于硬编码字段
      data_preview: Object.keys(first).filter(k => !['id', 'name', 'timestamp', 'created_at', 'updated_at'].includes(k)).slice(0, 10)
    })
  }

  // 更新allDevices数组
  allDevices.value = deviceList

  // 调试：检查构建的设备数据
  if (allDevices.value.length > 0) {
    const sampleDevice = allDevices.value[0]
    console.log('构建的设备样本:', sampleDevice)
    console.log('设备样本的基本信息:', {
      id: sampleDevice.id,
      name: sampleDevice.name,
      device_type: sampleDevice.device_type,
      location: sampleDevice.location,
    })
    console.log('设备样本的实时数据字段:', {
      preset_current: sampleDevice.preset_current,
      welding_current: sampleDevice.welding_current,
      device_status: sampleDevice.device_status,
      status: sampleDevice.status,
      team_name: sampleDevice.team_name,
      operator: sampleDevice.operator,
      material: sampleDevice.material,
    })
  }

  // 重新应用筛选和分页，更新devices.value
  applyFilters()

  // 停止加载状态
  loading.value = false
  realtimeDataLoading.value = false
  loadingProgress.value = ''

  // 调试：检查当前页显示的设备数据
  console.log('filteredDevices数量:', filteredDevices.value.length)
  if (filteredDevices.value.length > 0) {
    const currentPageSample = filteredDevices.value[0]
    console.log('当前页设备样本(filteredDevices):', currentPageSample)
    console.log('当前页设备完整信息:', {
      name: currentPageSample.name,
      id: currentPageSample.id,
      device_type: currentPageSample.device_type,
      location: currentPageSample.location,
      preset_current: currentPageSample.preset_current,
      welding_current: currentPageSample.welding_current,
      device_status: currentPageSample.device_status,
      status: currentPageSample.status,
      team_name: currentPageSample.team_name,
      operator: currentPageSample.operator,
    })
  } else {
    console.warn('filteredDevices为空，检查筛选逻辑')
  }
}

// WebSocket连接
const {
  isConnected,
  isConnecting,
  error: wsError,
  deviceData,
  deviceSummary: wsSummary,
  connect,
  disconnect,
  reconnect,
  subscribeDeviceType,
  unsubscribeDeviceType,
  requestRefresh,
} = useDeviceWebSocket({
  deviceType: filterType, // 传递设备类型筛选
  page: computed(() => pagination.value.page), // 传递当前页码
  pageSize: computed(() => pagination.value.pageSize), // 传递每页数量
  onDataUpdate: (data) => {
    console.log('WebSocket数据更新:', data)
    
    // 处理分页数据格式
    let items = []
    let total = 0
    let page = 1
    let pageSize = 20
    
    if (data && typeof data === 'object') {
      // 格式1: { items: [...], total: 7203, page: 1, page_size: 20 } - 服务端分页格式
      if (data.items && Array.isArray(data.items)) {
        items = data.items
        total = data.total || 0
        page = data.page || 1
        pageSize = data.page_size || 20
        console.log('✅ 检测到服务端分页格式:', { total, page, pageSize, itemsCount: items.length })
      }
      // 格式2: 直接是数组（旧格式）
      else if (Array.isArray(data)) {
        items = data
        total = data.length
        console.log('⚠️  检测到旧格式（数组）:', { itemsCount: items.length })
      }
      // 格式3: 其他对象格式
      else {
        console.warn('⚠️  未知的数据格式:', data)
        items = []
        total = 0
      }
    } else if (Array.isArray(data)) {
      items = data
      total = data.length
      console.log('⚠️  检测到旧格式（数组）:', { itemsCount: items.length })
    }
    
    console.log('📊 解析后的分页数据:', { 
      itemsCount: items.length, 
      total, 
      page, 
      pageSize,
      totalPages: total > 0 ? Math.ceil(total / pageSize) : 0
    })
    
    // 更新总设备数和分页信息
    if (total > 0) {
      pagination.value.itemCount = total
      console.log(`✅ 更新分页信息: 共${total}个设备，当前第${page}页，每页${pageSize}个`)
    } else {
      console.warn('⚠️  total为0，分页控件可能不会显示')
    }

    // 处理设备数据
    if (Array.isArray(items) && items.length > 0) {
      processWebSocketData(items)
    } else {
      console.warn('WebSocket数据格式不正确或为空:', data)
      // 如果没有数据，也要停止加载状态
      loading.value = false
      realtimeDataLoading.value = false
      loadingProgress.value = ''
    }
  },
  onError: (err) => {
    console.error('WebSocket错误:', err)
    message.error('实时数据连接异常，请检查网络连接')
  },
  onOpen: () => {
    console.log('实时数据连接已建立')
    message.success('实时数据连接已建立')
  },
})

// 设备类型缓存
let deviceTypesCache = null
let deviceTypesCacheTime = 0
const DEVICE_TYPES_CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 获取设备数量统计
 */
async function getDeviceCount(typeCode: string) {
  try {
    console.log(`获取设备类型 ${typeCode} 的设备数量...`)
    
    // 调用设备列表API，只获取总数，不获取详细数据
    const response = await deviceV2Api.devices.list({
      device_type: typeCode,
      page: 1,
      page_size: 1, // 只获取1条数据，减少数据传输
    })
    
    if (response && response.data) {
      const total = response.data.total || 0
      console.log(`设备类型 ${typeCode} 的设备总数: ${total}`)
      return total
    }
    
    return 0
  } catch (error) {
    console.error('获取设备数量失败:', error)
    return 0
  }
}

/**
 * 更新骨架屏数量
 */
async function updateSkeletonCount() {
  const typeCode = filterType.value || 'welding'
  const count = await getDeviceCount(typeCode)
  
  deviceCount.value = count
  
  // 计算当前页应该显示的骨架屏数量
  const currentPageSize = pagination.value.pageSize
  skeletonCount.value = Math.min(count, currentPageSize)
  
  console.log(`更新骨架屏数量: ${skeletonCount.value} (总设备数: ${count}, 每页: ${currentPageSize})`)
}

/**
 * 加载设备类型列表 - 性能优化版本
 */
async function loadDeviceTypes() {
  const startTime = performance.now()

  try {
    // 检查缓存
    const now = Date.now()
    if (deviceTypesCache && now - deviceTypesCacheTime < DEVICE_TYPES_CACHE_DURATION) {
      console.log('使用缓存的设备类型数据')
      deviceTypes.value = deviceTypesCache
      return
    }

    console.log('开始加载设备类型...')

    // 移除不必要的延迟，直接调用API
    // 调用API（使用Promise.race实现超时控制）
    // 不包含统计数据以提高响应速度
    const apiPromise = deviceV2Api.deviceTypes.list({ include_counts: false })
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error('API调用超时'))
      }, 15000) // 增加超时时间到15秒，避免网络延迟导致的超时
    })

    const response = await Promise.race([apiPromise, timeoutPromise]) as any

    if (response && response.data && Array.isArray(response.data)) {
      deviceTypes.value = response.data
      // 更新缓存
      deviceTypesCache = response.data
      deviceTypesCacheTime = now

      const loadTime = performance.now() - startTime
      console.log(
        `设备类型加载成功，耗时: ${loadTime.toFixed(2)}ms，获取到 ${
          response.data.length
        } 个设备类型`
      )
    } else {
      throw new Error('API返回数据格式不正确')
    }
  } catch (err) {
    const loadTime = performance.now() - startTime
    console.error(`设备类型加载失败，耗时: ${loadTime.toFixed(2)}ms`, err)

    // 提供更详细的错误信息
    let errorMsg = '获取设备类型失败'
    if (err.message === 'API调用超时') {
      errorMsg = '设备类型加载超时，正在使用默认配置'
      console.warn('设备类型API调用超时，可能存在网络问题或后端性能问题')
      message.info('设备类型加载较慢，已切换到默认配置')
    } else if (err.code === 'ECONNABORTED') {
      errorMsg = '网络连接超时，使用默认配置'
      message.warning(errorMsg)
    } else if (err.message) {
      errorMsg = `获取设备类型失败: ${err.message}`
      message.error(errorMsg)
    } else {
      message.warning(errorMsg)
    }

    // 使用默认类型选项作为降级处理
    const defaultTypes = [
      { type_code: 'welding', type_name: '焊接设备' },
      { type_code: 'cutting', type_name: '切割设备' },
      { type_code: 'assembly', type_name: '装配设备' },
    ]

    deviceTypes.value = defaultTypes

    // 缓存默认类型，避免重复失败
    if (!deviceTypesCache) {
      deviceTypesCache = defaultTypes
      deviceTypesCacheTime = Date.now()
    }
  }
}

/**
 * 检查网络连接状态
 */
async function checkNetworkConnection() {
  try {
    // 尝试访问设备类型接口作为健康检查
    const response = await deviceV2Api.deviceTypes.list()
    return response && response.data
  } catch (error) {
    console.warn('网络连接检查失败:', error)
    return false
  }
}

// 移除设备列表缓存相关函数 - 现在直接从WebSocket数据构建设备对象

/**
 * 清除实时数据缓存
 */
function clearRealtimeCache() {
  realtimeDataCache.value.clear()
  realtimeCacheTimestamps.value.clear()
  preloadedPages.value.clear()
  console.log('实时数据缓存已清除')
}

/**
 * 清理过期的实时数据缓存
 */
function cleanExpiredRealtimeCache() {
  const now = Date.now()
  const expiredKeys = []

  realtimeCacheTimestamps.value.forEach((timestamp, key) => {
    if (now - timestamp > REALTIME_CACHE_DURATION) {
      expiredKeys.push(key)
    }
  })

  expiredKeys.forEach((key) => {
    realtimeDataCache.value.delete(key)
    realtimeCacheTimestamps.value.delete(key)
  })

  if (expiredKeys.length > 0) {
    console.log(`清理了 ${expiredKeys.length} 个过期的实时数据缓存`)
  }
}

/**
 * 预加载下一页数据
 */
async function preloadNextPageData() {
  const currentPage = pagination.value.page
  const nextPage = currentPage + 1
  const totalPages = Math.ceil(pagination.value.itemCount / pagination.value.pageSize)

  // 如果下一页不存在或已预加载，则跳过
  if (nextPage > totalPages || preloadedPages.value.has(nextPage)) {
    return
  }

  try {
    console.log(`预加载第${nextPage}页数据`)

    // 获取下一页的设备列表
    const filteredDevices = getFilteredDevices()
    const startIndex = (nextPage - 1) * pagination.value.pageSize
    const endIndex = startIndex + pagination.value.pageSize
    const nextPageDevices = filteredDevices.slice(startIndex, endIndex)

    if (nextPageDevices.length === 0) {
      return
    }

    // 获取设备编码
    const deviceCodes = nextPageDevices
      .map((device) => {
        const deviceCode = device.id || device.device_code
        return deviceCode ? String(deviceCode) : null
      })
      .filter((code) => code !== null)

    // 预加载实时数据
    const typeCode = filterType.value || 'welding'
    const batchSize = 30
    const batches = []
    for (let i = 0; i < deviceCodes.length; i += batchSize) {
      batches.push(deviceCodes.slice(i, i + batchSize))
    }

    const batchPromises = batches.map(async (batch) => {
      const params = {
        type_code: typeCode,
        device_codes: batch,
      }
      return await deviceV2Api.devices.getRealtimeMonitoring(params)
    })

    const batchResponses = await Promise.all(batchPromises)

    // 缓存预加载的数据
    const cacheTime = Date.now()
    for (const response of batchResponses) {
      if (response.data && Array.isArray(response.data)) {
        response.data.forEach((item) => {
          if (item.device_code) {
            realtimeDataCache.value.set(item.device_code, item)
            realtimeCacheTimestamps.value.set(item.device_code, cacheTime)
          }
        })
      }
    }

    // 标记该页已预加载
    preloadedPages.value.add(nextPage)
    console.log(`第${nextPage}页数据预加载完成`)
  } catch (error) {
    console.warn('预加载下一页数据失败:', error)
  }
}

// 移除loadDeviceList函数 - 现在直接从WebSocket数据构建设备对象

/**
 * 通过HTTP API加载设备实时数据 (Mock模式专用)
 * 当Mock模式启用时，WebSocket无法工作，需要使用HTTP API
 */
async function loadDevicesByHttp() {
  console.log('📡 使用HTTP API加载设备实时数据 (Mock模式)')
  
  try {
    const params = {
      device_type: filterType.value,
    }
    
    const response = await deviceV2Api.devices.getRealtimeMonitoring(params)
    console.log('📦 HTTP API响应:', response)
    
    if (response && response.data && response.data.items) {
      const items = response.data.items
      console.log(`✅ 获取到 ${items.length} 台设备的实时数据`)
      
      // 转换数据格式为页面所需的DeviceInfo格式
      const deviceInfoList = items.map((item: any) => ({
        device_id: item.device_id,
        device_code: item.device_code,
        device_name: item.device_name,
        device_type: item.device_type,
        device_type_name: item.device_type_name || item.device_type,
        install_location: item.install_location,
        status: item.status,
        online: item.online,
        realtime_data: item.realtime_data || {},
        ...(item.realtime_data || {}), // 展平realtime_data中的字段
        health_status: item.health_status,
        health_score: item.health_score,
        last_maintenance: item.last_maintenance,
        next_maintenance: item.next_maintenance,
        alarms: item.alarms || [],
        timestamp: item.timestamp || new Date().toISOString()
      }))
      
      // 更新设备列表
      allDevices.value = deviceInfoList
      applyFilters()
      
      return deviceInfoList
    } else {
      console.warn('HTTP API返回数据格式不正确:', response)
      allDevices.value = []
      applyFilters()
      return []
    }
  } catch (error) {
    console.error('通过HTTP API加载设备数据失败:', error)
    message.error('加载设备数据失败，请检查Mock规则是否正确配置')
    allDevices.value = []
    applyFilters()
    return []
  }
}

/**
 * 加载设备实时数据 (已废弃)
 * 现在设备数据完全通过WebSocket实时推送，此函数仅保留用于向后兼容
 */
async function loadDevices() {
  console.warn('loadDevices函数已废弃，现在完全依赖WebSocket数据构建设备列表')

  // 如果没有设备数据，应用筛选显示空结果
  if (allDevices.value.length === 0) {
    applyFilters()
  }

  loading.value = false
}

/**
 * 获取设备类型的字段配置（用于动态参数展示）
 */
function getDeviceFields(deviceType: string) {
  if (!deviceType) return []
  
  // 从缓存获取
  const cached = deviceFieldsCache.value.get(deviceType)
  if (cached) {
    return cached
  }
  
  // 如果缓存中没有，从 store 获取
  deviceFieldStore.getMonitoringFields(deviceType).then((fields) => {
    deviceFieldsCache.value.set(deviceType, fields)
  }).catch((error) => {
    console.error(`获取设备类型 ${deviceType} 的字段配置失败:`, error)
  })
  
  return []
}

/**
 * 格式化字段值
 */
function formatFieldValue(value: any, field: any) {
  if (value === undefined || value === null || value === '') return '--'
  
  let formattedValue = value
  if (field.field_type === 'float') {
    const num = Number(value)
    if (!isNaN(num)) {
      formattedValue = num.toFixed(2)
    }
  } else if (field.field_type === 'boolean') {
    formattedValue = value ? '是' : '否'
  }
  
  if (field.unit) {
    return `${formattedValue} ${field.unit}`
  }
  
  return String(formattedValue)
}

/**
 * 获取设备的实时数据（用于动态参数展示）
 */
function getDeviceRealtimeData(device: any) {
  if (!device) return {}
  
  // 从设备对象中提取实时数据
  // 这里返回整个设备对象，让 DynamicMonitoringData 组件根据字段配置提取需要的数据
  return device
}

/**
 * 根据设备数据判断设备状态
 */
function getDeviceStatus(deviceData) {
  // 根据实际业务逻辑判断设备状态
  if (!deviceData.timestamp && !deviceData.ts) {
    return 'inactive'
  }

  const timestamp = deviceData.timestamp || deviceData.ts
  const lastUpdate = new Date(timestamp)
  const now = new Date()
  const diffMinutes = (now.getTime() - lastUpdate.getTime()) / (1000 * 60)

  // 如果超过5分钟没有数据更新，认为离线
  if (diffMinutes > 5) {
    return 'inactive'
  }

  // 根据TDengine中的device_status字段判断设备状态
  if (deviceData.device_status) {
    const status = deviceData.device_status.toLowerCase()
    switch (status) {
      case '焊接':
      case 'welding':
      case '待机':
      case 'standby':
        return 'active'
      case '报警':
      case 'alarm':
      case '故障':
      case 'fault':
        return 'fault'
      case '关机':
      case 'shutdown':
      case '离线':
      case 'offline':
        return 'inactive'
      case '维护':
      case 'maintenance':
        return 'maintenance'
      default:
        return 'active'
    }
  }

  // 根据设备数据判断是否故障（兼容旧逻辑）
  if (deviceData.alarm_status || deviceData.error_code) {
    return 'fault'
  }

  // 检查是否处于维护模式（兼容旧逻辑）
  if (deviceData.maintenance_mode) {
    return 'maintenance'
  }

  return 'active'
}

/**
 * 生成模拟设备数据
 */
function generateMockDevices() {
  return [
    {
      id: 'WD001',
      name: '焊接机器人-01',
      ip_address: '192.168.1.101',
      device_type: 'welding',
      status: 'active',
      device_status: 'active',
      location: '生产线A-工位1',
      preset_current: '275.0',
      preset_voltage: '26.5',
      welding_current: '273.2',
      welding_voltage: '26.1',
      created_at: new Date().toISOString(),
    },
    {
      id: 'WD002',
      name: '焊接机器人-02',
      ip_address: '192.168.1.102',
      device_type: 'welding',
      status: 'active',
      device_status: 'active',
      location: '生产线A-工位2',
      preset_current: '280.0',
      preset_voltage: '27.0',
      welding_current: '278.5',
      welding_voltage: '26.8',
      created_at: new Date().toISOString(),
    },
    {
      id: 'WD003',
      name: '焊接工作站-01',
      ip_address: '192.168.1.103',
      device_type: 'welding',
      status: 'maintenance',
      device_status: 'maintenance',
      location: '生产线B-工位1',
      preset_current: '270.0',
      preset_voltage: '26.0',
      welding_current: '0.0',
      welding_voltage: '0.0',
      created_at: new Date().toISOString(),
    },
  ]
}
/**
 * 刷新数据
 */
function refreshData(forceReload = false) {
  console.log('刷新数据，forceReload:', forceReload)
  
  // 设置加载状态
  loading.value = true
  realtimeDataLoading.value = true
  loadingProgress.value = '正在刷新数据...'
  
  // 如果强制重新加载，清除缓存
  if (forceReload) {
    clearRealtimeCache()
  }

  // 清空当前设备列表
  allDevices.value = []
  devices.value = []
  
  // 重新建立WebSocket连接以获取最新数据
  console.log('重新建立WebSocket连接以刷新数据')
  disconnect()
  
  setTimeout(() => {
    reconnect()
    
    // 设置超时，如果10秒内没有收到数据，停止加载状态
    setTimeout(() => {
      if (allDevices.value.length === 0) {
        loading.value = false
        realtimeDataLoading.value = false
        loadingProgress.value = ''
        message.warning('刷新数据超时，请检查WebSocket连接')
      }
    }, 10000)
  }, 100)
}

/**
 * 获取筛选后的设备列表
 */
function getFilteredDevices() {
  let filtered = [...allDevices.value]

  // 调试：输出筛选前的设备信息
  console.log('筛选前设备总数:', filtered.length)
  if (filtered.length > 0) {
    console.log('第一个设备的device_type:', filtered[0].device_type)
    console.log('当前filterType.value:', filterType.value)
  }

  // 按设备类型筛选
  if (filterType.value) {
    const beforeFilter = filtered.length
    filtered = filtered.filter((device) => {
      const match = device.device_type === filterType.value
      if (!match && beforeFilter <= 5) {
        // 只在设备数量少时输出详细信息，避免日志过多
        console.log('设备类型不匹配:', {
          device_code: device.device_code || device.id,
          device_type: device.device_type,
          expected: filterType.value
        })
      }
      return match
    })
    console.log(`设备类型筛选: ${beforeFilter} -> ${filtered.length}`)
  }

  // 按设备状态筛选
  if (filterStatus.value) {
    filtered = filtered.filter((device) => {
      const normalizedStatus = normalizeDeviceStatus(device.device_status)
      return normalizedStatus === filterStatus.value
    })
  }

  // 按设备位置筛选
  if (filterLocation.value) {
    filtered = filtered.filter(
      (device) => device.location && device.location.includes(filterLocation.value)
    )
  }

  // 按设备编码筛选
  if (filterDeviceCode.value) {
    filtered = filtered.filter(
      (device) => device.id && device.id.toString().includes(filterDeviceCode.value)
    )
  }

  // 按设备名称筛选
  if (filterDeviceName.value) {
    filtered = filtered.filter(
      (device) => device.name && device.name.includes(filterDeviceName.value)
    )
  }

  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(
      (device) =>
        device.name.toLowerCase().includes(keyword) ||
        String(device.id).toLowerCase().includes(keyword) ||
        (device.location && device.location.toLowerCase().includes(keyword))
    )
  }

  return filtered
}

/**
 * 应用筛选条件
 */
function applyFilters() {
  const filtered = getFilteredDevices()

  // ⚠️ 服务端分页模式：后端已经返回了当前页的数据，不需要再进行前端分页切片
  // 直接使用筛选后的结果作为当前页数据
  devices.value = filtered
  
  // ⚠️ 注意：在服务端分页模式下，不要覆盖itemCount
  // itemCount应该由WebSocket返回的total字段设置，而不是前端筛选后的数量
  // pagination.value.itemCount = filtered.length  // ❌ 不要覆盖

  console.log('筛选结果:', filtered.length, '个设备，当前页:', devices.value.length, '个设备')
  console.log('总设备数(itemCount):', pagination.value.itemCount, '（由服务端返回，不应被覆盖）')
  console.log('当前页码:', pagination.value.page, '每页数量:', pagination.value.pageSize)
}

/**
 * 处理筛选条件变化
 */
function handleFilterChange() {
  // 筛选条件变化时重置到第一页
  pagination.value.page = 1

  // 基于内存数据进行筛选和分页
  applyFilters()
}

// 监听设备类型变化，重新订阅WebSocket数据
watch(filterType, async (newType, oldType) => {
  if (newType !== oldType) {
    console.log('设备类型变化:', { from: oldType, to: newType })

    // 重置到第一页
    pagination.value.page = 1
    pagination.value.itemCount = 0

    // 设置加载状态，显示骨架屏
    loading.value = true
    realtimeDataLoading.value = true
    loadingProgress.value = '正在切换设备类型...'

    // 更新骨架屏数量
    await updateSkeletonCount()

    // 检查Mock模式
    const mockEnabled = checkMockMode()
    
    if (mockEnabled) {
      // Mock模式：使用HTTP API重新加载数据
      console.log('🎭 Mock模式：重新加载设备数据')
      loadDevicesByHttp()
    } else {
      // WebSocket模式：重新建立连接以切换设备类型
      console.log('🔄 重新建立WebSocket连接，切换设备类型:', newType || 'welding')
      
      // 清空当前设备数据，避免显示旧数据
      allDevices.value = []
      devices.value = []
      
      // 断开旧连接
      disconnect()
      
      // 等待一小段时间确保连接完全断开
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 重新建立连接（useDeviceWebSocket会使用新的filterType和page值）
      reconnect()
      
      // 设置超时，如果10秒内没有收到数据，停止加载状态
      setTimeout(() => {
        if (allDevices.value.length === 0) {
          loading.value = false
          realtimeDataLoading.value = false
          loadingProgress.value = ''
          console.warn('切换设备类型后未收到数据')
        }
      }, 10000)
    }
  }
})

/**
 * 重置筛选条件
 */
function resetFilters() {
  filterType.value = '' // 重置为显示所有设备类型
  filterStatus.value = ''
  filterLocation.value = ''
  filterDeviceCode.value = ''
  filterDeviceName.value = ''
  searchKeyword.value = ''
  pagination.value.page = 1

  // 重置后重新应用筛选
  applyFilters()
}

/**
 * 手动重试连接 (已废弃)
 * 现在完全依赖WebSocket连接，无需手动重试API连接
 */
function retryConnection() {
  console.warn('retryConnection函数已废弃，现在完全依赖WebSocket连接')
  retryCount.value = 0
  // WebSocket会自动重连，无需手动操作
}

/**
 * 权限相关处理
 */
function handleContactAdmin() {
  message.info('请联系系统管理员获取设备监测数据查看权限')
}

/**
 * 获取WebSocket连接状态文本
 */
function getWebSocketStatusText() {
  if (isConnected.value) {
    return 'WebSocket连接正常 - 实时数据推送中'
  } else if (isConnecting.value) {
    return 'WebSocket连接中... - 正在建立实时数据连接'
  } else {
    return 'WebSocket连接断开 - 无法接收实时数据'
  }
}

/**
 * 获取API连接状态文本
 */
function getConnectionStatusText() {
  switch (connectionStatus.value) {
    case 'connected':
      return 'API连接正常 - 后端服务可用'
    case 'disconnected':
      return 'API连接失败 - 后端服务不可用'
    case 'connecting':
      return 'API连接中... - 正在连接后端服务'
    default:
      return 'API连接状态未知'
  }
}

/**
 * 获取连接状态颜色
 */
function getConnectionStatusColor() {
  switch (connectionStatus.value) {
    case 'connected':
      return '#52c41a'
    case 'disconnected':
      return '#ff4d4f'
    default:
      return '#faad14'
  }
}

/**
 * 分页处理函数 - 服务端分页
 */
function handlePageChange(page) {
  console.log('🔄 [分页] 切换到第', page, '页')
  console.log('🔄 [分页] 当前pagination.value.page:', pagination.value.page)
  console.log('🔄 [分页] 当前pagination.value.pageSize:', pagination.value.pageSize)
  
  pagination.value.page = page
  
  console.log('🔄 [分页] 更新后pagination.value.page:', pagination.value.page)
  
  // 设置加载状态
  loading.value = true
  realtimeDataLoading.value = true
  loadingProgress.value = `正在加载第${page}页...`
  
  // 清空当前设备列表
  allDevices.value = []
  devices.value = []
  
  console.log('🔄 [分页] 准备断开WebSocket连接')
  
  // 重新连接WebSocket获取新页数据
  disconnect()
  
  setTimeout(() => {
    console.log('🔄 [分页] 准备重新连接WebSocket，page=', pagination.value.page, ', pageSize=', pagination.value.pageSize)
    reconnect()
    
    // 设置超时保护
    setTimeout(() => {
      if (allDevices.value.length === 0) {
        console.error('❌ [分页] 加载数据超时，allDevices为空')
        loading.value = false
        realtimeDataLoading.value = false
        loadingProgress.value = ''
        message.warning('加载数据超时，请检查网络连接')
      } else {
        console.log('✅ [分页] 数据加载成功，allDevices数量:', allDevices.value.length)
      }
    }, 10000)
  }, 100)
}

function handlePageSizeChange(pageSize) {
  console.log('每页数量改为', pageSize)
  
  pagination.value.pageSize = pageSize
  pagination.value.page = 1 // 重置到第一页
  
  // 重新加载数据
  handlePageChange(1)
}

/**
 * 显示设备详情
 */
function showDeviceDetails(device) {
  selectedDevice.value = device
  detailModalVisible.value = true
}

/**
 * 刷新设备详情数据
 */
function refreshDeviceDetail() {
  if (selectedDevice.value) {
    // 从当前设备列表中找到最新的设备数据
    const updatedDevice = allDevices.value.find((device) => device.id === selectedDevice.value.id)
    if (updatedDevice) {
      selectedDevice.value = updatedDevice
      message.success('设备详情已刷新')
    } else {
      message.warning('未找到设备最新数据')
    }
  }
}

/**
 * 获取设备状态描述
 */
function getDeviceStatusDescription(status) {
  const normalized = normalizeDeviceStatus(status)
  const descriptions = {
    welding: '设备正在运行中',
    standby: '设备处于待机状态',
    fault: '设备出现故障或报警',
    inactive: '设备已关机或离线',
  }
  return descriptions[normalized] || '设备状态未知'
}

/**
 * 显示设备历史数据
 * 跳转到历史数据查询页面，携带设备编码和设备名称参数
 */
async function showDeviceCharts(device) {
  console.log('showDeviceCharts 被调用，设备数据:', device)

  // 确保使用正确的设备编码和设备名称字段
  // 优先使用 device_code 作为业务主键，id 作为备选
  const deviceCode = device.device_code || device.id
  const deviceName = device.device_name || device.name || ''
  const deviceTypeCode = device.device_type_code || device.type_code || device.device_type || filterType.value

  console.log('提取的设备信息:', { deviceCode, deviceName, deviceTypeCode })

  if (!deviceCode) {
    console.error('设备编码不存在:', device)
    message.error('设备编码不存在，无法查看历史数据')
    return
  }

  // 准备跳转参数：携带设备编码、设备名称和设备类型代码
  // 不传递时间参数，让历史页面根据系统配置自动计算默认时间范围
  const routeParams = {
    path: '/device-monitor/history',
    query: {
      device_code: deviceCode,
      device_name: deviceName,
      device_type_code: deviceTypeCode,
    },
  }

  console.log('准备跳转到历史数据查询页面，路由参数:', routeParams)

  try {
    // 检查目标路由是否存在
    const targetRoute = router.resolve({ path: '/device-monitor/history' })
    
    // 如果路由解析为NotFound，使用name方式跳转
    if (targetRoute.name === 'NotFound') {
      console.log('使用路由名称方式跳转')
      await router.push({
        name: 'DeviceHistory',
        query: routeParams.query,
      })
    } else {
      console.log('使用路径方式跳转')
      await router.push(routeParams)
    }
    console.log('路由跳转成功')
  } catch (error) {
    console.error('路由跳转失败:', error)
    message.error('跳转到历史数据查询页面失败')
  }
}

// 生命周期 - 性能优化版本
onMounted(async () => {
  loading.value = true
  realtimeDataLoading.value = true

  try {
    // 记录性能时间戳
    const startTime = performance.now()

    // 检查Mock模式
    const mockEnabled = checkMockMode()
    
    if (mockEnabled) {
      console.log('🎭 检测到Mock模式已启用，将使用HTTP API替代WebSocket')
      message.info('Mock模式已启用，正在使用模拟数据', { duration: 3000 })
    }

    // 并行执行：设备类型加载和WebSocket连接
    loadingProgress.value = '正在初始化...'

    // 如果不是Mock模式，立即开始WebSocket连接
    if (!mockEnabled) {
      const defaultDeviceType = 'welding'
      console.log('提前订阅默认设备类型WebSocket数据:', defaultDeviceType)
      subscribeDeviceType(defaultDeviceType)
    }

    // 并行加载设备类型
    const deviceTypesPromise = loadDeviceTypes().then(async () => {
      // 设备类型加载完成后，更新筛选类型
      if (!filterType.value && deviceTypes.value.length > 0) {
        const weldingType = deviceTypes.value.find((type) => type.type_code === 'welding')
        if (weldingType) {
          filterType.value = 'welding'
          console.log('确认选择焊机类型:', weldingType)
        } else {
          // 如果没有焊机类型，选择第一个可用类型并重新订阅
          filterType.value = deviceTypes.value[0].type_code
          console.log('切换到第一个设备类型:', deviceTypes.value[0])
          subscribeDeviceType(filterType.value)
        }
      }

      const typeLoadTime = performance.now()
      console.log(`设备类型加载完成，耗时: ${(typeLoadTime - startTime).toFixed(2)}ms`)
      
      // 获取设备数量并更新骨架屏
      loadingProgress.value = '正在获取设备数量...'
      await updateSkeletonCount()
      
      // 预加载所有设备类型的字段配置
      console.log('开始预加载设备字段配置...')
      const deviceTypeCodes = deviceTypes.value.map(type => type.type_code)
      try {
        await deviceFieldStore.batchGetMonitoringFields(deviceTypeCodes)
        console.log('设备字段配置预加载完成')
      } catch (error) {
        console.error('预加载设备字段配置失败:', error)
      }
    })

    // 等待设备类型加载完成（但不阻塞WebSocket连接）
    await deviceTypesPromise

    loadingProgress.value = '正在等待实时数据...'

    // Mock模式：直接使用HTTP API加载数据
    if (mockEnabled) {
      console.log('🎭 Mock模式：使用HTTP API加载设备数据')
      await loadDevicesByHttp()
      
      loading.value = false
      realtimeDataLoading.value = false
      loadingProgress.value = ''
      
      const realtimeDataTime = performance.now()
      console.log(`实时数据(HTTP API)加载完成，总耗时: ${(realtimeDataTime - startTime).toFixed(2)}ms`)
      console.log('设备监测页面加载完成(使用Mock HTTP API)')
    } 
    // WebSocket模式
    else if (cachedWebSocketData) {
      console.log('处理缓存的WebSocket数据:', cachedWebSocketData.length)
      processWebSocketData(cachedWebSocketData)
      cachedWebSocketData = null // 清空缓存

      // WebSocket数据已经可用，立即停止加载状态
      loading.value = false
      realtimeDataLoading.value = false
      loadingProgress.value = ''

      const realtimeDataTime = performance.now()
      console.log(
        `实时数据(WebSocket缓存)加载完成，总耗时: ${(realtimeDataTime - startTime).toFixed(2)}ms`
      )
      console.log('设备监测页面加载完成(使用WebSocket缓存)')
    } else {
      // 等待WebSocket连接和数据推送
      console.log('等待WebSocket连接和实时数据推送...')

      // 优化超时机制，减少等待时间到5秒
      const timeout = setTimeout(() => {
        if (allDevices.value.length === 0) {
          loading.value = false
          realtimeDataLoading.value = false
          loadingProgress.value = ''
          message.warning('等待实时数据超时，请检查WebSocket连接')
        }
      }, 5000) // 从10秒减少到5秒

      // 优化WebSocket数据检查频率
      const checkDataInterval = setInterval(() => {
        if (allDevices.value.length > 0) {
          clearTimeout(timeout)
          clearInterval(checkDataInterval)

          loading.value = false
          realtimeDataLoading.value = false
          loadingProgress.value = ''

          const realtimeDataTime = performance.now()
          console.log(`实时数据加载完成，总耗时: ${(realtimeDataTime - startTime).toFixed(2)}ms`)
          console.log('设备监测页面加载完成(通过WebSocket实时数据)')
        }
      }, 200) // 从500ms减少到200ms，提高响应速度
    }

    // 设置定时清理过期缓存，每5分钟执行一次
    setInterval(() => {
      cleanExpiredRealtimeCache()
    }, 5 * 60 * 1000)
  } catch (error) {
    console.error('页面加载失败:', error)
    message.error('页面加载失败，请刷新重试')
    loadingProgress.value = ''
    loading.value = false
    realtimeDataLoading.value = false
  }
})

onUnmounted(() => {
  // WebSocket连接会自动断开
  console.log('设备监测页面已卸载')
})
</script>

<style scoped>
/* 分析设备按钮样式 - 强制使用橙色主题 */
/* PermissionButton 直接渲染 n-button，所以 analyze-device-btn 类会在 n-button 上 */
.analyze-device-btn.n-button {
  background-color: rgba(244, 81, 30, 0.12) !important;
  border-color: #F4511E !important;
  color: #F4511E !important;
}

.analyze-device-btn.n-button:hover {
  background-color: rgba(244, 81, 30, 0.2) !important;
  border-color: #F4511E !important;
}

.analyze-device-btn.n-button:active {
  background-color: rgba(244, 81, 30, 0.28) !important;
}

.analyze-device-btn :deep(.n-button__content) {
  color: #F4511E !important;
}

.analyze-device-btn :deep(.n-icon),
.analyze-device-btn :deep(svg) {
  color: #F4511E !important;
}

/* 连接状态指示器 */
.connection-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.connection-indicator--connected {
  background-color: #18a058;
  animation: pulse 2s infinite;
}

.connection-indicator--connecting {
  background-color: #f0a020;
  animation: blink 1s infinite;
}

.connection-indicator--disconnected {
  background-color: #d03050;
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0.3;
  }
}

/* 设备网格布局 - 紧凑简洁版本 */
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-top: 16px;
  padding: 2px;
}

@media (max-width: 1400px) {
  .device-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .device-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}

/* 设备卡片样式 - 紧凑简洁版本 (60%高度) */
.device-card {
  position: relative;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border-left: 3px solid #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.device-card :deep(.n-card__content) {
  padding: 8px 10px !important;
}

.device-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.device-card--welding {
  border-left-color: #10b981;
}

.device-card--welding:hover {
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.15);
}

.device-card--standby {
  border-left-color: #f59e0b;
}

.device-card--standby:hover {
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.15);
}

.device-card--fault {
  border-left-color: #ef4444;
}

.device-card--fault:hover {
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.15);
}

.device-card--inactive {
  border-left-color: #9ca3af;
  opacity: 0.8;
}

.device-card--inactive:hover {
  opacity: 1;
  box-shadow: 0 6px 16px rgba(107, 114, 128, 0.12);
}

/* 状态指示器 - 紧凑版本 */
.status-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  z-index: 10;
}

.status-indicator--welding {
  background-color: #10b981;
  animation: pulse-green 2s infinite;
}

.status-indicator--standby {
  background-color: #f59e0b;
  animation: pulse-orange 2s infinite;
}

.status-indicator--fault {
  background-color: #ef4444;
  animation: pulse-red 2s infinite;
}

.status-indicator--inactive {
  background-color: #9ca3af;
  animation: none;
}

/* 状态闪烁动画 - 简洁版本 */
@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
  50% { box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2); }
}

@keyframes pulse-orange {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.6); }
  50% { box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.2); }
}

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
  50% { box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2); }
}

/* 设备头部信息 - 紧凑版本 (60%高度) */
.device-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 2px 0;
  color: #1f2937;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-id {
  font-size: 10px;
  color: #9ca3af;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
}

.device-type {
  margin-left: 6px;
  flex-shrink: 0;
}

.device-type :deep(.n-tag) {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  line-height: 1.3;
}

/* 设备状态 */
.device-status {
  margin-bottom: 10px;
}

/* 监控数据 */
.monitoring-data {
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.data-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
  transition: opacity 0.3s ease;
}

.data-label {
  color: #666;
  margin-right: 4px;
}

.data-value {
  font-weight: 600;
  color: #333;
  transition: all 0.2s ease;
}

/* 数据加载过渡动画 */
.data-loading-enter-active,
.data-loading-leave-active {
  transition: opacity 0.3s ease;
}

.data-loading-enter-from,
.data-loading-leave-to {
  opacity: 0;
}

/* 设备状态过渡动画 */
.device-status {
  transition: all 0.3s ease;
}

/* 设备位置 - 紧凑版本 (60%高度) */
.device-location {
  display: flex;
  align-items: center;
  font-size: 10px;
  color: #9ca3af;
  margin-bottom: 4px;
  padding: 3px 0;
}

/* 设备操作 - 紧凑版本 (60%高度) */
.device-actions {
  display: flex;
  flex-direction: row;
  gap: 6px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.device-actions :deep(.n-button) {
  flex: 1;
  justify-content: center;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  padding: 0 8px;
  height: 26px;
  transition: all 0.2s ease;
}

.device-actions :deep(.n-button:hover) {
  transform: translateY(-1px);
}

.device-actions :deep(.n-button--default-type) {
  background: #f5f5f5;
  border: 1px solid #e5e5e5;
}

.device-actions :deep(.n-button--primary-type) {
  background: #3b82f6;
}

.n-card {
  border-radius: 12px;
}

/* 卡片入场动画 */
.device-card {
  animation: cardFadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  animation-fill-mode: both;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 卡片交错入场动画 */
.device-grid .device-card:nth-child(1) { animation-delay: 0.05s; }
.device-grid .device-card:nth-child(2) { animation-delay: 0.1s; }
.device-grid .device-card:nth-child(3) { animation-delay: 0.15s; }
.device-grid .device-card:nth-child(4) { animation-delay: 0.2s; }
.device-grid .device-card:nth-child(5) { animation-delay: 0.25s; }
.device-grid .device-card:nth-child(6) { animation-delay: 0.3s; }
.device-grid .device-card:nth-child(7) { animation-delay: 0.35s; }
.device-grid .device-card:nth-child(8) { animation-delay: 0.4s; }
.device-grid .device-card:nth-child(n+9) { animation-delay: 0.45s; }

/* 卡片悬浮时的光效 */
.device-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.4),
    transparent
  );
  transition: left 0.5s ease;
  pointer-events: none;
}

.device-card:hover::after {
  left: 100%;
}

/* 设备名称悬浮效果 */
.device-name {
  position: relative;
  display: inline-block;
}

.device-name::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.3s ease;
  border-radius: 1px;
}

.device-card:hover .device-name::after {
  width: 100%;
}

/* 设备ID徽章效果 */
.device-id {
  position: relative;
  overflow: hidden;
}

.device-id::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  transition: left 0.4s ease;
}

.device-card:hover .device-id::before {
  left: 100%;
}

/* 设备类型标签动画 */
.device-type :deep(.n-tag) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.device-card:hover .device-type :deep(.n-tag) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 位置图标动画 */
.device-location :deep(.icon) {
  transition: all 0.3s ease;
}

.device-location:hover :deep(.icon) {
  transform: scale(1.2);
  color: #3b82f6;
}

/* 按钮图标动画 */
.device-actions :deep(.n-button .icon) {
  transition: transform 0.3s ease;
}

.device-actions :deep(.n-button:hover .icon) {
  transform: scale(1.15);
}

/* 设备详情弹窗样式 */
.device-detail-modal {
  .n-card {
    border-radius: 12px;
  }
}

.device-detail {
  max-height: 80vh;
  overflow-y: auto;
}

/* 设备概览卡片 */
.device-overview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.device-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.device-icon {
  color: rgba(255, 255, 255, 0.9);
}

.title-info {
  .device-name {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: white;
  }

  .device-subtitle {
    margin: 4px 0 0 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }
}

.status-badge {
  .n-tag {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
  }
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: white;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
  }
}

/* 详情内容布局 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 24px;
  height: 100%;
  min-height: 0;
}

.detail-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  &:last-child {
    grid-template-columns: 1fr;
  }
}

.full-width {
  grid-column: 1 / -1;
}

/* 信息卡片样式 */
.info-card {
  height: 100%;
  display: flex;
  flex-direction: column;

  .n-card__header {
    padding-bottom: 12px;
  }

  .n-card__content {
    padding: 20px;
  }

  &.basic-info {
    border-left: 4px solid #3b82f6;
  }

  &.work-info {
    border-left: 4px solid #10b981;
  }

  &.process-info {
    border-left: 4px solid #8b5cf6;
  }

  &.status-info {
    border-left: 4px solid #f59e0b;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  flex: 1;
  overflow-y: auto;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }
}

.info-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  min-width: 80px;
  margin-right: 16px;
}

.info-value {
  font-size: 12px;
  color: #333;
  text-align: right;
  word-break: break-all;
  margin-left: 16px;
}

/* 监控卡片样式 */
.monitoring-card {
  border-left: 4px solid #f59e0b;

  .n-card__header {
    padding-bottom: 16px;
  }
}

.monitoring-status {
  display: flex;
  align-items: center;
  gap: 8px;

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #d1d5db;
    transition: all 0.3s ease;

    &.active {
      background: #10b981;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    }
  }

  .status-text {
    font-size: 13px;
    color: #666;
    font-weight: 500;
  }
}

.monitoring-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &.compact {
    gap: 12px;
  }
}

.metric-card {
  padding: 16px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;

  &.current {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-color: #f59e0b;
  }

  &.voltage {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border-color: #3b82f6;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;

  .metric-icon {
    color: #374151;
  }

  .metric-title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
  }
}

.metric-values {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric-item {
  text-align: center;

  .metric-label {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 4px;
    font-weight: 500;
  }

  .metric-value {
    font-size: 20px;
    font-weight: 700;
    color: #1f2937;

    &.preset {
      color: #059669;
    }

    &.actual {
      color: #dc2626;
    }

    .unit {
      font-size: 12px;
      color: #6b7280;
      font-weight: 500;
    }
  }
}

/* 状态内容 */
.status-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.status-main {
  flex: 1;
}

.status-indicator {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;

  &.welding {
    background: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
    animation: pulse 2s infinite;
  }

  &.inactive {
    background: #6b7280;
  }

  &.standby {
    background: #f59e0b;
  }

  &.fault {
    background: #ef4444;
    animation: pulse 2s infinite;
  }
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-time {
  font-size: 12px;
  color: #6b7280;
}

.status-description {
  font-size: 12px;
  color: #374151;
  margin-top: 4px;
}

.status-meta {
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.update-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #9ca3af;
}

/* 状态卡片中的监控数据样式 */
.status-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 0;
  padding: 16px;
  background: rgba(249, 250, 251, 0.8);
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.status-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .metric-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #666;
    font-weight: 500;
  }

  .metric-values {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;

    .preset {
      color: #059669;
    }

    .separator {
      color: #9ca3af;
      margin: 0 2px;
    }

    .actual {
      color: #dc2626;
    }
  }
}

/* 模态框操作按钮 */
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    gap: 20px;
  }

  .detail-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .device-overview {
    padding: 16px;
  }

  .overview-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .detail-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    gap: 16px;
  }

  .info-grid {
    gap: 12px;
  }

  .info-item {
    padding: 10px 0;
  }

  .info-card .n-card__content {
    padding: 16px;
  }

  .status-metrics {
    margin: 12px 0;
    padding: 12px;
  }

  .metric-values {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .detail-content {
    gap: 12px;
  }
}

/* 分页组件样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  margin-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.connection-status {
  display: flex;
  align-items: center;
  margin-left: 16px;
}
</style>
