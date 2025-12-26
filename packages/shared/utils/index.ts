/**
 * 工具函数集合（跨端通用，无 UI/DOM 依赖）
 * 统一导出所有工具模块
 */

// ========== 从 web 项目抽取的工具模块 ==========
// 类型检查与验证
export * from './validators';

// 日期时间处理
export * from './datetime';

// 数据格式化
export * from './format';

// 通用辅助函数（防抖、节流、深克隆等）
export * from './helpers';

// 存储抽象
export * from './storage';

// ========== 原有工具函数（保留向后兼容） ==========
export function isNil(value: unknown): value is null | undefined {
  return value === null || value === undefined;
}

export function clamp(num: number, min: number, max: number): number {
  return Math.min(Math.max(num, min), max);
}

export function toISODateTime(d: Date = new Date()): string {
  return d.toISOString();
}

export function safeParseJSON<T = unknown>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function pick<T extends object, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  const out = {} as Pick<T, K>;
  for (const k of keys) {
    if (k in obj) out[k] = obj[k];
  }
  return out;
}

export function omit<T extends object, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> {
  const set = new Set<keyof T>(keys);
  const out: Partial<T> = {};
  for (const key in obj) {
    if (!set.has(key)) (out as any)[key] = obj[key];
  }
  return out as Omit<T, K>;
}


