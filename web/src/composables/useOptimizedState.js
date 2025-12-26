/**
 * 优化的状态管理组合函数
 * 提供高性能的状态管理和缓存机制
 */

import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { debounce, throttle } from 'lodash-es'

/**
 * 创建优化的响应式状态
 * @param {*} initialValue - 初始值
 * @param {Object} options - 配置选项
 * @returns {Object} 状态管理对象
 */
export function useOptimizedState(initialValue, options = {}) {
  const {
    // 是否启用深度监听
    deep = false,
    // 是否立即执行
    immediate = false,
    // 防抖延迟
    debounceDelay = 0,
    // 节流延迟
    throttleDelay = 0,
    // 是否启用持久化
    persist = false,
    // 持久化键名
    persistKey = '',
    // 序列化函数
    serializer = JSON,
    // 验证函数
    validator = null,
    // 变更回调
    onChange = null,
  } = options

  // 从持久化存储加载初始值
  const loadPersistedValue = () => {
    if (!persist || !persistKey) return initialValue

    try {
      const stored = localStorage.getItem(persistKey)
      if (stored !== null) {
        return serializer.parse(stored)
      }
    } catch (error) {
      console.warn(`Failed to load persisted state for key "${persistKey}":`, error)
    }

    return initialValue
  }

  // 创建响应式状态
  const state = ref(loadPersistedValue())

  // 保存到持久化存储
  const persistState = (value) => {
    if (!persist || !persistKey) return

    try {
      localStorage.setItem(persistKey, serializer.stringify(value))
    } catch (error) {
      console.warn(`Failed to persist state for key "${persistKey}":`, error)
    }
  }

  // 设置状态值
  const setState = (newValue) => {
    // 验证新值
    if (validator && !validator(newValue)) {
      console.warn('State validation failed:', newValue)
      return false
    }

    const oldValue = state.value
    state.value = newValue

    // 持久化
    persistState(newValue)

    // 触发变更回调
    if (onChange) {
      onChange(newValue, oldValue)
    }

    return true
  }

  // 更新状态（支持函数式更新）
  const updateState = (updater) => {
    if (typeof updater === 'function') {
      setState(updater(state.value))
    } else {
      setState(updater)
    }
  }

  // 重置状态
  const resetState = () => {
    setState(initialValue)
  }

  // 创建防抖/节流的更新函数
  let debouncedUpdate = updateState
  let throttledUpdate = updateState

  if (debounceDelay > 0) {
    debouncedUpdate = debounce(updateState, debounceDelay)
  }

  if (throttleDelay > 0) {
    throttledUpdate = throttle(updateState, throttleDelay)
  }

  return {
    state,
    setState,
    updateState,
    resetState,
    debouncedUpdate,
    throttledUpdate,
  }
}

/**
 * 创建计算状态
 * @param {Function} getter - 计算函数
 * @param {Object} options - 配置选项
 * @returns {Object} 计算状态对象
 */
export function useComputedState(getter, options = {}) {
  const {
    // 缓存时间（毫秒）
    cacheTime = 0,
    // 是否启用缓存
    cache = cacheTime > 0,
    // 依赖项
    deps = [],
  } = options

  let cachedValue = null
  let cacheTimestamp = 0
  let cacheTimer = null

  const computedState = computed(() => {
    const now = Date.now()

    // 检查缓存是否有效
    if (cache && cachedValue !== null && now - cacheTimestamp < cacheTime) {
      return cachedValue
    }

    // 计算新值
    const newValue = getter()

    if (cache) {
      cachedValue = newValue
      cacheTimestamp = now

      // 设置缓存过期定时器
      if (cacheTimer) {
        clearTimeout(cacheTimer)
      }

      cacheTimer = setTimeout(() => {
        cachedValue = null
        cacheTimestamp = 0
      }, cacheTime)
    }

    return newValue
  })

  // 清除缓存
  const clearCache = () => {
    cachedValue = null
    cacheTimestamp = 0
    if (cacheTimer) {
      clearTimeout(cacheTimer)
      cacheTimer = null
    }
  }

  // 组件卸载时清理
  onUnmounted(() => {
    clearCache()
  })

  return {
    computedState,
    clearCache,
  }
}

/**
 * 创建异步状态
 * @param {Function} asyncFn - 异步函数
 * @param {Object} options - 配置选项
 * @returns {Object} 异步状态对象
 */
export function useAsyncState(asyncFn, options = {}) {
  const {
    // 初始数据
    initialData = null,
    // 是否立即执行
    immediate = true,
    // 重试次数
    retryTimes = 0,
    // 重试延迟
    retryDelay = 1000,
    // 超时时间
    timeout = 0,
    // 错误处理函数
    onError = null,
    // 成功处理函数
    onSuccess = null,
  } = options

  const data = ref(initialData)
  const loading = ref(false)
  const error = ref(null)
  const retryCount = ref(0)

  // 执行异步函数
  const execute = async (...args) => {
    loading.value = true
    error.value = null

    try {
      let promise = asyncFn(...args)

      // 添加超时处理
      if (timeout > 0) {
        promise = Promise.race([
          promise,
          new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), timeout)
          }),
        ])
      }

      const result = await promise
      data.value = result
      retryCount.value = 0

      if (onSuccess) {
        onSuccess(result)
      }

      return result
    } catch (err) {
      error.value = err

      // 重试机制
      if (retryCount.value < retryTimes) {
        retryCount.value++
        console.warn(`Async operation failed, retrying (${retryCount.value}/${retryTimes}):`, err)

        await new Promise((resolve) => setTimeout(resolve, retryDelay))
        return execute(...args)
      }

      if (onError) {
        onError(err)
      }

      throw err
    } finally {
      loading.value = false
    }
  }

  // 重置状态
  const reset = () => {
    data.value = initialData
    loading.value = false
    error.value = null
    retryCount.value = 0
  }

  // 立即执行
  if (immediate) {
    execute()
  }

  return {
    data,
    loading,
    error,
    execute,
    reset,
    retryCount,
  }
}

/**
 * 创建列表状态管理
 * @param {Object} options - 配置选项
 * @returns {Object} 列表状态对象
 */
export function useListState(options = {}) {
  const {
    // 初始数据
    initialData = [],
    // 分页大小
    pageSize = 20,
    // 是否启用虚拟滚动
    virtual = false,
    // 排序字段
    defaultSort = null,
    // 过滤函数
    defaultFilter = null,
  } = options

  const items = ref([...initialData])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const sortBy = ref(defaultSort)
  const filterFn = ref(defaultFilter)
  const selectedItems = ref(new Set())

  // 过滤后的数据
  const filteredItems = computed(() => {
    let result = items.value

    if (filterFn.value) {
      result = result.filter(filterFn.value)
    }

    return result
  })

  // 排序后的数据
  const sortedItems = computed(() => {
    if (!sortBy.value) return filteredItems.value

    const { field, order = 'asc' } = sortBy.value

    return [...filteredItems.value].sort((a, b) => {
      const aVal = a[field]
      const bVal = b[field]

      if (aVal < bVal) return order === 'asc' ? -1 : 1
      if (aVal > bVal) return order === 'asc' ? 1 : -1
      return 0
    })
  })

  // 分页数据
  const paginatedItems = computed(() => {
    if (virtual) return sortedItems.value

    const start = (currentPage.value - 1) * pageSize
    const end = start + pageSize
    return sortedItems.value.slice(start, end)
  })

  // 总页数
  const totalPages = computed(() => {
    return Math.ceil(filteredItems.value.length / pageSize)
  })

  // 添加项目
  const addItem = (item) => {
    items.value.push(item)
    total.value = items.value.length
  }

  // 添加多个项目
  const addItems = (newItems) => {
    items.value.push(...newItems)
    total.value = items.value.length
  }

  // 更新项目
  const updateItem = (index, item) => {
    if (index >= 0 && index < items.value.length) {
      items.value[index] = item
    }
  }

  // 删除项目
  const removeItem = (index) => {
    if (index >= 0 && index < items.value.length) {
      items.value.splice(index, 1)
      total.value = items.value.length
    }
  }

  // 批量删除
  const removeItems = (indices) => {
    // 从大到小排序，避免索引变化
    const sortedIndices = [...indices].sort((a, b) => b - a)
    sortedIndices.forEach((index) => removeItem(index))
  }

  // 清空列表
  const clear = () => {
    items.value = []
    total.value = 0
    selectedItems.value.clear()
    currentPage.value = 1
  }

  // 设置排序
  const setSort = (field, order = 'asc') => {
    sortBy.value = { field, order }
  }

  // 设置过滤
  const setFilter = (fn) => {
    filterFn.value = fn
    currentPage.value = 1 // 重置到第一页
  }

  // 切换页面
  const setPage = (page) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  // 选择项目
  const selectItem = (index) => {
    selectedItems.value.add(index)
  }

  // 取消选择项目
  const deselectItem = (index) => {
    selectedItems.value.delete(index)
  }

  // 切换选择状态
  const toggleSelect = (index) => {
    if (selectedItems.value.has(index)) {
      deselectItem(index)
    } else {
      selectItem(index)
    }
  }

  // 全选
  const selectAll = () => {
    paginatedItems.value.forEach((_, index) => {
      const actualIndex = virtual ? index : (currentPage.value - 1) * pageSize + index
      selectedItems.value.add(actualIndex)
    })
  }

  // 取消全选
  const deselectAll = () => {
    selectedItems.value.clear()
  }

  // 获取选中的项目
  const getSelectedItems = () => {
    return Array.from(selectedItems.value)
      .map((index) => items.value[index])
      .filter(Boolean)
  }

  return {
    // 数据
    items,
    filteredItems,
    sortedItems,
    paginatedItems,

    // 状态
    loading,
    total,
    currentPage,
    totalPages,
    selectedItems,

    // 操作方法
    addItem,
    addItems,
    updateItem,
    removeItem,
    removeItems,
    clear,

    // 排序和过滤
    setSort,
    setFilter,

    // 分页
    setPage,

    // 选择
    selectItem,
    deselectItem,
    toggleSelect,
    selectAll,
    deselectAll,
    getSelectedItems,
  }
}

/**
 * 创建表单状态管理
 * @param {Object} initialValues - 初始值
 * @param {Object} options - 配置选项
 * @returns {Object} 表单状态对象
 */
export function useFormState(initialValues = {}, options = {}) {
  const {
    // 验证规则
    rules = {},
    // 验证模式
    validateMode = 'onChange', // 'onChange' | 'onBlur' | 'onSubmit'
    // 是否重置脏状态
    resetDirtyOnSubmit = true,
  } = options

  const values = ref({ ...initialValues })
  const errors = ref({})
  const touched = ref({})
  const dirty = ref(false)
  const submitting = ref(false)

  // 是否有效
  const isValid = computed(() => {
    return Object.keys(errors.value).length === 0
  })

  // 是否已修改
  const isDirty = computed(() => {
    return dirty.value || Object.keys(touched.value).length > 0
  })

  // 设置字段值
  const setFieldValue = (field, value) => {
    values.value[field] = value
    touched.value[field] = true
    dirty.value = true

    if (validateMode === 'onChange') {
      validateField(field)
    }
  }

  // 设置字段错误
  const setFieldError = (field, error) => {
    if (error) {
      errors.value[field] = error
    } else {
      delete errors.value[field]
    }
  }

  // 验证字段
  const validateField = (field) => {
    const rule = rules[field]
    if (!rule) return true

    const value = values.value[field]
    let error = null

    if (typeof rule === 'function') {
      error = rule(value, values.value)
    } else if (rule.required && (!value || value === '')) {
      error = rule.message || `${field} is required`
    } else if (rule.pattern && !rule.pattern.test(value)) {
      error = rule.message || `${field} format is invalid`
    } else if (rule.min && value.length < rule.min) {
      error = rule.message || `${field} must be at least ${rule.min} characters`
    } else if (rule.max && value.length > rule.max) {
      error = rule.message || `${field} must be no more than ${rule.max} characters`
    }

    setFieldError(field, error)
    return !error
  }

  // 验证所有字段
  const validateForm = () => {
    let isFormValid = true

    Object.keys(rules).forEach((field) => {
      const isFieldValid = validateField(field)
      if (!isFieldValid) {
        isFormValid = false
      }
    })

    return isFormValid
  }

  // 处理字段失焦
  const handleBlur = (field) => {
    touched.value[field] = true

    if (validateMode === 'onBlur') {
      validateField(field)
    }
  }

  // 提交表单
  const handleSubmit = async (onSubmit) => {
    submitting.value = true

    try {
      // 验证表单
      const isFormValid = validateForm()
      if (!isFormValid) {
        throw new Error('Form validation failed')
      }

      // 执行提交
      await onSubmit(values.value)

      // 重置脏状态
      if (resetDirtyOnSubmit) {
        dirty.value = false
        touched.value = {}
      }
    } finally {
      submitting.value = false
    }
  }

  // 重置表单
  const resetForm = () => {
    values.value = { ...initialValues }
    errors.value = {}
    touched.value = {}
    dirty.value = false
    submitting.value = false
  }

  return {
    // 状态
    values,
    errors,
    touched,
    dirty,
    submitting,
    isValid,
    isDirty,

    // 方法
    setFieldValue,
    setFieldError,
    validateField,
    validateForm,
    handleBlur,
    handleSubmit,
    resetForm,
  }
}

export default {
  useOptimizedState,
  useComputedState,
  useAsyncState,
  useListState,
  useFormState,
}
