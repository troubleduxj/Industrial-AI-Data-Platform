/**
 * 组件扫描工具
 * 用于分析和统计项目中的组件使用情况
 */

/**
 * 生成组件数据
 * @param {Array} components - 组件列表
 * @returns {Object} 组件数据统计
 */
export function generateComponentData(components = []) {
  const data = {
    total: components.length,
    categories: {},
    usage: {},
    dependencies: {},
  }

  components.forEach((component) => {
    // 按类别分组
    const category = component.category || 'common'
    if (!data.categories[category]) {
      data.categories[category] = []
    }
    data.categories[category].push(component)

    // 使用统计
    data.usage[component.name] = component.usage || 0

    // 依赖关系
    if (component.dependencies) {
      data.dependencies[component.name] = component.dependencies
    }
  })

  return data
}

/**
 * 获取组件统计信息
 * @param {Array} components - 组件列表
 * @returns {Object} 统计信息
 */
export function getComponentStats(components = []) {
  const stats = {
    total: components.length,
    byCategory: {},
    byUsage: {
      high: 0,
      medium: 0,
      low: 0,
      unused: 0,
    },
    mostUsed: null,
    leastUsed: null,
  }

  let maxUsage = 0
  let minUsage = Infinity

  components.forEach((component) => {
    // 按类别统计
    const category = component.category || 'common'
    stats.byCategory[category] = (stats.byCategory[category] || 0) + 1

    // 按使用频率统计
    const usage = component.usage || 0
    if (usage === 0) {
      stats.byUsage.unused++
    } else if (usage >= 10) {
      stats.byUsage.high++
    } else if (usage >= 5) {
      stats.byUsage.medium++
    } else {
      stats.byUsage.low++
    }

    // 最多使用和最少使用
    if (usage > maxUsage) {
      maxUsage = usage
      stats.mostUsed = component
    }
    if (usage < minUsage && usage > 0) {
      minUsage = usage
      stats.leastUsed = component
    }
  })

  return stats
}

/**
 * 扫描组件文件
 * @param {string} directory - 目录路径
 * @returns {Promise<Array>} 组件列表
 */
export async function scanComponents(directory) {
  // 这里应该实现实际的文件扫描逻辑
  // 由于是前端环境，这里返回模拟数据
  return [
    {
      name: 'Button',
      category: 'common',
      usage: 15,
      path: '/components/common/Button.vue',
    },
    {
      name: 'Table',
      category: 'data',
      usage: 8,
      path: '/components/table/Table.vue',
    },
  ]
}

export default {
  generateComponentData,
  getComponentStats,
  scanComponents,
}
