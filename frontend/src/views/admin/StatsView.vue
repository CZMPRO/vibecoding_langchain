<template>
  <div class="layout">
    <AppSidebar :show-sessions="false" @new-chat="$router.push('/')" />
    <div class="main">
      <div class="topbar">
        <div class="title">运营统计</div>
        <el-button text @click="$router.push('/')">返回问答</el-button>
      </div>
      <div class="admin-page">
        <div class="stat-grid" v-loading="loading">
          <div class="stat-card" v-for="item in cards" :key="item.label">
            <div class="label">{{ item.label }}</div>
            <div class="value">{{ item.value }}</div>
          </div>
        </div>
        <el-alert
          type="success"
          :closable="false"
          show-icon
          title="统计数据来自业务库实时聚合，可用于答辩演示「企业级运营看板」能力。"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { statsOverviewApi } from '@/api/kb'

const loading = ref(false)
const stats = ref({
  user_count: 0,
  document_count: 0,
  ready_document_count: 0,
  conversation_count: 0,
  message_count: 0,
  today_qa_count: 0,
})

const cards = computed(() => [
  { label: '用户数', value: stats.value.user_count },
  { label: '知识库文档', value: stats.value.document_count },
  { label: '已就绪文档', value: stats.value.ready_document_count },
  { label: '会话数', value: stats.value.conversation_count },
  { label: '消息总数', value: stats.value.message_count },
  { label: '今日提问数', value: stats.value.today_qa_count },
])

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await statsOverviewApi()
    stats.value = data
  } finally {
    loading.value = false
  }
})
</script>
