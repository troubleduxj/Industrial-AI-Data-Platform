<template>
  <div class="quality-check">
    <n-card title="质量检查" size="small">
      <template #header-extra>
        <n-button size="small" type="primary" :loading="checking" @click="startQualityCheck">
          开始检查
        </n-button>
      </template>

      <n-space vertical>
        <!-- 检查配置 -->
        <n-form
          ref="formRef"
          :model="checkConfig"
          label-placement="left"
          label-width="80px"
          size="small"
        >
          <n-form-item label="检查类型">
            <n-select
              v-model:value="checkConfig.type"
              :options="checkTypeOptions"
              placeholder="选择检查类型"
            />
          </n-form-item>

          <n-form-item label="检查范围">
            <n-select
              v-model:value="checkConfig.scope"
              :options="scopeOptions"
              placeholder="选择检查范围"
            />
          </n-form-item>

          <n-form-item label="质量阈值">
            <n-slider
              v-model:value="checkConfig.threshold"
              :min="0"
              :max="100"
              :step="5"
              :marks="{ 60: '60%', 80: '80%', 95: '95%' }"
            />
          </n-form-item>
        </n-form>

        <!-- 检查结果 -->
        <div v-if="checkResult" class="check-result">
          <n-divider title-placement="left">检查结果</n-divider>

          <n-grid cols="2" x-gap="12" y-gap="8">
            <n-grid-item>
              <n-statistic label="总数据量" :value="checkResult.total" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="已检查" :value="checkResult.checked" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="通过率" :value="checkResult.passRate" suffix="%" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="问题数量" :value="checkResult.issues" />
            </n-grid-item>
          </n-grid>

          <!-- 问题列表 -->
          <div v-if="checkResult.issueList.length > 0" class="issue-list">
            <n-divider title-placement="left">问题详情</n-divider>

            <n-list>
              <n-list-item v-for="issue in checkResult.issueList" :key="issue.id">
                <n-thing>
                  <template #header>
                    <n-space align="center">
                      <n-tag :type="getIssueType(issue.severity)" size="small">
                        {{ getSeverityText(issue.severity) }}
                      </n-tag>
                      <n-text>数据ID: {{ issue.dataId }}</n-text>
                    </n-space>
                  </template>

                  <template #description>
                    <n-text depth="3">{{ issue.description }}</n-text>
                  </template>

                  <template #action>
                    <n-space>
                      <n-button size="small" @click="viewIssue(issue)"> 查看 </n-button>
                      <n-button size="small" type="primary" @click="fixIssue(issue)">
                        修复
                      </n-button>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>
        </div>

        <!-- 检查进度 -->
        <div v-if="checking" class="check-progress">
          <n-progress type="line" :percentage="checkProgress" :show-indicator="false" />
          <n-text depth="3" style="font-size: 12px; margin-top: 4px">
            正在检查... {{ checkProgress }}%
          </n-text>
        </div>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  NCard,
  NButton,
  NSpace,
  NForm,
  NFormItem,
  NSelect,
  NSlider,
  NDivider,
  NGrid,
  NGridItem,
  NStatistic,
  NList,
  NListItem,
  NThing,
  NTag,
  NText,
  NProgress,
  useMessage,
} from 'naive-ui'

// Message
const message = useMessage()

// Props
const props = defineProps({
  projectType: {
    type: String,
    default: 'classification',
  },
})

// Emits
const emit = defineEmits(['issue-selected'])

// 检查配置
const checkConfig = reactive({
  type: 'consistency',
  scope: 'all',
  threshold: 80,
})

// 检查类型选项
const checkTypeOptions = [
  { label: '一致性检查', value: 'consistency' },
  { label: '完整性检查', value: 'completeness' },
  { label: '准确性检查', value: 'accuracy' },
  { label: '规范性检查', value: 'compliance' },
]

// 检查范围选项
const scopeOptions = [
  { label: '全部数据', value: 'all' },
  { label: '最近标注', value: 'recent' },
  { label: '随机抽样', value: 'random' },
  { label: '指定范围', value: 'custom' },
]

// 检查状态
const checking = ref(false)
const checkProgress = ref(0)
const checkResult = ref(null)

// 开始质量检查
const startQualityCheck = async () => {
  checking.value = true
  checkProgress.value = 0
  checkResult.value = null

  try {
    // 模拟检查过程
    const interval = setInterval(() => {
      checkProgress.value += 10
      if (checkProgress.value >= 100) {
        clearInterval(interval)

        // 模拟检查结果
        checkResult.value = {
          total: 1000,
          checked: 1000,
          passRate: 85.6,
          issues: 144,
          issueList: [
            {
              id: 1,
              dataId: 'D001',
              severity: 'high',
              description: '标注框超出图像边界',
            },
            {
              id: 2,
              dataId: 'D002',
              severity: 'medium',
              description: '类别标签不一致',
            },
            {
              id: 3,
              dataId: 'D003',
              severity: 'low',
              description: '标注精度不足',
            },
          ],
        }

        checking.value = false
        message.success('质量检查完成')
      }
    }, 200)
  } catch (error) {
    checking.value = false
    message.error('检查失败: ' + error.message)
  }
}

// 获取问题严重程度类型
const getIssueType = (severity) => {
  const typeMap = {
    high: 'error',
    medium: 'warning',
    low: 'info',
  }
  return typeMap[severity] || 'default'
}

// 获取严重程度文本
const getSeverityText = (severity) => {
  const textMap = {
    high: '严重',
    medium: '中等',
    low: '轻微',
  }
  return textMap[severity] || severity
}

// 查看问题
const viewIssue = (issue) => {
  emit('issue-selected', issue)
  message.info(`查看问题: ${issue.description}`)
}

// 修复问题
const fixIssue = (issue) => {
  message.info(`修复问题: ${issue.description}`)
}
</script>

<style scoped>
.quality-check {
  height: 100%;
}

.check-result {
  margin-top: 16px;
}

.issue-list {
  margin-top: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.check-progress {
  margin-top: 16px;
}
</style>
