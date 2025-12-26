<template>
  <div class="field-mapping">
    <!-- 查询条件 -->
    <n-card :bordered="false" class="mb-4">
      <n-space>
        <n-input
          v-model:value="queryParams.search"
          placeholder="搜索字段或列名"
          clearable
          style="width: 250px"
        >
          <template #prefix>
            <n-icon :component="SearchOutline" />
          </template>
        </n-input>
        
        <n-select
          v-model:value="queryParams.device_type_code"
          placeholder="选择设备类型"
          clearable
          style="width: 200px"
          :options="deviceTypeOptions"
          @update:value="handleSearchDeviceTypeChange"
        />
        
        <n-input
          v-model:value="queryParams.tdengine_table"
          placeholder="TDengine表名"
          clearable
          style="width: 200px"
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
        
        <n-button 
          type="error" 
          @click="handleBatchDelete"
          :disabled="checkedRowKeys.length === 0"
        >
          <template #icon>
            <n-icon :component="TrashOutline" />
          </template>
          批量删除
        </n-button>

        <n-button type="success" @click="handleCreate">
          <template #icon>
            <n-icon :component="AddOutline" />
          </template>
          新增映射
        </n-button>
      </n-space>
    </n-card>

    <!-- 字段映射列表 -->
    <n-card :bordered="false">
      <n-data-table
        remote
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="mappingList"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 新增/编辑对话框 -->
    <n-modal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="width: 800px"
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
        label-width="140px"
      >
        <n-form-item label="设备类型" path="device_type_code">
          <n-select
            v-model:value="formData.device_type_code"
            placeholder="选择设备类型"
            :options="deviceTypeOptions"
            @update:value="handleDeviceTypeChange"
          />
        </n-form-item>
        
        <n-form-item label="字段定义" path="device_field_id">
          <n-select
            v-model:value="formData.device_field_id"
            placeholder="选择字段"
            :options="fieldOptions"
            filterable
            :loading="loadingFields"
            @update:value="handleFieldChange"
          />
          <n-text v-if="formData.device_type_code && fieldOptions.length === 0" depth="3" type="warning" class="mt-1">
            该设备类型下暂无可用字段，请先在"字段定义管理"中创建字段
          </n-text>
        </n-form-item>
        
        <n-divider title-placement="left">TDengine 配置</n-divider>
        
        <n-form-item label="数据库名" path="tdengine_database">
          <n-input v-model:value="formData.tdengine_database" placeholder="例如: devicemonitor" />
        </n-form-item>
        
        <n-form-item label="表名" path="tdengine_stable">
          <n-input v-model:value="formData.tdengine_stable" placeholder="例如: weld_realtime_data" />
        </n-form-item>
        
        <n-form-item label="列名" path="tdengine_column">
          <n-input v-model:value="formData.tdengine_column" placeholder="例如: voltage" />
        </n-form-item>
        
        <n-form-item label="是否TAG列">
          <n-switch v-model:value="formData.is_tag" />
          <n-text depth="3" class="ml-2">TAG列用于分组和索引</n-text>
        </n-form-item>
        
        <n-divider title-placement="left">数据转换规则</n-divider>
        
        <n-form-item label="转换类型">
          <n-select
            v-model:value="transformType"
            placeholder="选择转换类型"
            :options="transformTypeOptions"
            @update:value="handleTransformTypeChange"
          />
        </n-form-item>
        
        <!-- 表达式转换 -->
        <n-form-item 
          v-if="transformType === 'expression'" 
          label="转换表达式"
        >
          <n-input
            v-model:value="transformConfig.expression"
            placeholder="例如: value * 1.5 + 10"
            type="textarea"
            :rows="2"
          />
          <n-text depth="3" size="small" class="mt-1">
            使用 'value' 代表原始值，支持数学运算
          </n-text>
        </n-form-item>
        
        <!-- 映射转换 -->
        <n-form-item 
          v-if="transformType === 'mapping'" 
          label="值映射表"
        >
          <n-dynamic-input
            v-model:value="transformConfig.mappings"
            :on-create="() => ({ from: '', to: '' })"
          >
            <template #default="{ value }">
              <div style="display: flex; gap: 12px; align-items: center; width: 100%">
                <n-input v-model:value="value.from" placeholder="原始值" />
                <span>→</span>
                <n-input v-model:value="value.to" placeholder="转换后值" />
              </div>
            </template>
          </n-dynamic-input>
        </n-form-item>
        
        <!-- 范围限制 -->
        <n-form-item 
          v-if="transformType === 'range_limit'" 
          label="范围限制"
        >
          <div style="display: flex; gap: 12px; align-items: center">
            <n-input-number v-model:value="transformConfig.min" placeholder="最小值" style="flex: 1" />
            <span>到</span>
            <n-input-number v-model:value="transformConfig.max" placeholder="最大值" style="flex: 1" />
          </div>
        </n-form-item>
        
        <!-- 单位转换 -->
        <n-form-item 
          v-if="transformType === 'unit'" 
          label="单位转换"
        >
          <n-space vertical style="width: 100%">
            <div style="display: flex; gap: 12px">
              <n-input v-model:value="transformConfig.from_unit" placeholder="原始单位" style="flex: 1" />
              <n-input v-model:value="transformConfig.to_unit" placeholder="目标单位" style="flex: 1" />
            </div>
            <n-input-number 
              v-model:value="transformConfig.factor" 
              placeholder="转换系数" 
              :step="0.1"
              style="width: 100%"
            />
          </n-space>
        </n-form-item>
        
        <!-- 四舍五入 -->
        <n-form-item 
          v-if="transformType === 'round'" 
          label="小数位数"
        >
          <n-input-number 
            v-model:value="transformConfig.decimals" 
            :min="0" 
            :max="10"
            placeholder="保留小数位数"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { NButton, NTag, NSpace, useMessage, useDialog } from 'naive-ui'
import { SearchOutline, RefreshOutline, AddOutline, TrashOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'
import { deviceTypeApi } from '@/api/device-shared'

const message = useMessage()
const dialog = useDialog()

// 查询参数
const queryParams = reactive({
  search: '',
  device_type_code: null,
  tdengine_table: null,
  is_active: true
})

// 数据
const mappingList = ref([])
const loading = ref(false)
const checkedRowKeys = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page) => {
    pagination.page = page
    fetchMappingList()
  },
  onUpdatePageSize: (pageSize) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchMappingList()
  }
})

// 设备类型选项
const deviceTypeOptions = ref([])
const deviceTypeMap = ref({})

// 获取设备类型列表
const fetchDeviceTypes = async () => {
  try {
    const res = await deviceTypeApi.list({ limit: 100 })
    const list = res.data?.items || res.data?.data || res.data || []
    if (Array.isArray(list)) {
      deviceTypeOptions.value = list.map(item => ({
        label: item.type_name,
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

const handleSearchDeviceTypeChange = (value) => {
  if (value && deviceTypeMap.value[value]) {
    queryParams.tdengine_table = deviceTypeMap.value[value].tdengine_stable_name
  } else {
    queryParams.tdengine_table = null
  }
}

// 字段选项
const fieldOptions = ref([])
const loadingFields = ref(false)

// 转换类型选项
const transformTypeOptions = [
  { label: '无转换', value: null },
  { label: '表达式转换', value: 'expression' },
  { label: '值映射', value: 'mapping' },
  { label: '范围限制', value: 'range_limit' },
  { label: '单位转换', value: 'unit' },
  { label: '四舍五入', value: 'round' },
]

// 表格列定义
const columns = [
  { type: 'selection' },
  { title: 'ID', key: 'id', width: 80 },
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
    title: '字段名称',
    key: 'field_name',
    width: 150,
    render(row) {
      // 优先使用返回的字段信息
      if (row.field_name) {
        return row.field_name
      }
      // 尝试从device_field对象获取
      if (row.device_field && row.device_field.field_name) {
        return row.device_field.field_name
      }
      // 显示字段ID作为后备
      return row.device_field_id ? `字段ID: ${row.device_field_id}` : '-'
    }
  },
  {
    title: '字段代码',
    key: 'field_code',
    width: 150,
    render(row) {
      if (row.field_code) {
        return row.field_code
      }
      if (row.device_field && row.device_field.field_code) {
        return row.device_field.field_code
      }
      return '-'
    }
  },
  {
    title: 'TDengine数据库',
    key: 'tdengine_database',
    width: 150
  },
  {
    title: 'TDengine表',
    key: 'tdengine_stable',
    width: 150
  },
  {
    title: 'TDengine列',
    key: 'tdengine_column',
    width: 120
  },
  {
    title: 'TAG列',
    key: 'is_tag',
    width: 80,
    render(row) {
      return h(NTag, { 
        type: row.is_tag ? 'success' : 'default',
        size: 'small'
      }, { default: () => row.is_tag ? '是' : '否' })
    }
  },
  {
    title: '转换规则',
    key: 'transform_rule',
    width: 120,
    render(row) {
      if (!row.transform_rule) {
        return h(NTag, { type: 'default', size: 'small' }, { default: () => '无' })
      }
      const type = row.transform_rule.type || '未知'
      return h(NTag, { type: 'info', size: 'small' }, { default: () => type })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    render(row) {
      return h(NSpace, null, {
        default: () => [
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
const modalTitle = computed(() => formData.id ? '编辑字段映射' : '新增字段映射')
const formRef = ref(null)
const saving = ref(false)

const formData = reactive({
  id: null,
  device_type_code: null,
  device_field_id: null,
  tdengine_database: 'devicemonitor',
  tdengine_stable: '',
  tdengine_column: '',
  is_tag: false,
  transform_rule: null
})

const formRules = {
  device_type_code: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  device_field_id: [
    { required: true, message: '请选择字段', trigger: 'change' }
  ],
  tdengine_database: [
    { required: true, message: '请输入TDengine数据库名', trigger: 'blur' }
  ],
  tdengine_table: [
    { required: true, message: '请输入TDengine表名', trigger: 'blur' }
  ],
  tdengine_column: [
    { required: true, message: '请输入TDengine列名', trigger: 'blur' }
  ]
}

// 转换规则
const transformType = ref(null)
const transformConfig = reactive({
  // expression
  expression: '',
  // mapping
  mappings: [],
  // range_limit
  min: null,
  max: null,
  // unit
  from_unit: '',
  to_unit: '',
  factor: 1.0,
  // round
  decimals: 2
})

// 方法
const fetchMappingList = async () => {
  loading.value = true
  try {
    const response = await dataModelApi.getMappings({
      ...queryParams,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    
    if (response.success) {
      mappingList.value = response.data || []
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

const fetchFieldOptions = async (deviceTypeCode) => {
  if (!deviceTypeCode) {
    fieldOptions.value = []
    return
  }
  
  loadingFields.value = true
  try {
    const response = await dataModelApi.getFields({ 
      device_type_code: deviceTypeCode,
      is_active: true,
      page: 1,
      page_size: 1000
    })
    if (response.success) {
      fieldOptions.value = (response.data || []).map(field => ({
        label: `${field.field_name} (${field.field_code})`,
        value: field.id
      }))
    } else {
      message.error(response.message || '获取字段列表失败')
      fieldOptions.value = []
    }
  } catch (error) {
    message.error('获取字段列表失败：' + (error.message || '未知错误'))
    fieldOptions.value = []
  } finally {
    loadingFields.value = false
  }
}

const handleQuery = () => {
  pagination.page = 1
  fetchMappingList()
}

const handleReset = () => {
  queryParams.search = ''
  queryParams.device_type_code = null
  queryParams.tdengine_table = null
  handleQuery()
}

const handleCreate = () => {
  Object.assign(formData, {
    id: null,
    device_type_code: null,
    device_field_id: null,
    tdengine_database: 'devicemonitor',
    tdengine_table: '',
    tdengine_column: '',
    is_tag: false,
    transform_rule: null
  })
  transformType.value = null
  Object.assign(transformConfig, {
    expression: '',
    mappings: [],
    min: null,
    max: null,
    from_unit: '',
    to_unit: '',
    factor: 1.0,
    decimals: 2
  })
  showModal.value = true
}

const handleDeviceTypeChange = async (deviceTypeCode) => {
  // 清空字段选择
  formData.device_field_id = null
  
  // 加载该设备类型的字段列表
  if (deviceTypeCode) {
    await fetchFieldOptions(deviceTypeCode)
  } else {
    fieldOptions.value = []
  }
}

const handleEdit = async (id) => {
  try {
    const response = await dataModelApi.getMapping(id)
    if (response.success) {
      const mapping = response.data
      Object.assign(formData, mapping)
      
      // 先加载字段选项，然后再设置选中值
      if (mapping.device_type_code) {
        await fetchFieldOptions(mapping.device_type_code)
      }
      
      // 解析转换规则
      if (mapping.transform_rule) {
        transformType.value = mapping.transform_rule.type
        Object.assign(transformConfig, mapping.transform_rule.config || {})
      } else {
        transformType.value = null
      }
      
      showModal.value = true
    } else {
      message.error(response.message || '获取映射详情失败')
    }
  } catch (error) {
    message.error('获取映射详情失败：' + (error.message || '未知错误'))
  }
}

const handleDelete = (id) => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个字段映射吗？此操作不可恢复。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const response = await dataModelApi.deleteMapping(id)
        if (response.success) {
          message.success('删除成功')
          fetchMappingList()
        } else {
          message.error(response.message || '删除失败')
        }
      } catch (error) {
        message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handleFieldChange = (fieldId) => {
  // 字段改变时，可以自动填充一些默认值
}

const handleTransformTypeChange = (type) => {
  // 重置转换配置
  Object.assign(transformConfig, {
    expression: '',
    mappings: [],
    min: null,
    max: null,
    from_unit: '',
    to_unit: '',
    factor: 1.0,
    decimals: 2
  })
}

const buildTransformRule = () => {
  if (!transformType.value) {
    return null
  }
  
  const config = {}
  
  switch (transformType.value) {
    case 'expression':
      config.expression = transformConfig.expression
      break
    case 'mapping':
      config.mappings = transformConfig.mappings
      break
    case 'range_limit':
      config.min = transformConfig.min
      config.max = transformConfig.max
      break
    case 'unit':
      config.from_unit = transformConfig.from_unit
      config.to_unit = transformConfig.to_unit
      config.factor = transformConfig.factor
      break
    case 'round':
      config.decimals = transformConfig.decimals
      break
  }
  
  return {
    type: transformType.value,
    config: config
  }
}

const handleBatchDelete = () => {
  if (checkedRowKeys.value.length === 0) return
  
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 条映射吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        loading.value = true
        const res = await dataModelApi.batchDeleteMappingsByIds(checkedRowKeys.value)
        if (res.success) {
          message.success(res.message)
          checkedRowKeys.value = []
          fetchMappingList()
        } else {
          message.error(res.message || '删除失败')
        }
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    }
  })
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    
    saving.value = true
    
    // 构建请求数据
    const requestData = {
      ...formData,
      transform_rule: buildTransformRule()
    }
    
    const response = formData.id 
      ? await dataModelApi.updateMapping(formData.id, requestData)
      : await dataModelApi.createMapping(requestData)
    
    if (response.success) {
      message.success(formData.id ? '更新成功' : '创建成功')
      showModal.value = false
      fetchMappingList()
    } else {
      message.error(response.message || '保存失败')
    }
  } catch (error) {
    if (error.errors) {
      message.error('请检查表单填写')
    } else {
      message.error('保存失败：' + (error.message || '未知错误'))
    }
  } finally {
    saving.value = false
  }
}

// 生命周期
onMounted(() => {
  fetchMappingList()
  fetchDeviceTypes()
})
</script>

<style scoped>
.field-mapping {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.mt-1 {
  margin-top: 4px;
  display: block;
}
</style>

