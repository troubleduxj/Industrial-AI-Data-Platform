/**
 * 动态表单组合式函数
 * 提供基于信号定义的动态表单生成和验证功能
 */
import { ref, computed, watch, reactive } from 'vue'
import { useSignalDefinitions } from './useSignalDefinitions'

/**
 * 动态表单组合式函数
 * @param {number|string} categoryId - 资产类别ID
 * @param {Object} options - 配置选项
 */
export function useDynamicForm(categoryId, options = {}) {
  const {
    initialData = {},
    readonly = false,
    validateOnChange = true
  } = options

  const { 
    signals, 
    signalGroups, 
    loading: signalsLoading,
    toFormFields,
    formatSignalValue
  } = useSignalDefinitions(categoryId)

  const formRef = ref(null)
  const formData = reactive({})
  const validationErrors = ref({})
  const isDirty = ref(false)
  const isSubmitting = ref(false)

  // 表单字段配置
  const formFields = computed(() => {
    return toFormFields({ readonly })
  })

  // 按分组组织的表单字段
  const groupedFormFields = computed(() => {
    const groups = {}
    
    formFields.value.forEach(field => {
      const groupName = field.group || 'default'
      if (!groups[groupName]) {
        groups[groupName] = {
          name: groupName,
          title: getGroupTitle(groupName),
          fields: []
        }
      }
      groups[groupName].fields.push(field)
    })

    // 按排序字段排序
    Object.values(groups).forEach(group => {
      group.fields.sort((a, b) => (a.order || 0) - (b.order || 0))
    })

    return Object.values(groups).sort((a, b) => {
      const order = ['core', 'temperature', 'power', 'speed', 'dimension', 'pressure', 'other', 'default']
      return order.indexOf(a.name) - order.indexOf(b.name)
    })
  })

  // 表单验证规则
  const formRules = computed(() => {
    const rules = {}
    formFields.value.forEach(field => {
      if (field.rules && field.rules.length > 0) {
        rules[field.name] = field.rules
      }
    })
    return rules
  })

  // 是否有验证错误
  const hasErrors = computed(() => {
    return Object.keys(validationErrors.value).length > 0
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

  // 初始化表单数据
  function initializeFormData(data = {}) {
    // 清空现有数据
    Object.keys(formData).forEach(key => {
      delete formData[key]
    })

    // 根据信号定义设置默认值
    signals.value.forEach(signal => {
      const key = signal.code
      if (data[key] !== undefined) {
        formData[key] = data[key]
      } else {
        formData[key] = getDefaultValue(signal)
      }
    })

    isDirty.value = false
    validationErrors.value = {}
  }

  // 获取默认值
  function getDefaultValue(signal) {
    switch (signal.data_type) {
      case 'float':
      case 'int':
      case 'double':
      case 'bigint':
        return null
      case 'bool':
      case 'boolean':
        return false
      case 'string':
      case 'text':
        return ''
      case 'json':
        return {}
      default:
        return null
    }
  }

  // 设置字段值
  function setFieldValue(fieldName, value) {
    formData[fieldName] = value
    isDirty.value = true

    if (validateOnChange) {
      validateField(fieldName)
    }
  }

  // 获取字段值
  function getFieldValue(fieldName) {
    return formData[fieldName]
  }

  // 验证单个字段
  async function validateField(fieldName) {
    const field = formFields.value.find(f => f.name === fieldName)
    if (!field || !field.rules) return true

    const value = formData[fieldName]
    const errors = []

    for (const rule of field.rules) {
      // 必填验证
      if (rule.required && (value === null || value === undefined || value === '')) {
        errors.push(rule.message)
        continue
      }

      // 最小值验证
      if (rule.min !== undefined && typeof value === 'number' && value < rule.min) {
        errors.push(rule.message)
        continue
      }

      // 最大值验证
      if (rule.max !== undefined && typeof value === 'number' && value > rule.max) {
        errors.push(rule.message)
        continue
      }

      // 正则验证
      if (rule.pattern && typeof value === 'string' && !rule.pattern.test(value)) {
        errors.push(rule.message)
        continue
      }
    }

    if (errors.length > 0) {
      validationErrors.value[fieldName] = errors
      return false
    } else {
      delete validationErrors.value[fieldName]
      return true
    }
  }

  // 验证整个表单
  async function validate() {
    const results = await Promise.all(
      formFields.value.map(field => validateField(field.name))
    )
    return results.every(r => r)
  }

  // 重置表单
  function resetForm() {
    initializeFormData(initialData)
  }

  // 获取表单数据（用于提交）
  function getFormData() {
    const data = {}
    
    signals.value.forEach(signal => {
      const key = signal.code
      let value = formData[key]

      // 数据类型转换
      if (value !== null && value !== undefined && value !== '') {
        switch (signal.data_type) {
          case 'int':
          case 'bigint':
            value = parseInt(value, 10)
            break
          case 'float':
          case 'double':
            value = parseFloat(value)
            break
          case 'bool':
          case 'boolean':
            value = Boolean(value)
            break
        }
      }

      data[key] = value
    })

    return data
  }

  // 设置表单数据
  function setFormData(data) {
    Object.keys(data).forEach(key => {
      if (formData.hasOwnProperty(key)) {
        formData[key] = data[key]
      }
    })
    isDirty.value = true
  }

  // 清除验证错误
  function clearValidation() {
    validationErrors.value = {}
  }

  // 监听信号定义变化，重新初始化表单
  watch(signals, () => {
    initializeFormData(initialData)
  }, { deep: true })

  // 监听初始数据变化
  watch(() => initialData, (newData) => {
    initializeFormData(newData)
  }, { deep: true })

  return {
    // 状态
    formRef,
    formData,
    validationErrors,
    isDirty,
    isSubmitting,
    signalsLoading,
    // 计算属性
    formFields,
    groupedFormFields,
    formRules,
    hasErrors,
    // 方法
    initializeFormData,
    setFieldValue,
    getFieldValue,
    validateField,
    validate,
    resetForm,
    getFormData,
    setFormData,
    clearValidation,
    getGroupTitle
  }
}

export default useDynamicForm
