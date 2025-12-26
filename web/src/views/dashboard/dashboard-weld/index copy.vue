<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <!-- 设备状态概览 -->
      <n-card rounded-10>
        <div mb-4>
          <h2 text-18 font-semibold>设备状态</h2>
          <p text-14 op-60>当前设备总数: {{ deviceStats.total }}</p>
        </div>
        <n-spin :show="loading">
          <n-grid :cols="4" :x-gap="20">
            <n-grid-item>
              <n-card size="small" class="status-card welding">
                <div flex items-center>
                  <n-icon size="24" color="#52c41a">
                    <icon-mdi:flash />
                  </n-icon>
                  <div ml-3>
                    <div text-14 op-60>焊接设备</div>
                    <div text-24 font-bold>{{ deviceStats.welding }}</div>
                    <div text-12 op-50>
                      占比 {{ deviceStats.weldingRate.toFixed(1) }}% 正在焊接作业
                    </div>
                  </div>
                </div>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card size="small" class="status-card standby">
                <div flex items-center>
                  <n-icon size="24" color="#faad14">
                    <icon-mdi:pause-circle />
                  </n-icon>
                  <div ml-3>
                    <div text-14 op-60>待机设备</div>
                    <div text-24 font-bold>{{ deviceStats.standby }}</div>
                    <div text-12 op-50>
                      占比 {{ deviceStats.standbyRate.toFixed(1) }}% 处于待机状态
                    </div>
                  </div>
                </div>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card size="small" class="status-card alarm">
                <div flex items-center>
                  <n-icon size="24" color="#ff4d4f">
                    <icon-mdi:alert-circle />
                  </n-icon>
                  <div ml-3>
                    <div text-14 op-60>报警设备</div>
                    <div text-24 font-bold>{{ deviceStats.alarm }}</div>
                    <div text-12 op-50>占比 {{ deviceStats.alarmRate.toFixed(1) }}% 设备报警</div>
                  </div>
                </div>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card size="small" class="status-card shutdown">
                <div flex items-center>
                  <n-icon size="24" color="#8c8c8c">
                    <icon-mdi:power />
                  </n-icon>
                  <div ml-3>
                    <div text-14 op-60>关机设备</div>
                    <div text-24 font-bold>{{ deviceStats.shutdown }}</div>
                    <div text-12 op-50>
                      占比 {{ deviceStats.shutdownRate.toFixed(1) }}% 设备关机
                    </div>
                  </div>
                </div>
              </n-card>
            </n-grid-item>
          </n-grid>
        </n-spin>
      </n-card>

      <!-- 图表区域 -->
      <n-grid :cols="2" :x-gap="20" mt-4>
        <n-grid-item>
          <n-card title="实时在线率-焊接率" rounded-10>
            <template #header-extra>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="18" cursor-pointer>
                    <icon-mdi:information-outline />
                  </n-icon>
                </template>
                <div>实时在线率 = (待机+焊接+报警) / 总数</div>
                <div>实时焊接率 = 焊接 / (总数 - 关机)</div>
              </n-tooltip>
            </template>
            <div ref="onlineRateChart" style="height: 280px"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card title="设备实时状态率堆叠图" rounded-10>
            <div ref="statusStackedAreaChart" style="height: 280px"></div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="20" mt-4>
        <n-grid-item>
          <n-card title="设备实时状态分布饼图" rounded-10>
            <div ref="statusPieChart" style="height: 280px"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card title="报警信息列表" rounded-10>
            <div>
              <n-list>
                <n-list-item v-for="item in alarmList.slice(0, 2)" :key="item.id">
                  <n-card
                    size="small"
                    style="margin-bottom: 12px; background: #fff7f6; border-left: 4px solid #ff4d4f"
                  >
                    <div style="display: flex; align-items: center">
                      <n-icon size="22" color="#ff4d4f" style="margin-right: 8px">
                        <icon-mdi:alert-circle />
                      </n-icon>
                      <div style="flex: 1">
                        <div style="font-weight: bold; color: #ff4d4f; font-size: 15px">
                          {{ item.deviceName }}
                        </div>
                        <div style="color: #999; font-size: 12px; margin-bottom: 2px">
                          {{ item.time }}
                        </div>
                        <div style="color: #333; font-size: 14px">{{ item.message }}</div>
                      </div>
                    </div>
                  </n-card>
                </n-list-item>
              </n-list>
              <div style="text-align: center; color: #aaa; font-size: 13px; margin-top: 8px">
                ...更多报警信息已省略
              </div>
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
import { deviceDataApi } from '@/api/device-v2'

// 图表引用
const onlineRateChart = ref(null)
let onlineRateChartInstance = null
const onlineRateHistory = ref([])
const weldingRateHistory = ref([])

const statusStackedAreaChart = ref(null)
let statusStackedAreaChartInstance = null
const statusStackedAreaHistory = ref([])

const statusPieChart = ref(null)
let statusPieChartInstance = null

// 响应式数据
const deviceStats = ref({
  total: 0,
  standby: 0,
  welding: 0,
  alarm: 0,
  shutdown: 0,
  standbyRate: 0,
  weldingRate: 0,
  alarmRate: 0,
  shutdownRate: 0,
})

const loading = ref(false)
let intervalId = null

const alarmList = ref([
  {
    id: 1,
    deviceName: '焊机A001',
    message: '主回路过流报警',
    time: '2024-05-01 14:23:11',
  },
  {
    id: 2,
    deviceName: '焊机B002',
    message: '气体压力过低',
    time: '2024-05-01 14:25:47',
  },
  // ...更多报警信息已省略
])

// 初始化在线率图表
const initOnlineRateChart = () => {
  onlineRateChartInstance = echarts.init(onlineRateChart.value)
  const option = {
    grid: { left: '5%', right: '5%', top: '15%', bottom: '10%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        const time = params[0].axisValue
        let tooltipHtml = `${time}<br/>`
        params.forEach((item) => {
          tooltipHtml += `${item.marker} ${item.seriesName}: ${item.value}%<br/>`
        })
        return tooltipHtml
      },
    },
    legend: {
      data: ['在线率', '焊接率'],
      top: '5%',
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: onlineRateHistory.value.map((item) => item.time),
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    series: [
      {
        name: '在线率',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: onlineRateHistory.value.map((item) => item.rate),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
            { offset: 1, color: 'rgba(82, 196, 26, 0.1)' },
          ]),
        },
        lineStyle: { color: '#52c41a' },
        itemStyle: { color: '#52c41a' },
      },
      {
        name: '焊接率',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: weldingRateHistory.value.map((item) => item.rate),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
          ]),
        },
        lineStyle: { color: '#1890ff' },
        itemStyle: { color: '#1890ff' },
      },
    ],
  }
  onlineRateChartInstance.setOption(option)
  window.addEventListener('resize', () => onlineRateChartInstance?.resize())
}

// 初始化状态堆叠面积图
const initStatusStackedAreaChart = () => {
  statusStackedAreaChartInstance = echarts.init(statusStackedAreaChart.value)
  const option = {
    title: {
      text: '',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
    },
    legend: {
      data: ['关机', '待机', '报警', '焊接'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: statusStackedAreaHistory.value.map((item) => item.time),
      },
    ],
    yAxis: [
      {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}%' },
      },
    ],
    series: [
      {
        name: '关机',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: { width: 0 },
        showSymbol: false,
        color: '#8c8c8c',
        areaStyle: {
          opacity: 0.85,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(140, 140, 140, 0.75)' },
            { offset: 1, color: 'rgba(140, 140, 140, 0.2)' },
          ]),
        },
        emphasis: { focus: 'series' },
        data: statusStackedAreaHistory.value.map((item) => item.shutdownRate),
      },
      {
        name: '待机',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: { width: 0 },
        showSymbol: false,
        color: '#faad14',
        areaStyle: {
          opacity: 0.85,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(250, 173, 20, 0.75)' },
            { offset: 1, color: 'rgba(250, 173, 20, 0.2)' },
          ]),
        },
        emphasis: { focus: 'series' },
        data: statusStackedAreaHistory.value.map((item) => item.standbyRate),
      },
      {
        name: '报警',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: { width: 0 },
        showSymbol: false,
        color: '#ff4d4f',
        areaStyle: {
          opacity: 0.85,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 77, 79, 0.75)' },
            { offset: 1, color: 'rgba(255, 77, 79, 0.2)' },
          ]),
        },
        emphasis: { focus: 'series' },
        data: statusStackedAreaHistory.value.map((item) => item.alarmRate),
      },
      {
        name: '焊接',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: { width: 0 },
        showSymbol: false,
        color: '#52c41a',
        areaStyle: {
          opacity: 0.85,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(82, 196, 26, 0.75)' },
            { offset: 1, color: 'rgba(82, 196, 26, 0.2)' },
          ]),
        },
        emphasis: { focus: 'series' },
        data: statusStackedAreaHistory.value.map((item) => item.weldingRate),
      },
    ],
  }
  statusStackedAreaChartInstance.setOption(option)
  window.addEventListener('resize', () => statusStackedAreaChartInstance?.resize())
}

// 初始化饼图
const initStatusPieChart = () => {
  statusPieChartInstance = echarts.init(statusPieChart.value)
  const option = {
    title: {
      text: '',
      left: 'center',
      top: 20,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['待机', '焊接', '报警', '关机'],
    },
    series: [
      {
        name: '设备状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}: {d}%',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 18,
            fontWeight: 'bold',
          },
        },
        data: [
          { value: deviceStats.value.standby, name: '待机' },
          { value: deviceStats.value.welding, name: '焊接' },
          { value: deviceStats.value.alarm, name: '报警' },
          { value: deviceStats.value.shutdown, name: '关机' },
        ],
      },
    ],
  }
  statusPieChartInstance.setOption(option)
  window.addEventListener('resize', () => statusPieChartInstance?.resize())
}

// 获取设备实时状态统计数据
const fetchDeviceStats = async (isInitialLoad = false) => {
  // 仅在首次加载时显示加载动画
  if (isInitialLoad) {
    loading.value = true
  }
  try {
    const response = await deviceDataApi.getRealtimeDeviceStatus({ device_type: 'welding' })
    if (response.code === 200 && response.data) {
      deviceStats.value = {
        total: response.data.total_devices || 0,
        standby: response.data.standby_devices || 0,
        welding: response.data.welding_devices || 0,
        alarm: response.data.alarm_devices || 0,
        shutdown: response.data.shutdown_devices || 0,
        standbyRate: response.data.standby_rate || 0,
        weldingRate: response.data.welding_rate || 0,
        alarmRate: response.data.alarm_rate || 0,
        shutdownRate: response.data.shutdown_rate || 0,
      }

      // 计算并更新实时在线率
      const { standby_devices, welding_devices, alarm_devices, shutdown_devices, total_devices } =
        response.data
      if (total_devices > 0) {
        const online_devices = standby_devices + welding_devices + alarm_devices
        const currentOnlineRate = parseFloat(((online_devices / total_devices) * 100).toFixed(1))

        // 计算实时焊接率
        const working_total = total_devices - shutdown_devices
        const currentWeldingRate =
          working_total > 0 ? parseFloat(((welding_devices / working_total) * 100).toFixed(1)) : 0

        const now = new Date()
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(
          now.getMinutes()
        ).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`

        // 更新在线率历史
        onlineRateHistory.value.push({ time, rate: currentOnlineRate })
        if (onlineRateHistory.value.length > 20) {
          onlineRateHistory.value.shift()
        }

        // 更新焊接率历史
        weldingRateHistory.value.push({ time, rate: currentWeldingRate })
        if (weldingRateHistory.value.length > 20) {
          weldingRateHistory.value.shift()
        }

        // 更新状态分布历史
        statusStackedAreaHistory.value.push({
          time,
          standbyRate: deviceStats.value.standbyRate,
          weldingRate: deviceStats.value.weldingRate,
          alarmRate: deviceStats.value.alarmRate,
          shutdownRate: deviceStats.value.shutdownRate,
        })
        if (statusStackedAreaHistory.value.length > 20) {
          statusStackedAreaHistory.value.shift()
        }

        // 更新图表
        if (onlineRateChartInstance) {
          onlineRateChartInstance.setOption({
            xAxis: { data: onlineRateHistory.value.map((item) => item.time) },
            series: [
              { name: '在线率', data: onlineRateHistory.value.map((item) => item.rate) },
              { name: '焊接率', data: weldingRateHistory.value.map((item) => item.rate) },
            ],
          })
        }
        if (statusStackedAreaChartInstance) {
          statusStackedAreaChartInstance.setOption({
            xAxis: { data: statusStackedAreaHistory.value.map((item) => item.time) },
            series: [
              {
                name: '关机',
                data: statusStackedAreaHistory.value.map((item) => item.shutdownRate),
              },
              {
                name: '待机',
                data: statusStackedAreaHistory.value.map((item) => item.standbyRate),
              },
              { name: '报警', data: statusStackedAreaHistory.value.map((item) => item.alarmRate) },
              {
                name: '焊接',
                data: statusStackedAreaHistory.value.map((item) => item.weldingRate),
              },
            ],
          })
        }
        if (statusPieChartInstance) {
          statusPieChartInstance.setOption({
            series: [
              {
                data: [
                  { value: deviceStats.value.standby, name: '待机' },
                  { value: deviceStats.value.welding, name: '焊接' },
                  { value: deviceStats.value.alarm, name: '报警' },
                  { value: deviceStats.value.shutdown, name: '关机' },
                ],
              },
            ],
          })
        }
      }
    }
  } catch (error) {
    console.error('获取设备实时状态失败:', error)
    // 首次加载失败时显示错误提示
    if (isInitialLoad) {
      window.$message?.error('获取设备实时状态失败')
    }
  } finally {
    if (isInitialLoad) {
      loading.value = false
    }
  }
}

// 组件挂载后
onMounted(async () => {
  // 立即执行一次获取数据，并标记为首次加载
  await fetchDeviceStats(true)

  // DOM渲染完成后初始化图表
  nextTick(() => {
    initOnlineRateChart()
    initStatusStackedAreaChart()
    initStatusPieChart()
  })

  // 设置定时器，每15秒刷新一次数据（非首次加载）
  intervalId = setInterval(() => fetchDeviceStats(false), 15000)
})

// 组件销毁前
onBeforeUnmount(() => {
  // 清理定时器
  if (intervalId) {
    clearInterval(intervalId)
  }
  // 销毁图表实例
  if (onlineRateChartInstance) {
    onlineRateChartInstance.dispose()
    onlineRateChartInstance = null
  }
  if (statusStackedAreaChartInstance) {
    statusStackedAreaChartInstance.dispose()
    statusStackedAreaChartInstance = null
  }
  if (statusPieChartInstance) {
    statusPieChartInstance.dispose()
    statusPieChartInstance = null
  }
})
</script>

<style scoped>
.status-card {
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
}

.status-card.standby {
  border-left-color: #faad14;
}

.status-card.welding {
  border-left-color: #52c41a;
}

.status-card.alarm {
  border-left-color: #ff4d4f;
}

.status-card.shutdown {
  border-left-color: #8c8c8c;
}

.status-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
</style>
