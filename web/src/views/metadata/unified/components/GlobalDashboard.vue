<template>
  <div class="global-dashboard">
    <div class="search-section">
      <div class="search-header">
        <h2 class="title">全局资源概览</h2>
        <p class="subtitle">搜索并管理所有设备类型的字段、模型和报警规则</p>
      </div>
      <div class="search-box">
        <n-input
          v-model:value="keyword"
          size="large"
          round
          placeholder="输入关键词搜索字段、模型或报警规则..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon :component="SearchOutline" />
          </template>
          <template #suffix>
            <n-button circle type="primary" @click="handleSearch" :loading="loading">
              <template #icon>
                <n-icon :component="ArrowForwardOutline" />
              </template>
            </n-button>
          </template>
        </n-input>
      </div>
    </div>

    <div class="content-section" v-if="hasSearched || keyword">
      <n-grid :x-gap="24" :y-gap="24" cols="1 800:3">
        <!-- 字段结果 -->
        <n-grid-item>
          <n-card title="字段定义" :bordered="false" class="result-card">
            <template #header-extra>
              <n-tag type="info" round size="small">{{ results.fields.length }}</n-tag>
            </template>
            <div class="result-list">
              <n-empty v-if="results.fields.length === 0" description="无匹配字段" />
              <n-list v-else hoverable clickable>
                <n-list-item v-for="item in results.fields" :key="item.id" @click="handleSelect(item, 'fields')">
                  <n-thing :title="item.field_name">
                    <template #description>
                      <n-space size="small" style="margin-top: 4px;">
                        <n-tag size="small" :bordered="false">{{ item.field_code }}</n-tag>
                        <n-tag size="small" type="primary" :bordered="false">
                          {{ item.device_type_code }}
                        </n-tag>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </div>
          </n-card>
        </n-grid-item>

        <!-- 模型结果 -->
        <n-grid-item>
          <n-card title="模型配置" :bordered="false" class="result-card">
            <template #header-extra>
              <n-tag type="success" round size="small">{{ results.models.length }}</n-tag>
            </template>
            <div class="result-list">
              <n-empty v-if="results.models.length === 0" description="无匹配模型" />
              <n-list v-else hoverable clickable>
                <n-list-item v-for="item in results.models" :key="item.id" @click="handleSelect(item, 'models')">
                  <n-thing :title="item.model_name">
                    <template #description>
                      <n-space size="small" style="margin-top: 4px;">
                        <n-tag size="small" :bordered="false">{{ item.model_code }}</n-tag>
                        <n-tag size="small" type="primary" :bordered="false">
                          {{ item.device_type_code }}
                        </n-tag>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </div>
          </n-card>
        </n-grid-item>

        <!-- 报警结果 -->
        <n-grid-item>
          <n-card title="报警规则" :bordered="false" class="result-card">
            <template #header-extra>
              <n-tag type="warning" round size="small">{{ results.alarms.length }}</n-tag>
            </template>
            <div class="result-list">
              <n-empty v-if="results.alarms.length === 0" description="无匹配规则" />
              <n-list v-else hoverable clickable>
                <n-list-item v-for="item in results.alarms" :key="item.id" @click="handleSelect(item, 'alarms')">
                  <n-thing :title="item.rule_name">
                    <template #description>
                      <n-space size="small" style="margin-top: 4px;">
                        <n-tag size="small" :bordered="false">{{ item.metric_field }}</n-tag>
                        <n-tag size="small" type="primary" :bordered="false">
                          {{ item.device_type_code }}
                        </n-tag>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>
    </div>
    
    <div v-else class="welcome-section">
      <n-empty description="请在上方的搜索框中输入关键词，或直接选择左上角的设备类型开始配置">
        <template #extra>
          <div class="stats-preview">
            <n-grid :x-gap="12" cols="3">
              <n-grid-item>
                <div class="stat-item">
                  <div class="stat-value">字段</div>
                  <div class="stat-label">定义设备属性</div>
                </div>
              </n-grid-item>
              <n-grid-item>
                <div class="stat-item">
                  <div class="stat-value">模型</div>
                  <div class="stat-label">配置数据处理</div>
                </div>
              </n-grid-item>
              <n-grid-item>
                <div class="stat-item">
                  <div class="stat-value">报警</div>
                  <div class="stat-label">设置监控规则</div>
                </div>
              </n-grid-item>
            </n-grid>
          </div>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { 
  NInput, NButton, NIcon, NGrid, NGridItem, NCard, NList, NListItem, 
  NThing, NTag, NSpace, NEmpty, useMessage 
} from 'naive-ui'
import { SearchOutline, ArrowForwardOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'
import { alarmRulesApi } from '@/api/alarm-rules'

const emit = defineEmits(['select'])
const message = useMessage()

const keyword = ref('')
const loading = ref(false)
const hasSearched = ref(false)

const results = reactive({
  fields: [],
  models: [],
  alarms: []
})

const handleSearch = async () => {
  if (!keyword.value.trim()) {
    hasSearched.value = false
    return
  }
  
  loading.value = true
  hasSearched.value = true
  
  try {
    // 并行请求三个接口
    const [fieldsRes, modelsRes, alarmsRes] = await Promise.allSettled([
      dataModelApi.getFields({ search: keyword.value, page_size: 20 }),
      dataModelApi.getModels({ search: keyword.value, page_size: 20 }),
      alarmRulesApi.list({ search: keyword.value, page_size: 20 })
    ])
    
    // 处理字段结果
    if (fieldsRes.status === 'fulfilled' && fieldsRes.value.success) {
      results.fields = fieldsRes.value.data.items || fieldsRes.value.data || []
    } else {
      results.fields = []
    }
    
    // 处理模型结果
    if (modelsRes.status === 'fulfilled' && modelsRes.value.success) {
      results.models = modelsRes.value.data.items || modelsRes.value.data || []
    } else {
      results.models = []
    }
    
    // 处理报警结果
    if (alarmsRes.status === 'fulfilled' && alarmsRes.value.success) {
      results.alarms = alarmsRes.value.data.items || alarmsRes.value.data || []
    } else {
      results.alarms = []
    }
    
  } catch (error) {
    console.error('全局搜索失败:', error)
    message.error('搜索过程中发生错误')
  } finally {
    loading.value = false
  }
}

const handleSelect = (item, tab) => {
  emit('select', {
    deviceType: item.device_type_code,
    tab: tab,
    item: item
  })
}
</script>

<style scoped>
.global-dashboard {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-section {
  text-align: center;
  margin-bottom: 48px;
}

.title {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--n-text-color);
}

.subtitle {
  font-size: 14px;
  color: var(--n-text-color-3);
  margin-bottom: 32px;
}

.search-box {
  max-width: 600px;
  margin: 0 auto;
}

.result-card {
  height: 100%;
  background-color: var(--n-card-color);
  border-radius: 8px;
  box-shadow: 0 1px 2px -2px rgba(0, 0, 0, 0.08), 0 3px 6px 0 rgba(0, 0, 0, 0.06), 0 5px 12px 4px rgba(0, 0, 0, 0.04); 
}

.result-list {
  max-height: 400px;
  overflow-y: auto;
}

.welcome-section {
  margin-top: 64px;
}

.stats-preview {
  margin-top: 24px;
  padding: 24px;
  background-color: var(--n-action-color);
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--n-text-color-3);
}
</style>