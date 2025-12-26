/**
 * 数据格式化工具
 * 跨端通用，无外部依赖
 * 源自: web/src/utils/format.js
 */

/**
 * 格式化文件大小
 * @param size - 文件大小（字节）
 * @returns 格式化后的文件大小
 */
export function formatFileSize(size: number): string {
  if (!size || size === 0) return '0 B';
  if (typeof size !== 'number') return '未知';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let index = 0;
  let fileSize = size;

  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024;
    index++;
  }

  return `${fileSize.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

/**
 * 格式化数字
 * @param num - 数字
 * @param decimals - 小数位数
 * @returns 格式化后的数字
 */
export function formatNumber(num: number, decimals = 2): string {
  if (typeof num !== 'number') return '0';
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
}

/**
 * 格式化百分比
 * @param value - 数值
 * @param total - 总数
 * @param decimals - 小数位数
 * @returns 格式化后的百分比
 */
export function formatPercentage(
  value: number,
  total: number,
  decimals = 1
): string {
  if (!total || total === 0) return '0%';
  const percentage = (value / total) * 100;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * 格式化货币
 * @param amount - 金额
 * @param currency - 货币符号
 * @returns 格式化后的货币字符串
 */
export function formatCurrency(amount: number, currency = '¥'): string {
  if (typeof amount !== 'number') return `${currency}0.00`;
  return `${currency}${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * 格式化数字为紧凑形式（1K, 1M, 1B）
 * @param num - 数字
 * @param decimals - 小数位数
 * @returns 紧凑格式字符串
 */
export function formatCompactNumber(num: number, decimals = 1): string {
  if (typeof num !== 'number') return '0';

  const units = [
    { value: 1e9, symbol: 'B' },
    { value: 1e6, symbol: 'M' },
    { value: 1e3, symbol: 'K' },
  ];

  for (const unit of units) {
    if (Math.abs(num) >= unit.value) {
      return `${(num / unit.value).toFixed(decimals)}${unit.symbol}`;
    }
  }

  return num.toString();
}

/**
 * 数字补零
 * @param num - 数字
 * @param length - 总长度
 * @returns 补零后的字符串
 */
export function padZero(num: number, length = 2): string {
  return String(num).padStart(length, '0');
}

/**
 * 隐藏手机号中间四位
 * @param phone - 手机号
 * @returns 隐藏后的手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone;
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
}

/**
 * 隐藏身份证号部分信息
 * @param idCard - 身份证号
 * @returns 隐藏后的身份证号
 */
export function maskIdCard(idCard: string): string {
  if (!idCard || idCard.length < 8) return idCard;
  return idCard.replace(/(\d{6})\d+(\d{4})/, '$1********$2');
}

/**
 * 隐藏邮箱部分信息
 * @param email - 邮箱
 * @returns 隐藏后的邮箱
 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email;
  const [local, domain] = email.split('@');
  const visibleLength = Math.min(3, Math.floor(local.length / 2));
  const masked = local.slice(0, visibleLength) + '***';
  return `${masked}@${domain}`;
}

