<template>
  <div class="score-config">
    <n-card title="评分配置" size="small">
      <template #header-extra>
        <n-space>
          <n-button size="small" @click="resetConfig">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            重置
          </n-button>
          <n-button size="small" type="primary" @click="saveConfig">
            <template #icon>
              <n-icon><SaveOutline /></n-icon>
            </template>
            保存配置
          </n-button>
        </n-space>
      </template>

      <n-form
        ref="formRef"
        :model="configForm"
        :rules="rules"
        label-placement="left"
        label-width="120px"
        size="small"
      >
        <!-- 评分权重配置 -->
        <n-card title="评分权重" size="small" class="mb-4">
          <n-form-item label="温度权重" path="weights.temperature">
            <n-input-number
              v-model:value="configForm.weights.temperature"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >当前: {{ (configForm.weights.temperature * 100).toFixed(0) }}%</span
            >
          </n-form-item>

          <n-form-item label="振动权重" path="weights.vibration">
            <n-input-number
              v-model:value="configForm.weights.vibration"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >当前: {{ (configForm.weights.vibration * 100).toFixed(0) }}%</span
            >
          </n-form-item>

          <n-form-item label="电流权重" path="weights.current">
            <n-input-number
              v-model:value="configForm.weights.current"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >当前: {{ (configForm.weights.current * 100).toFixed(0) }}%</span
            >
          </n-form-item>

          <n-form-item label="压力权重" path="weights.pressure">
            <n-input-number
              v-model:value="configForm.weights.pressure"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >当前: {{ (configForm.weights.pressure * 100).toFixed(0) }}%</span
            >
          </n-form-item>

          <n-alert
            v-if="totalWeight !== 1"
            type="warning"
            title="权重提醒"
            :description="`当前权重总和为 ${(totalWeight * 100).toFixed(0)}%，建议调整为100%`"
            class="mt-2"
          />
        </n-card>

        <!-- 阈值配置 -->
        <n-card title="健康等级阈值" size="small" class="mb-4">
          <n-form-item label="优秀阈值" path="thresholds.excellent">
            <n-input-number
              v-model:value="configForm.thresholds.excellent"
              :min="0"
              :max="100"
              :step="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500">≥ {{ configForm.thresholds.excellent }} 分</span>
          </n-form-item>

          <n-form-item label="良好阈值" path="thresholds.good">
            <n-input-number
              v-model:value="configForm.thresholds.good"
              :min="0"
              :max="100"
              :step="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >{{ configForm.thresholds.good }} - {{ configForm.thresholds.excellent - 1 }} 分</span
            >
          </n-form-item>

          <n-form-item label="一般阈值" path="thresholds.average">
            <n-input-number
              v-model:value="configForm.thresholds.average"
              :min="0"
              :max="100"
              :step="1"
              style="width: 150px"
            />
            <span class="ml-2 text-gray-500"
              >{{ configForm.thresholds.average }} - {{ configForm.thresholds.good - 1 }} 分</span
            >
          </n-form-item>

          <n-form-item label="较差阈值">
            <span class="text-gray-500">< {{ configForm.thresholds.average }} 分</span>
          </n-form-item>
        </n-card>

        <!-- 参数范围配置 -->
        <n-card title="参数正常范围" size="small" class="mb-4">
          <n-form-item label="温度范围 (°C)">
            <n-space>
              <n-input-number
                v-model:value="configForm.ranges.temperature.min"
                :max="configForm.ranges.temperature.max"
                style="width: 100px"
                placeholder="最小值"
              />
              <span>-</span>
              <n-input-number
                v-model:value="configForm.ranges.temperature.max"
                :min="configForm.ranges.temperature.min"
                style="width: 100px"
                placeholder="最大值"
              />
            </n-space>
          </n-form-item>

          <n-form-item label="振动范围 (mm/s)">
            <n-space>
              <n-input-number
                v-model:value="configForm.ranges.vibration.min"
                :max="configForm.ranges.vibration.max"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最小值"
              />
              <span>-</span>
              <n-input-number
                v-model:value="configForm.ranges.vibration.max"
                :min="configForm.ranges.vibration.min"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最大值"
              />
            </n-space>
          </n-form-item>

          <n-form-item label="电流范围 (A)">
            <n-space>
              <n-input-number
                v-model:value="configForm.ranges.current.min"
                :max="configForm.ranges.current.max"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最小值"
              />
              <span>-</span>
              <n-input-number
                v-model:value="configForm.ranges.current.max"
                :min="configForm.ranges.current.min"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最大值"
              />
            </n-space>
          </n-form-item>

          <n-form-item label="压力范围 (MPa)">
            <n-space>
              <n-input-number
                v-model:value="configForm.ranges.pressure.min"
                :max="configForm.ranges.pressure.max"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最小值"
              />
              <span>-</span>
              <n-input-number
                v-model:value="configForm.ranges.pressure.max"
                :min="configForm.ranges.pressure.min"
                :step="0.1"
                :precision="1"
                style="width: 100px"
                placeholder="最大值"
              />
            </n-space>
          </n-form-item>
        </n-card>

        <!-- 预览效果 -->
        <n-card title="配置预览" size="small">
          <n-descriptions :column="2" bordered size="small">
            <n-descriptions-item label="权重总和">
              <n-tag :type="totalWeight === 1 ? 'success' : 'warning'">
                {{ (totalWeight * 100).toFixed(0) }}%
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="等级划分">
              <n-space vertical size="small">
                <n-tag type="success" size="small"
                  >优秀: ≥{{ configForm.thresholds.excellent }}</n-tag
                >
                <n-tag type="info" size="small"
                  >良好: {{ configForm.thresholds.good }}-{{
                    configForm.thresholds.excellent - 1
                  }}</n-tag
                >
                <n-tag type="warning" size="small"
                  >一般: {{ configForm.thresholds.average }}-{{
                    configForm.thresholds.good - 1
                  }}</n-tag
                >
                <n-tag type="error" size="small">较差: <{{ configForm.thresholds.average }}</n-tag>
              </n-space>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { RefreshOutline, SaveOutline } from '@vicons/ionicons5'

const message = useMessage()
const formRef = ref(null)

// 配置表单
const configForm = ref({
  weights: {
    temperature: 0.3,
    vibration: 0.2,
    current: 0.3,
    pressure: 0.2,
  },
  thresholds: {
    excellent: 90,
    good: 75,
    average: 60,
  },
  ranges: {
    temperature: { min: 20, max: 60 },
    vibration: { min: 0, max: 5 },
    current: { min: 5, max: 20 },
    pressure: { min: 0.2, max: 1.5 },
  },
})

// 默认配置
const defaultConfig = {
  weights: {
    temperature: 0.3,
    vibration: 0.2,
    current: 0.3,
    pressure: 0.2,
  },
  thresholds: {
    excellent: 90,
    good: 75,
    average: 60,
  },
  ranges: {
    temperature: { min: 20, max: 60 },
    vibration: { min: 0, max: 5 },
    current: { min: 5, max: 20 },
    pressure: { min: 0.2, max: 1.5 },
  },
}

// 表单验证规则
const rules = {
  'weights.temperature': {
    required: true,
    type: 'number',
    min: 0,
    max: 1,
    message: '温度权重必须在0-1之间',
  },
  'weights.vibration': {
    required: true,
    type: 'number',
    min: 0,
    max: 1,
    message: '振动权重必须在0-1之间',
  },
  'weights.current': {
    required: true,
    type: 'number',
    min: 0,
    max: 1,
    message: '电流权重必须在0-1之间',
  },
  'weights.pressure': {
    required: true,
    type: 'number',
    min: 0,
    max: 1,
    message: '压力权重必须在0-1之间',
  },
  'thresholds.excellent': {
    required: true,
    type: 'number',
    min: 0,
    max: 100,
    message: '优秀阈值必须在0-100之间',
  },
  'thresholds.good': {
    required: true,
    type: 'number',
    min: 0,
    max: 100,
    message: '良好阈值必须在0-100之间',
  },
  'thresholds.average': {
    required: true,
    type: 'number',
    min: 0,
    max: 100,
    message: '一般阈值必须在0-100之间',
  },
}

// 计算权重总和
const totalWeight = computed(() => {
  const weights = configForm.value.weights
  return weights.temperature + weights.vibration + weights.current + weights.pressure
})

// 加载配置
const loadConfig = async () => {
  try {
    // 模拟从API加载配置
    await new Promise((resolve) => setTimeout(resolve, 500))
    // 这里可以从后端加载实际配置
    message.success('配置加载成功')
  } catch (error) {
    message.error('加载配置失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    await formRef.value?.validate()

    if (Math.abs(totalWeight.value - 1) > 0.01) {
      message.warning('权重总和应该为100%，请调整权重配置')
      return
    }

    // 模拟保存到API
    await new Promise((resolve) => setTimeout(resolve, 1000))

    message.success('配置保存成功')
  } catch (error) {
    message.error('保存配置失败')
  }
}

// 重置配置
const resetConfig = () => {
  configForm.value = JSON.parse(JSON.stringify(defaultConfig))
  message.info('配置已重置为默认值')
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.score-config {
  height: 100%;
}

.mb-4 {
  margin-bottom: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.mt-2 {
  margin-top: 8px;
}
</style>
