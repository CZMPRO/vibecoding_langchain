import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : error.message || '请求失败'

    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push({ name: 'login' })
      ElMessage.error('登录已失效，请重新登录')
    } else if (status === 403) {
      ElMessage.error(msg || '没有权限')
    } else if (status === 429) {
      ElMessage.warning(msg || '请求太频繁')
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default http
