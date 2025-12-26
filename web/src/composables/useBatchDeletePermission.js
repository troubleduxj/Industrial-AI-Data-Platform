/**
 * 批量删除权限控制组合式函数
 *
 * 提供前端批量删除权限检查和控制功能，包括：
 * - 权限检查
 * - 按钮状态控制
 * - 权限缓存
 * - 与后端权限系统的集成
 *
 * 需求映射：
 * - 需求6.1: 前端权限控制
 * - 需求6.5: 权限一致性
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { systemV2Api } from '@/api/system-v2'

/**
 * 批量删除权限枚举
 */
export const BatchDeletePermissions = {
  API_BATCH_DELETE: 'api:batch_delete',
  DICT_TYPE_BATCH_DELETE: 'dict_type:batch_delete',
  DICT_DATA_BATCH_DELETE: 'dict_data:batch_delete',
  SYSTEM_PARAM_BATCH_DELETE: 'system_param:batch_delete',
  DEPT_BATCH_DELETE: 'dept:batch_delete',
  USER_BATCH_DELETE: 'user:batch_delete',
  ROLE_BATCH_DELETE: 'role:batch_delete',
  MENU_BATCH_DELETE: 'menu:batch_delete',
}

/**
 * 权限条件枚举
 */
export const PermissionConditions = {
  EXCLUDE_SYSTEM_ITEMS: 'exclude_system_items',
  EXCLUDE_REFERENCED_ITEMS: 'exclude_referenced_items',
  ONLY_OWN_ITEMS: 'only_own_items',
  ONLY_DEPT_ITEMS: 'only_dept_items',
}

/**
 * 批量删除权限控制组合式函数
 *
 * @param {string} resourceType - 资源类型
 * @param {Array} conditions - 权限条件列表
 * @returns {Object} 权限控制相关的响应式数据和方法
 */
export function useBatchDeletePermission(resourceType, conditions = []) {
  const userStore = useUserStore()

  // 响应式状态
  const hasPermission = ref(false)
  const isLoading = ref(false)
  const permissionError = ref(null)
  const permissionCache = ref(new Map())

  // 权限键
  const permissionKey = computed(() => `${resourceType}:batch_delete`)

  // 缓存键
  const cacheKey = computed(() => {
    const conditionsStr = conditions.sort().join(',')
    return `${permissionKey.value}:${conditionsStr}`
  })

  /**
   * 检查批量删除权限
   */
  const checkPermission = async () => {
    try {
      isLoading.value = true
      permissionError.value = null

      // 检查缓存
      if (permissionCache.value.has(cacheKey.value)) {
        const cached = permissionCache.value.get(cacheKey.value)
        if (Date.now() - cached.timestamp < 300000) {
          // 5分钟缓存
          hasPermission.value = cached.hasPermission
          return cached.hasPermission
        }
      }

      // 超级管理员直接通过
      if (userStore.userInfo?.is_superuser) {
        hasPermission.value = true
        cachePermissionResult(true)
        return true
      }

      // 调用后端API检查权限
      const result = await checkPermissionFromAPI()
      hasPermission.value = result
      cachePermissionResult(result)

      return result
    } catch (error) {
      console.error('权限检查失败:', error)
      permissionError.value = error.message || '权限检查失败'
      hasPermission.value = false
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 从API检查权限
   */
  const checkPermissionFromAPI = async () => {
    try {
      // 这里可以调用专门的权限检查API
      // 目前通过检查用户角色的API权限来判断
      const userPermissions = await getUserPermissions()

      // 检查是否有对应的批量删除API权限
      const requiredApiPaths = getRequiredApiPaths(resourceType)

      return requiredApiPaths.some((apiPath) =>
        userPermissions.some(
          (permission) => permission.method === 'DELETE' && permission.path === apiPath
        )
      )
    } catch (error) {
      console.error('API权限检查失败:', error)
      return false
    }
  }

  /**
   * 获取用户权限
   */
  const getUserPermissions = async () => {
    try {
      // 从用户信息中获取角色权限
      const roles = userStore.userInfo?.roles || []
      const allPermissions = []

      for (const role of roles) {
        if (role.apis) {
          allPermissions.push(...role.apis)
        }
      }

      return allPermissions
    } catch (error) {
      console.error('获取用户权限失败:', error)
      return []
    }
  }

  /**
   * 获取资源类型对应的API路径
   */
  const getRequiredApiPaths = (resourceType) => {
    const apiPathMapping = {
      api: ['delete/batch'],
      dict_type: ['delete/batch'],
      dict_data: ['delete/batch'],
      system_param: ['delete/batch'],
      dept: ['delete/batch'],
      user: ['delete/batch'],
      role: ['delete/batch'],
      menu: ['delete/batch'],
    }

    return apiPathMapping[resourceType] || []
  }

  /**
   * 缓存权限结果
   */
  const cachePermissionResult = (result) => {
    permissionCache.value.set(cacheKey.value, {
      hasPermission: result,
      timestamp: Date.now(),
    })
  }

  /**
   * 清除权限缓存
   */
  const clearPermissionCache = () => {
    permissionCache.value.clear()
  }

  /**
   * 检查项目级权限
   */
  const checkItemPermission = (item) => {
    if (!hasPermission.value) {
      return { allowed: false, reason: '缺少批量删除权限' }
    }

    // 检查权限条件
    for (const condition of conditions) {
      const conditionResult = checkPermissionCondition(item, condition)
      if (!conditionResult.allowed) {
        return conditionResult
      }
    }

    return { allowed: true, reason: null }
  }

  /**
   * 检查权限条件
   */
  const checkPermissionCondition = (item, condition) => {
    switch (condition) {
      case PermissionConditions.EXCLUDE_SYSTEM_ITEMS:
        if (item.is_system && !userStore.userInfo?.is_superuser) {
          return { allowed: false, reason: '系统内置项不允许删除' }
        }
        break

      case PermissionConditions.EXCLUDE_REFERENCED_ITEMS:
        if (item.is_referenced) {
          return { allowed: false, reason: '该项目被其他资源引用，无法删除' }
        }
        break

      case PermissionConditions.ONLY_OWN_ITEMS:
        if (item.created_by && item.created_by !== userStore.userInfo?.id) {
          return { allowed: false, reason: '只能删除自己创建的项目' }
        }
        break

      case PermissionConditions.ONLY_DEPT_ITEMS:
        if (item.dept_id && item.dept_id !== userStore.userInfo?.dept?.id) {
          return { allowed: false, reason: '只能删除本部门的项目' }
        }
        break
    }

    return { allowed: true, reason: null }
  }

  /**
   * 过滤可删除的项目
   */
  const filterDeletableItems = (items) => {
    const allowedItems = []
    const deniedItems = []

    for (const item of items) {
      const permissionResult = checkItemPermission(item)
      if (permissionResult.allowed) {
        allowedItems.push(item)
      } else {
        deniedItems.push({
          item,
          reason: permissionResult.reason,
        })
      }
    }

    return {
      allowedItems,
      deniedItems,
      allowedCount: allowedItems.length,
      deniedCount: deniedItems.length,
    }
  }

  /**
   * 批量删除按钮是否可用
   */
  const isBatchDeleteEnabled = computed(() => {
    return hasPermission.value && !isLoading.value
  })

  /**
   * 权限提示信息
   */
  const permissionTooltip = computed(() => {
    if (isLoading.value) {
      return '正在检查权限...'
    }

    if (permissionError.value) {
      return `权限检查失败: ${permissionError.value}`
    }

    if (!hasPermission.value) {
      return `缺少批量删除${resourceType}的权限`
    }

    return '可以执行批量删除操作'
  })

  // 监听用户信息变化，重新检查权限
  watch(
    () => userStore.userInfo,
    () => {
      clearPermissionCache()
      checkPermission()
    },
    { deep: true }
  )

  // 组件挂载时检查权限
  onMounted(() => {
    checkPermission()
  })

  return {
    // 状态
    hasPermission,
    isLoading,
    permissionError,
    isBatchDeleteEnabled,
    permissionTooltip,

    // 方法
    checkPermission,
    checkItemPermission,
    filterDeletableItems,
    clearPermissionCache,

    // 工具
    permissionKey,
    cacheKey,
  }
}

/**
 * 预定义的权限控制组合式函数
 */

export function useAPIBatchDeletePermission() {
  return useBatchDeletePermission('api', [PermissionConditions.EXCLUDE_SYSTEM_ITEMS])
}

export function useDictTypeBatchDeletePermission() {
  return useBatchDeletePermission('dict_type', [PermissionConditions.EXCLUDE_SYSTEM_ITEMS])
}

export function useDictDataBatchDeletePermission() {
  return useBatchDeletePermission('dict_data', [PermissionConditions.EXCLUDE_SYSTEM_ITEMS])
}

export function useSystemParamBatchDeletePermission() {
  return useBatchDeletePermission('system_param', [PermissionConditions.EXCLUDE_SYSTEM_ITEMS])
}

export function useDeptBatchDeletePermission() {
  return useBatchDeletePermission('dept', [
    PermissionConditions.EXCLUDE_SYSTEM_ITEMS,
    PermissionConditions.EXCLUDE_REFERENCED_ITEMS,
  ])
}

export function useUserBatchDeletePermission() {
  return useBatchDeletePermission('user', [
    PermissionConditions.EXCLUDE_SYSTEM_ITEMS,
    PermissionConditions.EXCLUDE_REFERENCED_ITEMS,
  ])
}

export function useRoleBatchDeletePermission() {
  return useBatchDeletePermission('role', [
    PermissionConditions.EXCLUDE_SYSTEM_ITEMS,
    PermissionConditions.EXCLUDE_REFERENCED_ITEMS,
  ])
}

export function useMenuBatchDeletePermission() {
  return useBatchDeletePermission('menu', [
    PermissionConditions.EXCLUDE_SYSTEM_ITEMS,
    PermissionConditions.EXCLUDE_REFERENCED_ITEMS,
  ])
}

/**
 * 全局权限检查工具函数
 */
export const BatchDeletePermissionUtils = {
  /**
   * 检查用户是否有特定的批量删除权限
   */
  async hasPermission(resourceType, conditions = []) {
    const { checkPermission } = useBatchDeletePermission(resourceType, conditions)
    return await checkPermission()
  },

  /**
   * 获取用户所有的批量删除权限
   */
  async getAllPermissions() {
    const resourceTypes = [
      'api',
      'dict_type',
      'dict_data',
      'system_param',
      'dept',
      'user',
      'role',
      'menu',
    ]
    const permissions = {}

    for (const resourceType of resourceTypes) {
      const { checkPermission } = useBatchDeletePermission(resourceType)
      permissions[`${resourceType}:batch_delete`] = await checkPermission()
    }

    return permissions
  },

  /**
   * 清除所有权限缓存
   */
  clearAllCache() {
    // 这里可以实现全局缓存清理逻辑
    console.log('清除所有批量删除权限缓存')
  },
}
