/**
 * useCRUD组合函数 - 修复版本
 * 修复了删除参数验证和模态框状态管理问题
 */
import { ref, computed } from 'vue'
import { isNullOrWhitespace } from '@/utils'

const ACTIONS = {
  view: '查看',
  edit: '编辑',
  add: '新增',
}

export function useCRUD({ name, initForm = {}, doCreate, doDelete, doUpdate, refresh }) {
  const modalVisible = ref(false)
  const modalAction = ref('')
  const modalTitle = computed(() => ACTIONS[modalAction.value] + name)
  const modalLoading = ref(false)
  const modalFormRef = ref(null)
  const modalForm = ref({ ...initForm })

  /** 新增 */
  function handleAdd() {
    modalAction.value = 'add'
    modalVisible.value = true
    modalForm.value = { ...initForm }
  }

  /** 修改 */
  function handleEdit(row) {
    modalAction.value = 'edit'
    modalVisible.value = true
    // 修复：正确映射字段，确保表单字段与数据字段对应
    modalForm.value = {
      id: row.id,
      role_name: row.name || row.role_name, // 将 name 映射到 role_name
      remark: row.desc || row.remark, // 将 desc 映射到 remark
    }
  }

  /** 查看 */
  function handleView(row) {
    modalAction.value = 'view'
    modalVisible.value = true
    modalForm.value = { ...row }
  }

  /** 保存 */
  function handleSave(...callbacks) {
    if (!['edit', 'add'].includes(modalAction.value)) {
      modalVisible.value = false
      return
    }
    modalFormRef.value?.validate(async (err) => {
      if (err) return
      const actions = {
        add: {
          api: () => doCreate(modalForm.value),
          cb: () => {
            callbacks.forEach((callback) => callback && callback())
          },
          msg: () => $message.success('新增成功'),
        },
        edit: {
          api: () => doUpdate(modalForm.value),
          cb: () => {
            callbacks.forEach((callback) => callback && callback())
          },
          msg: () => $message.success('编辑成功'),
        },
      }
      const action = actions[modalAction.value]

      try {
        modalLoading.value = true
        const data = await action.api()
        action.cb()
        action.msg()

        // 修复：分别设置状态，确保正确的状态管理
        modalLoading.value = false
        modalVisible.value = false

        data && refresh(data)
      } catch (error) {
        // 修复：只重置加载状态，保持模态框打开让用户重试
        modalLoading.value = false
        // modalVisible.value 保持 true，让用户可以重试
        console.error(`${modalAction.value === 'add' ? '新增' : '编辑'}${name}失败:`, error)
      }
    })
  }

  /** 删除 */
  async function handleDelete(params = {}) {
    // 修复：改进参数验证逻辑
    if (
      isNullOrWhitespace(params) ||
      (typeof params === 'object' && Object.keys(params).length === 0) ||
      (!params.id && !params.role_id && !params.user_id && !params.dept_id && !params.menu_id)
    ) {
      console.warn('删除操作缺少必要参数:', params)
      return
    }

    try {
      modalLoading.value = true
      const data = await doDelete(params)
      $message.success('删除成功')
      modalLoading.value = false
      refresh(data)
    } catch (error) {
      modalLoading.value = false
      console.error(`删除${name}失败:`, error)
    }
  }

  return {
    modalVisible,
    modalAction,
    modalTitle,
    modalLoading,
    handleAdd,
    handleDelete,
    handleEdit,
    handleView,
    handleSave,
    modalForm,
    modalFormRef,
  }
}
