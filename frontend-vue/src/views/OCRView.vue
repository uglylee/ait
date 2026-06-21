<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <!-- Left: Upload -->
      <div class="lg:col-span-2">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100">
          <div class="px-5 py-4 border-b border-gray-100">
            <h3 class="text-base font-semibold text-gray-800">OCR 文字识别</h3>
          </div>
          <div class="p-5">
            <div v-if="!previewUrl"
              class="border-2 border-dashed border-gray-200 rounded-lg p-12 text-center cursor-pointer transition-all hover:border-indigo-400 hover:bg-indigo-50"
              @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop"
            >
              <div class="text-5xl mb-3">📁</div>
              <p class="text-gray-600 mb-1">点击或拖拽上传图片</p>
              <p class="text-xs text-gray-400">支持 JPG, PNG, WEBP</p>
            </div>
            <div v-else class="text-center">
              <img :src="previewUrl" class="max-w-full max-h-[300px] rounded-lg border border-gray-100" />
              <div class="mt-3">
                <el-button size="small" @click="clearImg">重新选择</el-button>
              </div>
            </div>
            <input ref="fileRef" type="file" accept="image/*" style="display:none" @change="onFileChange" />
            <el-button type="primary" :loading="loading" :disabled="!selectedFile" @click="recognize" class="w-full !mt-4">
              开始识别
            </el-button>
          </div>
        </div>
      </div>

      <!-- Right: Results -->
      <div class="lg:col-span-3">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 h-full">
          <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-800">识别结果</h3>
            <el-tag v-if="result" :type="result.confidence > 0.9 ? 'success' : 'warning'" size="small">
              置信度 {{ (result.confidence * 100).toFixed(1) }}%
            </el-tag>
          </div>
          <div class="p-5 min-h-[200px]">
            <div v-if="!result" class="h-[200px] flex items-center justify-center">
              <p class="text-gray-400">上传图片后点击识别</p>
            </div>
            <div v-else>
              <el-tabs v-model="activeTab" @tab-change="onTabChange">
                <el-tab-pane label="原始识别" name="raw">
                  <pre class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">{{ result.text }}</pre>
                </el-tab-pane>
                <el-tab-pane label="AI 增强" name="enhanced">
                  <div v-if="enhancing" class="text-center py-10">
                    <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                    <p class="text-gray-400 mt-2 text-sm">AI 增强中...</p>
                  </div>
                  <pre v-else class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">{{ enhancedText }}</pre>
                </el-tab-pane>
              </el-tabs>
              <el-button size="small" class="!mt-3" @click="copyText">复制文本</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ocrRecognize, ocrEnhance } from '../api'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const fileRef = ref(null)
const previewUrl = ref('')
const selectedFile = ref(null)
const loading = ref(false)
const result = ref(null)
const activeTab = ref('raw')
const enhancedText = ref('')
const enhancing = ref(false)

const triggerUpload = () => fileRef.value?.click()
const onFileChange = (e) => { const f = e.target.files[0]; if (f) processFile(f) }
const onDrop = (e) => { const f = e.dataTransfer.files[0]; if (f) processFile(f) }
const processFile = (f) => { if (!f.type.startsWith('image/')) return ElMessage.warning('请上传图片'); selectedFile.value = f; previewUrl.value = URL.createObjectURL(f) }
const clearImg = () => { previewUrl.value = ''; selectedFile.value = null; result.value = null; enhancedText.value = ''; activeTab.value = 'raw'; if (fileRef.value) fileRef.value.value = '' }

const recognize = async () => {
  if (!selectedFile.value) return
  loading.value = true
  enhancedText.value = ''
  activeTab.value = 'raw'
  try {
    const { data } = await ocrRecognize(selectedFile.value)
    result.value = data
  } catch (e) { ElMessage.error('识别失败') } finally { loading.value = false }
}

const onTabChange = async (tab) => {
  if (tab === 'enhanced' && result.value && !enhancedText.value) {
    enhancing.value = true
    try {
      const { data } = await ocrEnhance(result.value.text)
      enhancedText.value = data.enhanced || result.value.text
    } catch (e) { enhancedText.value = result.value.text } finally { enhancing.value = false }
  }
}

const copyText = () => { if (result.value) { const text = activeTab.value === 'enhanced' ? enhancedText.value : result.value.text; navigator.clipboard.writeText(text); ElMessage.success('已复制') } }
</script>
