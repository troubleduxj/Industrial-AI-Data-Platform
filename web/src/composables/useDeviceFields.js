import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import deviceMaintenanceApi from '@/api/device-maintenance'

/**
 * 设备字段配置业务逻辑组合函数
 * 通用的设备字段管理功能，可在多个模块中复用
 */
export function useDeviceFields() {
  const message = useMessage()

  // 设备字段配置
  const deviceFields = ref([])
  const fieldsLoading = ref(false)
  const fieldsCache = ref(new Map()) // 字段配置缓存

  /**
   * 加载设备字段配置
   * @param {string} deviceType - 设备类型
   * @param {Object} options - 选项配置
   */
  const loadDeviceFields = async (deviceType, options = {}) => {
    if (!deviceType) {
      deviceFields.value = []
      return
    }

    // 检查缓存
    const cacheKey = `${deviceType}_${JSON.stringify(options)}`
    if (fieldsCache.value.has(cacheKey)) {
      deviceFields.value = fieldsCache.value.get(cacheKey)
      return
    }

    fieldsLoading.value = true

    try {
      const response = await deviceMaintenanceApi.getDeviceFields(deviceType, options)

      if (response && response.data) {
        const fields = response.data
        // 处理字段配置，确保包含必要的属性
        const processedFields = fields.map((field) => ({
          ...field,
          field_label: field.field_name || field.field_label,
          options: field.options || field.dict_options || [],
        }))

        deviceFields.value = processedFields
        // 缓存字段配置
        fieldsCache.value.set(cacheKey, processedFields)
      } else {
        // 使用默认字段配置
        const defaultFields = getDefaultDeviceFields(deviceType)
        deviceFields.value = defaultFields
        fieldsCache.value.set(cacheKey, defaultFields)
      }
    } catch (error) {
      console.error('加载设备字段配置失败:', error)
      if (options.showError !== false) {
        message.error('加载设备字段配置失败')
      }

      // 降级到默认字段配置
      const defaultFields = getDefaultDeviceFields(deviceType)
      deviceFields.value = defaultFields
      fieldsCache.value.set(cacheKey, defaultFields)
    } finally {
      fieldsLoading.value = false
    }
  }

  /**
   * 获取默认设备字段配置
   * @param {string} deviceType - 设备类型
   */
  const getDefaultDeviceFields = (deviceType) => {
    const commonFields = [
      {
        field_code: 'manufacturer',
        field_name: '制造商',
        field_type: 'text',
        is_required: false,
        sort_order: 1,
      },
      {
        field_code: 'model',
        field_name: '型号',
        field_type: 'text',
        is_required: true,
        sort_order: 2,
      },
      {
        field_code: 'serial_number',
        field_name: '序列号',
        field_type: 'text',
        is_required: false,
        sort_order: 3,
      },
    ]

    // 根据设备类型返回特定字段
    // 规范化设备类型名称，处理大小写和别名
    const normalizedType = deviceType ? deviceType.toLowerCase() : ''
    
    // 处理别名映射
    let typeKey = normalizedType
    if (normalizedType === 'cutter' || normalizedType === 'cutters') {
      typeKey = 'cutting'
    } else if (normalizedType === 'welder' || normalizedType === 'weldings') {
      typeKey = 'welding'
    }

    switch (typeKey) {
      case 'welding':
        return [
          ...commonFields,
          {
            field_code: 'brand',
            field_name: '品牌',
            field_type: 'select',
            is_required: true,
            sort_order: 4,
            options: [
              { label: '松下', value: '松下' },
              { label: '林肯', value: '林肯' },
              { label: '米勒', value: '米勒' },
              { label: '奥太', value: '奥太' },
              { label: '其他', value: '其他' },
            ],
          },
          {
            field_code: 'pin_type',
            field_name: '接口类型',
            field_type: 'select',
            is_required: false,
            sort_order: 5,
            options: [
              { label: '7P', value: '7P' },
              { label: '9P', value: '9P' },
            ],
          },
          {
            field_code: 'welding_type',
            field_name: '焊接类型',
            field_type: 'select',
            is_required: false,
            sort_order: 6,
            options: [
              { label: '二氧化碳保护焊', value: '二氧化碳保护焊' },
              { label: '氩弧焊', value: '氩弧焊' },
              { label: '电焊', value: '电焊' },
              { label: '其他', value: '其他' },
            ],
          },
          {
            field_code: 'power_rating',
            field_name: '额定功率',
            field_type: 'number',
            is_required: false,
            sort_order: 7,
            min_value: 0,
            max_value: 10000,
            precision: 1,
          },
          {
            field_code: 'installation_date',
            field_name: '安装日期',
            field_type: 'date',
            is_required: false,
            sort_order: 8,
          },
        ]

      case 'cutting':
        return [
          ...commonFields,
          {
            field_code: 'cutting_type',
            field_name: '切割类型',
            field_type: 'select',
            is_required: false,
            sort_order: 4,
            options: [
              { label: '等离子切割', value: '等离子切割' },
              { label: '激光切割', value: '激光切割' },
              { label: '火焰切割', value: '火焰切割' },
              { label: '水切割', value: '水切割' },
            ],
          },
          {
            field_code: 'cutting_thickness',
            field_name: '切割厚度',
            field_type: 'number',
            is_required: false,
            sort_order: 5,
            min_value: 0,
            max_value: 200,
            precision: 1,
          },
        ]

      default:
        return commonFields
    }
  }

  /**
   * 获取字段验证规则
   * @param {Object} field - 字段配置
   */
  const getFieldValidationRules = (field) => {
    const rules = []

    // 必填验证
    if (field.is_required) {
      rules.push({
        required: true,
        message: `请填写${field.field_name}`,
        trigger: ['blur', 'change'],
      })
    }

    // 根据字段类型添加特定验证
    switch (field.field_type) {
      case 'number':
        if (field.min_value !== undefined) {
          rules.push({
            type: 'number',
            min: field.min_value,
            message: `${field.field_name}不能小于${field.min_value}`,
            trigger: ['blur', 'change'],
          })
        }
        if (field.max_value !== undefined) {
          rules.push({
            type: 'number',
            max: field.max_value,
            message: `${field.field_name}不能大于${field.max_value}`,
            trigger: ['blur', 'change'],
          })
        }
        break

      case 'text':
        if (field.max_length) {
          rules.push({
            max: field.max_length,
            message: `${field.field_name}长度不能超过${field.max_length}个字符`,
            trigger: ['blur', 'change'],
          })
        }
        break

      case 'email':
        rules.push({
          type: 'email',
          message: `请输入正确的${field.field_name}格式`,
          trigger: ['blur', 'change'],
        })
        break

      case 'url':
        rules.push({
          type: 'url',
          message: `请输入正确的${field.field_name}格式`,
          trigger: ['blur', 'change'],
        })
        break
    }

    // 自定义验证规则
    if (field.validation_rule) {
      try {
        const customRule = JSON.parse(field.validation_rule)
        if (customRule.pattern) {
          rules.push({
            pattern: new RegExp(customRule.pattern),
            message: customRule.message || `${field.field_name}格式不正确`,
            trigger: ['blur', 'change'],
          })
        }
      } catch (error) {
        console.warn('解析字段验证规则失败:', error)
      }
    }

    return rules
  }

  /**
   * 清除字段缓存
   * @param {string} deviceType - 可选，指定设备类型
   */
  const clearFieldsCache = (deviceType) => {
    if (deviceType) {
      // 清除特定设备类型的缓存
      const keysToDelete = []
      for (const key of fieldsCache.value.keys()) {
        if (key.startsWith(deviceType)) {
          keysToDelete.push(key)
        }
      }
      keysToDelete.forEach((key) => fieldsCache.value.delete(key))
    } else {
      // 清除所有缓存
      fieldsCache.value.clear()
    }
  }

  /**
   * 获取字段默认值
   * @param {Object} field - 字段配置
   */
  const getFieldDefaultValue = (field) => {
    switch (field.field_type) {
      case 'boolean':
        return false
      case 'number':
        return field.default_value !== undefined ? field.default_value : null
      case 'select':
      case 'dict_select':
        return field.default_value || null
      case 'date':
      case 'datetime':
        return null
      case 'array':
        return []
      case 'object':
        return {}
      default:
        return field.default_value || ''
    }
  }

  /**
   * 验证字段值
   * @param {Object} field - 字段配置
   * @param {any} value - 字段值
   */
  const validateFieldValue = (field, value) => {
    const rules = getFieldValidationRules(field)
    const errors = []

    for (const rule of rules) {
      if (rule.required && (!value || value === '')) {
        errors.push(rule.message)
        continue
      }

      if (rule.type === 'number' && value !== null && value !== '') {
        const numValue = Number(value)
        if (isNaN(numValue)) {
          errors.push(`${field.field_name}必须是数字`)
          continue
        }
        if (rule.min !== undefined && numValue < rule.min) {
          errors.push(rule.message)
          continue
        }
        if (rule.max !== undefined && numValue > rule.max) {
          errors.push(rule.message)
          continue
        }
      }

      if (rule.pattern && value && !rule.pattern.test(value)) {
        errors.push(rule.message)
        continue
      }

      if (rule.max && value && value.length > rule.max) {
        errors.push(rule.message)
        continue
      }
    }

    return errors
  }

  /**
   * 批量验证字段值
   * @param {Array} fields - 字段配置数组
   * @param {Object} values - 字段值对象
   */
  const validateAllFields = (fields, values) => {
    const errors = {}

    fields.forEach((field) => {
      const value = values[field.field_code]
      const fieldErrors = validateFieldValue(field, value)
      if (fieldErrors.length > 0) {
        errors[field.field_code] = fieldErrors
      }
    })

    return errors
  }

  return {
    // 状态
    deviceFields,
    fieldsLoading,

    // 方法
    loadDeviceFields,
    getFieldValidationRules,
    getFieldDefaultValue,
    validateFieldValue,
    validateAllFields,
    clearFieldsCache,
  }
}
