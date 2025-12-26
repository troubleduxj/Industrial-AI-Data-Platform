import { requestV2 as request } from '@/utils/http'

const API_BASE = '/device/maintenance'

/**
 * 设备维护相关API
 */
const deviceMaintenanceApi = {
  /**
   * 获取维修记录列表
   */
  getRepairRecords(params = {}) {
    return request({
      url: `${API_BASE}/repair-records`,
      method: 'GET',
      params,
    })
  },

  /**
   * 获取维修记录详情
   */
  getRepairRecord(id) {
    return request({
      url: `${API_BASE}/repair-records/${id}`,
      method: 'GET',
    })
  },

  /**
   * 创建维修记录
   */
  createRepairRecord(data) {
    return request({
      url: `${API_BASE}/repair-records`,
      method: 'POST',
      data,
    })
  },

  /**
   * 更新维修记录
   */
  updateRepairRecord(id, data) {
    return request({
      url: `${API_BASE}/repair-records/${id}`,
      method: 'PUT',
      data,
    })
  },

  /**
   * 删除维修记录
   */
  deleteRepairRecord(id) {
    return request({
      url: `${API_BASE}/repair-records/${id}`,
      method: 'DELETE',
    })
  },

  /**
   * 批量删除维修记录
   */
  batchDeleteRepairRecords(ids) {
    return request({
      url: `${API_BASE}/repair-records/batch`,
      method: 'DELETE',
      data: { ids },
    })
  },

  /**
   * 获取设备字段配置
   */
  getDeviceFields(deviceType) {
    return request({
      url: `${API_BASE}/device-fields/${deviceType}`,
      method: 'GET',
    })
  },

  /**
   * 更新设备字段配置
   */
  updateDeviceFields(deviceType, data) {
    return request({
      url: `${API_BASE}/device-fields/${deviceType}`,
      method: 'POST',
      data,
    })
  },

  /**
   * 生成维修单号
   */
  generateRepairCode() {
    return request({
      url: `${API_BASE}/repair-codes/generate`,
      method: 'POST',
    })
  },

  /**
   * 获取维修记录统计
   */
  getRepairStatistics(params = {}) {
    return request({
      url: `${API_BASE}/repair-records/statistics`,
      method: 'GET',
      params,
    })
  },

  /**
   * 导出维修记录
   */
  exportRepairRecords(params = {}) {
    return request({
      url: `${API_BASE}/repair-records/export`,
      method: 'GET',
      params,
      responseType: 'blob',
    })
  },

  /**
   * 获取维修记录模板
   */
  getRepairRecordTemplate() {
    return request({
      url: `${API_BASE}/repair-records/template`,
      method: 'GET',
      responseType: 'blob',
    })
  },

  /**
   * 导入维修记录
   */
  importRepairRecords(file) {
    const formData = new FormData()
    formData.append('file', file)

    return request({
      url: `${API_BASE}/repair-records/import`,
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // =====================================================
  // 设备维护看板相关API
  // =====================================================

  /**
   * 获取维护记录列表
   */
  getMaintenanceRecords(params = {}) {
    return request({
      url: `${API_BASE}/records`,
      method: 'GET',
      params,
    })
  },

  /**
   * 获取维护记录详情
   */
  getMaintenanceRecord(id) {
    return request({
      url: `${API_BASE}/records/${id}`,
      method: 'GET',
    })
  },

  /**
   * 创建维护记录
   */
  createMaintenanceRecord(data) {
    return request({
      url: `${API_BASE}/records`,
      method: 'POST',
      data,
    })
  },

  /**
   * 更新维护记录
   */
  updateMaintenanceRecord(id, data) {
    return request({
      url: `${API_BASE}/records/${id}`,
      method: 'PUT',
      data,
    })
  },

  /**
   * 删除维护记录
   */
  deleteMaintenanceRecord(id) {
    return request({
      url: `${API_BASE}/records/${id}`,
      method: 'DELETE',
    })
  },

  /**
   * 获取维护统计信息
   */
  getMaintenanceStatistics(params = {}) {
    return request({
      url: `${API_BASE}/statistics`,
      method: 'GET',
      params,
    })
  },

  /**
   * 获取维护计划列表
   */
  getMaintenancePlans(params = {}) {
    return request({
      url: `${API_BASE}/plans`,
      method: 'GET',
      params,
    })
  },

  /**
   * 获取维护提醒列表
   */
  getMaintenanceReminders(params = {}) {
    return request({
      url: `${API_BASE}/reminders`,
      method: 'GET',
      params,
    })
  },
}

export default deviceMaintenanceApi
