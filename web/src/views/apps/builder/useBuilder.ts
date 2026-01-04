import { ref, computed } from 'vue'
import type { ComponentNode, ComponentType } from './types'

// Global state for the builder (could be moved to Pinia)
const components = ref<ComponentNode[]>([])
const selectedId = ref<string | null>(null)

export function useBuilder() {
  const selectedComponent = computed(() => 
    components.value.find(c => c.id === selectedId.value) || null
  )

  const addComponent = (type: ComponentType) => {
    const id = Math.random().toString(36).substr(2, 9)
    components.value.push({
      id,
      type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
      props: getDefaultProps(type),
      children: type === 'container' ? [] : undefined
    })
    selectedId.value = id
  }

  const selectComponent = (id: string | null) => {
    selectedId.value = id
  }

  const updateProps = (id: string, newProps: any) => {
    const comp = components.value.find(c => c.id === id)
    if (comp) {
      comp.props = { ...comp.props, ...newProps }
    }
  }
  
  const removeComponent = (id: string) => {
      components.value = components.value.filter(c => c.id !== id)
      if (selectedId.value === id) selectedId.value = null
  }

  return {
    components,
    selectedId,
    selectedComponent,
    addComponent,
    selectComponent,
    updateProps,
    removeComponent
  }
}

function getDefaultProps(type: ComponentType) {
  switch (type) {
    case 'button': return { type: 'primary', content: 'Click Me' }
    case 'text': return { content: 'Text Block', fontSize: 14, fontWeight: 'normal' }
    case 'input': return { placeholder: 'Input here...' }
    case 'statistic': return { label: 'Metric', value: '123.45', suffix: 'unit' }
    case 'container': return { padding: 20, bordered: true, title: 'Container' }
    case 'chart': return { title: 'Time Series', type: 'line', height: 300 }
    default: return {}
  }
}
