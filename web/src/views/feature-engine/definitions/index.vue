<template>
  <div class="feature-definitions-page">
    <n-card title="特征定义管理" :bordered="false">
      <template #header-extra>
        <n-button type="primary" @click="handleCreate">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          新建特征
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="features"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 创建/编辑弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 700px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="特征名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入特征名称" />
        </n-form-item>
        <n-form-item label="特征编码" path="code">
          <n-input v-model:value="formData.code" placeholder="请输入特征编码" />
        </n-form-item>
        <n-form-item label="数据源" path="source_signal">
          <n-input v-model:value="formData.source_signal" placeholder="源信号名称" />
        </n-form-item>
        <n-form-item label="聚合函数" path="aggregation">
          <n-select v-model:value="formData.aggregation" :options="aggregationOptions" placeholder="选择聚合函数" />
        </n-form-item>
        <n-form-item label="时间窗口" path="window_size">
          <n-input-group>
            <n-input-number v-model:value="formData.window_size" :min="1" style="width: 150px;" />
            <n-select v-model:value="formData.window_unit" :options="windowUnitOptions" style="width: 100px;" />
          </n-input-group>
        </n-form-item>
        <n-form-item label="DSL表达式">
          <n-input v-model:value="formData.dsl_expression" type="textarea" :rows="4" placeholder="特征DSL表达式" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="formData.description" type="textarea" placeholder="请输入描述" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="info" @click="handleValidate" :loading="validating">验证DSL</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const validating = ref(false)
const showModal = ref(false)
const modalTitle = ref('新建特征定义')
const features = ref([])
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
  source_signal: '',
  aggregation: '',
  window_size: 5,
  window_unit: 'minute',
  dsl_expression: '',
  description: ''
})

const rules = {
  name: { required: true, message: '请输入特征名称', trigger: 'blur' },
  code: { required: true, message: '请输入特征编码', trigger: 'blur' },
  source_signal: { required: true, message: '请输入数据源', trigger: 'blur' },
  aggregation: { required: true, message: '请选择聚合函数', trigger: 'change' }
}

const aggregationOptions = [
  { label: '平均值 (AVG)', value: 'avg' },
  { label: '最大值 (MAX)', value: 'max' },
  { label: '最小值 (MIN)', value: 'min' },
  { label: '求和 (SUM)', value: 'sum' },
  { label: '计数 (COUNT)', value: 'count' },
  { label: '标准差 (STDDEV)', value: 'stddev' },
  { label: '方差 (VARIANCE)', value: 'variance' },
  { label: '首值 (FIRST)', value: 'first' },
  { label: '末值 (LAST)', value: 'last' }
]

const windowUnitOptions = [
  { label: '秒', value: 'second' },
  { label: '分钟', value: 'minute' },
  { label: '小时', value: 'hour' },
  { label: '天', value: 'day' }
]

const statusMap = {
  draft: { text: '草稿', type: 'default' },
  active: { text: '激活', type: 'success' },
  disabled: { text: '禁用', type: 'warning' }
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '特征名称', key: 'name' },
  { title: '特征编码', key: 'code' },
  { title: '数据源', key: 'source_signal' },
  { title: '聚合函数', key: 'aggregation' },
  { title: '时间窗口', key: 'window', render: row => `${row.window_size} ${row.window_unit}` },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: row => {
      const status = statusMap[row.status] || statusMap.draft
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleToggle(row) }, () => row.status === 'active' ? '禁用' : '激活'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadFeatures = async () => {
  loading.value = true
  try {
    const res = await platformApi.getFeatureDefinitions()
    features.value = res.data || []
  } catch (error) {
    message.error('加载特征定义失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  modalTitle.value = '新建特征定义'
  Object.assign(formData, { 
    id: null, name: '', code: '', source_signal: '', 
    aggregation: '', window_size: 5, window_unit: 'minute',
    dsl_expression: '', description: '' 
  })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑特征定义'
  Object.assign(formData, row)
  showModal.value = true
}

const handleValidate = async () => {
  validating.value = true
  try {
    const dsl = formData.dsl_expression || generateDSL()
    await platformApi.validateFeatureDSL({ dsl })
    message.success('DSL验证通过')
  } catch (error) {
    message.error(error.message || 'DSL验证失败')
  } finally {
    validating.value = false
  }
}

const generateDSL = () => {
  return `${formData.aggregation}(${formData.source_signal}, ${formData.window_size}${formData.window_unit[0]})`
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data = {
      ...formData,
      dsl_expression: formData.dsl_expression || generateDSL()
    }
    if (formData.id) {
      await platformApi.updateFeatureDefinition(formData.id, data)
      message.success('更新成功')
    } else {
      await platformApi.createFeatureDefinition(data)
      message.success('创建成功')
    }
    showModal.value = false
    loadFeatures()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleToggle = async (row) => {
  try {
    const newStatus = row.status === 'active' ? 'disabled' : 'active'
    await platformApi.updateFeatureDefinition(row.id, { status: newStatus })
    message.success('状态更新成功')
    loadFeatures()
  } catch (error) {
    message.error('状态更新失败')
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除特征定义 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.deleteFeatureDefinition(row.id)
        message.success('删除成功')
        loadFeatures()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadFeatures()
})
</script>

<style scoped>
.feature-definitions-page {
  padding: 16px;
}
</style>
