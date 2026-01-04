<template>
  <div class="asset-categories-page">
    <n-card title="资产类别管理" :bordered="false">
      <template #header-extra>
        <n-button type="primary" @click="handleCreate">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          新建类别
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="categories"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 创建/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 600px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="类别名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入类别名称" />
        </n-form-item>
        <n-form-item label="类别编码" path="code">
          <n-input v-model:value="formData.code" placeholder="请输入类别编码" :disabled="!!formData.id" />
        </n-form-item>
        <n-form-item label="所属行业" path="industry">
          <n-select v-model:value="formData.industry" :options="industryOptions" placeholder="请选择行业" />
        </n-form-item>
        <n-form-item label="图标" path="icon">
          <IconPicker v-model:value="formData.icon" />
        </n-form-item>
        <n-form-item label="颜色" path="color">
          <n-color-picker v-model:value="formData.color" :show-alpha="false" />
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
import { ref, reactive, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import { categoryApi } from '@/api/v4'
import IconPicker from '@/components/icon/IconPicker.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const modalTitle = ref('新建资产类别')
const categories = ref([])
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const formData = reactive({
  id: null,
  name: '',
  code: '',
  industry: '',
  icon: '',
  description: ''
})

const rules = {
  name: { required: true, message: '请输入类别名称', trigger: 'blur' },
  code: { required: true, message: '请输入类别编码', trigger: 'blur' },
  industry: { required: true, message: '请选择行业', trigger: 'change' }
}

const industryOptions = [
  { label: '制造业', value: 'manufacturing' },
  { label: '能源', value: 'energy' },
  { label: '化工', value: 'chemical' },
  { label: '通用', value: 'general' }
]

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { 
    title: '图标', 
    key: 'icon', 
    width: 60, 
    align: 'center',
    render: row => row.icon ? h(TheIcon, { icon: row.icon, size: 20, color: row.color }) : '-' 
  },
  { title: '类别名称', key: 'name' },
  { title: '类别编码', key: 'code' },
  { title: '行业', key: 'industry', render: row => h(NTag, { type: 'info' }, () => row.industry) },
  { title: '信号数量', key: 'signal_count', width: 100 },
  { title: '资产数量', key: 'asset_count', width: 100 },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: row => h(NTag, { type: row.is_active ? 'success' : 'default' }, () => row.is_active ? '启用' : '禁用')
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleSignals(row) }, () => '信号定义'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadCategories = async () => {
  loading.value = true
  try {
    const res = await assetCategoryApi.getList()
    categories.value = res.data || []
  } catch (error) {
    message.error('加载资产类别失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  modalTitle.value = '新建资产类别'
  Object.assign(formData, { id: null, name: '', code: '', industry: '', icon: '', color: '#1890ff', description: '' })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑资产类别'
  Object.assign(formData, { ...row, color: row.color || '#1890ff' })
  showModal.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await assetCategoryApi.update(formData.id, formData)
      message.success('更新成功')
    } else {
      await assetCategoryApi.create(formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadCategories()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除该资产类别吗？删除后不可恢复。',
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await categoryApi.delete(row.id)
          message.success('删除成功')
          loadCategories()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

const handleSignals = (row) => {
  // 跳转到信号定义页面
  window.$router?.push(`/assets/categories/${row.id}/signals`)
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.asset-categories-page {
  padding: 16px;
}
</style>
