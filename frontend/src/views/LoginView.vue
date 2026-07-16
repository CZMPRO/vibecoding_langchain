<template>
  <div class="page-center">
    <div class="auth-card">
      <h1>电商知识库问答</h1>
      <p class="sub">登录后即可基于商品知识库进行智能问答</p>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="onSubmit">
          登录
        </el-button>
      </el-form>

      <div style="margin-top: 16px; text-align: center; color: #64748b; font-size: 13px">
        还没有账号？
        <router-link to="/register" style="color: #2563eb">去注册</router-link>
      </div>
      <div style="margin-top: 10px; text-align: center; color: #94a3b8; font-size: 12px">
        演示管理员：admin / 123456
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const { data } = await loginApi(form)
    userStore.setAuth(data.access_token, data.user)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.replace(String(redirect))
  } finally {
    loading.value = false
  }
}
</script>
