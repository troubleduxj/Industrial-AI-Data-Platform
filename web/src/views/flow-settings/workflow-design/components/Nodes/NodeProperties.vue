<template>
  <div class="node-properties">
    <div class="properties-header">
      <h3 class="properties-title">
        <span class="node-icon">{{ nodeIcon }}</span>
        {{ nodeTitle }}
      </h3>
      <button class="close-btn" @click="handleClose">
        <span class="icon">✕</span>
      </button>
    </div>

    <div v-if="selectedNode" class="properties-content">
      <!-- Basic Information -->
      <div class="property-section">
        <h4 class="section-title">基本信息</h4>

        <div class="property-item">
          <label class="property-label">节点名称</label>
          <input
            v-model="nodeData.name"
            type="text"
            class="property-input"
            placeholder="请输入节点名称"
            @input="handlePropertyChange"
          />
        </div>

        <div class="property-item">
          <label class="property-label">节点描述</label>
          <textarea
            v-model="nodeData.description"
            class="property-textarea"
            placeholder="请输入节点描述"
            rows="3"
            @input="handlePropertyChange"
          ></textarea>
        </div>

        <div class="property-item">
          <label class="property-label">节点类型</label>
          <select v-model="nodeData.type" class="property-select" @change="handleTypeChange">
            <option v-for="type in nodeTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Position and Size -->
      <div class="property-section">
        <h4 class="section-title">位置和尺寸</h4>

        <div class="property-row">
          <div class="property-item">
            <label class="property-label">X 坐标</label>
            <input
              v-model.number="nodeData.position.x"
              type="number"
              class="property-input"
              @input="handlePropertyChange"
            />
          </div>
          <div class="property-item">
            <label class="property-label">Y 坐标</label>
            <input
              v-model.number="nodeData.position.y"
              type="number"
              class="property-input"
              @input="handlePropertyChange"
            />
          </div>
        </div>

        <div class="property-row">
          <div class="property-item">
            <label class="property-label">宽度</label>
            <input
              v-model.number="nodeData.width"
              type="number"
              class="property-input"
              min="100"
              @input="handlePropertyChange"
            />
          </div>
          <div class="property-item">
            <label class="property-label">高度</label>
            <input
              v-model.number="nodeData.height"
              type="number"
              class="property-input"
              min="60"
              @input="handlePropertyChange"
            />
          </div>
        </div>
      </div>

      <!-- Node-specific Properties -->
      <div v-if="nodeSpecificProperties.length > 0" class="property-section">
        <h4 class="section-title">节点配置</h4>

        <div v-for="prop in nodeSpecificProperties" :key="prop.key" class="property-item">
          <label class="property-label">{{ prop.label }}</label>

          <!-- Text input -->
          <input
            v-if="prop.type === 'text'"
            v-model="nodeData.properties[prop.key]"
            type="text"
            class="property-input"
            :placeholder="prop.placeholder"
            @input="handlePropertyChange"
          />

          <!-- Number input -->
          <input
            v-else-if="prop.type === 'number'"
            v-model.number="nodeData.properties[prop.key]"
            type="number"
            class="property-input"
            :min="prop.min"
            :max="prop.max"
            :step="prop.step"
            @input="handlePropertyChange"
          />

          <!-- Select dropdown -->
          <select
            v-else-if="prop.type === 'select'"
            v-model="nodeData.properties[prop.key]"
            class="property-select"
            @change="handlePropertyChange"
          >
            <option v-for="option in prop.options" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>

          <!-- Boolean checkbox -->
          <label v-else-if="prop.type === 'boolean'" class="property-checkbox">
            <input
              v-model="nodeData.properties[prop.key]"
              type="checkbox"
              @change="handlePropertyChange"
            />
            <span class="checkbox-label">{{ prop.description }}</span>
          </label>

          <!-- Textarea -->
          <textarea
            v-else-if="prop.type === 'textarea'"
            v-model="nodeData.properties[prop.key]"
            class="property-textarea"
            :placeholder="prop.placeholder"
            :rows="prop.rows || 3"
            @input="handlePropertyChange"
          ></textarea>
        </div>
      </div>

      <!-- Validation and Status -->
      <div class="property-section">
        <h4 class="section-title">状态</h4>

        <div class="property-item">
          <label class="property-checkbox">
            <input v-model="nodeData.disabled" type="checkbox" @change="handlePropertyChange" />
            <span class="checkbox-label">禁用节点</span>
          </label>
        </div>

        <div v-if="validationErrors.length > 0" class="validation-status">
          <h5 class="validation-title">验证错误</h5>
          <ul class="validation-list">
            <li v-for="error in validationErrors" :key="error" class="validation-error">
              {{ error }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="properties-actions">
      <button class="action-btn primary" @click="handleSave">保存</button>
      <button class="action-btn" @click="handleReset">重置</button>
      <button class="action-btn danger" @click="handleDelete">删除节点</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NODE_TYPES } from '../../utils/nodeTypes'

// Props
const props = defineProps({
  selectedNode: {
    type: Object,
    default: null,
  },
})

// Emits
const emit = defineEmits(['update-node', 'delete-node', 'close'])

// Reactive data
const nodeData = ref({})
const validationErrors = ref([])

// Computed properties
const nodeTitle = computed(() => {
  return nodeData.value.name || nodeData.value.type || '未知节点'
})

const nodeIcon = computed(() => {
  const nodeType = NODE_TYPES[nodeData.value.type]
  return nodeType?.icon || '📦'
})

const nodeTypes = computed(() => {
  return Object.entries(NODE_TYPES).map(([key, type]) => ({
    value: key,
    label: type.name,
  }))
})

const nodeSpecificProperties = computed(() => {
  const nodeType = NODE_TYPES[nodeData.value.type]
  return nodeType?.properties || []
})

// Watch for selected node changes
watch(
  () => props.selectedNode,
  (newNode) => {
    if (newNode) {
      nodeData.value = JSON.parse(JSON.stringify(newNode))
      validateNode()
    }
  },
  { immediate: true, deep: true }
)

// Methods
function handlePropertyChange() {
  validateNode()
  emit('update-node', { ...nodeData.value })
}

function handleTypeChange() {
  // Reset properties when type changes
  nodeData.value.properties = {}
  handlePropertyChange()
}

function validateNode() {
  validationErrors.value = []

  if (!nodeData.value.name?.trim()) {
    validationErrors.value.push('节点名称不能为空')
  }

  if (!nodeData.value.type) {
    validationErrors.value.push('必须选择节点类型')
  }

  // Validate node-specific properties
  const nodeType = NODE_TYPES[nodeData.value.type]
  if (nodeType?.properties) {
    nodeType.properties.forEach((prop) => {
      if (prop.required && !nodeData.value.properties[prop.key]) {
        validationErrors.value.push(`${prop.label}是必填项`)
      }
    })
  }
}

function handleSave() {
  validateNode()
  if (validationErrors.value.length === 0) {
    emit('update-node', { ...nodeData.value })
  }
}

function handleReset() {
  if (props.selectedNode) {
    nodeData.value = JSON.parse(JSON.stringify(props.selectedNode))
    validateNode()
  }
}

function handleDelete() {
  if (confirm('确定要删除这个节点吗？')) {
    emit('delete-node', nodeData.value.id)
  }
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.node-properties {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-left: 1px solid #e8e8e8;
}

.properties-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.properties-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.node-icon {
  font-size: 18px;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 4px;
  color: #8c8c8c;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #262626;
}

.properties-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.property-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.property-item {
  margin-bottom: 12px;
}

.property-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.property-label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #595959;
}

.property-input,
.property-select,
.property-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.property-input:focus,
.property-select:focus,
.property-textarea:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.property-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 14px;
  color: #262626;
}

.validation-status {
  margin-top: 16px;
  padding: 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
}

.validation-title {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #cf1322;
}

.validation-list {
  margin: 0;
  padding-left: 16px;
}

.validation-error {
  font-size: 12px;
  color: #cf1322;
}

.properties-actions {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
}

.action-btn {
  flex: 1;
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #ffffff;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  border-color: #40a9ff;
  color: #1890ff;
}

.action-btn.primary {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.action-btn.primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

.action-btn.danger {
  border-color: #ff4d4f;
  color: #ff4d4f;
}

.action-btn.danger:hover {
  background: #ff4d4f;
  color: white;
}
</style>
