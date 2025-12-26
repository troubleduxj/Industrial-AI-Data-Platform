<template>
  <CommonPage show-footer title="报警规则配置">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="16" class="mr-5" />
        新建规则
      </NButton>
    </template>

    <!-- 搜索栏 -->
    <NCard class="mb-15" size="small">
      <div class="flex flex-wrap items-center gap-15">
        <QueryBarItem label="设备类型" :label-width="70">
          <NSelect
            v-if="!embedded"
            v-model:value="queryParams.device_type_code"
            :options="deviceTypeOptions"
            placeholder="全部类型"
            clearable
            filterable
            style="width: 200px"
          />
          <NInput
            v-else
            :value="currentDeviceTypeName"
            disabled
            placeholder="已锁定"
            style="width: 200px"
          />
        </QueryBarItem>
        <QueryBarItem label="启用状态" :label-width="70">
          <NSelect
            v-model:value="queryParams.is_enabled"
            :options="enabledOptions"
            placeholder="全部状态"
            clearable
            style="width: 120px"
          />
        </QueryBarItem>
        <QueryBarItem label="关键词" :label-width="60">
          <NInput
            v-model:value="queryParams.search"
            placeholder="规则名称"
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

    <!-- 规则列表 -->
    <NCard>
      <NSpin :show="loading">
        <NDataTable
          :columns="columns"
          :data="tableData"
          :pagination="pagination"
          :bordered="false"
          :single-line="false"
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
        :label-width="100"
      >
        <NFormItem label="规则名称" path="rule_name">
          <NInput v-model:value="formData.rule_name" placeholder="请输入规则名称" />
        </NFormItem>

        <NFormItem label="规则代码" path="rule_code">
          <NInput
            v-model:value="formData.rule_code"
            placeholder="请输入规则代码（唯一标识）"
            :disabled="isEdit"
          />
        </NFormItem>

        <NFormItem label="设备类型" path="device_type_code">
          <NSelect
            v-model:value="formData.device_type_code"
            :options="deviceTypeOptions"
            placeholder="请选择设备类型"
            :disabled="isEdit || embedded"
            @update:value="handleDeviceTypeChange"
          />
        </NFormItem>

        <NFormItem label="设备编码" path="device_code">
          <NSelect
            v-model:value="formData.device_code"
            :options="deviceOptions"
            placeholder="请选择设备（为空则为通用规则）"
            clearable
            :loading="deviceLoading"
            :disabled="!formData.device_type_code"
          />
        </NFormItem>

        <NFormItem label="监测字段" path="field_code">
          <NSelect
            v-model:value="formData.field_code"
            :options="fieldOptions"
            placeholder="请选择监测字段"
            :loading="fieldLoading"
            @update:value="handleFieldChange"
          />
        </NFormItem>

        <NFormItem label="阈值类型" path="threshold_type">
          <NSelect
            v-model:value="thresholdType"
            :options="thresholdTypeOptions"
            placeholder="请选择阈值类型"
          />
        </NFormItem>

        <!-- 阈值配置 -->
        <NCard title="阈值配置" size="small" class="mb-15">
          <div class="threshold-config">
            <!-- 警告阈值 -->
            <div class="threshold-row">
              <NTag type="warning" size="small">警告</NTag>
              <template v-if="thresholdType === 'range'">
                <NInputNumber
                  v-model:value="formData.threshold_config.warning.min"
                  placeholder="最小值"
                  style="width: 120px"
                />
                <span class="mx-10">~</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.warning.max"
                  placeholder="最大值"
                  style="width: 120px"
                />
              </template>
              <template v-else-if="thresholdType === 'upper'">
                <span class="mx-10">超过</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.warning.max"
                  placeholder="上限值"
                  style="width: 150px"
                />
              </template>
              <template v-else-if="thresholdType === 'lower'">
                <span class="mx-10">低于</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.warning.min"
                  placeholder="下限值"
                  style="width: 150px"
                />
              </template>
            </div>

            <!-- 严重阈值 -->
            <div class="threshold-row">
              <NTag type="error" size="small">严重</NTag>
              <template v-if="thresholdType === 'range'">
                <NInputNumber
                  v-model:value="formData.threshold_config.critical.min"
                  placeholder="最小值"
                  style="width: 120px"
                />
                <span class="mx-10">~</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.critical.max"
                  placeholder="最大值"
                  style="width: 120px"
                />
              </template>
              <template v-else-if="thresholdType === 'upper'">
                <span class="mx-10">超过</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.critical.max"
                  placeholder="上限值"
                  style="width: 150px"
                />
              </template>
              <template v-else-if="thresholdType === 'lower'">
                <span class="mx-10">低于</span>
                <NInputNumber
                  v-model:value="formData.threshold_config.critical.min"
                  placeholder="下限值"
                  style="width: 150px"
                />
              </template>
            </div>
          </div>
        </NCard>

        <NFormItem label="触发条件">
          <div class="flex items-center gap-10">
            <span>连续</span>
            <NInputNumber
              v-model:value="formData.trigger_condition.consecutive_count"
              :min="1"
              :max="10"
              style="width: 80px"
            />
            <span>次超阈值后触发报警</span>
          </div>
        </NFormItem>

        <NFormItem label="高级配置" path="trigger_config">
          <NInput
            v-model:value="formData.trigger_config"
            type="textarea"
            placeholder="请输入高级触发配置 (JSON格式)"
            :rows="3"
          />
        </NFormItem>

        <NFormItem label="默认级别" path="alarm_level">
          <NSelect
            v-model:value="formData.alarm_level"
            :options="alarmLevelOptions"
            placeholder="请选择默认报警级别"
          />
        </NFormItem>

        <NFormItem label="规则描述">
          <NInput
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入规则描述"
            :rows="2"
          />
        </NFormItem>

        <NFormItem label="启用状态">
          <NSwitch v-model:value="formData.is_enabled" />
        </NFormItem>
      </NForm>

      <template #footer>
        <div class="flex justify-end gap-10">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">保存</NButton>
        </div>
      </template>
    </NModal>

    <!-- 测试弹窗 -->
    <NModal v-model:show="testModalVisible" title="测试报警规则" preset="card" style="width: 500px">
      <div class="test-modal">
        <p class="mb-15">规则: {{ testRule?.rule_name }}</p>
        <NFormItem label="测试值">
          <NInputNumber v-model:value="testValue" placeholder="请输入测试值" style="width: 100%" />
        </NFormItem>
        <div v-if="testResult" class="test-result mt-15">
          <NAlert :type="testResult.triggered ? 'error' : 'success'">
            <template #header>
              {{ testResult.triggered ? `触发报警 (${testResult.level})` : '未触发报警' }}
            </template>
            {{ testResult.message }}
          </NAlert>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-10">
          <NButton @click="testModalVisible = false">关闭</NButton>
          <NButton type="primary" :loading="testing" @click="handleTest">测试</NButton>
        </div>
      </template>
    </NModal>
  </CommonPage>
</template>

<script setup>
import { ref, reactive, h, onMounted, watch, computed } from 'vue'
import {
  NCard,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NTag,
  NAlert,
  NSpin,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { alarmRulesApi, AlarmLevelOptions, ThresholdTypeOptions } from '@/api/alarm-rules'
import { deviceApi } from '@/api/device-v2'

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

// 状态
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const fieldLoading = ref(false)
const deviceLoading = ref(false)
const tableData = ref([])
const modalVisible = ref(false)
const testModalVisible = ref(false)
const modalTitle = ref('')
const isEdit = ref(false)
const formRef = ref(null)

// 查询参数
const queryParams = reactive({
  device_type_code: props.deviceTypeCode,
  device_code: null,
  is_enabled: null,
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

// 选项数据
const deviceTypeOptions = ref([])
const deviceOptions = ref([])
const fieldOptions = ref([])
const enabledOptions = [
  { label: '全部', value: null },
  { label: '已启用', value: true },
  { label: '已禁用', value: false },
]
const alarmLevelOptions = AlarmLevelOptions
const thresholdTypeOptions = ThresholdTypeOptions
const thresholdType = ref('range')

// 表单数据
const formData = reactive({
  rule_name: '',
  rule_code: '',
  device_type_code: null,
  device_code: null,
  field_code: null,
  field_name: '',
  threshold_config: {
    type: 'range',
    warning: { min: null, max: null },
    critical: { min: null, max: null },
  },
  trigger_condition: {
    consecutive_count: 1,
  },
  trigger_config: '',
  alarm_level: 'warning',
  description: '',
  is_enabled: true,
})

// 表单验证规则
const formRules = {
  rule_name: { required: true, message: '请输入规则名称', trigger: 'blur' },
  rule_code: { required: true, message: '请输入规则代码', trigger: 'blur' },
  device_type_code: { required: true, message: '请选择设备类型', trigger: 'change' },
  field_code: { required: true, message: '请选择监测字段', trigger: 'change' },
  trigger_config: {
    validator(rule, value) {
      if (!value) return true
      try {
        JSON.parse(value)
        return true
      } catch (e) {
        return new Error('请输入有效的JSON格式')
      }
    },
    trigger: 'blur'
  }
}

// 测试相关
const testRule = ref(null)
const testValue = ref(null)
const testResult = ref(null)

// 表格列定义
const columns = [
  { title: '规则名称', key: 'rule_name', width: 150 },
  { title: '规则代码', key: 'rule_code', width: 150 },
  { 
    title: '设备类型', 
    key: 'device_type_code', 
    width: 120,
    render(row) {
      const option = deviceTypeOptions.value.find(opt => opt.value === row.device_type_code)
      return option ? option.label : row.device_type_code
    }
  },
  { title: '设备编码', key: 'device_code', width: 120, render: (row) => row.device_code || '通用' },
  { title: '监测字段', key: 'field_name', width: 100 },
  {
    title: '报警级别',
    key: 'alarm_level',
    width: 80,
    render: (row) => {
      const level = AlarmLevelOptions.find((l) => l.value === row.alarm_level)
      return h(NTag, { type: getTagType(row.alarm_level), size: 'small' }, () => level?.label || row.alarm_level)
    },
  },
  {
    title: '状态',
    key: 'is_enabled',
    width: 80,
    render: (row) =>
      h(NTag, { type: row.is_enabled ? 'success' : 'default', size: 'small' }, () =>
        row.is_enabled ? '启用' : '禁用'
      ),
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row) =>
      h('div', { class: 'flex gap-5' }, [
        h(NButton, { size: 'small', onClick: () => handleEdit(row) }, () => '编辑'),
        h(NButton, { size: 'small', type: 'info', onClick: () => handleOpenTest(row) }, () => '测试'),
        h(
          NButton,
          { size: 'small', type: row.is_enabled ? 'warning' : 'success', onClick: () => handleToggle(row) },
          () => (row.is_enabled ? '禁用' : '启用')
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row) },
          {
            trigger: () => h(NButton, { size: 'small', type: 'error' }, () => '删除'),
            default: () => '确定删除该规则吗？',
          }
        ),
      ]),
  },
]

// 方法
const getTagType = (level) => {
  const map = { info: 'default', warning: 'warning', critical: 'error', emergency: 'error' }
  return map[level] || 'default'
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...queryParams,
    }
    // 清理空值
    Object.keys(params).forEach((key) => {
      if (params[key] === null || params[key] === '') delete params[key]
    })

    const res = await alarmRulesApi.list(params)
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

const loadDeviceTypes = async () => {
  try {
    const res = await alarmRulesApi.getDeviceTypes()
    if (res.success && res.data) {
      const items = Array.isArray(res.data) ? res.data : (res.data.items || [])
      deviceTypeOptions.value = items.map((item) => ({
        label: `${item.type_name} (${item.type_code})`,
        value: item.type_code,
      }))
    }
  } catch (error) {
    console.error('加载设备类型失败:', error)
  }
}

const loadDevices = async (deviceTypeCode) => {
  if (!deviceTypeCode) {
    deviceOptions.value = []
    return
  }
  deviceLoading.value = true
  try {
    const params = {
      device_type: deviceTypeCode,
      page: 1,
      page_size: 100 // 修正：后端限制最大100
    }
    
    const res = await deviceApi.list(params)
    if (res.success && res.data) {
      const items = res.data.items || res.data || []
      deviceOptions.value = items.map((item) => ({
        label: `${item.device_name} (${item.device_code})`,
        value: item.device_code,
      }))
    }
  } catch (error) {
    console.error('加载设备失败:', error)
    message.error('加载设备列表失败')
  } finally {
    deviceLoading.value = false
  }
}

const loadFields = async (deviceTypeCode) => {
  if (!deviceTypeCode) {
    fieldOptions.value = []
    return
  }
  fieldLoading.value = true
  try {
    const res = await alarmRulesApi.getFields(deviceTypeCode)
    if (res.success && res.data) {
      fieldOptions.value = res.data.map((item) => ({
        label: `${item.field_name} (${item.field_code})`,
        value: item.field_code,
        ...item,
      }))
    }
  } catch (error) {
    console.error('加载字段失败:', error)
  } finally {
    fieldLoading.value = false
  }
}

const handleDeviceTypeChange = (value) => {
  formData.field_code = null
  formData.field_name = ''
  formData.device_code = null
  loadFields(value)
  loadDevices(value)
}

const handleFieldChange = (value) => {
  const field = fieldOptions.value.find((f) => f.value === value)
  if (field) {
    formData.field_name = field.field_name
    // 如果字段有默认阈值配置，自动填充
    if (field.alarm_threshold) {
      formData.threshold_config = { ...field.alarm_threshold }
      thresholdType.value = field.alarm_threshold.type || 'range'
    }
  }
}

const handleReset = () => {
  queryParams.device_type_code = null
  queryParams.is_enabled = null
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
  formData.rule_name = ''
  formData.rule_code = ''
  formData.device_type_code = props.deviceTypeCode || null
  formData.device_code = null
  formData.field_code = null
  formData.field_name = ''
  formData.threshold_config = {
    type: 'range',
    warning: { min: null, max: null },
    critical: { min: null, max: null },
  }
  formData.trigger_condition = { consecutive_count: 1 }
  formData.trigger_config = ''
  formData.alarm_level = 'warning'
  formData.description = ''
  formData.is_enabled = true
  thresholdType.value = 'range'
  fieldOptions.value = []
  deviceOptions.value = []
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  modalTitle.value = '新建报警规则'
  
  // 如果有预设的设备类型（如嵌入模式），加载相关选项
  if (formData.device_type_code) {
    loadFields(formData.device_type_code)
    loadDevices(formData.device_type_code)
  }
  
  modalVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true
  modalTitle.value = '编辑报警规则'

  // 加载字段选项
  await loadFields(row.device_type_code)
  // 加载设备选项
  await loadDevices(row.device_type_code)

  // 填充表单
  Object.assign(formData, {
    id: row.id,
    rule_name: row.rule_name,
    rule_code: row.rule_code,
    device_type_code: row.device_type_code,
    device_code: row.device_code,
    field_code: row.field_code,
    field_name: row.field_name,
    threshold_config: row.threshold_config || { type: 'range', warning: {}, critical: {} },
    trigger_condition: row.trigger_condition || { consecutive_count: 1 },
    trigger_config: row.trigger_config ? JSON.stringify(row.trigger_config, null, 2) : '',
    alarm_level: row.alarm_level,
    description: row.description,
    is_enabled: row.is_enabled,
  })
  thresholdType.value = formData.threshold_config.type || 'range'

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
    // 构建阈值配置
    const thresholdConfig = {
      type: thresholdType.value,
      warning: formData.threshold_config.warning,
      critical: formData.threshold_config.critical,
    }

    let parsedTriggerConfig = null
    if (formData.trigger_config) {
      try {
        parsedTriggerConfig = JSON.parse(formData.trigger_config)
      } catch (e) {
        return
      }
    }

    const data = {
      rule_name: formData.rule_name,
      rule_code: formData.rule_code,
      device_type_code: formData.device_type_code,
      device_code: formData.device_code,
      field_code: formData.field_code,
      field_name: formData.field_name,
      threshold_config: thresholdConfig,
      trigger_condition: formData.trigger_condition,
      trigger_config: parsedTriggerConfig,
      alarm_level: formData.alarm_level,
      description: formData.description,
      is_enabled: formData.is_enabled,
    }

    let res
    if (isEdit.value) {
      res = await alarmRulesApi.update(formData.id, data)
    } else {
      res = await alarmRulesApi.create(data)
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

const handleToggle = async (row) => {
  try {
    const res = await alarmRulesApi.toggle(row.id)
    if (res.success) {
      message.success(res.message || '操作成功')
      loadData()
    }
  } catch (error) {
    console.error('切换状态失败:', error)
    message.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    const res = await alarmRulesApi.delete(row.id)
    if (res.success) {
      message.success('删除成功')
      loadData()
    }
  } catch (error) {
    console.error('删除失败:', error)
    message.error('删除失败')
  }
}

const handleOpenTest = (row) => {
  testRule.value = row
  testValue.value = null
  testResult.value = null
  testModalVisible.value = true
}

const handleTest = async () => {
  if (testValue.value === null) {
    message.warning('请输入测试值')
    return
  }
  testing.value = true
  try {
    const res = await alarmRulesApi.test(testRule.value.id, testValue.value)
    if (res.success && res.data) {
      testResult.value = res.data
    }
  } catch (error) {
    console.error('测试失败:', error)
    message.error('测试失败')
  } finally {
    testing.value = false
  }
}

// 计算当前设备类型名称（用于嵌入模式）
const currentDeviceTypeName = computed(() => {
  const code = queryParams.device_type_code
  if (!code) return ''
  const option = deviceTypeOptions.value.find(opt => opt.value === code)
  return option ? option.label : code
})

// 监听 prop 变化
watch(
  () => props.deviceTypeCode,
  (newVal) => {
    if (newVal) {
      queryParams.device_type_code = newVal
      loadData()
    }
  }
)

// 初始化
onMounted(() => {
  loadDeviceTypes()
  loadData()
})
</script>

<style scoped>
.threshold-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.threshold-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.test-result {
  margin-top: 15px;
}
</style>
