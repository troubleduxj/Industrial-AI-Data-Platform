<template>
  <div class="rule-editor">
    <!-- 条件编辑器 -->
    <n-card title="条件配置" size="small" :bordered="true">
      <template #header-extra>
        <n-radio-group v-model:value="conditionType" size="small">
          <n-radio-button value="AND">全部满足 (AND)</n-radio-button>
          <n-radio-button value="OR">任一满足 (OR)</n-radio-button>
        </n-radio-group>
      </template>
      
      <div class="conditions-list">
        <div v-for="(condition, index) in conditions" :key="index" class="condition-item">
          <n-space align="center">
            <n-select
              v-model:value="condition.field"
              :options="fieldOptions"
              placeholder="选择字段"
              style="width: 150px;"
              filterable
              tag
            />
            <n-select
              v-model:value="condition.operator"
              :options="operatorOptions"
              placeholder="运算符"
              style="width: 120px;"
            />
            <template v-if="condition.operator === 'between'">
              <n-input-number v-model:value="condition.value[0]" placeholder="最小值" style="width: 100px;" />
              <span>至</span>
              <n-input-number v-model:value="condition.value[1]" placeholder="最大值" style="width: 100px;" />
            </template>
            <template v-else-if="condition.operator === 'in' || condition.operator === 'not_in'">
              <n-dynamic-tags v-model:value="condition.value" />
            </template>
            <template v-else>
              <n-input v-model:value="condition.value" placeholder="值" style="width: 150px;" />
            </template>
            <n-button text type="error" @click="removeCondition(index)">
              <template #icon><n-icon><CloseOutline /></n-icon></template>
            </n-button>
          </n-space>
        </div>
      </div>
      
      <n-button dashed block @click="addCondition" style="margin-top: 12px;">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        添加条件
      </n-button>
    </n-card>

    <!-- 动作编辑器 -->
    <n-card title="动作配置" size="small" :bordered="true" style="margin-top: 16px;">
      <div class="actions-list">
        <div v-for="(action, index) in actions" :key="index" class="action-item">
          <n-card size="small" :bordered="true">
            <template #header>
              <n-space align="center">
                <n-select
                  v-model:value="action.type"
                  :options="actionTypeOptions"
                  placeholder="动作类型"
                  style="width: 150px;"
                  @update:value="onActionTypeChange(action)"
                />
                <n-button text type="error" @click="removeAction(index)">
                  <template #icon><n-icon><CloseOutline /></n-icon></template>
                </n-button>
              </n-space>
            </template>
            
            <!-- 告警动作配置 -->
            <template v-if="action.type === 'alert'">
              <n-form-item label="告警级别" label-placement="left" label-width="80px">
                <n-select
                  v-model:value="action.level"
                  :options="alertLevelOptions"
                  placeholder="选择级别"
                  style="width: 150px;"
                />
              </n-form-item>
              <n-form-item label="告警消息" label-placement="left" label-width="80px">
                <n-input v-model:value="action.message" placeholder="告警消息内容" />
              </n-form-item>
            </template>
            
            <!-- 通知动作配置 -->
            <template v-else-if="action.type === 'notification'">
              <n-form-item label="通知渠道" label-placement="left" label-width="80px">
                <n-checkbox-group v-model:value="action.channels">
                  <n-space>
                    <n-checkbox value="email">邮件</n-checkbox>
                    <n-checkbox value="sms">短信</n-checkbox>
                    <n-checkbox value="wechat">微信</n-checkbox>
                    <n-checkbox value="dingtalk">钉钉</n-checkbox>
                  </n-space>
                </n-checkbox-group>
              </n-form-item>
              <n-form-item label="接收人" label-placement="left" label-width="80px">
                <n-dynamic-tags v-model:value="action.recipients" />
              </n-form-item>
              <n-form-item label="消息内容" label-placement="left" label-width="80px">
                <n-input v-model:value="action.message" type="textarea" placeholder="通知消息内容" />
              </n-form-item>
            </template>
            
            <!-- Webhook动作配置 -->
            <template v-else-if="action.type === 'webhook'">
              <n-form-item label="URL" label-placement="left" label-width="80px">
                <n-input v-model:value="action.url" placeholder="Webhook URL" />
              </n-form-item>
              <n-form-item label="请求方法" label-placement="left" label-width="80px">
                <n-select
                  v-model:value="action.method"
                  :options="httpMethodOptions"
                  placeholder="选择方法"
                  style="width: 120px;"
                />
              </n-form-item>
              <n-form-item label="请求头" label-placement="left" label-width="80px">
                <n-input v-model:value="action.headers" type="textarea" placeholder='{"Content-Type": "application/json"}' :rows="2" />
              </n-form-item>
            </template>
            
            <!-- 工单动作配置 -->
            <template v-else-if="action.type === 'workorder'">
              <n-form-item label="工单类型" label-placement="left" label-width="80px">
                <n-select
                  v-model:value="action.workorder_type"
                  :options="workorderTypeOptions"
                  placeholder="选择类型"
                  style="width: 150px;"
                />
              </n-form-item>
              <n-form-item label="工单标题" label-placement="left" label-width="80px">
                <n-input v-model:value="action.title" placeholder="工单标题" />
              </n-form-item>
              <n-form-item label="工单描述" label-placement="left" label-width="80px">
                <n-input v-model:value="action.description" type="textarea" placeholder="工单描述" />
              </n-form-item>
              <n-form-item label="指派人" label-placement="left" label-width="80px">
                <n-input v-model:value="action.assignee" placeholder="指派人" />
              </n-form-item>
            </template>
          </n-card>
        </div>
      </div>
      
      <n-button dashed block @click="addAction" style="margin-top: 12px;">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        添加动作
      </n-button>
    </n-card>

    <!-- DSL预览 -->
    <n-card title="DSL预览" size="small" :bordered="true" style="margin-top: 16px;">
      <n-tabs type="line">
        <n-tab-pane name="conditions" tab="条件DSL">
          <pre class="dsl-preview">{{ conditionsDSL }}</pre>
        </n-tab-pane>
        <n-tab-pane name="actions" tab="动作DSL">
          <pre class="dsl-preview">{{ actionsDSL }}</pre>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { AddOutline, CloseOutline } from '@vicons/ionicons5'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      conditions: { type: 'AND', rules: [] },
      actions: []
    })
  }
})

const emit = defineEmits(['update:modelValue'])

// 条件类型
const conditionType = ref('AND')

// 条件列表
const conditions = ref([])

// 动作列表
const actions = ref([])

// 字段选项
const fieldOptions = [
  { label: '预测值', value: 'predicted_value' },
  { label: '置信度', value: 'confidence' },
  { label: '异常分数', value: 'anomaly_score' },
  { label: '是否异常', value: 'is_anomaly' },
  { label: '模型ID', value: 'model_id' },
  { label: '资产ID', value: 'asset_id' },
  { label: '类别ID', value: 'category_id' }
]

// 运算符选项
const operatorOptions = [
  { label: '等于', value: 'eq' },
  { label: '不等于', value: 'ne' },
  { label: '大于', value: 'gt' },
  { label: '大于等于', value: 'gte' },
  { label: '小于', value: 'lt' },
  { label: '小于等于', value: 'lte' },
  { label: '在列表中', value: 'in' },
  { label: '不在列表中', value: 'not_in' },
  { label: '在范围内', value: 'between' },
  { label: '包含', value: 'contains' },
  { label: '以...开头', value: 'starts_with' },
  { label: '以...结尾', value: 'ends_with' }
]

// 动作类型选项
const actionTypeOptions = [
  { label: '告警', value: 'alert' },
  { label: '通知', value: 'notification' },
  { label: 'Webhook', value: 'webhook' },
  { label: '工单', value: 'workorder' }
]

// 告警级别选项
const alertLevelOptions = [
  { label: '信息', value: 'info' },
  { label: '警告', value: 'warning' },
  { label: '错误', value: 'error' },
  { label: '严重', value: 'critical' }
]

// HTTP方法选项
const httpMethodOptions = [
  { label: 'POST', value: 'POST' },
  { label: 'GET', value: 'GET' },
  { label: 'PUT', value: 'PUT' }
]

// 工单类型选项
const workorderTypeOptions = [
  { label: '维修工单', value: 'repair' },
  { label: '巡检工单', value: 'inspection' },
  { label: '保养工单', value: 'maintenance' }
]

// 初始化数据
const initFromModelValue = () => {
  if (props.modelValue?.conditions) {
    conditionType.value = props.modelValue.conditions.type || 'AND'
    conditions.value = (props.modelValue.conditions.rules || []).map(r => ({
      field: r.field,
      operator: r.operator,
      value: r.value
    }))
  }
  if (props.modelValue?.actions) {
    actions.value = [...props.modelValue.actions]
  }
}

// 添加条件
const addCondition = () => {
  conditions.value.push({
    field: 'predicted_value',
    operator: 'gt',
    value: ''
  })
}

// 移除条件
const removeCondition = (index) => {
  conditions.value.splice(index, 1)
}

// 添加动作
const addAction = () => {
  actions.value.push({
    type: 'alert',
    level: 'warning',
    message: ''
  })
}

// 移除动作
const removeAction = (index) => {
  actions.value.splice(index, 1)
}

// 动作类型变更时重置配置
const onActionTypeChange = (action) => {
  const type = action.type
  // 保留type，清除其他属性
  Object.keys(action).forEach(key => {
    if (key !== 'type') delete action[key]
  })
  
  // 设置默认值
  if (type === 'alert') {
    action.level = 'warning'
    action.message = ''
  } else if (type === 'notification') {
    action.channels = []
    action.recipients = []
    action.message = ''
  } else if (type === 'webhook') {
    action.url = ''
    action.method = 'POST'
    action.headers = ''
  } else if (type === 'workorder') {
    action.workorder_type = 'repair'
    action.title = ''
    action.description = ''
    action.assignee = ''
  }
}

// 条件DSL
const conditionsDSL = computed(() => {
  const dsl = {
    type: conditionType.value,
    rules: conditions.value.map(c => ({
      field: c.field,
      operator: c.operator,
      value: parseValue(c.value, c.operator)
    }))
  }
  return JSON.stringify(dsl, null, 2)
})

// 动作DSL
const actionsDSL = computed(() => {
  const dsl = actions.value.map(a => {
    const result = { type: a.type }
    Object.keys(a).forEach(key => {
      if (key !== 'type' && a[key] !== undefined && a[key] !== '') {
        result[key] = a[key]
      }
    })
    return result
  })
  return JSON.stringify(dsl, null, 2)
})

// 解析值
const parseValue = (value, operator) => {
  if (operator === 'between') {
    return Array.isArray(value) ? value : [0, 0]
  }
  if (operator === 'in' || operator === 'not_in') {
    return Array.isArray(value) ? value : []
  }
  // 尝试转换为数字
  const num = Number(value)
  if (!isNaN(num) && value !== '') {
    return num
  }
  // 布尔值
  if (value === 'true') return true
  if (value === 'false') return false
  return value
}

// 监听变化并发出更新
watch([conditionType, conditions, actions], () => {
  emit('update:modelValue', {
    conditions: JSON.parse(conditionsDSL.value),
    actions: JSON.parse(actionsDSL.value)
  })
}, { deep: true })

// 初始化
initFromModelValue()
</script>

<style scoped>
.rule-editor {
  width: 100%;
}

.conditions-list,
.actions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.condition-item,
.action-item {
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.dsl-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}
</style>
