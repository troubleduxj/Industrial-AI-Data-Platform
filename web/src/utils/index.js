/**
 * Web 端工具函数统一导出
 *
 * 优先级：
 * 1. Shared 层工具（跨端通用）
 * 2. Web 端特定工具（依赖 Browser API）
 */

// ========== 跨端通用工具（来自 Shared 层） ==========
export * from './common' // 已集成 shared-compat

// ========== Web 端特定工具 ==========
export * from './storage'
export * from './http'
export * from './auth'
// format.js 已删除，功能由 Shared 层的 shared-compat 提供

// ========== 推荐：直接使用 Shared 工具 ==========
// 新代码建议直接从 '@/utils/shared' 导入：
// import { formatDate, isValidEmail, debounce } from '@/utils/shared'

// ========== 推荐：直接使用 Shared API ==========
// 新代码建议直接从 '@/api/shared' 导入：
// import sharedApi from '@/api/shared'
