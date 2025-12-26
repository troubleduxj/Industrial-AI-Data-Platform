<template>
  <div class="email-template-page">
    <n-card title="邮件模板">
      <template #header-extra>
        <n-space>
          <n-select v-model:value="filterType" placeholder="模板类型" clearable style="width: 120px" :options="typeOptions" @update:value="loadData" />
          <n-button type="primary" @click="handleCreate">
            <template #icon><n-icon><PlusOutlined /></n-icon></template>
            新增模板
          </n-button>
        </n-space>
      </template>

      <n-data-table :columns="columns" :data="tableData" :loading="loading" />
    </n-card>

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 900px">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="100px">
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="模板代码" path="code">
              <n-input v-model:value="formData.code" :disabled="!!editingId" placeholder="唯一标识，如：alarm_notification" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="模板名称" path="name">
              <n-input v-model:value="formData.name" placeholder="如：报警通知模板" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="模板类型" path="template_type">
              <n-select v-model:value="formData.template_type" :options="typeOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="启用">
              <n-switch v-model:value="formData.is_enabled" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="邮件主题" path="subject">
          <n-input v-model:value="formData.subject" placeholder="支持变量，如：【报警通知】{{rule_name}}" />
        </n-form-item>
        <n-form-item label="邮件内容" path="content">
          <n-input v-model:value="formData.content" type="textarea" :rows="12" placeholder="HTML格式，支持变量如 {{device_name}}" />
        </n-form-item>
        <n-form-item label="可用变量">
          <n-dynamic-input v-model:value="formData.variables" :on-create="() => ({ name: '', description: '' })">
            <template #default="{ value }">
              <n-space>
                <n-input v-model:value="value.name" placeholder="变量名" style="width: 150px" />
                <n-input v-model:value="value.description" placeholder="变量说明" style="width: 200px" />
              </n-space>
            </template>
          </n-dynamic-input>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="handlePreview">预览</n-button>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleSubmit">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 预览弹窗 -->
    <n-modal v-model:show="showPreview" preset="card" title="模板预览" style="width: 700px">
      <div class="preview-container" v-html="previewContent"></div>
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
const tableData = ref([])
const filterType = ref(null)
const showModal = ref(false)
const showPreview = ref(false)
const previewContent = ref('')
const modalTitle = ref('新增模板')
const editingId = ref(null)
const formRef = ref(null)

const typeOptions = [
  { label: '报警通知', value: 'alarm' },
  { label: '系统公告', value: 'announcement' },
  { label: '任务提醒', value: 'task' },
  { label: '自定义', value: 'custom' },
]

const formData = reactive({
  code: '',
  name: '',
  subject: '',
  content: '',
  template_type: 'custom',
  is_enabled: true,
  variables: [],
})

const formRules = {
  code: { required: true, message: '请输入模板代码', trigger: 'blur' },
  name: { required: true, message: '请输入模板名称', trigger: 'blur' },
  subject: { required: true, message: '请输入邮件主题', trigger: 'blur' },
  content: { required: true, message: '请输入邮件内容', trigger: 'blur' },
}

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '模板代码', key: 'code', width: 180 },
  { title: '模板名称', key: 'name', width: 150 },
  { title: '邮件主题', key: 'subject', ellipsis: { tooltip: true } },
  {
    title: '类型',
    key: 'template_type',
    width: 100,
    render: (row) => {
      const typeMap = { alarm: '报警通知', announcement: '系统公告', task: '任务提醒', custom: '自定义' }
      return typeMap[row.template_type] || row.template_type
    },
  },
  {
    title: '系统预设',
    key: 'is_system',
    width: 80,
    render: (row) => h(NTag, { type: row.is_system ? 'info' : 'default', size: 'small' }, () => row.is_system ? '是' : '否'),
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
    width: 150,
    render: (row) => {
      return h(NSpace, {}, () => [
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
        !row.is_system && h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, { trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'), default: () => '确定删除？' }),
      ])
    },
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await requestV2.get('/email-templates', { params: { template_type: filterType.value || undefined } })
    if (res.success && res.data) {
      tableData.value = res.data.items || res.data || []
    }
  } catch (error) {
    console.error('加载邮件模板列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  editingId.value = null
  modalTitle.value = '新增模板'
  Object.assign(formData, { code: '', name: '', subject: '', content: '', template_type: 'custom', is_enabled: true, variables: [] })
  showModal.value = true
}

const handleEdit = async (row) => {
  editingId.value = row.id
  modalTitle.value = '编辑模板'
  try {
    const res = await requestV2.get(`/email-templates/${row.id}`)
    if (res.success && res.data) {
      Object.assign(formData, res.data)
    }
  } catch (error) {
    message.error('获取模板详情失败')
  }
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    if (editingId.value) {
      await requestV2.put(`/email-templates/${editingId.value}`, formData)
      message.success('更新成功')
    } else {
      await requestV2.post('/email-templates', formData)
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
    await requestV2.delete(`/email-templates/${id}`)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

const handlePreview = () => {
  // 简单预览，用示例数据替换变量
  let content = formData.content
  formData.variables.forEach((v) => {
    content = content.replace(new RegExp(`\\{\\{${v.name}\\}\\}`, 'g'), `[${v.description || v.name}]`)
  })
  previewContent.value = content
  showPreview.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.email-template-page {
  padding: 16px;
}
.preview-container {
  border: 1px solid #eee;
  padding: 16px;
  background: #fff;
  max-height: 500px;
  overflow-y: auto;
}
</style>
