<template>
  <div class="asset-create-page">
    <n-card title="新建资产">
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
                <n-input v-model:value="basicForm.code" placeholder="请输入资产编码" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="资产名称" path="name">
                <n-input v-model:value="basicForm.name" placeholder="请输入资产名称" />
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
          </n-grid>
        </n-form>

        <n-divider>信号初始值（可选）</n-divider>

        <!-- 动态表单 -->
        <DynamicAssetForm
          v-if="currentCategory?.id"
          ref="dynamicFormRef"
          :category-id="currentCategory.id"
          :show-header="false"
          :show-actions="false"
          label-placement="top"
        />

        <!-- 操作按钮 -->
        <div class="form-actions">
          <n-space>
            <n-button type="primary" :loading="submitting" @click="handleSubmit">
              创建资产
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
import { useRouter } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NDatePicker, NButton, NSpace, 
  NGrid, NGi, NDivider, NSpin, useMessage
} from 'naive-ui'
import { assetApi } from '@/api/v3/platform'
import { DynamicAssetForm } from '@/components/platform'

const router = useRouter()
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

// 基本信息表单
const basicForm = reactive({
  code: '',
  name: '',
  location: '',
  manufacturer: '',
  model: '',
  serial_number: '',
  install_date: null,
  department: '',
  team: ''
})

// 验证规则
const basicRules = {
  code: [
    { required: true, message: '请输入资产编码', trigger: ['blur', 'input'] }
  ],
  name: [
    { required: true, message: '请输入资产名称', trigger: ['blur', 'input'] }
  ]
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
        message.error('请检查信号初始值')
        return
      }
      attributes = dynamicFormRef.value.getFormData()
    }

    submitting.value = true

    // 构建提交数据
    const submitData = {
      ...basicForm,
      category_id: currentCategory.value.id,
      attributes,
      install_date: basicForm.install_date 
        ? new Date(basicForm.install_date).toISOString().split('T')[0] 
        : null
    }

    await assetApi.create(submitData)
    message.success('创建成功')
    router.push(`/assets/${categoryCode.value}/list`)
  } catch (error) {
    if (error.message) {
      message.error(error.message)
    }
    console.error('创建资产失败:', error)
  } finally {
    submitting.value = false
  }
}

// 重置表单
function handleReset() {
  basicFormRef.value?.restoreValidation()
  Object.keys(basicForm).forEach(key => {
    basicForm[key] = key === 'install_date' ? null : ''
  })
  dynamicFormRef.value?.resetForm()
}

// 返回列表
function handleBack() {
  router.push(`/assets/${categoryCode.value}/list`)
}
</script>

<style scoped>
.asset-create-page {
  max-width: 1200px;
  margin: 0 auto;
}

.form-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--n-border-color);
}
</style>
