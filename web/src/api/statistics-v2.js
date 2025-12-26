/**
 * 统计报表 v2 API
 */
import { requestV2 } from '@/utils/http/v2-interceptors'

const statisticsV2Api = {
  // 焊接日报相关API
  getWeldingDailyReportSummary: (params) => {
    return requestV2({
      url: '/devices/statistics/daily-report/summary',
      method: 'GET',
      params,
    })
  },

  getWeldingDailyReportDetail: (params) => {
    return requestV2({
      url: '/devices/statistics/daily-report/detail',
      method: 'GET',
      params,
    })
  },

  // 在线率统计API
  getOnlineRateStatistics: (params) => {
    return requestV2({
      url: '/statistics/online-rate',
      method: 'GET',
      params,
    })
  },

  // 焊接记录API
  getWeldingRecords: (params) => {
    return requestV2({
      url: '/statistics/welding-records',
      method: 'GET',
      params,
    })
  },

  // 焊接时长统计API
  getWeldingTimeStatistics: (params) => {
    return requestV2({
      url: '/statistics/welding-time',
      method: 'GET',
      params,
    })
  },

  // 导出报告API
  exportReport: (type, params) => {
    return requestV2({
      url: `/statistics/export/${type}`,
      method: 'POST',
      data: params,
      responseType: 'blob',
    })
  },
}

export default statisticsV2Api
