<template>
  <CommonPage
    v-permission="{ action: 'read', resource: 'weld_record' }"
    show-footer
    title="焊接记录"
  >
    <template #action>
      <!-- 导出按钮 -->
      <PermissionButton
        permission="GET /api/v2/statistics/weld-records/export"
        type="primary"
        @click="handleExport"
      >
        <TheIcon icon="material-symbols:download" :size="16" class="mr-5" />
        导出记录
      </PermissionButton>
    </template>

    <!-- 查询条件 -->
    <NCard class="mb-15" rounded-10>
      <div class="query-container">
        <!-- 第一行：设备编码、开始时间、结束时间 -->
        <div
          class="query-row"
          style="
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 20px;
            margin-bottom: 16px;
          "
        >
          <QueryBarItem
            label="设备编码"
            :label-width="70"
            style="flex: 1; min-width: 200px; max-width: 300px"
          >
            <NInput
              v-model:value="queryForm.deviceCode"
              placeholder="请输入设备编码"
              clearable
              style="width: 100%"
            />
          </QueryBarItem>
          <QueryBarItem
            label="开始时间"
            :label-width="70"
            style="flex: 1; min-width: 260px; max-width: 350px"
          >
            <NDatePicker
              v-model:value="queryForm.startTime"
              type="datetime"
              clearable
              format="yyyy-MM-dd HH:mm:ss"
              style="width: 100%"
            />
          </QueryBarItem>
          <QueryBarItem
            label="结束时间"
            :label-width="70"
            style="flex: 1; min-width: 260px; max-width: 350px"
          >
            <NDatePicker
              v-model:value="queryForm.endTime"
              type="datetime"
              clearable
              format="yyyy-MM-dd HH:mm:ss"
              style="width: 100%"
            />
          </QueryBarItem>
        </div>

        <!-- 第二行：部门车间、班次、操作按钮 -->
        <div
          class="query-row"
          style="
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
          "
        >
          <div style="display: flex; gap: 20px; flex-wrap: wrap; flex-grow: 1">
            <QueryBarItem
              label="部门车间"
              :label-width="70"
              style="flex: 1; min-width: 200px; max-width: 300px"
            >
              <NSelect
                v-model:value="queryForm.deptId"
                :options="groupOptions"
                placeholder="全部部门车间"
                clearable
                style="width: 100%"
              />
            </QueryBarItem>
            <QueryBarItem
              label="班次"
              :label-width="50"
              style="flex: 1; min-width: 180px; max-width: 250px"
            >
              <NSelect
                v-model:value="queryForm.shift"
                :options="shiftOptions"
                placeholder="全部班次"
                clearable
                style="width: 100%"
              />
            </QueryBarItem>
          </div>

          <div
            class="query-actions"
            style="display: flex; align-items: center; gap: 12px; flex-shrink: 0"
          >
            <!-- 查询按钮 -->
            <NButton type="primary" @click="handleQuery">
              <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
              查询
            </NButton>

            <!-- 重置按钮 -->
            <NButton @click="handleReset">
              <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
              重置
            </NButton>
          </div>
        </div>
      </div>
    </NCard>

    <!-- 设备详细数据表格 -->
    <NCard title="焊接记录详细数据" class="mb-20">
      <NDataTable
        :columns="deviceColumns"
        :data="deviceData"
        :pagination="false"
        :loading="loading"
        striped
        size="medium"
        :row-key="(row) => row.ts"
      />

      <!-- 独立分页组件 -->
      <div v-if="deviceData.length > 0" class="mt-6 flex justify-center">
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
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import {
  NButton,
  NCard,
  NSelect,
  NDatePicker,
  NDataTable,
  NPagination,
  useMessage,
  NInput,
  type SelectOption,
  type DataTableColumns,
} from 'naive-ui'
import * as XLSX from 'xlsx'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate } from '@/utils'
import statisticsV2Api from '@/api/statistics-v2'
import { deviceDataApi } from '@/api/device-v2'
import { apiV2Client } from '@/utils/api-v2-migration'

defineOptions({ name: '焊接记录' })

// ==================== 类型定义 ====================

interface QueryForm {
  deviceCode: string
  startTime: number
  endTime: number
  deptId?: string | number
  shift?: string
}

interface WeldRecord {
  id: string | number
  device_code: string
  start_time: string
  end_time: string
  duration: number
  current?: number
  voltage?: number
  [key: string]: any
}

const message = useMessage()

// 响应式数据
const loading = ref<boolean>(false)

// 计算默认时间：前一天00:00:00 到 前一天23:59:59
const getDefaultTimeRange = () => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const yesterdayStart = new Date(yesterday)
  yesterdayStart.setHours(0, 0, 0, 0)
  
  const yesterdayEnd = new Date(yesterday)
  yesterdayEnd.setHours(23, 59, 59, 999)
  
  return {
    start: yesterdayStart.getTime(),
    end: yesterdayEnd.getTime()
  }
}

const defaultTime = getDefaultTimeRange()

const queryForm = reactive<QueryForm>({
  deviceCode: '', // 默认设备编码为空，查询所有设备
  startTime: defaultTime.start, // 默认开始时间为前一天00:00:00
  endTime: defaultTime.end, // 默认结束时间为前一天23:59:59
  deptId: undefined,
  shift: undefined,
})

// 设备组选项
const groupOptions: SelectOption[] = [
  { label: '生产车间A', value: 'workshop_a' },
  { label: '生产车间B', value: 'workshop_b' },
  { label: '生产车间C', value: 'workshop_c' },
  { label: '测试区域', value: 'test_area' },
]

// 班次选项
const shiftOptions: SelectOption[] = [
  { label: '早班 (08:00-16:00)', value: 'morning' },
  { label: '中班 (16:00-24:00)', value: 'afternoon' },
  { label: '夜班 (00:00-08:00)', value: 'night' },
]

// 设备数据（将通过API获取）
const deviceData = ref([])

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  showQuickJumper: true,
  itemCount: 0,
})

// 设备数据表格列配置
const deviceColumns = [
  {
    title: '设备编码',
    key: 'device_code',
    width: 120,
  },
  {
    title: '焊接开始时间',
    key: 'ts',
    width: 180,
    render: (row) => formatDate(row.ts, 'YYYY-MM-DD HH:mm:ss'),
  },
  {
    title: '焊接结束时间',
    key: 'weld_end_time',
    width: 180,
    render: (row) => formatDate(row.weld_end_time, 'YYYY-MM-DD HH:mm:ss'),
  },
  {
    title: '规范符合率',
    key: 'spec_match_rate',
    width: 120,
  },
  {
    title: '电流均值',
    key: 'avg_current',
    width: 120,
  },
  {
    title: '电压均值',
    key: 'avg_voltage',
    width: 120,
  },
  {
    title: '焊丝消耗',
    key: 'wire_consumption',
    width: 120,
  },
  {
    title: '时长',
    key: 'duration_sec',
    width: 120,
  },
]

// 查询数据
const handleQuery = async () => {
  loading.value = true
  try {
    // 添加调试信息
    console.log('查询表单数据:', queryForm)
    console.log(
      '开始时间:',
      queryForm.startTime,
      '格式化后:',
      queryForm.startTime ? formatDate(queryForm.startTime, 'YYYY-MM-DD HH:mm:ss') : undefined
    )
    console.log(
      '结束时间:',
      queryForm.endTime,
      '格式化后:',
      queryForm.endTime ? formatDate(queryForm.endTime, 'YYYY-MM-DD HH:mm:ss') : undefined
    )

    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      deviceCode: queryForm.deviceCode,
      start_time: queryForm.startTime
        ? formatDate(queryForm.startTime, 'YYYY-MM-DD HH:mm:ss')
        : undefined,
      end_time: queryForm.endTime
        ? formatDate(queryForm.endTime, 'YYYY-MM-DD HH:mm:ss')
        : undefined,
      deptId: queryForm.deptId,
      shift: queryForm.shift,
      device_type: 'welding', // 添加 device_type 参数
    }
    console.log('查询参数:', params)
    // 修复：去掉 /api/v2 前缀，因为 requestV2 的 baseURL 已经包含了
    const res = await apiV2Client.get('/devices/statistics/use-record/list', params, {
      isList: true,
    })
    console.log('API Response:', res)
    console.log('API Response type:', typeof res)
    console.log('API Response data:', res?.data)
    console.log('API Response total:', res?.total)

    if (res && res.data) {
      deviceData.value = res.data || []
      pagination.itemCount = res.total || 0
      console.log('数据赋值成功 - deviceData.value:', deviceData.value)
      console.log('数据赋值成功 - pagination.itemCount:', pagination.itemCount)
      console.log('数据条数:', deviceData.value.length)
    } else {
      deviceData.value = []
      pagination.itemCount = 0
      console.log('API返回数据为空或格式错误')
      console.log('deviceData.value (empty):', deviceData.value)
    }
  } catch (error) {
    message.error('获取焊接记录失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 重置查询条件
const handleReset = () => {
  const defaultTime = getDefaultTimeRange()
  queryForm.deviceCode = ''
  queryForm.startTime = defaultTime.start // 重置为前一天00:00:00
  queryForm.endTime = defaultTime.end // 重置为前一天23:59:59
  queryForm.deptId = undefined
  queryForm.shift = undefined
  handleQuery()
}

/**
 * 处理分页变化
 */
function handlePageChange(page) {
  pagination.page = page
  handleQuery()
}

/**
 * 处理每页大小变化
 */
function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  handleQuery()
}

// 导出记录
const handleExport = async () => {
  try {
    const params = {
      deviceCode: queryForm.deviceCode,
      start_time: queryForm.startTime
        ? formatDate(queryForm.startTime, 'YYYY-MM-DD HH:mm:ss')
        : undefined,
      end_time: queryForm.endTime
        ? formatDate(queryForm.endTime, 'YYYY-MM-DD HH:mm:ss')
        : undefined,
      deptId: queryForm.deptId,
      shift: queryForm.shift,
      device_type: 'welding', // 添加 device_type 参数
    }
    // 获取所有数据用于导出，不分页
    // 修复：去掉 /api/v2 前缀，因为 requestV2 的 baseURL 已经包含了
    const res = await apiV2Client.get(
      '/devices/statistics/use-record/list',
      { ...params, page: 1, pageSize: 10000 },
      { isList: true }
    )

    if (!res.data || res.data.length === 0) {
      message.warning('没有数据可导出')
      return
    }

    const dataToExport = res.data.map((item) => ({
      设备编码: item.device_code || '',
      焊接开始时间: formatDate(item.ts, 'YYYY-MM-DD HH:mm:ss'),
      焊接结束时间: formatDate(item.weld_end_time, 'YYYY-MM-DD HH:mm:ss'),
      规范符合率: item.spec_match_rate || '',
      电流均值: item.avg_current || '',
      电压均值: item.avg_voltage || '',
      焊丝消耗: item.wire_consumption || '',
      焊接时长: item.duration_sec || '',
    }))

    const ws = XLSX.utils.json_to_sheet(dataToExport)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '焊接记录')
    XLSX.writeFile(wb, `焊接记录_${formatDate(new Date(), 'YYYYMMDDHHmmss')}.xlsx`)
    message.success(`导出成功，共导出 ${dataToExport.length} 条记录`)
  } catch (error) {
    message.error('导出失败：' + error.message)
  }
}

// 组件挂载时初始化
onMounted(() => {
  // 页面初始化时使用默认查询条件自动查询数据
  handleQuery()
})

// 组件销毁前清理
onBeforeUnmount(() => {
  // 移除窗口大小变化监听
})
</script>

<style scoped>
/* 查询区域样式 */
.query-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.query-items {
  display: flex;
  align-items: center;
  gap: 32px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
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
</style>
