<template>
  <div class="repair-record-form">
    <!-- 验证警告提示 -->
    <div v-if="validationWarnings.length > 0" class="validation-alerts">
      <NAlert
        type="warning"
        title="数据完整性提醒"
        :show-icon="true"
        closable
      >
        <ul class="warning-list">
          <li v-for="warning in validationWarnings" :key="warning">{{ warning }}</li>
        </ul>
      </NAlert>
    </div>
    
    <!-- 验证错误提示 -->
    <div v-if="Object.keys(validationErrors).length > 0" class="validation-alerts">
      <NAlert
        type="error"
        title="验证失败"
        :show-icon="true"
        closable
      >
        <ul class="error-list">
          <li v-for="(error, field) in validationErrors" :key="field">{{ error }}</li>
        </ul>
      </NAlert>
    </div>

    <NForm
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-placement="left"
      :label-width="120"
      class="repair-form"
    >
      <!-- 基础信息区域 -->
      <div class="form-section">
        <h4 class="section-title">基础信息</h4>
        <div class="form-grid">
          <NFormItem label="报修时间" path="repair_date" class="form-item">
            <NDatePicker
              v-model:value="formData.repair_date"
              type="date"
              placeholder="请选择报修时间"
              style="width: 100%"
            />
          </NFormItem>
          
          <NFormItem label="维修完成时间" path="repair_completion_date" class="form-item">
            <NDatePicker
              v-model:value="formData.repair_completion_date"
              type="date"
              placeholder="请选择维修完成时间"
              style="width: 100%"
              :is-date-disabled="(ts) => {
                if (!formData.repair_date) return false
                const repairDate = typeof formData.repair_date === 'number' ? 
                  new Date(formData.repair_date) : new Date(formData.repair_date)
                return ts < repairDate.getTime()
              }"
            />
          </NFormItem>
          
          <NFormItem label="设备编号" path="device_number" class="form-item">
            <NSelect
              v-model:value="formData.device_number"
              :options="deviceOptions"
              :loading="deviceLoading"
              filterable
              remote
              clearable
              placeholder="请搜索或选择设备编号"
              :render-label="renderDeviceLabel"
              :render-tag="renderDeviceTag"
              @search="handleDeviceSearch"
              @update:value="handleDeviceSelect"
              @clear="handleDeviceClear"
            />
          </NFormItem>
          
          <NFormItem label="设备名称" path="device_name" class="form-item">
            <NSelect
              v-model:value="formData.device_name"
              :options="deviceNameOptions"
              :loading="deviceLoading"
              filterable
              remote
              clearable
              placeholder="请搜索或选择设备名称"
              :render-label="renderDeviceNameLabel"
              :render-tag="renderDeviceNameTag"
              @search="handleDeviceNameSearch"
              @update:value="handleDeviceNameSelect"
              @clear="handleDeviceNameClear"
            />
          </NFormItem>
          
          <NFormItem label="品牌" path="brand" class="form-item">
            <NSelect
              v-model:value="formData.brand"
              :options="brandOptions"
              placeholder="请选择品牌"
            />
          </NFormItem>
          
          <NFormItem label="型号" path="model" class="form-item">
            <NInput
              v-model:value="formData.model"
              placeholder="请输入型号"
            />
          </NFormItem>
          
          <NFormItem label="接口" path="pin_type" class="form-item">
            <NSelect
              v-model:value="formData.pin_type"
              :options="pinTypeOptions"
              placeholder="请选择接口类型"
            />
          </NFormItem>
          
          <NFormItem label="类别" path="category" class="form-item">
            <NSelect
              v-model:value="formData.category"
              :options="categoryOptions"
              placeholder="请选择设备类别"
            />
          </NFormItem>
        </div>
      </div>

      <!-- 公司信息区域 -->
      <div class="form-section">
        <h4 class="section-title">公司信息</h4>
        <div class="form-grid">
          <NFormItem label="公司" path="company" class="form-item">
            <NInput
              v-model:value="formData.company"
              placeholder="请输入公司名称"
            />
          </NFormItem>
          
          <NFormItem label="部门" path="department" class="form-item">
            <NInput
              v-model:value="formData.department"
              placeholder="请输入部门"
            />
          </NFormItem>
          
          <NFormItem label="车间" path="workshop" class="form-item">
            <NInput
              v-model:value="formData.workshop"
              placeholder="请输入车间"
            />
          </NFormItem>
          
          <NFormItem label="施工单位" path="construction_unit" class="form-item">
            <NInput
              v-model:value="formData.construction_unit"
              placeholder="请输入施工单位"
            />
          </NFormItem>
          
          <NFormItem label="申请人" path="applicant" class="form-item">
            <NInput
              v-model:value="formData.applicant"
              placeholder="请输入申请人"
            />
          </NFormItem>
          
          <NFormItem label="电话" path="phone" class="form-item">
            <NInput
              v-model:value="formData.phone"
              placeholder="请输入联系电话"
            />
          </NFormItem>
        </div>
      </div>

      <!-- 故障信息区域 -->
      <div class="form-section">
        <h4 class="section-title">故障信息</h4>
        <div class="form-grid">
          <NFormItem label="是否故障" path="is_fault" class="form-item">
            <NRadioGroup v-model:value="formData.is_fault">
              <NRadio :value="true">是</NRadio>
              <NRadio :value="false">否</NRadio>
            </NRadioGroup>
          </NFormItem>
          
          <NFormItem label="故障原因" path="fault_reason" class="form-item" v-if="formData.is_fault">
            <NSelect
              v-model:value="formData.fault_reason"
              :options="faultReasonOptions"
              placeholder="请选择故障原因"
            />
          </NFormItem>
          
          <NFormItem label="损坏类别" path="damage_category" class="form-item" v-if="formData.is_fault">
            <NSelect
              v-model:value="formData.damage_category"
              :options="damageCategoryOptions"
              placeholder="请选择损坏类别"
            />
          </NFormItem>
          
          <NFormItem label="故障内容" path="fault_content" class="form-item full-width" v-if="formData.is_fault">
            <NInput
              v-model:value="formData.fault_content"
              type="textarea"
              :rows="3"
              placeholder="请详细描述故障内容"
            />
          </NFormItem>
          
          <NFormItem label="故障部位" path="fault_location" class="form-item" v-if="formData.is_fault">
            <NInput
              v-model:value="formData.fault_location"
              placeholder="请输入故障部位"
            />
          </NFormItem>
        </div>
      </div>

      <!-- 维修信息区域 -->
      <div class="form-section">
        <h4 class="section-title">维修信息</h4>
        <div class="form-grid">
          <NFormItem label="维修内容" path="repair_content" class="form-item full-width">
            <NInput
              v-model:value="formData.repair_content"
              type="textarea"
              :rows="3"
              placeholder="请描述维修内容"
            />
          </NFormItem>
          
          <NFormItem label="配件名称" path="parts_name" class="form-item">
            <NInput
              v-model:value="formData.parts_name"
              placeholder="请输入更换的配件名称"
            />
          </NFormItem>
          
          <NFormItem label="维修人" path="repairer" class="form-item">
            <NInput
              v-model:value="formData.repairer"
              placeholder="请输入维修人员"
            />
          </NFormItem>
          
          <NFormItem label="备注" path="remarks" class="form-item full-width">
            <NInput
              v-model:value="formData.remarks"
              type="textarea"
              :rows="2"
              placeholder="请输入备注信息"
            />
          </NFormItem>
        </div>
      </div>
    </NForm>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, h, nextTick, type Ref, type VNodeChild } from 'vue'
import { 
  NForm, 
  NFormItem, 
  NInput, 
  NSelect, 
  NDatePicker, 
  NRadioGroup, 
  NRadio,
  NAlert,
  useMessage,
  type FormInst,
  type FormItemRule,
  type SelectOption,
  type SelectRenderLabel,
  type SelectRenderTag
} from 'naive-ui'
import { useRepairValidation } from '../composables/useRepairValidation'
import { useFormCache } from '../composables/useFormCache'
import { useRepairDictOptions } from '../composables/useRepairDictOptions'
import type { RepairRecordData } from '../composables/useDataExport'

// ==================== 类型定义 ====================

interface Props {
  modelValue?: Partial<RepairRecordData>
  loading?: boolean
  recordId?: string | number | null
  originalData?: Partial<RepairRecordData> | null
}

interface Emits {
  (e: 'update:modelValue', value: Partial<RepairRecordData>): void
  (e: 'validate', isValid: boolean): void
  (e: 'cache-loaded', data: Partial<RepairRecordData>): void
}

// Props
const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  loading: false,
  recordId: null,
  originalData: null
})

// Emits
const emit = defineEmits<Emits>()

// Form ref and validation
const formRef = ref<FormInst | null>(null)
const message = useMessage()
const { validateForm, checkDataIntegrity, formatValidationErrors } = useRepairValidation()

// 表单缓存管理
const { createFormManager, watchFormChanges, getDefaultFormData } = useFormCache()

// 验证状态
const validationErrors = ref<Record<string, string>>({})
const validationWarnings = ref<string[]>([])

// Form data - 使用默认数据结构
const formData = reactive(getDefaultFormData())

// 创建表单管理器
const formManager = createFormManager(formData)

// 选项数据 - 使用字典数据
const {
  categoryOptions,
  brandOptions,
  faultReasonOptions,
  damageCategoryOptions,
} = useRepairDictOptions({ withAllOption: false })

// 接口类型选项（固定值，不需要字典）
const pinTypeOptions = ref<SelectOption[]>([
  { label: '7P', value: '7P' },
  { label: '9P', value: '9P' }
])

// 设备数据类型
interface DeviceInfo {
  device_code: string
  device_name?: string
  model?: string
  brand?: string
  [key: string]: any
}

// 设备搜索相关
const deviceOptions = ref<SelectOption[]>([])
const deviceNameOptions = ref<SelectOption[]>([])
const deviceLoading = ref<boolean>(false)
const deviceSearchTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const deviceNameSearchTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const allDevices = ref<DeviceInfo[]>([]) // 缓存所有设备数据

// 表单验证规则
const formRules = {
  repair_date: {
    required: true,
    message: '请选择报修日期',
    trigger: ['change', 'blur'],
    validator: (rule, value) => {
      if (!value) {
        return new Error('请选择报修日期')
      }
      // 检查日期是否有效
      const date = typeof value === 'number' ? new Date(value) : new Date(value)
      if (isNaN(date.getTime())) {
        return new Error('请选择有效的报修日期')
      }
      // 检查日期不能超过今天
      const today = new Date()
      today.setHours(23, 59, 59, 999)
      if (date > today) {
        return new Error('报修日期不能超过今天')
      }
      return true
    }
  },
  category: {
    required: true,
    message: '请选择设备类别',
    trigger: 'change'
  },
  device_number: {
    required: true,
    message: '请输入焊机编号',
    trigger: 'blur',
    validator: async (rule, value) => {
      if (!value) {
        return new Error('请输入焊机编号')
      }
      
      // 调用设备编号验证逻辑
      try {
        const { useRepairValidation } = await import('../composables/useRepairValidation.js')
        const { businessRules } = useRepairValidation()
        
        const deviceExists = await businessRules.checkDeviceNumberExists(value)
        if (!deviceExists) {
          return new Error('设备编号不存在，请检查后重新输入')
        }
        
        return true
      } catch (error) {
        console.warn('设备编号验证失败，跳过验证:', error)
        return true
      }
    }
  },
  brand: {
    required: true,
    message: '请选择品牌',
    trigger: 'change'
  },
  model: {
    required: true,
    message: '请输入型号',
    trigger: 'blur'
  },
  company: {
    required: true,
    message: '请输入公司名称',
    trigger: 'blur'
  },
  applicant: {
    required: true,
    message: '请输入申请人',
    trigger: 'blur'
  },
  phone: {
    required: true,
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入正确的手机号码',
    trigger: 'blur'
  },
  fault_reason: {
    required: true,
    message: '请选择故障原因',
    trigger: 'change',
    validator: (rule, value) => {
      if (formData.is_fault && !value) {
        return new Error('故障时必须选择故障原因')
      }
      return true
    }
  },
  damage_category: {
    required: true,
    message: '请选择损坏类别',
    trigger: 'change',
    validator: (rule, value) => {
      if (formData.is_fault && !value) {
        return new Error('故障时必须选择损坏类别')
      }
      return true
    }
  },
  fault_content: {
    required: true,
    message: '请输入故障内容',
    trigger: 'blur',
    validator: (rule, value) => {
      if (formData.is_fault && !value) {
        return new Error('故障时必须输入故障内容')
      }
      return true
    }
  },
  repair_completion_date: {
    trigger: ['change', 'blur'],
    validator: (rule, value) => {
      if (!value) return true // 非必填字段
      
      const completionDate = typeof value === 'number' ? new Date(value) : new Date(value)
      
      // 检查日期是否有效
      if (isNaN(completionDate.getTime())) {
        return new Error('请选择有效的维修完成日期')
      }
      
      // 完成日期不能早于报修日期
      if (formData.repair_date) {
        const repairDate = typeof formData.repair_date === 'number' ? 
          new Date(formData.repair_date) : new Date(formData.repair_date)
        if (completionDate < repairDate) {
          return new Error('维修完成日期不能早于报修日期')
        }
      }
      
      // 完成日期不能超过今天
      const today = new Date()
      today.setHours(23, 59, 59, 999)
      if (completionDate > today) {
        return new Error('维修完成日期不能超过今天')
      }
      
      return true
    }
  }
}

// 设备搜索相关方法
const loadAllDevices = async () => {
  try {
    deviceLoading.value = true
    
    // 动态导入设备API
    const { default: deviceV2Api } = await import('@/api/device-v2')
    
    // 先加载第一页数据
    const response = await deviceV2Api.list({
      page: 1,
      page_size: 100, // API限制最大为100
      status: 'active' // 只获取活跃设备
    })
    
    if (response && response.success && response.data) {
      const devices = Array.isArray(response.data) ? response.data : (response.data.items || [])
      
      // 处理设备数据 - 为设备编号搜索
      allDevices.value = devices.map(device => ({
        label: device.device_code || device.device_number || device.id,
        value: device.device_code || device.device_number || device.id,
        device: device, // 保存完整设备信息
        searchText: `${device.device_code || ''} ${device.manufacturer || device.brand || ''} ${device.device_model || device.model || ''} ${device.device_type || device.category || ''}`.toLowerCase()
      }))
      
      // 为设备名称搜索准备数据
      const deviceNameData = devices.filter(device => device.device_name || device.name).map(device => ({
        label: device.device_name || device.name,
        value: device.device_name || device.name,
        device: device, // 保存完整设备信息
        searchText: `${device.device_name || device.name || ''} ${device.device_code || ''} ${device.manufacturer || device.brand || ''} ${device.device_model || device.model || ''}`.toLowerCase()
      }))
      
      console.log(`[RepairRecordForm] 设备编号数据: ${allDevices.value.length} 个`)
      console.log(`[RepairRecordForm] 设备名称数据: ${deviceNameData.length} 个`)
      
      // 初始化设备编号选项（显示前20个）
      deviceOptions.value = allDevices.value.slice(0, 20)
      
      // 初始化设备名称选项（使用独立的数据结构）
      deviceNameOptions.value = deviceNameData.slice(0, 20)
      
      console.log(`[RepairRecordForm] 设备编号选项初始化: ${deviceOptions.value.length} 个`)
      console.log(`[RepairRecordForm] 设备名称选项初始化: ${deviceNameOptions.value.length} 个`)
      
      console.log(`[RepairRecordForm] 加载了 ${allDevices.value.length} 个设备`)
      
      // 如果有更多数据，可以考虑后续优化为按需加载
      const meta = response.meta || {}
      if (meta.total && meta.total > devices.length) {
        console.log(`[RepairRecordForm] 注意：还有 ${meta.total - devices.length} 个设备未加载，当前仅显示前100个`)
      }
    }
  } catch (error) {
    console.error('[RepairRecordForm] 加载设备列表失败:', error)
    message.error('加载设备列表失败')
  } finally {
    deviceLoading.value = false
  }
}

const handleDeviceSearch = (query) => {
  // 清除之前的定时器
  if (deviceSearchTimer.value) {
    clearTimeout(deviceSearchTimer.value)
  }
  
  // 防抖搜索
  deviceSearchTimer.value = setTimeout(() => {
    if (!query || query.length < 1) {
      // 显示前20个设备
      deviceOptions.value = allDevices.value.slice(0, 20)
    } else {
      // 搜索匹配的设备
      const searchQuery = query.toLowerCase()
      deviceOptions.value = allDevices.value.filter(device => 
        device.searchText.includes(searchQuery) ||
        device.label.toLowerCase().includes(searchQuery)
      ).slice(0, 50) // 限制搜索结果数量
    }
  }, 300)
}

const handleDeviceSelect = (deviceCode) => {
  if (!deviceCode) return
  
  console.log('[RepairRecordForm] 设备选择事件触发:', deviceCode)
  
  // 查找选中的设备信息
  const selectedDevice = allDevices.value.find(item => item.value === deviceCode)
  
  if (selectedDevice && selectedDevice.device) {
    const device = selectedDevice.device
    
    console.log('[RepairRecordForm] 找到设备信息:', device)
    
    // 使用nextTick确保DOM更新
    nextTick(() => {
      try {
        // 自动填充设备相关信息
        formData.device_number = deviceCode
        
        // 填充设备名称
        const deviceName = device.device_name || device.name
        if (deviceName) {
          formData.device_name = deviceName
          console.log('[RepairRecordForm] 填充设备名称:', deviceName)
        }
        
        // 填充品牌信息 - 使用manufacturer字段
        const brandValue = device.manufacturer || device.brand
        if (brandValue) {
          const brandExists = brandOptions.value.some(option => option.value === brandValue)
          if (brandExists) {
            formData.brand = brandValue
            console.log('[RepairRecordForm] 填充品牌:', brandValue)
          } else {
            // 如果品牌不在选项中，添加到选项中
            brandOptions.value.push({ label: brandValue, value: brandValue })
            formData.brand = brandValue
            console.log('[RepairRecordForm] 添加并填充新品牌:', brandValue)
          }
        }
        
        // 填充型号信息 - 使用device_model字段
        const modelValue = device.device_model || device.model
        if (modelValue) {
          formData.model = modelValue
          console.log('[RepairRecordForm] 填充型号:', modelValue)
        }
        
        // 填充类别信息 - 使用device_type字段并转换为中文
        const deviceType = device.device_type || device.category
        let categoryValue = deviceType
        
        // 转换设备类型为中文
        if (deviceType === 'welding') {
          categoryValue = '二氧化碳保护焊机' // 默认焊接设备类型
        } else if (deviceType) {
          categoryValue = deviceType
        }
        
        if (categoryValue) {
          const categoryExists = categoryOptions.value.some(option => option.value === categoryValue)
          if (categoryExists) {
            formData.category = categoryValue
            console.log('[RepairRecordForm] 填充类别:', categoryValue)
          } else {
            // 如果类别不在选项中，添加到选项中
            categoryOptions.value.push({ label: categoryValue, value: categoryValue })
            formData.category = categoryValue
            console.log('[RepairRecordForm] 添加并填充新类别:', categoryValue)
          }
        }
        
        // 填充接口类型（如果有）
        if (device.pin_type) {
          const pinTypeExists = pinTypeOptions.value.some(option => option.value === device.pin_type)
          if (pinTypeExists) {
            formData.pin_type = device.pin_type
          } else {
            pinTypeOptions.value.push({ label: device.pin_type, value: device.pin_type })
            formData.pin_type = device.pin_type
          }
          console.log('[RepairRecordForm] 填充接口类型:', device.pin_type)
        }
        
        // 填充公司信息（如果有）
        if (device.company) {
          formData.company = device.company
          console.log('[RepairRecordForm] 填充公司:', device.company)
        }
        
        // 填充部门信息（如果有）
        if (device.department) {
          formData.department = device.department
          console.log('[RepairRecordForm] 填充部门:', device.department)
        }
        
        // 填充车间信息（如果有）
        if (device.workshop) {
          formData.workshop = device.workshop
          console.log('[RepairRecordForm] 填充车间:', device.workshop)
        }
        
        // 显示成功消息
        const filledFields = []
        if (device.device_name || device.name) filledFields.push('设备名称')
        if (device.manufacturer || device.brand) filledFields.push('品牌')
        if (device.device_model || device.model) filledFields.push('型号')
        if (device.device_type || device.category) filledFields.push('类别')
        if (device.company) filledFields.push('公司')
        if (device.department) filledFields.push('部门')
        if (device.workshop) filledFields.push('车间')
        
        if (filledFields.length > 0) {
          message.success(`已自动填充: ${filledFields.join('、')}`)
          console.log('[RepairRecordForm] 自动填充完成，填充字段:', filledFields)
        } else {
          message.info('设备信息不完整，请手动补充相关信息')
        }
        
      } catch (error) {
        console.error('[RepairRecordForm] 自动填充失败:', error)
        message.error('自动填充失败，请手动输入设备信息')
      }
    })
  } else {
    console.warn('[RepairRecordForm] 未找到设备信息:', deviceCode)
    message.warning('未找到设备信息，请检查设备编号')
  }
}

const handleDeviceClear = () => {
  // 清空设备相关字段，但保留用户可能手动输入的其他信息
  formData.device_number = ''
  // 注意：不清空品牌、型号等，因为用户可能想保留这些信息
}

// 设备名称搜索处理
const handleDeviceNameSearch = (query) => {
  // 清除之前的定时器
  if (deviceNameSearchTimer.value) {
    clearTimeout(deviceNameSearchTimer.value)
  }
  
  // 防抖搜索
  deviceNameSearchTimer.value = setTimeout(async () => {
    try {
      deviceLoading.value = true
      
      if (!query || query.length < 1) {
        // 显示前20个设备名称（从API数据中获取）
        const { default: deviceV2Api } = await import('@/api/device-v2')
        const response = await deviceV2Api.list({
          page: 1,
          page_size: 20,
          status: 'active'
        })
        
        if (response && response.success && response.data) {
          const devices = Array.isArray(response.data) ? response.data : (response.data.items || [])
          deviceNameOptions.value = devices
            .filter(device => device.device_name || device.name)
            .map(device => ({
              label: device.device_name || device.name,
              value: device.device_name || device.name,
              device: device,
              searchText: `${device.device_name || device.name || ''} ${device.device_code || ''} ${device.manufacturer || device.brand || ''} ${device.device_model || device.model || ''}`.toLowerCase()
            }))
        }
      } else {
        // 搜索匹配的设备名称（从API搜索）
        const { default: deviceV2Api } = await import('@/api/device-v2')
        const response = await deviceV2Api.list({
          page: 1,
          page_size: 50,
          status: 'active',
          search: query // 使用API的搜索功能
        })
        
        if (response && response.success && response.data) {
          const devices = Array.isArray(response.data) ? response.data : (response.data.items || [])
          const searchQuery = query.toLowerCase()
          
          deviceNameOptions.value = devices
            .filter(device => {
              const deviceName = device.device_name || device.name || ''
              const deviceCode = device.device_code || device.device_number || ''
              const brand = device.manufacturer || device.brand || ''
              const model = device.device_model || device.model || ''
              
              return deviceName.toLowerCase().includes(searchQuery) ||
                     deviceCode.toLowerCase().includes(searchQuery) ||
                     brand.toLowerCase().includes(searchQuery) ||
                     model.toLowerCase().includes(searchQuery)
            })
            .map(device => ({
              label: device.device_name || device.name,
              value: device.device_name || device.name,
              device: device,
              searchText: `${device.device_name || device.name || ''} ${device.device_code || ''} ${device.manufacturer || device.brand || ''} ${device.device_model || device.model || ''}`.toLowerCase()
            }))
        }
      }
      
      console.log(`[RepairRecordForm] 设备名称搜索结果: ${deviceNameOptions.value.length} 个`)
      
    } catch (error) {
      console.error('[RepairRecordForm] 设备名称搜索失败:', error)
      message.error('设备名称搜索失败')
    } finally {
      deviceLoading.value = false
    }
  }, 300)
}

const handleDeviceNameSelect = (deviceName) => {
  if (!deviceName) return
  
  console.log('[RepairRecordForm] 设备名称选择事件触发:', deviceName)
  
  // 查找选中的设备信息（从设备名称选项中）
  const selectedDevice = deviceNameOptions.value.find(item => item.value === deviceName)
  
  if (selectedDevice && selectedDevice.device) {
    const device = selectedDevice.device
    
    console.log('[RepairRecordForm] 通过设备名称找到设备信息:', device)
    
    // 使用nextTick确保DOM更新
    nextTick(() => {
      try {
        // 自动填充设备相关信息
        const deviceCode = device.device_code || device.device_number || device.id
        formData.device_number = deviceCode
        formData.device_name = deviceName
        
        // 填充品牌信息
        const brandValue = device.manufacturer || device.brand
        if (brandValue) {
          const brandExists = brandOptions.value.some(option => option.value === brandValue)
          if (brandExists) {
            formData.brand = brandValue
            console.log('[RepairRecordForm] 填充品牌:', brandValue)
          } else {
            brandOptions.value.push({ label: brandValue, value: brandValue })
            formData.brand = brandValue
            console.log('[RepairRecordForm] 添加并填充新品牌:', brandValue)
          }
        }
        
        // 填充型号信息
        const modelValue = device.device_model || device.model
        if (modelValue) {
          formData.model = modelValue
          console.log('[RepairRecordForm] 填充型号:', modelValue)
        }
        
        // 填充类别信息
        const deviceType = device.device_type || device.category
        let categoryValue = deviceType
        if (deviceType === 'welding') {
          categoryValue = '二氧化碳保护焊机'
        }
        
        if (categoryValue) {
          const categoryExists = categoryOptions.value.some(option => option.value === categoryValue)
          if (categoryExists) {
            formData.category = categoryValue
            console.log('[RepairRecordForm] 填充类别:', categoryValue)
          } else {
            categoryOptions.value.push({ label: categoryValue, value: categoryValue })
            formData.category = categoryValue
            console.log('[RepairRecordForm] 添加并填充新类别:', categoryValue)
          }
        }
        
        // 填充接口类型
        if (device.pin_type) {
          const pinTypeExists = pinTypeOptions.value.some(option => option.value === device.pin_type)
          if (pinTypeExists) {
            formData.pin_type = device.pin_type
          } else {
            pinTypeOptions.value.push({ label: device.pin_type, value: device.pin_type })
            formData.pin_type = device.pin_type
          }
          console.log('[RepairRecordForm] 填充接口类型:', device.pin_type)
        }
        
        // 填充公司信息
        if (device.company) {
          formData.company = device.company
          console.log('[RepairRecordForm] 填充公司:', device.company)
        }
        
        // 填充部门信息
        if (device.department) {
          formData.department = device.department
          console.log('[RepairRecordForm] 填充部门:', device.department)
        }
        
        // 填充车间信息
        if (device.workshop) {
          formData.workshop = device.workshop
          console.log('[RepairRecordForm] 填充车间:', device.workshop)
        }
        
        // 显示成功消息
        const filledFields = ['设备编号', '设备名称']
        if (brandValue) filledFields.push('品牌')
        if (modelValue) filledFields.push('型号')
        if (categoryValue) filledFields.push('类别')
        if (device.pin_type) filledFields.push('接口类型')
        if (device.company) filledFields.push('公司')
        if (device.department) filledFields.push('部门')
        if (device.workshop) filledFields.push('车间')
        
        message.success(`已自动填充: ${filledFields.join('、')}`)
        console.log('[RepairRecordForm] 通过设备名称自动填充完成')
        
      } catch (error) {
        console.error('[RepairRecordForm] 通过设备名称自动填充失败:', error)
        message.error('自动填充失败，请手动输入设备信息')
      }
    })
  } else {
    console.warn('[RepairRecordForm] 未找到设备名称对应的设备信息:', deviceName)
    message.warning('未找到设备信息，请检查设备名称')
  }
}

const handleDeviceNameClear = () => {
  formData.device_name = ''
}

// 设备选项渲染函数
const renderDeviceLabel = (option) => {
  if (!option.device) return option.label
  
  const device = option.device
  return h('div', { class: 'device-option' }, [
    h('div', { class: 'device-code' }, device.device_code || device.device_number),
    h('div', { class: 'device-info' }, `${device.brand || ''} ${device.model || ''} - ${device.category || ''}`)
  ])
}

const renderDeviceTag = (option) => {
  return option.label
}

// 设备名称选项渲染函数
const renderDeviceNameLabel = (option) => {
  if (!option.device) return option.label
  
  const device = option.device
  const deviceName = device.device_name || device.name
  const deviceCode = device.device_code || device.device_number
  
  return h('div', { class: 'device-option' }, [
    h('div', { class: 'device-code' }, deviceName),
    h('div', { class: 'device-info' }, `${deviceCode} - ${device.manufacturer || device.brand || ''} ${device.device_model || device.model || ''}`)
  ])
}

const renderDeviceNameTag = (option) => {
  return option.label
}

// 监听表单数据变化
watch(formData, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })

// 监听recordId变化，自动切换缓存
watch(() => props.recordId, async (newRecordId, oldRecordId) => {
  if (newRecordId !== oldRecordId) {
    console.log(`[RepairRecordForm] 记录ID变化: ${oldRecordId} -> ${newRecordId}`)
    
    try {
      // 切换到新记录，使用原始数据和缓存智能合并
      const switchResult = await formManager.switchToRecord(newRecordId, props.originalData, {
        autoSave: true,
        mergeWithOriginal: true,
        resetIfNoCache: !props.originalData
      })
      
      // 只有真正有缓存且有变化时才通知父组件
      if (switchResult && switchResult.hasCache && switchResult.hasRealChanges) {
        console.log(`[RepairRecordForm] 发送缓存加载事件: ${newRecordId}`)
        emit('cache-loaded', {
          recordId: newRecordId,
          hasCache: true,
          hasRealChanges: true,
          formData: switchResult.formData,
          timestamp: switchResult.timestamp,
          lastModified: switchResult.lastModified
        })
      } else {
        console.log(`[RepairRecordForm] 跳过缓存加载事件: ${newRecordId}`, {
          hasCache: switchResult?.hasCache || false,
          hasRealChanges: switchResult?.hasRealChanges || false
        })
      }
      
    } catch (error) {
      console.error('[RepairRecordForm] 切换记录失败:', error)
      message.error('切换记录失败，请重试')
    }
  }
}, { immediate: true })

// 监听原始数据变化
watch(() => props.originalData, (newOriginalData) => {
  if (newOriginalData && props.recordId) {
    // 如果没有缓存数据，使用原始数据
    if (!formManager.hasCacheData(props.recordId)) {
      console.log('[RepairRecordForm] 使用原始数据更新表单')
      
      // 确保日期字段正确处理
      const processedValue = { ...newOriginalData }
      if (processedValue.repair_date && typeof processedValue.repair_date === 'string') {
        processedValue.repair_date = new Date(processedValue.repair_date).getTime()
      }
      if (processedValue.repair_completion_date && typeof processedValue.repair_completion_date === 'string') {
        processedValue.repair_completion_date = new Date(processedValue.repair_completion_date).getTime()
      }
      
      Object.assign(formData, processedValue)
      
      // 保存到缓存作为基准
      formManager.saveCurrentForm()
    }
  }
}, { deep: true })

// 监听props.modelValue变化（兼容旧的使用方式）
watch(() => props.modelValue, (newValue) => {
  if (newValue && !props.recordId) {
    // 如果没有recordId，使用传统方式
    const processedValue = { ...newValue }
    if (processedValue.repair_date && typeof processedValue.repair_date === 'string') {
      processedValue.repair_date = new Date(processedValue.repair_date).getTime()
    }
    if (processedValue.repair_completion_date && typeof processedValue.repair_completion_date === 'string') {
      processedValue.repair_completion_date = new Date(processedValue.repair_completion_date).getTime()
    }
    Object.assign(formData, processedValue)
  }
}, { immediate: true, deep: true })

// 监听故障状态变化，清空相关字段
watch(() => formData.is_fault, (newValue) => {
  if (!newValue) {
    formData.fault_reason = ''
    formData.damage_category = ''
    formData.fault_content = ''
    formData.fault_location = ''
  }
})

// 暴露验证方法
const validate = async () => {
  try {
    // 先进行基础表单验证
    await formRef.value?.validate()
    
    // 然后进行业务规则验证
    const result = await validateForm(formData)
    
    if (!result.valid) {
      validationErrors.value = result.errors
      const errorMessages = formatValidationErrors(result.errors)
      message.error(`验证失败：${errorMessages.join('; ')}`)
      return false
    }
    
    // 检查数据完整性并显示警告
    const warnings = checkDataIntegrity(formData)
    validationWarnings.value = warnings
    
    if (warnings.length > 0) {
      message.warning(`建议完善以下信息：${warnings.join('; ')}`)
    }
    
    validationErrors.value = {}
    return true
  } catch (error) {
    console.error('Form validation error:', error)
    message.error('表单验证失败，请检查输入内容')
    return false
  }
}

// 暴露重置方法
const resetFields = () => {
  formRef.value?.restoreValidation()
  Object.assign(formData, getDefaultFormData())
  
  // 清除当前记录的缓存
  if (props.recordId) {
    formManager.clearCurrentCache()
  }
}

// 暴露缓存相关方法
const saveToCache = () => {
  formManager.saveCurrentForm()
}

const resetToCache = () => {
  formManager.resetToCache()
}

const hasUnsavedChanges = () => {
  return formManager.hasUnsavedChanges()
}

const getCacheInfo = () => {
  return {
    recordId: props.recordId,
    hasCache: formManager.hasCacheData(props.recordId),
    hasUnsavedChanges: formManager.hasUnsavedChanges(),
    cacheStats: formManager.getCacheStats()
  }
}

// 生命周期管理
let formWatcher = null

onMounted(() => {
  console.log('[RepairRecordForm] 组件挂载，启动表单缓存')
  
  // 启动自动保存和表单变化监听
  formManager.startAutoSave(2000) // 2秒自动保存
  formWatcher = watchFormChanges(formData, { debounce: 1000 })
  
  // 加载设备数据用于搜索
  loadAllDevices()
  
  // 如果有初始recordId，立即切换
  if (props.recordId) {
    formManager.switchToRecord(props.recordId, props.originalData)
  }
})

onUnmounted(() => {
  console.log('[RepairRecordForm] 组件卸载，保存当前表单状态')
  
  // 保存当前表单状态
  formManager.saveCurrentForm()
  
  // 停止自动保存和监听
  formManager.stopAutoSave()
  if (formWatcher) {
    formWatcher()
  }
  
  // 清理设备搜索定时器
  if (deviceSearchTimer.value) {
    clearTimeout(deviceSearchTimer.value)
  }
  
  // 清理设备名称搜索定时器
  if (deviceNameSearchTimer.value) {
    clearTimeout(deviceNameSearchTimer.value)
  }
})

defineExpose({
  validate,
  resetFields,
  saveToCache,
  resetToCache,
  hasUnsavedChanges,
  getCacheInfo,
  
  // 表单管理器方法
  switchToRecord: formManager.switchToRecord,
  getCurrentRecordId: formManager.getCurrentRecordId
})
</script>

<style scoped>
.repair-record-form {
  padding: 16px;
}

.validation-alerts {
  margin-bottom: 16px;
}

.warning-list,
.error-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.warning-list li,
.error-list li {
  margin-bottom: 4px;
}

.form-section {
  margin-bottom: 24px;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  padding: 16px;
  background-color: #fafafa;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #18a058;
  padding-bottom: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-items: start;
}

.form-item {
  margin-bottom: 0;
}

.form-item.full-width {
  grid-column: 1 / -1;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-section {
    padding: 12px;
  }
  
  .repair-record-form {
    padding: 8px;
  }
}

/* 表单样式优化 */
:deep(.n-form-item-label) {
  font-weight: 500;
}

:deep(.n-input), :deep(.n-select), :deep(.n-date-picker) {
  border-radius: 4px;
}

:deep(.n-radio-group) {
  display: flex;
  gap: 16px;
}

/* 设备选项样式 */
.device-option {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}

.device-code {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.device-info {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

/* 设备选择器样式优化 */
:deep(.n-base-selection .n-base-selection-label) {
  font-weight: 500;
}

:deep(.n-base-select-menu .n-base-select-option) {
  padding: 8px 12px;
}

:deep(.n-base-select-menu .n-base-select-option:hover) {
  background-color: #f0f8ff;
}
</style>