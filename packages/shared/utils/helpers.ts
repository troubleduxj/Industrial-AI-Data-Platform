/**
 * 通用辅助工具函数
 * 跨端通用，无外部依赖
 * 源自: web/src/utils/common/common.js
 */

/**
 * 函数防抖
 * @param method - 要执行的函数
 * @param wait - 等待时间（毫秒）
 * @param immediate - 是否立即执行
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(
  method: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function (this: any, ...args: Parameters<T>) {
    const context = this;

    if (timeout) {
      clearTimeout(timeout);
    }

    // 立即执行需要两个条件：一是 immediate 为 true，二是 timeout 未被赋值或被置为 null
    if (immediate) {
      const callNow = !timeout;
      timeout = setTimeout(() => {
        timeout = null;
      }, wait);
      if (callNow) {
        method.apply(context, args);
      }
    } else {
      // 如果 immediate 为 false，则函数 wait 毫秒后执行
      timeout = setTimeout(() => {
        method.apply(context, args);
      }, wait);
    }
  };
}

/**
 * 函数节流
 * @param fn - 要执行的函数
 * @param wait - 等待时间（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => void {
  let previous = 0;
  let context: any;
  let args: any;

  return function (this: any, ...funcArgs: Parameters<T>) {
    const now = Date.now();
    context = this;
    args = funcArgs;

    if (now - previous > wait) {
      fn.apply(context, args);
      previous = now;
    }
  };
}

/**
 * 深度克隆对象
 * @param obj - 要克隆的对象
 * @returns 克隆后的对象
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (obj instanceof Array) {
    const cloneArr: any[] = [];
    obj.forEach((item) => {
      cloneArr.push(deepClone(item));
    });
    return cloneArr as any;
  }

  if (obj instanceof Object) {
    const cloneObj: any = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloneObj[key] = deepClone(obj[key]);
      }
    }
    return cloneObj;
  }

  return obj;
}

/**
 * 生成唯一 ID
 * @param prefix - 前缀
 * @returns 唯一 ID 字符串
 */
export function generateId(prefix = 'id'): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 延迟执行
 * @param ms - 延迟时间（毫秒）
 * @returns Promise
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 数组去重
 * @param arr - 原数组
 * @param key - 对象数组时的唯一键
 * @returns 去重后的数组
 */
export function unique<T>(arr: T[], key?: keyof T): T[] {
  if (!key) {
    return Array.from(new Set(arr));
  }

  const map = new Map<any, T>();
  arr.forEach((item) => {
    const k = item[key];
    if (!map.has(k)) {
      map.set(k, item);
    }
  });
  return Array.from(map.values());
}

/**
 * 数组分组
 * @param arr - 原数组
 * @param key - 分组键
 * @returns 分组后的对象
 */
export function groupBy<T>(arr: T[], key: keyof T): Record<string, T[]> {
  return arr.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * 数组分页
 * @param arr - 原数组
 * @param page - 页码（从 1 开始）
 * @param pageSize - 每页大小
 * @returns 分页后的数组
 */
export function paginate<T>(arr: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize;
  return arr.slice(start, start + pageSize);
}

/**
 * 树结构扁平化
 * @param tree - 树形数据
 * @param childrenKey - 子节点键名
 * @returns 扁平化后的数组
 */
export function flattenTree<T extends Record<string, any>>(
  tree: T[],
  childrenKey = 'children'
): T[] {
  const result: T[] = [];

  function flatten(nodes: T[]) {
    nodes.forEach((node) => {
      result.push(node);
      if (node[childrenKey] && Array.isArray(node[childrenKey])) {
        flatten(node[childrenKey]);
      }
    });
  }

  flatten(tree);
  return result;
}

/**
 * 扁平数据转树形结构
 * @param list - 扁平数组
 * @param options - 配置项
 * @returns 树形数据
 */
export function listToTree<T extends Record<string, any>>(
  list: T[],
  options: {
    idKey?: string;
    parentKey?: string;
    childrenKey?: string;
    rootValue?: any;
  } = {}
): T[] {
  const {
    idKey = 'id',
    parentKey = 'parentId',
    childrenKey = 'children',
    rootValue = null,
  } = options;

  const map = new Map<any, T>();
  const result: T[] = [];

  // 先建立映射
  list.forEach((item) => {
    map.set(item[idKey], { ...item, [childrenKey]: [] });
  });

  // 建立父子关系
  list.forEach((item) => {
    const node = map.get(item[idKey]);
    const parentId = item[parentKey];

    if (parentId === rootValue || !map.has(parentId)) {
      result.push(node!);
    } else {
      const parent = map.get(parentId);
      if (parent) {
        parent[childrenKey].push(node!);
      }
    }
  });

  return result;
}

/**
 * 重试函数
 * @param fn - 要执行的函数
 * @param retries - 重试次数
 * @param delay - 重试延迟（毫秒）
 * @returns Promise
 */
export async function retry<T>(
  fn: () => Promise<T>,
  retries = 3,
  delay = 1000
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries <= 0) {
      throw error;
    }
    await sleep(delay);
    return retry(fn, retries - 1, delay);
  }
}

