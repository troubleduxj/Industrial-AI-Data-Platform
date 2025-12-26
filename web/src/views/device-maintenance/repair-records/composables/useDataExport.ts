import { ref } from 'vue'
import { useMessage } from 'naive-ui'

// ==================== 类型定义 ====================

/** 导出格式类型 */
export type ExportFormat = 'csv' | 'excel' | 'xlsx' | 'pdf'

/** 字段映射配置 */
export interface FieldMapping {
  [key: string]: string
}

/** 维修记录数据 */
export interface RepairRecordData {
  repair_date?: string | number | Date
  category?: string
  device_number?: string
  brand?: string
  model?: string
  pin_type?: string
  company?: string
  department?: string
  workshop?: string
  construction_unit?: string
  applicant?: string
  phone?: string
  is_fault?: boolean
  fault_reason?: string
  damage_category?: string
  fault_content?: string
  fault_location?: string
  repair_content?: string
  parts_name?: string
  repairer?: string
  repair_completion_date?: string | number | Date
  remarks?: string
  [key: string]: any
}

/** 格式化后的数据 */
type FormattedData = Record<string, string | number | boolean>

// ==================== Composable ====================

export function useDataExport() {
  const message = useMessage()
  const exporting = ref(false)

  // 字段映射配置
  const fieldMapping: FieldMapping = {
    repair_date: '报修日期',
    category: '类别',
    device_number: '焊机编号',
    brand: '品牌',
    model: '型号',
    pin_type: '接口类型',
    company: '公司',
    department: '部门',
    workshop: '车间',
    construction_unit: '施工单位',
    applicant: '申请人',
    phone: '电话',
    is_fault: '是否故障',
    fault_reason: '故障原因',
    damage_category: '损坏类别',
    fault_content: '故障内容',
    fault_location: '故障部位',
    repair_content: '维修内容',
    parts_name: '配件名称',
    repairer: '维修人',
    repair_completion_date: '维修完成日期',
    remarks: '备注',
  }

  /**
   * 数据格式化
   * @param data - 原始数据数组
   * @returns 格式化后的数据数组
   */
  const formatDataForExport = (data: RepairRecordData[]): FormattedData[] => {
    return data.map((item) => {
      const formattedItem: FormattedData = {}

      Object.entries(fieldMapping).forEach(([key, label]) => {
        let value: any = item[key]

        // 特殊字段格式化
        switch (key) {
          case 'is_fault':
            value = value ? '是' : '否'
            break
          case 'repair_date':
          case 'repair_completion_date':
            if (value) {
              value = new Date(value).toLocaleDateString('zh-CN')
            }
            break
          default:
            value = value || ''
        }

        formattedItem[label] = value
      })

      return formattedItem
    })
  }

  /**
   * 导出为CSV
   * @param data - 数据数组
   * @param filename - 文件名
   */
  const exportToCSV = async (data: RepairRecordData[], filename: string = '维修记录'): Promise<void> => {
    try {
      exporting.value = true

      const formattedData = formatDataForExport(data)

      if (formattedData.length === 0) {
        message.warning('没有数据可导出')
        return
      }

      // 获取表头
      const headers = Object.keys(formattedData[0])

      // 构建CSV内容
      const csvContent = [
        // 表头
        headers.join(','),
        // 数据行
        ...formattedData.map((row) =>
          headers
            .map((header) => {
              const value = row[header] || ''
              // 处理包含逗号或换行的值
              return `"${String(value).replace(/"/g, '""')}"`
            })
            .join(',')
        ),
      ].join('\n')

      // 添加BOM以支持中文
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })

      // 下载文件
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      message.success('导出成功')
    } catch (error) {
      console.error('Export to CSV failed:', error)
      message.error('导出失败，请稍后重试')
    } finally {
      exporting.value = false
    }
  }

  /**
   * 导出为Excel（回退到CSV）
   * @param data - 数据数组
   * @param filename - 文件名
   */
  const exportToExcel = async (data: RepairRecordData[], filename: string = '维修记录'): Promise<void> => {
    try {
      exporting.value = true

      const formattedData = formatDataForExport(data)

      if (formattedData.length === 0) {
        message.warning('没有数据可导出')
        return
      }

      // Excel功能需要额外依赖，回退到CSV导出
      message.info('Excel导出功能需要安装额外依赖，已为您使用CSV格式导出')
      await exportToCSV(data, filename)
    } catch (error) {
      console.error('Export to Excel failed:', error)
      message.error('导出失败，请稍后重试')
    } finally {
      exporting.value = false
    }
  }

  /**
   * 导出为PDF（回退到CSV）
   * @param data - 数据数组
   * @param filename - 文件名
   */
  const exportToPDF = async (data: RepairRecordData[], filename: string = '维修记录'): Promise<void> => {
    try {
      exporting.value = true

      const formattedData = formatDataForExport(data)

      if (formattedData.length === 0) {
        message.warning('没有数据可导出')
        return
      }

      // PDF功能需要额外依赖，回退到CSV导出
      message.info('PDF导出功能需要安装额外依赖，已为您使用CSV格式导出')
      await exportToCSV(data, filename)
    } catch (error) {
      console.error('Export to PDF failed:', error)
      message.error('导出失败，请稍后重试')
    } finally {
      exporting.value = false
    }
  }

  /**
   * 批量导出（支持多种格式）
   * @param data - 数据数组
   * @param formats - 导出格式数组
   * @param filename - 文件名
   */
  const batchExport = async (
    data: RepairRecordData[],
    formats: ExportFormat[] = ['excel'],
    filename: string = '维修记录'
  ): Promise<void> => {
    try {
      for (const format of formats) {
        switch (format.toLowerCase() as ExportFormat) {
          case 'csv':
            await exportToCSV(data, filename)
            break
          case 'excel':
          case 'xlsx':
            await exportToExcel(data, filename)
            break
          case 'pdf':
            await exportToPDF(data, filename)
            break
          default:
            console.warn(`Unsupported export format: ${format}`)
        }

        // 添加延迟避免浏览器阻止多个下载
        if (formats.length > 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000))
        }
      }
    } catch (error) {
      console.error('Batch export failed:', error)
      message.error('批量导出失败')
    }
  }

  /**
   * 导出模板
   * @param format - 导出格式
   */
  const exportTemplate = async (format: ExportFormat = 'csv'): Promise<void> => {
    try {
      const templateData: RepairRecordData[] = [
        {
          repair_date: '2025-01-01',
          category: '二氧化碳保护焊机',
          device_number: 'B001-00001',
          brand: '松下',
          model: 'YD-500ER2',
          pin_type: '7P',
          company: '示例公司名称',
          department: '示例部门',
          workshop: '示例车间',
          construction_unit: '示例施工单位',
          applicant: '张三',
          phone: '13800138000',
          is_fault: true,
          fault_reason: '操作不当',
          damage_category: '非正常损坏',
          fault_content: '示例故障内容描述',
          fault_location: '示例故障部位',
          repair_content: '示例维修内容描述',
          parts_name: '示例配件名称',
          repairer: '李师傅',
          repair_completion_date: '2025-01-01',
          remarks: '示例备注信息',
        },
      ]

      // 创建格式化的模板数据（使用中文标签）
      const formattedTemplateData = templateData.map((item) => {
        const formatted: Record<string, any> = {}
        Object.entries(fieldMapping).forEach(([key, label]) => {
          let value = item[key as keyof RepairRecordData]
          // 格式化 is_fault 为中文
          if (key === 'is_fault') {
            value = value ? '是' : '否'
          }
          formatted[label] = value
        })
        return formatted as FormattedData
      })

      // 统一使用CSV格式导出模板
      if (formattedTemplateData.length > 0) {
        const headers = Object.keys(formattedTemplateData[0])
        const csvContent = [
          headers.join(','),
          ...formattedTemplateData.map((row) =>
            headers
              .map((header) => {
                const value = row[header] || ''
                return `"${String(value).replace(/"/g, '""')}"`
              })
              .join(',')
          ),
        ].join('\n')

        const BOM = '\uFEFF'
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `维修记录导入模板_${new Date().toISOString().slice(0, 10)}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }

      if (format.toLowerCase() !== 'csv') {
        message.info(`${format.toUpperCase()}模板功能需要安装额外依赖，已为您使用CSV格式导出`)
      }
    } catch (error) {
      console.error('Export template failed:', error)
      message.error('导出模板失败')
    }
  }

  return {
    exporting,
    exportToCSV,
    exportToExcel,
    exportToPDF,
    batchExport,
    exportTemplate,
    fieldMapping,
  }
}

