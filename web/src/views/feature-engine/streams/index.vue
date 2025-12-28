<template>
  <div class="feature-streams-page">
    <n-card title="流计算任务管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button @click="refreshAll">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新状态
          </n-button>
          <n-button type="primary" @click="handleCreate">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            新建任务
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="streams"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 创建任务弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 700px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="任务名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入任务名称" />
        </n-form-item>
        <n-form-item label="关联特征" path="feature_id">
          <n-select v-model:value="formData.feature_id" :options="featureOptions" placeholder="选择特征定义" />
        </n-form-item>
        <n-form-item label="源表">
          <n-input v-model:value="formData.source_table" placeholder="TDengine源表名" />
        </n-form-item>
        <n-form-item label="目标表">
          <n-input v-model:value="formData.target_table" placeholder="TDengine目标表名" />
        </n-form-item>
        <n-form-item label="滑动窗口">
          <n-input-group>
            <n-input-number v-model:value="formData.sliding_window" :min="1" style="width: 150px;" />
            <n-select v-model:value="formData.sliding_unit" :options="windowUnitOptions" style="width: 100px;" />
          </n-input-group>
        </n-form-item>
        <n-form-item label="SQL语句">
          <n-input v-model:value="formData.sql_statement" type="textarea" :rows="6" placeholder="流计算SQL语句" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="info" @click="handleGenerateSQL">生成SQL</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
      </template>
    </n-modal>

    <!-- 日志弹窗 -->
    <n-modal v-model:show="showLogModal" preset="dialog" title="任务日志" style="width: 800px;">
      <n-log :log="taskLogs" :rows="20" language="log" />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h, computed } from 'vue'
import { NButton, NSpace, NTag, NProgress, useMessage, useDialog } from 'naive-ui'
import { AddOutline, RefreshOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const showLogModal = ref(false)
const modalTitle = ref('新建流计算任务')
const streams = ref([])
const features = ref([])
const taskLogs = ref('')
const formRef = ref(null)

const pagination = reactive({ page: 1, pageSize: 10 })

const formData = reactive({
  id: null,
  name: '',
  feature_id: null,
  source_table: '',
  target_table: '',
  sliding_window: 5,
  sliding_unit: 'minute',
  sql_statement: ''
})

const rules = {
  name: { required: true, message: '请输入任务名称', trigger: 'blur' },
  feature_id: { required: true, message: '请选择特征定义', trigger: 'change' }
}

const windowUnitOptions = [
  { label: '秒', value: 'second' },
  { label: '分钟', value: 'minute' },
  { label: '小时', value: 'hour' }
]

const featureOptions = computed(() => features.value.map(f => ({ label: f.name, value: f.id })))

const statusMap = {
  created: { text: '已创建', type: 'default', color: '#909399' },
  running: { text: '运行中', type: 'success', color: '#67c23a' },
  paused: { text: '已暂停', type: 'warning', color: '#e6a23c' },
  stopped: { text: '已停止', type: 'error', color: '#f56c6c' },
  error: { text: '错误', type: 'error', color: '#f56c6c' }
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '任务名称', key: 'name' },
  { title: '关联特征', key: 'feature_name' },
  { title: '源表', key: 'source_table' },
  { title: '目标表', key: 'target_table' },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const status = statusMap[row.status] || statusMap.created
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  {
    title: '处理进度',
    key: 'progress',
    width: 150,
    render: row => h(NProgress, { 
      type: 'line', 
      percentage: row.progress || 0,
      indicatorPlacement: 'inside',
      processing: row.status === 'running'
    })
  },
  { title: '处理记录数', key: 'processed_count', width: 100 },
  { title: '最后运行', key: 'last_run_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    render: row => h(NSpace, {}, () => [
      row.status === 'running' 
        ? h(NButton, { size: 'small', type: 'warning', onClick: () => handlePause(row) }, () => '暂停')
        : h(NButton, { size: 'small', type: 'success', onClick: () => handleStart(row) }, () => '启动'),
      h(NButton, { size: 'small', onClick: () => handleLogs(row) }, () => '日志'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadStreams = async () => {
  loading.value = true
  try {
    const res = await platformApi.getStreamTasks()
    streams.value = res.data || []
  } catch (error) {
    message.error('加载流计算任务失败')
  } finally {
    loading.value = false
  }
}

const loadFeatures = async () => {
  try {
    const res = await platformApi.getFeatureDefinitions()
    features.value = res.data || []
  } catch (error) {
    console.error('加载特征失败:', error)
  }
}

const refreshAll = () => {
  loadStreams()
  message.info('状态已刷新')
}

const handleCreate = () => {
  modalTitle.value = '新建流计算任务'
  Object.assign(formData, { 
    id: null, name: '', feature_id: null, source_table: '', 
    target_table: '', sliding_window: 5, sliding_unit: 'minute', sql_statement: '' 
  })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑流计算任务'
  Object.assign(formData, row)
  showModal.value = true
}

const handleGenerateSQL = async () => {
  if (!formData.feature_id) {
    message.warning('请先选择特征定义')
    return
  }
  try {
    const res = await platformApi.generateStreamSQL({
      feature_id: formData.feature_id,
      source_table: formData.source_table,
      target_table: formData.target_table,
      sliding_window: formData.sliding_window,
      sliding_unit: formData.sliding_unit
    })
    formData.sql_statement = res.data?.sql || ''
    message.success('SQL已生成')
  } catch (error) {
    message.error('生成SQL失败')
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await platformApi.updateStreamTask(formData.id, formData)
      message.success('更新成功')
    } else {
      await platformApi.createStreamTask(formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadStreams()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleStart = async (row) => {
  try {
    await platformApi.startStreamTask(row.id)
    message.success('任务已启动')
    loadStreams()
  } catch (error) {
    message.error('启动失败')
  }
}

const handlePause = async (row) => {
  try {
    await platformApi.pauseStreamTask(row.id)
    message.success('任务已暂停')
    loadStreams()
  } catch (error) {
    message.error('暂停失败')
  }
}

const handleLogs = async (row) => {
  try {
    const res = await platformApi.getStreamTaskLogs(row.id)
    taskLogs.value = res.data?.logs || '暂无日志'
    showLogModal.value = true
  } catch (error) {
    message.error('获取日志失败')
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除流计算任务 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.deleteStreamTask(row.id)
        message.success('删除成功')
        loadStreams()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadStreams()
  loadFeatures()
})
</script>

<style scoped>
.feature-streams-page {
  padding: 16px;
}
</style>
