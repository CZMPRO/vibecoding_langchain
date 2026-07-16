<template>
  <div class="layout">
    <AppSidebar :show-sessions="false" @new-chat="$router.push('/')" />
    <div class="main">
      <div class="topbar">
        <div class="title">知识库管理</div>
        <el-button text @click="$router.push('/')">返回问答</el-button>
      </div>

      <div class="admin-page">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>文档列表</span>
              <div style="display: flex; gap: 8px">
                <el-button @click="loadDocs" :loading="loading">刷新</el-button>
                <el-upload
                  :show-file-list="false"
                  :http-request="onUpload"
                  accept=".pdf,.docx,.txt,.md,.markdown,.csv,.xlsx,.xls"
                >
                  <el-button type="primary" :loading="uploading">上传文档</el-button>
                </el-upload>
              </div>
            </div>
          </template>

          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="支持 PDF / Word / TXT / Markdown / CSV / Excel。上传后后台自动解析入库，状态变为「就绪」后即可被问答引用。"
            style="margin-bottom: 14px"
          />

          <el-table :data="docs" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="file_type" label="类型" width="90" />
            <el-table-column label="大小" width="100">
              <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="片段数" width="90" />
            <el-table-column prop="error_message" label="错误信息" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  :disabled="row.status === 'processing'"
                  @click="onRetry(row)"
                >
                  重试
                </el-button>
                <el-button link type="danger" @click="onDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppSidebar from '@/components/AppSidebar.vue'
import {
  deleteDocumentApi,
  listDocumentsApi,
  retryDocumentApi,
  uploadDocumentApi,
} from '@/api/kb'

const docs = ref([])
const loading = ref(false)
const uploading = ref(false)
let timer = null

function statusText(s) {
  return (
    {
      pending: '等待中',
      processing: '处理中',
      ready: '就绪',
      failed: '失败',
    }[s] || s
  )
}

function statusType(s) {
  return (
    {
      pending: 'info',
      processing: 'warning',
      ready: 'success',
      failed: 'danger',
    }[s] || ''
  )
}

function formatSize(n) {
  if (!n && n !== 0) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

async function loadDocs() {
  loading.value = true
  try {
    const { data } = await listDocumentsApi({ page: 1, page_size: 100 })
    docs.value = data.items || []
  } finally {
    loading.value = false
  }
}

async function onUpload({ file }) {
  uploading.value = true
  try {
    await uploadDocumentApi(file)
    ElMessage.success('上传成功，正在后台解析入库…')
    await loadDocs()
  } finally {
    uploading.value = false
  }
}

async function onRetry(row) {
  await retryDocumentApi(row.id)
  ElMessage.success('已重新提交入库')
  await loadDocs()
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确定删除文档「${row.filename}」吗？相关向量也会删除。`, '删除确认', {
    type: 'warning',
  })
  await deleteDocumentApi(row.id)
  ElMessage.success('已删除')
  await loadDocs()
}

onMounted(async () => {
  await loadDocs()
  // 处理中的文档自动轮询状态
  timer = setInterval(() => {
    const busy = docs.value.some((d) => d.status === 'pending' || d.status === 'processing')
    if (busy) loadDocs()
  }, 3000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
