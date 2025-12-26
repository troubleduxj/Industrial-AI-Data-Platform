/**
 * 报警WebSocket Hook
 * 用于接收实时报警通知
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useMessage, useNotification } from 'naive-ui'
import { getToken } from '@/utils'

export function useAlarmWebSocket(options = {}) {
  const {
    deviceTypes = null, // 订阅的设备类型，null表示全部
    autoConnect = true,
    onAlarm = null, // 报警回调
    onStatisticsUpdate = null, // 统计更新回调
  } = options

  const message = useMessage()
  const notification = useNotification()

  const connected = ref(false)
  const connecting = ref(false)
  const alarms = ref([]) // 最近的报警列表
  const ws = ref(null)
  const reconnectTimer = ref(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  // 构建WebSocket URL
  const buildWsUrl = () => {
    const token = getToken()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    
    let url = `${protocol}//${host}/api/v2/alarm-ws/ws?token=${token}`
    
    if (deviceTypes && deviceTypes.length > 0) {
      url += `&device_types=${deviceTypes.join(',')}`
    }
    
    return url
  }

  // 连接WebSocket
  const connect = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      return
    }

    connecting.value = true
    const url = buildWsUrl()

    try {
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        connected.value = true
        connecting.value = false
        reconnectAttempts.value = 0
        console.log('[AlarmWS] 连接成功')
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (e) {
          console.error('[AlarmWS] 解析消息失败:', e)
        }
      }

      ws.value.onclose = (event) => {
        connected.value = false
        connecting.value = false
        console.log('[AlarmWS] 连接关闭:', event.code, event.reason)
        
        // 尝试重连
        if (reconnectAttempts.value < maxReconnectAttempts) {
          scheduleReconnect()
        }
      }

      ws.value.onerror = (error) => {
        console.error('[AlarmWS] 连接错误:', error)
        connecting.value = false
      }
    } catch (e) {
      console.error('[AlarmWS] 创建连接失败:', e)
      connecting.value = false
    }
  }

  // 处理消息
  const handleMessage = (data) => {
    const { type } = data

    switch (type) {
      case 'connected':
        console.log('[AlarmWS] 连接确认:', data.message)
        break

      case 'alarm':
        handleAlarm(data.data)
        break

      case 'statistics_update':
        if (onStatisticsUpdate) {
          onStatisticsUpdate()
        }
        break

      case 'ping':
        // 响应心跳
        send({ type: 'pong' })
        break

      case 'pong':
        // 心跳响应，忽略
        break

      default:
        console.log('[AlarmWS] 未知消息类型:', type)
    }
  }

  // 处理报警
  const handleAlarm = (alarm) => {
    console.log('[AlarmWS] 收到报警:', alarm)

    // 添加到列表
    alarms.value.unshift(alarm)
    if (alarms.value.length > 100) {
      alarms.value = alarms.value.slice(0, 100)
    }

    // 显示通知
    showAlarmNotification(alarm)

    // 调用回调
    if (onAlarm) {
      onAlarm(alarm)
    }
  }

  // 显示报警通知
  const showAlarmNotification = (alarm) => {
    const levelMap = {
      info: 'info',
      warning: 'warning',
      critical: 'error',
      emergency: 'error',
    }
    const levelNames = {
      info: '信息',
      warning: '警告',
      critical: '严重',
      emergency: '紧急',
    }

    const type = levelMap[alarm.alarm_level] || 'warning'
    const levelName = levelNames[alarm.alarm_level] || alarm.alarm_level

    notification[type]({
      title: `${levelName}报警`,
      content: alarm.alarm_title,
      description: alarm.alarm_content,
      duration: alarm.alarm_level === 'emergency' ? 0 : 5000, // 紧急报警不自动关闭
      meta: `设备: ${alarm.device_code}`,
    })
  }

  // 发送消息
  const send = (data) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    }
  }

  // 更新订阅
  const updateSubscription = (newDeviceTypes) => {
    send({
      type: 'subscribe',
      device_types: newDeviceTypes,
    })
  }

  // 安排重连
  const scheduleReconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
    reconnectAttempts.value++

    console.log(`[AlarmWS] ${delay / 1000}秒后尝试重连 (${reconnectAttempts.value}/${maxReconnectAttempts})`)

    reconnectTimer.value = setTimeout(() => {
      connect()
    }, delay)
  }

  // 断开连接
  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    connected.value = false
    reconnectAttempts.value = maxReconnectAttempts // 阻止重连
  }

  // 清除报警列表
  const clearAlarms = () => {
    alarms.value = []
  }

  // 生命周期
  onMounted(() => {
    if (autoConnect) {
      connect()
    }
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    connecting,
    alarms,
    connect,
    disconnect,
    updateSubscription,
    clearAlarms,
  }
}

export default useAlarmWebSocket
