# AI Framework 前端

现代化卡片式UI，基于 Vue 3 + Element Plus + Tailwind CSS

## 技术栈

| 技术 | 用途 |
|------|------|
| Vue 3 | 前端框架 |
| Element Plus | UI组件库 |
| Tailwind CSS | 样式框架 |
| Vite | 构建工具 |
| Vue Router | 路由管理 |
| Axios | HTTP请求 |

## 快速开始

```bash
# 安装依赖
cd frontend-vue
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 功能模块

### 1. 智能对话
- 多模型切换（DeepSeek/MiMo/Qwen/GLM）
- 流式响应
- 对话历史

### 2. AI写作
- 多种写作风格
- 可调节文章长度
- 一键复制

### 3. 智能推荐
- 卡片式展示
- 匹配度评分
- 个性化推荐

### 4. OCR识别
- 拖拽上传
- 图片预览
- 置信度显示

## 界面预览

```
┌─────────────────────────────────────────────────────┐
│  ┌───┐  ┌─────────────────────────────────────────┐ │
│  │AI │  │  智能对话                    模型: [▼]  │ │
│  │   │  ├─────────────────────────────────────────┤ │
│  │ 💬│  │                                         │ │
│  │ ✍️│  │  👤 你好                                 │ │
│  │ 📊│  │                                         │ │
│  │ 📷│  │        🤖 你好！有什么帮助？    │ │
│  │   │  │                                         │ │
│  │ ⚙️│  ├─────────────────────────────────────────┤ │
│  └───┘  │  [请输入你的问题...              ] [发送]│ │
│         └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
frontend-vue/
├── src/
│   ├── api/
│   │   └── index.js          # API接口
│   ├── router/
│   │   └── index.js          # 路由配置
│   ├── views/
│   │   ├── ChatView.vue      # 智能对话页面
│   │   ├── ContentView.vue   # 内容生成页面
│   │   ├── RecommendView.vue # 推荐系统页面
│   │   └── OCRView.vue       # OCR识别页面
│   ├── App.vue               # 主布局
│   ├── main.js               # 入口文件
│   └── style.css             # 全局样式
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 配置说明

### API代理

在 `vite.config.js` 中配置API代理：

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### 主题定制

在 `tailwind.config.js` 中修改主题颜色：

```js
theme: {
  extend: {
    colors: {
      primary: '#6366f1',
      secondary: '#8b5cf6',
    }
  }
}
```

## 部署

### 开发环境
```bash
npm run dev
# 访问 http://localhost:3000
```

### 生产环境
```bash
npm run build
# 将 dist/ 目录部署到 Nginx
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```
