/**
 * 工业AI数据平台 API v4 - 统一导出
 */
import { assetApi } from './assets'
import { categoryApi } from './categories'
import { signalApi } from './signals'
import { modelApi } from './models'

export {
  assetApi,
  categoryApi,
  signalApi,
  modelApi,
}

// 默认导出对象
export default {
  asset: assetApi,
  category: categoryApi,
  signal: signalApi,
  model: modelApi,
}
