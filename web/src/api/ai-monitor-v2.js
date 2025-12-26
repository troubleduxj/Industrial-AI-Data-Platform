/**
 * AI监控 v2 API
 */
import { request } from '@/utils/http'

const aiMonitorV2Api = {
  // 仪表板相关API
  dashboard: {
    getOverview: () => {
      return request({
        url: '/api/v2/ai-monitor/dashboard/overview',
        method: 'GET',
      })
    },

    getHealthData: () => {
      return request({
        url: '/api/v2/ai-monitor/dashboard/health',
        method: 'GET',
      })
    },

    getAnomalyTrend: (params) => {
      return request({
        url: '/api/v2/ai-monitor/dashboard/anomaly-trend',
        method: 'GET',
        params,
      })
    },

    getHealthTrend: (params) => {
      return request({
        url: '/api/v2/ai-monitor/dashboard/health-trend',
        method: 'GET',
        params,
      })
    },

    getInsights: () => {
      return request({
        url: '/api/v2/ai-monitor/dashboard/insights',
        method: 'GET',
      })
    },
  },

  // 异常检测相关API
  anomalyDetection: {
    getStatus: () => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/status',
        method: 'GET',
      })
    },

    startDetection: () => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/start',
        method: 'POST',
      })
    },

    stopDetection: () => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/stop',
        method: 'POST',
      })
    },

    getAnomalies: (params) => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/anomalies',
        method: 'GET',
        params,
      })
    },

    getAnomalyDetail: (id) => {
      return request({
        url: `/api/v2/ai-monitor/anomaly-detection/anomalies/${id}`,
        method: 'GET',
      })
    },

    handleAnomaly: (id, action) => {
      return request({
        url: `/api/v2/ai-monitor/anomaly-detection/anomalies/${id}/handle`,
        method: 'POST',
        data: { action },
      })
    },

    getThresholdConfig: () => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/threshold-config',
        method: 'GET',
      })
    },

    updateThresholdConfig: (config) => {
      return request({
        url: '/api/v2/ai-monitor/anomaly-detection/threshold-config',
        method: 'PUT',
        data: config,
      })
    },
  },

  // 健康评分相关API
  healthScoring: {
    getScores: (params) => {
      return request({
        url: '/api/v2/ai-monitor/health-scoring/scores',
        method: 'GET',
        params,
      })
    },

    getScoreDetail: (deviceId) => {
      return request({
        url: `/api/v2/ai-monitor/health-scoring/scores/${deviceId}`,
        method: 'GET',
      })
    },

    getScoreTrend: (deviceId, params) => {
      return request({
        url: `/api/v2/ai-monitor/health-scoring/trend/${deviceId}`,
        method: 'GET',
        params,
      })
    },
  },

  // 趋势预测相关API
  trendPrediction: {
    getPredictions: (params) => {
      return request({
        url: '/api/v2/ai-monitor/trend-prediction/predictions',
        method: 'GET',
        params,
      })
    },

    createPrediction: (data) => {
      return request({
        url: '/api/v2/ai-monitor/trend-prediction/predictions',
        method: 'POST',
        data,
      })
    },

    getPredictionDetail: (id) => {
      return request({
        url: `/api/v2/ai-monitor/trend-prediction/predictions/${id}`,
        method: 'GET',
      })
    },
  },

  // 智能分析相关API
  smartAnalysis: {
    getAnalysisResults: (params) => {
      return request({
        url: '/api/v2/ai-monitor/smart-analysis/results',
        method: 'GET',
        params,
      })
    },

    createAnalysis: (data) => {
      return request({
        url: '/api/v2/ai-monitor/smart-analysis/analyze',
        method: 'POST',
        data,
      })
    },

    getAnalysisDetail: (id) => {
      return request({
        url: `/api/v2/ai-monitor/smart-analysis/results/${id}`,
        method: 'GET',
      })
    },
  },

  // 模型管理相关API
  modelManagement: {
    getModels: (params) => {
      return request({
        url: '/api/v2/ai/models',
        method: 'GET',
        params,
      })
    },

    createModel: (data) => {
      return request({
        url: '/api/v2/ai/models',
        method: 'POST',
        data,
      })
    },

    updateModel: (id, data) => {
      return request({
        url: `/api/v2/ai/models/${id}`,
        method: 'PUT',
        data,
      })
    },

    deleteModel: (id) => {
      return request({
        url: `/api/v2/ai/models/${id}`,
        method: 'DELETE',
      })
    },

    deployModel: (id) => {
      return request({
        url: `/api/v2/ai/models/${id}/deploy`,
        method: 'POST',
      })
    },

    getModelMetrics: (id) => {
      return request({
        url: `/api/v2/ai/models/${id}/metrics`,
        method: 'GET',
      })
    },
  },

  // 数据标注相关API
  dataAnnotation: {
    getDatasets: (params) => {
      return request({
        url: '/api/v2/ai-monitor/data-annotation/datasets',
        method: 'GET',
        params,
      })
    },

    createDataset: (data) => {
      return request({
        url: '/api/v2/ai-monitor/data-annotation/datasets',
        method: 'POST',
        data,
      })
    },

    getAnnotations: (datasetId, params) => {
      return request({
        url: `/api/v2/ai-monitor/data-annotation/datasets/${datasetId}/annotations`,
        method: 'GET',
        params,
      })
    },

    createAnnotation: (datasetId, data) => {
      return request({
        url: `/api/v2/ai-monitor/data-annotation/datasets/${datasetId}/annotations`,
        method: 'POST',
        data,
      })
    },

    updateAnnotation: (datasetId, annotationId, data) => {
      return request({
        url: `/api/v2/ai-monitor/data-annotation/datasets/${datasetId}/annotations/${annotationId}`,
        method: 'PUT',
        data,
      })
    },

    deleteAnnotation: (datasetId, annotationId) => {
      return request({
        url: `/api/v2/ai-monitor/data-annotation/datasets/${datasetId}/annotations/${annotationId}`,
        method: 'DELETE',
      })
    },
  },
}

export default aiMonitorV2Api
