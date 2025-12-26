/**
 * 导出导入工具
 * Export and import utilities for workflows
 */

// ========== 类型定义 ==========

/** 导出格式 */
type ExportFormatType = 'json' | 'xml' | 'yaml' | 'png' | 'svg' | 'pdf'

/** 导出选项类型 */
type ExportOptionType = 'full' | 'nodes_only' | 'connections_only' | 'selected' | 'template'

/** 导入选项类型 */
type ImportModeType = 'replace' | 'merge' | 'append'

/** 导出选项 */
interface ExportOptions {
  format?: ExportOptionType
  includeMetadata?: boolean
  includeHistory?: boolean
  includeValidation?: boolean
  selectedNodes?: string[]
  selectedConnections?: string[]
  quality?: number
  width?: number
  height?: number
  backgroundColor?: string
  scale?: number
  includeIndex?: boolean
}

/** 导入选项 */
interface ImportOptions {
  mode?: ImportModeType
  validateOnImport?: boolean
  generateNewIds?: boolean
  currentWorkflow?: WorkflowData | null
}

/** 工作流信息 */
interface WorkflowInfo {
  name?: string
  description?: string
  author?: string
  version?: string
  tags?: string[]
  category?: string
  createdAt?: string
  updatedAt?: string
  [key: string]: any
}

/** 工作流数据 */
interface WorkflowData {
  nodes?: any[]
  connections?: any[]
  workflowInfo?: WorkflowInfo
  canvasState?: Record<string, any>
  history?: any[]
  validation?: any
  [key: string]: any
}

/** 导出数据结构 */
interface ExportData {
  version: string
  format: string
  timestamp: string
  metadata?: Record<string, any>
  nodes?: any[]
  connections?: any[]
  canvasState?: Record<string, any>
  history?: any[]
  validation?: any
  template?: {
    nodes: any[]
    connections: any[]
  }
}

/** 导入结果 */
interface ImportResult {
  success: boolean
  data?: WorkflowData
  error?: string
  message: string
}

/** 批量导出结果 */
interface BatchExportResult {
  success: boolean
  data: {
    version: string
    format: string
    timestamp: string
    count: number
    successful: number
    failed: number
    workflows: Array<{
      index: number
      name: string
      data: any
    }>
    index?: Array<{
      name: string
      index: number
    }>
  }
  errors: Array<{
    index: number
    name: string
    error: string
  }>
}

/** 格式信息 */
interface FormatInfo {
  name: string
  description: string
  mimeType: string
  extension: string
}

// ========== 常量定义 ==========

/**
 * 支持的文件格式
 */
export const EXPORT_FORMATS = {
  JSON: 'json' as const,
  XML: 'xml' as const,
  YAML: 'yaml' as const,
  PNG: 'png' as const,
  SVG: 'svg' as const,
  PDF: 'pdf' as const,
}

/**
 * 导出选项
 */
export const EXPORT_OPTIONS = {
  FULL: 'full' as const, // 完整工作流
  NODES_ONLY: 'nodes_only' as const, // 仅节点
  CONNECTIONS_ONLY: 'connections_only' as const, // 仅连接
  SELECTED: 'selected' as const, // 仅选中的元素
  TEMPLATE: 'template' as const, // 模板格式
}

/**
 * 导入选项
 */
export const IMPORT_OPTIONS = {
  REPLACE: 'replace' as const, // 替换当前工作流
  MERGE: 'merge' as const, // 合并到当前工作流
  APPEND: 'append' as const, // 追加到当前工作流
}

// ========== 导出函数 ==========

/**
 * 导出工作流为JSON格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns JSON格式的工作流数据
 */
export function exportToJSON(workflow: WorkflowData, options: ExportOptions = {}): ExportData {
  const {
    format = EXPORT_OPTIONS.FULL,
    includeMetadata = true,
    includeHistory = false,
    includeValidation = false,
    selectedNodes = [],
    selectedConnections = [],
  } = options

  let exportData: ExportData = {
    version: '1.0.0',
    format: 'workflow-json',
    timestamp: new Date().toISOString(),
  }

  if (includeMetadata) {
    exportData.metadata = {
      name: workflow.workflowInfo?.name || 'Untitled Workflow',
      description: workflow.workflowInfo?.description || '',
      author: workflow.workflowInfo?.author || '',
      version: workflow.workflowInfo?.version || '1.0.0',
      tags: workflow.workflowInfo?.tags || [],
      category: workflow.workflowInfo?.category || '',
      createdAt: workflow.workflowInfo?.createdAt || new Date().toISOString(),
      updatedAt: workflow.workflowInfo?.updatedAt || new Date().toISOString(),
    }
  }

  switch (format) {
    case EXPORT_OPTIONS.FULL:
      exportData.nodes = workflow.nodes || []
      exportData.connections = workflow.connections || []
      exportData.canvasState = workflow.canvasState || {}
      break

    case EXPORT_OPTIONS.NODES_ONLY:
      exportData.nodes = workflow.nodes || []
      break

    case EXPORT_OPTIONS.CONNECTIONS_ONLY:
      exportData.connections = workflow.connections || []
      break

    case EXPORT_OPTIONS.SELECTED:
      exportData.nodes = (workflow.nodes || []).filter((node: any) =>
        selectedNodes.includes(node.id)
      )
      exportData.connections = (workflow.connections || []).filter((conn: any) =>
        selectedConnections.includes(conn.id)
      )
      break

    case EXPORT_OPTIONS.TEMPLATE:
      exportData.template = {
        nodes: (workflow.nodes || []).map((node: any) => ({
          type: node.type,
          data: node.data,
          style: node.style,
        })),
        connections: (workflow.connections || []).map((conn: any) => ({
          type: conn.type,
          style: conn.style,
        })),
      }
      break
  }

  if (includeHistory && workflow.history) {
    exportData.history = workflow.history
  }

  if (includeValidation) {
    // 注意：如果 validateWorkflow 函数不存在，这里可能需要调整
    try {
      const { validateWorkflow } = require('./connectionValidator.js')
      const validation = validateWorkflow(workflow.nodes || [], workflow.connections || [])
      exportData.validation = validation
    } catch (error) {
      console.warn('Validation function not available')
    }
  }

  return exportData
}

/**
 * 导出工作流为XML格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns XML格式的工作流数据
 */
export function exportToXML(workflow: WorkflowData, options: ExportOptions = {}): string {
  const jsonData = exportToJSON(workflow, options)
  return jsonToXML(jsonData)
}

/**
 * 导出工作流为YAML格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns YAML格式的工作流数据
 */
export function exportToYAML(workflow: WorkflowData, options: ExportOptions = {}): string {
  const jsonData = exportToJSON(workflow, options)
  return jsonToYAML(jsonData)
}

/**
 * 导出工作流为图片格式
 * @param canvasElement - 画布元素
 * @param options - 导出选项
 * @returns 图片数据URL
 */
export async function exportToImage(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<string> {
  const {
    format = EXPORT_FORMATS.PNG,
    quality = 1.0,
    width,
    height,
    backgroundColor = '#ffffff',
    scale = 1,
  } = options

  return new Promise((resolve, reject) => {
    try {
      // 创建临时canvas
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        throw new Error('无法获取Canvas上下文')
      }

      // 设置画布尺寸
      const rect = canvasElement.getBoundingClientRect()
      canvas.width = (width || rect.width) * scale
      canvas.height = (height || rect.height) * scale

      // 设置背景色
      ctx.fillStyle = backgroundColor
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 使用html2canvas或类似库来捕获DOM元素
      // 这里简化处理，实际项目中需要引入相应的库
      if ((window as any).html2canvas) {
        ;(window as any)
          .html2canvas(canvasElement, {
            canvas: canvas,
            scale: scale,
            backgroundColor: backgroundColor,
            useCORS: true,
          })
          .then((canvas: HTMLCanvasElement) => {
            const dataURL = canvas.toDataURL(`image/${format}`, quality)
            resolve(dataURL)
          })
          .catch(reject)
      } else {
        // 备用方案：使用SVG
        const svgData = exportToSVG(canvasElement, options)
        const img = new Image()
        img.onload = () => {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
          const dataURL = canvas.toDataURL(`image/${format}`, quality)
          resolve(dataURL)
        }
        img.onerror = reject
        img.src = 'data:image/svg+xml;base64,' + btoa(svgData)
      }
    } catch (error: any) {
      reject(error)
    }
  })
}

/**
 * 导出工作流为SVG格式
 * @param canvasElement - 画布元素
 * @param options - 导出选项
 * @returns SVG字符串
 */
export function exportToSVG(canvasElement: HTMLElement, options: ExportOptions = {}): string {
  const { width, height, backgroundColor = '#ffffff' } = options

  const rect = canvasElement.getBoundingClientRect()
  const svgWidth = width || rect.width
  const svgHeight = height || rect.height

  // 创建SVG元素
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', String(svgWidth))
  svg.setAttribute('height', String(svgHeight))
  svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`)
  svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  // 添加背景
  const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  background.setAttribute('width', '100%')
  background.setAttribute('height', '100%')
  background.setAttribute('fill', backgroundColor)
  svg.appendChild(background)

  // 转换DOM元素为SVG
  const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
  foreignObject.setAttribute('width', '100%')
  foreignObject.setAttribute('height', '100%')

  const clonedElement = canvasElement.cloneNode(true) as HTMLElement
  foreignObject.appendChild(clonedElement)
  svg.appendChild(foreignObject)

  return new XMLSerializer().serializeToString(svg)
}

// ========== 导入函数 ==========

/**
 * 从JSON数据导入工作流
 * @param jsonData - JSON数据
 * @param options - 导入选项
 * @returns 导入结果
 */
export function importFromJSON(
  jsonData: ExportData | string,
  options: ImportOptions = {}
): ImportResult {
  const {
    mode = IMPORT_OPTIONS.REPLACE,
    validateOnImport = true,
    generateNewIds = false,
    currentWorkflow = null,
  } = options

  try {
    // 解析JSON数据
    const data: ExportData = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData

    // 验证数据格式
    if (!isValidWorkflowData(data)) {
      throw new Error('Invalid workflow data format')
    }

    // 处理节点ID
    let nodes = data.nodes || []
    let connections = data.connections || []

    if (generateNewIds) {
      const idMap = new Map<string, string>()

      // 为节点生成新ID
      nodes = nodes.map((node: any) => {
        const newId = generateId()
        idMap.set(node.id, newId)
        return { ...node, id: newId }
      })

      // 更新连接中的节点ID引用
      connections = connections.map((conn: any) => ({
        ...conn,
        id: generateId(),
        fromNodeId: idMap.get(conn.fromNodeId) || conn.fromNodeId,
        toNodeId: idMap.get(conn.toNodeId) || conn.toNodeId,
      }))
    }

    // 根据导入模式处理数据
    let result: WorkflowData = {
      nodes: [],
      connections: [],
      workflowInfo: data.metadata || {},
      canvasState: data.canvasState || {},
    }

    switch (mode) {
      case IMPORT_OPTIONS.REPLACE:
        result.nodes = nodes
        result.connections = connections
        break

      case IMPORT_OPTIONS.MERGE:
        if (currentWorkflow) {
          result.nodes = mergeNodes(currentWorkflow.nodes || [], nodes)
          result.connections = mergeConnections(currentWorkflow.connections || [], connections)
        } else {
          result.nodes = nodes
          result.connections = connections
        }
        break

      case IMPORT_OPTIONS.APPEND:
        if (currentWorkflow) {
          result.nodes = [...(currentWorkflow.nodes || []), ...nodes]
          result.connections = [...(currentWorkflow.connections || []), ...connections]
        } else {
          result.nodes = nodes
          result.connections = connections
        }
        break
    }

    // 验证导入的工作流
    if (validateOnImport) {
      try {
        const { validateWorkflow } = require('./connectionValidator.js')
        const validation = validateWorkflow(result.nodes || [], result.connections || [])
        if (validation.errors && validation.errors.length > 0) {
          console.warn('Imported workflow has validation errors:', validation.errors)
        }
        result.validation = validation
      } catch (error) {
        console.warn('Validation function not available')
      }
    }

    return {
      success: true,
      data: result,
      message: 'Workflow imported successfully',
    }
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      message: 'Failed to import workflow',
    }
  }
}

/**
 * 从XML数据导入工作流
 * @param xmlData - XML数据
 * @param options - 导入选项
 * @returns 导入结果
 */
export function importFromXML(xmlData: string, options: ImportOptions = {}): ImportResult {
  try {
    const jsonData = xmlToJSON(xmlData)
    return importFromJSON(jsonData, options)
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      message: 'Failed to import XML workflow',
    }
  }
}

/**
 * 从YAML数据导入工作流
 * @param yamlData - YAML数据
 * @param options - 导入选项
 * @returns 导入结果
 */
export function importFromYAML(yamlData: string, options: ImportOptions = {}): ImportResult {
  try {
    const jsonData = yamlToJSON(yamlData)
    return importFromJSON(jsonData, options)
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      message: 'Failed to import YAML workflow',
    }
  }
}

// ========== 文件操作 ==========

/**
 * 下载文件
 * @param content - 文件内容
 * @param filename - 文件名
 * @param mimeType - MIME类型
 */
export function downloadFile(
  content: string | Blob,
  filename: string,
  mimeType: string = 'application/json'
): void {
  const blob = typeof content === 'string' ? new Blob([content], { type: mimeType }) : content
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * 读取文件
 * @param file - 文件对象
 * @returns 文件内容
 */
export function readFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (event) => {
      resolve(event.target?.result as string)
    }

    reader.onerror = (error) => {
      reject(error)
    }

    reader.readAsText(file)
  })
}

/**
 * 批量导出工作流
 * @param workflows - 工作流数组
 * @param options - 导出选项
 * @returns 批量导出结果
 */
export function batchExport(
  workflows: WorkflowData[],
  options: ExportOptions = {}
): BatchExportResult {
  const { format = EXPORT_FORMATS.JSON, includeIndex = true } = options

  const results: Array<{ index: number; name: string; data: any }> = []
  const errors: Array<{ index: number; name: string; error: string }> = []

  workflows.forEach((workflow, index) => {
    try {
      let exportData: any

      switch (format) {
        case EXPORT_FORMATS.JSON:
          exportData = exportToJSON(workflow, options)
          break
        case EXPORT_FORMATS.XML:
          exportData = exportToXML(workflow, options)
          break
        case EXPORT_FORMATS.YAML:
          exportData = exportToYAML(workflow, options)
          break
        default:
          throw new Error(`Unsupported format: ${format}`)
      }

      results.push({
        index,
        name: workflow.workflowInfo?.name || `Workflow ${index + 1}`,
        data: exportData,
      })
    } catch (error: any) {
      errors.push({
        index,
        name: workflow.workflowInfo?.name || `Workflow ${index + 1}`,
        error: error.message,
      })
    }
  })

  const batchData: BatchExportResult['data'] = {
    version: '1.0.0',
    format: `batch-${format}`,
    timestamp: new Date().toISOString(),
    count: workflows.length,
    successful: results.length,
    failed: errors.length,
    workflows: results,
  }

  if (includeIndex) {
    batchData.index = results.map((result) => ({
      name: result.name,
      index: result.index,
    }))
  }

  return {
    success: errors.length === 0,
    data: batchData,
    errors,
  }
}

// ========== 辅助函数 ==========

/**
 * 验证工作流数据格式
 */
function isValidWorkflowData(data: any): boolean {
  if (!data || typeof data !== 'object') {
    return false
  }

  // 检查必要的字段
  if (!data.nodes && !data.connections && !data.template) {
    return false
  }

  // 验证节点格式
  if (data.nodes && !Array.isArray(data.nodes)) {
    return false
  }

  // 验证连接格式
  if (data.connections && !Array.isArray(data.connections)) {
    return false
  }

  return true
}

/**
 * 合并节点
 */
function mergeNodes(existingNodes: any[], newNodes: any[]): any[] {
  const nodeMap = new Map(existingNodes.map((node) => [node.id, node]))

  newNodes.forEach((node) => {
    if (nodeMap.has(node.id)) {
      // 更新现有节点
      nodeMap.set(node.id, { ...nodeMap.get(node.id), ...node })
    } else {
      // 添加新节点
      nodeMap.set(node.id, node)
    }
  })

  return Array.from(nodeMap.values())
}

/**
 * 合并连接
 */
function mergeConnections(existingConnections: any[], newConnections: any[]): any[] {
  const connectionMap = new Map(existingConnections.map((conn) => [conn.id, conn]))

  newConnections.forEach((conn) => {
    if (connectionMap.has(conn.id)) {
      // 更新现有连接
      connectionMap.set(conn.id, { ...connectionMap.get(conn.id), ...conn })
    } else {
      // 添加新连接
      connectionMap.set(conn.id, conn)
    }
  })

  return Array.from(connectionMap.values())
}

/**
 * JSON转XML
 */
function jsonToXML(obj: any, rootName: string = 'workflow'): string {
  function objectToXML(obj: any, name: string): string {
    if (obj === null || obj === undefined) {
      return `<${name}/>`
    }

    if (typeof obj !== 'object') {
      return `<${name}>${escapeXML(String(obj))}</${name}>`
    }

    if (Array.isArray(obj)) {
      return obj.map((item) => objectToXML(item, name.slice(0, -1))).join('')
    }

    const children = Object.keys(obj)
      .map((key) => {
        return objectToXML(obj[key], key)
      })
      .join('')

    return `<${name}>${children}</${name}>`
  }

  return `<?xml version="1.0" encoding="UTF-8"?>${objectToXML(obj, rootName)}`
}

/**
 * XML转JSON
 */
function xmlToJSON(xmlString: string): any {
  // 简化的XML解析，实际项目中建议使用专门的XML解析库
  const parser = new DOMParser()
  const xmlDoc = parser.parseFromString(xmlString, 'text/xml')

  function xmlNodeToObject(node: Node): any {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent?.trim()
    }

    const obj: any = {}
    const element = node as Element

    // 处理属性
    if (element.attributes) {
      for (let i = 0; i < element.attributes.length; i++) {
        const attr = element.attributes[i]
        obj[`@${attr.name}`] = attr.value
      }
    }

    // 处理子节点
    const children = Array.from(node.childNodes)
    const textContent = children
      .filter((child) => child.nodeType === Node.TEXT_NODE)
      .map((child) => child.textContent?.trim())
      .join('')

    if (textContent && children.length === 1) {
      return textContent
    }

    children.forEach((child) => {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const childObj = xmlNodeToObject(child)
        const childElement = child as Element
        if (obj[childElement.nodeName]) {
          if (!Array.isArray(obj[childElement.nodeName])) {
            obj[childElement.nodeName] = [obj[childElement.nodeName]]
          }
          obj[childElement.nodeName].push(childObj)
        } else {
          obj[childElement.nodeName] = childObj
        }
      }
    })

    return obj
  }

  return xmlNodeToObject(xmlDoc.documentElement)
}

/**
 * JSON转YAML
 */
function jsonToYAML(obj: any, indent: number = 0): string {
  const spaces = '  '.repeat(indent)

  if (obj === null || obj === undefined) {
    return 'null'
  }

  if (typeof obj === 'string') {
    return obj.includes('\n')
      ? `|\n${obj
          .split('\n')
          .map((line) => spaces + '  ' + line)
          .join('\n')}`
      : `"${obj}"`
  }

  if (typeof obj === 'number' || typeof obj === 'boolean') {
    return String(obj)
  }

  if (Array.isArray(obj)) {
    if (obj.length === 0) return '[]'
    return (
      '\n' +
      obj
        .map((item) => `${spaces}- ${jsonToYAML(item, indent + 1).replace(/^\s+/, '')}`)
        .join('\n')
    )
  }

  if (typeof obj === 'object') {
    const keys = Object.keys(obj)
    if (keys.length === 0) return '{}'
    return (
      '\n' +
      keys
        .map((key) => {
          const value = jsonToYAML(obj[key], indent + 1)
          return `${spaces}${key}:${value.startsWith('\n') ? value : ' ' + value}`
        })
        .join('\n')
    )
  }

  return String(obj)
}

/**
 * YAML转JSON
 */
function yamlToJSON(yamlString: string): any {
  // 简化的YAML解析，实际项目中建议使用专门的YAML解析库如js-yaml
  const lines = yamlString.split('\n')
  const result: any = {}
  const stack = [result]
  let currentIndent = 0

  lines.forEach((line) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return

    const indent = line.length - line.trimStart().length
    const colonIndex = trimmed.indexOf(':')

    if (colonIndex === -1) return

    const key = trimmed.substring(0, colonIndex).trim()
    const value = trimmed.substring(colonIndex + 1).trim()

    // 简化处理，仅支持基本的键值对
    if (value) {
      if (value === 'true') {
        result[key] = true
      } else if (value === 'false') {
        result[key] = false
      } else if (!isNaN(Number(value))) {
        result[key] = Number(value)
      } else {
        result[key] = value.replace(/^["']|["']$/g, '')
      }
    } else {
      result[key] = {}
    }
  })

  return result
}

/**
 * 转义XML特殊字符
 */
function escapeXML(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/**
 * 生成唯一ID
 */
function generateId(): string {
  return 'node_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// ========== 公开工具函数 ==========

/**
 * 创建导出文件名
 * @param workflow - 工作流数据
 * @param format - 文件格式
 * @returns 文件名
 */
export function createExportFilename(workflow: WorkflowData, format: string): string {
  const name = workflow.workflowInfo?.name || 'workflow'
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
  const extension = format.toLowerCase()

  return `${name}_${timestamp}.${extension}`
}

/**
 * 获取文件格式信息
 * @param format - 文件格式
 * @returns 格式信息
 */
export function getFormatInfo(format: string): FormatInfo {
  const formatMap: Record<string, FormatInfo> = {
    [EXPORT_FORMATS.JSON]: {
      name: 'JSON',
      description: 'JavaScript Object Notation',
      mimeType: 'application/json',
      extension: 'json',
    },
    [EXPORT_FORMATS.XML]: {
      name: 'XML',
      description: 'Extensible Markup Language',
      mimeType: 'application/xml',
      extension: 'xml',
    },
    [EXPORT_FORMATS.YAML]: {
      name: 'YAML',
      description: "YAML Ain't Markup Language",
      mimeType: 'application/x-yaml',
      extension: 'yaml',
    },
    [EXPORT_FORMATS.PNG]: {
      name: 'PNG',
      description: 'Portable Network Graphics',
      mimeType: 'image/png',
      extension: 'png',
    },
    [EXPORT_FORMATS.SVG]: {
      name: 'SVG',
      description: 'Scalable Vector Graphics',
      mimeType: 'image/svg+xml',
      extension: 'svg',
    },
    [EXPORT_FORMATS.PDF]: {
      name: 'PDF',
      description: 'Portable Document Format',
      mimeType: 'application/pdf',
      extension: 'pdf',
    },
  }

  return formatMap[format] || formatMap[EXPORT_FORMATS.JSON]
}

// ========== 导出类型 ==========

export type {
  ExportFormatType,
  ExportOptionType,
  ImportModeType,
  ExportOptions,
  ImportOptions,
  WorkflowInfo,
  WorkflowData,
  ExportData,
  ImportResult,
  BatchExportResult,
  FormatInfo,
}

