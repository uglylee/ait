<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="10">
        <div class="page-card">
          <div class="card-header"><h3>OCR 文字识别</h3></div>
          <div class="card-body">
            <div v-if="!previewUrl" class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="onDrop">
              <div style="font-size:48px;margin-bottom:12px">📁</div>
              <p style="color:#606266;margin-bottom:4px">点击或拖拽上传图片</p>
              <p style="color:#909399;font-size:12px">支持 JPG, PNG, WEBP</p>
            </div>
            <div v-else style="text-align:center">
              <img :src="previewUrl" style="max-width:100%;max-height:300px;border-radius:8px;border:1px solid #ebeef5" />
              <div style="margin-top:12px">
                <el-button size="small" @click="clearImg">重新选择</el-button>
              </div>
            </div>
            <input ref="fileRef" type="file" accept="image/*" style="display:none" @change="onFileChange" />
            <el-button type="primary" :loading="loading" :disabled="!selectedFile" @click="recognize" style="width:100%;margin-top:16px">
              开始识别
            </el-button>
          </div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="page-card" style="height:100%">
          <div class="card-header">
            <h3>识别结果</h3>
            <el-tag v-if="result" :type="result.confidence > 0.9 ? 'success' : 'warning'" size="small">
              置信度 {{ (result.confidence * 100).toFixed(1) }}%
            </el-tag>
          </div>
          <div class="card-body" style="min-height:200px">
            <div v-if="!result" class="empty-state">
              <p style="color:#909399">上传图片后点击识别</p>
            </div>
            <div v-else>
              <el-tabs v-model="activeTab" @tab-change="onTabChange">
                <el-tab-pane label="原始识别" name="raw">
                  <pre style="white-space:pre-wrap;font-size:14px;color:#303133;line-height:1.8">{{ result.text }}</pre>
                </el-tab-pane>
                <el-tab-pane label="AI 增强" name="enhanced">
                  <div v-if="enhancing" style="text-align:center;padding:40px 0">
                    <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                    <p style="color:#909399;margin-top:8px">AI 增强中...</p>
                  </div>
                  <pre v-else style="white-space:pre-wrap;font-size:14px;color:#303133;line-height:1.8">{{ enhancedText }}</pre>
                </el-tab-pane>
              </el-tabs>
              <el-button size="small" style="margin-top:12px" @click="copyText">复制文本</el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
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

<style scoped>
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 48px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-area:hover { border-color: #409eff; background: #ecf5ff; }
.empty-state { height: 200px; display: flex; align-items: center; justify-content: center; }
</style>
