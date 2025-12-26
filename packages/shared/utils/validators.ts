/**
 * 类型检查与验证工具
 * 跨端通用，无 DOM/Browser 依赖
 * 源自: web/src/utils/common/is.js
 */

const toString = Object.prototype.toString;

export function is(val: unknown, type: string): boolean {
  return toString.call(val) === `[object ${type}]`;
}

export function isDef<T = any>(val?: T): val is T {
  return typeof val !== 'undefined';
}

export function isUndef(val?: unknown): val is undefined {
  return typeof val === 'undefined';
}

export function isNull(val: unknown): val is null {
  return val === null;
}

export function isWhitespace(val: unknown): boolean {
  return val === '';
}

export function isObject(val: any): val is Record<any, any> {
  return !isNull(val) && is(val, 'Object');
}

export function isArray(val: any): val is any[] {
  return val && Array.isArray(val);
}

export function isString(val: unknown): val is string {
  return is(val, 'String');
}

export function isNumber(val: unknown): val is number {
  return is(val, 'Number');
}

export function isBoolean(val: unknown): val is boolean {
  return is(val, 'Boolean');
}

export function isDate(val: unknown): val is Date {
  return is(val, 'Date');
}

export function isRegExp(val: unknown): val is RegExp {
  return is(val, 'RegExp');
}

export function isFunction(val: unknown): val is Function {
  return typeof val === 'function';
}

export function isPromise<T = any>(val: unknown): val is Promise<T> {
  return (
    is(val, 'Promise') &&
    isObject(val) &&
    isFunction(val.then) &&
    isFunction(val.catch)
  );
}

export function isNullOrUndef(val: unknown): val is null | undefined {
  return isNull(val) || isUndef(val);
}

export function isNullOrWhitespace(val: unknown): boolean {
  return isNullOrUndef(val) || isWhitespace(val);
}

/** 空数组 | 空字符串 | 空对象 | 空Map | 空Set */
export function isEmpty(val: unknown): boolean {
  if (isArray(val) || isString(val)) {
    return val.length === 0;
  }

  if (val instanceof Map || val instanceof Set) {
    return val.size === 0;
  }

  if (isObject(val)) {
    return Object.keys(val).length === 0;
  }

  return false;
}

/**
 * 类似 mysql 的 IFNULL 函数
 * 第一个参数为 null/undefined/'' 则返回第二个参数作为备用值，否则返回第一个参数
 */
export function ifNull<T>(val: T, def: T): T;
export function ifNull(val: any, def = ''): any {
  return isNullOrWhitespace(val) ? def : val;
}

export function isUrl(path: string): boolean {
  const reg =
    /(((^https?:(?:\/\/)?)(?:[-;:&=+$,\w]+@)?[A-Za-z0-9.-]+(?::\d+)?|(?:www.|[-;:&=+$,\w]+@)[A-Za-z0-9.-]+)((?:\/[+~%/.\w-_]*)?\??(?:[-+=&;%@.\w_]*)#?(?:[\w]*))?)$/;
  return reg.test(path);
}

/**
 * 检测是否为外部链接
 */
export function isExternal(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path);
}

/**
 * 环境检测（仅检测 global 对象）
 * 注意：NativeScript 中也有 global 对象，不要依赖 window
 */
export const isServer = typeof window === 'undefined';
export const isClient = !isServer;

/**
 * Email 格式验证
 */
export function isValidEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * 手机号验证（中国大陆）
 */
export function isValidPhone(phone: string): boolean {
  const re = /^1[3-9]\d{9}$/;
  return re.test(phone);
}

