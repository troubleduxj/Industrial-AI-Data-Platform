/**
 * 交互状态管理组合式函数
 * 提供统一的加载状态、反馈提示和动画控制
 */

import { ref, reactive, computed, nextTick } from 'vue'
import { INTERACTION_CONFIG } from '@/components/interaction'

// 全局状态管理
const globalState = reactive({
  loading: false,
  loadingText: '',
  loadingProgress: null,
  toasts: [],
})

/**
 * 加载状态管理
 * @param {Object} options - 配置选项
 * @returns {Object} 加载状态管理对象
 */
export function useLoading(options = {}) {
  const loading = ref(false)
  const loadingText = ref(options.text || '')
  const loadingProgress = ref(null)

  // 开始加载
  function startLoading(text = '', showGlobal = false) {
    loading.value = true
    loadingText.value = text
    loadingProgress.value = null

    if (showGlobal) {
      globalState.loading = true
      globalState.loadingText = text
    }
  }

  // 更新进度
  function updateProgress(progress, text = '') {
    loadingProgress.value = progress
    if (text) {
      loadingText.value = text
    }

    if (globalState.loading) {
      globalState.loadingProgress = progress
      if (text) {
        globalState.loadingText = text
      }
    }
  }

  // 停止加载
  function stopLoading() {
    loading.value = false
    loadingText.value = ''
    loadingProgress.value = null

    if (globalState.loading) {
      globalState.loading = false
      globalState.loadingText = ''
      globalState.loadingProgress = null
    }
  }

  // 异步操作包装器
  async function withLoading(asyncFn, text = '加载中...', showGlobal = false) {
    startLoading(text, showGlobal)
    try {
      const result = await asyncFn()
      return result
    } finally {
      stopLoading()
    }
  }

  return {
    loading: readonly(loading),
    loadingText: readonly(loadingText),
    loadingProgress: readonly(loadingProgress),
    startLoading,
    updateProgress,
    stopLoading,
    withLoading,
  }
}

/**
 * 反馈提示管理
 * @param {Object} options - 配置选项
 * @returns {Object} 反馈提示管理对象
 */
export function useFeedback(options = {}) {
  const toastRef = ref(null)

  // 显示提示
  function showToast(type, message, options = {}) {
    const toastOptions = {
      type,
      message,
      duration: options.duration ?? INTERACTION_CONFIG.toast.defaultDuration,
      title: options.title,
      closable: options.closable,
      showProgress: options.showProgress,
      onClick: options.onClick,
      onClose: options.onClose,
    }

    if (toastRef.value) {
      return toastRef.value.show(toastOptions)
    } else {
      // 如果没有Toast组件引用，使用全局状态
      const toast = {
        id: Date.now() + Math.random().toString(36).substr(2, 9),
        ...toastOptions,
        timestamp: Date.now(),
      }
      globalState.toasts.push(toast)

      // 自动移除
      if (toast.duration > 0) {
        setTimeout(() => {
          const index = globalState.toasts.findIndex((t) => t.id === toast.id)
          if (index > -1) {
            globalState.toasts.splice(index, 1)
          }
        }, toast.duration)
      }

      return toast.id
    }
  }

  // 便捷方法
  function success(message, options = {}) {
    return showToast('success', message, options)
  }

  function info(message, options = {}) {
    return showToast('info', message, options)
  }

  function warning(message, options = {}) {
    return showToast('warning', message, options)
  }

  function error(message, options = {}) {
    return showToast('error', message, options)
  }

  // 移除提示
  function removeToast(id) {
    if (toastRef.value) {
      toastRef.value.removeToast(id)
    } else {
      const index = globalState.toasts.findIndex((t) => t.id === id)
      if (index > -1) {
        globalState.toasts.splice(index, 1)
      }
    }
  }

  // 清除所有提示
  function clearToasts() {
    if (toastRef.value) {
      toastRef.value.clear()
    } else {
      globalState.toasts.length = 0
    }
  }

  return {
    toastRef,
    showToast,
    success,
    info,
    warning,
    error,
    removeToast,
    clearToasts,
  }
}

/**
 * 动画控制管理
 * @param {Object} options - 配置选项
 * @returns {Object} 动画控制管理对象
 */
export function useAnimation(options = {}) {
  const animating = ref(false)
  const animationType = ref(options.type || 'fade')
  const animationDuration = ref(options.duration || 300)

  // 执行动画
  async function animate(element, type = animationType.value, duration = animationDuration.value) {
    if (!element) return

    animating.value = true

    return new Promise((resolve) => {
      const handleAnimationEnd = () => {
        element.removeEventListener('animationend', handleAnimationEnd)
        element.removeEventListener('transitionend', handleAnimationEnd)
        animating.value = false
        resolve()
      }

      element.addEventListener('animationend', handleAnimationEnd)
      element.addEventListener('transitionend', handleAnimationEnd)

      // 添加动画类
      element.classList.add(`animate-${type}`)

      // 设置动画持续时间
      element.style.animationDuration = `${duration}ms`
      element.style.transitionDuration = `${duration}ms`

      // 备用超时
      setTimeout(() => {
        if (animating.value) {
          handleAnimationEnd()
        }
      }, duration + 100)
    })
  }

  // 淡入动画
  async function fadeIn(element, duration = 300) {
    return animate(element, 'fade-in', duration)
  }

  // 淡出动画
  async function fadeOut(element, duration = 300) {
    return animate(element, 'fade-out', duration)
  }

  // 滑入动画
  async function slideIn(element, direction = 'up', duration = 300) {
    return animate(element, `slide-in-${direction}`, duration)
  }

  // 滑出动画
  async function slideOut(element, direction = 'up', duration = 300) {
    return animate(element, `slide-out-${direction}`, duration)
  }

  // 缩放动画
  async function scale(element, from = 0, to = 1, duration = 300) {
    if (!element) return

    animating.value = true

    return new Promise((resolve) => {
      element.style.transform = `scale(${from})`
      element.style.transition = `transform ${duration}ms ease`

      nextTick(() => {
        element.style.transform = `scale(${to})`

        setTimeout(() => {
          animating.value = false
          resolve()
        }, duration)
      })
    })
  }

  // 震动动画
  function shake(element, intensity = 10, duration = 500) {
    if (!element) return

    const originalTransform = element.style.transform
    const keyframes = []
    const steps = 10

    for (let i = 0; i <= steps; i++) {
      const progress = i / steps
      const offset = Math.sin(progress * Math.PI * 4) * intensity * (1 - progress)
      keyframes.push({ transform: `translateX(${offset}px)` })
    }

    return element
      .animate(keyframes, {
        duration,
        easing: 'ease-out',
      })
      .finished.then(() => {
        element.style.transform = originalTransform
      })
  }

  // 弹跳动画
  function bounce(element, height = 20, duration = 600) {
    if (!element) return

    const keyframes = [
      { transform: 'translateY(0px)' },
      { transform: `translateY(-${height}px)` },
      { transform: 'translateY(0px)' },
      { transform: `translateY(-${height / 2}px)` },
      { transform: 'translateY(0px)' },
    ]

    return element.animate(keyframes, {
      duration,
      easing: 'ease-out',
    }).finished
  }

  return {
    animating: readonly(animating),
    animationType: readonly(animationType),
    animationDuration: readonly(animationDuration),
    animate,
    fadeIn,
    fadeOut,
    slideIn,
    slideOut,
    scale,
    shake,
    bounce,
  }
}

/**
 * 交互状态组合管理
 * @param {Object} options - 配置选项
 * @returns {Object} 交互状态管理对象
 */
export function useInteraction(options = {}) {
  const loading = useLoading(options.loading)
  const feedback = useFeedback(options.feedback)
  const animation = useAnimation(options.animation)

  // 组合操作：带反馈的异步操作
  async function withFeedback(
    asyncFn,
    {
      loadingText = '处理中...',
      successMessage = '操作成功',
      errorMessage = '操作失败',
      showGlobal = false,
    } = {}
  ) {
    try {
      const result = await loading.withLoading(asyncFn, loadingText, showGlobal)
      if (successMessage) {
        feedback.success(successMessage)
      }
      return result
    } catch (error) {
      console.error('操作失败:', error)
      if (errorMessage) {
        feedback.error(typeof error === 'string' ? error : errorMessage)
      }
      throw error
    }
  }

  // 组合操作：带动画的状态切换
  async function animatedToggle(
    element,
    show,
    { showAnimation = 'fade-in', hideAnimation = 'fade-out', duration = 300 } = {}
  ) {
    if (show) {
      element.style.display = 'block'
      await animation.animate(element, showAnimation, duration)
    } else {
      await animation.animate(element, hideAnimation, duration)
      element.style.display = 'none'
    }
  }

  // 确认对话框
  async function confirm(
    message,
    { title = '确认', confirmText = '确定', cancelText = '取消', type = 'warning' } = {}
  ) {
    return new Promise((resolve) => {
      // 这里可以集成具体的对话框组件
      const result = window.confirm(`${title}\n${message}`)
      resolve(result)
    })
  }

  return {
    // 加载状态
    ...loading,

    // 反馈提示
    ...feedback,

    // 动画控制
    ...animation,

    // 组合操作
    withFeedback,
    animatedToggle,
    confirm,

    // 全局状态
    globalState: readonly(globalState),
  }
}

/**
 * 表单交互增强
 * @param {Object} formRef - 表单引用
 * @param {Object} options - 配置选项
 * @returns {Object} 表单交互管理对象
 */
export function useFormInteraction(formRef, options = {}) {
  const interaction = useInteraction(options)
  const submitting = ref(false)
  const validating = ref(false)

  // 提交表单
  async function submitForm(
    submitFn,
    {
      loadingText = '提交中...',
      successMessage = '提交成功',
      errorMessage = '提交失败',
      validateFirst = true,
    } = {}
  ) {
    if (submitting.value) return

    try {
      submitting.value = true

      // 验证表单
      if (validateFirst && formRef.value) {
        validating.value = true
        const validation = await formRef.value.validate()
        validating.value = false

        if (!validation.valid) {
          interaction.warning('请检查表单输入')
          return
        }
      }

      // 提交表单
      const result = await interaction.withFeedback(submitFn, {
        loadingText,
        successMessage,
        errorMessage,
      })

      return result
    } finally {
      submitting.value = false
      validating.value = false
    }
  }

  // 重置表单
  function resetForm(showConfirm = true) {
    const doReset = () => {
      if (formRef.value) {
        formRef.value.resetForm()
        interaction.info('表单已重置')
      }
    }

    if (showConfirm) {
      interaction.confirm('确定要重置表单吗？').then((confirmed) => {
        if (confirmed) {
          doReset()
        }
      })
    } else {
      doReset()
    }
  }

  return {
    ...interaction,
    submitting: readonly(submitting),
    validating: readonly(validating),
    submitForm,
    resetForm,
  }
}

// 工具函数
export const interactionHelpers = {
  /**
   * 创建防抖的交互函数
   * @param {Function} fn - 要防抖的函数
   * @param {number} delay - 延迟时间
   * @returns {Function} 防抖后的函数
   */
  debounced(fn, delay = 300) {
    let timeoutId
    return function (...args) {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => fn.apply(this, args), delay)
    }
  },

  /**
   * 创建节流的交互函数
   * @param {Function} fn - 要节流的函数
   * @param {number} limit - 限制时间
   * @returns {Function} 节流后的函数
   */
  throttled(fn, limit = 300) {
    let inThrottle
    return function (...args) {
      if (!inThrottle) {
        fn.apply(this, args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), limit)
      }
    }
  },

  /**
   * 创建只执行一次的交互函数
   * @param {Function} fn - 要执行的函数
   * @returns {Function} 只执行一次的函数
   */
  once(fn) {
    let called = false
    return function (...args) {
      if (!called) {
        called = true
        return fn.apply(this, args)
      }
    }
  },
}
