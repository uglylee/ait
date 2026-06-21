<template>
  <div class="max-w-4xl mx-auto px-6 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-800">{{ showMy ? '我创建的智能体' : '发现 AI 智能体' }}</h1>
      <div class="flex gap-2">
        <el-button @click="showMy = !showMy">{{ showMy ? '返回发现' : '我创建的' }}</el-button>
        <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon> 创建 AI 智能体</el-button>
      </div>
    </div>

    <!-- Category Tabs -->
    <div v-if="!showMy" class="flex gap-2 mb-6">
      <div v-for="cat in categories" :key="cat.key"
        :class="['px-5 py-2 rounded-full text-sm cursor-pointer transition-all',
          activeCategory === cat.key ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200']"
        @click="activeCategory = cat.key"
      >{{ cat.label }}</div>
    </div>

    <!-- My Agents -->
    <div v-if="showMy">
      <div v-if="!myAgents.length" class="text-center py-16 text-gray-400">
        <div class="text-5xl mb-3">📝</div>
        <p class="mb-4">还没有创建智能体</p>
        <el-button type="primary" @click="showCreate = true">创建第一个</el-button>
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div v-for="agent in myAgents" :key="agent._id"
          class="flex gap-3.5 p-4 bg-white border border-gray-100 rounded-xl cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 relative group"
          @click="startChat(agent)"
        >
          <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0" :style="{ background: agent.bgColor }">{{ agent.icon }}</div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-semibold text-gray-800 mb-1">{{ agent.name }}</div>
            <div class="text-xs text-gray-400 truncate mb-2">{{ agent.desc }}</div>
            <div class="flex items-center gap-1 text-xs text-gray-300"><el-icon><ChatDotRound /></el-icon> 我创建的</div>
          </div>
          <el-button class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" type="danger" text size="small" @click.stop="removeAgent(agent._id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Discovery -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div v-for="agent in filteredAgents" :key="agent.id"
        class="flex gap-3.5 p-4 bg-white border border-gray-100 rounded-xl cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5"
        @click="startChat(agent)"
      >
        <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0" :style="{ background: agent.bgColor }">{{ agent.icon }}</div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-semibold text-gray-800 mb-1">{{ agent.name }}</div>
          <div class="text-xs text-gray-400 truncate mb-2">{{ agent.desc }}</div>
          <div class="flex items-center gap-1 text-xs text-gray-300">
            <el-icon><ChatDotRound /></el-icon> {{ agent.chats }} 万人聊过
            <span>· @{{ agent.author }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreate" title="创建 AI 智能体" width="500px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="智能体名称" required>
          <el-input v-model="createForm.name" placeholder="例如：代码审查助手" />
        </el-form-item>
        <el-form-item label="简短描述">
          <el-input v-model="createForm.desc" placeholder="一句话描述这个智能体的功能" />
        </el-form-item>
        <el-form-item label="图标">
          <div class="flex flex-wrap gap-2">
            <div v-for="icon in iconOptions" :key="icon"
              :class="['w-10 h-10 rounded-lg flex items-center justify-center text-xl cursor-pointer border-2 transition-all',
                createForm.icon === icon ? 'border-blue-500 bg-blue-50' : 'border-transparent hover:bg-gray-100']"
              @click="createForm.icon = icon"
            >{{ icon }}</div>
          </div>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category" style="width:100%">
            <el-option v-for="cat in categories" :key="cat.key" :label="cat.label" :value="cat.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色设定（System Prompt）" required>
          <el-input v-model="createForm.systemPrompt" type="textarea" :rows="4" placeholder="描述这个智能体的角色、能力和行为规则..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="doCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, ChatDotRound, Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAgents, createAgent, deleteAgent } from '../api'

const router = useRouter()
const activeCategory = ref('work')
const showMy = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const myAgents = ref([])

const categories = [
  { key: 'work', label: '工作' },
  { key: 'study', label: '学习' },
  { key: 'create', label: '创作' },
  { key: 'life', label: '生活' },
]

const iconOptions = ['🤖', '✍️', '💡', '📊', '📝', '🎨', '🔬', '💻', '🌐', '🎯', '🚀', '⭐', '❤️', '🔥', '📚', '🎓']

const createForm = ref({ name: '', desc: '', icon: '🤖', bgColor: '#e8f0fe', category: 'work', systemPrompt: '' })

const builtInAgents = [
  { id: 1, name: '全能写作助手', desc: '提供多种文案创作选择，轻松完成各种文案...', icon: '✍️', bgColor: '#fff3e0', chats: 1384.5, author: '官方', category: 'work', systemPrompt: '你是一个专业的写作助手，可以帮助用户撰写各种类型的文案。' },
  { id: 2, name: '识图生成提示词', desc: '上传图片，根据图片内容精准生成提示词...', icon: '🖼️', bgColor: '#e3f2fd', chats: 111.1, author: '官方', category: 'work', systemPrompt: '你是一个图像分析助手，可以根据图片内容生成AI绘画提示词。' },
  { id: 3, name: 'EXCEL大全', desc: '拥有卓越数据处理能力，助您解决Excel各类...', icon: '📊', bgColor: '#e8f5e9', chats: 24.6, author: '社区', category: 'work', systemPrompt: '你是Excel专家，精通Excel公式、函数、数据分析、图表制作。' },
  { id: 4, name: '论文助手', desc: '能助力用户完成严谨详实论文的专业帮手', icon: '📝', bgColor: '#f3e5f5', chats: 45.6, author: '社区', category: 'work', systemPrompt: '你是一个论文写作助手，可以帮助用户进行论文选题、文献综述、论文结构设计。' },
  { id: 5, name: '公文写作', desc: '专业公文格式和写作规范', icon: '📋', bgColor: '#fce4ec', chats: 12.1, author: '社区', category: 'work', systemPrompt: '你是公文写作专家，精通各类公文格式和写作规范。' },
  { id: 6, name: '产品经理助手', desc: '专业的产品需求分析与PRD文档撰写', icon: '💡', bgColor: '#e0f7fa', chats: 89.3, author: '社区', category: 'work', systemPrompt: '你是资深产品经理助手，擅长需求分析、竞品分析、PRD文档撰写。' },
  { id: 7, name: 'Python编程', desc: '助您精通Python编程', icon: '🐍', bgColor: '#e8f5e9', chats: 28.4, author: '社区', category: 'study', systemPrompt: '你是Python编程专家，精通Python基础语法、面向对象编程、数据分析、Web开发。' },
  { id: 8, name: '英语写作润色', desc: 'An assistant dedicated to polishing English...', icon: '🔤', bgColor: '#e3f2fd', chats: 36.4, author: '官方', category: 'study', systemPrompt: 'You are an English writing assistant dedicated to polishing English writing.' },
  { id: 9, name: '中英翻译', desc: '专业翻译助手，精准转换中英内容', icon: '🌐', bgColor: '#fff3e0', chats: 318.2, author: '社区', category: 'study', systemPrompt: '你是专业翻译助手，精通中英互译，可以提供准确、流畅的翻译服务。' },
  { id: 10, name: '数学解题', desc: '帮你解答各种数学问题', icon: '🔢', bgColor: '#f3e5f5', chats: 156.7, author: '社区', category: 'study', systemPrompt: '你是数学解题助手，可以解答从小学到大学的各类数学问题。' },
  { id: 11, name: '高情商回复', desc: '聊天时不知道怎么回复，我来帮你~', icon: '💝', bgColor: '#fce4ec', chats: 1325.2, author: '社区', category: 'create', systemPrompt: '你是高情商聊天助手，擅长根据对话场景给出得体、温暖的回复建议。' },
  { id: 12, name: '爆款文案', desc: '知名博主，善写爆款文案', icon: '🔥', bgColor: '#fff3e0', chats: 85.4, author: '社区', category: 'create', systemPrompt: '你是爆款文案专家，精通小红书、抖音、微信公众号等平台的文案写作技巧。' },
  { id: 13, name: 'AI绘画助手', desc: '帮你生成各种风格的AI绘画提示词', icon: '🎨', bgColor: '#e8eaf6', chats: 203.8, author: '社区', category: 'create', systemPrompt: '你是AI绘画提示词专家，精通Midjourney、Stable Diffusion等工具的提示词编写。' },
  { id: 14, name: '故事创作', desc: '帮你创作各种精彩的故事和小说', icon: '📖', bgColor: '#f1f8e9', chats: 67.3, author: '社区', category: 'create', systemPrompt: '你是故事创作助手，擅长创作各种类型的故事，包括奇幻、科幻、悬疑、爱情等。' },
  { id: 15, name: '旅行规划', desc: '帮你制定完美的旅行计划和攻略', icon: '✈️', bgColor: '#e0f7fa', chats: 178.9, author: '社区', category: 'life', systemPrompt: '你是旅行规划助手，可以根据用户需求推荐目的地、安排行程。' },
  { id: 16, name: '健康顾问', desc: '提供健康饮食和运动建议', icon: '💪', bgColor: '#e8f5e9', chats: 95.6, author: '社区', category: 'life', systemPrompt: '你是健康顾问，可以提供健康饮食建议、运动方案、睡眠改善方法。' },
  { id: 17, name: '心理咨询', desc: '倾听你的烦恼，给你温暖的陪伴', icon: '🫂', bgColor: '#fce4ec', chats: 423.1, author: '社区', category: 'life', systemPrompt: '你是心理咨询助手，擅长倾听、共情，可以提供情绪支持和心理疏导建议。' },
  { id: 18, name: '美食推荐', desc: '根据你的口味推荐美食和菜谱', icon: '🍜', bgColor: '#fff3e0', chats: 234.5, author: '社区', category: 'life', systemPrompt: '你是美食推荐助手，可以根据用户口味偏好推荐合适的美食和菜谱。' },
  { id: 19, name: 'MiMo代码助手', desc: '基于MiMo大模型的智能编程助手，帮你写代码、调bug、解释代码', icon: '🤖', bgColor: '#e3f2fd', chats: 0, author: 'MiMo', category: 'work', systemPrompt: '你是MiMo代码助手，基于小米MiMo大模型。你精通多种编程语言（Python、JavaScript、Java、C++、Go等），擅长代码编写、调试、重构、代码审查和解释。你会用清晰简洁的中文回答编程问题，提供可运行的代码示例，并解释关键思路。' },
]

const filteredAgents = computed(() => builtInAgents.filter(a => a.category === activeCategory.value))

onMounted(() => { loadMyAgents() })

const loadMyAgents = async () => {
  try {
    const { data } = await getAgents()
    myAgents.value = data.agents || []
  } catch (e) {}
}

const doCreate = async () => {
  if (!createForm.value.name.trim()) return ElMessage.warning('请输入名称')
  if (!createForm.value.systemPrompt.trim()) return ElMessage.warning('请输入角色设定')
  creating.value = true
  try {
    await createAgent(createForm.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    createForm.value = { name: '', desc: '', icon: '🤖', bgColor: '#e8f0fe', category: 'work', systemPrompt: '' }
    await loadMyAgents()
  } catch (e) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const removeAgent = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这个智能体吗？', '提示', { type: 'warning' })
    await deleteAgent(id)
    ElMessage.success('已删除')
    await loadMyAgents()
  } catch (e) {}
}

const startChat = (agent) => {
  router.push({ path: '/chat', query: { agent: agent.name, prompt: agent.systemPrompt } })
}
</script>
