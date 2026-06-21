<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="h-14 bg-white/80 backdrop-blur-lg border-b border-gray-100/80 flex items-center justify-between px-5 sticky top-0 z-50">
      <div class="flex items-center gap-2">
        <!-- Logo -->
        <div
          class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-indigo-200 cursor-pointer hover:shadow-lg hover:shadow-indigo-300 transition-all duration-200 hover:scale-105"
          @click="$router.push('/home')"
        >AIT</div>

        <!-- Breadcrumb -->
        <template v-if="!isHome">
          <div class="flex items-center gap-1.5 ml-1">
            <svg class="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            <span
              class="text-xs text-gray-400 hover:text-indigo-500 cursor-pointer transition-colors px-1.5 py-0.5 rounded hover:bg-indigo-50"
              @click="$router.push('/home')"
            >首页</span>
            <svg class="w-3 h-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
            <span v-if="currentTitle" class="text-xs font-medium text-gray-600 px-1.5 py-0.5 bg-gray-50 rounded">{{ currentTitle }}</span>
          </div>
        </template>
        <template v-else>
          <span class="text-xs text-gray-300 ml-1 hidden sm:inline">AI 应用通用框架</span>
        </template>
      </div>

      <div class="flex items-center gap-3">
      </div>
    </header>

    <!-- Content -->
    <main class="min-h-[calc(100vh-56px)]">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const isHome = computed(() => route.path === '/home')
const currentTitle = computed(() => route.meta?.title || '')
</script>
