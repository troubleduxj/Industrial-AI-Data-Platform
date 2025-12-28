<template>
  <div class="ai-versions-page">
    <n-card title="模型版本管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-select v-model:value="selectedModel" :options="modelOptions" placeholder="选择模型" style="width: 200px;" @update:value="loadVersions" />
          <n-button type="primary" @click="handleCreate" :disabled="!selectedModel">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            创建版本
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="versions"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 创建版本弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" title="创建模型版本" style="width: 600px;">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100px">
        <n-form-item label="版本号" path="version">
          <n-input v-model:value="formData.version" placeholder="如: 1.0.0" />
        </n-form-item>
        <n-form-item label="模型文件" path="model_path">
          <n-input v-model:value="formData.model_path" placeholder="模型文件路径" />
        </n-form-item>
        <n-form-item label="超参数">
          <n-input v-model:value="formData.hyperparameters" type="textarea" placeholder="JSON格式的超参数配置" />
        </n-form-item>
        <n-form-item label="训练指标">
          <n-grid :cols="2" :x-gap="12">
            <n-gi>
              <n-input-number v-model:value="formData.accuracy" placeholder="准确率" :min="0" :max="1" :step="0.01" />
            </n-gi>
            <n-gi>
              <n-input-number v-model:value="formData.f1_score" placeholder="F1分数" :min="0" :max="1" :step="0.01" />
            </n-gi>
          </n-grid>
        </n-form-item>
        <n-form-item label="变更说明" path="changelog">
          <n-input v-model:value="formData.changelog" type="textarea" placeholder="版本变更说明" />
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
import { useRoute } from 'vue-router'
import { NButton, NSpace, NTag, useMessage, useDialog } from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'

const route = useRoute()
const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const versions = ref([])
const models = ref([])
const selectedModel = ref(null)
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const formData = reactive({
  version: '',
  model_path: '',
  hyperparameters: '',
  accuracy: null,
  f1_score: null,
  changelog: ''
})

const rules = {
  version: { required: true, message: '请输入版本号', trigger: 'blur' }
}

const modelOptions = computed(() => 
  models.value.map(m => ({ label: m.name, value: m.id }))
)

const statusMap = {
  created: { text: '已创建', type: 'default' },
  training: { text: '训练中', type: 'warning' },
  validated: { text: '已验证', type: 'info' },
  deployed: { text: '已部署', type: 'success' },
  archived: { text: '已归档', type: 'default' }
}

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '版本号', key: 'version' },
  { title: '模型', key: 'model_name' },
  { 
    title: '准确率', 
    key: 'accuracy', 
    width: 100,
    render: row => row.accuracy ? `${(row.accuracy * 100).toFixed(1)}%` : '-'
  },
  { 
    title: 'F1分数', 
    key: 'f1_score', 
    width: 100,
    render: row => row.f1_score ? row.f1_score.toFixed(3) : '-'
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: row => {
      const status = statusMap[row.status] || statusMap.created
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  {
    title: '是否激活',
    key: 'is_active',
    width: 80,
    render: row => h(NTag, { type: row.is_active ? 'success' : 'default' }, () => row.is_active ? '是' : '否')
  },
  { title: '创建时间', key: 'created_at', width: 180 },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', type: 'info', onClick: () => handleActivate(row), disabled: row.is_active }, () => '激活'),
      h(NButton, { size: 'small', type: 'warning', onClick: () => handleValidate(row) }, () => '验证'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleArchive(row) }, () => '归档')
    ])
  }
]

const loadModels = async () => {
  try {
    const res = await platformApi.getAIModels()
    models.value = res.data || []
    
    // 从URL参数获取模型ID
    const modelId = route.query.model_id
    if (modelId) {
      selectedModel.value = parseInt(modelId)
      loadVersions()
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const loadVersions = async () => {
  if (!selectedModel.value) {
    versions.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await platformApi.getModelVersions(selectedModel.value)
    versions.value = res.data || []
  } catch (error) {
    message.error('加载版本列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  Object.assign(formData, { 
    version: '', model_path: '', hyperparameters: '', 
    accuracy: null, f1_score: null, changelog: '' 
  })
  showModal.value = true
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const data = {
      ...formData,
      model_id: selectedModel.value,
      hyperparameters: formData.hyperparameters ? JSON.parse(formData.hyperparameters) : {},
      metrics: {
        accuracy: formData.accuracy,
        f1_score: formData.f1_score
      }
    }
    await platformApi.createModelVersion(data)
    message.success('创建成功')
    showModal.value = false
    loadVersions()
  } catch (error) {
    message.error(error.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleActivate = async (row) => {
  dialog.info({
    title: '激活版本',
    content: `确定要激活版本 "${row.version}" 吗？这将停用当前激活的版本。`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.activateModelVersion(row.id)
        message.success('激活成功')
        loadVersions()
      } catch (error) {
        message.error('激活失败')
      }
    }
  })
}

const handleValidate = async (row) => {
  message.info('开始验证模型版本...')
  try {
    await platformApi.validateModelVersion(row.id)
    message.success('验证完成')
    loadVersions()
  } catch (error) {
    message.error('验证失败')
  }
}

const handleArchive = (row) => {
  dialog.warning({
    title: '归档版本',
    content: `确定要归档版本 "${row.version}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await platformApi.archiveModelVersion(row.id)
        message.success('归档成功')
        loadVersions()
      } catch (error) {
        message.error('归档失败')
      }
    }
  })
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.ai-versions-page {
  padding: 16px;
}
</style>
