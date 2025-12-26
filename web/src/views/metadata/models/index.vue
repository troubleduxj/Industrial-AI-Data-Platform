<template>
  <div class="data-model-config">
    <!-- 查询条件 -->
    <n-card :bordered="false" class="mb-4">
      <n-space>
        <n-input
          v-model:value="queryParams.search"
          placeholder="搜索模型名称或代码"
          clearable
          style="width: 250px"
        >
          <template #prefix>
            <n-icon :component="SearchOutline" />
          </template>
        </n-input>
        
        <n-select
          v-if="!embedded"
          v-model:value="queryParams.device_type_code"
          placeholder="选择设备类型"
          clearable
          filterable
          style="width: 200px"
          :options="deviceTypeOptions"
        />
        
        <n-select
          v-model:value="queryParams.model_type"
          placeholder="选择模型类型"
          clearable
          style="width: 180px"
          :options="modelTypeOptions"
        />
        
        <n-button type="primary" @click="handleQuery">
          <template #icon>
            <n-icon :component="SearchOutline" />
          </template>
          查询
        </n-button>
        
        <n-button @click="handleReset">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
          重置
        </n-button>
        
        <n-button type="success" @click="handleCreate">
          <template #icon>
            <n-icon :component="AddOutline" />
          </template>
          新建模型
        </n-button>
      </n-space>
    </n-card>

    <!-- 数据模型列表 -->
    <n-card :bordered="false">
      <n-data-table
        remote
        :columns="columns"
        :data="modelList"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 新建/编辑对话框 -->
    <n-modal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="width: 900px"
      :segmented="{
        content: 'soft',
        footer: 'soft'
      }"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="120px"
      >
        <n-form-item label="模型名称" path="model_name">
          <n-input v-model:value="formData.model_name" placeholder="请输入模型名称" />
        </n-form-item>
        
        <n-form-item label="模型代码" path="model_code">
          <n-input v-model:value="formData.model_code" placeholder="请输入模型代码（唯一标识）" />
        </n-form-item>
        
        <n-form-item label="设备类型" path="device_type_code">
          <n-select
            v-model:value="formData.device_type_code"
            placeholder="选择设备类型"
            :options="deviceTypeOptions"
            @update:value="handleDeviceTypeChange"
          />
        </n-form-item>
        
        <n-form-item label="模型类型" path="model_type">
          <n-select
            v-model:value="formData.model_type"
            placeholder="选择模型类型"
            :options="modelTypeOptions"
          />
        </n-form-item>
        
        <n-form-item label="版本" path="version">
          <n-input v-model:value="formData.version" placeholder="请输入版本号" />
        </n-form-item>
        
        <n-form-item label="模型说明" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入模型说明"
            :rows="3"
          />
        </n-form-item>
        
        <n-form-item label="选择字段" path="selected_fields">
          <div style="width: 100%">
            <n-space justify="space-between" class="mb-2">
              <n-text depth="3">从下方选择需要的字段，或</n-text>
              <n-button
                size="small"
                type="info"
                @click="handleQuickSync"
                :disabled="!formData.device_type_code"
              >
                <template #icon>
                  <n-icon :component="CloudDownloadOutline" />
                </template>
                从TDengine同步字段
              </n-button>
            </n-space>
            <n-transfer
              v-model:value="selectedFieldCodes"
              :options="availableFields"
              source-title="可用字段"
              target-title="已选字段"
              source-filterable
            />
          </div>
        </n-form-item>

        <n-form-item 
          v-if="formData.model_type === 'statistics'" 
          label="聚合配置" 
          path="aggregation_config"
        >
          <AggregationConfigEditor
            v-model:value="formData.aggregation_config"
            :fields="selectedFieldOptions"
          />
        </n-form-item>

        <n-form-item 
          v-if="formData.model_type === 'ai_analysis'" 
          label="AI 配置" 
          path="ai_config"
        >
          <AiConfigEditor
            v-model:value="formData.ai_config"
            :fields="selectedFieldOptions"
          />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSave" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>
    <!-- 预览对话框 -->
    <n-modal
      v-model:show="showPreviewModal"
      title="模型预览"
      preset="card"
      style="width: 800px"
    >
      <n-tabs type="line" animated>
        <n-tab-pane name="basic" tab="基本信息">
          <n-descriptions bordered :column="2">
            <n-descriptions-item label="模型名称">{{ previewData.model_name }}</n-descriptions-item>
            <n-descriptions-item label="模型代码">
              <n-tag :bordered="false">{{ previewData.model_code }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="设备类型">
              {{ deviceTypeMap[previewData.device_type_code]?.type_name || previewData.device_type_code }}
            </n-descriptions-item>
            <n-descriptions-item label="模型类型">
              <n-tag :type="getModelTypeTag(previewData.model_type).type">
                {{ getModelTypeTag(previewData.model_type).label }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="版本">{{ previewData.version }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="previewData.is_active ? 'success' : 'error'">
                {{ previewData.is_active ? '已激活' : '已停用' }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="说明" :span="2">{{ previewData.description || '-' }}</n-descriptions-item>
          </n-descriptions>
        </n-tab-pane>
        <n-tab-pane name="fields" tab="包含字段">
          <n-data-table
            :columns="previewFieldColumns"
            :data="previewData.selected_fields || []"
            :pagination="false"
            max-height="400"
            size="small"
          />
        </n-tab-pane>
        <n-tab-pane name="json" tab="JSON结构">
          <n-code :code="JSON.stringify(previewData, null, 2)" language="json" word-wrap />
        </n-tab-pane>
      </n-tabs>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showPreviewModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h, watch } from 'vue'
import { 
  NButton, NTag, NSpace, NSwitch, useMessage, useDialog, 
  NDescriptions, NDescriptionsItem, NCode, NDataTable, NModal, NTabs, NTabPane, NForm, NFormItem, NInput, NSelect, NTransfer, NText, NIcon
} from 'naive-ui'
import { SearchOutline, RefreshOutline, AddOutline, CreateOutline, TrashOutline, EyeOutline, CloudDownloadOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'
import { deviceTypeApi } from '@/api/device-shared'
import AggregationConfigEditor from './components/AggregationConfigEditor.vue'
import AiConfigEditor from './components/AiConfigEditor.vue'

const props = defineProps({
  deviceTypeCode: {
    type: String,
    default: null
  },
  embedded: {
    type: Boolean,
    default: false
  }
})

const message = useMessage()
const dialog = useDialog()

// 查询参数
const queryParams = reactive({
  search: '',
  device_type_code: null,
  model_type: null,
  is_active: true
})

// 监听 prop 变化
watch(() => props.deviceTypeCode, (newVal) => {
  // 即使 newVal 为 null，也应该允许查询（显示所有模型）
  // 如果是 embedded 模式，则强制使用 props.deviceTypeCode
  // 否则，只有当 newVal 有值时才更新 queryParams.device_type_code
  if (props.embedded) {
    queryParams.device_type_code = newVal
    fetchModelList()
  } else if (newVal) {
    queryParams.device_type_code = newVal
    fetchModelList()
  }
}, { immediate: true })

// 数据
const modelList = ref([])
const loading = ref(false)
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page) => {
    pagination.page = page
    fetchModelList()
  },
  onUpdatePageSize: (pageSize) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchModelList()
  }
})

// 设备类型选项
const deviceTypeOptions = ref([])
const deviceTypeMap = ref({})

// 获取设备类型列表
const fetchDeviceTypes = async () => {
  try {
    const res = await deviceTypeApi.list({ limit: 100, is_active: true })
    const list = res.data?.items || res.data?.data || res.data || []
    if (Array.isArray(list)) {
      deviceTypeOptions.value = list.map(item => ({
        label: `${item.type_name} (${item.type_code})`, // 显示代码以便区分
        value: item.type_code,
        tdengine_stable_name: item.tdengine_stable_name
      }))
      
      // 构建映射字典
      const map = {}
      list.forEach(item => {
        map[item.type_code] = item
      })
      deviceTypeMap.value = map
    }
  } catch (error) {
    console.error('获取设备类型失败', error)
  }
}

// 模型类型选项
const modelTypeOptions = [
  { label: '实时监控', value: 'realtime' },
  { label: '统计分析', value: 'statistics' },
  { label: 'AI分析', value: 'ai_analysis' }
]

// 表格列定义
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '模型名称',
    key: 'model_name',
    width: 200
  },
  {
    title: '模型代码',
    key: 'model_code',
    width: 200
  },
  {
    title: '设备类型',
    key: 'device_type_code',
    width: 120,
    render(row) {
      if (row.device_type_code && deviceTypeMap.value[row.device_type_code]) {
        return deviceTypeMap.value[row.device_type_code].type_name
      }
      return row.device_type_code || '-'
    }
  },
  {
    title: '模型类型',
    key: 'model_type',
    width: 120,
    render(row) {
      const typeMap = {
        realtime: { label: '实时监控', type: 'info' },
        statistics: { label: '统计分析', type: 'success' },
        ai_analysis: { label: 'AI分析', type: 'warning' }
      }
      const config = typeMap[row.model_type] || { label: row.model_type, type: 'default' }
      return h(NTag, { type: config.type }, { default: () => config.label })
    }
  },
  {
    title: '版本',
    key: 'version',
    width: 80
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render(row) {
      return h(NSwitch, {
        value: row.is_active,
        onUpdateValue: (value) => handleToggleActive(row.id, value)
      })
    }
  },
  {
    title: '默认模型',
    key: 'is_default',
    width: 100,
    render(row) {
      return row.is_default ? h(NTag, { type: 'success' }, { default: () => '是' }) : h(NTag, { type: 'default' }, { default: () => '否' })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render(row) {
      return h(NSpace, null, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            onClick: () => handlePreview(row.id)
          }, { default: () => '预览' }),
          h(NButton, {
            size: 'small',
            type: 'info',
            onClick: () => handleEdit(row.id)
          }, { default: () => '编辑' }),
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row.id)
          }, { default: () => '删除' })
        ]
      })
    }
  }
]

// 表单相关
const showModal = ref(false)
const modalTitle = computed(() => formData.id ? '编辑数据模型' : '新建数据模型')
const formRef = ref(null)
const saving = ref(false)

const formData = reactive({
  id: null,
  model_name: '',
  model_code: '',
  device_type_code: null,
  model_type: null,
  version: '1.0',
  description: '',
  selected_fields: [],
  aggregation_config: null,
  ai_config: null
})

const formRules = {
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  model_code: [
    { required: true, message: '请输入模型代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '模型代码只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  device_type_code: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  version: [
    { required: true, message: '请输入版本号', trigger: 'blur' }
  ]
}

// 可用字段
const availableFields = ref([])
const selectedFieldCodes = ref([])

// 选中的字段选项（用于编辑器）
const selectedFieldOptions = computed(() => {
  return availableFields.value.filter(f => selectedFieldCodes.value.includes(f.value))
})

// 方法
const fetchModelList = async () => {
  loading.value = true
  try {
    const response = await dataModelApi.getModels({
      ...queryParams,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    
    if (response.success) {
      modelList.value = response.data || []
      pagination.itemCount = response.meta?.total || response.total || 0
    } else {
      message.error(response.message || '查询失败')
    }
  } catch (error) {
    message.error('查询失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  pagination.page = 1
  fetchModelList()
}

const handleReset = () => {
  queryParams.search = ''
  queryParams.device_type_code = null
  queryParams.model_type = null
  queryParams.is_active = true
  handleQuery()
}

const handleCreate = () => {
  Object.assign(formData, {
    id: null,
    model_name: '',
    model_code: '',
    device_type_code: null,
    model_type: null,
    version: '1.0',
    description: '',
    selected_fields: [],
    aggregation_config: null,
    ai_config: null
  })
  selectedFieldCodes.value = []
  availableFields.value = []
  showModal.value = true
}

const handleEdit = async (id) => {
  try {
    availableFields.value = [] // 清空旧数据
    const response = await dataModelApi.getModel(id)
    if (response.success) {
      const model = response.data
      Object.assign(formData, model)
      selectedFieldCodes.value = (model.selected_fields || []).map(f => f.field_code)
      
      // 加载可用字段
      if (model.device_type_code) {
        handleDeviceTypeChange(model.device_type_code)
      }
      
      showModal.value = true
    } else {
      message.error(response.message || '获取模型详情失败')
    }
  } catch (error) {
    message.error('获取模型详情失败：' + (error.message || '未知错误'))
  }
}

const handleDelete = (id) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个数据模型吗？此操作不可恢复。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const response = await dataModelApi.deleteModel(id)
        if (response.success) {
          message.success('删除成功')
          fetchModelList()
        } else {
          message.error(response.message || '删除失败')
        }
      } catch (error) {
        message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handlePreview = async (id) => {
  previewLoading.value = true
  try {
    const response = await dataModelApi.getModel(id)
    if (response.success) {
      previewData.value = response.data
      showPreviewModal.value = true
    } else {
      message.error(response.message || '获取模型详情失败')
    }
  } catch (error) {
    message.error('获取模型详情失败：' + (error.message || '未知错误'))
  } finally {
    previewLoading.value = false
  }
}

const getModelTypeTag = (type) => {
  const typeMap = {
    realtime: { label: '实时监控', type: 'info' },
    statistics: { label: '统计分析', type: 'success' },
    ai_analysis: { label: 'AI分析', type: 'warning' }
  }
  return typeMap[type] || { label: type, type: 'default' }
}

const showPreviewModal = ref(false)
const previewLoading = ref(false)
const previewData = ref({})
const previewFieldColumns = [
  { title: '字段代码', key: 'field_code' },
  { title: '字段别名', key: 'alias' },
  { 
    title: '必填', 
    key: 'is_required',
    render: (row) => row.is_required ? h(NTag, { type: 'error', size: 'small' }, { default: () => '是' }) : '否'
  },
  { title: '权重', key: 'weight' }
]

const handleToggleActive = async (id, value) => {
  try {
    const response = await dataModelApi.activateModel(id, value)
    if (response.success) {
      message.success(value ? '已激活' : '已停用')
      fetchModelList()
    } else {
      message.error(response.message || '操作失败')
      fetchModelList() // 刷新数据以恢复状态
    }
  } catch (error) {
    message.error('操作失败：' + (error.message || '未知错误'))
    fetchModelList() // 刷新数据以恢复状态
  }
}

const handleDeviceTypeChange = async (deviceTypeCode) => {
  if (!deviceTypeCode) {
    availableFields.value = []
    return
  }
  // 加载该设备类型的可用字段
  try {
    const response = await dataModelApi.getFields({
      device_type_code: deviceTypeCode,
      is_active: true,
      page_size: 1000
    })
    
    if (response.success) {
      availableFields.value = (response.data || []).map(field => ({
        label: `${field.field_name} (${field.field_code})`,
        value: field.field_code,
        field_name: field.field_name
      }))
    } else {
      message.error(response.message || '获取字段列表失败')
    }
  } catch (error) {
    message.error('获取字段列表失败：' + (error.message || '未知错误'))
  }
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    
    saving.value = true
    
    // 构建请求数据
    const requestData = {
      ...formData,
      selected_fields: selectedFieldCodes.value.map(code => {
        const field = availableFields.value.find(f => f.value === code)
        return {
          field_code: code,
          alias: field ? field.field_name : code,
          is_required: false,
          weight: 1.0
        }
      })
    }
    
    const response = formData.id 
      ? await dataModelApi.updateModel(formData.id, requestData)
      : await dataModelApi.createModel(requestData)
    
    if (response.success) {
      message.success(formData.id ? '更新成功' : '创建成功')
      showModal.value = false
      fetchModelList()
    } else {
      message.error(response.message || '保存失败')
    }
  } catch (error) {
    if (error.errors) {
      // 表单验证错误
      message.error('请检查表单填写')
    } else {
      message.error('保存失败：' + (error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

const handleQuickSync = () => {
  // 跳转到字段定义管理页面，并打开同步对话框
  const device_type = formData.device_type_code
  message.info('请前往"字段定义管理"页面进行同步操作')
  
  // 可以选择跳转
  setTimeout(() => {
    window.open(`/metadata/fields?device_type=${device_type}`, '_blank')
  }, 1000)
}

// 生命周期
onMounted(() => {
  fetchModelList()
  fetchDeviceTypes()
})
</script>

<style scoped>
.data-model-config {
  padding: 16px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>

