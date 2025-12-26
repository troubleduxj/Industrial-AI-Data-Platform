import { computed } from 'vue'

/**
 * 通用表单验证业务逻辑组合函数
 * 提供可复用的表单验证功能
 */
export function useFormValidation(validationConfig = {}) {
  /**
   * 基础验证规则生成器
   */
  const createBaseRules = () => ({
    // 必填验证
    required: (message, trigger = ['change', 'blur']) => ({
      required: true,
      message,
      trigger,
    }),

    // 长度验证
    length: (min, max, message, trigger = ['input', 'blur']) => ({
      min,
      max,
      message,
      trigger,
    }),

    // 模式验证
    pattern: (pattern, message, trigger = ['input', 'blur']) => ({
      pattern,
      message,
      trigger,
    }),

    // 手机号验证
    phone: (trigger = ['input', 'blur']) => ({
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号码',
      trigger,
    }),

    // 邮箱验证
    email: (trigger = ['input', 'blur']) => ({
      type: 'email',
      message: '请输入正确的邮箱格式',
      trigger,
    }),

    // 数字验证
    number: (min, max, message, trigger = ['change', 'blur']) => ({
      type: 'number',
      min,
      max,
      message,
      trigger,
    }),

    // 自定义验证器
    validator: (validatorFn, trigger = ['change', 'blur']) => ({
      validator: validatorFn,
      trigger,
    }),

    // 日期验证
    date: (compareDate, comparison = 'before', message, trigger = ['change', 'blur']) => ({
      validator: (rule, value) => {
        if (!value) return true

        const valueDate = new Date(value)
        const compareToDate = new Date(compareDate)

        switch (comparison) {
          case 'before':
            return valueDate <= compareToDate ? true : new Error(message)
          case 'after':
            return valueDate >= compareToDate ? true : new Error(message)
          case 'equal':
            return valueDate.getTime() === compareToDate.getTime() ? true : new Error(message)
          default:
            return true
        }
      },
      trigger,
    }),
  })

  /**
   * 维修记录专用验证规则
   */
  const repairRecordRules = computed(() => ({
    device_id: [createBaseRules().required('请选择设备')],
    repair_date: [
      createBaseRules().required('请选择报修日期'),
      createBaseRules().date(new Date(), 'before', '报修日期不能晚于当前日期'),
    ],
    repair_status: [createBaseRules().required('请选择维修状态')],
    priority: [createBaseRules().required('请选择优先级')],
    applicant: [
      createBaseRules().required('请输入申请人'),
      createBaseRules().length(2, 50, '申请人长度应在2-50个字符之间'),
    ],
    applicant_phone: [createBaseRules().required('请输入联系电话'), createBaseRules().phone()],
    applicant_dept: [createBaseRules().length(0, 100, '申请部门长度不能超过100个字符')],
    applicant_workshop: [createBaseRules().length(0, 100, '申请车间长度不能超过100个字符')],
    construction_unit: [createBaseRules().length(0, 100, '施工单位长度不能超过100个字符')],
    fault_content: [
      createBaseRules().validator((rule, value, callback, source) => {
        // 如果是故障，故障内容为必填
        if (source.is_fault && (!value || value.trim() === '')) {
          return new Error('故障时请填写故障内容')
        }
        return true
      }),
      createBaseRules().length(0, 500, '故障内容长度不能超过500个字符'),
    ],
    fault_location: [createBaseRules().length(0, 200, '故障部位长度不能超过200个字符')],
    repair_content: [createBaseRules().length(0, 500, '维修内容长度不能超过500个字符')],
    parts_name: [createBaseRules().length(0, 500, '配件名称长度不能超过500个字符')],
    repairer: [createBaseRules().length(0, 100, '维修人员长度不能超过100个字符')],
    repair_start_time: [
      createBaseRules().validator((rule, value, callback, source) => {
        if (value && source.repair_date) {
          const startTime = new Date(value)
          const repairDate = new Date(source.repair_date)
          if (startTime < repairDate) {
            return new Error('维修开始时间不能早于报修日期')
          }
        }
        return true
      }),
    ],
    repair_completion_date: [
      createBaseRules().validator((rule, value, callback, source) => {
        if (value) {
          const completionDate = new Date(value)

          // 完成日期不能早于报修日期
          if (source.repair_date) {
            const repairDate = new Date(source.repair_date)
            if (completionDate < repairDate) {
              return new Error('维修完成日期不能早于报修日期')
            }
          }

          // 完成日期不能早于开始时间
          if (source.repair_start_time) {
            const startTime = new Date(source.repair_start_time)
            if (completionDate < startTime) {
              return new Error('维修完成日期不能早于维修开始时间')
            }
          }

          // 完成日期不能晚于当前日期
          if (completionDate > new Date()) {
            return new Error('维修完成日期不能晚于当前日期')
          }
        }
        return true
      }),
    ],
    repair_cost: [createBaseRules().number(0, 999999.99, '维修成本应在0-999999.99之间')],
    remarks: [createBaseRules().length(0, 1000, '备注长度不能超过1000个字符')],
  }))

  /**
   * 通用表单验证规则生成器
   * @param {Object} config - 验证配置
   */
  const generateFormRules = (config) => {
    const rules = {}
    const baseRules = createBaseRules()

    Object.entries(config).forEach(([fieldName, fieldConfig]) => {
      rules[fieldName] = []

      // 必填验证
      if (fieldConfig.required) {
        rules[fieldName].push(
          baseRules.required(
            fieldConfig.requiredMessage || `请填写${fieldConfig.label || fieldName}`
          )
        )
      }

      // 长度验证
      if (fieldConfig.minLength || fieldConfig.maxLength) {
        rules[fieldName].push(
          baseRules.length(
            fieldConfig.minLength || 0,
            fieldConfig.maxLength || Infinity,
            fieldConfig.lengthMessage || `${fieldConfig.label || fieldName}长度不符合要求`
          )
        )
      }

      // 模式验证
      if (fieldConfig.pattern) {
        rules[fieldName].push(
          baseRules.pattern(
            fieldConfig.pattern,
            fieldConfig.patternMessage || `${fieldConfig.label || fieldName}格式不正确`
          )
        )
      }

      // 数字验证
      if (fieldConfig.type === 'number') {
        rules[fieldName].push(
          baseRules.number(
            fieldConfig.min,
            fieldConfig.max,
            fieldConfig.numberMessage || `${fieldConfig.label || fieldName}数值不符合要求`
          )
        )
      }

      // 自定义验证器
      if (fieldConfig.validator) {
        rules[fieldName].push(baseRules.validator(fieldConfig.validator))
      }
    })

    return rules
  }

  /**
   * 验证表单数据
   * @param {Object} formData - 表单数据
   * @param {Object} rules - 验证规则
   * @param {Array} dynamicFields - 动态字段配置
   */
  const validateFormData = (formData, rules, dynamicFields = []) => {
    const errors = {}

    // 验证基础字段
    Object.entries(rules).forEach(([fieldName, fieldRules]) => {
      const value = formData[fieldName]

      for (const rule of fieldRules) {
        if (rule.required && (!value || value === '')) {
          errors[fieldName] = rule.message
          break
        }

        if (rule.pattern && value && !rule.pattern.test(value)) {
          errors[fieldName] = rule.message
          break
        }

        if (rule.min && value && value.length < rule.min) {
          errors[fieldName] = rule.message
          break
        }

        if (rule.max && value && value.length > rule.max) {
          errors[fieldName] = rule.message
          break
        }

        if (rule.type === 'number' && value !== null && value !== undefined) {
          const numValue = Number(value)
          if (isNaN(numValue)) {
            errors[fieldName] = `${fieldName}必须是数字`
            break
          }
          if (rule.min !== undefined && numValue < rule.min) {
            errors[fieldName] = rule.message
            break
          }
          if (rule.max !== undefined && numValue > rule.max) {
            errors[fieldName] = rule.message
            break
          }
        }

        if (rule.validator) {
          try {
            const result = rule.validator(rule, value, null, formData)
            if (result !== true && result instanceof Error) {
              errors[fieldName] = result.message
              break
            }
          } catch (error) {
            errors[fieldName] = error.message
            break
          }
        }
      }
    })

    // 验证动态字段
    if (dynamicFields.length > 0 && formData.device_specific_data) {
      dynamicFields.forEach((field) => {
        const value = formData.device_specific_data[field.field_code]

        if (field.is_required && (!value || value === '')) {
          errors[`device_specific_data.${field.field_code}`] = `请填写${field.field_name}`
        }

        // 根据字段类型进行特定验证
        if (value) {
          switch (field.field_type) {
            case 'number':
              const numValue = Number(value)
              if (isNaN(numValue)) {
                errors[`device_specific_data.${field.field_code}`] = `${field.field_name}必须是数字`
              } else {
                if (field.min_value !== undefined && numValue < field.min_value) {
                  errors[
                    `device_specific_data.${field.field_code}`
                  ] = `${field.field_name}不能小于${field.min_value}`
                }
                if (field.max_value !== undefined && numValue > field.max_value) {
                  errors[
                    `device_specific_data.${field.field_code}`
                  ] = `${field.field_name}不能大于${field.max_value}`
                }
              }
              break

            case 'text':
            case 'textarea':
              if (field.max_length && value.length > field.max_length) {
                errors[
                  `device_specific_data.${field.field_code}`
                ] = `${field.field_name}长度不能超过${field.max_length}个字符`
              }
              break

            case 'email':
              if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                errors[
                  `device_specific_data.${field.field_code}`
                ] = `请输入正确的${field.field_name}格式`
              }
              break
          }
        }
      })
    }

    return errors
  }

  /**
   * 验证单个字段
   * @param {string} fieldName - 字段名
   * @param {any} value - 字段值
   * @param {Object} formData - 完整表单数据
   * @param {Object} rules - 验证规则
   */
  const validateField = (fieldName, value, formData = {}, rules = {}) => {
    const fieldRules = rules[fieldName]
    if (!fieldRules) return []

    const errors = []

    for (const rule of fieldRules) {
      if (rule.required && (!value || value === '')) {
        errors.push(rule.message)
        continue
      }

      if (rule.pattern && value && !rule.pattern.test(value)) {
        errors.push(rule.message)
        continue
      }

      if (rule.min && value && value.length < rule.min) {
        errors.push(rule.message)
        continue
      }

      if (rule.max && value && value.length > rule.max) {
        errors.push(rule.message)
        continue
      }

      if (rule.type === 'number' && value !== null && value !== '') {
        const numValue = Number(value)
        if (isNaN(numValue)) {
          errors.push(`${fieldName}必须是数字`)
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

      if (rule.validator) {
        try {
          const result = rule.validator(rule, value, null, formData)
          if (result !== true && result instanceof Error) {
            errors.push(result.message)
          }
        } catch (error) {
          errors.push(error.message)
        }
      }
    }

    return errors
  }

  /**
   * 检查表单是否有效
   * @param {Object} formData - 表单数据
   * @param {Object} rules - 验证规则
   * @param {Array} dynamicFields - 动态字段配置
   */
  const isFormValid = (formData, rules, dynamicFields = []) => {
    const errors = validateFormData(formData, rules, dynamicFields)
    return Object.keys(errors).length === 0
  }

  /**
   * 获取字段错误信息
   * @param {Object} errors - 错误对象
   * @param {string} fieldPath - 字段路径
   */
  const getFieldError = (errors, fieldPath) => {
    return errors[fieldPath] || null
  }

  return {
    // 预定义规则
    repairRecordRules,

    // 工具方法
    createBaseRules,
    generateFormRules,
    validateFormData,
    validateField,
    isFormValid,
    getFieldError,
  }
}
