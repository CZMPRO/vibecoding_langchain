<template>
  <div class="page-center">
    <div class="auth-card">
      <h1>注册账号</h1>
      <p class="sub">注册普通用户后可进行知识库问答（不可管理知识库）</p>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="至少 3 个字符" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input
            v-model="form.confirm"
            type="password"
            show-password
            placeholder="再输入一次密码"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="onSubmit">
          注册并登录
        </el-button>
      </el-form>

      <div style="margin-top: 16px; text-align: center; color: #64748b; font-size: 13px">
        已有账号？
        <router-link to="/login" style="color: #2563eb">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { registerApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
  confirm: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '至少 3 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_, value, cb) => {
        if (value !== form.password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const { data } = await registerApi({
      username: form.username,
      password: form.password,
    })
    userStore.setAuth(data.access_token, data.user)
    ElMessage.success('注册成功')
    router.replace('/')
  } finally {
    loading.value = false
  }
}
</script>
