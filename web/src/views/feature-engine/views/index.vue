<template>
  <div class="feature-views-page">
    <n-card title="特征视图管理" :bordered="false">
      <template #header-extra>
        <n-button type="primary" @click="handleCreate">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          新建视图
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="views"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 创建/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 700px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="视图名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入视图名称" />
        </n-form-item>
        <n-form-item label="视图编码" path="code">
          <n-input v-model:value="formData.code" placeholder="请输入视图编码" />
        </n-form-item>
        <n-form-item label="关联资产类别" path="category_id">
          <n-select v-model:value="formData.category_id" :options="categoryOptions" placeholder="选择资产类别" />
        </n-form-item>
        <n-form-item label="包含特征" path="feature_ids">
          <n-select v-model:value="formData.feature_ids" :options="featureOptions" multiple placeholder="选择特征" />
        </n-form-item>
        <n-form-item label="刷新间隔">
          <n-input-group>
            <n-input-number v-model:value="formData.refresh_interval" :min="1" style="width: 150px;" />
            <n-select v-model:value="formData.refresh_unit" :options="refreshUnitOptions" style="width: 100px;" />
          </n-input-group>
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

    <!-- 查看数据弹窗 -->
    <n-modal v-model:show="showDataModal" preset="dialog" title="特征数据" style="width: 900px;">
      <n-space style="margin-bottom: 16px;">
        <n-select v-model:value="dataFilter.asset_id" :options="assetOptions" placeholder="选择资产" style="width: 200px;" />
        <n-date-picker v-model:value="dataFilter.time_range" type="datetimerange" />
        <n-button @click="loadViewData">查询</n-button>
      </n-space>
      <n-data-table :columns="dataColumns" :data="viewData" :loading="dataLoading" />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h, computed } from 'vue'
import { NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const dataLoading = ref(false)
const showModal = ref(false)
const showDataModal = ref(false)
const modalTitle = ref('新建特征视图')
const views = ref([])
const categories = ref([])
const features = ref([])
const assets = ref([])
const viewData = ref([])
const currentView = ref(null)
const formRef = ref(null)

const pagination = reactive({ page: 1, pageSize: 10 })

const formData = reactive({
  id: null,
  name: '',
  code: '',
  category_id: null,
  feature_ids: [],
  refresh_interval: 60,
  refresh_unit: 'second',
  description: ''
})

const dataFilter = reactive({
  asset_id: null,
  time_range: null
})

const rules = {
  name: { required: true, message: '请输入视图名称', trigger: 'blur' },
  code: { required: true, message: '请输入视图编码', trigger: 'blur' },
  category_id: { required: true, message: '请选择资产类别', trigger: 'change' },
  feature_ids: { required: true, type: 'array', min: 1, message: '请选择至少一个特征', trigger: 'change' }
}

const refreshUnitOptions = [
  { label: '秒', value: 'second' },
  { label: '分钟', value: 'minute' },
  { label: '小时', value: 'hour' }
]

const categoryOptions = computed(() => categories.value.map(c => ({ label: c.name, value: c.id })))
const featureOptions = computed(() => features.value.map(f => ({ label: f.name, value: f.id })))
const assetOptions = computed(() => assets.value.map(a => ({ label: a.name, value: a.id })))

const dataColumns = computed(() => {
  if (!currentView.value) return []
  const cols = [
    { title: '时间', key: 'timestamp', width: 180 },
    { title: '资产', key: 'asset_name' }
  ]
  // 动态添加特征列
  currentView.value.features?.forEach(f => {
    cols.push({ title: f.name, key: f.code })
  })
  return cols
})

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '视图名称', key: 'name' },
  { title: '视图编码', key: 'code' },
  { title: '资产类别', key: 'category_name' },
  { title: '特征数量', key: 'feature_count', width: 100 },
  { title: '刷新间隔', key: 'refresh', render: row => `${row.refresh_interval} ${row.refresh_unit}` },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: row => h(NTag, { type: row.is_active ? 'success' : 'default' }, () => row.is_active ? '启用' : '禁用')
  },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleViewData(row) }, () => '查看数据'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadViews = async () => {
  loading.value = true
  try {
    const res = await platformApi.getFeatureViews()
    views.value = res.data || []
  } catch (error) {
    message.error('加载特征视图失败')
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const res = await platformApi.getAssetCategories()
    categories.value = res.data || []
  } catch (error) {
    console.error('加载类别失败:', error)
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

const loadAssets = async () => {
  try {
    const res = await platformApi.getAssets({})
    assets.value = res.data?.items || []
  } catch (error) {
    console.error('加载资产失败:', error)
  }
}

const handleCreate = () => {
  modalTitle.value = '新建特征视图'
  Object.assign(formData, { 
    id: null, name: '', code: '', category_id: null, 
    feature_ids: [], refresh_interval: 60, refresh_unit: 'second', description: '' 
  })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑特征视图'
  Object.assign(formData, {
    ...row,
    feature_ids: row.features?.map(f => f.id) || []
  })
  showModal.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await platformApi.updateFeatureView(formData.id, formData)
      message.success('更新成功')
    } else {
      await platformApi.createFeatureView(formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadViews()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除特征视图 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.deleteFeatureView(row.id)
        message.success('删除成功')
        loadViews()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

const handleViewData = (row) => {
  currentView.value = row
  dataFilter.asset_id = null
  dataFilter.time_range = null
  viewData.value = []
  showDataModal.value = true
}

const loadViewData = async () => {
  if (!currentView.value || !dataFilter.asset_id) {
    message.warning('请选择资产')
    return
  }
  dataLoading.value = true
  try {
    const res = await platformApi.getFeatureViewData(currentView.value.id, {
      asset_id: dataFilter.asset_id,
      start_time: dataFilter.time_range?.[0],
      end_time: dataFilter.time_range?.[1]
    })
    viewData.value = res.data || []
  } catch (error) {
    message.error('加载数据失败')
  } finally {
    dataLoading.value = false
  }
}

onMounted(() => {
  loadViews()
  loadCategories()
  loadFeatures()
  loadAssets()
})
</script>

<style scoped>
.feature-views-page {
  padding: 16px;
}
</style>
