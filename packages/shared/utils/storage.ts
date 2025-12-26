/**
 * 跨端存储抽象层
 * 定义统一的存储接口，各端实现适配器
 * 源自: web/src/utils/storage/storage.js
 */

/**
 * 存储项结构
 */
export interface StorageItem<T = any> {
  value: T;
  time: number;
  expire: number | null;
}

/**
 * 存储接口（各端需实现）
 */
export interface IStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  clear(): void;
}

/**
 * 存储配置
 */
export interface StorageOptions {
  storage: IStorage;
  prefixKey?: string;
}

/**
 * 跨端存储类
 * Web: 使用 localStorage/sessionStorage
 * NativeScript: 使用 ApplicationSettings
 */
export class Storage {
  private storage: IStorage;
  private prefixKey: string;

  constructor(options: StorageOptions) {
    this.storage = options.storage;
    this.prefixKey = options.prefixKey || '';
  }

  private getKey(key: string): string {
    return `${this.prefixKey}${key}`.toUpperCase();
  }

  /**
   * 设置存储项
   * @param key - 键
   * @param value - 值
   * @param expire - 过期时间（秒）
   */
  set<T = any>(key: string, value: T, expire?: number): void {
    const stringData = JSON.stringify({
      value,
      time: Date.now(),
      expire:
        expire !== undefined && expire !== null
          ? Date.now() + expire * 1000
          : null,
    } as StorageItem<T>);

    this.storage.setItem(this.getKey(key), stringData);
  }

  /**
   * 获取存储项的值
   * @param key - 键
   * @returns 值
   */
  get<T = any>(key: string): T | null {
    const { value } = this.getItem<T>(key, null);
    return value;
  }

  /**
   * 获取存储项（包含时间信息）
   * @param key - 键
   * @param def - 默认值
   * @returns 存储项
   */
  getItem<T = any>(
    key: string,
    def: T | null = null
  ): { value: T | null; time?: number } {
    const val = this.storage.getItem(this.getKey(key));
    if (!val) return { value: def };

    try {
      const data: StorageItem<T> = JSON.parse(val);
      const { value, time, expire } = data;

      // 检查是否过期
      if (expire === null || expire > Date.now()) {
        return { value, time };
      }

      // 已过期，移除
      this.remove(key);
      return { value: def };
    } catch (error) {
      console.warn('存储解析错误:', error);
      this.remove(key);
      return { value: def };
    }
  }

  /**
   * 移除存储项
   * @param key - 键
   */
  remove(key: string): void {
    this.storage.removeItem(this.getKey(key));
  }

  /**
   * 清空所有存储
   */
  clear(): void {
    this.storage.clear();
  }
}

/**
 * 创建存储实例
 * @param options - 配置项
 * @returns Storage 实例
 */
export function createStorage(options: StorageOptions): Storage {
  return new Storage(options);
}

// Web 端工厂函数示例（在 web 项目中使用）
// export function createWebStorage(prefixKey = '', persistent = true) {
//   return createStorage({
//     prefixKey,
//     storage: persistent ? localStorage : sessionStorage,
//   });
// }

// NativeScript 端工厂函数示例（在 mobile 项目中使用）
// import * as ApplicationSettings from '@nativescript/core/application-settings';
// export function createNSStorage(prefixKey = '') {
//   return createStorage({
//     prefixKey,
//     storage: {
//       getItem: ApplicationSettings.getString,
//       setItem: ApplicationSettings.setString,
//       removeItem: ApplicationSettings.remove,
//       clear: ApplicationSettings.clear,
//     },
//   });
// }

