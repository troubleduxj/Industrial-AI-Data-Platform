import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'

export function useRepairValidation() {
  const message = useMessage()

  // 验证规则配置
  const validationRules = {
    // 基础信息验证
    repair_date: {
      required: true,
      message: '请选择报修日期',
      validator: (value) => {
        if (!value) return false
        // NDatePicker 返回的可能是时间戳或日期对象
        const repairDate = typeof value === 'number' ? new Date(value) : new Date(value)
        const today = new Date()
        today.setHours(23, 59, 59, 999) // 设置为当天的最后一刻
        // 报修日期不能超过今天
        return repairDate <= today
      },
      errorMessage: '报修日期不能超过今天',
    },

    category: {
      required: true,
      message: '请选择设备类别',
    },

    device_number: {
      required: true,
      message: '请输入焊机编号',
      // 移除严格的格式验证，因为设备编号格式可能多样化
      // pattern: /^[A-Z]\d{3}-\d{5}$/,
      // patternMessage: '焊机编号格式不正确，应为：字母+3位数字-5位数字（如：B001-00826）'
    },

    brand: {
      required: true,
      message: '请选择品牌',
    },

    model: {
      required: true,
      message: '请输入型号',
    },

    // 公司信息验证
    company: {
      required: true,
      message: '请输入公司名称',
      minLength: 2,
      maxLength: 100,
    },

    applicant: {
      required: true,
      message: '请输入申请人',
      minLength: 2,
      maxLength: 20,
      pattern: /^[\u4e00-\u9fa5a-zA-Z]+$/,
      patternMessage: '申请人姓名只能包含中文和英文字母',
    },

    phone: {
      required: true,
      message: '请输入联系电话',
      pattern: /^1[3-9]\d{9}$/,
      patternMessage: '请输入正确的手机号码',
    },

    // 故障信息验证（条件验证）
    fault_reason: {
      conditionalRequired: (formData) => formData.is_fault === true,
      message: '故障时必须选择故障原因',
    },

    damage_category: {
      conditionalRequired: (formData) => formData.is_fault === true,
      message: '故障时必须选择损坏类别',
    },

    fault_content: {
      conditionalRequired: (formData) => formData.is_fault === true,
      message: '故障时必须输入故障内容',
      minLength: 5,
      maxLength: 500,
    },

    // 维修信息验证
    repair_completion_date: {
      validator: (value, formData) => {
        if (!value || !formData.repair_date) return true
        const repairDate = new Date(formData.repair_date)
        const completionDate = new Date(value)
        // 完成日期不能早于报修日期
        return completionDate >= repairDate
      },
      errorMessage: '维修完成日期不能早于报修日期',
    },
  }

  // 业务规则验证
  const businessRules = {
    // 检查设备编号是否已存在
    checkDeviceNumberExists: async (deviceNumber) => {
      try {
        // 动态导入设备API
        const { default: deviceV2Api } = await import('@/api/device-v2')

        // 使用设备编号查询设备列表
        const response = await deviceV2Api.list({
          device_code: deviceNumber,
          page: 1,
          page_size: 1,
        })

        console.log('设备编号验证API响应:', response)

        if (response && response.success && response.data && response.data.success) {
          const data = response.data.data
          const devices = Array.isArray(data) ? data : (data && data.items) || []
          console.log('找到的设备:', devices)
          return devices.length > 0
        }

        // 如果API调用失败，暂时跳过验证以免阻塞用户操作
        console.warn('设备编号验证API调用失败，跳过验证')
        return true
      } catch (error) {
        console.error('设备编号验证失败:', error)
        // API调用失败时，暂时跳过验证
        return true
      }
    },

    // 检查重复报修
    checkDuplicateRepair: async (deviceNumber, repairDate) => {
      try {
        // 动态导入维修记录API
        const { repairRecordsApi } = await import('@/api/device-v2')

        // 格式化日期为YYYY-MM-DD格式
        const dateStr =
          typeof repairDate === 'number'
            ? new Date(repairDate).toISOString().split('T')[0]
            : new Date(repairDate).toISOString().split('T')[0]

        // 查询同一设备在同一天的维修记录
        const response = await repairRecordsApi.list({
          device_number: deviceNumber,
          repair_date: dateStr,
          page: 1,
          page_size: 1,
        })

        console.log('重复报修检查API响应:', response)

        if (response && response.success && response.data && response.data.success) {
          const data = response.data.data
          const records = Array.isArray(data) ? data : (data && data.records) || []
          console.log('找到的维修记录:', records)
          return records.length > 0
        }

        return false
      } catch (error) {
        console.warn('重复报修检查失败，跳过验证:', error)
        // API调用失败时，跳过验证
        return false
      }
    },

    // 验证维修人员权限
    validateRepairerPermission: async (repairer) => {
      try {
        // 这里可以调用用户管理API检查维修人员权限
        // 暂时跳过严格的权限验证，允许任何维修人员
        return true

        // 如果需要严格验证，可以使用以下逻辑：
        // const { default: userApi } = await import('@/api/user')
        // const response = await userApi.checkRepairerPermission(repairer)
        // return response.hasPermission
      } catch (error) {
        console.warn('维修人员权限验证失败，跳过验证:', error)
        // API调用失败时，跳过验证
        return true
      }
    },
  }

  // 验证单个字段
  const validateField = (fieldName, value, formData = {}) => {
    const rule = validationRules[fieldName]
    if (!rule) return { valid: true }

    // 检查值是否为空（考虑不同的空值情况）
    const isEmpty =
      value === null ||
      value === undefined ||
      value === '' ||
      (typeof value === 'string' && value.trim() === '')

    // 必填验证
    if (rule.required && isEmpty) {
      return { valid: false, message: rule.message }
    }

    // 条件必填验证
    if (rule.conditionalRequired && rule.conditionalRequired(formData) && isEmpty) {
      return { valid: false, message: rule.message }
    }

    // 如果值为空且不是必填，则跳过其他验证
    if (isEmpty) {
      return { valid: true }
    }

    // 长度验证
    if (rule.minLength && value.length < rule.minLength) {
      return { valid: false, message: `${fieldName}长度不能少于${rule.minLength}个字符` }
    }

    if (rule.maxLength && value.length > rule.maxLength) {
      return { valid: false, message: `${fieldName}长度不能超过${rule.maxLength}个字符` }
    }

    // 正则验证
    if (rule.pattern && !rule.pattern.test(value)) {
      return { valid: false, message: rule.patternMessage || rule.message }
    }

    // 自定义验证器
    if (rule.validator && !rule.validator(value, formData)) {
      return { valid: false, message: rule.errorMessage || rule.message }
    }

    return { valid: true }
  }

  // 验证整个表单
  const validateForm = async (formData) => {
    const errors = {}
    let isValid = true

    // 基础字段验证
    for (const [fieldName, value] of Object.entries(formData)) {
      const result = validateField(fieldName, value, formData)
      if (!result.valid) {
        errors[fieldName] = result.message
        isValid = false
      }
    }

    // 如果基础验证失败，直接返回
    if (!isValid) {
      return { valid: false, errors }
    }

    // 业务规则验证
    try {
      // 检查设备编号是否存在
      if (formData.device_number) {
        const deviceExists = await businessRules.checkDeviceNumberExists(formData.device_number)
        if (!deviceExists) {
          errors.device_number = '设备编号不存在，请检查后重新输入'
          isValid = false
        }
      }

      // 检查重复报修
      if (formData.device_number && formData.repair_date) {
        const isDuplicate = await businessRules.checkDuplicateRepair(
          formData.device_number,
          formData.repair_date
        )
        if (isDuplicate) {
          errors.device_number = '该设备今日已有报修记录，请检查是否重复提交'
          isValid = false
        }
      }

      // 验证维修人员权限
      if (formData.repairer) {
        const hasPermission = await businessRules.validateRepairerPermission(formData.repairer)
        if (!hasPermission) {
          errors.repairer = '该维修人员无权限，请选择授权的维修人员'
          isValid = false
        }
      }
    } catch (error) {
      console.error('Business rule validation failed:', error)
      message.error('验证过程中发生错误，请稍后重试')
      return { valid: false, errors: { general: '验证失败' } }
    }

    return { valid: isValid, errors }
  }

  // 实时验证（防抖）
  const debounceValidate = (() => {
    let timeout
    return (fieldName, value, formData, callback) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => {
        const result = validateField(fieldName, value, formData)
        callback(result)
      }, 300)
    }
  })()

  // 数据完整性检查
  const checkDataIntegrity = (formData) => {
    const warnings = []

    // 检查故障信息完整性
    if (formData.is_fault) {
      if (!formData.fault_location && formData.fault_content) {
        warnings.push('建议填写故障部位以便更好地定位问题')
      }

      if (!formData.repair_content && formData.fault_content) {
        warnings.push('建议填写维修内容以记录处理过程')
      }
    }

    // 检查维修信息完整性
    if (formData.repair_content && !formData.repairer) {
      warnings.push('建议填写维修人员信息')
    }

    if (formData.repairer && !formData.repair_completion_date) {
      warnings.push('建议填写维修完成日期')
    }

    // 检查联系信息
    if (formData.applicant && !formData.phone) {
      warnings.push('建议填写申请人联系电话')
    }

    return warnings
  }

  // 格式化验证错误信息
  const formatValidationErrors = (errors) => {
    const fieldLabels = {
      repair_date: '报修日期',
      category: '设备类别',
      device_number: '焊机编号',
      brand: '品牌',
      model: '型号',
      company: '公司',
      applicant: '申请人',
      phone: '联系电话',
      fault_reason: '故障原因',
      damage_category: '损坏类别',
      fault_content: '故障内容',
      repair_completion_date: '维修完成日期',
      repairer: '维修人员',
    }

    return Object.entries(errors).map(([field, message]) => {
      const label = fieldLabels[field] || field
      return `${label}: ${message}`
    })
  }

  return {
    validationRules,
    businessRules,
    validateField,
    validateForm,
    debounceValidate,
    checkDataIntegrity,
    formatValidationErrors,
  }
}
