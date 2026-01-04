export type ComponentType = 'container' | 'button' | 'text' | 'input' | 'statistic' | 'chart';

export interface ComponentNode {
  id: string;
  type: ComponentType;
  label: string;
  props: Record<string, any>;
  children?: ComponentNode[]; // For containers
}

export interface PageSchema {
  id: string;
  name: string;
  components: ComponentNode[];
}
