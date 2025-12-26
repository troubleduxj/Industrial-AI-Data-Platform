<template>
  <div class="email-server-page">
    <n-card title="邮件服务器配置">
      <template #header-extra>
        <n-button type="primary" @click="handleCreate">
          <template #icon><n-icon><PlusOutlined /></n-icon></template>
          新增服务器
        </n-button>
      </template>

      <n-data-table :columns="columns" :data="tableData" :loading="loading" />
    </n-card>

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 600px">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="100px">
        <n-form-item label="配置名称" path="name">
          <n-input v-model:value="formData.name" placeholder="如：公司邮箱服务器" />
        </n-form-item>
        <n-form-item label="SMTP服务器" path="host">
          <n-input v-model:value="formData.host" placeholder="如：smtp.example.com" />
        </n-form-item>
        <n-form-item label="端口" path="port">
          <n-input-number v-model:value="formData.port" :min="1" :max="65535" style="width: 100%" />
        </n-form-item>
        <n-form-item label="加密方式">
          <n-select v-model:value="formData.encryption" :options="encryptionOptions" />
        </n-form-item>
        <n-form-item label="用户名">
          <n-input v-model:value="formData.username" placeholder="SMTP认证用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="formData.password" type="password" show-password-on="click" placeholder="SMTP认证密码" />
        </n-form-item>
        <n-form-item label="发件人邮箱" path="from_email">
          <n-input v-model:value="formData.from_email" placeholder="如：noreply@example.com" />
        </n-form-item>
        <n-form-item label="发件人名称">
          <n-input v-model:value="formData.from_name" placeholder="如：系统通知" />
        </n-form-item>
        <n-form-item label="设为默认">
          <n-switch v-model:value="formData.is_default" />
        </n-form-item>
        <n-form-item label="启用">
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

    <!-- 测试弹窗 -->
    <n-modal v-model:show="showTestModal" preset="card" title="测试邮件服务器" style="width: 400px">
      <n-form label-placement="left" label-width="100px">
        <n-form-item label="测试邮箱">
          <n-input v-model:value="testEmail" placeholder="输入接收测试邮件的邮箱" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTestModal = false">取消</n-button>
          <n-button type="primary" :loading="testing" @click="handleTest">发送测试</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import { NButton, NSpace, NTag, NPopconfirm, useMessage } from 'naive-ui'
import { AddOutline as PlusOutlined } from '@vicons/ionicons5'
import { requestV2 } from '@/utils/http/v2-interceptors'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const testing = ref(false)
const tableData = ref([])
const showModal = ref(false)
const showTestModal = ref(false)
const modalTitle = ref('新增服务器')
const editingId = ref(null)
const testServerId = ref(null)
const testEmail = ref('')
const formRef = ref(null)

const encryptionOptions = [
  { label: '无加密', value: 'none' },
  { label: 'SSL', value: 'ssl' },
  { label: 'TLS', value: 'tls' },
]

const formData = reactive({
  name: '',
  host: '',
  port: 587,
  encryption: 'tls',
  username: '',
  password: '',
  from_email: '',
  from_name: '',
  is_default: false,
  is_enabled: true,
})

const formRules = {
  name: { required: true, message: '请输入配置名称', trigger: 'blur' },
  host: { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' },
  port: { required: true, type: 'number', message: '请输入端口号', trigger: 'blur' },
  from_email: { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
}

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '配置名称', key: 'name', width: 150 },
  { title: 'SMTP服务器', key: 'host' },
  { title: '端口', key: 'port', width: 80 },
  { title: '加密', key: 'encryption', width: 80 },
  { title: '发件人', key: 'from_email', ellipsis: { tooltip: true } },
  {
    title: '默认',
    key: 'is_default',
    width: 70,
    render: (row) => h(NTag, { type: row.is_default ? 'success' : 'default', size: 'small' }, () => row.is_default ? '是' : '否'),
  },
  {
    title: '状态',
    key: 'test_status',
    width: 80,
    render: (row) => {
      const statusMap = { untested: { text: '未测试', type: 'default' }, success: { text: '正常', type: 'success' }, failed: { text: '失败', type: 'error' } }
      const status = statusMap[row.test_status] || statusMap.untested
      return h(NTag, { type: status.type, size: 'small' }, () => status.text)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h(NSpace, {}, () => [
        h(NButton, { size: 'small', onClick: () => openTestModal(row.id) }, () => '测试'),
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, { trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'), default: () => '确定删除？' }),
      ])
    },
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await requestV2.get('/email-servers')
    if (res.success && res.data) {
      tableData.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载邮件服务器列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  editingId.value = null
  modalTitle.value = '新增服务器'
  Object.assign(formData, { name: '', host: '', port: 587, encryption: 'tls', username: '', password: '', from_email: '', from_name: '', is_default: false, is_enabled: true })
  showModal.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  modalTitle.value = '编辑服务器'
  Object.assign(formData, { ...row, password: '' })
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    if (editingId.value) {
      await requestV2.put(`/email-servers/${editingId.value}`, formData)
      message.success('更新成功')
    } else {
      await requestV2.post('/email-servers', formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadData()
  } catch (error) {
    if (error.message) message.error(error.message)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await requestV2.delete(`/email-servers/${id}`)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

const openTestModal = (id) => {
  testServerId.value = id
  testEmail.value = ''
  showTestModal.value = true
}

const handleTest = async () => {
  if (!testEmail.value) {
    message.warning('请输入测试邮箱')
    return
  }
  testing.value = true
  try {
    const res = await requestV2.post(`/email-servers/${testServerId.value}/test?test_email=${encodeURIComponent(testEmail.value)}`)
    if (res.success) {
      message.success('测试邮件已发送，请检查收件箱')
      showTestModal.value = false
      loadData()
    } else {
      message.error(res.message || '测试失败')
    }
  } catch (error) {
    message.error(error.message || '测试失败')
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.email-server-page {
  padding: 16px;
}
</style>
