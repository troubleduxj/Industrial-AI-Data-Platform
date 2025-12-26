/**
 * Web 端接入 Shared Utils 层
 * 统一使用跨端工具函数
 */

// 从 shared 层导出所有工具函数
export {
  // 类型检查与验证
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
  isServer,
  isClient,
  isValidEmail,
  isValidPhone,
  
  // 日期时间处理
  formatDateTime,
  formatDate,
  formatDuration,
  getRelativeTime,
  parseDateRange,
  
  // 数据格式化
  formatFileSize,
  formatNumber,
  formatPercentage,
  formatCurrency,
  formatCompactNumber,
  padZero,
  maskPhone,
  maskIdCard,
  maskEmail,
  
  // 通用辅助函数
  debounce,
  throttle,
  deepClone,
  generateId,
  sleep,
  unique,
  groupBy,
  paginate,
  flattenTree,
  listToTree,
  retry,
  
  // 存储抽象
  Storage,
  createStorage,
  
  // 原有工具函数
  isNil,
  clamp,
  toISODateTime,
  safeParseJSON,
  pick,
  omit,
} from '@shared/utils';

// 导出类型
export type {
  StorageItem,
  IStorage,
  StorageOptions,
} from '@shared/utils/storage';

/**
 * 使用示例：
 * 
 * ```typescript
 * import { formatDate, isValidEmail, debounce } from '@/utils/shared';
 * 
 * // 日期格式化
 * const dateStr = formatDate(new Date());
 * 
 * // Email 验证
 * if (isValidEmail(email)) {
 *   // ...
 * }
 * 
 * // 防抖函数
 * const debouncedSearch = debounce((keyword: string) => {
 *   console.log('搜索:', keyword);
 * }, 300);
 * ```
 */

