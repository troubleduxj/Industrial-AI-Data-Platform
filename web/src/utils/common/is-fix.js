/**
 * 工具函数增强版本 - 修复参数验证问题
 */

/**
 * 增强的空值检查函数，专门用于API参数验证
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为空或无效
 */
export function isEmptyParams(val) {
  // null, undefined, 空字符串
  if (val == null || val === '') return true

  // 空对象
  if (typeof val === 'object' && !Array.isArray(val)) {
    return Object.keys(val).length === 0
  }

  // 空数组
  if (Array.isArray(val)) {
    return val.length === 0
  }

  return false
}

/**
 * 检查删除操作参数是否有效
 * @param {object} params 删除参数
 * @returns {boolean} 参数是否有效
 */
export function isValidDeleteParams(params) {
  if (isEmptyParams(params)) return false

  // 检查是否包含常见的ID字段
  const idFields = ['id', 'role_id', 'user_id', 'dept_id', 'menu_id', 'api_id']
  return idFields.some((field) => params[field] != null && params[field] !== '')
}

/**
 * 检查值是否为空
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为空
 */
export function isEmpty(val) {
  if (val == null) return true
  if (typeof val === 'string') return val.trim() === ''
  if (Array.isArray(val)) return val.length === 0
  if (typeof val === 'object') return Object.keys(val).length === 0
  return false
}

/**
 * 检查值是否不为空
 * @param {any} val 要检查的值
 * @returns {boolean} 是否不为空
 */
export function isNotEmpty(val) {
  return !isEmpty(val)
}

/**
 * 检查是否为数字
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为数字
 */
export function isNumber(val) {
  return typeof val === 'number' && !isNaN(val)
}

/**
 * 检查是否为字符串
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为字符串
 */
export function isString(val) {
  return typeof val === 'string'
}

/**
 * 检查是否为布尔值
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为布尔值
 */
export function isBoolean(val) {
  return typeof val === 'boolean'
}

/**
 * 检查是否为对象
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为对象
 */
export function isObject(val) {
  return val !== null && typeof val === 'object' && !Array.isArray(val)
}

/**
 * 检查是否为数组
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为数组
 */
export function isArray(val) {
  return Array.isArray(val)
}

/**
 * 检查是否为函数
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为函数
 */
export function isFunction(val) {
  return typeof val === 'function'
}

/**
 * 检查是否为有效的ID
 * @param {any} val 要检查的值
 * @returns {boolean} 是否为有效的ID
 */
export function isValidId(val) {
  return isNumber(val) && val > 0
}

/**
 * 检查是否为有效的邮箱
 * @param {string} email 邮箱地址
 * @returns {boolean} 是否为有效邮箱
 */
export function isValidEmail(email) {
  if (!isString(email)) return false
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 检查是否为有效的手机号
 * @param {string} phone 手机号
 * @returns {boolean} 是否为有效手机号
 */
export function isValidPhone(phone) {
  if (!isString(phone)) return false
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

export default {
  isEmpty,
  isNotEmpty,
  isNumber,
  isString,
  isBoolean,
  isObject,
  isArray,
  isFunction,
  isValidId,
  isValidEmail,
  isValidPhone,
  isEmptyParams,
  isValidDeleteParams,
}
