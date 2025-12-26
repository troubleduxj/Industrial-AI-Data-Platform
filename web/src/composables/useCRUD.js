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
    modalForm.value = { ...row }
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
          api: () => {
            // 修复：正确传递ID和数据参数
            const { id, ...data } = modalForm.value

            // 验证ID是否存在
            const numericId = Number(id)
            if (!id || isNaN(numericId) || numericId <= 0) {
              console.error('编辑失败：ID无效', { id, numericId, modalForm: modalForm.value })
              throw new Error(`编辑失败：${name}ID无效 (${id})`)
            }

            console.log('执行编辑操作:', { id, data, fullData: modalForm.value })
            // 修复：传递包含id的完整数据对象给updateMenu
            return doUpdate({ id, ...data })
          },
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
        console.error(`${modalAction.value === 'add' ? '新增' : '编辑'}失败:`, error)
      }
    })
  }

  /** 删除 */
  async function handleDelete(params = {}) {
    // 修复：改进参数验证逻辑，支持直接传入ID或对象
    let deleteParams = params

    // 如果传入的是数字，根据模块类型决定如何处理
    if (typeof params === 'number') {
      // 特殊处理：API分组直接传递ID，不转换为对象
      if (name && name.toLowerCase().includes('api') && name.toLowerCase().includes('分组')) {
        // 直接传递ID给API，让API层处理路径参数
        deleteParams = params
      } else {
        deleteParams = { id: params }
      }
    }

    // 验证参数
    if (
      isNullOrWhitespace(deleteParams) ||
      (typeof deleteParams === 'object' && Object.keys(deleteParams).length === 0) ||
      (typeof deleteParams === 'object' &&
        !deleteParams.id &&
        !deleteParams.role_id &&
        !deleteParams.user_id &&
        !deleteParams.dept_id &&
        !deleteParams.menu_id &&
        !deleteParams.group_id &&
        !deleteParams.type_id &&
        !deleteParams.data_id &&
        !deleteParams.param_id &&
        !deleteParams.config_id)
    ) {
      console.warn('删除操作缺少必要参数:', deleteParams)
      return
    }

    try {
      modalLoading.value = true
      const data = await doDelete(deleteParams)
      $message.success('删除成功')
      modalLoading.value = false
      refresh(data)
    } catch (error) {
      modalLoading.value = false
      console.error('删除失败:', error)
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
