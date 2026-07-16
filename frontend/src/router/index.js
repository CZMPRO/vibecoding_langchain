import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    name: 'chat',
    component: () => import('@/views/ChatView.vue'),
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
  },
  {
    path: '/admin/knowledge',
    name: 'knowledge',
    component: () => import('@/views/admin/KnowledgeView.vue'),
    meta: { roles: ['admin'] },
  },
  {
    path: '/admin/stats',
    name: 'stats',
    component: () => import('@/views/admin/StatsView.vue'),
    meta: { roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.public) {
    if (userStore.isLogin && (to.name === 'login' || to.name === 'register')) {
      next({ name: 'chat' })
      return
    }
    next()
    return
  }

  if (!userStore.isLogin) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.roles && !to.meta.roles.includes(userStore.user?.role)) {
    next({ name: 'chat' })
    return
  }

  next()
})

export default router
