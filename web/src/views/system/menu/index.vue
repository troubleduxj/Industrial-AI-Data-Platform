<script setup lang="ts">
import {
  h,
  onMounted,
  ref,
  resolveDirective,
  withDirectives,
  onActivated,
  getCurrentInstance,
} from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSwitch,
  NTreeSelect,
  NRadio,
  NRadioGroup,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import IconPicker from '@/components/icon/IconPicker.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import PermissionButton from '@/components/Permission/PermissionButton.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables/useCRUD'
import { useMenuBatchDelete } from '@/composables/useBatchDelete'
import api from '@/api'
import systemV2Api, { menuApi } from '@/api/system-v2'

// 导入消息提示
import { useMessage } from 'naive-ui'

// 在setup函数内部获取message实例
const $message = useMessage()

defineOptions({ name: 'SystemMenu' })

const $table = ref<any>(null)
const queryItems = ref<Record<string, any>>({})
const vPermission = resolveDirective('permission')

// 展开状态管理
const expandedRowKeys = ref<(string | number)[]>([])

// 表单初始化内容
const initForm = {
  name: '',
  path: '',
  menu_type: 'catalog',
  icon: '',
  order: 1,
  parent_id: 0,
  is_hidden: false,
  component: '',
  keepalive: true,
  redirect: '',
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete: originalHandleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '菜单',
  initForm,
  doCreate: systemV2Api.createMenu,
  doDelete: systemV2Api.deleteMenu,
  doUpdate: systemV2Api.updateMenu,
  refresh: () => $table.value?.handleSearch(),
})

// 自定义删除处理函数，提供更友好的错误提示
const handleDelete = async (params, showModal = true) => {
  try {
    // 检查menuApi是否可用，如果不可用则使用备用方案
    let checkUsageApi = menuApi?.checkUsage
    if (!checkUsageApi) {
      console.warn('menuApi.checkUsage不可用，尝试使用systemV2Api.menuApi')
      checkUsageApi = systemV2Api?.menuApi?.checkUsage
    }

    if (!checkUsageApi) {
      console.error('无法找到checkUsage API方法')
      $message.error('菜单使用情况检查功能不可用，将直接尝试删除')
      // 如果检查功能不可用，直接执行删除
      await originalHandleDelete(params, showModal)
      return
    }

    // 删除前检查菜单使用情况
    const usageResult = await checkUsageApi(params.id)
    const usageData = usageResult.data

    if (!usageData.can_delete) {
      // 构建详细的提示信息
      let messageText = '无法删除该菜单：\n'
      usageData.blocking_reasons.forEach((reason) => {
        if (reason.type === 'HAS_CHILDREN') {
          messageText += `• 该菜单包含 ${reason.count} 个子菜单\n`
        } else if (reason.type === 'ASSIGNED_TO_ROLES') {
          messageText += `• 该菜单已分配给 ${reason.count} 个角色`
          if (usageData.assigned_roles.length > 0) {
            const roleNames = usageData.assigned_roles.map((role) => role.name).join('、')
            messageText += `（${roleNames}）`
          }
          messageText += '\n'
        }
      })
      messageText += '\n请先处理以上问题后再删除。'

      $message.warning(messageText)
      return
    }

    // 如果可以删除，执行原始删除逻辑
    await originalHandleDelete(params, showModal)
  } catch (error) {
    console.error('删除菜单失败:', error)

    // 检查是否是菜单被角色使用的错误（兜底处理）
    if (error.message && error.message.includes('Cannot delete menu that is assigned to roles')) {
      $message.error(
        '无法删除该菜单：该菜单已分配给某些角色，请先从相关角色中移除此菜单权限后再删除'
      )
      return
    }

    // 检查其他常见的删除错误
    if (error.message && error.message.includes('has children')) {
      $message.error('无法删除该菜单：该菜单包含子菜单，请先删除所有子菜单')
      return
    }

    // 默认错误提示
    $message.error(error.message || '删除菜单失败，请稍后重试')
  }
}

// 批量删除组合式函数
const {
  selectedItems,
  selectedRowKeys,
  selectedCount,
  isLoading: batchDeleteLoading,
  handleBatchDelete,
  setSelectedItems,
  clearSelection,
} = useMenuBatchDelete({
  batchDeleteApi: systemV2Api.batchDeleteMenus,
  refresh: () => $table.value?.handleSearch(),
  validateItem: (item) => {
    // 检查是否为系统内置菜单
    if (item.is_system || item.menu_type === 'system') {
      return { valid: false, reason: '系统内置菜单不能删除' }
    }

    return { valid: true }
  },
})

// 构建菜单树形结构
const buildMenuTree = (menus, parentId = 0) => {
  const tree = []
  for (const menu of menus) {
    if (menu.parent_id === parentId) {
      // 创建菜单副本，避免修改原始数据
      const menuCopy = { ...menu }
      const children = buildMenuTree(menus, menu.id)
      if (children.length > 0) {
        menuCopy.children = children
      }
      tree.push(menuCopy)
    }
  }
  return tree.sort((a, b) => (a.order || 0) - (b.order || 0))
}

// 菜单列表数据获取函数 - 获取全部菜单，以树状形式显示
const getMenuListData = async (params) => {
  try {
    console.log('调用菜单列表API v2，参数:', params)

    // 直接调用底层API，绕过适配器
    const res = await menuApi.getTree({ include_hidden: false })

    console.log('菜单树形API原始响应:', res)

    // 检查响应格式
    if (res?.success === true || (res?.code === 200 && res?.data)) {
      // 树形API返回的数据结构: { tree: [...], total: ..., tree_depth: ... }
      const treeData = res.data?.tree || []
      const total = res.data?.total || 0

      console.log('解析后的树形数据:', treeData, '总数:', total)

      return {
        data: treeData,
        total: total,
      }
    }
    return { data: [], total: 0 }
  } catch (err) {
    console.error('菜单列表API v2错误:', err)

    // 检查是否是认证错误
    if (err.response?.status === 401 || err.code === 401) {
      console.warn('检测到认证错误，可能需要重新登录')
      $message.error('登录已过期，请重新登录。请手动刷新页面或点击登录按钮重新登录。', {
        duration: 0, // 不自动消失
        closable: true,
      })

      // 不自动清除认证信息，让用户自己决定
      // 不自动跳转，让用户自己操作
    } else {
      $message.error('获取菜单列表失败: ' + (err.message || '未知错误'))
    }

    // 兜底处理
    return { data: [], total: 0 }
  }
}

onMounted(() => {
  console.log('菜单管理页面 onMounted 钩子触发')
  console.log('$table ref 状态:', $table.value)

  // 延迟执行，确保应用完全初始化
  setTimeout(() => {
    console.log('延迟执行开始，$table ref 状态:', $table.value)
    if ($table.value?.handleSearch) {
      console.log('调用 $table.value.handleSearch()')
      $table.value.handleSearch()
    } else {
      console.error('$table.value.handleSearch 不可用')
    }
    getTreeSelect()
  }, 100)
})

onActivated(() => {
  console.log('Menu Management onActivated hook triggered.')
  console.log('$table ref:', $table.value)

  // 检查token是否存在
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.warn('Token不存在，跳过菜单数据加载')
    return
  }

  if ($table.value && typeof $table.value.handleSearch === 'function') {
    console.log('Calling $table.value.handleSearch()')
    $table.value.handleSearch()
  } else {
    console.error('$table.value is not available or handleSearch is not a function.')
  }
  getTreeSelect()
})

// 处理表格行选择
const handleTableSelection = (rowKeys, rows) => {
  setSelectedItems(rows || [], rowKeys || [])
}

// 是否展示 "菜单类型"
const showMenuType = ref(false)
const menuOptions = ref([])

const columns = [
  {
    type: 'selection',
    width: 50,
    align: 'center',
  },
  { title: 'ID', key: 'id', width: 70, ellipsis: { tooltip: true }, align: 'center' },
  { title: '菜单名称', key: 'name', width: 80, ellipsis: { tooltip: true }, align: 'center' },
  {
    title: '菜单类型',
    key: 'menu_type',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      let round = false
      let bordered = false
      if (row.menu_type === 'catalog') {
        bordered = true
        round = false
      } else if (row.menu_type === 'menu') {
        bordered = false
        round = true
      }
      return h(
        NTag,
        { type: 'primary', round: round, bordered: bordered },
        { default: () => (row.menu_type === 'catalog' ? '目录' : '菜单') }
      )
    },
  },
  {
    title: '图标',
    key: 'icon',
    width: 40,
    align: 'center',
    render(row) {
      return h(TheIcon, { icon: row.icon, size: 20 })
    },
  },
  { title: '排序', key: 'order', width: 40, ellipsis: { tooltip: true }, align: 'center' },
  { title: '访问路径', key: 'path', width: 100, ellipsis: { tooltip: true }, align: 'center' },
  { title: '组件路径', key: 'component', width: 100, ellipsis: { tooltip: true }, align: 'center' },
  {
    title: '保活',
    key: 'keepalive',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.keepalive,
        onUpdateValue: () => handleUpdateKeepalive(row),
      })
    },
  },
  {
    title: '隐藏',
    key: 'is_hidden',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_hidden,
        onUpdateValue: () => handleUpdateHidden(row),
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        h(
          PermissionButton,
          {
            permission: 'POST /api/v2/menus',
            size: 'tiny',
            type: 'primary',
            style: `display: ${row.menu_type === 'catalog' ? '' : 'none'};`,
            onClick: () => {
              initForm.parent_id = row.id
              initForm.menu_type = 'menu'
              initForm.is_hidden = false
              initForm.order = 1
              initForm.keepalive = true
              // 为子菜单提供默认相对路径格式
              initForm.path = 'child-menu'
              showMenuType.value = false
              handleAdd()
            },
          },
          {
            default: () => '子菜单',
            icon: renderIcon('material-symbols:add', { size: 16 }),
          }
        ),
        h(
          PermissionButton,
          {
            permission: 'PUT /api/v2/menus/{id}',
            size: 'tiny',
            type: 'info',
            onClick: () => {
              showMenuType.value = false
              handleEdit(row)
            },
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
          }
        ),
        h(
          PermissionButton,
          {
            permission: 'DELETE /api/v2/menus/{id}',
            size: 'tiny',
            type: 'error',
            style: `display: ${row.children && row.children.length > 0 ? 'none' : ''};`, //有子菜单不允许删除
            needConfirm: true,
            confirmTitle: '删除确认',
            confirmContent: '确定删除该菜单吗？此操作不可恢复。',
            onConfirm: () => handleDelete({ id: row.id }, false),
          },
          {
            default: () => '删除',
            icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
          }
        ),
      ]
    },
  },
]
// 修改是否keepalive
async function handleUpdateKeepalive(row) {
  if (!row.id) return
  try {
    row.publishing = true
    const newKeepalive = !row.keepalive
    console.log('更新菜单keepalive状态:', row.id, newKeepalive)

    // 只传递MenuUpdate schema中定义的字段
    const updateData = {
      id: row.id,
      name: row.name,
      path: row.path,
      menu_type: row.menu_type,
      icon: row.icon,
      order: row.order,
      parent_id: row.parent_id,
      is_hidden: row.is_hidden,
      component: row.component,
      keepalive: newKeepalive,
      redirect: row.redirect,
    }
    await systemV2Api.updateMenu(updateData)

    row.keepalive = newKeepalive
    $message?.success(row.keepalive ? 'KeepAlive已开启' : 'KeepAlive已关闭')
    console.log('菜单keepalive状态更新成功')
  } catch (error) {
    console.error('更新菜单keepalive状态失败:', error)
    // 检查错误是否已经被HTTP拦截器处理过，避免重复提示
    if (!(error && typeof error === 'object' && error.success === false)) {
      $message?.error('更新失败: ' + (error.message || '未知错误'))
    }
  } finally {
    row.publishing = false
  }
}

// 修改是否隐藏
async function handleUpdateHidden(row) {
  if (!row.id) return
  try {
    row.publishing = true
    const newHidden = !row.is_hidden
    console.log('更新菜单隐藏状态:', row.id, newHidden)

    // 只传递MenuUpdate schema中定义的字段
    const updateData = {
      id: row.id,
      name: row.name,
      path: row.path,
      menu_type: row.menu_type,
      icon: row.icon,
      order: row.order,
      parent_id: row.parent_id,
      is_hidden: newHidden,
      component: row.component,
      keepalive: row.keepalive,
      redirect: row.redirect,
    }
    await systemV2Api.updateMenu(updateData)

    row.is_hidden = newHidden
    $message?.success(row.is_hidden ? '菜单已隐藏' : '菜单已显示')
    console.log('菜单隐藏状态更新成功')
  } catch (error) {
    console.error('更新菜单隐藏状态失败:', error)
    // 检查错误是否已经被HTTP拦截器处理过，避免重复提示
    if (!(error && typeof error === 'object' && error.success === false)) {
      $message?.error('更新失败: ' + (error.message || '未知错误'))
    }
  } finally {
    row.publishing = false
  }
}

// 新增菜单(可选目录)
function handleClickAdd() {
  initForm.parent_id = 0
  initForm.menu_type = 'catalog'
  initForm.is_hidden = false
  initForm.order = 1
  initForm.keepalive = true
  showMenuType.value = true
  handleAdd()
}

// 处理展开状态切换
function handleExpandChange(expandedKeys) {
  console.log('展开状态变化:', expandedKeys)
  expandedRowKeys.value = expandedKeys
}

// 路径验证函数
function validatePath(rule, value) {
  if (!value) {
    return new Error('请输入访问路径')
  }

  // 根据菜单类型和父菜单进行不同的验证
  const menuType = modalForm.value.menu_type
  const parentId = modalForm.value.parent_id

  if (parentId === 0 || parentId === null) {
    // 根菜单必须以 / 开头
    if (!value.startsWith('/')) {
      return new Error('根菜单路径必须以 / 开头，例如：/system')
    }
    // 验证根菜单路径格式
    if (!/^\/[a-zA-Z0-9/_-]*$/.test(value)) {
      return new Error('路径格式不正确，只能包含字母、数字、/、_、-')
    }
  } else {
    // 子菜单可以不以 / 开头（相对路径）
    if (value.startsWith('/')) {
      // 如果子菜单以 / 开头，验证绝对路径格式
      if (!/^\/[a-zA-Z0-9/_-]*$/.test(value)) {
        return new Error('路径格式不正确，只能包含字母、数字、/、_、-')
      }
    } else {
      // 验证相对路径格式 - 允许斜杠用于多级路径
      if (!/^[a-zA-Z0-9/_-]+$/.test(value)) {
        return new Error('相对路径只能包含字母、数字、/、_、-')
      }
    }
  }

  return true
}

async function getTreeSelect() {
  try {
    console.log('获取菜单树形选择数据')
    const res = await menuApi.getTree({ include_hidden: false })
    console.log('菜单树形数据响应:', res)

    if (res?.success === true || (res?.code === 200 && res?.data)) {
      // 树形API返回的数据在 data.tree 中
      const treeData = res.data?.tree || []
      const menu = { id: 0, name: '根目录', children: treeData }
      menuOptions.value = [menu]
      console.log('菜单树形选择数据处理完成:', menuOptions.value)
    } else {
      menuOptions.value = [{ id: 0, name: '根目录', children: [] }]
    }
  } catch (error) {
    console.error('获取菜单树形数据失败:', error)
    $message?.error('获取菜单数据失败: ' + (error.message || '未知错误'))
    menuOptions.value = [{ id: 0, name: '根目录', children: [] }]
  }
}
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage
    show-footer
    title="菜单列表"
    class="system-menu-page system-management-page standard-page"
  >
    <template #action>
      <div class="flex items-center gap-3">
        <NButton
          v-if="selectedCount > 0"
          v-permission="'DELETE /api/v2/menus/batch'"
          type="error"
          :loading="batchDeleteLoading"
          :disabled="batchDeleteLoading"
          @click="handleBatchDelete"
        >
          <TheIcon icon="material-symbols:delete-outline" :size="18" class="mr-1" />
          批量删除 ({{ selectedCount }})
        </NButton>

        <PermissionButton permission="POST /api/v2/menus" type="primary" @click="handleClickAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />新建根菜单
        </PermissionButton>
      </div>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      v-model:checked-row-keys="selectedRowKeys"
      :is-pagination="false"
      :columns="columns"
      :get-data="getMenuListData"
      :single-line="true"
      :cascade="false"
      :children-key="'children'"
      :default-expand-all="false"
      :expanded-row-keys="expandedRowKeys"
      @update:expanded-row-keys="handleExpandChange"
      @on-checked="handleTableSelection"
    >
    </CrudTable>

    <!-- 新增/编辑/查看 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave(getTreeSelect)"
    >
      <!-- 表单 -->
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
      >
        <NFormItem label="菜单类型" path="menu_type">
          <NRadioGroup v-model:value="modalForm.menu_type">
            <NRadio label="目录" value="catalog" />
            <NRadio label="菜单" value="menu" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem label="上级菜单" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            key-field="id"
            label-field="name"
            :options="menuOptions"
            :default-expand-all="true"
          />
        </NFormItem>
        <NFormItem
          label="菜单名称"
          path="name"
          :rule="{
            required: true,
            message: '请输入唯一菜单名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" placeholder="请输入唯一菜单名称" />
        </NFormItem>
        <NFormItem
          label="访问路径"
          path="path"
          :rule="{
            required: true,
            validator: validatePath,
            trigger: ['blur'],
          }"
        >
          <NInput
            v-model:value="modalForm.path"
            placeholder="根菜单：/system，子菜单：user 或 /system/user"
          />
        </NFormItem>
        <NFormItem v-if="modalForm.menu_type === 'menu'" label="组件路径" path="component">
          <NInput
            v-model:value="modalForm.component"
            placeholder="请输入组件路径，例如：/system/user"
          />
        </NFormItem>
        <NFormItem label="跳转路径" path="redirect">
          <NInput
            v-model:value="modalForm.redirect"
            :disabled="modalForm.parent_id !== 0"
            :placeholder="
              modalForm.parent_id !== 0 ? '只有一级菜单可以设置跳转路径' : '请输入跳转路径'
            "
          />
        </NFormItem>
        <NFormItem label="菜单图标" path="icon">
          <IconPicker v-model:value="modalForm.icon" />
        </NFormItem>
        <NFormItem label="显示排序" path="order">
          <NInputNumber v-model:value="modalForm.order" :min="1" />
        </NFormItem>
        <NFormItem label="是否隐藏" path="is_hidden">
          <NSwitch v-model:value="modalForm.is_hidden" />
        </NFormItem>
        <NFormItem label="KeepAlive" path="keepalive">
          <NSwitch v-model:value="modalForm.keepalive" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
