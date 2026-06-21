<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 文本模型 -->
      <el-tab-pane label="文本模型" name="text">
        <el-form label-width="120px" style="max-width:700px" v-loading="loading">
          <div v-for="p in textProviders" :key="p.name" class="mb-2">
            <el-divider content-position="left">
              <span class="flex items-center gap-2 text-sm font-medium">
                <span class="w-2.5 h-2.5 rounded-full" :style="{ background: colors[p.name] }"></span>
                {{ p.label }}
              </span>
            </el-divider>
            <el-form-item label="API Key">
              <div class="flex gap-2 items-center w-full">
                <el-input v-model="config[p.key]" show-password class="flex-1" :placeholder="p.ph" />
                <el-button type="primary" :loading="testing === p.name" @click="testConn(p)" :disabled="!config[p.key]">
                  {{ testing === p.name ? '测试中...' : '测试' }}
                </el-button>
                <el-tag v-if="testResults[p.name] === 'ok'" type="success" size="small">通</el-tag>
                <el-tag v-else-if="testResults[p.name] === 'fail'" type="danger" size="small">不通</el-tag>
              </div>
            </el-form-item>
            <el-form-item label="Base URL"><el-input v-model="config[p.url]" /></el-form-item>
            <el-form-item label="模型名称">
              <div class="flex gap-2 items-center w-full">
                <el-input v-model="config[p.model]" :placeholder="p.mp" class="flex-1" />
                <el-button type="success" :loading="fetchingModels === p.name" @click="fetchModels(p)" :disabled="!config[p.key] || !config[p.url]">
                  {{ fetchingModels === p.name ? '获取中...' : '获取模型' }}
                </el-button>
                <el-button v-if="modelLists[p.name] && modelLists[p.name].length" type="info" @click="showModelPicker(p.name)" :disabled="!config[p.key]">
                  选择
                </el-button>
              </div>
            </el-form-item>
          </div>
          <el-form-item><el-button type="primary" :loading="saving" @click="save" size="large">保存配置</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 图像模型 -->
      <el-tab-pane label="图像生成" name="image">
        <el-form label-width="120px" style="max-width:700px" v-loading="loading">
          <div class="mb-2">
            <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> 图像生成提供商</span></el-divider>
            <el-form-item label="提供商">
              <el-radio-group v-model="config.image_provider">
                <el-radio value="agnes">Agnes</el-radio>
                <el-radio value="custom">自定义</el-radio>
              </el-radio-group>
            </el-form-item>
          </div>

          <template v-if="config.image_provider === 'agnes'">
            <div class="mb-2">
              <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Agnes 图像模型</span></el-divider>
              <el-form-item label="图像模型1">
                <div class="flex gap-2 items-center w-full">
                  <el-input v-model="config.agnes_image_model_1" placeholder="agnes-image-2.0-flash" class="flex-1" />
                  <el-button type="primary" :loading="testing === 'agnes_image'" @click="testImageModel(config.agnes_image_model_1)" :disabled="!config.agnes_key">
                    {{ testing === 'agnes_image' ? '测试中...' : '测试' }}
                  </el-button>
                  <el-tag v-if="testResults.agnes_image === 'ok'" type="success" size="small">通</el-tag>
                  <el-tag v-else-if="testResults.agnes_image === 'fail'" type="danger" size="small">不通</el-tag>
                </div>
              </el-form-item>
              <el-form-item label="图像模型2">
                <el-input v-model="config.agnes_image_model_2" placeholder="agnes-image-2.1-flash" />
              </el-form-item>
            </div>
          </template>

          <template v-else>
            <div class="mb-2">
              <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-violet-500"></span> 自定义图像接口</span></el-divider>
              <el-form-item label="API Key"><el-input v-model="config.custom_image_key" show-password placeholder="输入 API Key" /></el-form-item>
              <el-form-item label="Base URL"><el-input v-model="config.custom_image_url" placeholder="https://api.xxx.com/v1/images/generations" /></el-form-item>
              <el-form-item label="模型名称"><el-input v-model="config.custom_image_model" placeholder="model-name" /></el-form-item>
            </div>
          </template>
          <el-form-item><el-button type="primary" :loading="saving" @click="save" size="large">保存配置</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 视频模型 -->
      <el-tab-pane label="视频生成" name="video">
        <el-form label-width="120px" style="max-width:700px" v-loading="loading">
          <div class="mb-2">
            <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-green-500"></span> 视频生成提供商</span></el-divider>
            <el-form-item label="提供商">
              <el-radio-group v-model="config.video_provider">
                <el-radio value="agnes">Agnes</el-radio>
                <el-radio value="custom">自定义</el-radio>
              </el-radio-group>
            </el-form-item>
          </div>

          <template v-if="config.video_provider === 'agnes'">
            <div class="mb-2">
              <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-green-500"></span> Agnes 视频模型</span></el-divider>
              <el-form-item label="视频模型">
                <div class="flex gap-2 items-center w-full">
                  <el-input v-model="config.agnes_video_model" placeholder="agnes-video-v2.0" class="flex-1" />
                  <el-button type="primary" :loading="testing === 'agnes_video'" @click="testVideoModel(config.agnes_video_model)" :disabled="!config.agnes_key">
                    {{ testing === 'agnes_video' ? '测试中...' : '测试' }}
                  </el-button>
                  <el-tag v-if="testResults.agnes_video === 'ok'" type="success" size="small">通</el-tag>
                  <el-tag v-else-if="testResults.agnes_video === 'fail'" type="danger" size="small">不通</el-tag>
                </div>
              </el-form-item>
            </div>
          </template>

          <template v-else>
            <div class="mb-2">
              <el-divider content-position="left"><span class="flex items-center gap-2 text-sm font-medium"><span class="w-2.5 h-2.5 rounded-full bg-red-500"></span> 自定义视频接口</span></el-divider>
              <el-form-item label="API Key"><el-input v-model="config.custom_video_key" show-password placeholder="输入 API Key" /></el-form-item>
              <el-form-item label="Base URL"><el-input v-model="config.custom_video_url" placeholder="https://api.xxx.com/v1/video/generations" /></el-form-item>
              <el-form-item label="模型名称"><el-input v-model="config.custom_video_model" placeholder="model-name" /></el-form-item>
            </div>
          </template>
          <el-form-item><el-button type="primary" :loading="saving" @click="save" size="large">保存配置</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 模型设置 -->
      <el-tab-pane label="模型设置" name="model">
        <el-form label-width="120px" style="max-width:600px" v-loading="loading">
          <el-form-item label="默认文本模型">
            <el-select v-model="config.default_provider" style="width:100%">
              <el-option v-for="p in textProviders" :key="p.name" :label="p.label" :value="p.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="Temperature"><el-slider v-model="config.temperature" :min="0" :max="1" :step="0.1" show-input /></el-form-item>
          <el-form-item label="Max Tokens"><el-input-number v-model="config.max_tokens" :min="256" :max="8192" :step="256" /></el-form-item>
          <el-form-item><el-button type="primary" :loading="saving" @click="save">保存设置</el-button></el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 系统信息 -->
      <el-tab-pane label="系统信息" name="info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
          <el-descriptions-item label="运行状态"><el-tag type="success" size="small">正常</el-tag></el-descriptions-item>
          <el-descriptions-item label="Python">3.13.13</el-descriptions-item>
          <el-descriptions-item label="Node.js">24.15.0</el-descriptions-item>
          <el-descriptions-item label="LangChain">1.3.9</el-descriptions-item>
          <el-descriptions-item label="API 地址">http://localhost:8000</el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="modelPickerVisible" title="选择模型" width="400px" :close-on-click-modal="false">
      <el-input v-model="modelSearch" placeholder="搜索模型..." clearable style="margin-bottom:12px" />
      <el-scrollbar height="300px">
        <div v-for="model in filteredModels" :key="model"
          class="px-3 py-2 cursor-pointer rounded text-xs font-mono hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
          @click="selectModel(model)"
        >{{ model }}</div>
        <div v-if="!filteredModels.length" class="text-center text-gray-400 py-5">无匹配模型</div>
      </el-scrollbar>
      <template #footer>
        <el-button @click="modelPickerVisible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, saveSettings, testLLM, getModelList, testImageModel as testImageApi, testVideoModel as testVideoApi } from '../api'

const activeTab = ref('text')
const loading = ref(false)
const saving = ref(false)
const testing = ref('')
const testResults = reactive({})
const fetchingModels = ref('')
const modelLists = reactive({})
const modelPickerVisible = ref(false)
const modelSearch = ref('')
const currentPickerProvider = ref('')
const filteredModels = ref([])

const textProviders = [
  { name: 'deepseek', label: 'DeepSeek', key: 'deepseek_key', url: 'deepseek_url', model: 'deepseek_model', ph: 'sk-xxx', mp: 'deepseek-chat' },
  { name: 'mimo', label: 'MiMo', key: 'mimo_key', url: 'mimo_url', model: 'mimo_model', ph: 'xxx', mp: 'mimo-auto' },
  { name: 'agnes', label: 'Agnes', key: 'agnes_key', url: 'agnes_url', model: 'agnes_model', ph: 'sk-xxx', mp: 'agnes-2.0-flash' },
  { name: 'qwen', label: '通义千问', key: 'qwen_key', url: 'qwen_url', model: 'qwen_model', ph: 'sk-xxx', mp: 'qwen-turbo' },
  { name: 'glm', label: '智谱GLM', key: 'glm_key', url: 'glm_url', model: 'glm_model', ph: 'xxx', mp: 'glm-4-flash' },
  { name: 'openai', label: 'OpenAI', key: 'openai_key', url: 'openai_url', model: 'openai_model', ph: 'sk-xxx', mp: 'gpt-3.5-turbo' },
  { name: 'custom', label: '自定义API', key: 'custom_key', url: 'custom_url', model: 'custom_model', ph: 'sk-xxx', mp: 'model-name' },
]
const colors = { deepseek: '#3b82f6', mimo: '#22c55e', agnes: '#f59e0b', qwen: '#ef4444', glm: '#8b5cf6', openai: '#06b6d4', custom: '#64748b' }

const config = reactive({
  deepseek_key: '', deepseek_url: 'https://api.deepseek.com', deepseek_model: 'deepseek-chat',
  mimo_key: '', mimo_url: 'https://api.mimo.xiaomi.com', mimo_model: 'mimo-auto',
  agnes_key: '', agnes_url: 'https://apihub.agnes-ai.com', agnes_model: 'agnes-2.0-flash',
  qwen_key: '', qwen_url: 'https://dashscope.aliyuncs.com', qwen_model: 'qwen-turbo',
  glm_key: '', glm_url: 'https://open.bigmodel.cn/api/paas/v4', glm_model: 'glm-4-flash',
  openai_key: '', openai_url: 'https://api.openai.com', openai_model: 'gpt-3.5-turbo',
  custom_key: '', custom_url: '', custom_model: '',
  image_provider: 'agnes',
  agnes_image_model_1: 'agnes-image-2.0-flash', agnes_image_model_2: 'agnes-image-2.1-flash',
  custom_image_key: '', custom_image_url: '', custom_image_model: '',
  video_provider: 'agnes',
  agnes_video_model: 'agnes-video-v2.0',
  custom_video_key: '', custom_video_url: '', custom_video_model: '',
  default_provider: 'agnes', temperature: 0.7, max_tokens: 2048,
})

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await getSettings()
    Object.keys(config).forEach(k => { if (data[k] !== undefined && data[k] !== null) config[k] = data[k] })
  } catch (e) {}
  loading.value = false
})

const testConn = async (p) => {
  if (!config[p.key]) { ElMessage.warning('请先填写 API Key'); return }
  testing.value = p.name
  try {
    const { data } = await testLLM(p.name, config[p.key], config[p.url], config[p.model])
    testResults[p.name] = data.status === 'ok' ? 'ok' : 'fail'
    ElMessage[data.status === 'ok' ? 'success' : 'error'](`${p.label}: ${data.message}`)
  } catch (e) { testResults[p.name] = 'fail'; ElMessage.error(`${p.label}: 请求失败`) }
  testing.value = ''
}

const testImageModel = async (model) => {
  if (!config.agnes_key) { ElMessage.warning('请先在文本模型中配置 Agnes API Key'); return }
  testing.value = 'agnes_image'
  try {
    const { data } = await testImageApi(config.agnes_key, config.agnes_url, model)
    testResults.agnes_image = data.status === 'ok' ? 'ok' : 'fail'
    ElMessage[data.status === 'ok' ? 'success' : 'error'](`图像模型: ${data.message}`)
  } catch (e) { testResults.agnes_image = 'fail'; ElMessage.error('测试失败') }
  testing.value = ''
}

const testVideoModel = async (model) => {
  if (!config.agnes_key) { ElMessage.warning('请先在文本模型中配置 Agnes API Key'); return }
  testing.value = 'agnes_video'
  try {
    const { data } = await testVideoApi(config.agnes_key, config.agnes_url, model)
    testResults.agnes_video = data.status === 'ok' ? 'ok' : 'fail'
    ElMessage[data.status === 'ok' ? 'success' : 'error'](`视频模型: ${data.message}`)
  } catch (e) { testResults.agnes_video = 'fail'; ElMessage.error('测试失败') }
  testing.value = ''
}

const fetchModels = async (p) => {
  if (!config[p.key]) { ElMessage.warning('请先填写 API Key'); return }
  if (!config[p.url]) { ElMessage.warning('请先填写 Base URL'); return }
  fetchingModels.value = p.name
  try {
    const { data } = await getModelList(config[p.key], config[p.url])
    if (data.status === 'ok') {
      modelLists[p.name] = data.models || []
      ElMessage.success(`${p.label}: 获取到 ${data.models.length} 个模型`)
    } else {
      ElMessage.error(`${p.label}: ${data.message}`)
      modelLists[p.name] = []
    }
  } catch (e) { ElMessage.error('获取模型列表失败'); modelLists[p.name] = [] }
  fetchingModels.value = ''
}

const showModelPicker = (providerName) => {
  currentPickerProvider.value = providerName
  modelSearch.value = ''
  updateFilteredModels()
  modelPickerVisible.value = true
}

const updateFilteredModels = () => {
  const list = modelLists[currentPickerProvider.value] || []
  if (!modelSearch.value) { filteredModels.value = list; return }
  const kw = modelSearch.value.toLowerCase()
  filteredModels.value = list.filter(m => m.toLowerCase().includes(kw))
}

watch(modelSearch, () => updateFilteredModels())

const selectModel = (model) => {
  const p = textProviders.find(p => p.name === currentPickerProvider.value)
  if (p) config[p.model] = model
  modelPickerVisible.value = false
}

const save = async () => {
  saving.value = true
  try {
    await saveSettings(config)
    ElMessage.success('配置已保存并生效')
  } catch (e) { ElMessage.error('保存失败') }
  saving.value = false
}
</script>
