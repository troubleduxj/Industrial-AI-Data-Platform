<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <!-- 设备状态概览 -->
      <n-card rounded-10>
        <div mb-4>
          <h2 text-18 font-semibold>设备状态</h2>
          <p text-14 op-60>当前设备总数: 7181</p>
        </div>
        <n-grid :cols="4" :x-gap="20">
          <n-grid-item>
            <n-card size="small" class="online status-card">
              <div flex items-center>
                <n-icon size="24" color="#52c41a">
                  <icon-mdi:check-circle />
                </n-icon>
                <div ml-3>
                  <div text-14 op-60>在线设备</div>
                  <div text-24 font-bold>20</div>
                  <div text-12 op-50>占比 0.3% 设备正常运行</div>
                </div>
              </div>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="status-card warning">
              <div flex items-center>
                <n-icon size="24" color="#faad14">
                  <icon-mdi:alert-circle />
                </n-icon>
                <div ml-3>
                  <div text-14 op-60>待机设备</div>
                  <div text-24 font-bold>233</div>
                  <div text-12 op-50>占比 3.2% 处于待机状态</div>
                </div>
              </div>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="status-card error">
              <div flex items-center>
                <n-icon size="24" color="#ff4d4f">
                  <icon-mdi:close-circle />
                </n-icon>
                <div ml-3>
                  <div text-14 op-60>故障设备</div>
                  <div text-24 font-bold>2</div>
                  <div text-12 op-50>占比 0.0% 设备故障离线</div>
                </div>
              </div>
            </n-card>
          </n-grid-item>
          <n-grid-item>
            <n-card size="small" class="status-card offline">
              <div flex items-center>
                <n-icon size="24" color="#8c8c8c">
                  <icon-mdi:minus-circle />
                </n-icon>
                <div ml-3>
                  <div text-14 op-60>离线设备</div>
                  <div text-24 font-bold>6926</div>
                  <div text-12 op-50>占比 96.4% 设备离线</div>
                </div>
              </div>
            </n-card>
          </n-grid-item>
        </n-grid>
      </n-card>

      <!-- 图表区域 -->
      <n-grid :cols="2" :x-gap="20" mt-4>
        <!-- 设备在线率 -->
        <n-grid-item>
          <n-card title="设备在线率" rounded-10>
            <template #header-extra>
              <n-space>
                <n-button size="small" type="primary">月</n-button>
                <n-button size="small" quaternary>年</n-button>
              </n-space>
            </template>
            <div ref="onlineRateChart" style="height: 300px"></div>
          </n-card>
        </n-grid-item>

        <!-- 设备状态分布 -->
        <n-grid-item>
          <n-card title="设备状态分布" rounded-10>
            <div ref="statusDistributionChart" style="height: 300px"></div>
            <div mt-4 flex justify-center>
              <n-space>
                <div flex items-center>
                  <div mr-2 h-3 w-3 rounded-full bg-green-500></div>
                  <span text-12>在线</span>
                </div>
                <div flex items-center>
                  <div mr-2 h-3 w-3 rounded-full bg-yellow-500></div>
                  <span text-12>待机</span>
                </div>
                <div flex items-center>
                  <div mr-2 h-3 w-3 rounded-full bg-gray-500></div>
                  <span text-12>离线</span>
                </div>
                <div flex items-center>
                  <div mr-2 h-3 w-3 rounded-full bg-red-500></div>
                  <span text-12>故障</span>
                </div>
              </n-space>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

// 图表引用
const onlineRateChart = ref(null)
const statusDistributionChart = ref(null)
let onlineRateChartInstance = null
let statusDistributionChartInstance = null

// 初始化在线率图表
const initOnlineRateChart = () => {
  onlineRateChartInstance = echarts.init(onlineRateChart.value)
  const chart = onlineRateChartInstance
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: ['6月6日', '6月7日', '6月8日', '6月9日', '6月10日', '6月11日', '6月12日'],
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        formatter: '{value}%',
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
        },
      },
    },
    series: [
      {
        name: '在线率',
        type: 'line',
        data: [98, 99, 98.5, 99.2, 98.8, 99.1, 98.9],
        smooth: true,
        lineStyle: {
          color: '#ff69b4',
          width: 3,
        },
        itemStyle: {
          color: '#ff69b4',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(255, 105, 180, 0.3)',
              },
              {
                offset: 1,
                color: 'rgba(255, 105, 180, 0.1)',
              },
            ],
          },
        },
      },
    ],
  }
  chart.setOption(option)

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 初始化状态分布饼图
const initStatusDistributionChart = () => {
  statusDistributionChartInstance = echarts.init(statusDistributionChart.value)
  const chart = statusDistributionChartInstance
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
    },
    legend: {
      show: false,
    },
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: [
          { value: 20, name: '在线', itemStyle: { color: '#52c41a' } },
          { value: 233, name: '待机', itemStyle: { color: '#faad14' } },
          { value: 6926, name: '离线', itemStyle: { color: '#8c8c8c' } },
          { value: 2, name: '故障', itemStyle: { color: '#ff4d4f' } },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        label: {
          show: false,
        },
        labelLine: {
          show: false,
        },
      },
    ],
  }
  chart.setOption(option)

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 组件挂载后初始化图表
onMounted(() => {
  nextTick(() => {
    initOnlineRateChart()
    initStatusDistributionChart()
  })
})

// 组件销毁前清理
onBeforeUnmount(() => {
  // 销毁图表实例
  if (onlineRateChartInstance) {
    onlineRateChartInstance.dispose()
    onlineRateChartInstance = null
  }
  if (statusDistributionChartInstance) {
    statusDistributionChartInstance.dispose()
    statusDistributionChartInstance = null
  }
})
</script>

<style scoped>
.status-card {
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
}

.status-card.online {
  border-left-color: #52c41a;
}

.status-card.warning {
  border-left-color: #faad14;
}

.status-card.error {
  border-left-color: #ff4d4f;
}

.status-card.offline {
  border-left-color: #8c8c8c;
}

.status-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
</style>
