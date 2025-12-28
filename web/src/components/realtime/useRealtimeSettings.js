/**
 * 实时监控设置 Composable
 * 
 * 需求: 7.5 - 前端应支持配置数据刷新频率和显示精度
 */

import { ref, watch, onMounted } from 'vue'

// 本地存储键
const STORAGE_KEY = 'realtime_monitor_settings'

// 默认设置
const DEFAULT_SETTINGS = {
  refreshInterval: 1000,      // 刷新间隔（毫秒）
  displayPrecision: 2,        // 显示精度（小数位数）
  autoScroll: true,           // 自动滚动
  showAlertNotifications: true, // 显示告警通知
  playAlertSound: false,      // 播放告警声音
  maxDataPoints: 100,         // 最大数据点数
  chartType: 'line',          // 图表类型
  theme: 'auto'               // 主题
}

// 刷新间隔选项
export const REFRESH_INTERVAL_OPTIONS = [
  { label: '100ms (高频)', value: 100 },
  { label: '500ms', value: 500 },
  { label: '1秒 (推荐)', value: 1000 },
  { label: '2秒', value: 2000 },
  { label: '5秒', value: 5000 },
  { label: '10秒', value: 10000 },
  { label: '30秒', value: 30000 },
  { label: '1分钟', value: 60000 }
]

// 显示精度选项
export const DISPLAY_PRECISION_OPTIONS = [
  { label: '整数', value: 0 },
  { label: '1位小数', value: 1 },
  { label: '2位小数 (推荐)', value: 2 },
  { label: '3位小数', value: 3 },
  { label: '4位小数', value: 4 },
  { label: '6位小数', value: 6 }
]

/**
 * 实时监控设置 Composable
 * @param {Object} initialSettings - 初始设置覆盖
 */
export function useRealtimeSettings(initialSettings = {}) {
  // 设置状态
  const settings = ref({ ...DEFAULT_SETTINGS, ...initialSettings })
  
  // 单独的响应式引用（方便绑定）
  const refreshInterval = ref(settings.value.refreshInterval)
  const displayPrecision = ref(settings.value.displayPrecision)
  const autoScroll = ref(settings.value.autoScroll)
  const showAlertNotifications = ref(settings.value.showAlertNotifications)
  const playAlertSound = ref(settings.value.playAlertSound)
  const maxDataPoints = ref(settings.value.maxDataPoints)
  const chartType = ref(settings.value.chartType)
  const theme = ref(settings.value.theme)
  
  /**
   * 从本地存储加载设置
   */
  function loadSettings() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        settings.value = { ...DEFAULT_SETTINGS, ...parsed }
        
        // 同步到单独的引用
        refreshInterval.value = settings.value.refreshInterval
        displayPrecision.value = settings.value.displayPrecision
        autoScroll.value = settings.value.autoScroll
        showAlertNotifications.value = settings.value.showAlertNotifications
        playAlertSound.value = settings.value.playAlertSound
        maxDataPoints.value = settings.value.maxDataPoints
        chartType.value = settings.value.chartType
        theme.value = settings.value.theme
      }
    } catch (error) {
      console.error('加载设置失败:', error)
    }
  }
  
  /**
   * 保存设置到本地存储
   */
  function saveSettings() {
    try {
      // 从单独的引用同步到设置对象
      settings.value = {
        refreshInterval: refreshInterval.value,
        displayPrecision: displayPrecision.value,
        autoScroll: autoScroll.value,
        showAlertNotifications: showAlertNotifications.value,
        playAlertSound: playAlertSound.value,
        maxDataPoints: maxDataPoints.value,
        chartType: chartType.value,
        theme: theme.value
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings.value))
    } catch (error) {
      console.error('保存设置失败:', error)
    }
  }
  
  /**
   * 重置为默认设置
   */
  function resetSettings() {
    settings.value = { ...DEFAULT_SETTINGS }
    
    refreshInterval.value = DEFAULT_SETTINGS.refreshInterval
    displayPrecision.value = DEFAULT_SETTINGS.displayPrecision
    autoScroll.value = DEFAULT_SETTINGS.autoScroll
    showAlertNotifications.value = DEFAULT_SETTINGS.showAlertNotifications
    playAlertSound.value = DEFAULT_SETTINGS.playAlertSound
    maxDataPoints.value = DEFAULT_SETTINGS.maxDataPoints
    chartType.value = DEFAULT_SETTINGS.chartType
    theme.value = DEFAULT_SETTINGS.theme
    
    saveSettings()
  }
  
  /**
   * 更新单个设置
   */
  function updateSetting(key, value) {
    if (key in settings.value) {
      settings.value[key] = value
      
      // 同步到对应的引用
      switch (key) {
        case 'refreshInterval': refreshInterval.value = value; break
        case 'displayPrecision': displayPrecision.value = value; break
        case 'autoScroll': autoScroll.value = value; break
        case 'showAlertNotifications': showAlertNotifications.value = value; break
        case 'playAlertSound': playAlertSound.value = value; break
        case 'maxDataPoints': maxDataPoints.value = value; break
        case 'chartType': chartType.value = value; break
        case 'theme': theme.value = value; break
      }
      
      saveSettings()
    }
  }
  
  /**
   * 格式化数值
   */
  function formatValue(value, precision = null) {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'number') {
      return value.toFixed(precision ?? displayPrecision.value)
    }
    return String(value)
  }
  
  /**
   * 验证刷新间隔
   */
  function validateRefreshInterval(interval) {
    const min = 100
    const max = 60000
    return Math.max(min, Math.min(max, interval))
  }
  
  /**
   * 验证显示精度
   */
  function validateDisplayPrecision(precision) {
    return Math.max(0, Math.min(10, precision))
  }
  
  // 监听设置变化并自动保存
  watch([refreshInterval, displayPrecision, autoScroll, showAlertNotifications, 
         playAlertSound, maxDataPoints, chartType, theme], () => {
    saveSettings()
  })
  
  // 初始化时加载设置
  onMounted(() => {
    loadSettings()
  })
  
  return {
    // 设置对象
    settings,
    
    // 单独的设置项
    refreshInterval,
    displayPrecision,
    autoScroll,
    showAlertNotifications,
    playAlertSound,
    maxDataPoints,
    chartType,
    theme,
    
    // 方法
    loadSettings,
    saveSettings,
    resetSettings,
    updateSetting,
    formatValue,
    validateRefreshInterval,
    validateDisplayPrecision,
    
    // 选项
    refreshIntervalOptions: REFRESH_INTERVAL_OPTIONS,
    displayPrecisionOptions: DISPLAY_PRECISION_OPTIONS
  }
}

export default useRealtimeSettings
