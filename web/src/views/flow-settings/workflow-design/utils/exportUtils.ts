/**
 * 导入导出工具函数
 * Import/Export utilities
 */

// ========== 类型定义 ==========

/** 导出格式 */
export type ExportFormat = 'json' | 'xml' | 'yaml' | 'png' | 'svg' | 'pdf' | 'bpmn' | 'workflow'

/** 导出选项 */
interface ExportOptions {
  includeMetadata?: boolean
  includeHistory?: boolean
  includeComments?: boolean
  includeValidation?: boolean
  compression?: boolean
  prettyFormat?: boolean
  imageQuality?: number
  imageScale?: number
  backgroundColor?: string
  includeGrid?: boolean
  includeWatermark?: boolean
}

/** 导入选项 */
interface ImportOptions {
  generateNewIds?: boolean
  validateStructure?: boolean
  mergeMode?: boolean
}

/** 工作流数据 */
interface WorkflowData {
  id?: string
  name?: string
  description?: string
  nodes?: any[]
  connections?: any[]
  settings?: Record<string, any>
  creator?: string
  createdAt?: string
  updatedAt?: string
  version?: string
  tags?: string[]
  history?: any[]
  comments?: any[]
  validation?: any
  [key: string]: any
}

/** 导出数据结构 */
interface ExportData {
  version: string
  format: string
  exportTime: string
  workflow: WorkflowData
  metadata?: Record<string, any>
  history?: any[]
  comments?: any[]
  validation?: any
}

// ========== 常量定义 ==========

/**
 * 支持的导出格式
 */
export const EXPORT_FORMATS = {
  JSON: 'json' as const,
  XML: 'xml' as const,
  YAML: 'yaml' as const,
  PNG: 'png' as const,
  SVG: 'svg' as const,
  PDF: 'pdf' as const,
  BPMN: 'bpmn' as const,
  WORKFLOW: 'workflow' as const,
}

/**
 * 导出选项默认配置
 */
export const DEFAULT_EXPORT_OPTIONS: Required<ExportOptions> = {
  includeMetadata: true,
  includeHistory: false,
  includeComments: true,
  includeValidation: false,
  compression: false,
  prettyFormat: true,
  imageQuality: 0.9,
  imageScale: 1.0,
  backgroundColor: '#ffffff',
  includeGrid: false,
  includeWatermark: false,
}

// ========== 导出函数 ==========

/**
 * 导出工作流为JSON格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns JSON字符串
 */
export function exportToJSON(workflow: WorkflowData, options: ExportOptions = {}): string {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    const exportData = prepareWorkflowData(workflow, opts)

    if (opts.prettyFormat) {
      return JSON.stringify(exportData, null, 2)
    } else {
      return JSON.stringify(exportData)
    }
  } catch (error: any) {
    throw new Error(`JSON导出失败: ${error.message}`)
  }
}

/**
 * 导出工作流为XML格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns XML字符串
 */
export function exportToXML(workflow: WorkflowData, options: ExportOptions = {}): string {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    const exportData = prepareWorkflowData(workflow, opts)
    return convertToXML(exportData, opts)
  } catch (error: any) {
    throw new Error(`XML导出失败: ${error.message}`)
  }
}

/**
 * 导出工作流为YAML格式
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns YAML字符串
 */
export function exportToYAML(workflow: WorkflowData, options: ExportOptions = {}): string {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    const exportData = prepareWorkflowData(workflow, opts)
    return convertToYAML(exportData, opts)
  } catch (error: any) {
    throw new Error(`YAML导出失败: ${error.message}`)
  }
}

/**
 * 导出工作流为图片格式
 * @param canvasElement - 画布元素
 * @param format - 图片格式 (png, svg)
 * @param options - 导出选项
 * @returns 图片Blob
 */
export async function exportToImage(
  canvasElement: HTMLElement,
  format: ExportFormat = EXPORT_FORMATS.PNG,
  options: ExportOptions = {}
): Promise<Blob> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    if (format === EXPORT_FORMATS.SVG) {
      return await exportToSVG(canvasElement, opts)
    } else if (format === EXPORT_FORMATS.PNG) {
      return await exportToPNG(canvasElement, opts)
    } else {
      throw new Error(`不支持的图片格式: ${format}`)
    }
  } catch (error: any) {
    throw new Error(`图片导出失败: ${error.message}`)
  }
}

/**
 * 导出为PNG格式
 * @param canvasElement - 画布元素
 * @param options - 导出选项
 * @returns PNG Blob
 */
export async function exportToPNG(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<Blob> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  return new Promise((resolve, reject) => {
    try {
      // 创建临时canvas
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        throw new Error('无法获取Canvas上下文')
      }

      // 获取画布尺寸
      const rect = canvasElement.getBoundingClientRect()
      canvas.width = rect.width * opts.imageScale
      canvas.height = rect.height * opts.imageScale

      // 设置背景色
      ctx.fillStyle = opts.backgroundColor
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // 使用html2canvas或类似库来渲染DOM到canvas
      // 这里简化处理，实际项目中需要引入html2canvas
      if ((window as any).html2canvas) {
        ;(window as any)
          .html2canvas(canvasElement, {
            canvas: canvas,
            scale: opts.imageScale,
            backgroundColor: opts.backgroundColor,
            useCORS: true,
            allowTaint: true,
          })
          .then((canvas: HTMLCanvasElement) => {
            canvas.toBlob(
              (blob) => {
                if (blob) {
                  resolve(blob)
                } else {
                  reject(new Error('Canvas转Blob失败'))
                }
              },
              'image/png',
              opts.imageQuality
            )
          })
          .catch(reject)
      } else {
        // 降级方案：使用简单的截图方法
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Canvas转Blob失败'))
            }
          },
          'image/png',
          opts.imageQuality
        )
      }
    } catch (error: any) {
      reject(error)
    }
  })
}

/**
 * 导出为SVG格式
 * @param canvasElement - 画布元素
 * @param options - 导出选项
 * @returns SVG Blob
 */
export async function exportToSVG(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<Blob> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    const rect = canvasElement.getBoundingClientRect()
    const svgContent = generateSVGContent(canvasElement, {
      width: rect.width,
      height: rect.height,
      ...opts,
    })

    return new Blob([svgContent], { type: 'image/svg+xml' })
  } catch (error: any) {
    throw new Error(`SVG导出失败: ${error.message}`)
  }
}

/**
 * 生成SVG内容
 * @param element - DOM元素
 * @param options - 选项
 * @returns SVG字符串
 */
function generateSVGContent(element: HTMLElement, options: any): string {
  const { width, height, backgroundColor } = options

  let svgContent = `<?xml version="1.0" encoding="UTF-8"?>\n`
  svgContent += `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">\n`

  // 添加背景
  if (backgroundColor) {
    svgContent += `  <rect width="100%" height="100%" fill="${backgroundColor}"/>\n`
  }

  // 这里需要遍历DOM元素并转换为SVG元素
  // 实际实现会比较复杂，需要处理各种CSS样式和元素类型
  svgContent += convertElementToSVG(element)

  svgContent += `</svg>`

  return svgContent
}

/**
 * 将DOM元素转换为SVG元素
 * @param element - DOM元素
 * @returns SVG元素字符串
 */
function convertElementToSVG(element: HTMLElement): string {
  // 这是一个简化的实现
  // 实际项目中需要更复杂的DOM到SVG转换逻辑
  let svgContent = ''

  // 处理节点元素
  const nodes = element.querySelectorAll('.workflow-node')
  nodes.forEach((node) => {
    const rect = node.getBoundingClientRect()
    const style = window.getComputedStyle(node)

    svgContent += `  <rect x="${rect.x}" y="${rect.y}" width="${rect.width}" height="${rect.height}" `
    svgContent += `fill="${style.backgroundColor}" stroke="${style.borderColor}" stroke-width="${style.borderWidth}"/>\n`

    // 添加文本
    const text = node.textContent
    if (text) {
      svgContent += `  <text x="${rect.x + rect.width / 2}" y="${rect.y + rect.height / 2}" `
      svgContent += `text-anchor="middle" dominant-baseline="middle" fill="${style.color}">${text}</text>\n`
    }
  })

  // 处理连接线
  const connections = element.querySelectorAll('.workflow-connection')
  connections.forEach((conn) => {
    const path = conn.getAttribute('d')
    if (path) {
      svgContent += `  <path d="${path}" stroke="#666" stroke-width="2" fill="none"/>\n`
    }
  })

  return svgContent
}

/**
 * 导出为PDF格式
 * @param canvasElement - 画布元素
 * @param options - 导出选项
 * @returns PDF Blob
 */
export async function exportToPDF(
  canvasElement: HTMLElement,
  options: ExportOptions = {}
): Promise<Blob> {
  const opts = { ...DEFAULT_EXPORT_OPTIONS, ...options }

  try {
    // 首先导出为PNG
    const pngBlob = await exportToPNG(canvasElement, opts)

    // 使用jsPDF创建PDF
    if ((window as any).jsPDF) {
      const pdf = new (window as any).jsPDF({
        orientation: 'landscape',
        unit: 'px',
        format: [canvasElement.offsetWidth, canvasElement.offsetHeight],
      })

      const imgData = await blobToDataURL(pngBlob)
      pdf.addImage(imgData, 'PNG', 0, 0, canvasElement.offsetWidth, canvasElement.offsetHeight)

      return pdf.output('blob')
    } else {
      throw new Error('jsPDF库未加载')
    }
  } catch (error: any) {
    throw new Error(`PDF导出失败: ${error.message}`)
  }
}

// ========== 导入函数 ==========

/**
 * 从JSON导入工作流
 * @param jsonString - JSON字符串
 * @param options - 导入选项
 * @returns 工作流数据
 */
export function importFromJSON(
  jsonString: string,
  options: ImportOptions = {}
): WorkflowData {
  try {
    const data = JSON.parse(jsonString)
    return validateAndProcessImportData(data, options)
  } catch (error: any) {
    throw new Error(`JSON导入失败: ${error.message}`)
  }
}

/**
 * 从XML导入工作流
 * @param xmlString - XML字符串
 * @param options - 导入选项
 * @returns 工作流数据
 */
export function importFromXML(xmlString: string, options: ImportOptions = {}): WorkflowData {
  try {
    const data = parseXMLToObject(xmlString)
    return validateAndProcessImportData(data, options)
  } catch (error: any) {
    throw new Error(`XML导入失败: ${error.message}`)
  }
}

/**
 * 从YAML导入工作流
 * @param yamlString - YAML字符串
 * @param options - 导入选项
 * @returns 工作流数据
 */
export function importFromYAML(
  yamlString: string,
  options: ImportOptions = {}
): WorkflowData {
  try {
    const data = parseYAMLToObject(yamlString)
    return validateAndProcessImportData(data, options)
  } catch (error: any) {
    throw new Error(`YAML导入失败: ${error.message}`)
  }
}

/**
 * 从文件导入工作流
 * @param file - 文件对象
 * @param options - 导入选项
 * @returns 工作流数据
 */
export async function importFromFile(
  file: File,
  options: ImportOptions = {}
): Promise<WorkflowData> {
  try {
    const content = await readFileContent(file)
    const extension = getFileExtension(file.name).toLowerCase()

    switch (extension) {
      case 'json':
        return importFromJSON(content, options)
      case 'xml':
        return importFromXML(content, options)
      case 'yaml':
      case 'yml':
        return importFromYAML(content, options)
      default:
        throw new Error(`不支持的文件格式: ${extension}`)
    }
  } catch (error: any) {
    throw new Error(`文件导入失败: ${error.message}`)
  }
}

// ========== 辅助函数 ==========

/**
 * 准备工作流导出数据
 * @param workflow - 工作流数据
 * @param options - 导出选项
 * @returns 处理后的数据
 */
function prepareWorkflowData(
  workflow: WorkflowData,
  options: Required<ExportOptions>
): ExportData {
  const exportData: ExportData = {
    version: '1.0',
    format: 'workflow-designer',
    exportTime: new Date().toISOString(),
    workflow: {
      id: workflow.id,
      name: workflow.name,
      description: workflow.description,
      nodes: workflow.nodes || [],
      connections: workflow.connections || [],
      settings: workflow.settings || {},
    },
  }

  // 包含元数据
  if (options.includeMetadata) {
    exportData.metadata = {
      creator: workflow.creator,
      createdAt: workflow.createdAt,
      updatedAt: workflow.updatedAt,
      version: workflow.version,
      tags: workflow.tags || [],
    }
  }

  // 包含历史记录
  if (options.includeHistory && workflow.history) {
    exportData.history = workflow.history
  }

  // 包含注释
  if (options.includeComments && workflow.comments) {
    exportData.comments = workflow.comments
  }

  // 包含验证信息
  if (options.includeValidation && workflow.validation) {
    exportData.validation = workflow.validation
  }

  return exportData
}

/**
 * 验证和处理导入数据
 * @param data - 原始数据
 * @param options - 导入选项
 * @returns 处理后的工作流数据
 */
function validateAndProcessImportData(
  data: any,
  options: ImportOptions = {}
): WorkflowData {
  // 基础验证
  if (!data || typeof data !== 'object') {
    throw new Error('无效的数据格式')
  }

  // 检查是否是有效的工作流数据
  if (!data.workflow && !data.nodes) {
    throw new Error('不是有效的工作流数据')
  }

  // 提取工作流数据
  const workflow = data.workflow || data

  // 验证必需字段
  if (!workflow.nodes || !Array.isArray(workflow.nodes)) {
    throw new Error('缺少节点数据')
  }

  if (!workflow.connections || !Array.isArray(workflow.connections)) {
    workflow.connections = []
  }

  // 生成新的ID（如果需要）
  if (options.generateNewIds) {
    const idMap = new Map<string, string>()

    // 为节点生成新ID
    workflow.nodes.forEach((node: any) => {
      const newId = generateUniqueId()
      idMap.set(node.id, newId)
      node.id = newId
    })

    // 更新连接中的节点ID引用
    workflow.connections.forEach((conn: any) => {
      if (idMap.has(conn.sourceNodeId)) {
        conn.sourceNodeId = idMap.get(conn.sourceNodeId)
      }
      if (idMap.has(conn.targetNodeId)) {
        conn.targetNodeId = idMap.get(conn.targetNodeId)
      }
    })
  }

  // 验证节点数据完整性
  workflow.nodes.forEach((node: any, index: number) => {
    if (!node.id) {
      throw new Error(`节点 ${index} 缺少ID`)
    }
    if (!node.type) {
      throw new Error(`节点 ${node.id} 缺少类型`)
    }
    if (!node.position) {
      node.position = { x: 100 + index * 150, y: 100 }
    }
  })

  // 验证连接数据完整性
  workflow.connections.forEach((conn: any, index: number) => {
    if (!conn.sourceNodeId || !conn.targetNodeId) {
      throw new Error(`连接 ${index} 缺少源节点或目标节点ID`)
    }
    if (!conn.sourcePort || !conn.targetPort) {
      conn.sourcePort = conn.sourcePort || 'output'
      conn.targetPort = conn.targetPort || 'input'
    }
  })

  return {
    ...workflow,
    id: workflow.id || generateUniqueId(),
    name: workflow.name || '导入的工作流',
    description: workflow.description || '',
    settings: workflow.settings || {},
    metadata: data.metadata || {},
    importedAt: new Date().toISOString(),
  }
}

/**
 * 转换为XML格式
 * @param data - 数据对象
 * @param options - 选项
 * @returns XML字符串
 */
function convertToXML(data: any, options: ExportOptions): string {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
  xml += '<workflow>\n'

  // 递归转换对象为XML
  function objectToXML(obj: any, indent: string = '  '): string {
    let result = ''

    for (const [key, value] of Object.entries(obj)) {
      if (Array.isArray(value)) {
        result += `${indent}<${key}>\n`
        value.forEach((item: any) => {
          if (typeof item === 'object') {
            result += `${indent}  <item>\n`
            result += objectToXML(item, indent + '    ')
            result += `${indent}  </item>\n`
          } else {
            result += `${indent}  <item>${escapeXML(item)}</item>\n`
          }
        })
        result += `${indent}</${key}>\n`
      } else if (typeof value === 'object' && value !== null) {
        result += `${indent}<${key}>\n`
        result += objectToXML(value, indent + '  ')
        result += `${indent}</${key}>\n`
      } else {
        result += `${indent}<${key}>${escapeXML(value)}</${key}>\n`
      }
    }

    return result
  }

  xml += objectToXML(data)
  xml += '</workflow>'

  return xml
}

/**
 * 转换为YAML格式
 * @param data - 数据对象
 * @param options - 选项
 * @returns YAML字符串
 */
function convertToYAML(data: any, options: ExportOptions): string {
  // 简化的YAML转换实现
  // 实际项目中建议使用js-yaml库
  function objectToYAML(obj: any, indent: number = 0): string {
    let yaml = ''
    const spaces = '  '.repeat(indent)

    for (const [key, value] of Object.entries(obj)) {
      if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`
        value.forEach((item: any) => {
          if (typeof item === 'object') {
            yaml += `${spaces}  -\n`
            yaml += objectToYAML(item, indent + 2)
          } else {
            yaml += `${spaces}  - ${item}\n`
          }
        })
      } else if (typeof value === 'object' && value !== null) {
        yaml += `${spaces}${key}:\n`
        yaml += objectToYAML(value, indent + 1)
      } else {
        yaml += `${spaces}${key}: ${value}\n`
      }
    }

    return yaml
  }

  return objectToYAML(data)
}

/**
 * 解析XML为对象
 * @param xmlString - XML字符串
 * @returns 解析后的对象
 */
function parseXMLToObject(xmlString: string): any {
  // 简化的XML解析实现
  // 实际项目中建议使用专门的XML解析库
  const parser = new DOMParser()
  const xmlDoc = parser.parseFromString(xmlString, 'text/xml')

  function xmlNodeToObject(node: Element): any {
    const obj: any = {}

    // 处理属性
    if (node.attributes) {
      for (const attr of Array.from(node.attributes)) {
        obj[`@${attr.name}`] = attr.value
      }
    }

    // 处理子节点
    const children = Array.from(node.childNodes).filter((child) => child.nodeType === 1)

    if (children.length === 0) {
      return node.textContent
    }

    for (const child of children as Element[]) {
      const childName = child.nodeName
      const childValue = xmlNodeToObject(child)

      if (obj[childName]) {
        if (!Array.isArray(obj[childName])) {
          obj[childName] = [obj[childName]]
        }
        obj[childName].push(childValue)
      } else {
        obj[childName] = childValue
      }
    }

    return obj
  }

  return xmlNodeToObject(xmlDoc.documentElement)
}

/**
 * 解析YAML为对象
 * @param yamlString - YAML字符串
 * @returns 解析后的对象
 */
function parseYAMLToObject(yamlString: string): any {
  // 简化的YAML解析实现
  // 实际项目中建议使用js-yaml库
  if ((window as any).jsyaml) {
    return (window as any).jsyaml.load(yamlString)
  } else {
    throw new Error('YAML解析库未加载')
  }
}

/**
 * 读取文件内容
 * @param file - 文件对象
 * @returns 文件内容
 */
function readFileContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = (e) => reject(new Error('文件读取失败'))
    reader.readAsText(file)
  })
}

/**
 * 获取文件扩展名
 * @param filename - 文件名
 * @returns 扩展名
 */
function getFileExtension(filename: string): string {
  return filename.split('.').pop() || ''
}

/**
 * Blob转DataURL
 * @param blob - Blob对象
 * @returns DataURL
 */
function blobToDataURL(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = (e) => reject(new Error('Blob转换失败'))
    reader.readAsDataURL(blob)
  })
}

/**
 * 转义XML特殊字符
 * @param value - 值
 * @returns 转义后的字符串
 */
function escapeXML(value: any): string {
  if (value == null) return ''

  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

/**
 * 生成唯一ID
 * @returns 唯一ID
 */
function generateUniqueId(): string {
  return 'node_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// ========== 公开工具函数 ==========

/**
 * 下载文件
 * @param content - 文件内容
 * @param filename - 文件名
 * @param mimeType - MIME类型
 */
export function downloadFile(
  content: Blob | string,
  filename: string,
  mimeType: string = 'application/octet-stream'
): void {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * 获取导出文件名
 * @param workflow - 工作流数据
 * @param format - 导出格式
 * @returns 文件名
 */
export function getExportFilename(workflow: WorkflowData, format: string): string {
  const name = workflow.name || 'workflow'
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
  return `${name}_${timestamp}.${format}`
}

/**
 * 验证导出格式
 * @param format - 格式
 * @returns 是否支持
 */
export function isSupportedExportFormat(format: string): boolean {
  return Object.values(EXPORT_FORMATS).includes(format as ExportFormat)
}

/**
 * 获取格式的MIME类型
 * @param format - 格式
 * @returns MIME类型
 */
export function getFormatMimeType(format: string): string {
  const mimeTypes: Record<string, string> = {
    [EXPORT_FORMATS.JSON]: 'application/json',
    [EXPORT_FORMATS.XML]: 'application/xml',
    [EXPORT_FORMATS.YAML]: 'application/x-yaml',
    [EXPORT_FORMATS.PNG]: 'image/png',
    [EXPORT_FORMATS.SVG]: 'image/svg+xml',
    [EXPORT_FORMATS.PDF]: 'application/pdf',
    [EXPORT_FORMATS.BPMN]: 'application/xml',
    [EXPORT_FORMATS.WORKFLOW]: 'application/json',
  }

  return mimeTypes[format] || 'application/octet-stream'
}

/**
 * 批量导出工作流
 * @param workflows - 工作流数组
 * @param format - 导出格式
 * @param options - 导出选项
 * @returns 压缩包Blob
 */
export async function batchExportWorkflows(
  workflows: WorkflowData[],
  format: string,
  options: ExportOptions = {}
): Promise<Blob> {
  try {
    // 这里需要使用JSZip库来创建压缩包
    if (!(window as any).JSZip) {
      throw new Error('JSZip库未加载')
    }

    const zip = new (window as any).JSZip()

    for (const workflow of workflows) {
      let content: string
      let filename: string

      switch (format) {
        case EXPORT_FORMATS.JSON:
          content = exportToJSON(workflow, options)
          filename = `${workflow.name || workflow.id}.json`
          break
        case EXPORT_FORMATS.XML:
          content = exportToXML(workflow, options)
          filename = `${workflow.name || workflow.id}.xml`
          break
        case EXPORT_FORMATS.YAML:
          content = exportToYAML(workflow, options)
          filename = `${workflow.name || workflow.id}.yaml`
          break
        default:
          throw new Error(`批量导出不支持格式: ${format}`)
      }

      zip.file(filename, content)
    }

    return await zip.generateAsync({ type: 'blob' })
  } catch (error: any) {
    throw new Error(`批量导出失败: ${error.message}`)
  }
}

// ========== 导出类型 ==========

export type {
  ExportFormat,
  ExportOptions,
  ImportOptions,
  WorkflowData,
  ExportData,
}

