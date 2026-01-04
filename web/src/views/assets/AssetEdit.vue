<template>
  <div class="asset-edit-page">
    <n-card title="编辑资产">
      <template #header-extra>
        <n-button @click="handleBack">返回</n-button>
      </template>

      <n-spin :show="loading">
        <!-- 基本信息 -->
        <n-form
          ref="basicFormRef"
          :model="basicForm"
          :rules="basicRules"
          label-placement="top"
        >
          <n-grid :cols="3" :x-gap="16">
            <n-gi>
              <n-form-item label="资产编码" path="code">
                <n-input v-model:value="basicForm.code" placeholder="请输入资产编码" disabled />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="资产名称" path="name">
                <n-input v-model:value="basicForm.name" placeholder="请输入资产名称" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="状态" path="status">
                <n-select
                  v-model:value="basicForm.status"
                  :options="statusOptions"
                  placeholder="请选择状态"
                />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="位置" path="location">
                <n-input v-model:value="basicForm.location" placeholder="请输入位置" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="制造商" path="manufacturer">
                <n-input v-model:value="basicForm.manufacturer" placeholder="请输入制造商" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="型号" path="model">
                <n-input v-model:value="basicForm.model" placeholder="请输入型号" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="序列号" path="serial_number">
                <n-input v-model:value="basicForm.serial_number" placeholder="请输入序列号" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="安装日期" path="install_date">
                <n-date-picker v-model:value="basicForm.install_date" type="date" style="width: 100%" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="所属部门" path="department">
                <n-input v-model:value="basicForm.department" placeholder="请输入所属部门" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="所属班组" path="team">
                <n-input v-model:value="basicForm.team" placeholder="请输入所属班组" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="IP地址" path="ip_address">
                <n-input v-model:value="basicForm.ip_address" placeholder="请输入IP地址" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="MAC地址" path="mac_address">
                <n-input v-model:value="basicForm.mac_address" placeholder="请输入MAC地址" />
              </n-form-item>
            </n-gi>
          </n-grid>
        </n-form>

        <n-divider>扩展属性</n-divider>

        <!-- 动态表单 -->
        <DynamicAssetForm
          v-if="currentCategory?.id"
          ref="dynamicFormRef"
          :category-id="currentCategory.id"
          :initial-data="attributesData"
          :show-header="false"
          :show-actions="false"
          label-placement="top"
        />

        <!-- 操作按钮 -->
        <div class="form-actions">
          <n-space>
            <n-button type="primary" :loading="submitting" @click="handleSubmit">
              保存修改
            </n-button>
            <n-button @click="handleReset">重置</n-button>
            <n-button @click="handleBack">取消</n-button>
          </n-space>
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NSelect, NDatePicker, NButton, NSpace, 
  NGrid, NGi, NDivider, NSpin, useMessage
} from 'naive-ui'
import { assetApi } from '@/api/v4/assets'
import { DynamicAssetForm } from '@/components/platform'

const router = useRouter()
const route = useRoute()
const message = useMessage()

// 注入类别信息
const currentCategory = inject('currentCategory')
const categoryCode = inject('categoryCode')

// 表单引用
const basicFormRef = ref(null)
const dynamicFormRef = ref(null)

// 状态
const loading = ref(false)
const submitting = ref(false)
const attributesData = ref({})

// 状态选项
const statusOptions = [
  { label: '在线', value: 'online' },
  { label: '离线', value: 'offline' },
  { label: '故障', value: 'error' },
  { label: '维护中', value: 'maintenance' }
]

// 基本信息表单
const basicForm = reactive({
  code: '',
  name: '',
  status: 'offline',
  location: '',
  manufacturer: '',
  model: '',
  serial_number: '',
  install_date: null,
  department: '',
  team: '',
  ip_address: '',
  mac_address: ''
})

// 验证规则
const basicRules = {
  name: [
    { required: true, message: '请输入资产名称', trigger: ['blur', 'input'] }
  ]
}

// 加载资产数据
async function loadAsset() {
  const assetId = route.params.id
  if (!assetId) return

  loading.value = true
  try {
    const response = await assetApi.getById(assetId)
    const asset = response.data || response

    // 填充基本信息
    Object.keys(basicForm).forEach(key => {
      if (asset[key] !== undefined) {
        if (key === 'install_date' && asset[key]) {
          basicForm[key] = new Date(asset[key]).getTime()
        } else {
          basicForm[key] = asset[key]
        }
      }
    })

    // 填充扩展属性
    attributesData.value = asset.attributes || {}
  } catch (error) {
    message.error('加载资产数据失败')
    console.error('加载资产数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 提交表单
async function handleSubmit() {
  try {
    // 验证基本信息表单
    await basicFormRef.value?.validate()

    // 获取动态表单数据
    let attributes = {}
    if (dynamicFormRef.value) {
      const isValid = await dynamicFormRef.value.validate()
      if (!isValid) {
        message.error('请检查扩展属性')
        return
      }
      attributes = dynamicFormRef.value.getFormData()
    }

    submitting.value = true

    // 构建提交数据
    const submitData = {
      ...basicForm,
      attributes,
      install_date: basicForm.install_date 
        ? new Date(basicForm.install_date).toISOString().split('T')[0] 
        : null
    }

    // 移除不可编辑的字段
    delete submitData.code

    await assetApi.update(route.params.id, submitData)
    message.success('保存成功')
    router.push(`/assets/${categoryCode.value}/${route.params.id}`)
  } catch (error) {
    if (error.message) {
      message.error(error.message)
    }
    console.error('保存资产失败:', error)
  } finally {
    submitting.value = false
  }
}

// 重置表单
function handleReset() {
  loadAsset()
}

// 返回
function handleBack() {
  router.push(`/assets/${categoryCode.value}/${route.params.id}`)
}

// 初始化
onMounted(() => {
  loadAsset()
})
</script>

<style scoped>
.asset-edit-page {
  max-width: 1200px;
  margin: 0 auto;
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
}
</style>
