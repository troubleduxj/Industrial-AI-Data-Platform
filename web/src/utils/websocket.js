/**
 * WebSocket客户端
 * 
 * 实现WebSocket连接管理、自动重连和状态管理功能。
 * 
 * 需求: 3.4 - 当连接断开时，平台应支持自动重连和状态恢复
 * 需求: 7.1 - 当打开监控页面时，前端应自动建立WebSocket连接
 * 需求: 7.5 - 前端应支持配置数据刷新频率和显示精度
 * 需求: 7.6 - 当网络断开时，前端应显示连接状态并自动重连
 */

import { ref, reactive, computed, watch, onUnmounted } from 'vue'

// 连接状态枚举
export const ConnectionState = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
}

// 默认配置
const DEFAULT_CONFIG = {
  // 重连配置
  reconnect: true,
  reconnectInterval: 1000,      // 初始重连间隔（毫秒）
  maxReconnectInterval: 30000,  // 最大重连间隔（毫秒）
  reconnectDecay: 1.5,          // 重连间隔增长系数
  maxReconnectAttempts: 10,     // 最大重连次数
  
  // 心跳配置
  heartbeat: true,
  heartbeatInterval: 30000,     // 心跳间隔（毫秒）
  heartbeatTimeout: 10000,      // 心跳超时（毫秒）
  
  // 数据刷新配置 (需求 7.5)
  refreshInterval: 1000,        // 数据刷新间隔（毫秒）
  minRefreshInterval: 100,      // 最小刷新间隔（毫秒）
  maxRefreshInterval: 60000,    // 最大刷新间隔（毫秒）
  
  // 显示精度配置 (需求 7.5)
  displayPrecision: 2,          // 默认显示精度（小数位数）
  
  // 其他配置
  debug: false
}

/**
 * WebSocket客户端类
 */
export class WebSocketClient {
  constructor(url, options = {}) {
    this.url = url
    this.config = { ...DEFAULT_CONFIG, ...options }
    
    // 连接状态
    this.state = ref(ConnectionState.DISCONNECTED)
    this.socket = null
    
    // 重连相关
    this.reconnectAttempts = 0
    this.reconnectTimer = null
    this.currentReconnectInterval = this.config.reconnectInterval
    
    // 心跳相关
    this.heartbeatTimer = null
    this.heartbeatTimeoutTimer = null
    
    // 订阅的资产
    this.subscribedAssets = reactive(new Set())
    
    // 消息处理器
    this.messageHandlers = new Map()
    
    // 事件监听器
    this.eventListeners = {
      open: [],
      close: [],
      error: [],
      message: [],
      stateChange: []
    }
    
    // 刷新频率配置 (需求 7.5)
    this.refreshInterval = ref(this.config.refreshInterval)
    this.displayPrecision = ref(this.config.displayPrecision)
    
    // 保存最后使用的token
    this._lastToken = null
  }
  
  /**
   * 获取连接状态
   */
  get connectionState() {
    return this.state.value
  }
  
  /**
   * 是否已连接
   */
  get isConnected() {
    return this.state.value === ConnectionState.CONNECTED
  }
  
  /**
   * 建立连接
   * @param {string} token - JWT认证令牌
   */
  connect(token) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this._log('已经连接，跳过')
      return
    }
    
    // 保存token用于重连
    this._lastToken = token
    
    this._setState(ConnectionState.CONNECTING)
    
    // 构建带token的URL
    const wsUrl = token ? `${this.url}?token=${token}` : this.url
    
    try {
      this.socket = new WebSocket(wsUrl)
      this._setupSocketHandlers()
    } catch (error) {
      this._log('连接失败:', error)
      this._setState(ConnectionState.ERROR)
      this._scheduleReconnect()
    }
  }
  
  /**
   * 断开连接
   */
  disconnect() {
    this._clearTimers()
    this.reconnectAttempts = 0
    
    if (this.socket) {
      this.socket.close(1000, '主动断开')
      this.socket = null
    }
    
    this._setState(ConnectionState.DISCONNECTED)
  }
  
  /**
   * 订阅资产数据
   * @param {number|number[]} assetIds - 资产ID或ID数组
   * @param {string} type - 订阅类型 (asset_data, alert, prediction, all)
   */
  subscribe(assetIds, type = 'asset_data') {
    const ids = Array.isArray(assetIds) ? assetIds : [assetIds]
    
    if (!this.isConnected) {
      this._log('未连接，无法订阅')
      return false
    }
    
    this._send({
      action: 'subscribe',
      asset_ids: ids,
      type: type
    })
    
    // 记录订阅
    ids.forEach(id => this.subscribedAssets.add(id))
    
    return true
  }
  
  /**
   * 取消订阅
   * @param {number|number[]} assetIds - 资产ID或ID数组
   */
  unsubscribe(assetIds) {
    const ids = Array.isArray(assetIds) ? assetIds : [assetIds]
    
    if (!this.isConnected) {
      this._log('未连接，无法取消订阅')
      return false
    }
    
    this._send({
      action: 'unsubscribe',
      asset_ids: ids
    })
    
    // 移除订阅记录
    ids.forEach(id => this.subscribedAssets.delete(id))
    
    return true
  }
  
  /**
   * 获取当前订阅列表
   */
  getSubscriptions() {
    if (!this.isConnected) {
      return
    }
    
    this._send({
      action: 'get_subscriptions'
    })
  }
  
  /**
   * 设置刷新频率 (需求 7.5)
   * @param {number} interval - 刷新间隔（毫秒）
   */
  setRefreshInterval(interval) {
    const clampedInterval = Math.max(
      this.config.minRefreshInterval,
      Math.min(this.config.maxRefreshInterval, interval)
    )
    this.refreshInterval.value = clampedInterval
    this._log(`刷新频率设置为: ${clampedInterval}ms`)
    
    // 通知服务器更新推送频率
    if (this.isConnected) {
      this._send({
        action: 'set_refresh_interval',
        interval: clampedInterval
      })
    }
    
    return clampedInterval
  }
  
  /**
   * 获取刷新频率
   */
  getRefreshInterval() {
    return this.refreshInterval.value
  }
  
  /**
   * 设置显示精度 (需求 7.5)
   * @param {number} precision - 小数位数
   */
  setDisplayPrecision(precision) {
    const clampedPrecision = Math.max(0, Math.min(10, precision))
    this.displayPrecision.value = clampedPrecision
    this._log(`显示精度设置为: ${clampedPrecision}位小数`)
    return clampedPrecision
  }
  
  /**
   * 获取显示精度
   */
  getDisplayPrecision() {
    return this.displayPrecision.value
  }
  
  /**
   * 注册消息处理器
   * @param {string} type - 消息类型
   * @param {Function} handler - 处理函数
   */
  onMessage(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type).push(handler)
    
    // 返回取消注册函数
    return () => {
      const handlers = this.messageHandlers.get(type)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }
  
  /**
   * 注册事件监听器
   * @param {string} event - 事件名称 (open, close, error, message, stateChange)
   * @param {Function} listener - 监听函数
   */
  on(event, listener) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].push(listener)
    }
    
    // 返回取消监听函数
    return () => {
      const listeners = this.eventListeners[event]
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }
  
  /**
   * 设置Socket事件处理器
   */
  _setupSocketHandlers() {
    this.socket.onopen = (event) => {
      this._log('连接已建立')
      this._setState(ConnectionState.CONNECTED)
      this.reconnectAttempts = 0
      this.currentReconnectInterval = this.config.reconnectInterval
      
      // 启动心跳
      if (this.config.heartbeat) {
        this._startHeartbeat()
      }
      
      // 恢复订阅
      this._restoreSubscriptions()
      
      // 触发事件
      this._emit('open', event)
    }
    
    this.socket.onclose = (event) => {
      this._log('连接已关闭:', event.code, event.reason)
      this._clearTimers()
      
      // 触发事件
      this._emit('close', event)
      
      // 非主动关闭时尝试重连
      if (event.code !== 1000 && this.config.reconnect) {
        this._scheduleReconnect()
      } else {
        this._setState(ConnectionState.DISCONNECTED)
      }
    }
    
    this.socket.onerror = (error) => {
      this._log('连接错误:', error)
      this._setState(ConnectionState.ERROR)
      this._emit('error', error)
    }
    
    this.socket.onmessage = (event) => {
      this._handleMessage(event.data)
    }
  }
  
  /**
   * 处理接收到的消息
   */
  _handleMessage(data) {
    try {
      const message = JSON.parse(data)
      
      this._log('收到消息:', message.type)
      
      // 处理心跳响应
      if (message.type === 'pong') {
        this._handlePong()
        return
      }
      
      // 触发通用消息事件
      this._emit('message', message)
      
      // 触发特定类型的处理器
      const handlers = this.messageHandlers.get(message.type)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message)
          } catch (error) {
            this._log('消息处理器错误:', error)
          }
        })
      }
      
    } catch (error) {
      this._log('消息解析失败:', error)
    }
  }
  
  /**
   * 发送消息
   */
  _send(data) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this._log('无法发送消息：未连接')
      return false
    }
    
    try {
      this.socket.send(JSON.stringify(data))
      return true
    } catch (error) {
      this._log('发送消息失败:', error)
      return false
    }
  }
  
  /**
   * 启动心跳
   */
  _startHeartbeat() {
    this._clearHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this._send({ action: 'ping' })
        
        // 设置心跳超时
        this.heartbeatTimeoutTimer = setTimeout(() => {
          this._log('心跳超时，重新连接')
          this.socket.close(4000, '心跳超时')
        }, this.config.heartbeatTimeout)
      }
    }, this.config.heartbeatInterval)
  }
  
  /**
   * 处理心跳响应
   */
  _handlePong() {
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer)
      this.heartbeatTimeoutTimer = null
    }
  }
  
  /**
   * 清除心跳定时器
   */
  _clearHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer)
      this.heartbeatTimeoutTimer = null
    }
  }
  
  /**
   * 安排重连
   */
  _scheduleReconnect() {
    if (!this.config.reconnect) {
      return
    }
    
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this._log('达到最大重连次数，停止重连')
      this._setState(ConnectionState.ERROR)
      return
    }
    
    this._setState(ConnectionState.RECONNECTING)
    this.reconnectAttempts++
    
    this._log(`${this.currentReconnectInterval}ms 后进行第 ${this.reconnectAttempts} 次重连`)
    
    this.reconnectTimer = setTimeout(() => {
      this.connect(this._lastToken)
    }, this.currentReconnectInterval)
    
    // 增加重连间隔
    this.currentReconnectInterval = Math.min(
      this.currentReconnectInterval * this.config.reconnectDecay,
      this.config.maxReconnectInterval
    )
  }
  
  /**
   * 恢复订阅
   */
  _restoreSubscriptions() {
    if (this.subscribedAssets.size > 0) {
      const assetIds = Array.from(this.subscribedAssets)
      this._log('恢复订阅:', assetIds)
      this._send({
        action: 'subscribe',
        asset_ids: assetIds,
        type: 'asset_data'
      })
    }
  }
  
  /**
   * 清除所有定时器
   */
  _clearTimers() {
    this._clearHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
  
  /**
   * 设置状态
   */
  _setState(newState) {
    const oldState = this.state.value
    this.state.value = newState
    
    if (oldState !== newState) {
      this._emit('stateChange', { oldState, newState })
    }
  }
  
  /**
   * 触发事件
   */
  _emit(event, data) {
    const listeners = this.eventListeners[event]
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data)
        } catch (error) {
          this._log('事件监听器错误:', error)
        }
      })
    }
  }
  
  /**
   * 日志输出
   */
  _log(...args) {
    if (this.config.debug) {
      console.log('[WebSocket]', ...args)
    }
  }
}

/**
 * Vue Composable - 使用WebSocket
 * @param {string} url - WebSocket URL
 * @param {Object} options - 配置选项
 */
export function useWebSocket(url, options = {}) {
  const client = new WebSocketClient(url, options)
  
  // 响应式状态
  const state = computed(() => client.state.value)
  const isConnected = computed(() => client.isConnected)
  const subscribedAssets = computed(() => Array.from(client.subscribedAssets))
  const refreshInterval = computed(() => client.refreshInterval.value)
  const displayPrecision = computed(() => client.displayPrecision.value)
  
  // 最新消息
  const lastMessage = ref(null)
  const lastAssetData = ref(null)
  const lastAlert = ref(null)
  const lastPrediction = ref(null)
  
  // 历史数据缓存（用于图表）
  const dataHistory = reactive({})
  const maxHistoryLength = ref(100)
  
  // 注册默认消息处理器
  client.onMessage('asset_data', (msg) => {
    lastMessage.value = msg
    lastAssetData.value = msg
    
    // 缓存历史数据
    const assetId = msg.asset_id
    if (!dataHistory[assetId]) {
      dataHistory[assetId] = []
    }
    dataHistory[assetId].push({
      timestamp: msg.timestamp || new Date().toISOString(),
      data: msg.data
    })
    // 限制历史数据长度
    if (dataHistory[assetId].length > maxHistoryLength.value) {
      dataHistory[assetId].shift()
    }
  })
  
  client.onMessage('alert', (msg) => {
    lastMessage.value = msg
    lastAlert.value = msg
  })
  
  client.onMessage('prediction', (msg) => {
    lastMessage.value = msg
    lastPrediction.value = msg
  })
  
  // 清除历史数据
  const clearHistory = (assetId) => {
    if (assetId) {
      delete dataHistory[assetId]
    } else {
      Object.keys(dataHistory).forEach(key => delete dataHistory[key])
    }
  }
  
  // 获取资产历史数据
  const getAssetHistory = (assetId) => {
    return dataHistory[assetId] || []
  }
  
  // 组件卸载时断开连接
  onUnmounted(() => {
    client.disconnect()
  })
  
  return {
    // 状态
    state,
    isConnected,
    subscribedAssets,
    lastMessage,
    lastAssetData,
    lastAlert,
    lastPrediction,
    refreshInterval,
    displayPrecision,
    dataHistory,
    
    // 方法
    connect: (token) => client.connect(token),
    disconnect: () => client.disconnect(),
    subscribe: (assetIds, type) => client.subscribe(assetIds, type),
    unsubscribe: (assetIds) => client.unsubscribe(assetIds),
    getSubscriptions: () => client.getSubscriptions(),
    setRefreshInterval: (interval) => client.setRefreshInterval(interval),
    setDisplayPrecision: (precision) => client.setDisplayPrecision(precision),
    clearHistory,
    getAssetHistory,
    setMaxHistoryLength: (length) => { maxHistoryLength.value = length },
    
    // 事件注册
    onMessage: (type, handler) => client.onMessage(type, handler),
    on: (event, listener) => client.on(event, listener),
    
    // 原始客户端
    client
  }
}

/**
 * 创建全局WebSocket实例
 */
let globalClient = null

export function getGlobalWebSocket() {
  return globalClient
}

export function createGlobalWebSocket(url, options = {}) {
  if (globalClient) {
    globalClient.disconnect()
  }
  globalClient = new WebSocketClient(url, options)
  return globalClient
}

export default {
  WebSocketClient,
  useWebSocket,
  getGlobalWebSocket,
  createGlobalWebSocket,
  ConnectionState
}
