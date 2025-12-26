/**
 * 系统管理模块 API v2
 * 提供用户、角色、菜单、部门管理的v2版本API接口
 */

import { pageApiHelper } from '@/utils/api-v2-migration'
import { createSafeApiCall } from '@/utils/error-handler'
import { requestV2 } from '@/utils/http/v2-interceptors'

// 创建系统管理API实例
const systemApis = pageApiHelper.createSystemApis()

// 创建认证API实例
const authApis = pageApiHelper.createAuthApis()

// 创建带错误处理的API包装函数
function wrapApiWithErrorHandler(apiFunction, options = {}) {
  return createSafeApiCall(apiFunction, {
    rethrow: true, // 允许页面组件处理特定错误
    ...options,
  })
}

// 标准化批量删除API调用函数
function createStandardBatchDeleteApi(resourcePath) {
  return wrapApiWithErrorHandler((ids, options = {}) => {
    // 参数验证
    if (!Array.isArray(ids) || ids.length === 0) {
      throw new Error('ids must be a non-empty array')
    }

    // 验证ID格式
    const validIds = ids.filter((id) => typeof id === 'number' && !isNaN(id) && id > 0)
    if (validIds.length !== ids.length) {
      throw new Error('All ids must be positive numbers')
    }

    // 构建请求数据
    const requestData = { ids: validIds }
    if (options.force !== undefined) {
      requestData.force = options.force
    }

    // 发送请求
    return requestV2.delete(`/${resourcePath}/batch`, { data: requestData })
  })
}

// 用户管理API
export const userApi = {
  // 获取用户列表
  list: wrapApiWithErrorHandler((params = {}) => systemApis.users.list(params)),

  // 获取用户详情
  get: wrapApiWithErrorHandler((id, params = {}) => systemApis.users.get(id, params)),

  // 创建用户
  create: wrapApiWithErrorHandler((data = {}) => systemApis.users.create(data)),

  // 更新用户
  update: wrapApiWithErrorHandler((id, data = {}) => systemApis.users.update(id, data)),

  // 删除用户
  delete: wrapApiWithErrorHandler((id) => systemApis.users.delete(id)),

  // 重置密码
  resetPassword: wrapApiWithErrorHandler((id, data = {}) =>
    systemApis.users.resetPassword({ id }, data)
  ),

  // 获取用户权限
  getPermissions: wrapApiWithErrorHandler((id, params = {}) =>
    systemApis.users.getPermissions({ id }, params)
  ),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => systemApis.users.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => systemApis.users.batchUpdate(items)),
  batchDelete: createStandardBatchDeleteApi('users'),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => systemApis.users.search(params)),
}

// 认证管理API
export const authApi = {
  // 用户登录
  login: wrapApiWithErrorHandler((data = {}) => authApis.login(data)),

  // 获取用户信息
  getUserInfo: wrapApiWithErrorHandler(() => authApis.getUserInfo()),

  // 修改密码
  changePassword: wrapApiWithErrorHandler((data = {}) => authApis.changePassword(data)),

  // 用户登出
  logout: wrapApiWithErrorHandler(() => authApis.logout()),

  // 获取用户API权限
  getUserApis: wrapApiWithErrorHandler(() => authApis.getUserApis()),

  // 获取用户菜单权限
  getUserMenus: wrapApiWithErrorHandler(() => authApis.getUserMenus()),
}

// 角色管理API
export const roleApi = {
  // 获取角色列表
  list: wrapApiWithErrorHandler((params = {}) => systemApis.roles.list(params)),

  // 获取角色详情
  get: wrapApiWithErrorHandler((id, params = {}) => systemApis.roles.get(id, params)),

  // 创建角色
  create: wrapApiWithErrorHandler((data = {}) => systemApis.roles.create(data)),

  // 更新角色
  update: wrapApiWithErrorHandler((id, data = {}) => systemApis.roles.update(id, data)),

  // 删除角色
  delete: wrapApiWithErrorHandler((id) => systemApis.roles.delete(id)),

  // 获取角色权限
  getPermissions: wrapApiWithErrorHandler((id, params = {}) =>
    systemApis.roles.getPermissions(id, params)
  ),

  // 分配权限
  assignPermissions: wrapApiWithErrorHandler((id, data = {}) =>
    systemApis.roles.assignPermissions(id, data)
  ),

  // 获取角色用户
  getUsers: wrapApiWithErrorHandler((id, params = {}) => systemApis.roles.getUsers(id, params)),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => systemApis.roles.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => systemApis.roles.batchUpdate(items)),
  batchDelete: createStandardBatchDeleteApi('roles'),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => systemApis.roles.search(params)),
}

// 菜单管理API
export const menuApi = {
  // 获取菜单列表
  list: wrapApiWithErrorHandler((params = {}) => systemApis.menus.list(params)),

  // 获取菜单详情
  get: wrapApiWithErrorHandler((id, params = {}) => systemApis.menus.get(id, params)),

  // 创建菜单
  create: wrapApiWithErrorHandler((data = {}) => systemApis.menus.create(data)),

  // 更新菜单
  update: wrapApiWithErrorHandler((id, data = {}) => systemApis.menus.update(id, data)),

  // 删除菜单
  delete: wrapApiWithErrorHandler((id) => systemApis.menus.delete(id)),

  // 获取菜单树
  getTree: wrapApiWithErrorHandler((params = {}) => systemApis.menus.getTree(params)),

  // 检查菜单使用情况
  checkUsage: wrapApiWithErrorHandler((id) => requestV2.get(`/menus/${id}/usage`)),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => systemApis.menus.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => systemApis.menus.batchUpdate(items)),
  batchDelete: createStandardBatchDeleteApi('menus'),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => systemApis.menus.search(params)),
}

// 部门管理API
export const departmentApi = {
  // 获取部门列表
  list: wrapApiWithErrorHandler((params = {}) => systemApis.departments.list(params)),

  // 获取部门详情
  get: wrapApiWithErrorHandler((id, params = {}) => systemApis.departments.get(id, params)),

  // 创建部门
  create: wrapApiWithErrorHandler((data = {}) => systemApis.departments.create(data)),

  // 更新部门
  update: wrapApiWithErrorHandler((id, data = {}) => systemApis.departments.update(id, data)),

  // 删除部门
  delete: wrapApiWithErrorHandler((id) => systemApis.departments.delete(id)),

  // 获取部门树
  getTree: wrapApiWithErrorHandler((params = {}) => systemApis.departments.getTree(params)),

  // 批量操作
  batchCreate: wrapApiWithErrorHandler((items) => systemApis.departments.batchCreate(items)),
  batchUpdate: wrapApiWithErrorHandler((items) => systemApis.departments.batchUpdate(items)),
  batchDelete: createStandardBatchDeleteApi('departments'),

  // 高级搜索
  search: wrapApiWithErrorHandler((params) => systemApis.departments.search(params)),
}

// 兼容性API - 保持与v1相同的接口名称
export const compatibilityApi = {
  // 用户管理 - v1兼容接口
  getUserList: wrapApiWithErrorHandler((params = {}) => userApi.list(params)),
  createUser: wrapApiWithErrorHandler((data = {}) => userApi.create(data)),
  updateUser: wrapApiWithErrorHandler((data = {}) => {
    const { id, ...updateData } = data
    return userApi.update(id || data.user_id, updateData)
  }),
  deleteUser: wrapApiWithErrorHandler((params = {}) => userApi.delete(params.user_id || params.id)),
  resetPassword: wrapApiWithErrorHandler((data = {}) =>
    userApi.resetPassword(data.user_id || data.id, data)
  ),

  // 角色管理 - v1兼容接口
  getRoleList: wrapApiWithErrorHandler((params = {}) => roleApi.list(params)),
  createRole: wrapApiWithErrorHandler((data = {}) => roleApi.create(data)),
  updateRole: wrapApiWithErrorHandler((data = {}) => {
    const { id, ...updateData } = data
    return roleApi.update(id || data.role_id, updateData)
  }),
  deleteRole: wrapApiWithErrorHandler((params = {}) => roleApi.delete(params.role_id || params.id)),
  getRoleAuthorized: wrapApiWithErrorHandler((params = {}) => roleApi.getPermissions(params.id)),
  updateRoleAuthorized: wrapApiWithErrorHandler((data = {}) => {
    const { id, ...permissionData } = data
    return roleApi.assignPermissions(id, permissionData)
  }),

  // 菜单管理 - v1兼容接口
  getMenus: wrapApiWithErrorHandler((params = {}) => menuApi.list(params)),
  createMenu: wrapApiWithErrorHandler((data = {}) => menuApi.create(data)),
  updateMenu: wrapApiWithErrorHandler((data = {}) => {
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('菜单更新失败：ID无效', { id, data })
      throw new Error(`菜单ID无效: ${id}`)
    }

    // 保留id字段在updateData中，因为后端MenuUpdate schema需要id字段
    return menuApi.update(id, { id, ...updateData })
  }),
  deleteMenu: wrapApiWithErrorHandler((params = {}) => menuApi.delete(params.id)),
  batchDeleteMenus: createStandardBatchDeleteApi('menus'),

  // 部门管理 - v1兼容接口
  getDepts: wrapApiWithErrorHandler((params = {}) => {
    // 如果指定了view='tree'，使用getTree方法
    if (params?.view === 'tree') {
      return departmentApi.getTree(params)
    }
    return departmentApi.list(params)
  }),
  createDept: wrapApiWithErrorHandler((data = {}) => departmentApi.create(data)),
  updateDept: wrapApiWithErrorHandler((data = {}) => {
    const { id, ...updateData } = data
    return departmentApi.update(id || data.dept_id, updateData)
  }),
  deleteDept: wrapApiWithErrorHandler((params = {}) => {
    const id = params.dept_id || params.id
    const force = params.force || false
    return departmentApi.delete(id, { force })
  }),
  batchDeleteDepts: (deptIds, force = false) =>
    createStandardBatchDeleteApi('departments')(deptIds, { force }),

  // API管理 - 使用真正的v2接口
  getApiList: wrapApiWithErrorHandler((params = {}) => systemApis.apis.list(params)),
  getApis: wrapApiWithErrorHandler((params = {}) => systemApis.apis.list(params)), // v1兼容别名
  createApi: wrapApiWithErrorHandler((data = {}) => systemApis.apis.create(data)),
  updateApi: wrapApiWithErrorHandler((data = {}) => {
    // 修复：与updateMenu保持一致的调用格式，从data对象中提取id
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('API更新失败：ID无效', { id, data })
      throw new Error(`API ID无效: ${id}`)
    }

    return systemApis.apis.update(id, updateData)
  }),
  deleteApi: wrapApiWithErrorHandler((id) => systemApis.apis.delete(id)),
  batchDeleteApis: createStandardBatchDeleteApi('apis'),
  refreshApi: wrapApiWithErrorHandler(() => systemApis.apis.refresh()),

  // 审计日志 - 使用真正的v2接口
  getAuditLogList: wrapApiWithErrorHandler((params = {}) => systemApis.auditLogs.list(params)),

  // 字典类型管理 - 使用真正的v2接口
  getDictTypeList: wrapApiWithErrorHandler((params = {}) => systemApis.dictTypes.list(params)),
  createDictType: wrapApiWithErrorHandler((data = {}) => systemApis.dictTypes.create(data)),
  updateDictType: wrapApiWithErrorHandler((data = {}) => {
    // 修复：与updateMenu保持一致的调用格式，从data对象中提取id
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('字典类型更新失败：ID无效', { id, data })
      throw new Error(`字典类型ID无效: ${id}`)
    }

    return systemApis.dictTypes.update(id, updateData)
  }),
  deleteDictType: wrapApiWithErrorHandler((params) => {
    // 支持直接传入ID或包含type_id的对象
    const id = typeof params === 'object' ? params.type_id || params.id : params
    return systemApis.dictTypes.delete(id)
  }),
  batchDeleteDictTypes: createStandardBatchDeleteApi('dict-types'),

  // 字典数据管理 - 使用真正的v2接口
  getDictDataList: wrapApiWithErrorHandler((params = {}) => systemApis.dictData.list(params)),
  createDictData: wrapApiWithErrorHandler((data = {}) => systemApis.dictData.create(data)),
  updateDictData: wrapApiWithErrorHandler((data = {}) => {
    // 修复：与updateMenu保持一致的调用格式，从data对象中提取id
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('字典数据更新失败：ID无效', { id, data })
      throw new Error(`字典数据ID无效: ${id}`)
    }

    return systemApis.dictData.update(id, updateData)
  }),
  deleteDictData: wrapApiWithErrorHandler((params) => {
    // 支持直接传入ID或包含data_id的对象
    const id = typeof params === 'object' ? params.data_id || params.id : params
    return systemApis.dictData.delete(id)
  }),
  batchDeleteDictData: createStandardBatchDeleteApi('dict-data'),

  // 按字典类型编码获取字典数据 - v2接口
  getDictDataByType: wrapApiWithErrorHandler((typeCode, params = {}) =>
    requestV2.get(`/dict-data/by-type/${typeCode}`, { params })
  ),

  // 系统参数管理 - 使用真正的v2接口
  getSystemParamList: wrapApiWithErrorHandler(async (params = {}) => {
    const response = await systemApis.systemParams.list(params)
    // 适配CrudTable期望的数据格式：{data: Array, total: Number}
    // 后端返回格式：{data: {items: Array, total: Number}}
    if (response && response.data && response.data.items) {
      return {
        data: response.data.items,
        total: response.data.total || 0,
        // 保留其他可能的字段
        ...response,
      }
    }
    return response
  }),
  getSystemConfigByKey: wrapApiWithErrorHandler((key, params = {}) =>
    requestV2.get(`/system-params/cached/${key}`, { params })
  ),
  createSystemParam: wrapApiWithErrorHandler((data = {}) => systemApis.systemParams.create(data)),
  updateSystemParam: wrapApiWithErrorHandler((data = {}) => {
    // 修复：与updateMenu保持一致的调用格式，从data对象中提取id
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('系统参数更新失败：ID无效', { id, data })
      throw new Error(`系统参数ID无效: ${id}`)
    }

    return systemApis.systemParams.update(id, updateData)
  }),
  deleteSystemParam: wrapApiWithErrorHandler((params) => {
    // 支持直接传入ID或包含param_id/config_id的对象
    const id =
      typeof params === 'object' ? params.param_id || params.config_id || params.id : params
    return systemApis.systemParams.delete(id)
  }),
  batchDeleteSystemParams: createStandardBatchDeleteApi('system-params'),

  // API分组管理 - 使用真正的v2接口
  getApiGroupList: wrapApiWithErrorHandler((params = {}) => systemApis.apiGroups.list(params)),
  getAllApiGroups: wrapApiWithErrorHandler(() => systemApis.apiGroups.all()),
  createApiGroup: wrapApiWithErrorHandler((data = {}) => systemApis.apiGroups.create(data)),
  updateApiGroup: wrapApiWithErrorHandler((data = {}) => {
    // 修复：与updateMenu保持一致的调用格式，从data对象中提取id
    const { id, ...updateData } = data

    // 验证ID是否存在且有效
    if (!id || isNaN(id) || id <= 0) {
      console.error('API分组更新失败：ID无效', { id, data })
      throw new Error(`API分组ID无效: ${id}`)
    }

    return systemApis.apiGroups.update(id, updateData)
  }),
  deleteApiGroup: wrapApiWithErrorHandler((id) => systemApis.apiGroups.delete(id)),
  batchDeleteApiGroups: createStandardBatchDeleteApi('api-groups'),
  moveApisToGroup: wrapApiWithErrorHandler((groupId, apiIds) =>
    systemApis.apiGroups.moveApis(groupId, apiIds)
  ),
}

// 系统API导出 - 包含所有兼容性接口
export const systemApi = {
  ...compatibilityApi,
}

// systemV2Api导出 - 包含字典数据等系统API
export const systemV2Api = {
  // 菜单管理API
  menuApi,

  // 字典数据管理
  getDictDataByType: wrapApiWithErrorHandler((typeCode, params = {}) =>
    requestV2.get(`/dict-data/by-type/${typeCode}`, { params })
  ),

  // 其他系统API可以在这里添加
  ...compatibilityApi,
}

// 默认导出
export default {
  users: userApi,
  roles: roleApi,
  menus: menuApi,
  departments: departmentApi,

  // v1兼容性接口
  ...compatibilityApi,
}
