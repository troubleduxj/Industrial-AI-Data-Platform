/**
 * Shared 层工具函数兼容层
 * 从 shared 层导入工具函数，并提供别名以保持向后兼容
 */

// ========== 从 Shared 层导入 ==========
import {
  // 类型检查
  is,
  isDef,
  isUndef,
  isNull,
  isWhitespace,
  isObject,
  isArray,
  isString,
  isNumber,
  isBoolean,
  isDate,
  isRegExp,
  isFunction,
  isPromise,
  isNullOrUndef,
  isNullOrWhitespace,
  isEmpty,
  ifNull,
  isUrl,
  isExternal,
  isValidEmail,
  isValidPhone,

  // 日期时间
  formatDateTime as sharedFormatDateTime,
  formatDate as sharedFormatDate,
  formatDuration,
  getRelativeTime,

  // 防抖节流
  debounce as sharedDebounce,
  throttle as sharedThrottle,

  // 对象操作
  deepClone as sharedDeepClone,
  generateId,
  unique,
  groupBy,

  // 数据格式化
  formatFileSize,
  formatNumber,
  formatPercentage,
  formatCurrency,
  maskPhone,
  maskEmail,
} from '@shared/utils'

// ========== 导出（保持原有命名） ==========

// 类型检查函数
export {
  is,
  isDef,
  isUndef,
  isNull,
  isWhitespace,
  isObject,
  isArray,
  isString,
  isNumber,
  isBoolean,
  isDate,
  isRegExp,
  isFunction,
  isPromise,
  isNullOrUndef,
  isNullOrWhitespace,
  isEmpty,
  ifNull,
  isUrl,
  isExternal,
  isValidEmail,
  isValidPhone,
}

// 日期时间函数（别名以保持兼容）
export const formatDateTime = sharedFormatDateTime
export const formatDate = sharedFormatDate
export { formatDuration, getRelativeTime }

// 防抖节流（别名以保持兼容）
export const debounce = sharedDebounce
export const throttle = sharedThrottle

// 对象操作
export const deepClone = sharedDeepClone
export { generateId, unique, groupBy }

// 数据格式化
export { formatFileSize, formatNumber, formatPercentage, formatCurrency, maskPhone, maskEmail }

/**
 * 使用说明：
 * 1. 这个文件从 shared 层导入工具函数
 * 2. 保持原有函数名，确保现有代码不受影响
 * 3. 逐步替换原有的 common.js 和 is.js 中的实现
 * 4. 未来可以直接从 '@/utils/shared' 导入
 */
