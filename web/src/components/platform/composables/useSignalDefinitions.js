/**
 * 信号定义组合式函数
 * 提供信号定义的获取、缓存和转换功能
 */
import { ref, computed, watch } from 'vue'
import { assetCategoryApi, signalApi } from '@/api/v3/platform'

// 信号定义缓存
const signalCache = new Map()

/**
 * 信号定义组合式函数
 * @param {number|string} categoryId - 资产类别ID或编码
 */
export function useSignalDefinitions(categoryId) {
  const signals = ref([])
  const loading = ref(false)
  const error = ref(null)

  // 按分组组织的信号
  const signalGroups = computed(() => {
    const groups = {}
    
    signals.value.forEach(signal => {
      const groupName = signal.field_group || signal.display_config?.group || 'default'
      if (!groups[groupName]) {
        groups[groupName] = {
          name: groupName,
          title: getGroupTitle(groupName),
          signals: []
        }
      }
      groups[groupName].signals.push(signal)
    })

    // 按排序字段排序
    Object.values(groups).forEach(group => {
      group.signals.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    })

    return Object.values(groups).sort((a, b) => {
      const order = ['core', 'temperature', 'power', 'speed', 'dimension', 'pressure', 'other', 'default']
      return order.indexOf(a.name) - order.indexOf(b.name)
    })
  })

  // 实时监控信号
  const realtimeSignals = computed(() => {
    return signals.value.filter(s => s.is_realtime)
  })

  // 特征工程信号
  const featureSignals = computed(() => {
    return signals.value.filter(s => s.is_feature)
  })

  // 存储信号
  const storedSignals = computed(() => {
    return signals.value.filter(s => s.is_stored)
  })

  // 报警启用信号
  const alarmSignals = computed(() => {
    return signals.value.filter(s => s.is_alarm_enabled)
  })

  // 获取分组标题
  function getGroupTitle(groupName) {
    const titles = {
      core: '核心参数',
      temperature: '温度相关',
      power: '功率相关',
      speed: '速度相关',
      dimension: '尺寸相关',
      pressure: '压力相关',
      other: '其他参数',
      default: '基本信息'
    }
    return titles[groupName] || groupName
  }

  // 加载信号定义
  async function loadSignals(forceRefresh = false) {
    if (!categoryId) return

    const cacheKey = String(categoryId)
    
    // 检查缓存
    if (!forceRefresh && signalCache.has(cacheKey)) {
      signals.value = signalCache.get(cacheKey)
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await assetCategoryApi.getSignals(categoryId)
      const data = response.data || response
      
      signals.value = Array.isArray(data) ? data : (data.items || data.signals || [])
      
      // 更新缓存
      signalCache.set(cacheKey, signals.value)
    } catch (err) {
      error.value = err.message || '加载信号定义失败'
      console.error('加载信号定义失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 将信号定义转换为表单字段配置
  function toFormFields(options = {}) {
    const { 
      includeGroups = true,
      filterFn = null,
      readonly = false 
    } = options

    let filteredSignals = signals.value
    if (filterFn) {
      filteredSignals = filteredSignals.filter(filterFn)
    }

    return filteredSignals.map(signal => ({
      name: signal.code,
      label: signal.name,
      type: mapDataTypeToFieldType(signal.data_type),
      required: signal.is_required || false,
      disabled: readonly,
      placeholder: `请输入${signal.name}`,
      // 数值范围
      min: signal.value_range?.min,
      max: signal.value_range?.max,
      // 精度
      precision: signal.data_type === 'float' ? 2 : 0,
      // 单位
      unit: signal.unit,
      // 验证规则
      rules: buildValidationRules(signal),
      // 分组
      group: signal.field_group || signal.display_config?.group || 'default',
      // 排序
      order: signal.sort_order || 0,
      // 原始信号定义
      _signal: signal
    }))
  }

  // 将信号定义转换为表格列配置
  function toTableColumns(options = {}) {
    const { 
      filterFn = null,
      showUnit = true,
      width = 120 
    } = options

    let filteredSignals = signals.value
    if (filterFn) {
      filteredSignals = filteredSignals.filter(filterFn)
    }

    return filteredSignals.map(signal => ({
      key: signal.code,
      title: showUnit && signal.unit ? `${signal.name} (${signal.unit})` : signal.name,
      width,
      align: isNumericType(signal.data_type) ? 'right' : 'left',
      render: (row) => formatSignalValue(row[signal.code], signal),
      sorter: isNumericType(signal.data_type) ? 'default' : false,
      // 原始信号定义
      _signal: signal
    }))
  }

  // 映射数据类型到表单字段类型
  function mapDataTypeToFieldType(dataType) {
    const typeMap = {
      'float': 'number',
      'int': 'number',
      'double': 'number',
      'bigint': 'number',
      'bool': 'switch',
      'boolean': 'switch',
      'string': 'input',
      'text': 'textarea',
      'date': 'date',
      'datetime': 'datetime',
      'json': 'json'
    }
    return typeMap[dataType] || 'input'
  }

  // 构建验证规则
  function buildValidationRules(signal) {
    const rules = []

    // 必填验证
    if (signal.is_required) {
      rules.push({
        required: true,
        message: `请输入${signal.name}`,
        trigger: ['blur', 'input']
      })
    }

    // 数值范围验证
    if (signal.value_range && isNumericType(signal.data_type)) {
      if (signal.value_range.min !== undefined) {
        rules.push({
          type: 'number',
          min: signal.value_range.min,
          message: `${signal.name}不能小于${signal.value_range.min}`,
          trigger: ['blur', 'input']
        })
      }
      if (signal.value_range.max !== undefined) {
        rules.push({
          type: 'number',
          max: signal.value_range.max,
          message: `${signal.name}不能大于${signal.value_range.max}`,
          trigger: ['blur', 'input']
        })
      }
    }

    // 自定义验证规则
    if (signal.validation_rules) {
      if (signal.validation_rules.maxLength) {
        rules.push({
          max: signal.validation_rules.maxLength,
          message: `${signal.name}长度不能超过${signal.validation_rules.maxLength}个字符`,
          trigger: ['blur', 'input']
        })
      }
      if (signal.validation_rules.pattern) {
        rules.push({
          pattern: new RegExp(signal.validation_rules.pattern),
          message: signal.validation_rules.patternMessage || `${signal.name}格式不正确`,
          trigger: ['blur', 'input']
        })
      }
    }

    return rules
  }

  // 格式化信号值
  function formatSignalValue(value, signal) {
    if (value === null || value === undefined) return '-'

    switch (signal.data_type) {
      case 'float':
      case 'double':
        return typeof value === 'number' ? value.toFixed(2) : String(value)
      case 'int':
      case 'bigint':
        return String(Math.round(Number(value)))
      case 'bool':
      case 'boolean':
        return value ? '是' : '否'
      default:
        return String(value)
    }
  }

  // 判断是否为数值类型
  function isNumericType(dataType) {
    return ['float', 'int', 'double', 'bigint'].includes(dataType)
  }

  // 清除缓存
  function clearCache(categoryIdToClear = null) {
    if (categoryIdToClear) {
      signalCache.delete(String(categoryIdToClear))
    } else {
      signalCache.clear()
    }
  }

  // 监听categoryId变化
  watch(() => categoryId, (newId) => {
    if (newId) {
      loadSignals()
    }
  }, { immediate: true })

  return {
    // 状态
    signals,
    loading,
    error,
    // 计算属性
    signalGroups,
    realtimeSignals,
    featureSignals,
    storedSignals,
    alarmSignals,
    // 方法
    loadSignals,
    toFormFields,
    toTableColumns,
    formatSignalValue,
    clearCache,
    getGroupTitle
  }
}

export default useSignalDefinitions
