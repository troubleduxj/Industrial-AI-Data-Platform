<template>
  <CommonPage show-footer>
    <!-- 查询条件 -->
    <NCard class="mb-15" rounded-10>
      <div class="flex flex-wrap items-center gap-4">
        <QueryBarItem label="设备类型" :label-width="70">
          <NSelect
            v-model:value="filterType"
            :options="deviceTypeOptions"
            placeholder="请选择设备类型"
            clearable
            style="width: 200px"
          />
        </QueryBarItem>
        <QueryBarItem label="设备编码" :label-width="70">
          <NInput
            v-model:value="prodCode"
            placeholder="请输入设备编码"
            clearable
            style="width: 160px"
          />
        </QueryBarItem>
        <QueryBarItem label="时间范围" :label-width="70">
          <NDatePicker
            v-model:value="dateRange"
            type="daterange"
            clearable
            format="yyyy-MM-dd"
            value-format="timestamp"
            placeholder="请选择时间范围"
            style="width: 320px; min-width: 320px"
          />
        </QueryBarItem>
        <div class="ml-auto flex items-center gap-2">
          <PermissionButton
            permission="GET /api/v2/alarms"
            type="primary"
            :loading="loading"
            @click="handleQuery"
          >
            <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
          </PermissionButton>
          <PermissionButton permission="GET /api/v2/alarms" @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
          </PermissionButton>
        </div>
      </div>
    </NCard>

    <!-- 报警列表 -->
    <NCard class="mb-15" rounded-10>
      <template #header>
        <span>报警列表</span>
      </template>

      <NDataTable
        ref="tableRef"
        :columns="columns"
        :data="alarmData"
        :loading="loading"
        :pagination="false"
        :row-key="(row) => row.id"
        striped
        size="small"
        flex-height
        style="height: 500px"
      ></NDataTable>
      <!-- 独立分页组件 -->
      <div v-if="alarmData.length > 0" class="mt-6 flex justify-center">
        <NPagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          :show-size-picker="pagination.showSizePicker"
          :show-quick-jumper="pagination.showQuickJumper"
          :prefix="(info) => `共 ${info.itemCount} 条`"
          :suffix="(info) => `显示 ${info.startIndex}-${info.endIndex} 条`"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </NCard>
  </CommonPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import {
  NCard,
  NButton,
  NSelect,
  NDatePicker,
  NInput,
  NDataTable,
  NTag,
  useMessage,
  NPagination,
} from 'naive-ui' // 导入NPagination
import { formatDate } from '@/utils'
import PermissionButton from '@/components/common/PermissionButton.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import CommonPage from '@/components/page/CommonPage.vue'
// ✅ Shared API 迁移 (2025-10-25)
import { deviceTypeApi } from '@/api/device-shared'
import { alarmApi } from '@/api/alarm-shared'
import { useRoute } from 'vue-router'

// 消息提示
const message = useMessage()

// 路由实例
const route = useRoute()

// 响应式数据
const loading = ref(false)
const tableRef = ref()

// 查询条件
const filterType = ref(null)
const prodCode = ref('')
const dateRange = ref(null)

// 报警数据
const alarmData = ref([])

// 设备类型数据
const deviceTypes = ref([])

// 加载设备类型数据
const loadDeviceTypes = async () => {
  try {
    // ✅ Shared API 迁移
    const response = await deviceTypeApi.list()
    if (response && response.data) {
      deviceTypes.value = response.data
      console.log('✅ Shared API - 设备类型数据加载成功:', deviceTypes.value)
    }
  } catch (error) {
    console.warn('获取设备类型失败，使用默认选项:', error)
    message.warning('获取设备类型失败，使用默认选项')
    // deviceTypes保持空数组，计算属性会自动使用降级选项
  }
}

// 设备类型选项 - 计算属性，支持动态获取和降级处理
const deviceTypeOptions = computed(() => {
  const baseOptions = [{ label: '全部设备', value: null }]

  if (deviceTypes.value && deviceTypes.value.length > 0) {
    const dynamicOptions = deviceTypes.value.map((type) => ({
      label: type.type_name,
      value: type.type_code,
    }))
    return [...baseOptions, ...dynamicOptions]
  }

  // 降级处理：API调用失败时使用默认选项
  const defaultOptions = [
    { label: '焊机', value: 'welding' },
    { label: '切割设备', value: 'cutting' },
    { label: '装配设备', value: 'assembly' },
  ]
  return [...baseOptions, ...defaultOptions]
})

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
  // onChange: (page) => {
  //   pagination.page = page
  //   handleQuery()
  // },
  // onUpdatePageSize: (pageSize) => {
  //   pagination.pageSize = pageSize
  //   pagination.page = 1
  //   handleQuery()
  // }
})

// 处理分页变化
function handlePageChange(page) {
  pagination.page = page
  handleQuery()
}

// 处理每页大小变化
function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  handleQuery()
}

// 表格列配置 - 使用后端实际返回的字段名
const columns = [
  {
    title: '设备编码',
    key: 'prod_code',
    width: 180,
  },
  {
    title: '报警时间',
    key: 'alarm_time',
    width: 180,
    render: (row) => formatDate(row.alarm_time, 'YYYY-MM-DD HH:mm:ss'),
  },
  {
    title: '报警结束时间',
    key: 'alarm_end_time',
    width: 180,
    render: (row) =>
      row.alarm_end_time ? formatDate(row.alarm_end_time, 'YYYY-MM-DD HH:mm:ss') : '-',
  },
  {
    title: '报警代码',
    key: 'alarm_code',
    width: 120,
  },
  {
    title: '持续时间(秒)',
    key: 'alarm_duration_sec',
    width: 120,
    render: (row) => row.alarm_duration_sec || 0,
  },
  {
    title: '报警内容',
    key: 'alarm_message',
    width: 200,
  },
  {
    title: '解决方案',
    key: 'alarm_solution',
    width: 200,
    render: (row) => row.alarm_solution || '-',
  },
]

// 处理查询
async function handleQuery() {
  loading.value = true

  try {
    // 构建查询参数 - 匹配后端V2 API的AlarmQuery模型
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    // 处理时间范围 - 使用V2 API期望的参数名
    if (dateRange.value && dateRange.value.length === 2) {
      const [startTime, endTime] = dateRange.value
      params.date_from = new Date(startTime).toISOString().replace('T', ' ').slice(0, 19)
      params.date_to = new Date(endTime).toISOString().replace('T', ' ').slice(0, 19)
    }

    // 添加设备类型筛选
    if (filterType.value) {
      params.device_type = filterType.value
    }

    // 添加搜索关键词（如果有产品代码）
    if (prodCode.value) {
      params.search = prodCode.value
    }

    console.log('查询参数:', params)

    // ✅ Shared API 迁移
    const response = await alarmApi.list(params)

    console.log('✅ Shared API - 告警列表响应:', response)

    // 检查响应数据结构
    if (response && response.data && Array.isArray(response.data)) {
      // V2 API的标准响应格式：{data: [], meta: {total, page, ...}, links: {}}
      alarmData.value = response.data
      pagination.itemCount = response.meta?.total || response.data.length

      console.log('V2 API数据解析成功:', {
        dataType: 'array',
        itemsCount: alarmData.value.length,
        totalFromMeta: response.meta?.total,
      })

      console.log('报警数据查询成功:', {
        items: alarmData.value.length,
        total: pagination.itemCount,
        page: pagination.page,
        pageSize: pagination.pageSize,
      })

      message.success(`查询成功，共找到 ${pagination.itemCount} 条记录`)
      return // 添加return语句，避免继续执行后续的else if条件
    } else if (response && response.success && response.data) {
      // 带success字段的响应格式
      if (Array.isArray(response.data)) {
        alarmData.value = response.data
        pagination.itemCount = response.meta?.total || response.data.length

        console.log('带success字段的数据解析成功:', {
          dataType: 'array',
          itemsCount: alarmData.value.length,
          totalFromMeta: response.meta?.total,
        })

        message.success(`查询成功，共找到 ${pagination.itemCount} 条记录`)
        return // 添加return语句
      } else if (response.data.items) {
        // 兼容其他可能的格式
        alarmData.value = response.data.items
        pagination.itemCount = response.data.total || 0

        console.log('兼容格式数据解析成功:', {
          dataType: 'object with items',
          itemsCount: alarmData.value.length,
          total: response.data.total,
        })

        message.success(`查询成功，共找到 ${pagination.itemCount} 条记录`)
        return // 添加return语句
      } else if (typeof response.data === 'object' && response.data !== null) {
        // 处理对象格式的数据（数字索引的对象）
        const dataKeys = Object.keys(response.data)
        const isIndexedObject = dataKeys.every(
          (key) => !isNaN(parseInt(key)) || key === '_processed'
        )

        if (isIndexedObject) {
          // 将数字索引的对象转换为数组
          const dataArray = []
          dataKeys.forEach((key) => {
            if (!isNaN(parseInt(key))) {
              dataArray[parseInt(key)] = response.data[key]
            }
          })
          // 过滤掉空元素
          alarmData.value = dataArray.filter((item) => item !== undefined)
          pagination.itemCount = response.meta?.total || alarmData.value.length

          console.log('索引对象格式数据解析成功:', {
            dataType: 'indexed object',
            itemsCount: alarmData.value.length,
            totalFromMeta: response.meta?.total,
          })

          message.success(`查询成功，共找到 ${pagination.itemCount} 条记录`)
          return // 添加return语句
        } else {
          console.warn('未知的响应数据格式:', {
            hasSuccess: !!response.success,
            hasData: !!response.data,
            dataType: typeof response.data,
            dataKeys: response.data ? Object.keys(response.data) : 'N/A',
            hasMeta: !!response.meta,
          })
          alarmData.value = []
          pagination.itemCount = 0
        }
      } else {
        console.warn('未知的响应数据格式:', {
          hasSuccess: !!response.success,
          hasData: !!response.data,
          dataType: typeof response.data,
          dataKeys: response.data ? Object.keys(response.data) : 'N/A',
          hasMeta: !!response.meta,
        })
        alarmData.value = []
        pagination.itemCount = 0
      }

      console.log('报警数据查询成功:', {
        items: alarmData.value.length,
        total: pagination.itemCount,
        page: pagination.page,
        pageSize: pagination.pageSize,
      })

      message.success(`查询成功，共找到 ${pagination.itemCount} 条记录`)
    } else {
      console.warn('未知的响应数据格式:', {
        hasSuccess: !!response?.success,
        hasData: !!response?.data,
        dataType: typeof response?.data,
        dataKeys: response?.data ? Object.keys(response.data) : 'N/A',
        hasMeta: !!response?.meta,
        responseKeys: response ? Object.keys(response) : 'N/A',
      })
      alarmData.value = []
      pagination.itemCount = 0
      message.error('获取报警数据失败: 数据格式不正确')
    }
  } catch (error) {
    console.error('查询报警数据失败:', error)
    message.error('查询失败，请重试')
    alarmData.value = []
    pagination.itemCount = 0
  } finally {
    loading.value = false
  }
}

// 处理重置
function handleReset() {
  filterType.value = 'welding'
  prodCode.value = ''
  dateRange.value = null

  // 重新查询
  pagination.page = 1
  handleQuery()

  message.success('重置成功')
}

// 处理刷新
function handleRefresh() {
  handleQuery()
}

// 初始化
onMounted(async () => {
  try {
    // 先加载设备类型数据
    await loadDeviceTypes()

    // 检查路由查询参数
    const { device_code, start_time, end_time } = route.query

    if (device_code) {
      // 如果有设备编码参数，使用传递的参数
      prodCode.value = device_code
      console.log('从路由获取设备编码:', device_code)

      if (start_time && end_time) {
        // 如果有时间范围参数，转换为时间戳
        const startTimestamp = new Date(start_time).getTime()
        const endTimestamp = new Date(end_time).getTime()
        dateRange.value = [startTimestamp, endTimestamp]
        console.log('从路由获取时间范围:', { start_time, end_time })
      } else {
        // 如果没有时间范围，使用最近7天
        const now = new Date()
        const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        dateRange.value = [sevenDaysAgo.getTime(), now.getTime()]
      }

      // 设备类型默认选择焊机
      filterType.value = 'welding'
    } else {
      // 如果没有路由参数，使用默认参数：设备类型为焊机，时间范围为前一天到今天
      filterType.value = 'welding'
      // 使用前一天到今天作为默认时间范围
      const today = new Date()
      today.setHours(23, 59, 59, 999)  // 今天的结束时刻
      
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
      yesterday.setHours(0, 0, 0, 0)  // 前一天的开始时刻
      
      dateRange.value = [yesterday.getTime(), today.getTime()]
      console.log('默认时间范围:', { start: yesterday, end: today })
    }

    // 然后查询报警数据
    await handleQuery()
    console.log('报警信息页面初始化完成')
  } catch (error) {
    console.error('页面初始化失败:', error)
    message.error('页面初始化失败')
  }
})
</script>

<style scoped>
/* 页面头部样式 */
.page-header {
  text-align: center;
  padding: 20px 0;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 16px;
  color: #666;
  margin: 0;
}

/* 查询容器样式 */
.query-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.query-items {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
  flex: 1;
}

.query-items :deep(.query-bar-item) {
  flex: 0 0 auto;
  min-width: 200px;
}

.query-items :deep(.n-select),
.query-items :deep(.n-input) {
  width: 100%;
}

.query-items :deep(.n-date-picker) {
  /* 不设置width: 100%，让inline style生效 */
}

.query-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  min-width: fit-content;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .query-container {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .query-items {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .query-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 600px) {
  .query-items {
    flex-direction: column;
    align-items: stretch;
  }
}

/* 统计卡片样式 */
.statistics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
}

.info-icon {
  position: absolute;
  top: -8px;
  right: -8px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
}

.info-icon:hover {
  color: #1890ff;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.critical {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #faad14 0%, #d48806 100%);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.stat-icon.resolved {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 表格样式 */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

/* 报警详情样式 */
.alarm-detail {
  padding: 16px 0;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
}

.detail-item .label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
  margin-right: 8px;
}

.detail-item .value {
  color: #333;
  flex: 1;
}

.alarm-content,
.alarm-description,
.alarm-solution {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  color: #333;
  line-height: 1.6;
}

/* 批量处理样式 */
.batch-process {
  padding: 16px 0;
}

.batch-info {
  background: #f0f9ff;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.batch-actions {
  margin-bottom: 16px;
}

.batch-remark .label {
  display: block;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

/* 弹窗操作按钮 */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .statistics-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .statistics-cards {
    grid-template-columns: 1fr;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
