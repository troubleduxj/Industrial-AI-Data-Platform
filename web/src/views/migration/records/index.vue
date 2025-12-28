<template>
  <div class="migration-records-page">
    <n-card title="迁移记录" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-select v-model:value="filter.status" :options="statusOptions" placeholder="状态筛选" style="width: 150px;" clearable />
          <n-date-picker v-model:value="filter.date_range" type="daterange" clearable />
          <n-button @click="loadRecords">查询</n-button>
          <n-button type="info" @click="exportRecords">导出</n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="records"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
        @update:page="handlePageChange"
      />
    </n-card>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="dialog" title="迁移详情" style="width: 800px;">
      <n-descriptions :column="2" label-placement="left" bordered>
        <n-descriptions-item label="记录ID">{{ detail.id }}</n-descriptions-item>
        <n-descriptions-item label="迁移类型">{{ detail.migration_type }}</n-descriptions-item>
        <n-descriptions-item label="源表">{{ detail.source_table }}</n-descriptions-item>
        <n-descriptions-item label="目标表">{{ detail.target_table }}</n-descriptions-item>
        <n-descriptions-item label="记录数">{{ detail.record_count }}</n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="statusMap[detail.status]?.type">{{ statusMap[detail.status]?.text }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="开始时间">{{ detail.started_at }}</n-descriptions-item>
        <n-descriptions-item label="完成时间">{{ detail.completed_at }}</n-descriptions-item>
        <n-descriptions-item label="耗时">{{ detail.duration }}秒</n-descriptions-item>
        <n-descriptions-item label="执行人">{{ detail.executed_by }}</n-descriptions-item>
      </n-descriptions>

      <n-divider>错误信息</n-divider>
      <n-code v-if="detail.error_message" :code="detail.error_message" language="text" />
      <n-empty v-else description="无错误信息" />

      <n-divider>迁移日志</n-divider>
      <n-log :log="detail.logs || '暂无日志'" :rows="10" language="log" />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import { platformApi } from '@/api/v3/platform'

const message = useMessage()

const loading = ref(false)
const showDetail = ref(false)
const records = ref([])
const detail = ref({})

const filter = reactive({
  status: null,
  date_range: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const statusOptions = [
  { label: '全部', value: null },
  { label: '进行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已回滚', value: 'rolled_back' }
]

const statusMap = {
  pending: { text: '等待中', type: 'default' },
  running: { text: '进行中', type: 'info' },
  completed: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'error' },
  rolled_back: { text: '已回滚', type: 'warning' }
}

const typeMap = {
  device_type: '设备类型 → 资产类别',
  device_field: '设备字段 → 信号定义',
  device: '设备 → 资产',
  full: '完整迁移'
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { 
    title: '迁移类型', 
    key: 'migration_type',
    render: row => typeMap[row.migration_type] || row.migration_type
  },
  { title: '源表', key: 'source_table' },
  { title: '目标表', key: 'target_table' },
  { title: '记录数', key: 'record_count', width: 100 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const status = statusMap[row.status] || statusMap.pending
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  { title: '耗时(秒)', key: 'duration', width: 100 },
  { title: '执行时间', key: 'started_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleDetail(row) }, () => '详情'),
      row.status === 'completed' && h(NButton, { 
        size: 'small', 
        type: 'warning', 
        onClick: () => handleRollbackRecord(row) 
      }, () => '回滚')
    ])
  }
]

const loadRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filter.status,
      start_date: filter.date_range?.[0],
      end_date: filter.date_range?.[1]
    }
    const res = await platformApi.getMigrationRecords(params)
    records.value = res.data?.items || []
    pagination.itemCount = res.data?.total || 0
  } catch (error) {
    message.error('加载迁移记录失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  loadRecords()
}

const handleDetail = async (row) => {
  try {
    const res = await platformApi.getMigrationRecordDetail(row.id)
    detail.value = res.data || row
    showDetail.value = true
  } catch (error) {
    detail.value = row
    showDetail.value = true
  }
}

const handleRollbackRecord = async (row) => {
  try {
    await platformApi.rollbackMigrationRecord(row.id)
    message.success('回滚成功')
    loadRecords()
  } catch (error) {
    message.error('回滚失败')
  }
}

const exportRecords = async () => {
  try {
    const params = {
      status: filter.status,
      start_date: filter.date_range?.[0],
      end_date: filter.date_range?.[1]
    }
    const res = await platformApi.exportMigrationRecords(params)
    
    // 下载文件
    const blob = new Blob([res.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `migration_records_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    
    message.success('导出成功')
  } catch (error) {
    message.error('导出失败')
  }
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.migration-records-page {
  padding: 16px;
}
</style>
