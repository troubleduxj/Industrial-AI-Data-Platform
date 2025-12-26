/**
 * 日期时间处理工具
 * 跨端通用，不依赖 dayjs（移动端可按需引入）
 * 源自: web/src/utils/common/common.js + web/src/utils/format.js
 */

/**
 * 格式化日期时间（原生实现，无第三方依赖）
 * @param date - Date 对象、时间戳或字符串
 * @param format - 格式化模式（支持 YYYY, MM, DD, HH, mm, ss）
 * @returns 格式化后的字符串
 */
export function formatDateTime(
  date?: Date | string | number | null,
  format = 'YYYY-MM-DD HH:mm:ss'
): string {
  if (!date || date === null || date === undefined || date === '') {
    return '-';
  }

  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) {
      return '-';
    }

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  } catch (error) {
    console.warn('时间格式化错误:', error, '原始时间:', date);
    return '-';
  }
}

/**
 * 格式化日期（仅日期部分）
 */
export function formatDate(
  date?: Date | string | number | null,
  format = 'YYYY-MM-DD'
): string {
  return formatDateTime(date, format);
}

/**
 * 格式化时长（秒转可读格式）
 * @param seconds - 秒数
 * @returns 格式化后的时长字符串
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0秒';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`;
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`;
  } else {
    return `${secs}秒`;
  }
}

/**
 * 获取相对时间描述
 * @param date - 时间
 * @returns 相对时间字符串（如"刚刚"、"3分钟前"）
 */
export function getRelativeTime(date: Date | string | number): string {
  const now = Date.now();
  const target = new Date(date).getTime();
  const diff = now - target;

  if (diff < 0) return '未来';
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  if (diff < 2592000000) return `${Math.floor(diff / 86400000)}天前`;
  if (diff < 31536000000) return `${Math.floor(diff / 2592000000)}个月前`;
  return `${Math.floor(diff / 31536000000)}年前`;
}

/**
 * 解析日期范围
 * @param range - 预设范围（today, week, month, year）
 * @returns [startDate, endDate]
 */
export function parseDateRange(range: string): [Date, Date] {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);

  const end = new Date(now);
  end.setHours(23, 59, 59, 999);

  switch (range) {
    case 'today':
      return [start, end];
    case 'week':
      start.setDate(now.getDate() - 7);
      return [start, end];
    case 'month':
      start.setMonth(now.getMonth() - 1);
      return [start, end];
    case 'year':
      start.setFullYear(now.getFullYear() - 1);
      return [start, end];
    default:
      return [start, end];
  }
}

