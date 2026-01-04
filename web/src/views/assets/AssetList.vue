<template>
  <div class="asset-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ categoryName }}列表</h2>
        <n-tag v-if="totalCount > 0" type="info" size="small">
          共 {{ totalCount }} 个
        </n-tag>
      </div>
      <div class="header-right">
        <n-space>
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索资产名称或编码"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <n-icon :component="SearchOutline" />
            </template>
          </n-input>
          <n-button type="primary" @click="handleCreate">
            <template #icon>
              <n-icon :component="AddOutline" />
            </template>
            新建资产
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 数据表格 -->
    <n-spin :show="loading">
      <n-data-table
        :columns="tableColumns"
        :data="assetList"
        :pagination="pagination"
        :row-key="row => row.id"
        striped
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-spin>

    <!-- 空状态 -->
    <n-empty
      v-if="!loading && assetList.length === 0"
      description="暂无资产数据"
      class="empty-state"
    >
      <template #extra>
        <n-button type="primary" @click="handleCreate">
          创建第一个资产
        </n-button>
      </template>
    </n-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NDataTable, NButton, NSpace, NInput, NIcon, NTag, NSpin, NEmpty,
  NPopconfirm, useMessage
} from 'naive-ui'
import { SearchOutline, AddOutline, CreateOutline, TrashOutline, EyeOutline } from '@vicons/ionicons5'
import { assetApi } from '@/api/v4/assets'
import { useSignalDefinitions } from '@/components/platform/composables/useSignalDefinitions'

const router = useRouter()
const route = useRoute()
const message = useMessage()

// 注入类别信息
const currentCategory = inject('currentCategory')
const categoryCode = inject('categoryCode')

// 类别名称
const categoryName = computed(() => currentCategory.value?.name || '资产')

// 使用信号定义
const { signals, toTableColumns } = useSignalDefinitions(currentCategory.value?.id)

// 状态
const loading = ref(false)
const assetList = ref([])
const totalCount = ref(0)
const searchKeyword = ref('')

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0
})

// 表格列
const tableColumns = computed(() => {
  const baseColumns = [
    {
      title: '资产编码',
      key: 'code',
      width: 150,
      fixed: 'left'
    },
    {
      title: '资产名称',
      key: 'name',
      width: 180
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (row) => {
        const statusMap = {
          online: { type: 'success', text: '在线' },
          offline: { type: 'default', text: '离线' },
          error: { type: 'error', text: '故障' },
          maintenance: { type: 'warning', text: '维护中' }
        }
        const status = statusMap[row.status] || statusMap.offline
        return h(NTag, { type: status.type, size: 'small' }, () => status.text)
      }
    },
    {
      title: '位置',
      key: 'location',
      width: 150,
      ellipsis: { tooltip: true }
    }
  ]

  // 添加信号列（最多显示5个）
  const signalColumns = toTableColumns({ 
    filterFn: (s) => s.is_default_visible !== false 
  }).slice(0, 5)

  const actionColumn = {
    title: '操作',
    key: 'actions',
    width: 180,
    fixed: 'right',
    render: (row) => {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => handleView(row)
        }, {
          icon: () => h(NIcon, { component: EyeOutline }),
          default: () => '查看'
        }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => handleEdit(row)
        }, {
          icon: () => h(NIcon, { component: CreateOutline }),
          default: () => '编辑'
        }),
        h(NPopconfirm, {
          onPositiveClick: () => handleDelete(row)
        }, {
          trigger: () => h(NButton, {
            size: 'small',
            quaternary: true,
            type: 'error'
          }, {
            icon: () => h(NIcon, { component: TrashOutline }),
            default: () => '删除'
          }),
          default: () => '确定要删除这个资产吗？'
        })
      ])
    }
  }

  return [...baseColumns, ...signalColumns, actionColumn]
})

// 加载资产列表
async function loadAssets() {
  if (!currentCategory.value?.id) return

  loading.value = true
  try {
    const response = await assetApi.getList({
      category_id: currentCategory.value.id,
      keyword: searchKeyword.value,
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })

    const data = response.data || response
    assetList.value = data.items || data.assets || []
    totalCount.value = data.total || assetList.value.length
    pagination.value.itemCount = totalCount.value
  } catch (error) {
    message.error('加载资产列表失败')
    console.error('加载资产列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.value.page = 1
  loadAssets()
}

// 分页变化
function handlePageChange(page) {
  pagination.value.page = page
  loadAssets()
}

function handlePageSizeChange(pageSize) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadAssets()
}

// 新建资产
function handleCreate() {
  router.push(`/assets/${categoryCode.value}/create`)
}

// 查看资产
function handleView(row) {
  router.push(`/assets/${categoryCode.value}/${row.id}`)
}

// 编辑资产
function handleEdit(row) {
  router.push(`/assets/${categoryCode.value}/${row.id}/edit`)
}

// 删除资产
async function handleDelete(row) {
  try {
    await assetApi.delete(row.id)
    message.success('删除成功')
    loadAssets()
  } catch (error) {
    message.error('删除失败')
    console.error('删除资产失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadAssets()
})
</script>

<style scoped>
.asset-list-page {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.empty-state {
  margin-top: 100px;
}
</style>
