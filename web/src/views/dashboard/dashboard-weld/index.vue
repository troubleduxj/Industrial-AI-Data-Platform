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
              <n-card size="small" class="standby status-card">
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
          <n-card title="在线率-焊接率" rounded-10>
            <template #header-extra>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="18" cursor-pointer>
                    <icon-mdi:information-outline />
                  </n-icon>
                </template>
                <div>实时在线率 = (待机+焊接+报警) / 总数</div>
                <div>实时焊接率 = 焊接数 / 开机数</div>
              </n-tooltip>
            </template>
            <div ref="onlineRateChart" style="height: 280px"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card title="7日消耗统计" rounded-10>
            <template #header-extra>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="18" cursor-pointer>
                    <icon-mdi:information-outline />
                  </n-icon>
                </template>
                <div>展示近7日焊丝、气体、电能消耗趋势</div>
              </n-tooltip>
            </template>
            <div ref="consumptionChart" style="height: 280px"></div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="20" mt-4>
        <n-grid-item>
          <n-card title="报警类型分布" rounded-10>
            <template #header-extra>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-icon size="18" cursor-pointer>
                    <icon-mdi:information-outline />
                  </n-icon>
                </template>
                <div>展示最近7日各类型报警分布情况</div>
              </n-tooltip>
            </template>
            <div ref="alarmCategoryChart" style="height: 320px"></div>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card title="报警信息Top" rounded-10>
            <template #header-extra>
              <PermissionButton
                v-if="alarmTopList.length > 3"
                permission="GET /api/v2/alarms"
                text
                type="primary"
                @click="showFullAlarmList"
              >
                更多报警
              </PermissionButton>
            </template>
            <div>
              <n-list>
                <n-list-item v-for="item in alarmList.slice(0, 3)" :key="item.id">
                  <n-card
                    size="small"
                    style="
                      margin-bottom: 8px;
                      background: #fff7f6;
                      border-left: 4px solid #ff4d4f;
                      cursor: pointer;
                    "
                    @click="handleAlarmItemClick(item)"
                  >
                    <div style="display: flex; align-items: center">
                      <n-icon size="20" color="#ff4d4f" style="margin-right: 8px">
                        <icon-mdi:alert-circle />
                      </n-icon>
                      <div style="flex: 1">
                        <div style="font-weight: bold; color: #ff4d4f; font-size: 14px">
                          {{ item.deviceName }}
                        </div>
                        <div style="color: #999; font-size: 11px; margin-bottom: 2px">
                          设备编码: {{ item.deviceCode }}
                        </div>
                        <div style="color: #333; font-size: 13px">{{ item.message }}</div>
                      </div>
                    </div>
                  </n-card>
                </n-list-item>
              </n-list>
              <div
                v-if="alarmList.length === 0"
                style="text-align: center; color: #aaa; font-size: 13px; margin-top: 8px"
              >
                <n-empty description="暂无报警数据" />
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>

    <!-- 报警Top列表弹窗 -->
    <n-modal
      v-model:show="showAlarmModal"
      preset="card"
      title="最近7天报警时长排行榜"
      style="width: 600px"
    >
      <div class="alarm-top-list">
        <div
          v-for="(alarm, index) in alarmTopList"
          :key="alarm.rank"
          class="alarm-top-item"
          @click="handleAlarmItemClick(alarm)"
        >
          <div class="alarm-top-rank">
            <span
              class="rank-badge"
              :class="{
                'rank-first': index === 0,
                'rank-second': index === 1,
                'rank-third': index === 2,
              }"
            >
              {{ index + 1 }}
            </span>
          </div>
          <div class="alarm-top-content">
            <div class="device-info">
              <div class="device-name">{{ alarm.device_name }}</div>
              <div class="device-code">设备编码: {{ alarm.prod_code }}</div>
            </div>
            <div class="alarm-duration">
              <span class="duration-text">{{ formatAlarmTime(alarm.record_time) }}</span>
            </div>
          </div>
        </div>
        <div v-if="alarmTopList.length === 0" class="no-data">
          <n-empty description="暂无报警数据" />
        </div>
      </div>
    </n-modal>
  </AppPage>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, type Ref } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import PermissionButton from '@/components/common/PermissionButton.vue'
import { deviceDataApi } from '@/api/device-v2'
import { useRouter } from 'vue-router'

// ==================== 类型定义 ====================

interface DeviceStats {
  total: number
  standby: number
  welding: number
  alarm: number
  shutdown: number
  standbyRate: number
  weldingRate: number
  alarmRate: number
  shutdownRate: number
}

interface OnlineRateHistoryItem {
  time: string
  rate: number
}

interface WeldingRateHistoryItem {
  time: string
  rate: number
}

interface ConsumptionHistoryItem {
  date: string
  current: number
  voltage: number
  power: number
}

interface AlarmItem {
  id: string | number
  device_code: string
  alarm_type: string
  alarm_message: string
  alarm_time: string
  [key: string]: any
}

// 图表引用
const onlineRateChart = ref<HTMLElement | null>(null)
let onlineRateChartInstance: ECharts | null = null
const onlineRateHistory = ref<OnlineRateHistoryItem[]>([])
const weldingRateHistory = ref<WeldingRateHistoryItem[]>([])

const consumptionChart = ref<HTMLElement | null>(null)
let consumptionChartInstance: ECharts | null = null
const consumptionHistory = ref<ConsumptionHistoryItem[]>([])

const alarmCategoryChart = ref<HTMLElement | null>(null)
let alarmCategoryChartInstance: ECharts | null = null

// 响应式数据
const deviceStats = ref<DeviceStats>({
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

const loading = ref<boolean>(false)
let intervalId: ReturnType<typeof setInterval> | null = null

const alarmList = ref<AlarmItem[]>([])
const showAlarmModal = ref<boolean>(false)
const alarmTopList = ref<AlarmItem[]>([])

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

// 初始化消耗统计图表
const initConsumptionChart = () => {
  consumptionChartInstance = echarts.init(consumptionChart.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985',
        },
      },
      formatter: function (params) {
        let tooltipHtml = `${params[0].axisValue}<br/>`
        params.forEach((item) => {
          const unit =
            item.seriesName === '焊丝消耗' ? 'kg' : item.seriesName === '气体消耗' ? 'm³' : 'kWh'
          tooltipHtml += `${item.marker} ${item.seriesName}: ${item.value} ${unit}<br/>`
        })
        return tooltipHtml
      },
    },
    legend: {
      data: ['焊丝消耗', '气体消耗', '电能消耗'],
      top: '5%',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: consumptionHistory.value.map((item) => item.date),
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '焊丝/气体',
        position: 'left',
        axisLabel: {
          formatter: '{value}',
        },
        splitLine: { lineStyle: { type: 'dashed' } },
      },
      {
        type: 'value',
        name: '电能(kWh)',
        position: 'right',
        axisLabel: {
          formatter: '{value} kWh',
        },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '焊丝消耗',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 0,
        data: consumptionHistory.value.map((item) => item.wireConsumption),
        lineStyle: { color: '#1890ff', width: 3 },
        itemStyle: { color: '#1890ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
          ]),
        },
      },
      {
        name: '气体消耗',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 0,
        data: consumptionHistory.value.map((item) => item.gasConsumption),
        lineStyle: { color: '#52c41a', width: 3 },
        itemStyle: { color: '#52c41a' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
            { offset: 1, color: 'rgba(82, 196, 26, 0.1)' },
          ]),
        },
      },
      {
        name: '电能消耗',
        type: 'bar',
        yAxisIndex: 1,
        data: consumptionHistory.value.map((item) => item.powerConsumption),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#faad14' },
            { offset: 1, color: '#ffd666' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '30%',
      },
    ],
  }
  consumptionChartInstance.setOption(option)
  window.addEventListener('resize', () => consumptionChartInstance?.resize())
}

// 初始化饼图
const initAlarmCategoryChart = () => {
  alarmCategoryChartInstance = echarts.init(alarmCategoryChart.value)
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
      formatter: function (params) {
        return `${params.name}<br/>记录数: ${params.value}<br/>占比: ${params.percent}%`
      },
    },
    // 图例放在底部，避免遮挡
    legend: {
      orient: 'horizontal',
      bottom: '0%',
      left: 'center',
      type: 'scroll',
      pageIconColor: '#2f4554',
      pageIconInactiveColor: '#aaa',
      pageIconSize: 12,
      pageTextStyle: {
        color: '#666',
      },
      itemWidth: 12,
      itemHeight: 12,
      textStyle: {
        fontSize: 12,
      },
    },
    // 调整饼图位置和大小，为图例和标签留出空间
    grid: {
      top: '10%',
      bottom: '25%',
      left: '5%',
      right: '5%',
      containLabel: true,
    },
    series: [
      {
        name: '报警类型',
        type: 'pie',
        radius: ['35%', '60%'], // 减小半径，留出更多空间
        center: ['50%', '45%'], // 向上移动，为底部图例留出空间
        avoidLabelOverlap: true, // 启用标签防重叠
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}: {d}%',
          fontSize: 12,
          // 添加引导线配置
          alignTo: 'edge',
          edgeDistance: '10%',
        },
        labelLine: {
          show: true,
          length: 10, // 第一段引导线长度
          length2: 15, // 第二段引导线长度
          smooth: true,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        data: [], // 初始为空，将通过API获取数据
      },
    ],
  }
  alarmCategoryChartInstance.setOption(option)
  window.addEventListener('resize', () => alarmCategoryChartInstance?.resize())
}

// 获取7日消耗统计数据
const fetchConsumptionData = async () => {
  try {
    // 生成7天的日期数组
    const dates = []
    const consumptionData = []

    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      const dateStr = date.toISOString().split('T')[0]
      dates.push(dateStr)

      try {
        // 为每一天调用API获取数据
        const response = await deviceDataApi.getWeldingDailyReportSummary({
          report_date: dateStr,
          device_type: 'welding',
        })

        if (response.success && response.data) {
          consumptionData.push({
            date: dateStr,
            wireConsumption: response.data.total_wire || 0,
            gasConsumption: response.data.total_gas || 0,
            powerConsumption: response.data.total_energy || 0,
          })
        } else {
          // 如果某天没有数据，填充0
          consumptionData.push({
            date: dateStr,
            wireConsumption: 0,
            gasConsumption: 0,
            powerConsumption: 0,
          })
        }
      } catch (dayError) {
        console.warn(`获取${dateStr}数据失败:`, dayError)
        // 如果某天数据获取失败，填充0
        consumptionData.push({
          date: dateStr,
          wireConsumption: 0,
          gasConsumption: 0,
          powerConsumption: 0,
        })
      }
    }

    // 更新消耗历史数据
    consumptionHistory.value = consumptionData.map((item) => ({
      date: item.date.substring(5), // 只显示月-日
      wireConsumption: item.wireConsumption,
      gasConsumption: item.gasConsumption,
      powerConsumption: item.powerConsumption,
    }))

    // 更新图表
    if (consumptionChartInstance) {
      consumptionChartInstance.setOption({
        xAxis: {
          data: consumptionHistory.value.map((item) => item.date),
        },
        series: [
          {
            name: '焊丝消耗',
            data: consumptionHistory.value.map((item) => item.wireConsumption),
          },
          {
            name: '气体消耗',
            data: consumptionHistory.value.map((item) => item.gasConsumption),
          },
          {
            name: '电能消耗',
            data: consumptionHistory.value.map((item) => item.powerConsumption),
          },
        ],
      })
    }
  } catch (error) {
    console.error('获取消耗统计数据失败:', error)
    // 如果API失败，使用模拟数据
    const dates = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      dates.push(date.toISOString().split('T')[0].substring(5))
    }

    consumptionHistory.value = dates.map((date, index) => ({
      date,
      wireConsumption: Math.round(Math.random() * 50 + 20), // 20-70kg
      gasConsumption: Math.round(Math.random() * 30 + 10), // 10-40m³
      powerConsumption: Math.round(Math.random() * 200 + 100), // 100-300kWh
    }))

    if (consumptionChartInstance) {
      consumptionChartInstance.setOption({
        xAxis: {
          data: consumptionHistory.value.map((item) => item.date),
        },
        series: [
          {
            name: '焊丝消耗',
            data: consumptionHistory.value.map((item) => item.wireConsumption),
          },
          {
            name: '气体消耗',
            data: consumptionHistory.value.map((item) => item.gasConsumption),
          },
          {
            name: '电能消耗',
            data: consumptionHistory.value.map((item) => item.powerConsumption),
          },
        ],
      })
    }
  }
}

// 获取报警类型分布数据
const fetchAlarmCategoryData = async () => {
  try {
    // 计算最近7天的日期范围
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 6)

    const startTime = startDate.toISOString().split('T')[0]
    const endTime = endDate.toISOString().split('T')[0]

    console.log('调用报警类型分布API，参数:', { start_time: startTime, end_time: endTime })
    const response = await deviceDataApi.getAlarmCategorySummary({
      start_time: startTime,
      end_time: endTime,
    })
    console.log('报警类型分布API响应:', response)

    if (response.success && response.data && response.data.alarm_categories) {
      const alarmData = response.data.alarm_categories.map((item) => ({
        name: item.alarm_message || '未知报警',
        value: item.record_count || 0,
      }))

      // 更新报警类型分布图表
      if (alarmCategoryChartInstance) {
        alarmCategoryChartInstance.setOption({
          legend: {
            data: alarmData.map((item) => item.name),
          },
          series: [
            {
              data: alarmData,
            },
          ],
        })
      }
    } else {
      console.warn('报警类型分布API返回数据格式异常:', response)
      // 使用空数据
      if (alarmCategoryChartInstance) {
        alarmCategoryChartInstance.setOption({
          legend: {
            data: [],
          },
          series: [
            {
              data: [],
            },
          ],
        })
      }
    }
  } catch (error) {
    console.error('获取报警类型分布数据失败:', error)
    // 使用空数据
    if (alarmCategoryChartInstance) {
      alarmCategoryChartInstance.setOption({
        legend: {
          data: [],
        },
        series: [
          {
            data: [],
          },
        ],
      })
    }
  }
}

// 获取报警记录Top数据
const fetchAlarmRecordTopData = async () => {
  try {
    // 计算最近7天的日期范围
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 6)

    const startTime = startDate.toISOString().split('T')[0]
    const endTime = endDate.toISOString().split('T')[0]

    console.log('调用报警记录Top API，参数:', { start_time: startTime, end_time: endTime, top: 10 })
    const response = await deviceDataApi.getAlarmRecordTop({
      start_time: startTime,
      end_time: endTime,
      top: 10,
    })
    console.log('报警记录Top API响应:', response)

    if (response.success && response.data && response.data.alarm_records) {
      // 统一处理alarmTopList，确保有deviceCode字段
      alarmTopList.value = response.data.alarm_records.map((item) => ({
        ...item,
        deviceCode: item.prod_code || item.device_code || item.deviceCode, // 兼容多种字段名
      }))
      
      // 只显示前3条作为列表展示
      alarmList.value = response.data.alarm_records.slice(0, 3).map((item) => ({
        id: item.rank,
        rank: item.rank,
        deviceName: item.device_name,
        deviceCode: item.prod_code || item.device_code || item.deviceCode,
        message: `报警时长: ${formatAlarmTime(item.record_time)}`,
        time: `排名: #${item.rank}`,
      }))
      
      console.log('处理后的alarmTopList:', alarmTopList.value)
      console.log('处理后的alarmList:', alarmList.value)
    } else {
      console.warn('报警记录Top API返回数据格式异常:', response)
      alarmList.value = []
      alarmTopList.value = []
    }
  } catch (error) {
    console.error('获取报警记录Top数据失败:', error)
    alarmList.value = []
    alarmTopList.value = []
  }
}

// 格式化报警时长
const formatAlarmTime = (seconds) => {
  if (!seconds || seconds === 0) return '0秒'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60

  if (hours > 0) {
    return `${hours}小时${minutes}分钟${remainingSeconds}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟${remainingSeconds}秒`
  } else {
    return `${remainingSeconds}秒`
  }
}

// 显示完整报警Top列表
const showFullAlarmList = () => {
  showAlarmModal.value = true
}

// 路由实例
const router = useRouter()

// 处理报警项点击事件
const handleAlarmItemClick = (alarm) => {
  // 打印完整的alarm对象以便调试
  console.log('点击的报警项完整数据:', alarm)
  
  // 计算最近7天的时间范围
  const now = new Date()
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

  // 跳转到报警信息页面，并传递查询参数
  // 兼容多种可能的设备编码字段名
  const deviceCode = alarm.deviceCode || alarm.prod_code || alarm.device_code || alarm.deviceId
  
  console.log('提取的设备编码:', deviceCode)
  
  if (!deviceCode) {
    console.error('无法获取设备编码，alarm对象:', alarm)
    window.$message?.error('无法获取设备编码')
    return
  }

  const queryParams = {
    device_code: deviceCode,
    start_time: sevenDaysAgo.toISOString().replace('T', ' ').slice(0, 19),
    end_time: now.toISOString().replace('T', ' ').slice(0, 19),
  }
  
  console.log('跳转到报警信息页面，参数:', queryParams)

  router.push({
    path: '/alarm/alarm-info',
    query: queryParams,
  })
}

// 获取在线率和焊接率统计数据
const fetchOnlineWeldingRateData = async () => {
  try {
    // 计算最近7天的日期范围
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(endDate.getDate() - 6)

    const startTime = startDate.toISOString().split('T')[0]
    const endTime = endDate.toISOString().split('T')[0]

    // 生成7天的日期数组
    const dates = []
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate)
      date.setDate(startDate.getDate() + i)
      const dateStr = date.toISOString().split('T')[0]
      dates.push(dateStr.substring(5)) // 只显示月-日
    }

    try {
      console.log('调用在线率-焊接率API，参数:', { start_time: startTime, end_time: endTime })
      // 一次性调用API获取7天的数据
      const response = await deviceDataApi.getOnlineWeldingRateStatistics({
        start_time: startTime,
        end_time: endTime,
      })
      console.log('在线率-焊接率API响应:', response)

      if (response.success && response.data) {
        // 使用返回的每日数据
        const dailyData = response.data.daily_data || []

        let onlineRates = []
        let weldingRates = []

        if (dailyData.length > 0) {
          // 使用实际的每日数据
          onlineRates = dailyData.map((day) => day.online_rate || 0)
          weldingRates = dailyData.map((day) => day.welding_rate || 0)
        } else {
          // 如果没有每日数据，使用平均值
          const onlineRate = response.data.online_rate || 0
          const weldingRate = response.data.welding_rate || 0
          onlineRates = new Array(7).fill(onlineRate)
          weldingRates = new Array(7).fill(weldingRate)
        }

        // 更新图表数据
        onlineRateHistory.value = dates.map((date, index) => ({
          time: date,
          rate: onlineRates[index] || 0,
        }))

        weldingRateHistory.value = dates.map((date, index) => ({
          time: date,
          rate: weldingRates[index] || 0,
        }))

        // 更新在线率图表
        if (onlineRateChartInstance) {
          onlineRateChartInstance.setOption({
            xAxis: { data: dates },
            series: [
              { name: '在线率', data: onlineRates },
              { name: '焊接率', data: weldingRates },
            ],
          })
        }
      } else {
        console.warn('获取在线率和焊接率数据失败: API返回数据格式错误')
        // 使用默认数据
        const onlineRates = new Array(7).fill(0)
        const weldingRates = new Array(7).fill(0)

        onlineRateHistory.value = dates.map((date, index) => ({
          time: date,
          rate: onlineRates[index],
        }))

        weldingRateHistory.value = dates.map((date, index) => ({
          time: date,
          rate: weldingRates[index],
        }))

        if (onlineRateChartInstance) {
          onlineRateChartInstance.setOption({
            xAxis: { data: dates },
            series: [
              { name: '在线率', data: onlineRates },
              { name: '焊接率', data: weldingRates },
            ],
          })
        }
      }
    } catch (apiError) {
      console.error('调用在线率和焊接率API失败:', apiError)
      console.error('错误详情:', {
        message: apiError.message,
        code: apiError.code,
        error: apiError.error,
        response: apiError.response,
      })
      // 使用默认数据
      const onlineRates = new Array(7).fill(0)
      const weldingRates = new Array(7).fill(0)

      onlineRateHistory.value = dates.map((date, index) => ({
        time: date,
        rate: onlineRates[index],
      }))

      weldingRateHistory.value = dates.map((date, index) => ({
        time: date,
        rate: weldingRates[index],
      }))

      if (onlineRateChartInstance) {
        onlineRateChartInstance.setOption({
          xAxis: { data: dates },
          series: [
            { name: '在线率', data: onlineRates },
            { name: '焊接率', data: weldingRates },
          ],
        })
      }
    }
  } catch (error) {
    console.error('获取在线率和焊接率统计数据失败:', error)
    // 如果API失败，使用模拟数据
    const dates = []
    const onlineRates = []
    const weldingRates = []

    for (let i = 6; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      dates.push(date.toISOString().split('T')[0].substring(5))
      onlineRates.push(Math.round(Math.random() * 20 + 75)) // 75-95%
      weldingRates.push(Math.round(Math.random() * 30 + 40)) // 40-70%
    }

    onlineRateHistory.value = dates.map((date, index) => ({
      time: date,
      rate: onlineRates[index],
    }))

    weldingRateHistory.value = dates.map((date, index) => ({
      time: date,
      rate: weldingRates[index],
    }))

    if (onlineRateChartInstance) {
      onlineRateChartInstance.setOption({
        xAxis: { data: dates },
        series: [
          { name: '在线率', data: onlineRates },
          { name: '焊接率', data: weldingRates },
        ],
      })
    }
  }
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

      // 状态分布历史数据已移除，改为报警类型分布图表
      // 报警类型分布图表不需要在这里更新，只在初始化时获取数据
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
  nextTick(async () => {
    initOnlineRateChart()
    initConsumptionChart()
    initAlarmCategoryChart()

    // 获取7日消耗数据
    await fetchConsumptionData()
    // 获取在线率和焊接率数据
    await fetchOnlineWeldingRateData()
    // 获取报警类型分布数据
    await fetchAlarmCategoryData()
    // 获取报警记录Top数据
    await fetchAlarmRecordTopData()
  })

  // 移除定时器，只在初始化时获取数据
  // intervalId = setInterval(() => fetchDeviceStats(false), 15000)
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
  if (consumptionChartInstance) {
    consumptionChartInstance.dispose()
    consumptionChartInstance = null
  }
  if (alarmCategoryChartInstance) {
    alarmCategoryChartInstance.dispose()
    alarmCategoryChartInstance = null
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

/* 报警项悬停样式 */
.n-card:hover {
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.15);
  transform: translateY(-1px);
  transition: all 0.3s ease;
}

/* 报警Top列表弹窗样式 */
.alarm-top-list {
  max-height: 500px;
  overflow-y: auto;
}

.alarm-top-item {
  display: flex;
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.alarm-top-item:hover {
  background: #f5f5f5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.alarm-top-rank {
  margin-right: 16px;
}

.rank-badge {
  display: inline-block;
  width: 40px;
  height: 40px;
  line-height: 40px;
  text-align: center;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
  color: white;
  background: #8c8c8c;
}

.rank-badge.rank-first {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #333;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.rank-badge.rank-second {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #333;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.3);
}

.rank-badge.rank-third {
  background: linear-gradient(135deg, #cd7f32, #daa520);
  color: white;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.3);
}

.alarm-top-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-info {
  flex: 1;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.device-code {
  font-size: 12px;
  color: #666;
}

.alarm-duration {
  text-align: right;
}

.duration-text {
  font-size: 14px;
  font-weight: 600;
  color: #ff4d4f;
  background: #fff2f0;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #ffccc7;
}
</style>
