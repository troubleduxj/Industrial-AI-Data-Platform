/**
 * 配置模板服务
 * 提供配置模板的获取、缓存和字段解析功能
 */
import { collectorApi } from '@/api/collector'
import { useMessage } from 'naive-ui'

class TemplateService {
  constructor() {
    this.cache = new Map()
    this.message = useMessage()
  }

  /**
   * 获取配置模板列表
   * @param {Object} params - 查询参数
   * @returns {Promise<Array>} 模板列表
   */
  async getTemplates(params = {}) {
    try {
      const response = await collectorApi.getConfigTemplates(params)
      return response.data || []
    } catch (error) {
      console.error('获取配置模板失败:', error)
      this.message?.error('获取配置模板失败')
      return []
    }
  }

  /**
   * 获取配置模板详情
   * @param {string|number} templateId - 模板ID
   * @param {boolean} useCache - 是否使用缓存
   * @returns {Promise<Object|null>} 模板详情
   */
  async getTemplate(templateId, useCache = true) {
    const cacheKey = `template_${templateId}`

    // 检查缓存
    if (useCache && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)
    }

    try {
      const response = await collectorApi.getConfigTemplate(templateId)
      const template = response.data

      if (template && useCache) {
        this.cache.set(cacheKey, template)
      }

      return template
    } catch (error) {
      console.error('获取配置模板详情失败:', error)
      this.message?.error('获取配置模板详情失败')
      return null
    }
  }

  /**
   * 将模板字段转换为动态表单字段
   * @param {Array} templateFields - 模板字段列表
   * @returns {Array} 动态表单字段列表
   */
  convertTemplateToFormFields(templateFields = []) {
    return templateFields.map((field) => {
      const formField = {
        name: field.field_name,
        label: field.display_name || field.field_name,
        type: this.mapFieldType(field.field_type),
        required: field.is_required || false,
        placeholder: field.placeholder || `请输入${field.display_name || field.field_name}`,
        defaultValue: field.default_value,
        disabled: field.is_readonly || false,
        showFeedback: true,
      }

      // 根据字段类型添加特定配置
      switch (field.field_type) {
        case 'select':
        case 'radio':
        case 'checkbox':
          formField.options = this.parseOptions(field.options)
          formField.multiple = field.field_type === 'checkbox'
          break

        case 'number':
        case 'integer':
          formField.min = field.min_value
          formField.max = field.max_value
          formField.step = field.step || 1
          formField.precision = field.precision
          break

        case 'textarea':
          formField.rows = field.rows || 3
          formField.maxlength = field.max_length
          formField.showCount = !!field.max_length
          break

        case 'input':
        case 'text':
          formField.maxlength = field.max_length
          formField.showCount = !!field.max_length
          break

        case 'switch':
        case 'boolean':
          formField.checkedText = field.checked_text || '是'
          formField.uncheckedText = field.unchecked_text || '否'
          break

        case 'date':
          formField.dateType = field.date_type || 'date'
          break

        case 'dynamic':
          formField.onCreate = () => this.parseDefaultValue(field.item_default)
          formField.min = field.min_items || 0
          formField.max = field.max_items
          break
      }

      // 添加验证规则
      if (field.validation_rules) {
        formField.rules = this.parseValidationRules(field.validation_rules, formField)
      }

      // 添加字段联动
      if (field.dependencies) {
        formField.onChange = (value, formData) => {
          this.handleFieldDependencies(field.dependencies, value, formData)
        }
      }

      return formField
    })
  }

  /**
   * 映射字段类型
   * @param {string} templateType - 模板字段类型
   * @returns {string} 表单字段类型
   */
  mapFieldType(templateType) {
    const typeMap = {
      text: 'input',
      string: 'input',
      integer: 'number',
      float: 'number',
      boolean: 'switch',
      select: 'select',
      radio: 'select',
      checkbox: 'select',
      textarea: 'textarea',
      date: 'date',
      datetime: 'date',
      time: 'time',
      array: 'dynamic',
      object: 'group',
    }

    return typeMap[templateType] || 'input'
  }

  /**
   * 解析选项数据
   * @param {string|Array} options - 选项数据
   * @returns {Array} 选项列表
   */
  parseOptions(options) {
    if (Array.isArray(options)) {
      return options.map((opt) => {
        if (typeof opt === 'string') {
          return { label: opt, value: opt }
        }
        return {
          label: opt.label || opt.text || opt.name,
          value: opt.value || opt.key,
        }
      })
    }

    if (typeof options === 'string') {
      try {
        const parsed = JSON.parse(options)
        return this.parseOptions(parsed)
      } catch {
        // 如果是逗号分隔的字符串
        return options.split(',').map((opt) => {
          const trimmed = opt.trim()
          return { label: trimmed, value: trimmed }
        })
      }
    }

    return []
  }

  /**
   * 解析默认值
   * @param {any} defaultValue - 默认值
   * @returns {any} 解析后的默认值
   */
  parseDefaultValue(defaultValue) {
    if (typeof defaultValue === 'string') {
      try {
        return JSON.parse(defaultValue)
      } catch {
        return defaultValue
      }
    }
    return defaultValue
  }

  /**
   * 解析验证规则
   * @param {string|Object} rules - 验证规则
   * @param {Object} field - 字段配置
   * @returns {Object} 验证规则对象
   */
  parseValidationRules(rules, field) {
    let parsedRules = rules

    if (typeof rules === 'string') {
      try {
        parsedRules = JSON.parse(rules)
      } catch {
        return {}
      }
    }

    const validationRules = {}

    if (field.required) {
      validationRules.required = true
      validationRules.message = `请输入${field.label}`
      validationRules.trigger = ['blur', 'input']
    }

    if (parsedRules.pattern) {
      validationRules.pattern = new RegExp(parsedRules.pattern)
      validationRules.message = parsedRules.patternMessage || '格式不正确'
    }

    if (parsedRules.min !== undefined) {
      validationRules.min = parsedRules.min
    }

    if (parsedRules.max !== undefined) {
      validationRules.max = parsedRules.max
    }

    if (parsedRules.validator) {
      // 自定义验证器（需要在运行时动态创建）
      validationRules.validator = new Function('rule', 'value', parsedRules.validator)
    }

    return validationRules
  }

  /**
   * 处理字段依赖关系
   * @param {Array} dependencies - 依赖配置
   * @param {any} value - 当前字段值
   * @param {Object} formData - 表单数据
   */
  handleFieldDependencies(dependencies, value, formData) {
    dependencies.forEach((dep) => {
      const targetField = dep.target_field
      const condition = dep.condition
      const action = dep.action

      // 检查条件是否满足
      const conditionMet = this.evaluateCondition(condition, value)

      // 执行动作
      if (conditionMet) {
        this.executeFieldAction(targetField, action, formData)
      }
    })
  }

  /**
   * 评估条件
   * @param {Object} condition - 条件配置
   * @param {any} value - 当前值
   * @returns {boolean} 条件是否满足
   */
  evaluateCondition(condition, value) {
    const { operator, expected } = condition

    switch (operator) {
      case 'equals':
      case '==':
        return value === expected
      case 'not_equals':
      case '!=':
        return value !== expected
      case 'in':
        return Array.isArray(expected) && expected.includes(value)
      case 'not_in':
        return Array.isArray(expected) && !expected.includes(value)
      case 'greater_than':
      case '>':
        return value > expected
      case 'less_than':
      case '<':
        return value < expected
      case 'contains':
        return String(value).includes(expected)
      default:
        return false
    }
  }

  /**
   * 执行字段动作
   * @param {string} targetField - 目标字段
   * @param {Object} action - 动作配置
   * @param {Object} formData - 表单数据
   */
  executeFieldAction(targetField, action, formData) {
    const { type, value } = action

    switch (type) {
      case 'show':
        // 显示字段（需要在组件层面实现）
        break
      case 'hide':
        // 隐藏字段（需要在组件层面实现）
        break
      case 'set_value':
        formData[targetField] = value
        break
      case 'clear_value':
        delete formData[targetField]
        break
      case 'enable':
        // 启用字段（需要在组件层面实现）
        break
      case 'disable':
        // 禁用字段（需要在组件层面实现）
        break
    }
  }

  /**
   * 根据采集器类型获取推荐模板
   * @param {string} collectorType - 采集器类型
   * @returns {Promise<Array>} 推荐模板列表
   */
  async getRecommendedTemplates(collectorType) {
    try {
      const templates = await this.getTemplates({
        collector_type: collectorType,
        is_active: true,
      })

      // 按推荐度排序
      return templates.sort((a, b) => {
        const scoreA = (a.usage_count || 0) + (a.rating || 0) * 10
        const scoreB = (b.usage_count || 0) + (b.rating || 0) * 10
        return scoreB - scoreA
      })
    } catch (error) {
      console.error('获取推荐模板失败:', error)
      return []
    }
  }

  /**
   * 清除缓存
   * @param {string} key - 缓存键，不传则清除所有
   */
  clearCache(key) {
    if (key) {
      this.cache.delete(key)
    } else {
      this.cache.clear()
    }
  }

  /**
   * 验证配置数据
   * @param {Object} configData - 配置数据
   * @param {string} templateId - 模板ID
   * @returns {Promise<Object>} 验证结果
   */
  async validateConfig(configData, templateId) {
    try {
      const response = await collectorApi.validateConfig({
        config: configData,
        template_id: templateId,
      })

      return {
        valid: response.data.valid,
        errors: response.data.errors || [],
        warnings: response.data.warnings || [],
      }
    } catch (error) {
      console.error('配置验证失败:', error)
      return {
        valid: false,
        errors: ['配置验证服务异常'],
        warnings: [],
      }
    }
  }
}

// 创建单例实例
const templateService = new TemplateService()

export default templateService
export { TemplateService }
