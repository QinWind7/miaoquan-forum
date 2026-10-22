import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useUserStore } from '@/stores/user'
import AuthLayout from '@/layouts/AuthLayout.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'boards/:slug',
        name: 'board',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '分区' },
      },
      // 注意：posts/create 必须写在 posts/:id 之前，否则会被 :id 吃掉
      {
        path: 'posts/create',
        name: 'post-create',
        component: () => import('@/views/post/PostCreateView.vue'),
        meta: { title: '发布帖子', requiresAuth: true },
      },
      {
        path: 'posts/:id',
        name: 'post-detail',
        component: () => import('@/views/post/PostDetailView.vue'),
        meta: { title: '帖子详情' },
      },
      {
        path: 'posts/:id/edit',
        name: 'post-edit',
        component: () => import('@/views/post/PostCreateView.vue'),
        meta: { title: '编辑帖子', requiresAuth: true },
      },
      {
        path: 'chat',
        name: 'chat',
        component: () => import('@/views/chat/ChatView.vue'),
        meta: { title: '我的私聊', requiresAuth: true },
      },
      {
        path: 'users/:id',
        name: 'user-profile',
        component: () => import('@/views/user/UserProfile.vue'),
        meta: { title: '个人主页' },
      },
      {
        path: 'me/friends',
        name: 'my-friends',
        component: () => import('@/views/user/SocialListView.vue'),
        meta: { title: '我的好友', requiresAuth: true, socialMode: 'friends' },
      },
      {
        path: 'me/fans',
        name: 'my-fans',
        component: () => import('@/views/user/SocialListView.vue'),
        meta: { title: '我的粉丝', requiresAuth: true, socialMode: 'fans' },
      },
      {
        path: 'me/posts',
        name: 'my-posts',
        component: () => import('@/views/user/MyPostsView.vue'),
        meta: { title: '我的帖子', requiresAuth: true },
      },
      {
        path: 'me/likes',
        name: 'my-likes',
        component: () => import('@/views/user/MyLikesView.vue'),
        meta: { title: '我点赞的帖子', requiresAuth: true },
      },
    ],
  },
  {
    path: '/',
    component: AuthLayout,
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { title: '登录', guestOnly: true },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/RegisterView.vue'),
        meta: { title: '注册', guestOnly: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面走丢了' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const SITE_NAME = '喵圈'

router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.guestOnly && userStore.isLoggedIn) {
    return { name: 'home' }
  }
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} · ${SITE_NAME}` : SITE_NAME
})

export default router
