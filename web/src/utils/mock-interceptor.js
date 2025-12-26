/**
 * Mock数据拦截器
 * 拦截API请求并返回Mock数据
 */

let mockRules = []
// Mock功能默认禁用，需要手动开启
// 从localStorage读取状态
const savedMockState = localStorage.getItem('mock_enabled')
let mockEnabled = savedMockState === 'true'

console.log('[Mock拦截器] 初始化状态:', mockEnabled ? '已启用' : '已禁用')

/**
 * 从服务器加载Mock规则
 */
export async function loadMockRules() {
  try {
    const response = await fetch('/api/v2/mock-data/active/list')
    const result = await response.json()
    
    if (result.code === 200) {
      mockRules = result.data || []
      console.log(`[Mock拦截器] 加载了 ${mockRules.length} 条Mock规则`)
      return mockRules
    }
  } catch (error) {
    console.error('[Mock拦截器] 加载Mock规则失败:', error)
  }
  return []
}

/**
 * 启用Mock
 */
export function enableMock() {
  mockEnabled = true
  console.log('[Mock拦截器] Mock已启用')
  // 保存到localStorage
  localStorage.setItem('mock_enabled', 'true')
}

/**
 * 禁用Mock
 */
export function disableMock() {
  mockEnabled = false
  console.log('[Mock拦截器] Mock已禁用')
  // 保存到localStorage
  localStorage.setItem('mock_enabled', 'false')
}

/**
 * 检查Mock是否启用
 */
export function isMockEnabled() {
  // 从localStorage读取状态
  const saved = localStorage.getItem('mock_enabled')
  if (saved !== null) {
    mockEnabled = saved === 'true'
  }
  return mockEnabled
}

/**
 * 切换Mock状态
 */
export function toggleMock() {
  if (mockEnabled) {
    disableMock()
  } else {
    enableMock()
  }
  return mockEnabled
}

/**
 * 匹配URL模式
 * 支持通配符 * 和 ** 以及正则表达式
 */
function matchUrlPattern(url, pattern) {
  // 移除查询参数和URL开头的/api/v2（如果存在）
  let urlPath = url.split('?')[0]
  
  // 规范化URL路径
  if (urlPath.startsWith('/api/v2')) {
    urlPath = urlPath // 保持完整路径
  } else if (!urlPath.startsWith('/')) {
    urlPath = '/' + urlPath // 确保以/开头
  }
  
  try {
    // 将pattern转换为正则表达式
    // 支持两种格式：
    // 1. 简单通配符：/api/v2/devices/*
    // 2. 正则表达式：/api/v2/devices/100[1-5]$
    
    let regexPattern = pattern
    
    // 如果pattern已经包含正则特殊字符（除了*），直接作为正则使用
    if (/[\[\]\(\)\{\}\^\$\+\?]/.test(pattern)) {
      // 确保正则完整匹配
      if (!pattern.startsWith('^')) {
        regexPattern = '^' + regexPattern
      }
      if (!pattern.endsWith('$') && !pattern.includes('.*')) {
        regexPattern = regexPattern + '$'
      }
    } else {
      // 简单通配符模式
      regexPattern = pattern
        .replace(/\*\*/g, '___DOUBLE_STAR___')  // 临时标记
        .replace(/\*/g, '[^/]*')  // * 匹配除/外的任意字符
        .replace(/___DOUBLE_STAR___/g, '.*')  // ** 匹配任意字符
        .replace(/\//g, '\\/')    // 转义/
        .replace(/\./g, '\\.')    // 转义.
      
      regexPattern = '^' + regexPattern + '$'
    }
    
    const regex = new RegExp(regexPattern)
    const matched = regex.test(urlPath)
    
    if (matched) {
      console.log('[Mock拦截器] URL匹配成功:', {
        url: urlPath,
        pattern,
        regex: regexPattern
      })
    }
    
    return matched
  } catch (error) {
    console.error('[Mock拦截器] URL匹配错误:', { url: urlPath, pattern, error })
    return false
  }
}

/**
 * 查找匹配的Mock规则
 */
function findMatchingRule(method, url) {
  if (!mockEnabled || !mockRules || mockRules.length === 0) {
    return null
  }
  
  // 按优先级排序（loadMockRules已经按优先级排序，这里再确保一次）
  const sortedRules = [...mockRules].sort((a, b) => (b.priority || 0) - (a.priority || 0))
  
  for (const rule of sortedRules) {
    if (rule.method === method && matchUrlPattern(url, rule.url_pattern)) {
      return rule
    }
  }
  
  return null
}

/**
 * 记录Mock命中
 */
async function recordMockHit(mockId) {
  try {
    await fetch(`/api/v2/mock-data/${mockId}/hit`, {
      method: 'POST'
    })
  } catch (error) {
    // 静默失败，不影响Mock功能
  }
}

/**
 * 创建Mock响应
 */
function createMockResponse(rule) {
  return new Promise((resolve) => {
    const delay = rule.delay || 0
    
    setTimeout(() => {
      // 记录命中
      if (rule.id) {
        recordMockHit(rule.id)
      }
      
      console.log('[Mock拦截器] 命中规则:', {
        id: rule.id,
        method: rule.method,
        url_pattern: rule.url_pattern,
        response_code: rule.response_code
      })
      
      resolve({
        status: rule.response_code,
        data: rule.response_data,
        headers: {
          'content-type': 'application/json',
          'x-mock-match': 'true'
        }
      })
    }, delay)
  })
}

/**
 * Axios请求拦截器
 * 在发送请求前拦截并返回Mock数据
 */
export function mockRequestInterceptor(config) {
  if (!isMockEnabled()) {
    return config
  }
  
  const method = (config.method || 'GET').toUpperCase()
  const url = config.url || ''
  
  const matchedRule = findMatchingRule(method, url)
  
  if (matchedRule) {
    console.log('[Mock拦截器] 拦截请求:', {
      method,
      url,
      ruleName: matchedRule.name,
      ruleId: matchedRule.id
    })
    
    // 标记为Mock请求
    config._isMockRequest = true
    config._mockRule = matchedRule
  } else {
    // 未匹配到规则，正常请求
    // console.log('[Mock拦截器] 未匹配规则，正常请求:', { method, url })
  }
  
  return config
}

/**
 * Axios响应拦截器（适配器）
 * 如果是Mock请求，返回Mock响应
 */
export function mockResponseAdapter(config) {
  if (config._isMockRequest && config._mockRule) {
    return createMockResponse(config._mockRule)
  }
  
  // 不是Mock请求，返回null让axios继续正常请求
  return null
}

/**
 * 获取当前Mock规则
 */
export function getMockRules() {
  return mockRules
}

/**
 * 获取Mock统计信息
 */
export function getMockStats() {
  return {
    enabled: mockEnabled,
    rulesCount: mockRules.length,
    rules: mockRules.map(r => ({
      id: r.id,
      name: r.name,
      method: r.method,
      url_pattern: r.url_pattern,
      priority: r.priority
    }))
  }
}

/**
 * 初始化Mock拦截器
 */
export async function initMockInterceptor() {
  // 检查localStorage中的状态
  const saved = localStorage.getItem('mock_enabled')
  if (saved === 'true') {
    mockEnabled = true
  }
  
  // 加载Mock规则
  await loadMockRules()
  
  console.log('[Mock拦截器] 初始化完成', {
    enabled: mockEnabled,
    rulesCount: mockRules.length
  })
}

// 提供全局访问（用于调试）
if (typeof window !== 'undefined') {
  window.__mockInterceptor = {
    enable: enableMock,
    disable: disableMock,
    toggle: toggleMock,
    isEnabled: isMockEnabled,
    getRules: getMockRules,
    getStats: getMockStats,
    reload: loadMockRules
  }
  
  console.log('[Mock拦截器] 已挂载到 window.__mockInterceptor')
  console.log('使用方法:')
  console.log('  window.__mockInterceptor.enable()  - 启用Mock')
  console.log('  window.__mockInterceptor.disable() - 禁用Mock')
  console.log('  window.__mockInterceptor.toggle()  - 切换Mock状态')
  console.log('  window.__mockInterceptor.getStats() - 查看Mock统计')
  console.log('  window.__mockInterceptor.reload()  - 重新加载规则')
}

export default {
  loadMockRules,
  enableMock,
  disableMock,
  isMockEnabled,
  toggleMock,
  getMockRules,
  getMockStats,
  mockRequestInterceptor,
  mockResponseAdapter,
  initMockInterceptor
}

