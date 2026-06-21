import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'Home', component: () => import('../views/HomeView.vue'), meta: { title: '' } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '工作台' } },
  { path: '/chat', name: 'Chat', component: () => import('../views/ChatView.vue'), meta: { title: 'AI 对话' } },
  { path: '/codegen', name: 'CodeGen', component: () => import('../views/CodeGenView.vue'), meta: { title: '代码生成' } },
  { path: '/recommend', name: 'Recommend', component: () => import('../views/RecommendView.vue'), meta: { title: '智能推荐' } },
  { path: '/ocr', name: 'OCR', component: () => import('../views/OCRView.vue'), meta: { title: 'OCR 识别' } },
  { path: '/media', name: 'Media', component: () => import('../views/MediaView.vue'), meta: { title: 'AI 创作' } },
  { path: '/knowledge', name: 'Knowledge', component: () => import('../views/KnowledgeView.vue'), meta: { title: '知识库' } },
  { path: '/discover', name: 'Discover', component: () => import('../views/DiscoverView.vue'), meta: { title: '发现智能体' } },
  { path: '/workflow', name: 'Workflow', component: () => import('../views/WorkflowView.vue'), meta: { title: '工作流' } },
  { path: '/settings', name: 'Settings', component: () => import('../views/SettingsView.vue'), meta: { title: '系统设置' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
