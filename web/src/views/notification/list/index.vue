<template>
  <div class="notification-list-page">
    <n-card title="通知列表">
      <template #header-extra>
        <n-space>
          <n-input v-model:value="searchText" placeholder="搜索通知标题" clearable style="width: 200px" @keyup.enter="handleSearch">
            <template #prefix>
              <n-icon><SearchOutlined /></n-icon>
            </template>
          </n-input>
          <n-select v-model:value="filterType" placeholder="通知类型" clearable style="width: 120px" :options="typeOptions" @update:value="handleSearch" />
          <n-button type="primary" @click="handleCreate">
            <template #icon><n-icon><PlusOutlined /></n-icon></template>
            新增通知
          </n-button>
        </n-space>
      </template>

      <n-data-table :columns="columns" :data="tableData" :loading="loading" :pagination="pagination" remote @update:page="handlePageChange" />
    </n-card>

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" style="width: 700px">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="80px">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="formData.title" placeholder="请输入通知标题" />
        </n-form-item>
        <n-form-item label="类型" path="notification_type">
          <n-select v-model:value="formData.notification_type" :options="typeOptions" placeholder="请选择通知类型" />
        </n-form-item>
        <n-form-item label="级别" path="level">
          <n-select v-model:value="formData.level" :options="levelOptions" placeholder="请选择通知级别" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input v-model:value="formData.content" type="textarea" :rows="5" placeholder="请输入通知内容" />
        </n-form-item>
        <n-form-item label="跳转链接">
          <n-input v-model:value="formData.link_url" placeholder="可选，点击通知后跳转的链接" />
        </n-form-item>
        <n-form-item label="发送范围" path="scope">
          <n-select v-model:value="formData.scope" :options="scopeOptions" placeholder="请选择发送范围" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="handleSubmit">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import { NButton, NSpace, NTag, NPopconfirm, useMessage } from 'naive-ui'
import { SearchOutline as SearchOutlined, AddOutline as PlusOutlined } from '@vicons/ionicons5'
import { notificationApi } from '@/api/notification'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const searchText = ref('')
const filterType = ref(null)
const showModal = ref(false)
const modalTitle = ref('新增通知')
const editingId = ref(null)
const formRef = ref(null)

const typeOptions = [
  { label: '系统公告', value: 'announcement' },
  { label: '报警通知', value: 'alarm' },
  { label: '任务提醒', value: 'task' },
  { label: '系统消息', value: 'system' },
]

const levelOptions = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '错误', value: 'error' },
]

const scopeOptions = [
  { label: '全部用户', value: 'all' },
  { label: '指定角色', value: 'role' },
  { label: '指定用户', value: 'user' },
]

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

const formData = reactive({
  title: '',
  content: '',
  notification_type: 'announcement',
  level: 'info',
  scope: 'all',
  link_url: '',
})

const formRules = {
  title: { required: true, message: '请输入通知标题', trigger: 'blur' },
  content: { required: true, message: '请输入通知内容', trigger: 'blur' },
  notification_type: { required: true, message: '请选择通知类型', trigger: 'change' },
}

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  {
    title: '类型',
    key: 'notification_type',
    width: 100,
    render: (row) => {
      const typeMap = { announcement: '系统公告', alarm: '报警通知', task: '任务提醒', system: '系统消息' }
      return typeMap[row.notification_type] || row.notification_type
    },
  },
  {
    title: '级别',
    key: 'level',
    width: 80,
    render: (row) => {
      const levelMap = { info: { text: '信息', type: 'info' }, warning: { text: '警告', type: 'warning' }, error: { text: '错误', type: 'error' } }
      const level = levelMap[row.level] || { text: row.level, type: 'default' }
      return h(NTag, { type: level.type, size: 'small' }, () => level.text)
    },
  },
  {
    title: '状态',
    key: 'is_published',
    width: 80,
    render: (row) => h(NTag, { type: row.is_published ? 'success' : 'default', size: 'small' }, () => row.is_published ? '已发布' : '草稿'),
  },
  { title: '发布时间', key: 'publish_time', width: 160 },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) => {
      return h(NSpace, {}, () => [
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
        row.is_published
          ? h(NPopconfirm, { onPositiveClick: () => handleUnpublish(row.id) }, { trigger: () => h(NButton, { size: 'small', type: 'warning' }, () => '撤回'), default: () => '确定撤回此通知？' })
          : h(NPopconfirm, { onPositiveClick: () => handlePublish(row.id) }, { trigger: () => h(NButton, { size: 'small', type: 'success' }, () => '发布'), default: () => '确定发布此通知？' }),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, { trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'), default: () => '确定删除此通知？' }),
      ])
    },
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await notificationApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      notification_type: filterType.value || undefined,
    })
    if (res.success && res.data) {
      tableData.value = res.data.items || []
      pagination.itemCount = res.data.total || 0
    }
  } catch (error) {
    console.error('加载通知列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const handleCreate = () => {
  editingId.value = null
  modalTitle.value = '新增通知'
  Object.assign(formData, { title: '', content: '', notification_type: 'announcement', level: 'info', scope: 'all', link_url: '' })
  showModal.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  modalTitle.value = '编辑通知'
  Object.assign(formData, row)
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    if (editingId.value) {
      await notificationApi.update(editingId.value, formData)
      message.success('更新成功')
    } else {
      await notificationApi.create(formData)
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

const handlePublish = async (id) => {
  try {
    await notificationApi.publish(id)
    message.success('发布成功')
    loadData()
  } catch (error) {
    message.error('发布失败')
  }
}

const handleUnpublish = async (id) => {
  try {
    await notificationApi.unpublish(id)
    message.success('撤回成功')
    loadData()
  } catch (error) {
    message.error('撤回失败')
  }
}

const handleDelete = async (id) => {
  try {
    await notificationApi.delete(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.notification-list-page {
  padding: 16px;
}
</style>
