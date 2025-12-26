/**
 * 统一主题配置中心
 * 定义标准化的CSS变量和主题预设
 */

// 标准化的设计令牌定义
export const DESIGN_TOKENS = {
  // 主色调系统
  colors: {
    primary: {
      default: '#343434',
      violet: '#8b5cf6',
      blue: '#3b82f6',
      green: '#22c55e',
      orange: '#f97316',
      rose: '#e11d48',
      red: '#dc2626',
      yellow: '#eab308',
    },
    // 语义化颜色
    semantic: {
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
      info: '#1890ff',
    },
    // 中性色系
    neutral: {
      text: {
        primary: '#262626',
        secondary: '#595959',
        disabled: '#bfbfbf',
        inverse: '#ffffff',
      },
      background: {
        base: '#ffffff',
        light: '#fafafa',
        dark: '#f5f5f5',
        elevated: '#ffffff',
      },
      border: {
        base: '#d9d9d9',
        light: '#e8e8e8',
        dark: '#bfbfbf',
      },
    },
  },

  // 间距系统
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },

  // 字体系统
  typography: {
    fontSizes: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  // 边框圆角
  borderRadius: {
    none: '0',
    sm: '2px',
    base: '4px',
    md: '6px',
    lg: '8px',
    xl: '12px',
    full: '9999px',
  },

  // 阴影系统
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
}

// 组件主题配置
export const COMPONENT_THEMES = {
  // 表格组件主题
  table: {
    headerBackground: 'var(--background-light)',
    headerTextColor: 'var(--text-color-primary)',
    rowBackground: 'var(--background-base)',
    rowHoverBackground: 'var(--background-light)',
    borderColor: 'var(--border-color-light)',
    padding: 'var(--spacing-md)',
  },

  // 表单组件主题
  form: {
    labelColor: 'var(--text-color-primary)',
    inputBackground: 'var(--background-base)',
    inputBorderColor: 'var(--border-color-base)',
    inputFocusBorderColor: 'var(--primary-color)',
    spacing: 'var(--spacing-md)',
  },

  // 按钮组件主题
  button: {
    primaryBackground: 'var(--primary-color)',
    primaryTextColor: 'var(--primary-foreground)',
    secondaryBackground: 'var(--secondary)',
    secondaryTextColor: 'var(--secondary-foreground)',
    borderRadius: 'var(--border-radius-base)',
    padding: 'var(--spacing-sm) var(--spacing-md)',
  },

  // 模态框组件主题
  modal: {
    background: 'var(--background-base)',
    headerBackground: 'var(--background-light)',
    borderColor: 'var(--border-color-light)',
    shadow: 'var(--shadow-lg)',
    borderRadius: 'var(--border-radius-lg)',
  },
}

// 主题预设配置
export const THEME_PRESETS = [
  {
    name: '默认',
    key: 'default',
    primaryColor: '#343434',
    description: '经典灰色主题，适合商务场景',
    cssClass: 'theme-default',
  },
  {
    name: '紫色',
    key: 'violet',
    primaryColor: '#8b5cf6',
    description: '优雅紫色主题，现代感强',
    cssClass: 'theme-violet',
  },
  {
    name: '蓝色',
    key: 'blue',
    primaryColor: '#3b82f6',
    description: '经典蓝色主题，专业可靠',
    cssClass: 'theme-blue',
  },
  {
    name: '绿色',
    key: 'green',
    primaryColor: '#22c55e',
    description: '清新绿色主题，自然舒适',
    cssClass: 'theme-green',
  },
  {
    name: '橙色',
    key: 'orange',
    primaryColor: '#f97316',
    description: '活力橙色主题，温暖友好',
    cssClass: 'theme-orange',
  },
  {
    name: '玫瑰色',
    key: 'rose',
    primaryColor: '#e11d48',
    description: '浪漫玫瑰主题，优雅时尚',
    cssClass: 'theme-rose',
  },
  {
    name: '红色',
    key: 'red',
    primaryColor: '#dc2626',
    description: '醒目红色主题，强调重点',
    cssClass: 'theme-red',
  },
  {
    name: '黄色',
    key: 'yellow',
    primaryColor: '#eab308',
    description: '明亮黄色主题，活泼阳光',
    cssClass: 'theme-yellow',
  },
]

// CSS变量映射表
export const CSS_VARIABLE_MAPPING = {
  // 主色调变量
  primary: {
    '--primary-color': 'colors.primary',
    '--primary-color-hover': 'colors.primary.hover',
    '--primary-color-pressed': 'colors.primary.pressed',
    '--primary-color-light': 'colors.primary.light',
    '--primary-color-dark': 'colors.primary.dark',
  },

  // 语义化颜色变量
  semantic: {
    '--success-color': 'colors.semantic.success',
    '--warning-color': 'colors.semantic.warning',
    '--error-color': 'colors.semantic.error',
    '--info-color': 'colors.semantic.info',
  },

  // 文本颜色变量
  text: {
    '--text-color-primary': 'colors.neutral.text.primary',
    '--text-color-secondary': 'colors.neutral.text.secondary',
    '--text-color-disabled': 'colors.neutral.text.disabled',
  },

  // 背景颜色变量
  background: {
    '--background-color-base': 'colors.neutral.background.base',
    '--background-color-light': 'colors.neutral.background.light',
    '--background-color-dark': 'colors.neutral.background.dark',
  },

  // 边框颜色变量
  border: {
    '--border-color-base': 'colors.neutral.border.base',
    '--border-color-light': 'colors.neutral.border.light',
    '--border-color-dark': 'colors.neutral.border.dark',
  },

  // 间距变量
  spacing: {
    '--spacing-xs': 'spacing.xs',
    '--spacing-sm': 'spacing.sm',
    '--spacing-md': 'spacing.md',
    '--spacing-lg': 'spacing.lg',
    '--spacing-xl': 'spacing.xl',
    '--spacing-xxl': 'spacing.xxl',
  },

  // 字体变量
  typography: {
    '--font-size-xs': 'typography.fontSizes.xs',
    '--font-size-sm': 'typography.fontSizes.sm',
    '--font-size-base': 'typography.fontSizes.base',
    '--font-size-lg': 'typography.fontSizes.lg',
    '--font-size-xl': 'typography.fontSizes.xl',
    '--font-weight-normal': 'typography.fontWeights.normal',
    '--font-weight-medium': 'typography.fontWeights.medium',
    '--font-weight-semibold': 'typography.fontWeights.semibold',
    '--font-weight-bold': 'typography.fontWeights.bold',
  },

  // 边框圆角变量
  borderRadius: {
    '--border-radius-sm': 'borderRadius.sm',
    '--border-radius-base': 'borderRadius.base',
    '--border-radius-md': 'borderRadius.md',
    '--border-radius-lg': 'borderRadius.lg',
    '--border-radius-xl': 'borderRadius.xl',
  },

  // 阴影变量
  shadows: {
    '--shadow-sm': 'shadows.sm',
    '--shadow-base': 'shadows.base',
    '--shadow-md': 'shadows.md',
    '--shadow-lg': 'shadows.lg',
    '--shadow-xl': 'shadows.xl',
  },
}

// 主题合规性规则
export const THEME_COMPLIANCE_RULES = {
  // 禁止使用的硬编码颜色
  forbiddenColors: [
    '#000000',
    '#ffffff',
    '#ff0000',
    '#00ff00',
    '#0000ff',
    'black',
    'white',
    'red',
    'green',
    'blue',
  ],

  // 必须使用的CSS变量前缀
  requiredVariablePrefixes: [
    '--primary-',
    '--text-color-',
    '--background-color-',
    '--border-color-',
    '--spacing-',
    '--font-size-',
    '--border-radius-',
  ],

  // 组件样式规范
  componentRules: {
    table: {
      requiredClasses: ['standard-table', 'standard-data-table'],
      requiredVariables: ['--background-color-base', '--border-color-light'],
    },
    form: {
      requiredClasses: ['standard-form', 'standard-form-item'],
      requiredVariables: ['--text-color-primary', '--spacing-md'],
    },
    button: {
      requiredClasses: ['standard-button'],
      requiredVariables: ['--primary-color', '--border-radius-base'],
    },
    modal: {
      requiredClasses: ['standard-modal'],
      requiredVariables: ['--background-color-base', '--shadow-lg'],
    },
  },
}

// 导出默认配置
export default {
  DESIGN_TOKENS,
  COMPONENT_THEMES,
  THEME_PRESETS,
  CSS_VARIABLE_MAPPING,
  THEME_COMPLIANCE_RULES,
}
