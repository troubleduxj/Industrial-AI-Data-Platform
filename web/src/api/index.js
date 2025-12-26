import { request } from '@/utils'
import { requestV2 } from '@/utils/http/v2-interceptors'
import deviceApis, {
  deviceApi as deviceApiV1,
  deviceTypeApi as deviceTypeApiV1,
  deviceDataApi as deviceDataApiV1,
} from './device'
// 导入V2版本的API
import deviceV2Apis, {
  deviceApi as deviceApiV2,
  deviceTypeApi as deviceTypeApiV2,
  deviceDataApi as deviceDataApiV2,
} from './device-v2'
// 导入系统管理V2版本的API
import systemV2Apis from './system-v2'

// 导出具名API模块 (优先使用V2版本)
export const deviceApi = deviceApiV2
export const deviceTypeApi = deviceTypeApiV2
export const deviceDataApi = deviceDataApiV2
export const systemV2Api = systemV2Apis

// V1版本的API作为备用
export { deviceApiV1, deviceTypeApiV1, deviceDataApiV1 }

export default {
  ...deviceApis,
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),

  // dict
  getDictTypeList: (params = {}) => request.get('/system/dict/types', { params }),
  createDictType: (data = {}) => request.post('/system/dict/types', data),
  updateDictType: (data = {}) => request.put(`/system/dict/types/${data.id}`, data),
  deleteDictType: (params = {}) =>
    request.delete(`/system/dict/types/${params.type_id}`, { params }),
  getDictDataList: (params = {}) => request.get('/system/dict/data', { params }),
  createDictData: (data = {}) => request.post('/system/dict/data', data),
  updateDictData: (data = {}) => request.put(`/system/dict/data/${data.id}`, data),
  deleteDictData: (params = {}) =>
    request.delete(`/system/dict/data/${params.data_id}`, { params }),
  getDictDataByTypeCode: (typeCode, params = {}) =>
    request.get(`/system/dict/data/by_code/${typeCode}`, { params }),
  // 为了兼容性，添加getDictDataByType别名
  getDictDataByType: (typeCode, params = {}) =>
    request.get(`/system/dict/data/by_code/${typeCode}`, { params }),

  // config
  getCachedConfig: (paramKey) => request.get(`/system-params/cached/${paramKey}`),
}

export const getCachedConfig = (paramKey) => {
  // 使用v2版本的API
  return requestV2.get(`/system-params/cached/${paramKey}`)
}
export const getDictDataByType = (typeCode, params = {}) =>
  request.get(`/system/dict/data/by_code/${typeCode}`, { params })

export * from './device'
