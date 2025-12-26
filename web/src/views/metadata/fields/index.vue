<template>
  <div class="field-management">
    <!-- 查询条件 -->
    <n-card :bordered="false" class="mb-4">
      <n-space>
        <n-select
          v-if="!embedded"
          v-model:value="queryParams.device_type_code"
          placeholder="选择设备类型"
          clearable
          style="width: 200px"
          :options="deviceTypeOptions"
        />
        
        <n-select
          v-model:value="queryParams.field_category"
          placeholder="选择字段分类"
          clearable
          style="width: 180px"
          :options="fieldCategoryOptions"
        />
        
        <n-input
          v-model:value="queryParams.search"
          placeholder="搜索字段名称或代码"
          clearable
          style="width: 250px"
        >
          <template #prefix>
            <n-icon :component="SearchOutline" />
          </template>
        </n-input>
        
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
          新建字段
        </n-button>
        
        <n-button type="info" @click="handleSyncFromTDengine">
          <template #icon>
            <n-icon :component="CloudDownloadOutline" />
          </template>
          从TDengine同步
        </n-button>

        <n-button 
          type="error" 
          @click="handleBatchDelete"
          :disabled="checkedRowKeys.length === 0 && !queryParams.device_type_code"
        >
          <template #icon>
            <n-icon :component="TrashOutline" />
          </template>
          {{ checkedRowKeys.length > 0 ? `批量删除 (${checkedRowKeys.length})` : '清空分类' }}
        </n-button>

        <n-button 
          type="warning" 
          @click="handleCheckDiff"
        >
          <template #icon>
            <n-icon :component="GitCompareOutline" />
          </template>
          结构比对
        </n-button>
      </n-space>
    </n-card>

    <!-- 字段列表 -->
    <n-card :bordered="false">
      <n-data-table
        remote
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="fieldList"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.id"
      />
    </n-card>

    <!-- 新建/编辑字段对话框 -->
    <n-modal
      v-model:show="showFieldModal"
      :title="fieldModalTitle"
      preset="card"
      style="width: 800px"
    >
      <n-form
        ref="fieldFormRef"
        :model="fieldFormData"
        :rules="fieldFormRules"
        label-placement="left"
        label-width="120px"
      >
        <n-form-item label="设备类型" path="device_type_code">
          <n-select
            v-model:value="fieldFormData.device_type_code"
            placeholder="选择设备类型"
            :options="deviceTypeOptions"
          />
        </n-form-item>
        
        <n-form-item label="字段名称" path="field_name">
          <n-input v-model:value="fieldFormData.field_name" placeholder="请输入字段中文名称" />
        </n-form-item>
        
        <n-form-item label="字段代码" path="field_code">
          <n-input v-model:value="fieldFormData.field_code" placeholder="请输入字段代码（英文）" />
        </n-form-item>
        
        <n-form-item label="字段类型" path="field_type">
          <n-select
            v-model:value="fieldFormData.field_type"
            placeholder="选择字段类型"
            :options="fieldTypeOptions"
          />
        </n-form-item>
        
        <n-form-item label="字段分类" path="field_category">
          <n-select
            v-model:value="fieldFormData.field_category"
            placeholder="选择字段分类"
            :options="fieldCategoryOptions"
          />
        </n-form-item>
        
        <n-form-item label="单位">
          <n-input v-model:value="fieldFormData.unit" placeholder="如：A、V、℃" />
        </n-form-item>
        
        <n-form-item label="字段描述">
          <n-input
            v-model:value="fieldFormData.description"
            type="textarea"
            placeholder="请输入字段描述"
            :rows="3"
          />
        </n-form-item>

        <n-card title="实时监测展示配置" size="small" :bordered="true" class="bg-gray-50 mb-4">
          <n-grid :cols="2" :x-gap="24">
            <n-gi :span="2">
              <n-form-item label="监控关键字段" path="is_monitoring_key">
                <n-space align="center">
                  <n-switch v-model:value="fieldFormData.is_monitoring_key" />
                  <n-text depth="3" style="font-size: 13px">
                    勾选后，该字段将作为关键指标在卡片摘要、列表等显眼位置优先展示
                  </n-text>
                </n-space>
              </n-form-item>
            </n-gi>
            
            <n-gi>
              <n-form-item label="展示分组">
                <n-select
                  v-model:value="fieldFormData.field_group"
                  :options="fieldGroupOptions"
                  placeholder="选择或输入分组"
                  filterable
                  tag
                  clearable
                />
              </n-form-item>
            </n-gi>
            
            <n-gi>
              <n-form-item label="分组排序">
                <n-input-number v-model:value="fieldFormData.group_order" placeholder="分组内排序" />
              </n-form-item>
            </n-gi>
            
            <n-gi>
              <n-form-item label="卡片显示">
                <n-switch v-model:value="fieldFormData.is_default_visible">
                  <template #checked>显示</template>
                  <template #unchecked>隐藏</template>
                </n-switch>
              </n-form-item>
            </n-gi>
            
            <n-gi>
              <n-form-item label="全局排序">
                <n-input-number v-model:value="fieldFormData.sort_order" placeholder="全局列表排序" />
              </n-form-item>
            </n-gi>

            <n-gi>
              <n-form-item label="图标 (Emoji)">
                <n-input v-model:value="fieldFormData.display_config.icon" placeholder="输入Emoji，如 ⚡" />
              </n-form-item>
            </n-gi>
            
            <n-gi>
              <n-form-item label="显示颜色">
                <n-color-picker v-model:value="fieldFormData.display_config.color" :show-alpha="false" />
              </n-form-item>
            </n-gi>
          </n-grid>
        </n-card>
        
        <n-divider title-placement="left">高级属性</n-divider>
        
        <n-grid :cols="2">
          <n-gi>
            <n-form-item label="允许报警配置">
              <n-switch v-model:value="fieldFormData.is_alarm_enabled" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="AI特征字段">
              <n-switch v-model:value="fieldFormData.is_ai_feature" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showFieldModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveField" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- TDengine同步对话框 -->
    <n-modal
      v-model:show="showSyncModal"
      title="从TDengine同步字段"
      preset="card"
      style="width: 900px"
    >
      <n-steps :current="syncStep" :status="syncStatus">
        <n-step title="配置参数" />
        <n-step title="预览字段" />
        <n-step title="执行同步" />
      </n-steps>
      
      <!-- 步骤1: 配置参数 -->
      <div v-show="syncStep === 1" class="mt-4">
        <n-form
          ref="syncFormRef"
          :model="syncFormData"
          :rules="syncFormRules"
          label-placement="left"
          label-width="140px"
        >
          <n-form-item label="设备类型" path="device_type_code">
            <n-select
              v-model:value="syncFormData.device_type_code"
              placeholder="选择设备类型"
              :options="deviceTypeOptions"
              @update:value="handleSyncDeviceTypeChange"
            />
          </n-form-item>
          
          <n-form-item label="TDengine数据库" path="tdengine_database">
            <n-input
              v-model:value="syncFormData.tdengine_database"
              placeholder="如：device_monitor"
            />
          </n-form-item>
          
          <n-form-item label="TDengine超级表" path="tdengine_stable">
            <n-input
              v-model:value="syncFormData.tdengine_stable"
              placeholder="如：weld_data"
            />
          </n-form-item>
          
          <n-form-item label="字段分类">
            <n-select
              v-model:value="syncFormData.field_category"
              placeholder="选择字段分类"
              :options="fieldCategoryOptions"
            />
          </n-form-item>
          
          <n-form-item label="覆盖已存在字段">
             <n-switch v-model:value="syncFormData.overwrite_existing" />
             <n-text depth="3" class="ml-2">选中后将更新已存在字段的名称、类型等属性</n-text>
          </n-form-item>
        </n-form>
      </div>
      
      <!-- 步骤2: 预览字段 -->
      <div v-show="syncStep === 2" class="mt-4">
        <n-alert type="info" class="mb-4">
          <template #header>
            预览结果
          </template>
          将创建 <strong>{{ previewResult.new_fields }}</strong> 个新字段，
          跳过 <strong>{{ previewResult.existing_fields }}</strong> 个已存在字段，
          忽略 <strong>{{ previewResult.skip_fields }}</strong> 个系统字段
        </n-alert>
        
        <n-data-table
          v-model:checked-row-keys="selectedPreviewFields"
          :columns="previewColumns"
          :data="previewResult.fields"
          :max-height="400"
          :pagination="false"
          :row-key="row => row.field_code"
        />
      </div>
      
      <!-- 步骤3: 同步结果 -->
      <div v-show="syncStep === 3" class="mt-4">
        <n-result
          :status="syncStatus === 'error' ? 'error' : 'success'"
          :title="syncResultTitle"
          :description="syncResultDescription"
        >
          <template #footer>
            <n-collapse>
              <n-collapse-item title="查看详情">
                <n-tabs type="line">
                  <n-tab-pane name="created" :tab="`已创建 (${syncResult.created?.length || 0})`">
                    <n-list>
                      <n-list-item v-for="field in syncResult.created" :key="field.field_code">
                        <n-thing :title="field.field_code" :description="field.field_name">
                          <template #description>
                            {{ field.field_name }} | 类型: {{ field.field_type }}
                          </template>
                        </n-thing>
                      </n-list-item>
                    </n-list>
                  </n-tab-pane>
                  
                  <n-tab-pane name="skipped" :tab="`已跳过 (${syncResult.skipped?.length || 0})`">
                    <n-list>
                      <n-list-item v-for="field in syncResult.skipped" :key="field.field_code">
                        <n-thing :title="field.field_code">
                          <template #description>
                            原因: {{ field.reason }}
                          </template>
                        </n-thing>
                      </n-list-item>
                    </n-list>
                  </n-tab-pane>
                  
                  <n-tab-pane v-if="syncResult.errors?.length" name="errors" :tab="`失败 (${syncResult.errors?.length || 0})`">
                    <n-list>
                      <n-list-item v-for="field in syncResult.errors" :key="field.field_code">
                        <n-thing :title="field.field_code">
                          <template #description>
                            <n-text type="error">{{ field.error }}</n-text>
                          </template>
                        </n-thing>
                      </n-list-item>
                    </n-list>
                  </n-tab-pane>
                </n-tabs>
              </n-collapse-item>
            </n-collapse>
          </template>
        </n-result>
      </div>
      
      <template #footer>
        <n-space justify="end">
          <n-button v-if="syncStep > 1 && syncStep < 3" @click="syncStep--">上一步</n-button>
          <n-button @click="handleCloseSyncModal">{{ syncStep === 3 ? '完成' : '取消' }}</n-button>
          <n-button v-if="syncStep === 1" type="primary" @click="handlePreviewSync" :loading="previewing">
            下一步：预览
          </n-button>
          <n-button v-if="syncStep === 2" type="primary" @click="handleExecuteSync" :loading="syncing">
            执行同步
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 报警阈值配置抽屉 -->
    <n-drawer v-model:show="showAlarmConfigDrawer" :width="400">
      <n-drawer-content title="默认报警阈值配置">
        <n-form
          :model="alarmConfigData"
          label-placement="top"
        >
          <n-alert type="info" class="mb-4">
            为字段 <strong>{{ alarmConfigData.field_name }}</strong> 设置默认报警阈值。
            这些阈值将作为创建报警规则时的推荐值。
          </n-alert>

          <n-form-item label="警告阈值 (Warning)">
            <n-input-number v-model:value="alarmConfigData.warning" placeholder="请输入数值" clearable style="width: 100%" />
          </n-form-item>

          <n-form-item label="严重阈值 (Critical)">
            <n-input-number v-model:value="alarmConfigData.critical" placeholder="请输入数值" clearable style="width: 100%" />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showAlarmConfigDrawer = false">取消</n-button>
            <n-button type="primary" @click="handleSaveAlarmConfig" :loading="savingAlarmConfig">
              保存
            </n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <SchemaDiffModal
      v-model:show="showSchemaDiffModal"
      :device-type-code="queryParams.device_type_code"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h, watch } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NTag, NSpace, NSwitch, useMessage, NGrid, NGi, NInputNumber, NDrawer, NDrawerContent, NForm, NFormItem, NIcon, NColorPicker } from 'naive-ui'
import { 
  SearchOutline, 
  RefreshOutline, 
  AddOutline, 
  CreateOutline, 
  TrashOutline,
  CloudDownloadOutline,
  GitCompareOutline,
  EyeOutline
} from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'
import { deviceTypeApi } from '@/api/device-v2'
import { systemV2Api } from '@/api/system-v2'
// Note: Ensure this component exists in the same directory or update path
import SchemaDiffModal from './components/SchemaDiffModal.vue'

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
const route = useRoute()

// 查询参数
const queryParams = reactive({
  device_type_code: null,
  field_category: null,
  search: '',
  is_active: true
})

// 监听 prop 变化
watch(() => props.deviceTypeCode, (newVal) => {
  if (newVal) {
    queryParams.device_type_code = newVal
    handleQuery()
  }
}, { immediate: true })

// 数据
const fieldList = ref([])
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
    fetchFieldList()
  },
  onUpdatePageSize: (pageSize) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchFieldList()
  }
})

// 选项
const deviceTypeOptions = ref([])

const fetchDeviceTypes = async () => {
  try {
    const res = await deviceTypeApi.list({
      page: 1,
      page_size: 100,
      is_active: true
    })
    if (res.success) {
      deviceTypeOptions.value = res.data.map(item => ({
        label: item.type_name,
        value: item.type_code,
        tdengine_stable_name: item.tdengine_stable_name
      }))
    }
  } catch (error) {
    console.error('获取设备类型列表失败:', error)
    // 不显示错误提示，以免打断用户流程，只是下拉框为空
  }
}

const fieldCategoryOptions = [
  { label: '数据采集', value: 'data_collection' },
  { label: '维护记录', value: 'maintenance_record' },
  { label: 'AI分析', value: 'ai_analysis' }
]

const fieldTypeOptions = [
  { label: '整数', value: 'int' },
  { label: '大整数', value: 'bigint' },
  { label: '浮点数', value: 'float' },
  { label: '双精度浮点数', value: 'double' },
  { label: '字符串', value: 'string' },
  { label: '布尔值', value: 'boolean' },
  { label: '时间戳', value: 'timestamp' },
  { label: 'JSON', value: 'json' }
]

// 表格列定义
const columns = [
  { type: 'selection' },
  { title: 'ID', key: 'id', width: 80 },
  { title: '字段代码', key: 'field_code', width: 180 },
  { title: '字段名称', key: 'field_name', width: 150 },
  { 
    title: '设备类型', 
    key: 'device_type_code', 
    width: 150,
    render(row) {
      const option = deviceTypeOptions.value.find(opt => opt.value === row.device_type_code)
      return option ? option.label : row.device_type_code
    }
  },
  { 
    title: '字段类型', 
    key: 'field_type', 
    width: 100,
    render(row) {
      const typeMap = {
        int: 'info',
        float: 'success',
        double: 'success',
        string: 'default',
        boolean: 'warning'
      }
      return h(NTag, { type: typeMap[row.field_type] || 'default' }, { default: () => row.field_type })
    }
  },
  {
    title: '字段分组',
    key: 'field_group',
    width: 100,
    render(row) {
      return row.field_group ? h(NTag, { size: 'small', bordered: false }, { default: () => row.field_group }) : '-'
    }
  },
  {
    title: '卡片显示',
    key: 'is_default_visible',
    width: 80,
    render(row) {
      return row.is_default_visible ? h(NIcon, { component: EyeOutline, color: '#18a058' }) : '-'
    }
  },
  { title: '单位', key: 'unit', width: 80 },
  {
    title: '监控字段',
    key: 'is_monitoring_key',
    width: 100,
    render(row) {
      return row.is_monitoring_key ? h(NTag, { type: 'success', size: 'small' }, { default: () => '是' }) : '-'
    }
  },
  {
    title: '允许报警',
    key: 'is_alarm_enabled',
    width: 100,
    render(row) {
      return h(NSwitch, {
        value: row.is_alarm_enabled,
        disabled: !row.is_monitoring_key, // 只有监控字段才能开启报警
        onUpdateValue: (value) => handleToggleAlarmEnabled(row, value)
      })
    }
  },
  {
    title: 'AI特征',
    key: 'is_ai_feature',
    width: 100,
    render(row) {
      return row.is_ai_feature ? h(NTag, { type: 'warning', size: 'small' }, { default: () => '是' }) : '-'
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render(row) {
      return h(NSwitch, {
        value: row.is_active,
        onUpdateValue: (value) => handleToggleActive(row.id, value)
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right',
    render(row) {
      const actions = [
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
      
      // 如果已开启报警，显示配置按钮
      if (row.is_alarm_enabled) {
        actions.unshift(h(NButton, {
          size: 'small',
          type: 'warning',
          style: 'margin-right: 8px',
          onClick: () => handleOpenAlarmConfig(row)
        }, { default: () => '阈值' }))
      }
      
      return h(NSpace, null, { default: () => actions })
    }
  }
]

// 字段表单相关
const showFieldModal = ref(false)
const fieldModalTitle = computed(() => fieldFormData.id ? '编辑字段' : '新建字段')
const fieldFormRef = ref(null)
const saving = ref(false)

const fieldFormData = reactive({
  id: null,
  device_type_code: null,
  field_code: '',
  field_name: '',
  field_type: 'float',
  field_category: 'data_collection',
  field_group: 'default',
  group_order: 0,
  is_default_visible: true,
  sort_order: 0,
  unit: '',
  is_monitoring_key: false,
  is_alarm_enabled: false,
  alarm_threshold: { warning: null, critical: null },
  display_config: { icon: '', color: '' },
  is_ai_feature: false,
  description: '',
  is_active: true
})

// 报警配置抽屉
const showAlarmConfigDrawer = ref(false)
const alarmConfigData = reactive({
  id: null,
  field_name: '',
  warning: null,
  critical: null
})
const savingAlarmConfig = ref(false)


const fieldGroupOptions = computed(() => {
  // 1. 优先使用字典数据（保留标签）
  const options = [...dictGroupOptions.value]
  const existingValues = new Set(options.map(o => o.value))

  // 2. 合并现有字段中的分组（如果不在字典中，则label=value）
  fieldList.value.forEach(f => {
    if (f.field_group && !existingValues.has(f.field_group)) {
      options.push({ label: f.field_group, value: f.field_group })
      existingValues.add(f.field_group)
    }
  })

  // 3. 确保包含默认分组
  if (!existingValues.has('default')) {
    options.push({ label: 'default', value: 'default' })
  }
  
  return options
})

const fieldFormRules = {
  device_type_code: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  field_name: [{ required: true, message: '请输入字段名称', trigger: 'blur' }],
  field_code: [
    { required: true, message: '请输入字段代码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '字段代码只能包含小写字母、数字和下划线，且必须以字母开头', trigger: 'blur' }
  ],
  field_type: [{ required: true, message: '请选择字段类型', trigger: 'change' }],
  field_category: [{ required: true, message: '请选择字段分类', trigger: 'change' }]
}

// TDengine同步相关
const showSyncModal = ref(false)
const showSchemaDiffModal = ref(false)
const syncStep = ref(1)
const syncStatus = ref('process')
const previewing = ref(false)
const syncing = ref(false)
const syncFormRef = ref(null)

const syncFormData = reactive({
  device_type_code: null,
  tdengine_database: '',
  tdengine_stable: '',
  field_category: 'data_collection',
  overwrite_existing: false
})

const handleSyncDeviceTypeChange = (value, option) => {
  if (option && option.tdengine_stable_name) {
    syncFormData.tdengine_stable = option.tdengine_stable_name
    message.success(`已自动填充超级表名: ${option.tdengine_stable_name}`)
  }
}

const syncFormRules = {
  device_type_code: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  tdengine_database: [{ required: true, message: '请输入TDengine数据库名', trigger: 'blur' }],
  tdengine_stable: [{ required: true, message: '请输入TDengine超级表名', trigger: 'blur' }]
}

const previewResult = reactive({
  total_fields: 0,
  new_fields: 0,
  existing_fields: 0,
  skip_fields: 0,
  fields: []
})

const selectedPreviewFields = ref([])

const previewColumns = [
  { type: 'selection' },
  { 
    title: '状态', 
    key: 'status_text', 
    width: 120,
    render(row) {
      const statusMap = {
        new: { type: 'success', text: '✓ 将创建' },
        exists: { type: 'default', text: '- 已存在' },
        skip_system: { type: 'warning', text: '⊗ 跳过' }
      }
      const config = statusMap[row.status] || { type: 'default', text: row.status_text }
      return h(NTag, { type: config.type }, { default: () => config.text })
    }
  },
  { title: '字段代码', key: 'field_code', width: 180 },
  { title: '字段名称', key: 'field_name', width: 150 },
  { title: 'TDengine类型', key: 'tdengine_type', width: 120 },
  { title: '系统类型', key: 'field_type', width: 100 },
  { 
    title: 'TAG', 
    key: 'is_tag', 
    width: 80,
    render(row) {
      return row.is_tag ? h(NTag, { type: 'info', size: 'small' }, { default: () => 'TAG' }) : '-'
    }
  }
]

const syncResult = reactive({
  created: [],
  skipped: [],
  errors: []
})

const syncResultTitle = computed(() => {
  if (syncStatus.value === 'error') return '同步失败'
  const total = syncResult.created.length + syncResult.skipped.length + syncResult.errors.length
  return `同步完成！共处理 ${total} 个字段`
})

const syncResultDescription = computed(() => {
  return `成功创建 ${syncResult.created.length} 个，跳过 ${syncResult.skipped.length} 个，失败 ${syncResult.errors.length} 个`
})

// 方法
const fetchFieldList = async () => {
  loading.value = true
  try {
    const response = await dataModelApi.getFields({
      ...queryParams,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    
    if (response.success) {
      fieldList.value = response.data || []
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

// 字典分组相关
const monitoringGroupTypeId = ref(null)
const dictGroupOptions = ref([])

const initDictData = async () => {
  try {
    // 1. 确保字典类型存在
    await ensureDictTypeExists()

    // 2. 获取字典数据
    console.log('正在获取字典数据...')
    const dataRes = await systemV2Api.getDictDataByType('monitoring_field_group')
    console.log('获取到的字典数据响应:', dataRes)
    
    // 兼容处理多种返回结构
    const items = dataRes.data?.data || dataRes.data || []
    console.log('解析后的字典数据项:', items)
    
    if (Array.isArray(items)) {
      dictGroupOptions.value = items.map(d => ({ label: d.data_label, value: d.data_value }))
      console.log('字典选项已更新:', dictGroupOptions.value)
    }
  } catch (error) {
    console.error('初始化字典数据失败:', error)
  }
}

const ensureDictTypeExists = async () => {
  if (monitoringGroupTypeId.value) return monitoringGroupTypeId.value
  
  try {
    // 再次检查是否存在
    const typeRes = await systemV2Api.getDictTypeList({ type_code: 'monitoring_field_group' })
    
    // 兼容处理多种返回结构
    let items = []
    if (typeRes.data && Array.isArray(typeRes.data.items)) {
      items = typeRes.data.items
    } else if (typeRes.items && Array.isArray(typeRes.items)) {
      items = typeRes.items
    } else if (typeRes.data && Array.isArray(typeRes.data.data)) {
      items = typeRes.data.data
    } else if (typeRes.data && Array.isArray(typeRes.data)) {
      items = typeRes.data
    } else if (Array.isArray(typeRes)) {
      items = typeRes
    }

    if (items.length > 0) {
      monitoringGroupTypeId.value = items[0].id
      return monitoringGroupTypeId.value
    }
    
    // 不存在则创建
    const createRes = await systemV2Api.createDictType({ 
      type_name: '监测字段分组', 
      type_code: 'monitoring_field_group', 
      is_enabled: true,
      description: '设备实时监测字段的分组定义'
    })
    if (createRes.code === 200 && createRes.data) {
      monitoringGroupTypeId.value = createRes.data.id
      return monitoringGroupTypeId.value
    }
  } catch (error) {
    console.error('创建字典类型失败:', error)
  }
  return null
}

const handleAutoCreateDictData = async (groupName) => {
  if (!groupName || groupName === 'default') return
  // 检查是否已存在于字典选项中
  if (dictGroupOptions.value.some(o => o.value === groupName)) return
  
  try {
    const typeId = await ensureDictTypeExists()
    if (!typeId) return
    
    await systemV2Api.createDictData({
      dict_type_id: typeId,
      data_label: groupName,
      data_value: groupName,
      is_enabled: true,
      sort_order: 0
    })
    
    // 刷新选项
    const dataRes = await systemV2Api.getDictDataByType('monitoring_field_group')
    const items = dataRes.data?.data || dataRes.data || []
    if (Array.isArray(items)) {
      dictGroupOptions.value = items.map(d => ({ label: d.data_label, value: d.data_value }))
    }
  } catch (e) {
    console.error('自动创建字典数据失败:', e)
  }
}

const handleQuery = () => {
  pagination.page = 1
  fetchFieldList()
}

const handleReset = () => {
  queryParams.device_type_code = null
  queryParams.field_category = null
  queryParams.search = ''
  handleQuery()
}

const handleCheckDiff = () => {
  if (!queryParams.device_type_code) {
    message.warning('请先选择设备类型')
    return
  }
  showSchemaDiffModal.value = true
}

const handleCreate = () => {
  Object.assign(fieldFormData, {
    id: null,
    device_type_code: null,
    field_name: '',
    field_code: '',
    field_type: null,
    field_category: 'data_collection',
    field_group: 'default',
    group_order: 0,
    is_default_visible: true,
    sort_order: 0,
    unit: '',
    description: '',
    is_monitoring_key: false,
    is_alarm_enabled: false,
    is_ai_feature: false,
    display_config: { icon: '', color: '' }
  })
  showFieldModal.value = true
}

const handleEdit = async (id) => {
  try {
    const response = await dataModelApi.getField(id)
    if (response.success) {
      Object.assign(fieldFormData, response.data)
      if (!fieldFormData.display_config) {
        fieldFormData.display_config = { icon: '', color: '' }
      }
      showFieldModal.value = true
    } else {
      message.error(response.message || '获取字段详情失败')
    }
  } catch (error) {
    message.error('获取字段详情失败：' + (error.message || '未知错误'))
  }
}

// 批量删除
const handleBatchDelete = async () => {
  // 情况1：删除选中项
  if (checkedRowKeys.value.length > 0) {
    window.$dialog.warning({
      title: '确认删除',
      content: `确定要删除选中的 ${checkedRowKeys.value.length} 个字段吗？`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: async () => {
         try {
            loading.value = true
            const res = await dataModelApi.batchDeleteFieldsByIds(checkedRowKeys.value)
            if (res.success) {
                message.success(res.message)
                checkedRowKeys.value = []
                fetchFieldList()
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
    return
  }

  // 情况2：清空当前分类
  if (!queryParams.device_type_code) {
    message.warning('请先选择要删除的字段，或选择设备类型以执行清空操作')
    return
  }

  const option = deviceTypeOptions.value.find(opt => opt.value === queryParams.device_type_code)
  const deviceTypeName = option ? option.label : queryParams.device_type_code
  
  window.$dialog.error({
    title: '危险操作警告',
    content: `确定要删除该设备类型（${deviceTypeName}）下的所有字段吗？此操作不可恢复！`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      // 二次确认
      window.$dialog.error({
        title: '最终确认',
        content: '请再次确认：这将清空该分类下所有字段定义！如果字段已被模型使用，删除将失败。',
        positiveText: '我已确认风险，执行删除',
        negativeText: '取消',
        onPositiveClick: async () => {
          try {
            loading.value = true
            const res = await dataModelApi.batchDeleteFields(queryParams.device_type_code)
            if (res.success) {
              message.success(res.message)
              fetchFieldList()
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
  })
}

const handleSaveField = async () => {
  try {
    await fieldFormRef.value?.validate()
    
    saving.value = true
    
    // 尝试自动创建字典数据
    await handleAutoCreateDictData(fieldFormData.field_group)
    
    const response = fieldFormData.id
      ? await dataModelApi.updateField(fieldFormData.id, fieldFormData)
      : await dataModelApi.createField(fieldFormData)
    
    if (response.success) {
      message.success(fieldFormData.id ? '更新成功' : '创建成功')
      showFieldModal.value = false
      fetchFieldList()
    } else {
      message.error(response.message || (fieldFormData.id ? '更新失败' : '创建失败'))
    }
  } catch (error) {
    message.error((fieldFormData.id ? '更新失败' : '创建失败') + '：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  window.$dialog.warning({
    title: '确认删除',
    content: '确定要删除该字段配置吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const response = await dataModelApi.deleteField(id)
        if (response.success) {
          message.success('删除成功')
          fetchFieldList()
        } else {
          message.error(response.message || '删除失败')
        }
      } catch (error) {
        console.error('删除失败:', error)
        // 全局错误拦截器会显示错误信息，此处不再重复显示
        // message.error('删除失败：' + (error.message || '未知错误'))
      }
    }
  })
}

const handleToggleActive = async (id, value) => {
  try {
    // 这里需要后端支持更新单个字段的接口，或者使用 updateField
    const response = await dataModelApi.updateField(id, { is_active: value })
    if (response.success) {
      message.success(value ? '启用成功' : '停用成功')
      fetchFieldList()
    } else {
      message.error(response.message || '操作失败')
    }
  } catch (error) {
    message.error('操作失败：' + (error.message || '未知错误'))
  }
}

const handleToggleAlarmEnabled = async (row, value) => {
  const originalValue = row.is_alarm_enabled
  try {
    // 乐观更新
    row.is_alarm_enabled = value
    
    const response = await dataModelApi.updateField(row.id, { 
      is_alarm_enabled: value 
    })
    
    if (response.success) {
      message.success(value ? '开启报警配置成功' : '关闭报警配置成功')
    } else {
      // 回滚
      row.is_alarm_enabled = originalValue
      message.error(response.message || '操作失败')
    }
  } catch (error) {
    // 回滚
    row.is_alarm_enabled = originalValue
    message.error('操作失败：' + (error.message || '未知错误'))
  }
}

const handleOpenAlarmConfig = (row) => {
  alarmConfigData.id = row.id
  alarmConfigData.field_name = row.field_name
  
  // 初始化现有值或默认值
  const threshold = row.alarm_threshold || {}
  alarmConfigData.warning = threshold.warning
  alarmConfigData.critical = threshold.critical
  
  showAlarmConfigDrawer.value = true
}

const handleSaveAlarmConfig = async () => {
  savingAlarmConfig.value = true
  try {
    const threshold = {
      warning: alarmConfigData.warning,
      critical: alarmConfigData.critical
    }
    
    const response = await dataModelApi.updateField(alarmConfigData.id, {
      alarm_threshold: threshold
    })
    
    if (response.success) {
      message.success('报警阈值配置保存成功')
      showAlarmConfigDrawer.value = false
      
      // 更新本地列表
      const item = fieldList.value.find(item => item.id === alarmConfigData.id)
      if (item) {
        item.alarm_threshold = threshold
      }
    } else {
      message.error(response.message || '保存失败')
    }
  } catch (error) {
    message.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    savingAlarmConfig.value = false
  }
}

// TDengine同步方法
const handleSyncFromTDengine = async () => {
  syncStep.value = 1
  syncStatus.value = 'process'
  syncFormData.device_type_code = queryParams.device_type_code
  
  // 自动填充：获取TDengine默认配置
  try {
    const res = await dataModelApi.getTDengineDefaultConfig()
    if (res.success && res.data.database) {
      syncFormData.tdengine_database = res.data.database
    }
  } catch (e) {
    console.error('获取TDengine默认配置失败', e)
  }

  // 自动填充：如果已选择设备类型，填充超级表名
  if (syncFormData.device_type_code) {
    const option = deviceTypeOptions.value.find(opt => opt.value === syncFormData.device_type_code)
    if (option && option.tdengine_stable_name) {
      syncFormData.tdengine_stable = option.tdengine_stable_name
    }
  }

  showSyncModal.value = true
}

const handleCloseSyncModal = () => {
  showSyncModal.value = false
}

const handlePreviewSync = async () => {
  try {
    await syncFormRef.value?.validate()
    previewing.value = true
    
    const response = await dataModelApi.previewTDengineFields(syncFormData)
    if (response.success) {
      Object.assign(previewResult, response.data)
      // 默认全选新字段
      selectedPreviewFields.value = previewResult.fields
        .filter(f => f.status === 'new')
        .map(f => f.field_code)
        
      syncStep.value = 2
    } else {
      message.error(response.message || '预览失败')
    }
  } catch (error) {
    message.error('预览失败：' + (error.message || '未知错误'))
  } finally {
    previewing.value = false
  }
}

const handleExecuteSync = async () => {
  if (selectedPreviewFields.value.length === 0) {
    message.warning('请选择要同步的字段')
    return
  }
  
  try {
    syncing.value = true
    const response = await dataModelApi.syncFromTDengine({
      ...syncFormData,
      field_codes: selectedPreviewFields.value
    })
    
    if (response.success) {
      Object.assign(syncResult, response.data)
      syncStep.value = 3
      if (syncResult.errors.length > 0) {
        syncStatus.value = 'warning'
      } else {
        syncStatus.value = 'finish'
      }
      fetchFieldList()
    } else {
      message.error(response.message || '同步失败')
      syncStatus.value = 'error'
    }
  } catch (error) {
    message.error('同步失败：' + (error.message || '未知错误'))
    syncStatus.value = 'error'
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  await fetchDeviceTypes()
  
  // 初始化字典数据
  initDictData()
  
  // 处理路由查询参数
  if (route.query.device_type) {
    queryParams.device_type_code = route.query.device_type
  }
  
  fetchFieldList()
})
</script>

<style scoped>
.field-management {
  padding: 16px;
}
</style>
