<template>
  <div class="annotation-tools">
    <!-- 分类标注工具 -->
    <div v-if="project?.type === 'classification'" class="classification-tools">
      <n-card title="分类标注" size="small">
        <n-space vertical>
          <n-form-item label="类别选择">
            <n-select
              v-model:value="localAnnotation.category"
              :options="classificationOptions"
              placeholder="选择类别"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>

          <n-form-item label="置信度">
            <n-slider
              v-model:value="localAnnotation.confidence"
              :min="0"
              :max="1"
              :step="0.01"
              :format-tooltip="(value) => (value * 100).toFixed(0) + '%'"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>

          <n-form-item label="备注">
            <n-input
              v-model:value="localAnnotation.notes"
              type="textarea"
              placeholder="添加备注信息"
              :autosize="{ minRows: 2, maxRows: 4 }"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>
        </n-space>
      </n-card>
    </div>

    <!-- 目标检测标注工具 -->
    <div v-else-if="project?.type === 'detection'" class="detection-tools">
      <n-card title="目标检测标注" size="small">
        <n-space vertical>
          <n-form-item label="检测对象">
            <n-select
              v-model:value="selectedDetectionClass"
              :options="detectionClassOptions"
              placeholder="选择检测类别"
            />
          </n-form-item>

          <n-form-item label="绘制模式">
            <n-radio-group v-model:value="drawingMode">
              <n-space>
                <n-radio value="box">矩形框</n-radio>
                <n-radio value="polygon">多边形</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-divider style="margin: 12px 0" />

          <div class="detection-list">
            <n-text strong style="margin-bottom: 8px; display: block">检测框列表</n-text>
            <n-list v-if="localAnnotation.boxes?.length">
              <n-list-item
                v-for="(box, index) in localAnnotation.boxes"
                :key="index"
                class="detection-item"
              >
                <n-space justify="space-between" align="center" style="width: 100%">
                  <div>
                    <n-text>{{ box.label }}</n-text>
                    <br />
                    <n-text depth="3" style="font-size: 12px">
                      ({{ box.x.toFixed(0) }}, {{ box.y.toFixed(0) }}) {{ box.width.toFixed(0) }}×{{
                        box.height.toFixed(0)
                      }}
                    </n-text>
                  </div>
                  <n-space>
                    <n-button size="tiny" @click="editDetection(index)">
                      <template #icon>
                        <n-icon><create-outline /></n-icon>
                      </template>
                    </n-button>
                    <n-button size="tiny" type="error" @click="deleteDetection(index)">
                      <template #icon>
                        <n-icon><trash-outline /></n-icon>
                      </template>
                    </n-button>
                  </n-space>
                </n-space>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无检测框" size="small" />
          </div>
        </n-space>
      </n-card>
    </div>

    <!-- 图像分割标注工具 -->
    <div v-else-if="project?.type === 'segmentation'" class="segmentation-tools">
      <n-card title="图像分割标注" size="small">
        <n-space vertical>
          <n-form-item label="分割类别">
            <n-select
              v-model:value="selectedSegmentationClass"
              :options="segmentationClassOptions"
              placeholder="选择分割类别"
            />
          </n-form-item>

          <n-form-item label="绘制工具">
            <n-radio-group v-model:value="segmentationTool">
              <n-space vertical>
                <n-radio value="polygon">多边形工具</n-radio>
                <n-radio value="brush">画笔工具</n-radio>
                <n-radio value="magic">魔术棒</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-form-item v-if="segmentationTool === 'brush'" label="画笔大小">
            <n-slider
              v-model:value="brushSize"
              :min="1"
              :max="50"
              :step="1"
              :format-tooltip="(value) => value + 'px'"
            />
          </n-form-item>

          <n-divider style="margin: 12px 0" />

          <div class="segmentation-list">
            <n-text strong style="margin-bottom: 8px; display: block">分割区域</n-text>
            <n-list v-if="localAnnotation.masks?.length">
              <n-list-item
                v-for="(mask, index) in localAnnotation.masks"
                :key="index"
                class="segmentation-item"
              >
                <n-space justify="space-between" align="center" style="width: 100%">
                  <div>
                    <n-text>{{ mask.label }}</n-text>
                    <br />
                    <n-text depth="3" style="font-size: 12px">
                      {{ mask.points?.length || 0 }} 个点
                    </n-text>
                  </div>
                  <n-space>
                    <n-button size="tiny" @click="editSegmentation(index)">
                      <template #icon>
                        <n-icon><create-outline /></n-icon>
                      </template>
                    </n-button>
                    <n-button size="tiny" type="error" @click="deleteSegmentation(index)">
                      <template #icon>
                        <n-icon><trash-outline /></n-icon>
                      </template>
                    </n-button>
                  </n-space>
                </n-space>
              </n-list-item>
            </n-list>
            <n-empty v-else description="暂无分割区域" size="small" />
          </div>
        </n-space>
      </n-card>
    </div>

    <!-- 回归标注工具 -->
    <div v-else-if="project?.type === 'regression'" class="regression-tools">
      <n-card title="回归标注" size="small">
        <n-space vertical>
          <n-form-item label="目标值">
            <n-input-number
              v-model:value="localAnnotation.targetValue"
              placeholder="输入目标值"
              style="width: 100%"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>

          <n-form-item label="预测值">
            <n-input-number
              v-model:value="localAnnotation.predictedValue"
              placeholder="输入预测值"
              style="width: 100%"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>

          <n-form-item label="误差">
            <n-statistic
              label="绝对误差"
              :value="
                Math.abs(
                  (localAnnotation.targetValue || 0) - (localAnnotation.predictedValue || 0)
                ).toFixed(2)
              "
            />
          </n-form-item>

          <n-form-item label="质量评级">
            <n-rate
              v-model:value="localAnnotation.quality"
              :count="5"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>

          <n-form-item label="备注">
            <n-input
              v-model:value="localAnnotation.notes"
              type="textarea"
              placeholder="添加备注信息"
              :autosize="{ minRows: 2, maxRows: 4 }"
              @update:value="handleAnnotationChange"
            />
          </n-form-item>
        </n-space>
      </n-card>
    </div>

    <!-- 通用操作按钮 -->
    <n-card title="操作" size="small" style="margin-top: 16px">
      <n-space>
        <n-button type="primary" :disabled="!isAnnotationValid" @click="markAsCompleted">
          <template #icon>
            <n-icon><checkmark-outline /></n-icon>
          </template>
          标记完成
        </n-button>

        <n-button @click="markAsSkipped">
          <template #icon>
            <n-icon><play-skip-forward-outline /></n-icon>
          </template>
          跳过
        </n-button>

        <n-button @click="resetAnnotation">
          <template #icon>
            <n-icon><refresh-outline /></n-icon>
          </template>
          重置
        </n-button>
      </n-space>
    </n-card>

    <!-- 快捷键提示 -->
    <n-card title="快捷键" size="small" style="margin-top: 16px">
      <n-space vertical size="small">
        <div class="shortcut-item">
          <n-text code>Space</n-text>
          <n-text depth="3">标记完成</n-text>
        </div>
        <div class="shortcut-item">
          <n-text code>S</n-text>
          <n-text depth="3">跳过当前</n-text>
        </div>
        <div class="shortcut-item">
          <n-text code>R</n-text>
          <n-text depth="3">重置标注</n-text>
        </div>
        <div class="shortcut-item">
          <n-text code>←/→</n-text>
          <n-text depth="3">上一条/下一条</n-text>
        </div>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  NCard,
  NSpace,
  NFormItem,
  NSelect,
  NSlider,
  NInput,
  NInputNumber,
  NRadioGroup,
  NRadio,
  NDivider,
  NList,
  NListItem,
  NText,
  NButton,
  NIcon,
  NEmpty,
  NStatistic,
  NRate,
  useMessage,
} from 'naive-ui'
import {
  CreateOutline,
  TrashOutline,
  CheckmarkOutline,
  PlaySkipForwardOutline,
  RefreshOutline,
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  project: {
    type: Object,
    default: null,
  },
  currentAnnotation: {
    type: Object,
    default: null,
  },
})

// Emits
const emit = defineEmits(['annotation-change'])

// 响应式数据
const localAnnotation = ref({})
const selectedDetectionClass = ref('异常')
const drawingMode = ref('box')
const selectedSegmentationClass = ref('关键区域')
const segmentationTool = ref('polygon')
const brushSize = ref(10)

// 消息提示
const message = useMessage()

// 分类选项
const classificationOptions = [
  { label: '正常', value: 'normal' },
  { label: '异常', value: 'abnormal' },
  { label: '警告', value: 'warning' },
  { label: '严重', value: 'critical' },
]

// 检测类别选项
const detectionClassOptions = [
  { label: '异常区域', value: '异常' },
  { label: '关键部件', value: '部件' },
  { label: '损坏区域', value: '损坏' },
  { label: '磨损区域', value: '磨损' },
]

// 分割类别选项
const segmentationClassOptions = [
  { label: '关键区域', value: '关键区域' },
  { label: '异常区域', value: '异常区域' },
  { label: '背景区域', value: '背景区域' },
  { label: '边界区域', value: '边界区域' },
]

// 计算标注是否有效
const isAnnotationValid = computed(() => {
  if (!props.project || !localAnnotation.value) return false

  switch (props.project.type) {
    case 'classification':
      return !!localAnnotation.value.category
    case 'detection':
      return localAnnotation.value.boxes && localAnnotation.value.boxes.length > 0
    case 'segmentation':
      return localAnnotation.value.masks && localAnnotation.value.masks.length > 0
    case 'regression':
      return (
        localAnnotation.value.targetValue !== undefined &&
        localAnnotation.value.targetValue !== null
      )
    default:
      return false
  }
})

// 处理标注变化
const handleAnnotationChange = () => {
  emit('annotation-change', localAnnotation.value)
}

// 编辑检测框
const editDetection = (index) => {
  message.info(`编辑检测框 ${index + 1}`)
  // 这里可以实现检测框编辑逻辑
}

// 删除检测框
const deleteDetection = (index) => {
  if (localAnnotation.value.boxes) {
    localAnnotation.value.boxes.splice(index, 1)
    handleAnnotationChange()
    message.success('检测框已删除')
  }
}

// 编辑分割区域
const editSegmentation = (index) => {
  message.info(`编辑分割区域 ${index + 1}`)
  // 这里可以实现分割区域编辑逻辑
}

// 删除分割区域
const deleteSegmentation = (index) => {
  if (localAnnotation.value.masks) {
    localAnnotation.value.masks.splice(index, 1)
    handleAnnotationChange()
    message.success('分割区域已删除')
  }
}

// 标记为完成
const markAsCompleted = () => {
  if (isAnnotationValid.value) {
    localAnnotation.value.status = 'completed'
    localAnnotation.value.completedAt = new Date().toISOString()
    handleAnnotationChange()
    message.success('标注已完成')
  } else {
    message.warning('请完成必要的标注信息')
  }
}

// 标记为跳过
const markAsSkipped = () => {
  localAnnotation.value.status = 'skipped'
  localAnnotation.value.skippedAt = new Date().toISOString()
  handleAnnotationChange()
  message.info('已跳过当前数据')
}

// 重置标注
const resetAnnotation = () => {
  const defaultAnnotation = getDefaultAnnotation()
  localAnnotation.value = { ...defaultAnnotation }
  handleAnnotationChange()
  message.info('标注已重置')
}

// 获取默认标注
const getDefaultAnnotation = () => {
  const base = {
    status: 'pending',
    annotator: props.currentAnnotation?.annotator || '当前用户',
    createdAt: new Date().toISOString(),
  }

  switch (props.project?.type) {
    case 'classification':
      return {
        ...base,
        category: null,
        confidence: 0.8,
        notes: '',
      }
    case 'detection':
      return {
        ...base,
        boxes: [],
      }
    case 'segmentation':
      return {
        ...base,
        masks: [],
      }
    case 'regression':
      return {
        ...base,
        targetValue: null,
        predictedValue: null,
        quality: 3,
        notes: '',
      }
    default:
      return base
  }
}

// 处理键盘快捷键
const handleKeydown = (e) => {
  switch (e.key) {
    case ' ': // Space
      e.preventDefault()
      markAsCompleted()
      break
    case 's':
    case 'S':
      e.preventDefault()
      markAsSkipped()
      break
    case 'r':
    case 'R':
      e.preventDefault()
      resetAnnotation()
      break
  }
}

// 监听当前标注变化
watch(
  () => props.currentAnnotation,
  (newAnnotation) => {
    if (newAnnotation) {
      localAnnotation.value = { ...newAnnotation }
    } else {
      localAnnotation.value = getDefaultAnnotation()
    }
  },
  { immediate: true, deep: true }
)

// 组件挂载时添加键盘监听
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

// 组件卸载时移除键盘监听
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.annotation-tools {
  height: 100%;
  overflow-y: auto;
}

.detection-item,
.segmentation-item {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 8px;
  padding: 8px;
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
