<template>
  <CommonPage show-footer title="通知管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="16" class="mr-5" />
        新建通知
      </NButton>
    </template>

    <!-- 搜索栏 -->
    <NCard class="mb-15" size="small">
      <div class="flex flex-wrap items-center gap-15">
        <QueryBarItem label="通知类型" :label-width="70">
          <NSelect
            v-model:value="queryParams.notification_type"
            :options="typeOptions"
            placeholder="全部类型"
            clearable
            style="width: 130px"
          />
        </QueryBarItem>
        <QueryBarItem label="发布状态" :label-width="70">
          <NSelect
            v-model:value="queryParams.is_published"
            :options="publishedOptions"
            placeholder="全部状态"
            clearable
            style="width: 120px"
          />
        </QueryBarItem>
        <QueryBarItem label="关键词" :label-width="60">
          <NInput
            v-model:value="queryParams.search"
            placeholder="标题"
            clearable
            style="width: 150px"
          />
        </QueryBarItem>
        <NButton type="primary" @click="loadData">
          <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />
          查询
        </NButton>
        <NButton @click="handleReset">
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />
          重置
        </NButton>
      </div>
    </NCard>

    <!-- 通知列表 -->
    <NCard>
      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="tableData"
          :pagination="pagination"
          :bordered="false"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </NSpin>
    </NCard>

    <!-- 新建/编辑弹窗 -->
    <NModal
      v-model:show="modalVisible"
      :title="modalTitle"
      preset="card"
      style="width: 700px"
      :mask-closable="false"
    >
      <NForm
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        :label-width="80"
      >
        <NFormItem label="标题" path="title">
          <NInput v-model:value="formData.title" placeholder="请输入通知标题" />
        </NFormItem>

        <NFormItem label="类型" path="notification_type">
          <NSelect
            v-model:value="formData.notification_type"
            :options="NotificationTypeOptions"
            placeholder="请选择通知类型"
          />
        </NFormItem>

        <NFormItem label="级别" path="level">
          <NSelect
            v-model:value="formData.level"
            :options="NotificationLevelOptions"
            placeholder="请选择通知级别"
          />
        </NFormItem>

        <NFormItem label="发送范围" path="scope">
          <NSelect
            v-model:value="formData.scope"
            :options="NotificationScopeOptions"
            placeholder="请选择发送范围"
          />
        </NFormItem>

        <NFormItem label="内容" path="content">
          <NInput
            v-model:value="formData.content"
            type="textarea"
            placeholder="请输入通知内容"
            :rows="4"
          />
        </NFormItem>

        <NFormItem label="跳转链接">
          <NInput v-model:value="formData.link_url" placeholder="可选，点击通知后跳转的链接" />
        </NFormItem>

        <NFormItem label="过期时间">
          <NDatePicker
            v-model:value="formData.expire_time"
            type="datetime"
            clearable
            style="width: 100%"
          />
        </NFormItem>

        <NFormItem label="立即发布">
          <NSwitch v-model:value="formData.is_published" />
        </NFormItem>
      </NForm>

      <template #footer>
        <div class="flex justify-end gap-10">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">保存</NButton>
        </div>
      </template>
    </NModal>
  </CommonPage>
</template>

<script setup>
import { ref, reactive, h, onMounted } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NTag,
  NDatePicker,
  NSpin,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import {
  notificationApi,
  NotificationTypeOptions,
  NotificationLevelOptions,
  NotificationScopeOptions,
} from '@/api/notification'
import { formatDate } from '@/utils'

const message = useMessage()

// 状态
const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const modalVisible = ref(false)
const modalTitle = ref('')
const isEdit = ref(false)
const formRef = ref(null)

// 查询参数
const queryParams = reactive({
  notification_type: null,
  is_published: null,
  search: '',
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

// 选项
const typeOptions = [
  { label: '全部', value: null },
  ...NotificationTypeOptions,
]

const publishedOptions = [
  { label: '全部', value: null },
  { label: '已发布', value: true },
  { label: '未发布', value: false },
]

// 表单数据
const formData = reactive({
  title: '',
  content: '',
  notification_type: 'announcement',
  level: 'info',
  scope: 'all',
  link_url: '',
  expire_time: null,
  is_published: true,
})

// 表单验证规则
const formRules = {
  title: { required: true, message: '请输入标题', trigger: 'blur' },
  notification_type: { required: true, message: '请选择类型', trigger: 'change' },
}

// 表格列定义
const columns = [
  { title: '标题', key: 'title', width: 200, ellipsis: { tooltip: true } },
  {
    title: '类型',
    key: 'notification_type',
    width: 100,
    render: (row) => {
      const type = NotificationTypeOptions.find((t) => t.value === row.notification_type)
      return type?.label || row.notification_type
    },
  },
  {
    title: '级别',
    key: 'level',
    width: 80,
    render: (row) => {
      const levelMap = { info: 'default', warning: 'warning', error: 'error' }
      const level = NotificationLevelOptions.find((l) => l.value === row.level)
      return h(NTag, { type: levelMap[row.level] || 'default', size: 'small' }, () => level?.label || row.level)
    },
  },
  {
    title: '范围',
    key: 'scope',
    width: 90,
    render: (row) => {
      const scope = NotificationScopeOptions.find((s) => s.value === row.scope)
      return scope?.label || row.scope
    },
  },
  {
    title: '状态',
    key: 'is_published',
    width: 80,
    render: (row) =>
      h(NTag, { type: row.is_published ? 'success' : 'default', size: 'small' }, () =>
        row.is_published ? '已发布' : '未发布'
      ),
  },
  {
    title: '发布时间',
    key: 'publish_time',
    width: 160,
    render: (row) => (row.publish_time ? formatDate(row.publish_time, 'YYYY-MM-DD HH:mm') : '-'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) =>
      h('div', { class: 'flex gap-5' }, [
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
        row.is_published
          ? h(NButton, { size: 'small', type: 'warning', onClick: () => handleUnpublish(row) }, () => '撤回')
          : h(NButton, { size: 'small', type: 'success', onClick: () => handlePublish(row) }, () => '发布'),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row) },
          {
            trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'),
            default: () => '确定删除该通知吗？',
          }
        ),
      ]),
  },
]

// 方法
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryParams,
    }
    Object.keys(params).forEach((key) => {
      if (params[key] === null || params[key] === '') delete params[key]
    })

    const res = await notificationApi.list(params)
    if (res.success && res.data) {
      tableData.value = res.data.items || res.data || []
      pagination.itemCount = res.data.total || tableData.value.length
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryParams.notification_type = null
  queryParams.is_published = null
  queryParams.search = ''
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadData()
}

const resetForm = () => {
  formData.title = ''
  formData.content = ''
  formData.notification_type = 'announcement'
  formData.level = 'info'
  formData.scope = 'all'
  formData.link_url = ''
  formData.expire_time = null
  formData.is_published = true
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  modalTitle.value = '新建通知'
  modalVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  modalTitle.value = '编辑通知'
  Object.assign(formData, {
    id: row.id,
    title: row.title,
    content: row.content,
    notification_type: row.notification_type,
    level: row.level,
    scope: row.scope,
    link_url: row.link_url,
    expire_time: row.expire_time ? new Date(row.expire_time).getTime() : null,
    is_published: row.is_published,
  })
  modalVisible.value = true
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const data = {
      ...formData,
      expire_time: formData.expire_time ? new Date(formData.expire_time).toISOString() : null,
    }

    let res
    if (isEdit.value) {
      res = await notificationApi.update(formData.id, data)
    } else {
      res = await notificationApi.create(data)
    }

    if (res.success) {
      message.success(isEdit.value ? '更新成功' : '创建成功')
      modalVisible.value = false
      loadData()
    } else {
      message.error(res.message || '操作失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handlePublish = async (row) => {
  try {
    const res = await notificationApi.publish(row.id)
    if (res.success) {
      message.success('发布成功')
      loadData()
    }
  } catch (error) {
    console.error('发布失败:', error)
    message.error('发布失败')
  }
}

const handleUnpublish = async (row) => {
  try {
    const res = await notificationApi.unpublish(row.id)
    if (res.success) {
      message.success('撤回成功')
      loadData()
    }
  } catch (error) {
    console.error('撤回失败:', error)
    message.error('撤回失败')
  }
}

const handleDelete = async (row) => {
  try {
    const res = await notificationApi.delete(row.id)
    if (res.success) {
      message.success('删除成功')
      loadData()
    }
  } catch (error) {
    console.error('删除失败:', error)
    message.error('删除失败')
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>
