<template>
  <div class="decision-rules-page">
    <n-card title="决策规则管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-button @click="handleReload" :loading="reloading">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            重新加载
          </n-button>
          <n-button type="primary" @click="handleCreate">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            创建规则
          </n-button>
        </n-space>
      </template>

      <!-- 筛选条件 -->
      <n-space class="filter-bar" :wrap="true">
        <n-input v-model:value="filters.keyword" placeholder="搜索规则名称" clearable style="width: 200px;" />
        <n-select v-model:value="filters.enabled" :options="enabledOptions" placeholder="启用状态" clearable style="width: 120px;" />
        <n-select v-model:value="filters.category_id" :options="categoryOptions" placeholder="资产类别" clearable style="width: 150px;" />
        <n-button @click="loadRules">查询</n-button>
      </n-space>

      <!-- 运行时状态 -->
      <n-alert v-if="runtimeStatus" type="info" :bordered="false" class="runtime-status">
        运行时状态: 已加载 {{ runtimeStatus.total_rules }} 条规则，其中 {{ runtimeStatus.enabled_rules }} 条已启用
      </n-alert>

      <n-data-table
        :columns="columns"
        :data="rules"
        :loading="loading"
        :pagination="pagination"
        :row-key="row => row.rule_id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>

    <!-- 创建/编辑规则弹窗 -->
    <n-modal v-model:show="showModal" preset="dialog" :title="modalTitle" style="width: 800px;">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="100px">
        <n-form-item label="规则ID" path="rule_id">
          <n-input v-model:value="formData.rule_id" placeholder="唯一标识符" :disabled="isEdit" />
        </n-form-item>
        <n-form-item label="规则名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入规则名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="formData.description" type="textarea" placeholder="规则描述" />
        </n-form-item>
        <n-form-item label="资产类别" path="category_id">
          <n-select v-model:value="formData.category_id" :options="categoryOptions" placeholder="可选，关联资产类别" clearable />
        </n-form-item>
        <n-form-item label="AI模型" path="model_id">
          <n-select v-model:value="formData.model_id" :options="modelOptions" placeholder="可选，关联AI模型" clearable />
        </n-form-item>
        <n-form-item label="优先级" path="priority">
          <n-input-number v-model:value="formData.priority" :min="0" placeholder="数字越小优先级越高" />
        </n-form-item>
        <n-form-item label="冷却时间" path="cooldown_seconds">
          <n-input-number v-model:value="formData.cooldown_seconds" :min="0" placeholder="秒">
            <template #suffix>秒</template>
          </n-input-number>
        </n-form-item>
        <n-form-item label="启用状态" path="enabled">
          <n-switch v-model:value="formData.enabled" />
        </n-form-item>
        <n-divider>条件配置</n-divider>
        <n-form-item label="条件DSL" path="conditions">
          <n-input 
            v-model:value="conditionsJson" 
            type="textarea" 
            :rows="6"
            placeholder='{"type": "AND", "rules": [{"field": "predicted_value", "operator": "gt", "value": 80}]}'
          />
        </n-form-item>
        <n-divider>动作配置</n-divider>
        <n-form-item label="动作DSL" path="actions">
          <n-input 
            v-model:value="actionsJson" 
            type="textarea" 
            :rows="6"
            placeholder='[{"type": "alert", "level": "warning", "message": "预测值超过阈值"}]'
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="handleValidate" :loading="validating">验证DSL</n-button>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 测试规则弹窗 -->
    <n-modal v-model:show="showTestModal" preset="dialog" title="测试规则" style="width: 600px;">
      <n-form label-placement="left" label-width="100px">
        <n-form-item label="测试数据">
          <n-input 
            v-model:value="testDataJson" 
            type="textarea" 
            :rows="8"
            placeholder='{"predicted_value": 85, "confidence": 0.9}'
          />
        </n-form-item>
      </n-form>
      <template v-if="testResult">
        <n-divider>测试结果</n-divider>
        <n-alert :type="testResult.triggered ? 'success' : 'info'" :bordered="false">
          {{ testResult.triggered ? `规则触发，将执行 ${testResult.actions_count} 个动作` : '规则未触发' }}
        </n-alert>
        <n-collapse v-if="testResult.actions && testResult.actions.length > 0" class="test-actions">
          <n-collapse-item title="触发的动作" name="actions">
            <pre>{{ JSON.stringify(testResult.actions, null, 2) }}</pre>
          </n-collapse-item>
        </n-collapse>
      </template>
      <template #action>
        <n-button @click="showTestModal = false">关闭</n-button>
        <n-button type="primary" @click="handleTest" :loading="testing">执行测试</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { NButton, NSpace, NTag, NSwitch, useMessage, useDialog } from 'naive-ui'
import { AddOutline, RefreshOutline } from '@vicons/ionicons5'
import { decisionApi, assetCategoryApi, aiModelApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

// 状态
const loading = ref(false)
const submitting = ref(false)
const validating = ref(false)
const testing = ref(false)
const reloading = ref(false)
const showModal = ref(false)
const showTestModal = ref(false)
const isEdit = ref(false)
const modalTitle = ref('创建规则')
const rules = ref([])
const runtimeStatus = ref(null)
const categoryOptions = ref([])
const modelOptions = ref([])
const testResult = ref(null)
const currentTestRuleId = ref('')

// 筛选条件
const filters = reactive({
  keyword: '',
  enabled: null,
  category_id: null
})

const enabledOptions = [
  { label: '已启用', value: true },
  { label: '已禁用', value: false }
]

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0
})

// 表单数据
const formData = reactive({
  rule_id: '',
  name: '',
  description: '',
  category_id: null,
  model_id: null,
  priority: 0,
  cooldown_seconds: 0,
  enabled: true,
  conditions: { type: 'AND', rules: [] },
  actions: []
})

const conditionsJson = ref('')
const actionsJson = ref('')
const testDataJson = ref('{\n  "predicted_value": 85,\n  "confidence": 0.9\n}')

// 表单验证规则
const formRules = {
  rule_id: { required: true, message: '请输入规则ID', trigger: 'blur' },
  name: { required: true, message: '请输入规则名称', trigger: 'blur' }
}

const formRef = ref(null)

// 状态映射
const statusMap = {
  true: { text: '已启用', type: 'success' },
  false: { text: '已禁用', type: 'default' }
}

// 表格列定义
const columns = [
  { title: '规则ID', key: 'rule_id', width: 150 },
  { title: '规则名称', key: 'name', width: 180 },
  { title: '优先级', key: 'priority', width: 80 },
  { title: '冷却时间', key: 'cooldown_seconds', width: 100, render: row => `${row.cooldown_seconds}秒` },
  {
    title: '状态',
    key: 'enabled',
    width: 100,
    render: row => {
      const status = statusMap[row.enabled]
      return h(NTag, { type: status.type }, () => status.text)
    }
  },
  { 
    title: '创建时间', 
    key: 'created_at', 
    width: 180,
    render: row => row.created_at ? new Date(row.created_at).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    render: row => h(NSpace, {}, () => [
      h(NButton, { size: 'small', onClick: () => handleTest(row) }, () => '测试'),
      row.enabled
        ? h(NButton, { size: 'small', type: 'warning', onClick: () => handleToggleEnable(row) }, () => '禁用')
        : h(NButton, { size: 'small', type: 'success', onClick: () => handleToggleEnable(row) }, () => '启用'),
      h(NButton, { size: 'small', type: 'info', onClick: () => handleEdit(row) }, () => '编辑'),
      h(NButton, { size: 'small', type: 'error', onClick: () => handleDelete(row) }, () => '删除')
    ])
  }
]

// 加载规则列表
const loadRules = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      enabled: filters.enabled,
      category_id: filters.category_id || undefined
    }
    const res = await decisionApi.getRules(params)
    rules.value = res.data || []
    pagination.itemCount = res.total || 0
  } catch (error) {
    message.error('加载规则列表失败')
  } finally {
    loading.value = false
  }
}

// 加载运行时状态
const loadRuntimeStatus = async () => {
  try {
    const res = await decisionApi.getRuntimeStatus()
    runtimeStatus.value = res.data
  } catch (error) {
    console.error('加载运行时状态失败', error)
  }
}

// 加载资产类别选项
const loadCategoryOptions = async () => {
  try {
    const res = await assetCategoryApi.getList()
    categoryOptions.value = (res.data || []).map(c => ({
      label: c.name,
      value: c.id
    }))
  } catch (error) {
    console.error('加载资产类别失败', error)
  }
}

// 加载AI模型选项
const loadModelOptions = async () => {
  try {
    const res = await aiModelApi.getList()
    modelOptions.value = (res.data || []).map(m => ({
      label: m.name,
      value: m.id
    }))
  } catch (error) {
    console.error('加载AI模型失败', error)
  }
}

// 分页处理
const handlePageChange = (page) => {
  pagination.page = page
  loadRules()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadRules()
}

// 创建规则
const handleCreate = () => {
  isEdit.value = false
  modalTitle.value = '创建规则'
  Object.assign(formData, {
    rule_id: '',
    name: '',
    description: '',
    category_id: null,
    model_id: null,
    priority: 0,
    cooldown_seconds: 0,
    enabled: true,
    conditions: { type: 'AND', rules: [] },
    actions: []
  })
  conditionsJson.value = JSON.stringify({ type: 'AND', rules: [{ field: 'predicted_value', operator: 'gt', value: 80 }] }, null, 2)
  actionsJson.value = JSON.stringify([{ type: 'alert', level: 'warning', message: '预测值超过阈值' }], null, 2)
  showModal.value = true
}

// 编辑规则
const handleEdit = (row) => {
  isEdit.value = true
  modalTitle.value = '编辑规则'
  Object.assign(formData, {
    rule_id: row.rule_id,
    name: row.name,
    description: row.description,
    category_id: row.category_id,
    model_id: row.model_id,
    priority: row.priority,
    cooldown_seconds: row.cooldown_seconds,
    enabled: row.enabled,
    conditions: row.conditions,
    actions: row.actions
  })
  conditionsJson.value = JSON.stringify(row.conditions, null, 2)
  actionsJson.value = JSON.stringify(row.actions, null, 2)
  showModal.value = true
}

// 验证DSL
const handleValidate = async () => {
  validating.value = true
  try {
    const conditions = JSON.parse(conditionsJson.value)
    const actions = JSON.parse(actionsJson.value)
    
    const res = await decisionApi.validateRuleDSL({
      rule_id: formData.rule_id || 'test',
      name: formData.name || 'test',
      conditions,
      actions
    })
    
    if (res.data?.valid) {
      message.success('DSL格式验证通过')
    } else {
      message.error(`DSL格式验证失败: ${res.data?.errors?.join('; ')}`)
    }
  } catch (error) {
    message.error(`JSON解析失败: ${error.message}`)
  } finally {
    validating.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value?.validate()
  
  try {
    formData.conditions = JSON.parse(conditionsJson.value)
    formData.actions = JSON.parse(actionsJson.value)
  } catch (error) {
    message.error(`JSON解析失败: ${error.message}`)
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await decisionApi.updateRule(formData.rule_id, formData)
      message.success('更新成功')
    } else {
      await decisionApi.createRule(formData)
      message.success('创建成功')
    }
    showModal.value = false
    loadRules()
    loadRuntimeStatus()
  } catch (error) {
    message.error(error.response?.data?.msg || error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 删除规则
const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除规则 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await decisionApi.deleteRule(row.rule_id)
        message.success('删除成功')
        loadRules()
        loadRuntimeStatus()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

// 启用/禁用规则
const handleToggleEnable = async (row) => {
  try {
    if (row.enabled) {
      await decisionApi.disableRule(row.rule_id)
      message.success('规则已禁用')
    } else {
      await decisionApi.enableRule(row.rule_id)
      message.success('规则已启用')
    }
    loadRules()
    loadRuntimeStatus()
  } catch (error) {
    message.error('操作失败')
  }
}

// 测试规则
const handleTest = async (row) => {
  if (row && row.rule_id) {
    currentTestRuleId.value = row.rule_id
    testResult.value = null
    showTestModal.value = true
    return
  }
  
  if (!currentTestRuleId.value) return
  
  testing.value = true
  try {
    const testData = JSON.parse(testDataJson.value)
    const res = await decisionApi.testRule(currentTestRuleId.value, testData)
    testResult.value = res.data
  } catch (error) {
    message.error(`测试失败: ${error.message}`)
  } finally {
    testing.value = false
  }
}

// 重新加载规则
const handleReload = async () => {
  reloading.value = true
  try {
    const res = await decisionApi.reloadRules()
    message.success(`已重新加载 ${res.data?.loaded_count || 0} 条规则`)
    loadRuntimeStatus()
  } catch (error) {
    message.error('重新加载失败')
  } finally {
    reloading.value = false
  }
}

onMounted(() => {
  loadRules()
  loadRuntimeStatus()
  loadCategoryOptions()
  loadModelOptions()
})
</script>

<style scoped>
.decision-rules-page {
  padding: 16px;
}

.filter-bar {
  margin-bottom: 16px;
}

.runtime-status {
  margin-bottom: 16px;
}

.test-actions {
  margin-top: 16px;
}

.test-actions pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
