<template>
  <div class="ai-models-page">
    <n-card title="AI模型管理" :bordered="false">
      <template #header-extra>
        <n-button type="primary" @click="handleCreate">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          注册模型
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="models"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 注册模型弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 650px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="模型名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入模型名称" />
        </n-form-item>
        <n-form-item label="模型类型" path="model_type">
          <n-select v-model:value="formData.model_type" :options="modelTypeOptions" placeholder="请选择模型类型" />
        </n-form-item>
        <n-form-item label="算法框架" path="framework">
          <n-select v-model:value="formData.framework" :options="frameworkOptions" placeholder="请选择算法框架" />
        </n-form-item>
        <n-form-item label="输入特征" path="input_features">
          <n-dynamic-tags v-model:value="formData.input_features" />
        </n-form-item>
        <n-form-item label="输出目标" path="output_targets">
          <n-dynamic-tags v-model:value="formData.output_targets" />
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
import { platformApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const modalTitle = ref('注册模型')
const models = ref([])
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
  model_type: '',
  framework: '',
  input_features: [],
  output_targets: [],
  description: ''
})

const rules = {
  name: { required: true, message: '请输入模型名称', trigger: 'blur' },
  model_type: { required: true, message: '请选择模型类型', trigger: 'change' },
  framework: { required: true, message: '请选择算法框架', trigger: 'change' }
}

const modelTypeOptions = [
  { label: '异常检测', value: 'anomaly_detection' },
  { label: '预测性维护', value: 'predictive_maintenance' },
  { label: '时序预测', value: 'time_series_forecast' },
  { label: '分类', value: 'classification' },
  { label: '回归', value: 'regression' }
]

const frameworkOptions = [
  { label: 'Isolation Forest', value: 'isolation_forest' },
  { label: 'ARIMA', value: 'arima' },
  { label: 'XGBoost', value: 'xgboost' },
  { label: 'LSTM', value: 'lstm' },
  { label: 'Prophet', value: 'prophet' }
]

const statusMap = {
  registered: { text: '已注册', type: 'default' },
  training: { text: '训练中', type: 'warning' },
  ready: { text: '就绪', type: 'success' },
  deployed: { text: '已部署', type: 'info' },
  deprecated: { text: '已废弃', type: 'error' }
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '模型名称', key: 'name' },
  { title: '模型类型', key: 'model_type' },
  { title: '算法框架', key: 'framework' },
  { title: '版本数', key: 'version_count', width: 80 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const status = statusMap[row.status] || statusMap.registered
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  { title: '创建时间', key: 'created_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleVersions(row) }, () => '版本'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleDeploy(row) }, () => '部署'),
      h(NButton, { size: 'small', type: 'warning', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

const loadModels = async () => {
  loading.value = true
  try {
    const res = await platformApi.getAIModels()
    models.value = res.data || []
  } catch (error) {
    message.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  modalTitle.value = '注册模型'
  Object.assign(formData, { 
    id: null, name: '', model_type: '', framework: '', 
    input_features: [], output_targets: [], description: '' 
  })
  showModal.value = true
}

const handleEdit = (row) => {
  modalTitle.value = '编辑模型'
  Object.assign(formData, {
    ...row,
    input_features: row.input_features || [],
    output_targets: row.output_targets || []
  })
  showModal.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (formData.id) {
      await platformApi.updateAIModel(formData.id, formData)
      message.success('更新成功')
    } else {
      await platformApi.registerAIModel(formData)
      message.success('注册成功')
    }
    showModal.value = false
    loadModels()
  } catch (error) {
    message.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除模型 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
        try {
          await platformApi.delete(row.id)
          message.success('删除成功')
          loadModels()
        } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

const handleVersions = (row) => {
  window.$router?.push(`/ai-engine/versions?model_id=${row.id}`)
}

const handleDeploy = async (row) => {
  dialog.info({
    title: '部署模型',
    content: `确定要部署模型 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.deployAIModel(row.id)
        message.success('部署成功')
        loadModels()
      } catch (error) {
        message.error('部署失败')
      }
    }
  })
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.ai-models-page {
  padding: 16px;
}
</style>
