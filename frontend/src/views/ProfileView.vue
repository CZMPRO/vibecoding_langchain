<template>
  <div class="layout">
    <AppSidebar />
    <div class="main">
      <div class="topbar">
        <div class="title">个人中心</div>
        <el-button text @click="$router.push('/')">返回问答</el-button>
      </div>
      <div class="admin-page" style="max-width: 560px">
        <el-card shadow="never">
          <template #header>账号信息</template>
          <p><b>用户名：</b>{{ userStore.username }}</p>
          <p><b>角色：</b>{{ userStore.isAdmin ? '管理员' : '普通用户' }}</p>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>修改密码</template>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="form.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="form.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="onSubmit">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import { changePasswordApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({
  old_password: '',
  new_password: '',
})

const rules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位', trigger: 'blur' },
  ],
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await changePasswordApi(form)
    ElMessage.success('密码已修改，请重新登录')
    userStore.logout()
    router.replace('/login')
  } finally {
    loading.value = false
  }
}
</script>
