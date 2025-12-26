import { ref, computed, onMounted, onUnmounted, type Ref, type ComputedRef } from 'vue'

// ==================== 类型定义 ====================

/** 设备类型 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop' | 'large'

/** 屏幕尺寸 */
export type ScreenSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

/** 布局类型 */
export type LayoutType = 'vertical' | 'horizontal'

/** 断点配置 */
export interface Breakpoints {
  xs: number
  sm: number
  md: number
  lg: number
  xl: number
}

/** 分页配置 */
interface PaginationConfig {
  pageSize: number
  showSizePicker: boolean
  showQuickJumper: boolean
  simple: boolean
}

/** 列配置 */
interface ColumnConfig {
  maxVisible: number
  priority: string[]
}

/** 表格配置 */
export interface TableConfig {
  size: 'small' | 'medium' | 'large'
  scrollX: number
  pagination: PaginationConfig
  columns: ColumnConfig
}

/** 布局配置 */
interface LayoutConfig {
  columns: number
  gap: string
}

/** 模态框配置 */
interface ModalConfig {
  width: string
  maxWidth: string
}

/** 表单配置 */
export interface FormConfig {
  labelPlacement: 'top' | 'left'
  labelWidth: 'auto' | number
  size: 'small' | 'medium' | 'large'
  layout: LayoutConfig
  modal: ModalConfig
}

/** 搜索配置 */
export interface SearchConfig {
  layout: LayoutType
  itemsPerRow: number
  showAdvancedByDefault: boolean
  compactMode: boolean
}

/** 卡片配置 */
export interface CardConfig {
  columns: number
  size: 'small' | 'medium' | 'large'
  showFullContent: boolean
}

/** 工具栏配置 */
export interface ToolbarConfig {
  layout: LayoutType
  showLabels: boolean
  groupActions: boolean
  size: 'small' | 'medium' | 'large'
}

/** 响应式类 */
export interface ResponsiveClasses {
  'is-mobile': boolean
  'is-tablet': boolean
  'is-desktop': boolean
  'is-large-screen': boolean
  [key: string]: boolean
}

/** 容器样式 */
export interface ContainerStyle {
  padding: string
  margin: string
}

/** 表格列定义 */
export interface TableColumn {
  key: string
  configurable?: boolean
  [key: string]: any
}

// ==================== Composable ====================

export function useResponsiveLayout() {
  const windowWidth: Ref<number> = ref(window.innerWidth)
  const windowHeight: Ref<number> = ref(window.innerHeight)

  // 断点定义
  const breakpoints: Breakpoints = {
    xs: 480,
    sm: 768,
    md: 992,
    lg: 1200,
    xl: 1600,
  }

  // 响应式状态
  const isMobile: ComputedRef<boolean> = computed(() => windowWidth.value < breakpoints.sm)
  const isTablet: ComputedRef<boolean> = computed(
    () => windowWidth.value >= breakpoints.sm && windowWidth.value < breakpoints.md
  )
  const isDesktop: ComputedRef<boolean> = computed(() => windowWidth.value >= breakpoints.md)
  const isLargeScreen: ComputedRef<boolean> = computed(() => windowWidth.value >= breakpoints.xl)

  // 设备类型
  const deviceType: ComputedRef<DeviceType> = computed(() => {
    if (windowWidth.value < breakpoints.sm) return 'mobile'
    if (windowWidth.value < breakpoints.md) return 'tablet'
    if (windowWidth.value < breakpoints.xl) return 'desktop'
    return 'large'
  })

  // 屏幕尺寸类别
  const screenSize: ComputedRef<ScreenSize> = computed(() => {
    if (windowWidth.value < breakpoints.xs) return 'xs'
    if (windowWidth.value < breakpoints.sm) return 'sm'
    if (windowWidth.value < breakpoints.md) return 'md'
    if (windowWidth.value < breakpoints.lg) return 'lg'
    return 'xl'
  })

  // 表格配置
  const tableConfig: ComputedRef<TableConfig> = computed(() => {
    if (isMobile.value) {
      return {
        size: 'small',
        scrollX: 800,
        pagination: {
          pageSize: 10,
          showSizePicker: false,
          showQuickJumper: false,
          simple: true,
        },
        columns: {
          maxVisible: 4,
          priority: ['device_number', 'applicant', 'is_fault', 'actions'],
        },
      }
    }

    if (isTablet.value) {
      return {
        size: 'small',
        scrollX: 1200,
        pagination: {
          pageSize: 15,
          showSizePicker: true,
          showQuickJumper: false,
          simple: false,
        },
        columns: {
          maxVisible: 8,
          priority: [
            'device_number',
            'brand',
            'applicant',
            'company',
            'is_fault',
            'fault_content',
            'repairer',
            'actions',
          ],
        },
      }
    }

    return {
      size: 'medium',
      scrollX: 2000,
      pagination: {
        pageSize: 20,
        showSizePicker: true,
        showQuickJumper: true,
        simple: false,
      },
      columns: {
        maxVisible: -1, // 显示所有列
        priority: [],
      },
    }
  })

  // 表单配置
  const formConfig: ComputedRef<FormConfig> = computed(() => {
    if (isMobile.value) {
      return {
        labelPlacement: 'top',
        labelWidth: 'auto',
        size: 'medium',
        layout: {
          columns: 1,
          gap: '12px',
        },
        modal: {
          width: '95%',
          maxWidth: '400px',
        },
      }
    }

    if (isTablet.value) {
      return {
        labelPlacement: 'left',
        labelWidth: 100,
        size: 'medium',
        layout: {
          columns: 2,
          gap: '16px',
        },
        modal: {
          width: '90%',
          maxWidth: '800px',
        },
      }
    }

    return {
      labelPlacement: 'left',
      labelWidth: 120,
      size: 'medium',
      layout: {
        columns: 3,
        gap: '16px',
      },
      modal: {
        width: '90%',
        maxWidth: '1200px',
      },
    }
  })

  // 搜索配置
  const searchConfig: ComputedRef<SearchConfig> = computed(() => {
    if (isMobile.value) {
      return {
        layout: 'vertical',
        itemsPerRow: 1,
        showAdvancedByDefault: false,
        compactMode: true,
      }
    }

    if (isTablet.value) {
      return {
        layout: 'horizontal',
        itemsPerRow: 2,
        showAdvancedByDefault: false,
        compactMode: false,
      }
    }

    return {
      layout: 'horizontal',
      itemsPerRow: 4,
      showAdvancedByDefault: false,
      compactMode: false,
    }
  })

  // 卡片视图配置
  const cardConfig: ComputedRef<CardConfig> = computed(() => {
    if (isMobile.value) {
      return {
        columns: 1,
        size: 'small',
        showFullContent: false,
      }
    }

    if (isTablet.value) {
      return {
        columns: 2,
        size: 'medium',
        showFullContent: true,
      }
    }

    return {
      columns: 3,
      size: 'medium',
      showFullContent: true,
    }
  })

  // 工具栏配置
  const toolbarConfig: ComputedRef<ToolbarConfig> = computed(() => {
    if (isMobile.value) {
      return {
        layout: 'vertical',
        showLabels: false,
        groupActions: true,
        size: 'small',
      }
    }

    return {
      layout: 'horizontal',
      showLabels: true,
      groupActions: false,
      size: 'medium',
    }
  })

  /**
   * 更新窗口尺寸
   */
  const updateWindowSize = (): void => {
    windowWidth.value = window.innerWidth
    windowHeight.value = window.innerHeight
  }

  /**
   * 获取优化的列配置
   * @param allColumns - 所有列配置
   * @returns 优化后的列配置
   */
  const getOptimizedColumns = (allColumns: TableColumn[]): TableColumn[] => {
    const config = tableConfig.value.columns

    if (config.maxVisible === -1) {
      return allColumns
    }

    // 按优先级筛选列
    const priorityColumns = allColumns.filter(
      (col) => config.priority.includes(col.key) || !col.configurable
    )

    // 如果优先级列数量超过最大显示数量，则截取
    if (priorityColumns.length > config.maxVisible) {
      return priorityColumns.slice(0, config.maxVisible)
    }

    // 如果优先级列不足，则添加其他列
    const remainingSlots = config.maxVisible - priorityColumns.length
    const otherColumns = allColumns
      .filter((col) => !config.priority.includes(col.key) && col.configurable)
      .slice(0, remainingSlots)

    return [...priorityColumns, ...otherColumns]
  }

  /**
   * 获取响应式样式类
   * @returns 响应式CSS类对象
   */
  const getResponsiveClasses = (): ResponsiveClasses => {
    return {
      'is-mobile': isMobile.value,
      'is-tablet': isTablet.value,
      'is-desktop': isDesktop.value,
      'is-large-screen': isLargeScreen.value,
      [`screen-${screenSize.value}`]: true,
      [`device-${deviceType.value}`]: true,
    }
  }

  /**
   * 获取容器样式
   * @returns 容器样式对象
   */
  const getContainerStyle = (): ContainerStyle => {
    if (isMobile.value) {
      return {
        padding: '8px',
        margin: '0',
      }
    }

    if (isTablet.value) {
      return {
        padding: '12px',
        margin: '0 8px',
      }
    }

    return {
      padding: '16px',
      margin: '0 16px',
    }
  }

  /**
   * 检查是否支持触摸
   */
  const isTouchDevice: ComputedRef<boolean> = computed(() => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
  })

  /**
   * 获取最佳输入尺寸
   * @returns 输入框尺寸
   */
  const getOptimalInputSize = (): 'small' | 'medium' | 'large' => {
    if (isMobile.value) return 'large'
    if (isTablet.value) return 'medium'
    return 'medium'
  }

  // 生命周期
  onMounted(() => {
    window.addEventListener('resize', updateWindowSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateWindowSize)
  })

  return {
    // 响应式状态
    windowWidth,
    windowHeight,
    isMobile,
    isTablet,
    isDesktop,
    isLargeScreen,
    deviceType,
    screenSize,
    isTouchDevice,

    // 配置对象
    tableConfig,
    formConfig,
    searchConfig,
    cardConfig,
    toolbarConfig,

    // 方法
    getOptimizedColumns,
    getResponsiveClasses,
    getContainerStyle,
    getOptimalInputSize,
    updateWindowSize,

    // 断点
    breakpoints,
  }
}

