<template>
  <div class="notification-center">
    <n-card title="通知中心">
      <template #header-extra>
        <n-space>
          <n-input
            v-model:value="searchText"
            placeholder="搜索通知标题"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <n-icon><SearchOutlined /></n-icon>
            </template>
          </n-input>
          
          <n-select
            v-model:value="filterType"
            placeholder="通知类型"
            clearable
            style="width: 120px"
            :options="typeOptions"
            @update:value="handleSearch"
          />
          
          <n-select
            v-model:value="filterRead"
            placeholder="状态"
            clearable
            style="width: 120px"
            :options="readOptions"
            @update:value="handleSearch"
          />

          <n-button @click="handleMarkAllRead">
            <template #icon>
              <n-icon><CheckmarkDoneOutline /></n-icon>
            </template>
            全部已读
          </n-button>
        </n-space>
      </template>

      <n-spin :show="loading">
        <n-list hoverable clickable>
          <template v-if="notifications.length > 0">
            <n-list-item v-for="item in notifications" :key="item.id">
              <template #prefix>
                <div class="notification-icon" :class="item.level">
                  <TheIcon :icon="getIcon(item.notification_type)" :size="24" />
                </div>
              </template>
              
              <n-thing :title="item.title" content-style="margin-top: 10px;">
                <template #description>
                  <n-space size="small" style="margin-top: 4px">
                    <n-tag size="small" :bordered="false" :type="getLevelType(item.level)">
                      {{ getLevelLabel(item.level) }}
                    </n-tag>
                    <span class="time-text">{{ formatTime(item.publish_time) }}</span>
                    <n-tag v-if="!item.is_read" size="small" type="error" :bordered="false">未读</n-tag>
                    <n-tag v-else size="small" type="success" :bordered="false">已读</n-tag>
                  </n-space>
                </template>
                
                <div class="notification-content">
                  {{ item.content }}
                </div>
              </n-thing>
              
              <template #suffix>
                <n-space vertical>
                  <n-button size="small" v-if="!item.is_read" @click.stop="handleMarkRead(item)">
                    标记已读
                  </n-button>
                  <n-button size="small" type="error" ghost @click.stop="handleDelete(item)">
                    删除
                  </n-button>
                </n-space>
              </template>
            </n-list-item>
          </template>
          <n-empty v-else description="暂无通知" style="padding: 40px 0" />
        </n-list>
        
        <div class="pagination-container" v-if="total > 0">
          <n-pagination
            v-model:page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :item-count="total"
            show-size-picker
            :page-sizes="[10, 20, 50]"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { SearchOutline as SearchOutlined, CheckmarkDoneOutline } from '@vicons/ionicons5'
import TheIcon from '@/components/icon/TheIcon.vue'
import { userNotificationApi, NotificationTypeOptions, NotificationLevelOptions } from '@/api/notification'
import { useUserStore } from '@/store'

const message = useMessage()
const dialog = useDialog()
const userStore = useUserStore()

const loading = ref(false)
const notifications = ref([])
const total = ref(0)
const searchText = ref('')
const filterType = ref(null)
const filterRead = ref(null)

const typeOptions = NotificationTypeOptions
const readOptions = [
  { label: '已读', value: true },
  { label: '未读', value: false }
]

const pagination = reactive({
  page: 1,
  pageSize: 10
})

const getUserId = () => {
  return userStore.userInfo?.id || 1
}

// 加载通知列表
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      user_id: getUserId(),
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      notification_type: filterType.value || undefined,
      is_read: filterRead.value === null ? undefined : filterRead.value
    }
    
    const res = await userNotificationApi.list(params)
    if (res.success && res.data) {
      notifications.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载通知列表失败:', error)
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 获取图标
const getIcon = (type) => {
  const iconMap = {
    announcement: 'material-symbols:campaign',
    alarm: 'material-symbols:warning',
    task: 'material-symbols:task',
    system: 'material-symbols:info',
  }
  return iconMap[type] || 'material-symbols:notifications'
}

// 获取级别标签
const getLevelLabel = (level) => {
  const opt = NotificationLevelOptions.find(o => o.value === level)
  return opt ? opt.label : level
}

// 获取级别类型
const getLevelType = (level) => {
  const map = {
    info: 'info',
    warning: 'warning',
    error: 'error'
  }
  return map[level] || 'default'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString()
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 分页
const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadData()
}

// 标记已读
const handleMarkRead = async (item) => {
  try {
    await userNotificationApi.markAsRead(item.id, getUserId())
    message.success('已标记为已读')
    item.is_read = true
    // loadData() // 可选：刷新列表
  } catch (error) {
    message.error('操作失败')
  }
}

// 全部标记已读
const handleMarkAllRead = async () => {
  dialog.warning({
    title: '确认',
    content: '确定要将所有通知标记为已读吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await userNotificationApi.markAllAsRead(getUserId())
        message.success('已全部标记为已读')
        loadData()
      } catch (error) {
        message.error('操作失败')
      }
    }
  })
}

// 删除通知
const handleDelete = async (item) => {
  dialog.warning({
    title: '确认',
    content: '确定要删除这条通知吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await userNotificationApi.delete(item.id, getUserId())
        message.success('删除成功')
        loadData()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.notification-center {
  padding: 16px;
}

.notification-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f5f5f5;
  margin-right: 12px;
}

.notification-icon.info { color: #909399; background-color: #f4f4f5; }
.notification-icon.warning { color: #e6a23c; background-color: #fdf6ec; }
.notification-icon.error { color: #f56c6c; background-color: #fef0f0; }

.notification-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-top: 8px;
}

.time-text {
  color: #909399;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
