<template>
  <div class="ai-predictions-page">
    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <!-- 预测服务状态 -->
      <n-gi :span="24">
        <n-card title="预测服务状态" :bordered="false" size="small">
          <n-grid :cols="4" :x-gap="16">
            <n-gi>
              <n-statistic label="活跃模型数" :value="stats.activeModels">
                <template #prefix><n-icon color="#18a058"><CheckmarkCircleOutline /></n-icon></template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="今日预测次数" :value="stats.todayPredictions" />
            </n-gi>
            <n-gi>
              <n-statistic label="平均响应时间" :value="stats.avgResponseTime">
                <template #suffix>ms</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="成功率" :value="stats.successRate">
                <template #suffix>%</template>
              </n-statistic>
            </n-gi>
          </n-grid>
        </n-card>
      </n-gi>

      <!-- 在线预测 -->
      <n-gi :span="12">
        <n-card title="在线预测" :bordered="false">
          <n-form ref="formRef" :model="predictionForm" label-placement="left" label-width="100px">
            <n-form-item label="选择模型">
              <n-select v-model:value="predictionForm.model_id" :options="modelOptions" placeholder="请选择模型" />
            </n-form-item>
            <n-form-item label="选择资产">
              <n-select v-model:value="predictionForm.asset_id" :options="assetOptions" placeholder="请选择资产" />
            </n-form-item>
            <n-form-item label="输入特征">
              <n-dynamic-input v-model:value="predictionForm.features" :on-create="() => ({ name: '', value: '' })">
                <template #default="{ value }">
                  <n-space>
                    <n-input v-model:value="value.name" placeholder="特征名" style="width: 150px" />
                    <n-input-number v-model:value="value.value" placeholder="特征值" style="width: 150px" />
                  </n-space>
                </template>
              </n-dynamic-input>
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="handlePredict" :loading="predicting">
                执行预测
              </n-button>
            </n-form-item>
          </n-form>

          <n-divider />

          <n-card v-if="predictionResult" title="预测结果" size="small" embedded>
            <n-descriptions :column="2">
              <n-descriptions-item label="预测值">
                <n-tag type="success" size="large">{{ predictionResult.prediction }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="置信度">
                <n-progress type="line" :percentage="predictionResult.confidence * 100" />
              </n-descriptions-item>
              <n-descriptions-item label="模型版本">{{ predictionResult.model_version }}</n-descriptions-item>
              <n-descriptions-item label="响应时间">{{ predictionResult.response_time }}ms</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-card>
      </n-gi>

      <!-- 预测历史 -->
      <n-gi :span="12">
        <n-card title="预测历史" :bordered="false">
          <template #header-extra>
            <n-date-picker v-model:value="dateRange" type="daterange" clearable />
          </template>
          <n-data-table
            :columns="historyColumns"
            :data="predictionHistory"
            :loading="historyLoading"
            :max-height="400"
            size="small"
          />
        </n-card>
      </n-gi>

      <!-- 预测趋势图 -->
      <n-gi :span="24">
        <n-card title="预测趋势" :bordered="false">
          <div ref="chartRef" style="height: 300px;"></div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, reactive, h, onMounted, computed, watch } from 'vue'
import { NTag, useMessage } from 'naive-ui'
import { CheckmarkCircleOutline } from '@vicons/ionicons5'
import api from '@/api'
import { platformApi } from '@/api/v3/platform'
import * as echarts from 'echarts'

const message = useMessage()

const stats = reactive({
  activeModels: 0,
  todayPredictions: 0,
  avgResponseTime: 0,
  successRate: 0
})

const models = ref([])
const assets = ref([])
const predicting = ref(false)
const predictionResult = ref(null)
const predictionHistory = ref([])
const historyLoading = ref(false)
const dateRange = ref(null)
const chartRef = ref(null)
let chartInstance = null

const predictionForm = reactive({
  model_id: null,
  asset_id: null,
  features: []
})

const modelOptions = computed(() => 
  models.value.map(m => ({ label: m.name, value: m.id }))
)

const assetOptions = computed(() => 
  assets.value.map(a => ({ label: a.name, value: a.id }))
)

const historyColumns = [
  { title: '时间', key: 'created_at', width: 150 },
  { title: '模型', key: 'model_name', width: 120 },
  { title: '资产', key: 'asset_name', width: 120 },
  { 
    title: '预测值', 
    key: 'prediction',
    render: row => h(NTag, { type: 'info', size: 'small' }, () => row.prediction)
  },
  { title: '置信度', key: 'confidence', render: row => `${(row.confidence * 100).toFixed(1)}%` }
]

const loadStats = async () => {
  try {
    const res = await api.get('/api/v3/ai/predictions/stats')
    Object.assign(stats, res.data?.data || {})
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const loadModels = async () => {
  try {
    const res = await api.get('/api/v3/ai/models', { params: { status: 'active' } })
    models.value = res.data?.data || []
  } catch (error) {
    console.error('加载模型失败:', error)
  }
}

const loadAssets = async () => {
  try {
    const res = await platformApi.getAssets({ page_size: 100 })
    assets.value = res.data?.items || []
  } catch (error) {
    console.error('加载资产失败:', error)
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const params = {}
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await api.get('/api/v3/ai/predictions/history', { params })
    predictionHistory.value = res.data?.data || []
  } catch (error) {
    console.error('加载历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

const handlePredict = async () => {
  if (!predictionForm.model_id || !predictionForm.asset_id) {
    message.warning('请选择模型和资产')
    return
  }
  predicting.value = true
  try {
    const features = {}
    predictionForm.features.forEach(f => {
      if (f.name) features[f.name] = f.value
    })
    const res = await api.post('/api/v3/ai/predictions', {
      model_id: predictionForm.model_id,
      asset_id: predictionForm.asset_id,
      features
    })
    predictionResult.value = res.data?.data
    message.success('预测完成')
    loadHistory()
    loadStats()
  } catch (error) {
    message.error('预测失败: ' + (error.message || '未知错误'))
  } finally {
    predicting.value = false
  }
}

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['预测次数', '成功率'] },
    xAxis: { type: 'category', data: [] },
    yAxis: [
      { type: 'value', name: '预测次数' },
      { type: 'value', name: '成功率', max: 100, axisLabel: { formatter: '{value}%' } }
    ],
    series: [
      { name: '预测次数', type: 'bar', data: [] },
      { name: '成功率', type: 'line', yAxisIndex: 1, data: [] }
    ]
  })
}

const loadChartData = async () => {
  try {
    const res = await api.get('/api/v3/ai/predictions/trend')
    const data = res.data?.data || []
    if (chartInstance) {
      chartInstance.setOption({
        xAxis: { data: data.map(d => d.date) },
        series: [
          { data: data.map(d => d.count) },
          { data: data.map(d => d.success_rate) }
        ]
      })
    }
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  }
}

watch(dateRange, () => {
  loadHistory()
})

onMounted(() => {
  loadStats()
  loadModels()
  loadAssets()
  loadHistory()
  initChart()
  loadChartData()
})
</script>

<style scoped>
.ai-predictions-page {
  padding: 16px;
}
</style>
