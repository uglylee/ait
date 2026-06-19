<template>
  <div class="media-page">
    <div class="welcome-section">
      <h1><span class="welcome-highlight">欢迎</span> 我能为您做什么？</h1>
    </div>

    <div class="input-card">
      <textarea
        v-model="prompt"
        rows="3"
        :placeholder="type === 'image' ? '描述你想要生成的图片' : type === 'video' ? '描述你想要生成的视频' : type === 'doc' ? '描述你想要生成的文档内容' : '请输入文章主题，例如：人工智能在医疗领域的应用'"
        @keydown.enter.ctrl="generate"
        @keydown.enter.meta="generate"
      ></textarea>
      <div v-if="uploadedImage" class="uploaded-preview">
        <img :src="uploadedImage.preview" />
        <button class="remove-btn" @click="removeUploadedImage">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>
      <div class="input-toolbar">
        <div class="toolbar-left">
          <button class="toolbar-btn" @click="showSettings = !showSettings" title="参数设置">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="toolbar-btn" title="上传参考图" @click="$refs.fileInput.click()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
          </button>
          <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="handleFileUpload" />
          <div class="type-switch">
            <button :class="{ active: type === 'image' }" @click="type = 'image'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
              AI 设计
            </button>
            <button :class="{ active: type === 'video' }" @click="type = 'video'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg>
              AI 视频
            </button>
            <button :class="{ active: type === 'write' }" @click="type = 'write'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              AI 写作
            </button>
            <button :class="{ active: type === 'doc' }" @click="type = 'doc'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
              AI 文档
            </button>
          </div>
          <div v-if="type !== 'write' && type !== 'doc'" class="model-selector" @click="showModelMenu = !showModelMenu">
            <span class="model-icon">🎨</span>
            <span>{{ currentModelLabel }}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
            <div v-if="showModelMenu" class="model-menu" @click.stop>
              <div v-for="m in allDisplayModels" :key="m.id"
                class="model-option" :class="{ active: model === m.id }" @click="selectModel(m.id)">
                {{ m.name }}
              </div>
            </div>
          </div>
        </div>
        <button class="send-btn" :disabled="generating || !prompt.trim()" @click="generate">
          <svg v-if="!generating" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
          <div v-else class="btn-spinner"></div>
        </button>
      </div>

      <!-- 参数设置面板 -->
      <div v-if="showSettings" class="settings-panel">
        <div v-if="type === 'image'">
          <div class="settings-row">
            <div class="setting-item">
              <label>尺寸</label>
              <select v-model="settings.image_size">
                <option value="original">和原图一样</option>
                <optgroup label="正方形">
                  <option value="256">256×256 (小)</option>
                  <option value="512">512×512 (标准)</option>
                  <option value="768">768×768 (高清)</option>
                  <option value="1024">1024×1024 (2K)</option>
                  <option value="2048">2048×2048 (4K)</option>
                  <option value="4096">4096×4096 (8K)</option>
                </optgroup>
                <optgroup label="横版">
                  <option value="1024x768">1024×768 (4:3)</option>
                  <option value="1280x720">1280×720 (16:9)</option>
                  <option value="1920x1080">1920×1080 (全高清)</option>
                  <option value="2560x1440">2560×1440 (2K)</option>
                  <option value="3840x2160">3840×2160 (4K)</option>
                </optgroup>
                <optgroup label="竖版">
                  <option value="768x1024">768×1024 (3:4)</option>
                  <option value="720x1280">720×1280 (9:16)</option>
                  <option value="1080x1920">1080×1920 (全高清竖版)</option>
                  <option value="1440x2560">1440×2560 (2K竖版)</option>
                  <option value="2160x3840">2160×3840 (4K竖版)</option>
                </optgroup>
              </select>
            </div>
            <div class="setting-item">
              <label>数量</label>
              <select v-model.number="settings.image_num">
                <option :value="1">1</option>
                <option :value="2">2</option>
                <option :value="3">3</option>
                <option :value="4">4</option>
              </select>
            </div>
            <div class="setting-item">
              <label>质量</label>
              <select v-model="settings.image_quality">
                <option value="draft">草稿 (快速)</option>
                <option value="standard">标准</option>
                <option value="hd">高清</option>
                <option value="fhd">超清 (FHD)</option>
                <option value="uhd">极清 (UHD)</option>
                <option value="max">最高质量</option>
              </select>
            </div>
          </div>
          <div class="settings-row">
            <div class="setting-item">
              <label>风格</label>
              <select v-model="settings.image_style">
                <option value="">默认</option>
                <option value="photorealistic">写实</option>
                <option value="anime">动漫</option>
                <option value="oil-painting">油画</option>
                <option value="watercolor">水彩</option>
                <option value="sketch">素描</option>
                <option value="digital-art">数字艺术</option>
                <option value="3d-render">3D渲染</option>
              </select>
            </div>
            <div class="setting-item">
              <label>种子</label>
              <input type="number" v-model.number="settings.image_seed" placeholder="随机" class="setting-input" />
            </div>
            <div class="setting-item">
              <label>引导系数</label>
              <input type="number" v-model.number="settings.image_guidance_scale" placeholder="默认" min="1" max="30" step="0.5" class="setting-input" />
            </div>
          </div>
          <div class="settings-row">
            <div class="setting-item setting-item-full">
              <label>反向提示词</label>
              <input type="text" v-model="settings.image_negative_prompt" placeholder="不希望出现的内容，如：blurry, low quality" class="setting-input-wide" />
            </div>
          </div>
        </div>
        <div v-else-if="type === 'video'">
          <div class="settings-row">
            <div class="setting-item">
              <label>时长</label>
              <select v-model.number="settings.video_duration">
                <option :value="3">3秒</option>
                <option :value="5">5秒</option>
                <option :value="8">8秒</option>
                <option :value="10">10秒</option>
              </select>
            </div>
            <div class="setting-item">
              <label>帧率</label>
              <select v-model.number="settings.video_fps">
                <option :value="12">12</option>
                <option :value="18">18</option>
                <option :value="24">24</option>
                <option :value="30">30</option>
              </select>
            </div>
            <div class="setting-item">
              <label>分辨率</label>
              <select v-model="settings.video_resolution">
                <option value="360p">360p (流畅)</option>
                <option value="480p">480p (标清)</option>
                <option value="720p">720p (高清)</option>
                <option value="1080p">1080p (全高清)</option>
                <option value="1440p">1440p (2K)</option>
                <option value="2160p">2160p (4K)</option>
              </select>
            </div>
          </div>
          <div class="settings-row">
            <div class="setting-item">
              <label>种子</label>
              <input type="number" v-model.number="settings.video_seed" placeholder="随机" class="setting-input" />
            </div>
            <div class="setting-item setting-item-full">
              <label>反向提示词</label>
              <input type="text" v-model="settings.video_negative_prompt" placeholder="不希望出现的内容" class="setting-input-wide" />
            </div>
          </div>
        </div>
        <div v-else-if="type === 'write'">
          <div class="settings-row">
            <div class="setting-item">
              <label>写作风格</label>
              <select v-model="settings.write_style">
                <option value="专业分析">专业分析</option>
                <option value="科普文章">科普文章</option>
                <option value="新闻报道">新闻报道</option>
                <option value="产品文案">产品文案</option>
              </select>
            </div>
            <div class="setting-item">
              <label>文章长度</label>
              <select v-model="settings.write_length">
                <option value="short">短篇</option>
                <option value="medium">中篇</option>
                <option value="long">长篇</option>
              </select>
            </div>
          </div>
          <div class="settings-row">
            <div class="setting-item setting-item-full">
              <label>补充说明</label>
              <input type="text" v-model="settings.write_extra" placeholder="其他要求（可选）" class="setting-input-wide" />
            </div>
          </div>
        </div>
        <div v-else-if="type === 'doc'">
          <div class="settings-row">
            <div class="setting-item">
              <label>文档格式</label>
              <select v-model="settings.doc_format">
                <option value="pptx">PPT 演示文稿</option>
                <option value="pdf">PDF 文档</option>
                <option value="docx">Word 文档</option>
              </select>
            </div>
            <div class="setting-item">
              <label>文档风格</label>
              <select v-model="settings.doc_style">
                <option value="商务">商务</option>
                <option value="学术">学术</option>
                <option value="简洁">简洁</option>
                <option value="创意">创意</option>
              </select>
            </div>
            <div class="setting-item">
              <label>页数</label>
              <select v-model.number="settings.doc_pages">
                <option :value="5">5页</option>
                <option :value="10">10页</option>
                <option :value="15">15页</option>
                <option :value="20">20页</option>
                <option :value="30">30页</option>
              </select>
            </div>
          </div>
          <div class="settings-row">
            <div class="setting-item setting-item-full">
              <label>补充说明</label>
              <input type="text" v-model="settings.doc_extra" placeholder="其他要求（可选）" class="setting-input-wide" />
            </div>
          </div>
        </div>
        <div class="settings-row"><button class="setting-save" @click="saveSettings">保存</button></div>
      </div>

      <!-- 生成进度 -->
      <div v-if="generating" class="progress-bar">
        <div class="progress-text">
          <div class="btn-spinner"></div>
          <span>{{ statusText }}</span>
        </div>
      </div>
    </div>

    <!-- 生成结果 -->
    <div v-if="results.length" class="results-section">
      <div v-if="type === 'write'" class="write-results">
        <div v-for="(r, i) in results" :key="i" class="write-result-card">
          <div class="write-result-header">
            <h3>{{ r.title }}</h3>
            <div class="write-result-actions">
              <button class="action-btn" @click="copyText(r.content)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                复制
              </button>
              <button class="action-btn" @click="downloadText(r)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                下载
              </button>
            </div>
          </div>
          <div class="write-result-content" v-html="r.content"></div>
        </div>
      </div>
      <div v-else-if="type === 'doc'" class="doc-results">
        <div v-for="(r, i) in results" :key="i" class="doc-result-card">
          <div class="doc-result-preview">
            <div v-if="r.previewLoading" class="doc-preview-loading">
              <div class="btn-spinner"></div>
              <span>正在加载预览...</span>
            </div>
            <iframe v-else-if="r.previewHtml" :srcdoc="r.previewHtml" class="doc-preview-iframe"></iframe>
            <div v-else class="doc-preview-placeholder">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1">
                <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
              </svg>
              <span>{{ r.format.toUpperCase() }} 文档</span>
            </div>
          </div>
          <div class="doc-result-footer">
            <div class="doc-result-info">
              <div class="doc-result-name">{{ r.filename }}</div>
              <div class="doc-result-format">{{ r.format === 'pptx' ? 'PPT' : r.format === 'docx' ? 'Word' : 'PDF' }} 文档</div>
            </div>
            <div class="doc-result-actions">
              <button class="action-btn download-btn" @click.stop="downloadFile(r)" title="下载">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                下载
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="results-grid">
        <div v-for="(r, i) in results" :key="i" class="result-item">
          <div class="result-media" @click="openFull(r.src)">
            <img v-if="r.type === 'image'" :src="r.src" />
            <video v-else controls @click.stop :src="r.src"></video>
          </div>
          <div class="result-actions">
            <button class="action-btn download-btn" @click.stop="downloadFile(r)" title="下载">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              下载
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误 -->
    <div v-if="error" class="error-toast">
      <span>✕</span> {{ error }}
    </div>

    <!-- 示例模板 -->
    <div v-if="!results.length && !generating" class="examples-section">
      <div class="examples-grid">
        <div v-for="(ex, i) in examples" :key="i" class="example-card" @click="applyTemplate(ex)">
          <div class="example-content">
            <div class="example-text">
              <div class="example-title">{{ ex.title }}</div>
              <div class="example-desc">{{ ex.desc }}</div>
            </div>
            <div class="example-thumb" :style="{ background: ex.color }">
              <span>{{ ex.icon }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div v-if="gallery.length && !generating" class="gallery-section">
      <h3 class="section-title">历史记录</h3>
      <div class="gallery-grid">
        <div v-for="(r, i) in gallery" :key="'g'+i" class="gallery-item">
          <div class="result-media" @click="openFull(r.src)">
            <img v-if="r.type === 'image'" :src="r.src" />
            <video v-else controls @click.stop :src="r.src"></video>
          </div>
          <div class="gallery-actions">
            <button class="action-btn-sm" @click.stop="downloadFile(r)" title="下载">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 全屏预览 -->
    <div v-if="fullSrc" class="fullscreen" @click="fullSrc = ''">
      <img :src="fullSrc" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'

const type = ref('image')
const model = ref('agnes-image-2.1-flash')
const prompt = ref('')
const generating = ref(false)
const statusText = ref('')
const results = ref([])
const error = ref('')
const gallery = ref([])
const fullSrc = ref('')
const showSettings = ref(false)
const showModelMenu = ref(false)
const uploadedImage = ref(null)

const settings = reactive({
  image_size: '1920x1080', image_num: 1, image_quality: 'fhd',
  image_negative_prompt: '', image_style: '', image_seed: null, image_guidance_scale: null,
  video_duration: 5, video_fps: 24, video_resolution: '720p',
  video_negative_prompt: '', video_seed: null,
  write_style: '专业分析', write_length: 'medium', write_extra: '',
  doc_format: 'pptx', doc_style: '商务', doc_pages: 10, doc_extra: '',
})

const imageModels = ref([])
const videoModels = ref([])

const currentModelLabel = computed(() => {
  const all = [...imageModels.value, ...videoModels.value]
  const found = all.find(m => m.id === model.value)
  return found?.name || model.value
})

const allDisplayModels = computed(() => {
  if (type.value === 'write') return []
  const list = type.value === 'image' ? imageModels.value : videoModels.value
  if (model.value && !list.find(m => m.id === model.value)) {
    return [{ id: model.value, name: model.value, provider: '' }, ...list]
  }
  return list
})

const examples = [
  { title: '赛博朋克城市夜景', desc: 'Neon-lit cyberpunk cityscape at night with flying cars and holographic billboards...', icon: '🌃', color: '#1a1a3e', prompt: 'Neon-lit cyberpunk cityscape at night with flying cars and holographic billboards, rain-slicked streets, volumetric lighting, ultra detailed', params: { image_size: '1024', image_quality: 'hd', image_negative_prompt: 'blurry, low quality, deformed' } },
  { title: '水墨山水画', desc: 'Traditional Chinese ink wash painting of misty mountains and flowing rivers...', icon: '🏔️', color: '#2d3436', prompt: 'Traditional Chinese ink wash painting of misty mountains and flowing rivers, elegant brushstrokes, serene atmosphere', params: { image_style: 'watercolor', image_size: '768x1024' } },
  { title: '可爱猫咪头像', desc: 'A cute fluffy kitten sitting on a windowsill, warm sunlight, soft focus...', icon: '🐱', color: '#fdcb6e', prompt: 'A cute fluffy kitten sitting on a windowsill, warm sunlight, soft focus, bokeh background, adorable expression', params: { image_size: '512', image_quality: 'hd', image_style: 'photorealistic' } },
  { title: '科幻太空站', desc: 'Futuristic space station orbiting Earth, detailed metal structures, stars...', icon: '🚀', color: '#0c2461', prompt: 'Futuristic space station orbiting Earth, detailed metal structures, stars in background, cinematic lighting, sci-fi concept art', params: { image_size: '1024', image_quality: 'hd', image_negative_prompt: 'blurry, low quality' } },
  { title: '日系动漫少女', desc: 'High-quality anime illustration of a girl with flowing hair, cherry blossoms...', icon: '🌸', color: '#e84393', prompt: 'High-quality anime illustration of a girl with flowing hair, cherry blossoms, pastel colors, detailed eyes, studio ghibli style', params: { image_style: 'anime', image_size: '768x1024' } },
  { title: '美食摄影', desc: 'Professional food photography of a gourmet dish, warm lighting, bokeh...', icon: '🍜', color: '#e17055', prompt: 'Professional food photography of a gourmet dish, warm lighting, bokeh background, shallow depth of field, appetizing colors', params: { image_style: 'photorealistic', image_size: '1024x768', image_quality: 'hd' } },
  { title: '极简 Logo 设计', desc: 'Minimalist modern logo design, clean lines, professional branding...', icon: '✨', color: '#636e72', prompt: 'Minimalist modern logo design, clean lines, professional branding, vector style, white background, simple geometric shapes', params: { image_size: '512', image_negative_prompt: 'complex, busy, cluttered' } },
  { title: '油画风景', desc: 'Impressionist oil painting of a sunset over lavender fields in Provence...', icon: '🎨', color: '#a29bfe', prompt: 'Impressionist oil painting of a sunset over lavender fields in Provence, golden hour, thick brushstrokes, vibrant colors', params: { image_style: 'oil-painting', image_size: '1024x768' } },
]

const API = '/api/v1'

onMounted(() => {
  loadGallery()
  loadModels()
  document.addEventListener('click', () => { showModelMenu.value = false })
})

watch(type, (v) => {
  const models = v === 'image' ? imageModels.value : videoModels.value
  model.value = models.length > 0 ? models[0].id : (v === 'image' ? 'agnes-image-2.1-flash' : 'agnes-video-v2.0')
})

const loadSettings = async () => {
  try {
    const resp = await fetch(`${API}/settings`)
    const data = await resp.json()
    if (data.image_size) settings.image_size = data.image_size
    if (data.image_num) settings.image_num = Number(data.image_num)
    if (data.image_quality) settings.image_quality = data.image_quality
    if (data.image_negative_prompt !== undefined) settings.image_negative_prompt = data.image_negative_prompt
    if (data.image_style !== undefined) settings.image_style = data.image_style
    if (data.image_seed) settings.image_seed = Number(data.image_seed)
    if (data.image_guidance_scale) settings.image_guidance_scale = Number(data.image_guidance_scale)
    if (data.video_duration) settings.video_duration = Number(data.video_duration)
    if (data.video_fps) settings.video_fps = Number(data.video_fps)
    if (data.video_resolution) settings.video_resolution = data.video_resolution
    if (data.video_negative_prompt !== undefined) settings.video_negative_prompt = data.video_negative_prompt
    if (data.video_seed) settings.video_seed = Number(data.video_seed)
    if (data.write_style) settings.write_style = data.write_style
    if (data.write_length) settings.write_length = data.write_length
    if (data.write_extra !== undefined) settings.write_extra = data.write_extra
  } catch (e) {}
}

const loadModels = async () => {
  try {
    const resp = await fetch(`${API}/media/models`)
    const data = await resp.json()
    imageModels.value = data.image_models || []
    videoModels.value = data.video_models || []
    
    if (imageModels.value.length === 0) {
      imageModels.value = [{ id: 'agnes-image-2.1-flash', name: 'agnes-image-2.1-flash', provider: 'agnes' }]
    }
    if (videoModels.value.length === 0) {
      videoModels.value = [{ id: 'agnes-video-v2.0', name: 'agnes-video-v2.0', provider: 'agnes' }]
    }
    
    if (type.value === 'image' && imageModels.value.length > 0) {
      model.value = imageModels.value[0].id
    }
    if (type.value === 'video' && videoModels.value.length > 0) {
      model.value = videoModels.value[0].id
    }
  } catch (e) {
    imageModels.value = [{ id: 'agnes-image-2.1-flash', name: 'agnes-image-2.1-flash', provider: 'agnes' }]
    videoModels.value = [{ id: 'agnes-video-v2.0', name: 'agnes-video-v2.0', provider: 'agnes' }]
  }
}

const saveSettings = async () => {
  try {
    await fetch(`${API}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    })
    loadModels()
  } catch (e) {}
}

const selectModel = (m) => {
  model.value = m
  showModelMenu.value = false
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片文件'
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = {
      file: file,
      preview: e.target.result,
      name: file.name
    }
    settings.image_size = 'original'
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

const removeUploadedImage = () => {
  uploadedImage.value = null
  settings.image_size = '1920x1080'
}

const applyTemplate = (ex) => {
  prompt.value = ex.prompt
  if (ex.params) {
    Object.entries(ex.params).forEach(([k, v]) => {
      if (k in settings) settings[k] = v
    })
  }
}

const downloadFile = (item) => {
  if (item.src && item.src.startsWith('http')) {
    const a = document.createElement('a')
    a.href = item.src
    a.download = item.filename || 'image.png'
    a.target = '_blank'
    a.click()
  } else if (item.filename) {
    const a = document.createElement('a')
    a.href = `/api/v1/media/download?filename=${encodeURIComponent(item.filename)}`
    a.download = item.filename
    a.click()
  }
}

const copyText = (content) => {
  navigator.clipboard.writeText(content).then(() => {
    alert('已复制到剪贴板')
  })
}

const downloadText = (item) => {
  const blob = new Blob([item.content], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${item.title || 'article'}.html`
  a.click()
  URL.revokeObjectURL(url)
}

const loadGallery = async () => {
  try {
    const resp = await fetch(`${API}/media/gallery`)
    const data = await resp.json()
    gallery.value = [
      ...data.images.map(f => ({ type: 'image', src: `/api/v1/media/download?filename=${encodeURIComponent(f.filename)}`, filename: f.filename })),
      ...data.videos.map(f => ({ type: 'video', src: `/api/v1/media/download?filename=${encodeURIComponent(f.filename)}`, filename: f.filename })),
    ]
  } catch (e) {}
}

const generate = async () => {
  if (!prompt.value.trim() || generating.value) return
  generating.value = true
  error.value = ''
  results.value = []
  statusText.value = type.value === 'video' ? '正在提交视频生成任务...' : type.value === 'write' ? '正在生成文章...' : type.value === 'doc' ? '正在生成文档...' : '正在生成图像...'

  try {
    if (type.value === 'write') {
      const resp = await fetch(`${API}/content/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: prompt.value,
          style: settings.write_style,
          length: settings.write_length,
        })
      })
      const data = await resp.json()
      if (data.status === 'ok' || data.content) {
        results.value = [{ type: 'write', content: data.content || data, title: prompt.value }]
      } else {
        error.value = data.message || '生成失败'
      }
      } else if (type.value === 'doc') {
      const resp = await fetch(`${API}/content/generate-doc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: prompt.value,
          format: settings.doc_format,
          style: settings.doc_style,
          pages: settings.doc_pages,
          extra: settings.doc_extra,
        })
      })
      const data = await resp.json()
      if (data.status === 'ok' && data.filename) {
        const ext = data.filename.split('.').pop().toLowerCase()
        let previewHtml = ''
        
        try {
          const previewResp = await fetch(`${API}/media/preview-doc?filename=${encodeURIComponent(data.filename)}`)
          const previewData = await previewResp.json()
          if (previewData.status === 'ok' && previewData.html) {
            previewHtml = previewData.html
          }
        } catch (e) {}
        
        results.value = [{ type: 'doc', src: `/api/v1/media/download?filename=${encodeURIComponent(data.filename)}`, filename: data.filename, format: ext, previewHtml: previewHtml, previewLoading: false }]
      } else {
        error.value = data.message || '文档生成失败'
      }
    } else {
      const endpoint = type.value === 'image' ? '/media/generate-image' : '/media/generate-video'
      let resp
      if (uploadedImage.value && type.value === 'image') {
        const formData = new FormData()
        formData.append('file', uploadedImage.value.file)
        formData.append('prompt', prompt.value)
        formData.append('model', model.value)
        formData.append('size', settings.image_size)
        formData.append('num', settings.image_num)
        if (settings.image_negative_prompt) formData.append('negative_prompt', settings.image_negative_prompt)
        if (settings.image_seed) formData.append('seed', settings.image_seed)
        if (settings.image_guidance_scale) formData.append('guidance_scale', settings.image_guidance_scale)
        resp = await fetch(`${API}/media/edit-image`, {
          method: 'POST',
          body: formData
        })
      } else {
        const body = {
          prompt: prompt.value,
          model: model.value,
        }
        if (type.value === 'image') {
          body.size = settings.image_size
          body.num = settings.image_num
          body.quality = settings.image_quality
          if (settings.image_negative_prompt) body.negative_prompt = settings.image_negative_prompt
          if (settings.image_style) body.style = settings.image_style
          if (settings.image_seed) body.seed = settings.image_seed
          if (settings.image_guidance_scale) body.guidance_scale = settings.image_guidance_scale
        } else {
          body.duration = settings.video_duration
          body.fps = settings.video_fps
          body.resolution = settings.video_resolution
          if (settings.video_negative_prompt) body.negative_prompt = settings.video_negative_prompt
          if (settings.video_seed) body.seed = settings.video_seed
        }
        resp = await fetch(`${API}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        })
      }
      const data = await resp.json()

      if (data.status === 'ok') {
        if (type.value === 'image' && data.images) {
          results.value = data.images.map(img => {
            if (img.url) return { type: 'image', src: img.url, filename: img.url.split('/').pop() }
            if (img.path) return { type: 'image', src: `/api/v1/media/download?filename=${encodeURIComponent(img.filename)}`, filename: img.filename }
            return null
          }).filter(Boolean)
        } else if (type.value === 'video' && data.video) {
          if (data.video.path) {
            results.value = [{ type: 'video', src: `/api/v1/media/download?filename=${encodeURIComponent(data.video.filename)}`, filename: data.video.filename }]
          } else if (data.video.video_url) {
            results.value = [{ type: 'video', src: data.video.video_url, filename: 'video.mp4' }]
          }
        }
        loadGallery()
      } else if (data.status === 'pending' && data.task_id) {
        pollVideoStatus(data.task_id)
        return
      } else {
        error.value = data.message || '生成失败'
      }
    }
  } catch (e) {
    error.value = '请求失败: ' + e.message
  }
  generating.value = false
}

let pollTimer = null
const pollVideoStatus = async (taskId) => {
  let count = 0
  const maxPolls = 120
  const poll = async () => {
    count++
    statusText.value = `视频生成中... (${count * 10}s)`
    try {
      const resp = await fetch(`${API}/media/video-status?task_id=${taskId}`)
      const data = await resp.json()
      if (data.status === 'ok') {
        if (data.video) {
          if (data.video.path) {
            results.value = [{ type: 'video', src: `file:///${data.video.path.replace(/\\/g, '/')}`, filename: data.video.filename }]
          } else if (data.video.video_url) {
            results.value = [{ type: 'video', src: data.video.video_url, filename: 'video.mp4' }]
          }
        }
        loadGallery()
      } else if (data.status === 'pending' && count < maxPolls) {
        pollTimer = setTimeout(poll, 10000)
        return
      } else if (data.status === 'error') {
        error.value = data.message || '视频生成失败'
      } else {
        error.value = '视频生成超时'
      }
    } catch (e) {
      if (count < maxPolls) { pollTimer = setTimeout(poll, 10000); return }
      error.value = '查询失败: ' + e.message
    }
    generating.value = false
  }
  poll()
}

const openFull = (src) => { fullSrc.value = src }
</script>

<style scoped>
.media-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 欢迎区 */
.welcome-section {
  text-align: center;
  margin-bottom: 32px;
}
.welcome-section h1 {
  font-size: 28px;
  font-weight: 400;
  color: #333;
}
.welcome-highlight {
  color: #409eff;
  font-weight: 500;
}

/* 输入卡片 */
.input-card {
  width: 100%;
  max-width: 780px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  overflow: hidden;
}
.input-card textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: 20px 24px 8px;
  font-size: 15px;
  line-height: 1.6;
  font-family: inherit;
  color: #333;
  background: transparent;
}
.input-card textarea::placeholder { color: #bbb; }
.uploaded-preview {
  padding: 8px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.uploaded-preview img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}
.remove-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: #f56c6c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}
.remove-btn:hover { background: #f78989; }

/* 工具栏 */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 4px;
}
.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  transition: background 0.15s;
}
.toolbar-btn:hover { background: #f5f5f5; }

.type-switch {
  display: flex;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 2px;
  margin-left: 4px;
}
.type-switch button {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.type-switch button.active {
  background: #fff;
  color: #333;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  font-weight: 500;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  margin-left: 8px;
  transition: background 0.15s;
  position: relative;
}
.model-selector:hover { background: #f5f5f5; }
.model-icon { font-size: 16px; }

.model-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 4px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 4px;
  min-width: 200px;
  z-index: 100;
}
.model-option {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: background 0.1s;
}
.model-option:hover { background: #f0f0f0; }
.model-option.active { background: #ecf5ff; color: #409eff; }

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #e0e0e0;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.send-btn:not(:disabled) {
  background: #409eff;
}
.send-btn:not(:disabled):hover {
  background: #337ecc;
  transform: scale(1.05);
}
.send-btn:disabled { cursor: not-allowed; }

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 参数设置 */
.settings-panel {
  padding: 12px 24px 16px;
  border-top: 1px solid #f0f0f0;
}
.settings-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.setting-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.setting-item label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}
.setting-item select {
  padding: 5px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  background: #fff;
  outline: none;
  cursor: pointer;
}
.setting-item select:focus { border-color: #409eff; }
.setting-input {
  padding: 5px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  background: #fff;
  outline: none;
  width: 80px;
}
.setting-input:focus { border-color: #409eff; }
.setting-input-wide {
  flex: 1;
  padding: 5px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  background: #fff;
  outline: none;
  min-width: 200px;
}
.setting-input-wide:focus { border-color: #409eff; }
.setting-item-full { flex: 1; }
.setting-save {
  padding: 5px 14px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  margin-left: auto;
}
.setting-save:hover { background: #337ecc; }

/* 进度 */
.progress-bar {
  padding: 0 24px 16px;
}
.progress-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #409eff;
}
.progress-text .btn-spinner {
  border-color: rgba(64,158,255,0.3);
  border-top-color: #409eff;
}

/* 结果 */
.results-section {
  width: 100%;
  max-width: 780px;
  margin-top: 24px;
}
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.write-results {
  width: 100%;
}
.write-result-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
}
.write-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}
.write-result-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}
.write-result-actions {
  display: flex;
  gap: 8px;
}
.write-result-content {
  padding: 20px;
  line-height: 1.8;
  font-size: 14px;
  color: #303133;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
}
.doc-results {
  width: 100%;
}
.doc-result-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
  margin-bottom: 16px;
}
.doc-result-preview {
  width: 100%;
  height: 500px;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
  background: #fafafa;
}
.doc-preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
.doc-preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #999;
}
.doc-result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}
.doc-result-info {
  flex: 1;
  min-width: 0;
}
.doc-result-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-result-format {
  font-size: 13px;
  color: #999;
}
.doc-result-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}
.result-item {
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.result-item:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.result-media {
  cursor: pointer;
  aspect-ratio: 1;
  overflow: hidden;
}
.result-media img, .result-media video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.result-actions {
  padding: 8px 12px;
  display: flex;
  justify-content: flex-end;
}
.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  background: #fff;
  border-radius: 6px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
}
.action-btn:hover {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
}
.gallery-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  gap: 4px;
}
.action-btn-sm {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(0,0,0,0.5);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  transition: background 0.15s;
  opacity: 0;
}
.gallery-item:hover .action-btn-sm { opacity: 1; }
.action-btn-sm:hover { background: rgba(0,0,0,0.7); }

/* 错误 */
.error-toast {
  margin-top: 16px;
  padding: 10px 20px;
  background: #fef0f0;
  color: #f44336;
  border-radius: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 示例模板 */
.examples-section {
  width: 100%;
  max-width: 780px;
  margin-top: 32px;
}
.examples-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.example-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #f0f0f0;
}
.example-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64,158,255,0.1);
}
.example-content {
  display: flex;
  gap: 12px;
  align-items: center;
}
.example-text { flex: 1; min-width: 0; }
.example-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.example-desc {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.example-thumb {
  width: 56px;
  height: 56px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

/* 历史记录 */
.gallery-section {
  width: 100%;
  max-width: 780px;
  margin-top: 32px;
}
.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 12px;
}
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}
.gallery-item {
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 1;
  transition: transform 0.15s;
  position: relative;
}
.gallery-item:hover { transform: scale(1.03); }
.gallery-item .result-media { aspect-ratio: 1; }
.gallery-item img, .gallery-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 全屏 */
.fullscreen {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  cursor: pointer;
}
.fullscreen img { max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; }

@media (max-width: 640px) {
  .examples-grid { grid-template-columns: 1fr; }
  .type-switch button span { display: none; }
}
</style>
