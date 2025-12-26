/**
 * AI模块状态管理 Store
 * 用于管理AI模块的启用状态、健康检查、资源监控等
 */
import { defineStore } from 'pinia'
import { aiModuleApi } from '@/api/v2/ai-module'

/**
 * AI模块健康状态接口
 */
export interface AIModuleHealth {
  status: 'healthy' | 'disabled' | 'error'
  modules: {
    core: {
      enabled: boolean
      status: string
    }
    ai: {
      enabled: boolean
      loaded: boolean
      status: string
    }
  }
}

/**
 * AI模块配置接口
 */
export interface AIModuleConfig {
  enabled: boolean
  features: {
    feature_extraction: boolean
    anomaly_detection: boolean
    trend_prediction: boolean
    health_scoring: boolean
    smart_analysis: boolean
  }
  resources: {
    max_memory_mb: number
    max_cpu_percent: number
    worker_threads: number
  }
}

/**
 * AI模块资源使用情况接口
 */
export interface AIModuleResources {
  timestamp: string
  memory_mb: number
  cpu_percent: number
  status: 'healthy' | 'warning' | 'critical'
  status_reason: string
}

/**
 * AI模块 Store 状态接口
 */
interface AIModuleState {
  // 模块健康状态
  health: AIModuleHealth | null
  // 模块配置
  config: AIModuleConfig | null
  // 资源使用情况
  resources: AIModuleResources | null
  // 加载状态
  loading: boolean
  // 错误信息
  error: string | null
  // 最后更新时间
  lastUpdate: Date | null
}

/**
 * AI模块 Store
 */
export const useAIModuleStore = defineStore('aiModule', {
  state: (): AIModuleState => ({
    health: null,
    config: null,
    resources: null,
    loading: false,
    error: null,
    lastUpdate: null,
  }),

  getters: {
    /**
     * AI模块是否启用
     */
    isEnabled(): boolean {
      return this.health?.modules?.ai?.enabled || false
    },

    /**
     * AI模块是否已加载
     */
    isLoaded(): boolean {
      return this.health?.modules?.ai?.loaded || false
    },

    /**
     * 系统整体状态
     */
    systemStatus(): string {
      return this.health?.status || 'unknown'
    },

    /**
     * AI模块状态
     */
    aiStatus(): string {
      return this.health?.modules?.ai?.status || 'unknown'
    },

    /**
     * 资源状态
     */
    resourceStatus(): 'healthy' | 'warning' | 'critical' | 'unknown' {
      return this.resources?.status || 'unknown'
    },

    /**
     * 是否需要显示警告
     */
    hasWarning(): boolean {
      return this.resourceStatus === 'warning' || this.resourceStatus === 'critical'
    },

    /**
     * 已启用的功能列表
     */
    enabledFeatures(): string[] {
      if (!this.config?.features) return []
      
      const features = this.config.features
      const enabledList: string[] = []
      
      if (features.feature_extraction) enabledList.push('特征提取')
      if (features.anomaly_detection) enabledList.push('异常检测')
      if (features.trend_prediction) enabledList.push('趋势预测')
      if (features.health_scoring) enabledList.push('健康评分')
      if (features.smart_analysis) enabledList.push('智能分析')
      
      return enabledList
    },

    /**
     * 资源使用百分比
     */
    resourceUsage(): { memory: number; cpu: number } | null {
      if (!this.resources || !this.config) return null
      
      return {
        memory: Math.round((this.resources.memory_mb / this.config.resources.max_memory_mb) * 100),
        cpu: Math.round((this.resources.cpu_percent / this.config.resources.max_cpu_percent) * 100),
      }
    },
  },

  actions: {
    /**
     * 获取AI模块健康状态
     */
    async fetchHealth(): Promise<void> {
      this.loading = true
      this.error = null
      
      try {
        const response = await aiModuleApi.getHealth()
        
        if (response.code === 200 && response.data) {
          // 将新格式的API响应转换为Store期望的格式
          const aiModuleStatus = response.data.ai_module_status || {}
          this.health = {
            status: response.data.status || 'healthy',
            modules: {
              core: { enabled: true, status: 'running' },
              ai: {
                enabled: aiModuleStatus.module_enabled || false,
                loaded: aiModuleStatus.module_loaded || false,
                status: (aiModuleStatus.module_enabled && aiModuleStatus.module_loaded) 
                  ? 'running' 
                  : (aiModuleStatus.module_enabled ? 'loading' : 'disabled'),
              },
            },
          }
          this.lastUpdate = new Date()
        } else {
          throw new Error(response.message || '获取健康状态失败')
        }
      } catch (error: any) {
        console.error('获取AI模块健康状态失败:', error)
        this.error = error.message || '未知错误'
        
        // 设置默认的禁用状态
        this.health = {
          status: 'disabled',
          modules: {
            core: { enabled: true, status: 'running' },
            ai: { enabled: false, loaded: false, status: 'disabled' },
          },
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取AI模块配置
     */
    async fetchConfig(): Promise<void> {
      if (!this.isEnabled) {
        console.log('AI模块未启用，跳过配置获取')
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await aiModuleApi.getConfig()
        
        if (response.code === 200 && response.data) {
          this.config = response.data as AIModuleConfig
          this.lastUpdate = new Date()
        } else {
          throw new Error(response.message || '获取配置失败')
        }
      } catch (error: any) {
        console.error('获取AI模块配置失败:', error)
        this.error = error.message || '未知错误'
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取AI模块资源使用情况
     */
    async fetchResources(): Promise<void> {
      if (!this.isEnabled) {
        console.log('AI模块未启用，跳过资源获取')
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await aiModuleApi.getResources()
        
        if (response.code === 200 && response.data) {
          this.resources = response.data as AIModuleResources
          this.lastUpdate = new Date()
        } else {
          throw new Error(response.message || '获取资源使用情况失败')
        }
      } catch (error: any) {
        console.error('获取AI模块资源使用情况失败:', error)
        this.error = error.message || '未知错误'
        
        // 如果是503错误，说明AI模块未启用
        if (error.response?.status === 503) {
          this.resources = null
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * 初始化AI模块（获取所有状态）
     */
    async initialize(): Promise<void> {
      console.log('🚀 初始化AI模块Store...')
      
      // 先获取健康状态
      await this.fetchHealth()
      
      // 如果AI模块启用，再获取配置和资源
      if (this.isEnabled) {
        await Promise.all([
          this.fetchConfig(),
          this.fetchResources(),
        ])
        console.log('✅ AI模块Store初始化完成')
      } else {
        console.log('⏸️ AI模块未启用，跳过详细配置加载')
      }
    },

    /**
     * 刷新所有数据
     */
    async refresh(): Promise<void> {
      await this.initialize()
    },

    /**
     * 重置Store
     */
    reset(): void {
      this.$reset()
    },
  },
})

