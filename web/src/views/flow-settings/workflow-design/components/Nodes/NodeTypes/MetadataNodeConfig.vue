<template>
  <div class="node-config">
    <div class="form-item">
      <label>选择模型</label>
      <select v-model="config.model_code" @change="updateConfig">
        <option value="">请选择...</option>
        <option v-for="model in models" :key="model.model_code" :value="model.model_code">
          {{ model.model_name }} ({{ model.model_code }})
        </option>
      </select>
    </div>
    <div class="form-info" v-if="config.model_code">
      <p>已选择: {{ config.model_code }}</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios' // Assuming axios is available or use fetch

export default {
  name: 'MetadataNodeConfig',
  props: {
    node: {
      type: Object,
      required: true
    }
  },
  emits: ['update'],
  setup(props, { emit }) {
    const config = ref({
      model_code: props.node.data?.model_code || ''
    })

    const models = ref([])

    onMounted(async () => {
      try {
        // Fetch models from API
        // Using relative path or absolute based on proxy
        const res = await fetch('/api/v2/metadata/models')
        if (res.ok) {
            const data = await res.json()
            // API returns { code: 200, data: { items: [...] } } or similar
            // Adjust based on actual API response
            if (data.data && Array.isArray(data.data.items)) {
                models.value = data.data.items
            } else if (Array.isArray(data.data)) {
                models.value = data.data
            } else {
                // Fallback
                models.value = []
            }
        }
      } catch (e) {
        console.error('Failed to load models', e)
        // Mock for fallback
        models.value = [
            { model_name: '电压异常检测', model_code: 'VOLTAGE_ANOMALY' },
            { model_name: '温度趋势分析', model_code: 'TEMP_TREND' }
        ]
      }
    })

    const updateConfig = () => {
      emit('update', { ...props.node.data, ...config.value })
    }

    watch(() => props.node, (newNode) => {
      if (newNode.data) {
        config.value = { ...config.value, ...newNode.data }
      }
    }, { deep: true })

    return {
      config,
      models,
      updateConfig
    }
  }
}
</script>

<style scoped>
.node-config {
  padding: 10px;
}
.form-item {
  margin-bottom: 12px;
}
.form-item label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}
.form-item select {
  width: 100%;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}
.form-info {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
