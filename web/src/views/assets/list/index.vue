<template>
  <div class="asset-list-page">
    <n-card title="资产列表" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-select v-model:value="selectedCategory" :options="categoryOptions" placeholder="选择资产类别" style="width: 200px;" clearable @update:value="loadAssets" />
          <n-input v-model:value="searchKeyword" placeholder="搜索资产名称" style="width: 200px;" clearable @keyup.enter="loadAssets">
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
          <n-button type="primary" @click="handleCreate" :disabled="!selectedCategory">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            新建资产
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="assets"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
        @update:page="handlePageChange"
      />
    </n-card>

    <!-- 创建/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 700px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="资产名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入资产名称" />
        </n-form-item>
        <n-form-item label="资产编码" path="code">
          <n-input v-model:value="formData.code" placeholder="请输入资产编码" />
        </n-form-item>
        <n-form-item label="位置" path="location">
          <n-input v-model:value="formData.location" placeholder="请输入位置" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="formData.description" type="textarea" placeholder="请输入描述" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h, computed } from 'vue'
import { NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import { AddOutline, SearchOutline } from '@vicons/ionicons5'
import { assetApi, categoryApi } from '@/api/v4'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const modalTitle = ref('新建资产')
const assets = ref([])
const categories = ref([])
const selectedCategory = ref(null)
const searchKeyword = ref('')
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const formData = reactive({
  id: null,
  name: '',
  code: '',
  location: '',
  description: '',
  category_id: null
})

const rules = {
  name: { required: true, message: '请输入资产名称', trigger: 'blur' },
  code: { required: true, message: '请输入资产编码', trigger: 'blur' }
}

const categoryOptions = computed(() => 
  categories.value.map(c => ({ label: c.name, value: c.id }))
)

const statusMap = {
  normal: { text: '正常', type: 'success' },
  warning: { text: '警告', type: 'warning' },
  error: { text: '故障', type: 'error' },
  offline: { text: '离线', type: 'default' }
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '资产名称', key: 'name' },
  { title: '资产编码', key: 'code' },
  { title: '类别', key: 'category_name' },
  { title: '位置', key: 'location' },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const status = statusMap[row.status] || statusMap.offline
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  { title: '创建时间', key: 'created_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleView(row) }, () => '查看'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadCategories = async () => {
  try {
    const res = await platformApi.getAssetCategories()
    categories.value = res.data || []
  } catch (error) {
    console.error('加载类别失败:', error)
  }
}

const loadAssets = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      category_id: selectedCategory.value,
      keyword: searchKeyword.value
    }
    const res = await assetApi.getList(params)
    assets.value = res.data?.items || []
    pagination.itemCount = res.data?.total || 0
  } catch (error) {
    message.error('加载资产列表失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  loadAssets()
}

const handleCreate = () => {
  modalTitle.value = '新建资产'
  Object.assign(formData, { 
    id: null, name: '', code: '', location: '', description: '',
    category_id: selectedCategory.value
  })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑资产'
  Object.assign(formData, row)
  showModal.value = true
}

const handleView = (row) => {
  window.$router?.push(`/assets/${row.category_code}/${row.id}`)
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await assetApi.update(formData.id, formData)
      message.success('更新成功')
    } else {
      await assetApi.create(formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadAssets()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除资产 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await assetApi.delete(row.id)
        message.success('删除成功')
        loadAssets()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadCategories()
  loadAssets()
})
</script>

<style scoped>
.asset-list-page {
  padding: 16px;
}
</style>
