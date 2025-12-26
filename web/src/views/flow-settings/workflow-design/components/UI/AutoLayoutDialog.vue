<template>
  <el-dialog
    v-model="visible"
    title="自动布局"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="auto-layout-dialog">
      <el-form :model="layoutConfig" label-width="100px">
        <el-form-item label="布局算法">
          <el-select v-model="layoutConfig.algorithm" style="width: 100%">
            <el-option 
              v-for="item in layoutAlgorithms" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value"
            >
              <div class="algorithm-option">
                <span>{{ item.label }}</span>
                <span class="description">{{ item.description }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="布局方向" v-if="showDirection">
          <el-radio-group v-model="layoutConfig.direction">
            <el-radio-button value="TB">从上到下</el-radio-button>
            <el-radio-button value="LR">从左到右</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="节点间距">
          <el-slider 
            v-model="layoutConfig.nodeSpacing" 
            :min="50" 
            :max="300" 
            :step="10"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="层级间距">
          <el-slider 
            v-model="layoutConfig.levelSpacing" 
            :min="80" 
            :max="400" 
            :step="10"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="边距">
          <el-slider 
            v-model="layoutConfig.padding" 
            :min="20" 
            :max="200" 
            :step="10"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="对齐方式">
          <el-radio-group v-model="layoutConfig.alignment">
            <el-radio-button value="start">左对齐</el-radio-button>
            <el-radio-button value="center">居中</el-radio-button>
            <el-radio-button value="end">右对齐</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <div class="preview-info">
        <el-alert 
          :title="previewInfo" 
          type="info" 
          :closable="false"
          show-icon
        />
      </div>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="default" @click="handleAutoSelect">
        智能推荐
      </el-button>
      <el-button type="primary" @click="handleApply" :loading="applying">
        应用布局
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  hierarchicalLayout, 
  forceDirectedLayout, 
  circularLayout, 
  gridLayout,
  treeLayout,
  layeredLayout,
  organicLayout,
  autoLayout,
  LAYOUT_TYPES 
} from '../../utils/layoutAlgorithms'

const props = defineProps({
  modelValue: Boolean,
  nodes: {
    type: Array,
    default: () => [],
  },
  connections: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'apply'])

const visible = ref(false)
const applying = ref(false)

const layoutConfig = reactive({
  algorithm: 'hierarchical',
  direction: 'TB',
  nodeSpacing: 120,
  levelSpacing: 150,
  padding: 50,
  alignment: 'center',
})

const layoutAlgorithms = [
  { value: 'hierarchical', label: '层次布局', description: '适合流程图，从上到下或从左到右排列' },
  { value: 'forceDirected', label: '力导向布局', description: '自然分布，适合复杂网络' },
  { value: 'circular', label: '圆形布局', description: '节点围绕圆形排列' },
  { value: 'grid', label: '网格布局', description: '规则的网格排列' },
  { value: 'tree', label: '树形布局', description: '适合树状结构' },
  { value: 'layered', label: '分层布局', description: '按拓扑顺序分层' },
  { value: 'organic', label: '有机布局', description: '自然、有机的分布效果' },
]

const showDirection = computed(() => {
  return ['hierarchical', 'tree', 'layered'].includes(layoutConfig.algorithm)
})

const previewInfo = computed(() => {
  const nodeCount = props.nodes.length
  const connCount = props.connections.length
  return `当前工作流包含 ${nodeCount} 个节点和 ${connCount} 条连接`
})

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleAutoSelect = () => {
  // 使用智能推荐算法
  const result = autoLayout(props.nodes, props.connections, {
    nodeSpacing: layoutConfig.nodeSpacing,
    levelSpacing: layoutConfig.levelSpacing,
    padding: layoutConfig.padding,
    direction: layoutConfig.direction,
    alignment: layoutConfig.alignment,
  })
  
  layoutConfig.algorithm = result.algorithm
  ElMessage.info(`推荐使用 ${getAlgorithmLabel(result.algorithm)}：${result.reason}`)
}

const getAlgorithmLabel = (algorithm) => {
  const item = layoutAlgorithms.find(a => a.value === algorithm)
  return item ? item.label : algorithm
}

const handleApply = () => {
  applying.value = true
  
  try {
    const config = {
      nodeSpacing: layoutConfig.nodeSpacing,
      levelSpacing: layoutConfig.levelSpacing,
      padding: layoutConfig.padding,
      direction: layoutConfig.direction,
      alignment: layoutConfig.alignment,
    }
    
    let layoutedNodes
    
    // 转换连接格式
    const connections = props.connections.map(conn => ({
      fromNodeId: conn.fromNodeId || conn.from_node_id,
      toNodeId: conn.toNodeId || conn.to_node_id,
    }))
    
    switch (layoutConfig.algorithm) {
      case 'hierarchical':
        layoutedNodes = hierarchicalLayout(props.nodes, connections, config)
        break
      case 'forceDirected':
        layoutedNodes = forceDirectedLayout(props.nodes, connections, config)
        break
      case 'circular':
        layoutedNodes = circularLayout(props.nodes, connections, config)
        break
      case 'grid':
        layoutedNodes = gridLayout(props.nodes, connections, config)
        break
      case 'tree':
        layoutedNodes = treeLayout(props.nodes, connections, config)
        break
      case 'layered':
        layoutedNodes = layeredLayout(props.nodes, connections, config)
        break
      case 'organic':
        layoutedNodes = organicLayout(props.nodes, connections, config)
        break
      default:
        layoutedNodes = hierarchicalLayout(props.nodes, connections, config)
    }
    
    emit('apply', layoutedNodes)
    visible.value = false
    ElMessage.success('布局应用成功')
  } catch (error) {
    console.error('布局失败:', error)
    ElMessage.error('布局应用失败')
  } finally {
    applying.value = false
  }
}
</script>

<style scoped lang="scss">
.auto-layout-dialog {
  .algorithm-option {
    display: flex;
    flex-direction: column;
    
    .description {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .preview-info {
    margin-top: 16px;
  }
}
</style>
