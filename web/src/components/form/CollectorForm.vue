<template>
  <n-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-placement="left"
    label-width="120px"
    require-mark-placement="right-hanging"
  >
    <!-- 基础信息 -->
    <n-card title="基础信息" class="mb-4">
      <n-form-item label="采集器名称" path="name">
        <n-input
          v-model:value="formData.name"
          placeholder="请输入采集器名称"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item label="采集器类型" path="collector_type">
        <n-select
          v-model:value="formData.collector_type"
          :options="collectorTypeOptions"
          placeholder="请选择采集器类型"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item label="描述" path="description">
        <n-input
          v-model:value="formData.description"
          type="textarea"
          placeholder="请输入采集器描述"
          :autosize="{ minRows: 2, maxRows: 4 }"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item label="状态" path="is_active">
        <n-switch v-model:value="formData.is_active" :disabled="readonly">
          <template #checked>启用</template>
          <template #unchecked>禁用</template>
        </n-switch>
      </n-form-item>
    </n-card>

    <!-- 连接配置 -->
    <n-card title="连接配置" class="mb-4">
      <n-form-item label="API地址" path="config.api_url">
        <n-input
          v-model:value="formData.config.api_url"
          placeholder="请输入API地址"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item label="认证方式" path="config.auth_type">
        <n-select
          v-model:value="formData.config.auth_type"
          :options="authTypeOptions"
          placeholder="请选择认证方式"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item v-if="formData.config.auth_type === 'token'" label="Token" path="config.token">
        <n-input
          v-model:value="formData.config.token"
          type="password"
          placeholder="请输入Token"
          show-password-on="click"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item
        v-if="formData.config.auth_type === 'basic'"
        label="用户名"
        path="config.username"
      >
        <n-input
          v-model:value="formData.config.username"
          placeholder="请输入用户名"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item v-if="formData.config.auth_type === 'basic'" label="密码" path="config.password">
        <n-input
          v-model:value="formData.config.password"
          type="password"
          placeholder="请输入密码"
          show-password-on="click"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item label="超时时间(秒)" path="config.timeout">
        <n-input-number
          v-model:value="formData.config.timeout"
          :min="1"
          :max="300"
          placeholder="请输入超时时间"
          :disabled="readonly"
        />
      </n-form-item>
    </n-card>

    <!-- 调度配置 -->
    <n-card title="调度配置" class="mb-4">
      <n-form-item label="调度类型" path="schedule_type">
        <n-select
          v-model:value="formData.schedule_type"
          :options="scheduleTypeOptions"
          placeholder="请选择调度类型"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item
        v-if="formData.schedule_type === 'interval'"
        label="执行间隔(秒)"
        path="schedule_config.interval"
      >
        <n-input-number
          v-model:value="formData.schedule_config.interval"
          :min="10"
          placeholder="请输入执行间隔"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item
        v-if="formData.schedule_type === 'cron'"
        label="Cron表达式"
        path="schedule_config.cron"
      >
        <n-input
          v-model:value="formData.schedule_config.cron"
          placeholder="请输入Cron表达式，如：0 */5 * * * *"
          :disabled="readonly"
        />
      </n-form-item>
    </n-card>

    <!-- 数据处理配置 -->
    <n-card title="数据处理配置" class="mb-4">
      <n-form-item label="数据映射" path="config.field_mapping">
        <n-dynamic-input
          v-model:value="formData.config.field_mapping"
          :on-create="createFieldMapping"
          :disabled="readonly"
        >
          <template #default="{ value }">
            <div class="w-full flex gap-2">
              <n-input
                v-model:value="value.source"
                placeholder="源字段"
                class="flex-1"
                :disabled="readonly"
              />
              <n-input
                v-model:value="value.target"
                placeholder="目标字段"
                class="flex-1"
                :disabled="readonly"
              />
            </div>
          </template>
        </n-dynamic-input>
      </n-form-item>

      <n-form-item label="存储配置" path="config.storage">
        <n-select
          v-model:value="formData.config.storage.type"
          :options="storageTypeOptions"
          placeholder="请选择存储类型"
          :disabled="readonly"
        />
      </n-form-item>

      <n-form-item
        v-if="formData.config.storage.type"
        label="存储表名"
        path="config.storage.table_name"
      >
        <n-input
          v-model:value="formData.config.storage.table_name"
          placeholder="请输入存储表名"
          :disabled="readonly"
        />
      </n-form-item>
    </n-card>

    <!-- 操作按钮 -->
    <div v-if="!readonly" class="flex justify-end gap-3">
      <n-button @click="handleReset">重置</n-button>
      <n-button type="primary" :loading="loading" @click="handleSubmit">
        {{ isEdit ? '更新' : '创建' }}
      </n-button>
      <n-button v-if="!isEdit" type="info" :loading="testLoading" @click="handleTestConnection">
        测试连接
      </n-button>
    </div>
  </n-form>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NCard,
  NButton,
  NDynamicInput,
  useMessage,
} from 'naive-ui'

/**
 * 采集器配置表单组件
 * 支持创建和编辑采集器配置
 */
const props = defineProps({
  // 表单数据
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  // 是否为编辑模式
  isEdit: {
    type: Boolean,
    default: false,
  },
  // 是否只读
  readonly: {
    type: Boolean,
    default: false,
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'submit', 'test-connection'])
const message = useMessage()

// 表单引用
const formRef = ref(null)
const testLoading = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  collector_type: 'web_api',
  description: '',
  is_active: true,
  schedule_type: 'interval',
  schedule_config: {
    interval: 300,
    cron: '',
  },
  config: {
    api_url: '',
    auth_type: 'none',
    token: '',
    username: '',
    password: '',
    timeout: 30,
    field_mapping: [],
    storage: {
      type: 'postgresql',
      table_name: '',
    },
  },
  ...props.modelValue,
})

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    Object.assign(formData, {
      name: '',
      collector_type: 'web_api',
      description: '',
      is_active: true,
      schedule_type: 'interval',
      schedule_config: {
        interval: 300,
        cron: '',
      },
      config: {
        api_url: '',
        auth_type: 'none',
        token: '',
        username: '',
        password: '',
        timeout: 30,
        field_mapping: [],
        storage: {
          type: 'postgresql',
          table_name: '',
        },
      },
      ...newVal,
    })
  },
  { deep: true, immediate: true }
)

// 监听表单数据变化
watch(
  formData,
  (newVal) => {
    emit('update:modelValue', newVal)
  },
  { deep: true }
)

// 选项配置
const collectorTypeOptions = [
  { label: 'Web API', value: 'web_api' },
  { label: 'MQTT', value: 'mqtt' },
  { label: '数据库', value: 'database' },
  { label: '文件', value: 'file' },
]

const authTypeOptions = [
  { label: '无认证', value: 'none' },
  { label: 'Token认证', value: 'token' },
  { label: '基础认证', value: 'basic' },
]

const scheduleTypeOptions = [
  { label: '定时执行', value: 'interval' },
  { label: 'Cron表达式', value: 'cron' },
  { label: '手动执行', value: 'manual' },
]

const storageTypeOptions = [
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'TDengine', value: 'tdengine' },
]

// 表单验证规则
const rules = {
  name: {
    required: true,
    message: '请输入采集器名称',
    trigger: ['input', 'blur'],
  },
  collector_type: {
    required: true,
    message: '请选择采集器类型',
    trigger: ['change', 'blur'],
  },
  'config.api_url': {
    required: true,
    message: '请输入API地址',
    trigger: ['input', 'blur'],
  },
  'config.timeout': {
    required: true,
    type: 'number',
    message: '请输入有效的超时时间',
    trigger: ['input', 'blur'],
  },
  'schedule_config.interval': {
    required: computed(() => formData.schedule_type === 'interval'),
    type: 'number',
    message: '请输入有效的执行间隔',
    trigger: ['input', 'blur'],
  },
  'schedule_config.cron': {
    required: computed(() => formData.schedule_type === 'cron'),
    message: '请输入Cron表达式',
    trigger: ['input', 'blur'],
  },
}

// 创建字段映射
const createFieldMapping = () => {
  return {
    source: '',
    target: '',
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    emit('submit', formData)
  } catch (error) {
    message.error('请检查表单输入')
  }
}

// 重置表单
const handleReset = () => {
  formRef.value?.restoreValidation()
  Object.assign(formData, {
    name: '',
    collector_type: 'web_api',
    description: '',
    is_active: true,
    schedule_type: 'interval',
    schedule_config: {
      interval: 300,
      cron: '',
    },
    config: {
      api_url: '',
      auth_type: 'none',
      token: '',
      username: '',
      password: '',
      timeout: 30,
      field_mapping: [],
      storage: {
        type: 'postgresql',
        table_name: '',
      },
    },
  })
}

// 测试连接
const handleTestConnection = async () => {
  try {
    await formRef.value?.validate(['config.api_url', 'config.timeout'])
    testLoading.value = true
    emit('test-connection', {
      api_url: formData.config.api_url,
      auth_type: formData.config.auth_type,
      token: formData.config.token,
      username: formData.config.username,
      password: formData.config.password,
      timeout: formData.config.timeout,
    })
  } catch (error) {
    message.error('请先填写连接配置')
  } finally {
    testLoading.value = false
  }
}

// 暴露方法
defineExpose({
  validate: () => formRef.value?.validate(),
  reset: handleReset,
})
</script>

<style scoped>
.flex {
  display: flex;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-3 {
  gap: 0.75rem;
}

.w-full {
  width: 100%;
}

.flex-1 {
  flex: 1;
}

.justify-end {
  justify-content: flex-end;
}

.mb-4 {
  margin-bottom: 1rem;
}
</style>
