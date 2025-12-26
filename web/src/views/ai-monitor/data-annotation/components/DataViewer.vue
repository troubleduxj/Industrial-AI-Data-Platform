<template>
  <div class="data-viewer">
    <div v-if="!data" class="no-data">
      <n-empty description="暂无数据" size="small" />
    </div>

    <!-- 分类数据查看器 -->
    <div v-else-if="projectType === 'classification'" class="classification-viewer">
      <n-card title="特征数据" size="small">
        <n-grid :cols="2" :x-gap="16" :y-gap="8">
          <n-grid-item v-for="(value, index) in data.content.values" :key="index">
            <n-statistic
              :label="data.content.features[index]"
              :value="value.toFixed(2)"
              :value-style="{ fontSize: '14px' }"
            />
          </n-grid-item>
        </n-grid>
      </n-card>

      <n-card title="数据可视化" size="small" style="margin-top: 16px">
        <div class="chart-container">
          <div class="chart-placeholder">
            <n-icon size="32" color="#ccc">
              <bar-chart-outline />
            </n-icon>
            <p>特征数据图表</p>
          </div>
        </div>
      </n-card>
    </div>

    <!-- 目标检测数据查看器 -->
    <div v-else-if="projectType === 'detection'" class="detection-viewer">
      <div class="image-container">
        <div class="image-placeholder">
          <n-icon size="48" color="#ccc">
            <image-outline />
          </n-icon>
          <p>图像数据</p>
          <n-text depth="3" style="font-size: 12px">
            {{ data.content.width }} x {{ data.content.height }}
          </n-text>
        </div>

        <!-- 检测框覆盖层 -->
        <div class="detection-overlay">
          <!-- 这里可以添加检测框的绘制逻辑 -->
        </div>
      </div>

      <div class="detection-tools">
        <n-space>
          <n-button size="small" @click="addDetectionBox">
            <template #icon>
              <n-icon><add-outline /></n-icon>
            </template>
            添加检测框
          </n-button>
          <n-button size="small" @click="clearDetections">
            <template #icon>
              <n-icon><trash-outline /></n-icon>
            </template>
            清空
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 图像分割数据查看器 -->
    <div v-else-if="projectType === 'segmentation'" class="segmentation-viewer">
      <div class="image-container">
        <div class="image-placeholder">
          <n-icon size="48" color="#ccc">
            <image-outline />
          </n-icon>
          <p>图像数据</p>
          <n-text depth="3" style="font-size: 12px">
            {{ data.content.width }} x {{ data.content.height }}
          </n-text>
        </div>

        <!-- 分割掩码覆盖层 -->
        <div class="segmentation-overlay">
          <!-- 这里可以添加分割掩码的绘制逻辑 -->
        </div>
      </div>

      <div class="segmentation-tools">
        <n-space>
          <n-button size="small" @click="startPolygonDrawing">
            <template #icon>
              <n-icon><create-outline /></n-icon>
            </template>
            绘制多边形
          </n-button>
          <n-button size="small" @click="startBrushDrawing">
            <template #icon>
              <n-icon><brush-outline /></n-icon>
            </template>
            画笔工具
          </n-button>
          <n-button size="small" @click="clearSegmentation">
            <template #icon>
              <n-icon><trash-outline /></n-icon>
            </template>
            清空
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 回归数据查看器 -->
    <div v-else-if="projectType === 'regression'" class="regression-viewer">
      <n-card title="时间序列数据" size="small">
        <div class="chart-container">
          <div class="chart-placeholder">
            <n-icon size="32" color="#ccc">
              <trending-up-outline />
            </n-icon>
            <p>时间序列图表</p>
            <n-text depth="3" style="font-size: 12px">
              {{ data.content.timeSeries.length }} 个数据点
            </n-text>
          </div>
        </div>
      </n-card>

      <n-card title="统计信息" size="small" style="margin-top: 16px">
        <n-descriptions :column="2" size="small">
          <n-descriptions-item label="最小值">
            {{ getTimeSeriesStats().min.toFixed(2) }}
          </n-descriptions-item>
          <n-descriptions-item label="最大值">
            {{ getTimeSeriesStats().max.toFixed(2) }}
          </n-descriptions-item>
          <n-descriptions-item label="平均值">
            {{ getTimeSeriesStats().mean.toFixed(2) }}
          </n-descriptions-item>
          <n-descriptions-item label="标准差">
            {{ getTimeSeriesStats().std.toFixed(2) }}
          </n-descriptions-item>
        </n-descriptions>
      </n-card>
    </div>

    <!-- 数据元信息 -->
    <n-card title="数据信息" size="small" style="margin-top: 16px">
      <n-descriptions :column="2" size="small">
        <n-descriptions-item label="数据ID">
          {{ data.id }}
        </n-descriptions-item>
        <n-descriptions-item label="数据源">
          {{ data.metadata.source }}
        </n-descriptions-item>
        <n-descriptions-item label="时间戳">
          <n-time :time="new Date(data.metadata.timestamp)" format="yyyy-MM-dd HH:mm:ss" />
        </n-descriptions-item>
        <n-descriptions-item label="质量等级">
          <n-tag :type="data.metadata.quality === 'high' ? 'success' : 'warning'" size="small">
            {{ data.metadata.quality === 'high' ? '高' : '中' }}
          </n-tag>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NIcon,
  NText,
  NSpace,
  NButton,
  NEmpty,
  NDescriptions,
  NDescriptionsItem,
  NTime,
  NTag,
  useMessage,
} from 'naive-ui'
import {
  BarChartOutline,
  ImageOutline,
  AddOutline,
  TrashOutline,
  CreateOutline,
  BrushOutline,
  TrendingUpOutline,
} from '@vicons/ionicons5'

// Props
const props = defineProps({
  data: {
    type: Object,
    default: null,
  },
  projectType: {
    type: String,
    required: true,
  },
})

// Emits
const emit = defineEmits(['data-change'])

// 消息提示
const message = useMessage()

// 计算时间序列统计信息
const getTimeSeriesStats = () => {
  if (!props.data?.content?.timeSeries) {
    return { min: 0, max: 0, mean: 0, std: 0 }
  }

  const values = props.data.content.timeSeries.map((item) => item.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
  const std = Math.sqrt(variance)

  return { min, max, mean, std }
}

// 添加检测框
const addDetectionBox = () => {
  message.info('添加检测框功能')
  // 这里可以实现实际的检测框添加逻辑
  emit('data-change', {
    content: {
      ...props.data.content,
      detectionBoxes: [
        ...(props.data.content.detectionBoxes || []),
        {
          id: Date.now(),
          x: 100,
          y: 100,
          width: 100,
          height: 100,
          label: '新检测框',
        },
      ],
    },
  })
}

// 清空检测框
const clearDetections = () => {
  message.info('清空检测框')
  emit('data-change', {
    content: {
      ...props.data.content,
      detectionBoxes: [],
    },
  })
}

// 开始多边形绘制
const startPolygonDrawing = () => {
  message.info('开始多边形绘制')
  // 这里可以实现实际的多边形绘制逻辑
}

// 开始画笔绘制
const startBrushDrawing = () => {
  message.info('开始画笔绘制')
  // 这里可以实现实际的画笔绘制逻辑
}

// 清空分割
const clearSegmentation = () => {
  message.info('清空分割')
  emit('data-change', {
    content: {
      ...props.data.content,
      regions: [],
    },
  })
}
</script>

<style scoped>
.data-viewer {
  height: 100%;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.classification-viewer {
  height: 100%;
}

.chart-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  background-color: #fafafa;
}

.chart-placeholder {
  text-align: center;
  color: #999;
}

.chart-placeholder p {
  margin: 8px 0 4px 0;
  font-size: 14px;
}

.detection-viewer,
.segmentation-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-container {
  position: relative;
  flex: 1;
  min-height: 300px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #fafafa;
  color: #999;
}

.image-placeholder p {
  margin: 8px 0 4px 0;
  font-size: 16px;
}

.detection-overlay,
.segmentation-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.detection-tools,
.segmentation-tools {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.regression-viewer {
  height: 100%;
}
</style>
