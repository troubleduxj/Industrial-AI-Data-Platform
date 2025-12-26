import axios from 'axios'
import { resReject, resResolve, reqReject, reqResolve } from './interceptors'
import { requestV2 } from './v2-interceptors'

export function createAxios(options = {}) {
  const defaultOptions = {
    timeout: 60000, // 增加到60秒，适应TDengine查询时间
  }
  const service = axios.create({
    ...defaultOptions,
    ...options,
  })
  service.interceptors.request.use(reqResolve, reqReject)
  service.interceptors.response.use(resResolve, resReject)
  return service
}

export const request = createAxios({
  baseURL: import.meta.env.VITE_BASE_API,
})

// 导出v2 API客户端
export { requestV2 }
