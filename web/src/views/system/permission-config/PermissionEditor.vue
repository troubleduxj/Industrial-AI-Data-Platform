<template>
  <div class="permission-editor">
    <CommonPage show-footer title="权限配置编辑器" class="editor-page">
      <template #action>
        <div class="flex items-center gap-3">
          <NButton type="primary" :loading="saving" @click="handleSave">
            <TheIcon icon="material-symbols:save" :size="18" class="mr-1" />
            保存配置
          </NButton>
          <NButton @click="handleValidate">
            <TheIcon icon="material-symbols:check-circle" :size="18" class="mr-1" />
            验证配置
          </NButton>
          <NButton @click="handlePreview">
            <TheIcon icon="material-symbols:preview" :size="18" class="mr-1" />
            预览效果
          </NButton>
          <NButton @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="18" class="mr-1" />
            重置
          </NButton>
        </div>
      </template>

      <div class="editor-layout">
        <!-- 左侧配置树 -->
        <div class="config-tree-panel">
          <NCard title="配置结构" class="config-tree-card">
            <template #header-extra>
              <NDropdown :options="addOptions" @select="handleAddConfig">
                <NButton size="small">
                  <TheIcon icon="material-symbols:add" :size="16" class="mr-1" />
                  添加配置
                </NButton>
              </NDropdown>
            </template>

            <NTree
              :data="configTree"
              :render-label="renderConfigLabel"
              :render-prefix="renderConfigIcon"
              :render-suffix="renderConfigActions"
              block-line
              selectable
              :selected-keys="selectedKeys"
              @update:selected-keys="handleSelectConfig"
            />
          </NCard>
        </div>

        <!-- 右侧编辑器 -->
        <div class="editor-panel">
          <div v-if="!selectedConfig" class="empty-editor">
            <TheIcon icon="material-symbols:edit-note" :size="64" class="empty-icon" />
            <p class="empty-text">请选择一个配置项进行编辑</p>
          </div>

          <div v-else class="config-editor">
            <NTabs v-model:value="editorTab" type="line" animated>
              <!-- 基本配置 -->
              <NTabPane name="basic" tab="基本配置">
                <div class="basic-config">
                  <NForm
                    :model="selectedConfig"
                    :rules="configRules"
                    label-placement="left"
                    label-width="120px"
                  >
                    <NFormItem label="配置名称" path="name">
                      <NInput v-model:value="selectedConfig.name" placeholder="请输入配置名称" />
                    </NFormItem>
                    
                    <NFormItem label="配置类型" path="type">
                      <NSelect
                        v-model:value="selectedConfig.type"
                        :options="configTypeOptions"
                        placeholder="请选择配置类型"
                      />
                    </NFormItem>
                    
                    <NFormItem label="描述" path="description">
                      <NInput
                        v-model:value="selectedConfig.description"
                        type="textarea"
                        placeholder="请输入配置描述"
                        :rows="3"
                      />
                    </NFormItem>
                    
                    <NFormItem label="状态" path="enabled">
                      <NSwitch v-model:value="selectedConfig.enabled">
                        <template #checked>启用</template>
                        <template #unchecked>禁用</template>
                      </NSwitch>
                    </NFormItem>
                  </NForm>
                </div>
              </NTabPane>

              <!-- 权限规则 -->
              <NTabPane name="rules" tab="权限规则">
                <div class="permission-rules">
                  <div class="rules-header">
                    <h4>权限规则配置</h4>
                    <NButton size="small" @click="handleAddRule">
                      <TheIcon icon="material-symbols:add" :size="16" class="mr-1" />
                      添加规则
                    </NButton>
                  </div>

                  <div class="rules-list">
                    <div
                      v-for="(rule, index) in selectedConfig.rules"
                      :key="index"
                      class="rule-item"
                    >
                      <div class="rule-header">
                        <span class="rule-title">规则 {{ index + 1 }}</span>
                        <div class="rule-actions">
                          <NButton size="tiny" @click="handleEditRule(index)">
                            <TheIcon icon="material-symbols:edit" :size="14" />
                          </NButton>
                          <NPopconfirm @positive-click="handleDeleteRule(index)">
                            <template #trigger>
                              <NButton size="tiny" type="error">
                                <TheIcon icon="material-symbols:delete" :size="14" />
                              </NButton>
                            </template>
                            确定删除此规则吗？
                          </NPopconfirm>
                        </div>
                      </div>
                      
                      <div class="rule-content">
                        <NForm :model="rule" label-placement="left" label-width="100px" size="small">
                          <NFormItem label="资源类型">
                            <NSelect
                              v-model:value="rule.resource_type"
                              :options="resourceTypeOptions"
                              placeholder="选择资源类型"
                            />
                          </NFormItem>
                          
                          <NFormItem label="资源路径">
                            <NInput
                              v-model:value="rule.resource_path"
                              placeholder="如: /api/users/*"
                            />
                          </NFormItem>
                          
                          <NFormItem label="操作权限">
                            <NCheckboxGroup v-model:value="rule.actions">
                              <NSpace>
                                <NCheckbox value="read">读取</NCheckbox>
                                <NCheckbox value="write">写入</NCheckbox>
                                <NCheckbox value="delete">删除</NCheckbox>
                                <NCheckbox value="execute">执行</NCheckbox>
                              </NSpace>
                            </NCheckboxGroup>
                          </NFormItem>
                          
                          <NFormItem label="条件表达式">
                            <NInput
                              v-model:value="rule.condition"
                              placeholder="如: user.department == 'IT'"
                            />
                          </NFormItem>
                        </NForm>
                      </div>
                    </div>
                  </div>
                </div>
              </NTabPane>

              <!-- 条件配置 -->
              <NTabPane name="conditions" tab="条件配置">
                <div class="condition-config">
                  <div class="condition-builder">
                    <h4>条件构建器</h4>
                    <p class="condition-desc">使用可视化方式构建权限条件</p>
                    
                    <div class="condition-groups">
                      <div
                        v-for="(group, groupIndex) in selectedConfig.conditions"
                        :key="groupIndex"
                        class="condition-group"
                      >
                        <div class="group-header">
                          <span class="group-title">条件组 {{ groupIndex + 1 }}</span>
                          <div class="group-actions">
                            <NSelect
                              v-model:value="group.operator"
                              :options="operatorOptions"
                              size="small"
                              style="width: 80px"
                            />
                            <NButton size="tiny" @click="handleAddCondition(groupIndex)">
                              <TheIcon icon="material-symbols:add" :size="14" />
                            </NButton>
                            <NButton size="tiny" type="error" @click="handleDeleteGroup(groupIndex)">
                              <TheIcon icon="material-symbols:delete" :size="14" />
                            </NButton>
                          </div>
                        </div>
                        
                        <div class="conditions-list">
                          <div
                            v-for="(condition, condIndex) in group.conditions"
                            :key="condIndex"
                            class="condition-item"
                          >
                            <NSelect
                              v-model:value="condition.field"
                              :options="fieldOptions"
                              placeholder="选择字段"
                              style="width: 120px"
                            />
                            <NSelect
                              v-model:value="condition.operator"
                              :options="conditionOperatorOptions"
                              placeholder="操作符"
                              style="width: 100px"
                            />
                            <NInput
                              v-model:value="condition.value"
                              placeholder="值"
                              style="width: 150px"
                            />
                            <NButton size="tiny" type="error" @click="handleDeleteCondition(groupIndex, condIndex)">
                              <TheIcon icon="material-symbols:delete" :size="14" />
                            </NButton>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div class="condition-actions">
                      <NButton @click="handleAddConditionGroup">
                        <TheIcon icon="material-symbols:add" :size="16" class="mr-1" />
                        添加条件组
                      </NButton>
                    </div>
                  </div>
                  
                  <div class="condition-preview">
                    <h4>条件预览</h4>
                    <NCode :code="generateConditionExpression()" language="javascript" />
                  </div>
                </div>
              </NTabPane>

              <!-- JSON编辑 -->
              <NTabPane name="json" tab="JSON编辑">
                <div class="json-editor">
                  <div class="json-toolbar">
                    <NSpace>
                      <NButton size="small" @click="handleFormatJson">
                        <TheIcon icon="material-symbols:code" :size="16" class="mr-1" />
                        格式化
                      </NButton>
                      <NButton size="small" @click="handleValidateJson">
                        <TheIcon icon="material-symbols:check" :size="16" class="mr-1" />
                        验证JSON
                      </NButton>
                      <NButton size="small" @click="handleImportJson">
                        <TheIcon icon="material-symbols:upload" :size="16" class="mr-1" />
                        导入
                      </NButton>
                    </NSpace>
                  </div>
                  
                  <div class="json-content">
                    <NInput
                      v-model:value="jsonConfig"
                      type="textarea"
                      :rows="20"
                      placeholder="在此编辑JSON配置..."
                      @blur="handleJsonChange"
                    />
                  </div>
                </div>
              </NTabPane>
            </NTabs>
          </div>
        </div>
      </div>
    </CommonPage>

    <!-- 预览模态框 -->
    <NModal v-model:show="previewVisible" preset="card" title="配置预览" style="width: 80%">
      <div class="config-preview">
        <NTabs type="line">
          <NTabPane name="tree" tab="树形结构">
            <NTree :data="previewTree" block-line />
          </NTabPane>
          <NTabPane name="json" tab="JSON格式">
            <NCode :code="previewJson" language="json" />
          </NTabPane>
          <NTabPane name="effect" tab="效果预览">
            <div class="effect-preview">
              <h4>权限效果模拟</h4>
              <div class="simulation-controls">
                <NForm inline>
                  <NFormItem label="用户角色">
                    <NSelect v-model:value="simulationRole" :options="roleOptions" style="width: 150px" />
                  </NFormItem>
                  <NFormItem label="访问路径">
                    <NInput v-model:value="simulationPath" placeholder="/api/users" style="width: 200px" />
                  </NFormItem>
                  <NFormItem>
                    <NButton @click="handleSimulate">模拟测试</NButton>
                  </NFormItem>
                </NForm>
              </div>
              <div v-if="simulationResult" class="simulation-result">
                <NAlert :type="simulationResult.allowed ? 'success' : 'error'">
                  <template #header>
                    {{ simulationResult.allowed ? '访问允许' : '访问拒绝' }}
                  </template>
                  {{ simulationResult.reason }}
                </NAlert>
              </div>
            </div>
          </NTabPane>
        </NTabs>
      </div>
    </NModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, watch } from 'vue'
import {
  NButton,
  NCard,
  NTree,
  NTabs,
  NTabPane,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NCheckboxGroup,
  NCheckbox,
  NSpace,
  NDropdown,
  NPopconfirm,
  NCode,
  NModal,
  NAlert,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import systemV2Api from '@/api/system-v2'

defineOptions({ name: 'PermissionEditor' })

const $message = useMessage()

// 数据状态
const configTree = ref([])
const selectedConfig = ref(null)
const selectedKeys = ref([])
const editorTab = ref('basic')
const saving = ref(false)
const jsonConfig = ref('')
const previewVisible = ref(false)
const previewTree = ref([])
const previewJson = ref('')

// 模拟测试
const simulationRole = ref(null)
const simulationPath = ref('')
const simulationResult = ref(null)

// 配置选项
const configTypeOptions = [
  { label: '角色权限', value: 'role' },
  { label: 'API权限', value: 'api' },
  { label: '菜单权限', value: 'menu' },
  { label: '数据权限', value: 'data' },
  { label: '字段权限', value: 'field' },
]

const resourceTypeOptions = [
  { label: 'API接口', value: 'api' },
  { label: '菜单页面', value: 'menu' },
  { label: '数据表', value: 'table' },
  { label: '文件资源', value: 'file' },
]

const operatorOptions = [
  { label: 'AND', value: 'and' },
  { label: 'OR', value: 'or' },
]

const conditionOperatorOptions = [
  { label: '等于', value: 'eq' },
  { label: '不等于', value: 'ne' },
  { label: '包含', value: 'in' },
  { label: '不包含', value: 'not_in' },
  { label: '大于', value: 'gt' },
  { label: '小于', value: 'lt' },
  { label: '匹配', value: 'match' },
]

const fieldOptions = [
  { label: '用户ID', value: 'user.id' },
  { label: '用户角色', value: 'user.role' },
  { label: '部门ID', value: 'user.department' },
  { label: '请求时间', value: 'request.time' },
  { label: '请求IP', value: 'request.ip' },
  { label: '资源所有者', value: 'resource.owner' },
]

const roleOptions = ref([
  { label: '管理员', value: 'admin' },
  { label: '普通用户', value: 'user' },
  { label: '访客', value: 'guest' },
])

const addOptions = [
  {
    label: '角色配置',
    key: 'role',
    icon: () => h(TheIcon, { icon: 'material-symbols:person', size: 16 })
  },
  {
    label: 'API配置',
    key: 'api',
    icon: () => h(TheIcon, { icon: 'material-symbols:api', size: 16 })
  },
  {
    label: '菜单配置',
    key: 'menu',
    icon: () => h(TheIcon, { icon: 'material-symbols:menu', size: 16 })
  },
  {
    label: '数据配置',
    key: 'data',
    icon: () => h(TheIcon, { icon: 'material-symbols:database', size: 16 })
  },
]

// 表单验证规则
const configRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '配置名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择配置类型', trigger: 'change' }
  ]
}

// 生命周期
onMounted(() => {
  loadConfigs()
})

// 监听选中配置变化
watch(selectedConfig, (newConfig) => {
  if (newConfig) {
    jsonConfig.value = JSON.stringify(newConfig, null, 2)
  }
}, { deep: true })

// 方法
async function loadConfigs() {
  try {
    const response = await systemV2Api.getPermissionConfigs()
    configTree.value = response.data || []
  } catch (error) {
    $message.error('加载权限配置失败')
    console.error('Load configs error:', error)
  }
}

function handleSelectConfig(keys) {
  selectedKeys.value = keys
  if (keys.length > 0) {
    const configId = keys[0]
    const config = findConfigById(configTree.value, configId)
    if (config) {
      selectedConfig.value = { ...config }
      editorTab.value = 'basic'
    }
  } else {
    selectedConfig.value = null
  }
}

function findConfigById(configs, id) {
  for (const config of configs) {
    if (config.key === id) {
      return config
    }
    if (config.children) {
      const found = findConfigById(config.children, id)
      if (found) return found
    }
  }
  return null
}

function handleAddConfig(key) {
  const newConfig = {
    key: `${key}_${Date.now()}`,
    name: `新${getConfigTypeLabel(key)}配置`,
    type: key,
    description: '',
    enabled: true,
    rules: [],
    conditions: [],
  }
  
  configTree.value.push(newConfig)
  selectedKeys.value = [newConfig.key]
  selectedConfig.value = newConfig
}

function getConfigTypeLabel(type) {
  const labels = {
    role: '角色',
    api: 'API',
    menu: '菜单',
    data: '数据'
  }
  return labels[type] || type
}

function handleAddRule() {
  if (!selectedConfig.value.rules) {
    selectedConfig.value.rules = []
  }
  
  selectedConfig.value.rules.push({
    resource_type: '',
    resource_path: '',
    actions: [],
    condition: ''
  })
}

function handleEditRule(index) {
  // 编辑规则逻辑
}

function handleDeleteRule(index) {
  selectedConfig.value.rules.splice(index, 1)
}

function handleAddConditionGroup() {
  if (!selectedConfig.value.conditions) {
    selectedConfig.value.conditions = []
  }
  
  selectedConfig.value.conditions.push({
    operator: 'and',
    conditions: []
  })
}

function handleAddCondition(groupIndex) {
  selectedConfig.value.conditions[groupIndex].conditions.push({
    field: '',
    operator: 'eq',
    value: ''
  })
}

function handleDeleteGroup(groupIndex) {
  selectedConfig.value.conditions.splice(groupIndex, 1)
}

function handleDeleteCondition(groupIndex, condIndex) {
  selectedConfig.value.conditions[groupIndex].conditions.splice(condIndex, 1)
}

function generateConditionExpression() {
  if (!selectedConfig.value?.conditions?.length) {
    return '// 暂无条件配置'
  }
  
  const groups = selectedConfig.value.conditions.map(group => {
    const conditions = group.conditions.map(cond => {
      return `${cond.field} ${cond.operator} "${cond.value}"`
    }).join(` ${group.operator.toUpperCase()} `)
    
    return `(${conditions})`
  }).join(' AND ')
  
  return groups || '// 条件表达式为空'
}

async function handleSave() {
  if (!selectedConfig.value) {
    $message.warning('请先选择一个配置项')
    return
  }
  
  try {
    saving.value = true
    
    if (selectedConfig.value.id) {
      await systemV2Api.updatePermissionConfig(selectedConfig.value.id, selectedConfig.value)
      $message.success('配置更新成功')
    } else {
      await systemV2Api.createPermissionConfig(selectedConfig.value)
      $message.success('配置创建成功')
    }
    
    await loadConfigs()
  } catch (error) {
    $message.error('保存配置失败')
    console.error('Save config error:', error)
  } finally {
    saving.value = false
  }
}

function handleValidate() {
  if (!selectedConfig.value) {
    $message.warning('请先选择一个配置项')
    return
  }
  
  try {
    // 验证配置的完整性和正确性
    const errors = validateConfig(selectedConfig.value)
    
    if (errors.length === 0) {
      $message.success('配置验证通过')
    } else {
      $message.error(`配置验证失败：${errors.join(', ')}`)
    }
  } catch (error) {
    $message.error('配置验证出错')
    console.error('Validate error:', error)
  }
}

function validateConfig(config) {
  const errors = []
  
  if (!config.name) {
    errors.push('配置名称不能为空')
  }
  
  if (!config.type) {
    errors.push('配置类型不能为空')
  }
  
  if (config.rules) {
    config.rules.forEach((rule, index) => {
      if (!rule.resource_type) {
        errors.push(`规则${index + 1}的资源类型不能为空`)
      }
      if (!rule.resource_path) {
        errors.push(`规则${index + 1}的资源路径不能为空`)
      }
    })
  }
  
  return errors
}

function handlePreview() {
  if (!selectedConfig.value) {
    $message.warning('请先选择一个配置项')
    return
  }
  
  // 生成预览数据
  previewTree.value = generatePreviewTree(selectedConfig.value)
  previewJson.value = JSON.stringify(selectedConfig.value, null, 2)
  previewVisible.value = true
}

function generatePreviewTree(config) {
  return [
    {
      label: config.name,
      key: config.key,
      children: [
        {
          label: `类型: ${config.type}`,
          key: `${config.key}_type`
        },
        {
          label: `状态: ${config.enabled ? '启用' : '禁用'}`,
          key: `${config.key}_status`
        },
        {
          label: `规则数量: ${config.rules?.length || 0}`,
          key: `${config.key}_rules`
        },
        {
          label: `条件组数量: ${config.conditions?.length || 0}`,
          key: `${config.key}_conditions`
        }
      ]
    }
  ]
}

function handleReset() {
  if (selectedConfig.value) {
    const configId = selectedConfig.value.key
    const originalConfig = findConfigById(configTree.value, configId)
    if (originalConfig) {
      selectedConfig.value = { ...originalConfig }
      $message.info('配置已重置')
    }
  }
}

function handleFormatJson() {
  try {
    const parsed = JSON.parse(jsonConfig.value)
    jsonConfig.value = JSON.stringify(parsed, null, 2)
    $message.success('JSON格式化成功')
  } catch (error) {
    $message.error('JSON格式错误')
  }
}

function handleValidateJson() {
  try {
    JSON.parse(jsonConfig.value)
    $message.success('JSON格式验证通过')
  } catch (error) {
    $message.error('JSON格式错误')
  }
}

function handleImportJson() {
  try {
    const parsed = JSON.parse(jsonConfig.value)
    selectedConfig.value = parsed
    $message.success('JSON导入成功')
  } catch (error) {
    $message.error('JSON格式错误，导入失败')
  }
}

function handleJsonChange() {
  try {
    const parsed = JSON.parse(jsonConfig.value)
    selectedConfig.value = parsed
  } catch (error) {
    // 忽略JSON解析错误，用户可能正在编辑
  }
}

function handleSimulate() {
  if (!simulationRole.value || !simulationPath.value) {
    $message.warning('请填写模拟参数')
    return
  }
  
  // 模拟权限检查
  const result = simulatePermissionCheck(
    simulationRole.value,
    simulationPath.value,
    selectedConfig.value
  )
  
  simulationResult.value = result
}

function simulatePermissionCheck(role, path, config) {
  // 简单的模拟逻辑
  if (!config.rules || config.rules.length === 0) {
    return {
      allowed: false,
      reason: '没有配置权限规则'
    }
  }
  
  for (const rule of config.rules) {
    if (pathMatches(path, rule.resource_path)) {
      return {
        allowed: true,
        reason: `匹配规则: ${rule.resource_path}`
      }
    }
  }
  
  return {
    allowed: false,
    reason: '没有匹配的权限规则'
  }
}

function pathMatches(path, pattern) {
  // 简单的路径匹配逻辑
  if (pattern.includes('*')) {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'))
    return regex.test(path)
  }
  return path === pattern
}

// 渲染方法
function renderConfigLabel({ option }) {
  return h('span', { class: 'config-label' }, [
    h('span', { class: 'config-name' }, option.name),
    h('span', { class: 'config-type' }, ` (${option.type})`)
  ])
}

function renderConfigIcon({ option }) {
  const iconMap = {
    role: 'material-symbols:person',
    api: 'material-symbols:api',
    menu: 'material-symbols:menu',
    data: 'material-symbols:database'
  }
  return h(TheIcon, { icon: iconMap[option.type] || 'material-symbols:settings', size: 16 })
}

function renderConfigActions({ option }) {
  return h('div', { class: 'config-actions' }, [
    h(NButton, {
      size: 'tiny',
      onClick: (e) => {
        e.stopPropagation()
        handleEditConfig(option)
      }
    }, () => h(TheIcon, { icon: 'material-symbols:edit', size: 12 })),
    h(NPopconfirm, {
      onPositiveClick: () => handleDeleteConfig(option)
    }, {
      trigger: () => h(NButton, {
        size: 'tiny',
        type: 'error',
        onClick: (e) => e.stopPropagation()
      }, () => h(TheIcon, { icon: 'material-symbols:delete', size: 12 })),
      default: () => '确定删除此配置吗？'
    })
  ])
}

function handleEditConfig(config) {
  selectedKeys.value = [config.key]
  selectedConfig.value = { ...config }
}

async function handleDeleteConfig(config) {
  try {
    if (config.id) {
      await systemV2Api.deletePermissionConfig(config.id)
    }
    
    // 从树中移除
    removeConfigFromTree(configTree.value, config.key)
    
    if (selectedConfig.value?.key === config.key) {
      selectedConfig.value = null
      selectedKeys.value = []
    }
    
    $message.success('配置删除成功')
  } catch (error) {
    $message.error('删除配置失败')
    console.error('Delete config error:', error)
  }
}

function removeConfigFromTree(configs, key) {
  for (let i = 0; i < configs.length; i++) {
    if (configs[i].key === key) {
      configs.splice(i, 1)
      return true
    }
    if (configs[i].children) {
      if (removeConfigFromTree(configs[i].children, key)) {
        return true
      }
    }
  }
  return false
}
</script>

<style scoped>
.permission-editor {
  height: 100%;
}

.editor-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 200px);
}

.config-tree-panel {
  width: 300px;
  flex-shrink: 0;
}

.config-tree-card {
  height: 100%;
}

.editor-panel {
  flex: 1;
  overflow: hidden;
}

.empty-editor {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-secondary);
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
}

.config-editor {
  height: 100%;
}

.basic-config {
  padding: 16px 0;
  max-width: 600px;
}

.permission-rules {
  padding: 16px 0;
}

.rules-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.rules-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rule-item {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
}

.rule-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.rule-title {
  font-weight: 500;
}

.rule-actions {
  display: flex;
  gap: 4px;
}

.condition-config {
  padding: 16px 0;
}

.condition-builder {
  margin-bottom: 24px;
}

.condition-builder h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.condition-desc {
  margin: 0 0 16px 0;
  color: var(--text-color-secondary);
  font-size: 14px;
}

.condition-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.condition-group {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.group-title {
  font-weight: 500;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.condition-preview h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 500;
}

.json-editor {
  padding: 16px 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.json-toolbar {
  margin-bottom: 16px;
}

.json-content {
  flex: 1;
}

.config-preview {
  padding: 16px 0;
}

.effect-preview h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
}

.simulation-controls {
  margin-bottom: 16px;
}

.simulation-result {
  margin-top: 16px;
}

.config-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-name {
  font-weight: 500;
}

.config-type {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.config-actions {
  display: flex;
  gap: 4px;
}

.mr-1 {
  margin-right: 4px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-3 {
  gap: 12px;
}
</style>