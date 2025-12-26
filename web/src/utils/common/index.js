// 优先从 Shared 兼容层导出（跨端工具函数）
export * from './shared-compat'

// 保留 Web 端特定的工具（依赖 DOM/Browser API）
export * from './icon'
export * from './offlineIcons'
export * from './naiveTools'
export * from './useResize'

// 注意：common.js 和 is.js 的功能已由 shared-compat 提供
// 如果需要使用原有实现，请显式导入：
// import { xxx } from './common'  // 旧实现
// import { xxx } from './is'      // 旧实现
