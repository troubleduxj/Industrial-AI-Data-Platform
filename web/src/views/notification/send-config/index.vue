<template>
  <div class="send-config-page">
    <n-card title="通知发送配置">
      <n-alert type="info" style="margin-bottom: 16px">
        配置不同类型通知的发送渠道、重试策略和静默时段
      </n-alert>

      <n-data-table :columns="columns" :data="tableData" :loading="loading" />
    </n-card>

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" title="编辑发送配置" style="width: 600px">
      <n-form :model="formData" label-placement="left" label-width="100px">
        <n-divider title-placement="left">发送渠道</n-divider>
        <n-form-item label="站内信">
          <n-switch v-model:value="formData.channels.site" />
          <span class="switch-label">启用后，通知将显示在用户的通知中心</span>
        </n-form-item>
        <n-form-item label="邮件通知">
          <n-switch v-model:value="formData.channels.email" />
          <span class="switch-label">启用后，将发送邮件通知</span>
        </n-form-item>
        <n-form-item v-if="formData.channels.email" label="邮件模板">
          <n-select v-model:value="formData.email_template_id" :options="templateOptions" placeholder="选择邮件模板" clearable />
        </n-form-item>
        <n-form-item label="短信通知">
          <n-switch v-model:value="formData.channels.sms" disabled />
          <span class="switch-label">短信通知功能开发中</span>
        </n-form-item>

        <n-divider title-placement="left">重试策略</n-divider>
        <n-form-item label="启用重试">
          <n-switch v-model:value="formData.retry_config.enabled" />
        </n-form-item>
        <n-form-item v-if="formData.retry_config.enabled" label="最大重试次数">
          <n-input-number v-model:value="formData.retry_config.max_retries" :min="1" :max="10" />
        </n-form-item>
        <n-form-item v-if="formData.retry_config.enabled" label="重试间隔(秒)">
          <n-input-number v-model:value="formData.retry_config.retry_interval" :min="10" :max="3600" />
        </n-form-item>

        <n-divider title-placement="left">频率限制</n-divider>
        <n-form-item label="启用限制">
          <n-switch v-model:value="formData.rate_limit.enabled" />
        </n-form-item>
        <n-form-item v-if="formData.rate_limit.enabled" label="每小时最大数">
          <n-input-number v-model:value="formData.rate_limit.max_per_hour" :min="1" :max="1000" />
        </n-form-item>

        <n-divider title-placement="left">静默时段</n-divider>
        <n-form-item label="启用静默">
          <n-switch v-model:value="formData.silent_period.enabled" />
          <span class="switch-label">静默时段内不发送通知</span>
        </n-form-item>
        <n-form-item v-if="formData.silent_period.enabled" label="静默时段">
          <n-space>
            <n-time-picker v-model:formatted-value="formData.silent_period.start_time" format="HH:mm" value-format="HH:mm" />
            <span>至</span>
            <n-time-picker v-model:formatted-value="formData.silent_period.end_time" format="HH:mm" value-format="HH:mm" />
          </n-space>
        </n-form-item>

        <n-form-item label="启用配置">
          <n-switch v-model:value="formData.is_enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleSubmit">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import { NButton, NSpace, NTag, useMessage } from 'naive-ui'
import { requestV2 } from '@/utils/http/v2-interceptors'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const templateOptions = ref([])
const showModal = ref(false)
const editingId = ref(null)

const formData = reactive({
  channels: { site: true, email: false, sms: false },
  email_template_id: null,
  retry_config: { enabled: true, max_retries: 3, retry_interval: 60 },
  rate_limit: { enabled: false, max_per_hour: 100 },
  silent_period: { enabled: false, start_time: '22:00', end_time: '08:00' },
  is_enabled: true,
})

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '通知类型', key: 'type_name', width: 120 },
  {
    title: '发送渠道',
    key: 'channels',
    render: (row) => {
      const channels = row.channels || {}
      const tags = []
      if (channels.site) tags.push(h(NTag, { type: 'info', size: 'small' }, () => '站内信'))
      if (channels.email) tags.push(h(NTag, { type: 'success', size: 'small' }, () => '邮件'))
      if (channels.sms) tags.push(h(NTag, { type: 'warning', size: 'small' }, () => '短信'))
      return h(NSpace, { size: 'small' }, () => tags.length ? tags : [h(NTag, { type: 'default', size: 'small' }, () => '无')])
    },
  },
  {
    title: '重试策略',
    key: 'retry_config',
    render: (row) => {
      const config = row.retry_config || {}
      return config.enabled ? `最多${config.max_retries}次，间隔${config.retry_interval}秒` : '未启用'
    },
  },
  {
    title: '静默时段',
    key: 'silent_period',
    render: (row) => {
      const config = row.silent_period || {}
      return config.enabled ? `${config.start_time} - ${config.end_time}` : '未启用'
    },
  },
  {
    title: '状态',
    key: 'is_enabled',
    width: 80,
    render: (row) => h(NTag, { type: row.is_enabled ? 'success' : 'default', size: 'small' }, () => row.is_enabled ? '启用' : '禁用'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await requestV2.get('/notification-configs')
    if (res.success && res.data) {
      tableData.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载发送配置失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  try {
    const res = await requestV2.get('/email-templates', { params: { is_enabled: true } })
    if (res.success && res.data) {
      const items = res.data.items || res.data || []
      templateOptions.value = items.map((t) => ({ label: t.name, value: t.id }))
    }
  } catch (error) {
    console.error('加载邮件模板失败:', error)
  }
}

const handleEdit = (row) => {
  editingId.value = row.id
  Object.assign(formData, {
    channels: row.channels || { site: true, email: false, sms: false },
    email_template_id: row.email_template_id,
    retry_config: row.retry_config || { enabled: true, max_retries: 3, retry_interval: 60 },
    rate_limit: row.rate_limit || { enabled: false, max_per_hour: 100 },
    silent_period: row.silent_period || { enabled: false, start_time: '22:00', end_time: '08:00' },
    is_enabled: row.is_enabled !== false,
  })
  showModal.value = true
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await requestV2.put(`/notification-configs/${editingId.value}`, formData)
    message.success('保存成功')
    showModal.value = false
    loadData()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
  loadTemplates()
})
</script>

<style scoped>
.send-config-page {
  padding: 16px;
}
.switch-label {
  margin-left: 12px;
  color: #999;
  font-size: 12px;
}
</style>
