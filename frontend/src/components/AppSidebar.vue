<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="brand">电商<span>知识库</span>问答</div>
      <div style="margin-top: 6px; font-size: 12px; color: #94a3b8">
        {{ userStore.username }} · {{ userStore.isAdmin ? '管理员' : '用户' }}
      </div>
    </div>

    <div class="sidebar-actions">
      <el-button type="primary" style="width: 100%" @click="emit('new-chat')">
        <el-icon style="margin-right: 6px"><Plus /></el-icon>
        新建会话
      </el-button>
    </div>

    <div class="session-list" v-if="showSessions">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === activeId }"
        @click="emit('select', s)"
      >
        <span class="title">{{ s.title }}</span>
        <el-dropdown trigger="click" @command="(cmd) => onCommand(cmd, s)">
          <span @click.stop style="color: #94a3b8; padding: 0 2px">⋯</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="rename">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div v-if="!sessions.length" style="padding: 12px; color: #64748b; font-size: 12px">
        暂无会话，点击上方新建
      </div>
    </div>
    <div v-else class="session-list"></div>

    <div class="sidebar-footer">
      <el-button
        v-if="userStore.isAdmin"
        text
        style="width: 100%; color: #e2e8f0; justify-content: flex-start"
        @click="$router.push('/admin/knowledge')"
      >
        知识库管理
      </el-button>
      <el-button
        v-if="userStore.isAdmin"
        text
        style="width: 100%; color: #e2e8f0; justify-content: flex-start"
        @click="$router.push('/admin/stats')"
      >
        运营统计
      </el-button>
      <el-button
        text
        style="width: 100%; color: #e2e8f0; justify-content: flex-start"
        @click="$router.push('/profile')"
      >
        个人中心
      </el-button>
      <el-button
        text
        style="width: 100%; color: #fca5a5; justify-content: flex-start"
        @click="onLogout"
      >
        退出登录
      </el-button>
    </div>
  </aside>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

defineProps({
  sessions: { type: Array, default: () => [] },
  activeId: { type: [Number, null], default: null },
  showSessions: { type: Boolean, default: true },
})

const emit = defineEmits(['new-chat', 'select', 'rename', 'delete'])
const userStore = useUserStore()
const router = useRouter()

function onCommand(cmd, session) {
  if (cmd === 'rename') emit('rename', session)
  if (cmd === 'delete') emit('delete', session)
}

async function onLogout() {
  await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
  userStore.logout()
  router.replace('/login')
}
</script>
