<template>
  <div class="workflow-page">
    <!-- 工作流列表视图 -->
    <div v-if="!editing">
      <div class="page-card">
        <div class="card-header">
          <h3>AI 工作流</h3>
          <div>
            <el-button size="small" @click="showImportDialog">导入</el-button>
            <el-button type="primary" size="small" @click="createNew">新建工作流</el-button>
          </div>
        </div>
        <div class="card-body">
          <el-table :data="workflows" stripe v-loading="loadingList">
            <el-table-column prop="name" label="工作流名称" />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column label="节点数" width="80" align="center">
              <template #default="{ row }">{{ (row.nodes || []).length }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '启用' : '草稿' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-button class="btn-edit" size="small" @click="editWorkflow(row)">
                    <span class="btn-icon">✏️</span> 编辑
                  </el-button>
                  <el-button class="btn-run" size="small" @click="runWorkflowDialog(row)">
                    <span class="btn-icon">▶</span> 执行
                  </el-button>
                  <el-dropdown trigger="click" @command="(cmd) => handleMore(cmd, row)">
                    <el-button class="btn-more" size="small">
                      更多 <span style="margin-left:2px">▾</span>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="log"><span class="btn-icon">📋</span> 日志</el-dropdown-item>
                        <el-dropdown-item command="version"><span class="btn-icon">🕐</span> 版本</el-dropdown-item>
                        <el-dropdown-item command="export"><span class="btn-icon">📤</span> 导出</el-dropdown-item>
                        <el-dropdown-item command="delete" divided><span class="btn-icon">🗑️</span> 删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 工作流编辑器视图 -->
    <div v-else class="editor-layout">
      <div class="editor-topbar">
        <el-button size="small" @click="backToList">← 返回</el-button>
        <el-input v-model="currentWf.name" style="width:200px;margin:0 12px" size="small" />
        <el-tag :type="currentWf.status === 'active' ? 'success' : 'info'" size="small" style="margin-right:8px">
          {{ currentWf.status === 'active' ? '启用' : '草稿' }}
        </el-tag>
        <el-button size="small" @click="toggleStatus">{{ currentWf.status === 'active' ? '停用' : '启用' }}</el-button>
        <div style="flex:1"></div>
        <el-button size="small" @click="showSaveVersionDialog">保存版本</el-button>
        <el-button size="small" @click="doExport(currentWf)">导出</el-button>
        <el-button type="primary" size="small" @click="saveWf" :loading="saving">保存</el-button>
        <el-button type="success" size="small" @click="runWf">执行</el-button>
      </div>
      <div class="editor-body">
        <!-- 左侧节点面板 -->
        <div class="node-panel">
          <div class="panel-title">节点类型</div>
          <div v-for="nt in nodeTypes" :key="nt.type" class="node-item" draggable="true" @dragstart="onDragStart($event, nt.type)">
            <span class="node-icon" :style="{ background: nt.color }">{{ nt.icon }}</span>
            <span>{{ nt.label }}</span>
          </div>
        </div>
        <!-- 画布 -->
        <div class="canvas-wrap" ref="canvasRef" @drop="onDrop" @dragover.prevent>
          <VueFlow v-model:nodes="nodes" v-model:edges="edges" fit-view-on-init :default-edge-options="{ type: 'smoothstep', animated: true }" :edges-updatable="true" :edges-focusable="true">
            <Background />
            <MiniMap />
            <Controls />
            <template #node-start="nodeProps">
              <div class="custom-node start-node"><Handle type="source" :position="Position.Right" /><span class="cn-icon">📥</span><span class="cn-label">{{ nodeProps.data?.label || '输入' }}</span></div>
            </template>
            <template #node-llm="nodeProps">
              <div class="custom-node llm-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🧠</span><span class="cn-label">{{ nodeProps.data?.label || 'LLM' }}</span></div>
            </template>
            <template #node-tool="nodeProps">
              <div class="custom-node tool-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔧</span><span class="cn-label">{{ nodeProps.data?.label || '工具' }}</span></div>
            </template>
            <template #node-condition="nodeProps">
              <div class="custom-node condition-node"><Handle type="target" :position="Position.Left" /><Handle id="true" type="source" :position="Position.Right" /><Handle id="false" type="source" :position="Position.Bottom" /><span class="cn-icon">🔀</span><span class="cn-label">{{ nodeProps.data?.label || '条件' }}</span></div>
            </template>
            <template #node-transform="nodeProps">
              <div class="custom-node transform-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔄</span><span class="cn-label">{{ nodeProps.data?.label || '转换' }}</span></div>
            </template>
            <template #node-output="nodeProps">
              <div class="custom-node output-node"><Handle type="target" :position="Position.Left" /><span class="cn-icon">📤</span><span class="cn-label">{{ nodeProps.data?.label || '输出' }}</span></div>
            </template>
            <template #node-delay="nodeProps">
              <div class="custom-node delay-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">⏱️</span><span class="cn-label">{{ nodeProps.data?.label || '延时' }}</span></div>
            </template>
            <template #node-loop="nodeProps">
              <div class="custom-node loop-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><Handle id="each" type="source" :position="Position.Bottom" /><span class="cn-icon">🔁</span><span class="cn-label">{{ nodeProps.data?.label || '循环' }}</span></div>
            </template>
            <template #node-parallel="nodeProps">
              <div class="custom-node parallel-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">⚡</span><span class="cn-label">{{ nodeProps.data?.label || '并行' }}</span></div>
            </template>
            <template #node-database="nodeProps">
              <div class="custom-node database-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🗄️</span><span class="cn-label">{{ nodeProps.data?.label || '数据库' }}</span></div>
            </template>
            <template #node-file_operation="nodeProps">
              <div class="custom-node file-operation-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📁</span><span class="cn-label">{{ nodeProps.data?.label || '文件操作' }}</span></div>
            </template>
            <template #node-webhook="nodeProps">
              <div class="custom-node webhook-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🌐</span><span class="cn-label">{{ nodeProps.data?.label || 'Webhook' }}</span></div>
            </template>
            <template #node-code_exec="nodeProps">
              <div class="custom-node code-exec-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">💻</span><span class="cn-label">{{ nodeProps.data?.label || '代码执行' }}</span></div>
            </template>
            <template #node-image_gen="nodeProps">
              <div class="custom-node image-gen-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🎨</span><span class="cn-label">{{ nodeProps.data?.label || '图像生成' }}</span></div>
            </template>
            <template #node-error_handler="nodeProps">
              <div class="custom-node error-handler-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🛡️</span><span class="cn-label">{{ nodeProps.data?.label || '错误处理' }}</span></div>
            </template>
            <template #node-text_split="nodeProps">
              <div class="custom-node text-split-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">✂️</span><span class="cn-label">{{ nodeProps.data?.label || '文本分割' }}</span></div>
            </template>
            <template #node-text_translate="nodeProps">
              <div class="custom-node text-translate-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🌍</span><span class="cn-label">{{ nodeProps.data?.label || '文本翻译' }}</span></div>
            </template>
            <template #node-text_summarize="nodeProps">
              <div class="custom-node text-summarize-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📝</span><span class="cn-label">{{ nodeProps.data?.label || '文本摘要' }}</span></div>
            </template>
            <template #node-json_build="nodeProps">
              <div class="custom-node json-build-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📦</span><span class="cn-label">{{ nodeProps.data?.label || 'JSON构建' }}</span></div>
            </template>
            <template #node-data_filter="nodeProps">
              <div class="custom-node data-filter-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔍</span><span class="cn-label">{{ nodeProps.data?.label || '数据过滤' }}</span></div>
            </template>
            <template #node-data_sort="nodeProps">
              <div class="custom-node data-sort-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔃</span><span class="cn-label">{{ nodeProps.data?.label || '数据排序' }}</span></div>
            </template>
            <template #node-switch="nodeProps">
              <div class="custom-node switch-node"><Handle type="target" :position="Position.Left" /><Handle id="default" type="source" :position="Position.Right" /><Handle id="case1" type="source" :position="Position.Bottom" /><span class="cn-icon">🎯</span><span class="cn-label">{{ nodeProps.data?.label || '多分支' }}</span></div>
            </template>
            <template #node-sub_workflow="nodeProps">
              <div class="custom-node sub-workflow-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔗</span><span class="cn-label">{{ nodeProps.data?.label || '子工作流' }}</span></div>
            </template>
            <template #node-retry="nodeProps">
              <div class="custom-node retry-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔄</span><span class="cn-label">{{ nodeProps.data?.label || '重试' }}</span></div>
            </template>
            <template #node-notify="nodeProps">
              <div class="custom-node notify-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📢</span><span class="cn-label">{{ nodeProps.data?.label || '通知推送' }}</span></div>
            </template>
            <template #node-math_calc="nodeProps">
              <div class="custom-node math-calc-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔢</span><span class="cn-label">{{ nodeProps.data?.label || '数学计算' }}</span></div>
            </template>
            <template #node-datetime="nodeProps">
              <div class="custom-node datetime-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🕐</span><span class="cn-label">{{ nodeProps.data?.label || '日期时间' }}</span></div>
            </template>
            <template #node-type_convert="nodeProps">
              <div class="custom-node type-convert-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔄</span><span class="cn-label">{{ nodeProps.data?.label || '类型转换' }}</span></div>
            </template>
            <template #node-csv_parse="nodeProps">
              <div class="custom-node csv-parse-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📊</span><span class="cn-label">{{ nodeProps.data?.label || 'CSV解析' }}</span></div>
            </template>
            <template #node-excel_read="nodeProps">
              <div class="custom-node excel-read-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📗</span><span class="cn-label">{{ nodeProps.data?.label || 'Excel读取' }}</span></div>
            </template>
            <template #node-regex_replace="nodeProps">
              <div class="custom-node regex-replace-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔤</span><span class="cn-label">{{ nodeProps.data?.label || '正则替换' }}</span></div>
            </template>
            <template #node-hash_encode="nodeProps">
              <div class="custom-node hash-encode-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">#️⃣</span><span class="cn-label">{{ nodeProps.data?.label || '哈希编码' }}</span></div>
            </template>
            <template #node-uuid_generate="nodeProps">
              <div class="custom-node uuid-generate-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🆔</span><span class="cn-label">{{ nodeProps.data?.label || 'UUID生成' }}</span></div>
            </template>
            <template #node-text_embedding="nodeProps">
              <div class="custom-node text-embedding-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🧬</span><span class="cn-label">{{ nodeProps.data?.label || '文本嵌入' }}</span></div>
            </template>
            <template #node-speech_to_text="nodeProps">
              <div class="custom-node speech-to-text-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🎤</span><span class="cn-label">{{ nodeProps.data?.label || '语音转文字' }}</span></div>
            </template>
            <template #node-text_to_speech="nodeProps">
              <div class="custom-node text-to-speech-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔊</span><span class="cn-label">{{ nodeProps.data?.label || '文字转语音' }}</span></div>
            </template>
            <template #node-image_process="nodeProps">
              <div class="custom-node image-process-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🖼️</span><span class="cn-label">{{ nodeProps.data?.label || '图片处理' }}</span></div>
            </template>
            <template #node-markdown_html="nodeProps">
              <div class="custom-node markdown-html-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📄</span><span class="cn-label">{{ nodeProps.data?.label || 'Markdown→HTML' }}</span></div>
            </template>
            <template #node-websocket_connect="nodeProps">
              <div class="custom-node websocket-connect-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔌</span><span class="cn-label">{{ nodeProps.data?.label || 'WebSocket' }}</span></div>
            </template>
            <template #node-http_stream="nodeProps">
              <div class="custom-node http-stream-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📡</span><span class="cn-label">{{ nodeProps.data?.label || 'HTTP流式' }}</span></div>
            </template>
            <template #node-network_ping="nodeProps">
              <div class="custom-node network-ping-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🏓</span><span class="cn-label">{{ nodeProps.data?.label || '网络Ping' }}</span></div>
            </template>
            <template #node-url_shorten="nodeProps">
              <div class="custom-node url-shorten-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔗</span><span class="cn-label">{{ nodeProps.data?.label || 'URL缩短' }}</span></div>
            </template>
            <template #node-qrcode_gen="nodeProps">
              <div class="custom-node qrcode-gen-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📱</span><span class="cn-label">{{ nodeProps.data?.label || '二维码生成' }}</span></div>
            </template>
            <template #node-qrcode_scan="nodeProps">
              <div class="custom-node qrcode-scan-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📷</span><span class="cn-label">{{ nodeProps.data?.label || '二维码识别' }}</span></div>
            </template>
            <template #node-pdf_generate="nodeProps">
              <div class="custom-node pdf-generate-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📋</span><span class="cn-label">{{ nodeProps.data?.label || 'PDF生成' }}</span></div>
            </template>
            <template #node-json_diff="nodeProps">
              <div class="custom-node json-diff-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔍</span><span class="cn-label">{{ nodeProps.data?.label || 'JSON对比' }}</span></div>
            </template>
          </VueFlow>
        </div>
        <!-- 右侧配置面板 -->
        <div class="config-panel" v-if="selectedNode">
          <div class="panel-title">节点配置</div>
          <div class="var-hint" v-if="upstreamVars.length">
            <div class="var-hint-title">可用变量</div>
            <div class="var-hint-tip">在输入框中用 <code v-html="'{{变量名}}'"></code> 引用</div>
            <div v-for="v in upstreamVars" :key="v.name" class="var-hint-item">
              <code v-html="'{{' + v.name + '}}'"></code>
              <span class="var-hint-desc">{{ v.desc }}</span>
            </div>
          </div>
          <el-form label-position="top" size="small">
            <el-form-item label="标签">
              <el-input v-model="selectedNode.data.label" />
            </el-form-item>
            <!-- LLM 配置 -->
            <template v-if="selectedNode.type === 'llm'">
              <el-form-item label="Provider">
                <el-select v-model="selectedNode.data.config.provider" style="width:100%">
                  <el-option label="agnes" value="agnes" />
                  <el-option label="deepseek" value="deepseek" />
                  <el-option label="openai" value="openai" />
                </el-select>
              </el-form-item>
              <el-form-item label="Prompt 模板">
                <el-input v-model="selectedNode.data.config.prompt" type="textarea" :rows="4" placeholder="用 {{变量名}} 引用上游输出" />
              </el-form-item>
            </template>
            <!-- Tool 配置 -->
            <template v-if="selectedNode.type === 'tool'">
              <el-form-item label="工具">
                <el-select v-model="selectedNode.data.config.tool_name" style="width:100%" filterable>
                  <el-option label="知识库搜索" value="knowledge_search" />
                  <el-option label="OCR 识别" value="ocr" />
                  <el-option label="HTTP 请求" value="http" />
                  <el-option label="打开应用" value="open_app" />
                  <el-option label="执行命令" value="run_command" />
                  <el-option label="发送邮件" value="send_email" />
                  <el-option label="读取文件" value="file_read" />
                  <el-option label="写入文件" value="file_write" />
                  <el-option label="文本截取" value="text_extract" />
                  <el-option label="正则匹配" value="regex" />
                  <el-option label="JSON 解析" value="json_parse" />
                  <el-option label="PDF 提取" value="pdf_extract" />
                  <el-option label="剪贴板" value="clipboard" />
                  <el-option label="截图" value="screenshot" />
                </el-select>
              </el-form-item>
              <template v-if="selectedNode.data.config.tool_name === 'http'">
                <el-form-item label="请求方法">
                  <el-select v-model="selectedNode.data.config.method" style="width:100%">
                    <el-option label="GET" value="GET" />
                    <el-option label="POST" value="POST" />
                    <el-option label="PUT" value="PUT" />
                    <el-option label="DELETE" value="DELETE" />
                    <el-option label="PATCH" value="PATCH" />
                  </el-select>
                </el-form-item>
                <el-form-item label="URL">
                  <el-input v-model="selectedNode.data.config.input_template" placeholder="https://api.example.com/data" />
                </el-form-item>
                <el-form-item label="请求头 (JSON 或 Key: Value)">
                  <el-input v-model="selectedNode.data.config.headers" type="textarea" :rows="2" placeholder='{"Content-Type": "application/json"}' />
                </el-form-item>
                <el-form-item label="请求体 (POST/PUT)">
                  <el-input v-model="selectedNode.data.config.body" type="textarea" :rows="3" placeholder='{"key": "value"}' />
                </el-form-item>
                <el-form-item label="超时 (秒)">
                  <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="120" style="width:100%" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'regex'">
                <el-form-item label="正则表达式">
                  <el-input v-model="selectedNode.data.config.pattern" placeholder="(\d+)" />
                </el-form-item>
                <el-form-item label="输入文本">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'json_parse'">
                <el-form-item label="JSON 路径 (可选)">
                  <el-input v-model="selectedNode.data.config.path" placeholder="data.items.0.name" />
                </el-form-item>
                <el-form-item label="JSON 输入">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'text_extract'">
                <el-form-item label="最大长度">
                  <el-input-number v-model="selectedNode.data.config.max_length" :min="100" :max="50000" style="width:100%" />
                </el-form-item>
                <el-form-item label="输入文本">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'open_app'">
                <el-form-item label="应用名称">
                  <el-input v-model="selectedNode.data.config.input_template" placeholder="notepad / 记事本 / chrome / vscode" />
                </el-form-item>
                <el-form-item>
                  <div style="font-size:12px;color:#909399;line-height:1.8">
                    支持: notepad/记事本, calculator/计算器, paint/画图, chrome, edge, firefox, vscode, word, excel, terminal/终端, 或任意 exe 路径
                  </div>
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'run_command'">
                <el-form-item label="命令">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="ipconfig / dir / python --version" />
                </el-form-item>
                <el-form-item label="超时 (秒)">
                  <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="120" style="width:100%" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'file_read'">
                <el-form-item label="文件路径">
                  <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\test.txt 或 {{变量名}}" />
                </el-form-item>
                <el-form-item label="编码">
                  <el-select v-model="selectedNode.data.config.encoding" style="width:100%">
                    <el-option label="UTF-8" value="utf-8" />
                    <el-option label="GBK" value="gbk" />
                    <el-option label="GB2312" value="gb2312" />
                  </el-select>
                </el-form-item>
                <el-form-item label="最大读取字数">
                  <el-input-number v-model="selectedNode.data.config.max_size" :min="100" :max="100000" style="width:100%" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'send_email'">
                <el-form-item label="SMTP 服务器">
                  <el-input v-model="selectedNode.data.config.smtp_host" placeholder="smtp.qq.com" />
                </el-form-item>
                <el-form-item label="SMTP 端口">
                  <el-input-number v-model="selectedNode.data.config.smtp_port" :min="1" :max="65535" style="width:100%" />
                </el-form-item>
                <el-form-item label="发件人邮箱">
                  <el-input v-model="selectedNode.data.config.smtp_user" placeholder="your@qq.com" />
                </el-form-item>
                <el-form-item label="授权码/密码">
                  <el-input v-model="selectedNode.data.config.smtp_pass" type="password" show-password placeholder="SMTP 授权码" />
                </el-form-item>
                <el-form-item label="使用 SSL">
                  <el-switch v-model="selectedNode.data.config.use_ssl" />
                </el-form-item>
                <el-form-item label="收件人邮箱">
                  <el-input v-model="selectedNode.data.config.to_addr" placeholder="recipient@example.com" />
                </el-form-item>
                <el-form-item label="邮件主题">
                  <el-input v-model="selectedNode.data.config.subject" placeholder="测试邮件" />
                </el-form-item>
                <el-form-item label="邮件正文 (用 {{变量名}} 引用上游)">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="4" placeholder="{{llm_1}}" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'file_write'">
                <el-form-item label="写入路径">
                  <el-input v-model="selectedNode.data.config.file_path" placeholder="C:\Users\test.txt 或 {{变量名}}" />
                </el-form-item>
                <el-form-item label="写入模式">
                  <el-select v-model="selectedNode.data.config.write_mode" style="width:100%">
                    <el-option label="覆盖写入" value="overwrite" />
                    <el-option label="追加写入" value="append" />
                  </el-select>
                </el-form-item>
                <el-form-item label="写入内容">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="4" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'knowledge_search'">
                <el-form-item label="搜索关键词">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
                <el-form-item label="返回条数">
                  <el-input-number v-model="selectedNode.data.config.top_k" :min="1" :max="20" style="width:100%" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'ocr'">
                <el-form-item label="图像输入">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="文件路径或用 {{变量名}} 引用 base64 数据" />
                </el-form-item>
                <el-form-item label="来源">
                  <el-select v-model="selectedNode.data.config.ocr_source" style="width:100%">
                    <el-option label="文件路径" value="path" />
                    <el-option label="Base64 数据" value="base64" />
                    <el-option label="上游变量" value="context" />
                  </el-select>
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'pdf_extract'">
                <el-form-item label="PDF 路径">
                  <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\doc.pdf 或 {{变量名}}" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'clipboard'">
                <el-form-item label="操作">
                  <el-select v-model="selectedNode.data.config.action" style="width:100%">
                    <el-option label="读取剪贴板" value="paste" />
                    <el-option label="写入剪贴板" value="copy" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="selectedNode.data.config.action === 'copy'" label="写入内容">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
              <template v-else-if="selectedNode.data.config.tool_name === 'screenshot'">
                <el-form-item label="保存路径">
                  <el-input v-model="selectedNode.data.config.save_path" placeholder="留空自动生成" />
                </el-form-item>
              </template>
              <template v-else>
                <el-form-item label="输入模板">
                  <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
                </el-form-item>
              </template>
            </template>
            <!-- Condition 配置 -->
            <template v-if="selectedNode.type === 'condition'">
              <el-form-item label="条件表达式">
                <el-input v-model="selectedNode.data.config.condition" type="textarea" :rows="2" placeholder='如: {{result}} == "是"' />
              </el-form-item>
            </template>
            <!-- Transform 配置 -->
            <template v-if="selectedNode.type === 'transform'">
              <el-form-item label="输出模板">
                <el-input v-model="selectedNode.data.config.template" type="textarea" :rows="3" placeholder="用 {{变量名}} 引用上游输出" />
              </el-form-item>
            </template>
            <!-- Delay 配置 -->
            <template v-if="selectedNode.type === 'delay'">
              <el-form-item label="等待秒数">
                <el-input-number v-model="selectedNode.data.config.seconds" :min="1" :max="60" style="width:100%" />
              </el-form-item>
            </template>
            <!-- Loop 配置 -->
            <template v-if="selectedNode.type === 'loop'">
              <el-form-item label="遍历变量名">
                <el-input v-model="selectedNode.data.config.list_var" placeholder="input / items / results" />
              </el-form-item>
              <el-form-item>
                <div style="font-size:12px;color:#909399">从上游结果中取列表逐项遍历</div>
              </el-form-item>
            </template>
            <!-- Parallel 配置 -->
            <template v-if="selectedNode.type === 'parallel'">
              <el-form-item>
                <div style="font-size:12px;color:#909399">自动并行执行所有入边连接的上游节点</div>
              </el-form-item>
            </template>
            <!-- Database 配置 -->
            <template v-if="selectedNode.type === 'database'">
              <el-form-item label="数据库类型">
                <el-select v-model="selectedNode.data.config.db_type" style="width:100%">
                  <el-option label="MongoDB" value="mongodb" />
                  <el-option label="MySQL" value="mysql" />
                  <el-option label="PostgreSQL" value="postgresql" />
                </el-select>
              </el-form-item>
              <el-form-item label="连接字符串">
                <el-input v-model="selectedNode.data.config.connection_string" placeholder="mongodb://... 或 postgresql://..." />
              </el-form-item>
              <template v-if="selectedNode.data.config.db_type === 'mongodb'">
                <el-form-item label="数据库名">
                  <el-input v-model="selectedNode.data.config.db_name" placeholder="mydb" />
                </el-form-item>
                <el-form-item label="集合名">
                  <el-input v-model="selectedNode.data.config.collection" placeholder="mycollection" />
                </el-form-item>
              </template>
              <el-form-item label="查询语句">
                <el-input v-model="selectedNode.data.config.query" type="textarea" :rows="3" placeholder='MongoDB: {"status": "active"}&#10;SQL: SELECT * FROM users' />
              </el-form-item>
            </template>
            <!-- File Operation 配置 -->
            <template v-if="selectedNode.type === 'file_operation'">
              <el-form-item label="操作类型">
                <el-select v-model="selectedNode.data.config.operation" style="width:100%">
                  <el-option label="读取文件" value="read" />
                  <el-option label="写入文件" value="write" />
                  <el-option label="复制文件" value="copy" />
                  <el-option label="移动文件" value="move" />
                  <el-option label="删除文件" value="delete" />
                  <el-option label="列出目录" value="list" />
                </el-select>
              </el-form-item>
              <el-form-item label="文件路径">
                <el-input v-model="selectedNode.data.config.path" placeholder="C:\test.txt 或 {{变量名}}" />
              </el-form-item>
              <template v-if="selectedNode.data.config.operation === 'write'">
                <el-form-item label="写入内容">
                  <el-input v-model="selectedNode.data.config.content" type="textarea" :rows="4" placeholder="{{llm_1}}" />
                </el-form-item>
              </template>
              <template v-if="['copy','move'].includes(selectedNode.data.config.operation)">
                <el-form-item label="目标路径">
                  <el-input v-model="selectedNode.data.config.dest" placeholder="D:\backup\test.txt" />
                </el-form-item>
              </template>
              <template v-if="selectedNode.data.config.operation === 'read'">
                <el-form-item label="编码">
                  <el-select v-model="selectedNode.data.config.encoding" style="width:100%">
                    <el-option label="UTF-8" value="utf-8" />
                    <el-option label="GBK" value="gbk" />
                  </el-select>
                </el-form-item>
              </template>
            </template>
            <!-- Webhook 配置 -->
            <template v-if="selectedNode.type === 'webhook'">
              <el-form-item label="请求方法">
                <el-select v-model="selectedNode.data.config.method" style="width:100%">
                  <el-option label="GET" value="GET" />
                  <el-option label="POST" value="POST" />
                  <el-option label="PUT" value="PUT" />
                  <el-option label="DELETE" value="DELETE" />
                  <el-option label="PATCH" value="PATCH" />
                </el-select>
              </el-form-item>
              <el-form-item label="URL">
                <el-input v-model="selectedNode.data.config.url" placeholder="https://api.example.com/data" />
              </el-form-item>
              <el-form-item label="请求头 (JSON)">
                <el-input v-model="selectedNode.data.config.headers" type="textarea" :rows="2" placeholder='{"Authorization": "Bearer xxx"}' />
              </el-form-item>
              <el-form-item label="请求体">
                <el-input v-model="selectedNode.data.config.body" type="textarea" :rows="3" placeholder='{"key": "value"}' />
              </el-form-item>
              <el-form-item label="超时 (秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="120" style="width:100%" />
              </el-form-item>
            </template>
            <!-- Code Exec 配置 -->
            <template v-if="selectedNode.type === 'code_exec'">
              <el-form-item label="语言">
                <el-select v-model="selectedNode.data.config.language" style="width:100%">
                  <el-option label="Python" value="python" />
                  <el-option label="JavaScript" value="javascript" />
                </el-select>
              </el-form-item>
              <el-form-item label="代码">
                <el-input v-model="selectedNode.data.config.code" type="textarea" :rows="8" placeholder="print('hello')" style="font-family:monospace" />
              </el-form-item>
              <el-form-item label="超时 (秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="60" style="width:100%" />
              </el-form-item>
            </template>
            <!-- Image Gen 配置 -->
            <template v-if="selectedNode.type === 'image_gen'">
              <el-form-item label="Prompt">
                <el-input v-model="selectedNode.data.config.prompt" type="textarea" :rows="3" placeholder="一只可爱的猫咪在太空漫步" />
              </el-form-item>
              <el-form-item label="图片尺寸">
                <el-select v-model="selectedNode.data.config.size" style="width:100%">
                  <el-option label="512x512" value="512x512" />
                  <el-option label="1024x1024" value="1024x1024" />
                  <el-option label="1920x1080" value="1920x1080" />
                </el-select>
              </el-form-item>
              <el-form-item label="模型 (可选)">
                <el-input v-model="selectedNode.data.config.model" placeholder="留空使用默认模型" />
              </el-form-item>
            </template>
            <!-- Error Handler 配置 -->
            <template v-if="selectedNode.type === 'error_handler'">
              <el-form-item label="备用输出值">
                <el-input v-model="selectedNode.data.config.fallback_output" type="textarea" :rows="3" placeholder="上游出错时的默认返回内容" />
              </el-form-item>
              <el-form-item>
                <div style="font-size:12px;color:#909399">当上游节点执行失败时，此节点会捕获错误并返回备用值</div>
              </el-form-item>
            </template>
            <!-- Text Split 配置 -->
            <template v-if="selectedNode.type === 'text_split'">
              <el-form-item label="分隔符">
                <el-input v-model="selectedNode.data.config.delimiter" placeholder="\n 或 , 或 ;" />
              </el-form-item>
              <el-form-item label="输入文本">
                <el-input v-model="selectedNode.data.config.text" type="textarea" :rows="3" placeholder="{{input}}" />
              </el-form-item>
            </template>
            <!-- Text Translate 配置 -->
            <template v-if="selectedNode.type === 'text_translate'">
              <el-form-item label="目标语言">
                <el-select v-model="selectedNode.data.config.target_lang" style="width:100%">
                  <el-option label="英语" value="英语" />
                  <el-option label="中文" value="中文" />
                  <el-option label="日语" value="日语" />
                  <el-option label="韩语" value="韩语" />
                  <el-option label="法语" value="法语" />
                  <el-option label="德语" value="德语" />
                  <el-option label="西班牙语" value="西班牙语" />
                </el-select>
              </el-form-item>
              <el-form-item label="输入文本">
                <el-input v-model="selectedNode.data.config.text" type="textarea" :rows="3" placeholder="{{input}}" />
              </el-form-item>
            </template>
            <!-- Text Summarize 配置 -->
            <template v-if="selectedNode.type === 'text_summarize'">
              <el-form-item label="最大字数">
                <el-input-number v-model="selectedNode.data.config.max_length" :min="50" :max="2000" style="width:100%" />
              </el-form-item>
              <el-form-item label="输入文本">
                <el-input v-model="selectedNode.data.config.text" type="textarea" :rows="3" placeholder="{{input}}" />
              </el-form-item>
            </template>
            <!-- JSON Build 配置 -->
            <template v-if="selectedNode.type === 'json_build'">
              <el-form-item label="键值对 (每行 key=value)">
                <el-input v-model="selectedNode.data.config.key_value_pairs" type="textarea" :rows="5" placeholder='name={{input}}\ntype=report\ndate=2024-01-01' />
              </el-form-item>
            </template>
            <!-- Data Filter 配置 -->
            <template v-if="selectedNode.type === 'data_filter'">
              <el-form-item label="列表变量名">
                <el-input v-model="selectedNode.data.config.list_var" placeholder="items / input" />
              </el-form-item>
              <el-form-item label="过滤字段">
                <el-input v-model="selectedNode.data.config.field" placeholder="留空则过滤整个元素" />
              </el-form-item>
              <el-form-item label="运算符">
                <el-select v-model="selectedNode.data.config.operator" style="width:100%">
                  <el-option label="等于" value="eq" />
                  <el-option label="不等于" value="ne" />
                  <el-option label="大于" value="gt" />
                  <el-option label="小于" value="lt" />
                  <el-option label="包含" value="contains" />
                  <el-option label="开头是" value="startswith" />
                </el-select>
              </el-form-item>
              <el-form-item label="比较值">
                <el-input v-model="selectedNode.data.config.value" placeholder="active" />
              </el-form-item>
            </template>
            <!-- Data Sort 配置 -->
            <template v-if="selectedNode.type === 'data_sort'">
              <el-form-item label="列表变量名">
                <el-input v-model="selectedNode.data.config.list_var" placeholder="items / input" />
              </el-form-item>
              <el-form-item label="排序字段">
                <el-input v-model="selectedNode.data.config.sort_field" placeholder="留空按值排序" />
              </el-form-item>
              <el-form-item label="降序">
                <el-switch v-model="selectedNode.data.config.reverse" />
              </el-form-item>
            </template>
            <!-- Switch 配置 -->
            <template v-if="selectedNode.type === 'switch'">
              <el-form-item label="判断变量">
                <el-input v-model="selectedNode.data.config.switch_var" placeholder="{{llm_1}}" />
              </el-form-item>
              <el-form-item label="分支规则 (每行 值:分支名)">
                <el-input v-model="selectedNode.data.config.cases" type="textarea" :rows="4" placeholder='是:approve\n否:reject' />
              </el-form-item>
              <el-form-item label="默认分支">
                <el-input v-model="selectedNode.data.config.default_case" placeholder="default" />
              </el-form-item>
            </template>
            <!-- Sub Workflow 配置 -->
            <template v-if="selectedNode.type === 'sub_workflow'">
              <el-form-item label="子工作流 ID">
                <el-input v-model="selectedNode.data.config.workflow_id" placeholder="email-demo-001" />
              </el-form-item>
              <el-form-item label="输入参数 (JSON)">
                <el-input v-model="selectedNode.data.config.inputs_map" type="textarea" :rows="3" placeholder='{"input": "{{input}}"}' />
              </el-form-item>
            </template>
            <!-- Retry 配置 -->
            <template v-if="selectedNode.type === 'retry'">
              <el-form-item label="最大重试次数">
                <el-input-number v-model="selectedNode.data.config.max_retries" :min="1" :max="10" style="width:100%" />
              </el-form-item>
              <el-form-item label="重试间隔 (秒)">
                <el-input-number v-model="selectedNode.data.config.delay" :min="1" :max="30" style="width:100%" />
              </el-form-item>
            </template>
            <!-- Notify 配置 -->
            <template v-if="selectedNode.type === 'notify'">
              <el-form-item label="通知类型">
                <el-select v-model="selectedNode.data.config.notify_type" style="width:100%">
                  <el-option label="钉钉" value="dingtalk" />
                  <el-option label="企业微信" value="wecom" />
                  <el-option label="飞书" value="feishu" />
                  <el-option label="自定义" value="custom" />
                </el-select>
              </el-form-item>
              <el-form-item label="Webhook URL">
                <el-input v-model="selectedNode.data.config.webhook_url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx" />
              </el-form-item>
              <el-form-item label="标题">
                <el-input v-model="selectedNode.data.config.title" placeholder="工作流通知" />
              </el-form-item>
              <el-form-item label="通知内容">
                <el-input v-model="selectedNode.data.config.content" type="textarea" :rows="3" placeholder="{{transform_1}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'math_calc'">
              <el-form-item label="数学表达式">
                <el-input v-model="selectedNode.data.config.expression" placeholder="2 + 3 * 4 / sqrt(16)" />
              </el-form-item>
              <el-form-item>
                <div style="font-size:12px;color:#909399;line-height:1.8">支持: +, -, *, /, **, %, sqrt, sin, cos, tan, log, log10, abs, round, min, max, ceil, floor, pi, e</div>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'datetime'">
              <el-form-item label="操作">
                <el-select v-model="selectedNode.data.config.action" style="width:100%">
                  <el-option label="当前时间" value="now" />
                  <el-option label="今天日期" value="today" />
                  <el-option label="时间戳" value="timestamp" />
                  <el-option label="解析日期" value="parse" />
                  <el-option label="日期加减" value="add" />
                  <el-option label="日期差值" value="diff" />
                </el-select>
              </el-form-item>
              <el-form-item label="格式">
                <el-input v-model="selectedNode.data.config.format" placeholder="%Y-%m-%d %H:%M:%S" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='parse'||selectedNode.data.config.action==='add'||selectedNode.data.config.action==='diff'" label="输入日期">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="2025-01-01T12:00:00" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='add'" label="加天数">
                <el-input-number v-model="selectedNode.data.config.days" :min="-365" :max="365" style="width:100%" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='add'" label="加小时">
                <el-input-number v-model="selectedNode.data.config.hours" :min="-48" :max="48" style="width:100%" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='diff'" label="结束日期">
                <el-input v-model="selectedNode.data.config.end_date" placeholder="2025-12-31T23:59:59" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'type_convert'">
              <el-form-item label="目标类型">
                <el-select v-model="selectedNode.data.config.target_type" style="width:100%">
                  <el-option label="字符串 String" value="string" />
                  <el-option label="整数 Int" value="int" />
                  <el-option label="浮点数 Float" value="float" />
                  <el-option label="布尔 Bool" value="bool" />
                  <el-option label="列表 List" value="list" />
                  <el-option label="JSON 对象" value="json" />
                  <el-option label="字典 Dict" value="dict" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.target_type==='list'" label="分隔符">
                <el-input v-model="selectedNode.data.config.delimiter" placeholder="," />
              </el-form-item>
              <el-form-item label="输入值">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="2" placeholder="用 {{变量名}} 引用上游输出" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'csv_parse'">
              <el-form-item label="分隔符">
                <el-input v-model="selectedNode.data.config.delimiter" placeholder="," />
              </el-form-item>
              <el-form-item label="首行为表头">
                <el-switch v-model="selectedNode.data.config.has_header" />
              </el-form-item>
              <el-form-item label="CSV 内容/文件路径">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="{{变量名}} 或 文件路径" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'excel_read'">
              <el-form-item label="Excel 文件路径">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\data.xlsx" />
              </el-form-item>
              <el-form-item label="Sheet 名称 (留空=活动页)">
                <el-input v-model="selectedNode.data.config.sheet_name" placeholder="Sheet1" />
              </el-form-item>
              <el-form-item label="最大行数">
                <el-input-number v-model="selectedNode.data.config.max_rows" :min="1" :max="10000" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'regex_replace'">
              <el-form-item label="正则表达式">
                <el-input v-model="selectedNode.data.config.pattern" placeholder="(\d+)" />
              </el-form-item>
              <el-form-item label="替换为">
                <el-input v-model="selectedNode.data.config.replacement" placeholder="number: $1" />
              </el-form-item>
              <el-form-item label="输入文本">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="2" placeholder="{{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'hash_encode'">
              <el-form-item label="算法">
                <el-select v-model="selectedNode.data.config.algorithm" style="width:100%">
                  <el-option label="MD5" value="md5" />
                  <el-option label="SHA1" value="sha1" />
                  <el-option label="SHA256" value="sha256" />
                  <el-option label="SHA512" value="sha512" />
                  <el-option label="Base64 编码" value="base64_encode" />
                  <el-option label="Base64 解码" value="base64_decode" />
                  <el-option label="URL 编码" value="url_encode" />
                  <el-option label="URL 解码" value="url_decode" />
                </el-select>
              </el-form-item>
              <el-form-item label="输入内容">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="2" placeholder="{{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'uuid_generate'">
              <el-form-item label="UUID 版本">
                <el-select v-model="selectedNode.data.config.version" style="width:100%">
                  <el-option label="v4 (随机)" value="4" />
                  <el-option label="v1 (时间戳)" value="1" />
                </el-select>
              </el-form-item>
              <el-form-item label="生成数量">
                <el-input-number v-model="selectedNode.data.config.count" :min="1" :max="100" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'text_embedding'">
              <el-form-item label="输入文本">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="{{变量名}}" />
              </el-form-item>
              <el-form-item label="提供商">
                <el-select v-model="selectedNode.data.config.provider" style="width:100%">
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="Agnes" value="agnes" />
                </el-select>
              </el-form-item>
              <el-form-item label="模型">
                <el-input v-model="selectedNode.data.config.model" placeholder="text-embedding-ada-002" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'speech_to_text'">
              <el-form-item label="音频文件路径">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\audio.mp3" />
              </el-form-item>
              <el-form-item label="语言">
                <el-select v-model="selectedNode.data.config.language" style="width:100%">
                  <el-option label="中文" value="zh" />
                  <el-option label="英文" value="en" />
                  <el-option label="日文" value="ja" />
                  <el-option label="自动检测" value="auto" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'text_to_speech'">
              <el-form-item label="文本内容">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="要转换的文本" />
              </el-form-item>
              <el-form-item label="音色">
                <el-select v-model="selectedNode.data.config.voice" style="width:100%">
                  <el-option label="Alloy" value="alloy" />
                  <el-option label="Echo" value="echo" />
                  <el-option label="Fable" value="fable" />
                  <el-option label="Onyx" value="onyx" />
                  <el-option label="Nova" value="nova" />
                  <el-option label="Shimmer" value="shimmer" />
                </el-select>
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="留空自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'image_process'">
              <el-form-item label="图片路径">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\image.png" />
              </el-form-item>
              <el-form-item label="操作">
                <el-select v-model="selectedNode.data.config.action" style="width:100%">
                  <el-option label="缩放" value="resize" />
                  <el-option label="裁剪" value="crop" />
                  <el-option label="旋转" value="rotate" />
                  <el-option label="水印" value="watermark" />
                  <el-option label="灰度" value="grayscale" />
                  <el-option label="缩略图" value="thumbnail" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='resize'" label="宽度">
                <el-input-number v-model="selectedNode.data.config.width" :min="1" :max="10000" style="width:100%" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='resize'" label="高度">
                <el-input-number v-model="selectedNode.data.config.height" :min="1" :max="10000" style="width:100%" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='rotate'" label="旋转角度">
                <el-input-number v-model="selectedNode.data.config.angle" :min="-360" :max="360" style="width:100%" />
              </el-form-item>
              <el-form-item v-if="selectedNode.data.config.action==='watermark'" label="水印文字">
                <el-input v-model="selectedNode.data.config.text" placeholder="Watermark" />
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="留空覆盖原文件" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'markdown_html'">
              <el-form-item label="Markdown 内容">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="4" placeholder="{{变量名}}" />
              </el-form-item>
              <el-form-item label="保存路径 (可选)">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="C:\Users\output.html" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'websocket_connect'">
              <el-form-item label="WebSocket URL">
                <el-input v-model="selectedNode.data.config.url" placeholder="ws://localhost:8080/ws" />
              </el-form-item>
              <el-form-item label="发送消息">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="2" placeholder='{"action": "ping"}' />
              </el-form-item>
              <el-form-item label="超时 (秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="60" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'http_stream'">
              <el-form-item label="请求方法">
                <el-select v-model="selectedNode.data.config.method" style="width:100%">
                  <el-option label="GET" value="GET" />
                  <el-option label="POST" value="POST" />
                </el-select>
              </el-form-item>
              <el-form-item label="URL">
                <el-input v-model="selectedNode.data.config.url" placeholder="https://api.example.com/stream" />
              </el-form-item>
              <el-form-item label="请求头">
                <el-input v-model="selectedNode.data.config.headers" type="textarea" :rows="2" placeholder='{"Authorization": "Bearer xxx"}' />
              </el-form-item>
              <el-form-item label="请求体">
                <el-input v-model="selectedNode.data.config.body" type="textarea" :rows="2" placeholder='{"prompt": "hello"}' />
              </el-form-item>
              <el-form-item label="超时 (秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="120" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'network_ping'">
              <el-form-item label="目标地址">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="8.8.8.8 或 google.com" />
              </el-form-item>
              <el-form-item label="Ping 次数">
                <el-input-number v-model="selectedNode.data.config.count" :min="1" :max="10" style="width:100%" />
              </el-form-item>
              <el-form-item label="超时 (秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="1" :max="30" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'url_shorten'">
              <el-form-item label="原始 URL">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="https://example.com/very/long/url" />
              </el-form-item>
              <el-form-item label="缩短服务">
                <el-select v-model="selectedNode.data.config.provider" style="width:100%">
                  <el-option label="TinyURL" value="tinyurl" />
                  <el-option label="is.gd" value="is.gd" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'qrcode_gen'">
              <el-form-item label="二维码内容">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="https://example.com 或任意文本" />
              </el-form-item>
              <el-form-item label="图片尺寸">
                <el-input-number v-model="selectedNode.data.config.size" :min="128" :max="1024" style="width:100%" />
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="留空自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'qrcode_scan'">
              <el-form-item label="图片路径">
                <el-input v-model="selectedNode.data.config.input_template" placeholder="C:\Users\qrcode.png" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'pdf_generate'">
              <el-form-item label="PDF 标题">
                <el-input v-model="selectedNode.data.config.title" placeholder="文档标题" />
              </el-form-item>
              <el-form-item label="正文内容">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="4" placeholder="{{变量名}} 或纯文本" />
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="留空自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'json_diff'">
              <el-form-item label="JSON A">
                <el-input v-model="selectedNode.data.config.input_template" type="textarea" :rows="3" placeholder="{{变量名}}" />
              </el-form-item>
              <el-form-item label="JSON B">
                <el-input v-model="selectedNode.data.config.compare_value" type="textarea" :rows="3" placeholder="{{变量名}}" />
              </el-form-item>
            </template>
            <el-button type="danger" size="small" @click="removeNode" style="width:100%;margin-top:8px">删除节点</el-button>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 执行输入对话框 -->
    <el-dialog v-model="showRunDialog" title="执行工作流" width="500px">
      <el-form label-position="top" size="small">
        <el-form-item label="输入参数 (JSON)">
          <el-input v-model="runInputs" type="textarea" :rows="6" placeholder='{"input": "你的输入内容"}' />
        </el-form-item>
      </el-form>
      <div v-if="runResult">
        <el-divider />
        <div style="font-size:13px;color:#606266;margin-bottom:8px">执行结果</div>
        <el-tag :type="runResult.status === 'completed' ? 'success' : 'danger'" size="small" style="margin-bottom:8px">{{ runResult.status }}</el-tag>
        <pre style="background:#f5f7fa;padding:12px;border-radius:6px;font-size:12px;max-height:300px;overflow:auto;white-space:pre-wrap">{{ JSON.stringify(runResult.outputs || runResult.node_results, null, 2) }}</pre>
      </div>
      <template #footer>
        <el-button @click="showRunDialog = false">关闭</el-button>
        <el-button type="primary" :loading="running" @click="doRun">执行</el-button>
      </template>
    </el-dialog>

    <!-- 执行日志对话框 -->
    <el-dialog v-model="showRunsDialog" title="执行日志" width="700px">
      <el-table :data="runLogs" stripe size="small" v-loading="loadingRuns">
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" width="170">
          <template #default="{ row }">{{ row.started_at }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">
            {{ row.finished_at ? ((new Date(row.finished_at) - new Date(row.started_at)) / 1000).toFixed(1) + 's' : '执行中...' }}
          </template>
        </el-table-column>
        <el-table-column label="结果" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error" style="color:#f56c6c">{{ row.error }}</span>
            <span v-else style="color:#67c23a">成功</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialogFlag" title="导入工作流" width="600px">
      <el-form label-position="top" size="small">
        <el-form-item label="导入方式">
          <el-radio-group v-model="importMode">
            <el-radio value="json">粘贴 JSON</el-radio>
            <el-radio value="file">上传文件</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="importMode === 'json'" label="工作流 JSON">
          <el-input v-model="importJson" type="textarea" :rows="10" placeholder='粘贴导出的 JSON...' />
        </el-form-item>
        <el-form-item v-else label="选择文件">
          <input type="file" accept=".json" @change="onImportFileChange" ref="importFileInput" style="display:none" />
          <el-button @click="$refs.importFileInput.click()">选择 JSON 文件</el-button>
          <span v-if="importFileName" style="margin-left:8px;color:#909399">{{ importFileName }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialogFlag = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- 版本控制对话框 -->
    <el-dialog v-model="showVersionsDialog" title="版本历史" width="700px">
      <el-table :data="versions" stripe size="small" v-loading="loadingVersions">
        <el-table-column label="版本" width="80" align="center">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="节点数" width="80" align="center">
          <template #default="{ row }">{{ (row.nodes || []).length }}</template>
        </el-table-column>
        <el-table-column label="备注" prop="comment" show-overflow-tooltip />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="doRestoreVersion(row)">恢复</el-button>
            <el-button type="info" text size="small" @click="doExportVersion(row)">导出</el-button>
            <el-button type="danger" text size="small" @click="doDeleteVersion(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 保存版本对话框 -->
    <el-dialog v-model="showSaveVersionFlag" title="保存版本" width="400px">
      <el-form label-position="top" size="small">
        <el-form-item label="版本备注">
          <el-input v-model="versionComment" type="textarea" :rows="3" placeholder="描述本次修改内容..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveVersionFlag = false">取消</el-button>
        <el-button type="primary" :loading="savingVersion" @click="doSaveVersion">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'
import { Controls } from '@vue-flow/controls'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWorkflows, createWorkflow as apiCreate, getWorkflow, updateWorkflow as apiUpdate, deleteWorkflow as apiDelete, runWorkflow as apiRun, getWorkflowRuns, exportWorkflow as apiExport, importWorkflow as apiImport, saveWorkflowVersion as apiSaveVersion, getWorkflowVersions as apiGetVersions, restoreWorkflowVersion as apiRestoreVersion, deleteWorkflowVersion as apiDeleteVersion } from '../api'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/minimap/dist/style.css'
import '@vue-flow/controls/dist/style.css'

const loadingList = ref(false)
const workflows = ref([])
const editing = ref(false)
const saving = ref(false)
const currentWf = ref({ name: '', nodes: [], edges: [], status: 'draft' })
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)

const nodeTypes = [
  { type: 'start', label: '输入', icon: '📥', color: '#ecf5ff' },
  { type: 'llm', label: 'LLM 调用', icon: '🧠', color: '#f0f9eb' },
  { type: 'tool', label: '工具调用', icon: '🔧', color: '#fdf6ec' },
  { type: 'condition', label: '条件分支', icon: '🔀', color: '#fef0f0' },
  { type: 'transform', label: '数据转换', icon: '🔄', color: '#f4f4f5' },
  { type: 'delay', label: '延时等待', icon: '⏱️', color: '#fef0f0' },
  { type: 'loop', label: '循环遍历', icon: '🔁', color: '#ecf5ff' },
  { type: 'parallel', label: '并行执行', icon: '⚡', color: '#fdf6ec' },
  { type: 'database', label: '数据库', icon: '🗄️', color: '#f0f9eb' },
  { type: 'file_operation', label: '文件操作', icon: '📁', color: '#f4f4f5' },
  { type: 'webhook', label: 'Webhook', icon: '🌐', color: '#ecf5ff' },
  { type: 'code_exec', label: '代码执行', icon: '💻', color: '#fef0f0' },
  { type: 'image_gen', label: '图像生成', icon: '🎨', color: '#fdf6ec' },
  { type: 'error_handler', label: '错误处理', icon: '🛡️', color: '#fef0f0' },
  { type: 'text_split', label: '文本分割', icon: '✂️', color: '#f4f4f5' },
  { type: 'text_translate', label: '文本翻译', icon: '🌍', color: '#ecf5ff' },
  { type: 'text_summarize', label: '文本摘要', icon: '📝', color: '#f0f9eb' },
  { type: 'json_build', label: 'JSON构建', icon: '📦', color: '#fdf6ec' },
  { type: 'data_filter', label: '数据过滤', icon: '🔍', color: '#f4f4f5' },
  { type: 'data_sort', label: '数据排序', icon: '🔃', color: '#ecf5ff' },
  { type: 'switch', label: '多分支', icon: '🎯', color: '#fef0f0' },
  { type: 'sub_workflow', label: '子工作流', icon: '🔗', color: '#f0f9eb' },
  { type: 'retry', label: '重试', icon: '🔄', color: '#fdf6ec' },
  { type: 'notify', label: '通知推送', icon: '📢', color: '#ecf5ff' },
  { type: 'math_calc', label: '数学计算', icon: '🔢', color: '#f0f9eb' },
  { type: 'datetime', label: '日期时间', icon: '🕐', color: '#ecf5ff' },
  { type: 'type_convert', label: '类型转换', icon: '🔄', color: '#f4f4f5' },
  { type: 'csv_parse', label: 'CSV解析', icon: '📊', color: '#fdf6ec' },
  { type: 'excel_read', label: 'Excel读取', icon: '📗', color: '#f0f9eb' },
  { type: 'regex_replace', label: '正则替换', icon: '🔤', color: '#fef0f0' },
  { type: 'hash_encode', label: '哈希编码', icon: '#️⃣', color: '#ecf5ff' },
  { type: 'uuid_generate', label: 'UUID生成', icon: '🆔', color: '#fdf6ec' },
  { type: 'text_embedding', label: '文本嵌入', icon: '🧬', color: '#f0f9eb' },
  { type: 'speech_to_text', label: '语音转文字', icon: '🎤', color: '#fef0f0' },
  { type: 'text_to_speech', label: '文字转语音', icon: '🔊', color: '#ecf5ff' },
  { type: 'image_process', label: '图片处理', icon: '🖼️', color: '#fdf6ec' },
  { type: 'markdown_html', label: 'Markdown→HTML', icon: '📄', color: '#f4f4f5' },
  { type: 'websocket_connect', label: 'WebSocket', icon: '🔌', color: '#ecf5ff' },
  { type: 'http_stream', label: 'HTTP流式', icon: '📡', color: '#f0f9eb' },
  { type: 'network_ping', label: '网络Ping', icon: '🏓', color: '#fef0f0' },
  { type: 'url_shorten', label: 'URL缩短', icon: '🔗', color: '#fdf6ec' },
  { type: 'qrcode_gen', label: '二维码生成', icon: '📱', color: '#f4f4f5' },
  { type: 'qrcode_scan', label: '二维码识别', icon: '📷', color: '#ecf5ff' },
  { type: 'pdf_generate', label: 'PDF生成', icon: '📋', color: '#fef0f0' },
  { type: 'json_diff', label: 'JSON对比', icon: '🔍', color: '#f0f9eb' },
  { type: 'output', label: '输出', icon: '📤', color: '#ecf5ff' },
]

const showRunDialog = ref(false)
const runInputs = ref('{\n  "input": "测试输入"\n}')
const runResult = ref(null)
const running = ref(false)
const runTarget = ref(null)

const showRunsDialog = ref(false)
const runLogs = ref([])
const loadingRuns = ref(false)

const showImportDialogFlag = ref(false)
const importMode = ref('json')
const importJson = ref('')
const importFileName = ref('')
const importFileData = ref(null)
const importing = ref(false)

const showVersionsDialog = ref(false)
const versions = ref([])
const loadingVersions = ref(false)
const showSaveVersionFlag = ref(false)
const versionComment = ref('')
const savingVersion = ref(false)
const versionTarget = ref(null)

const fetchWorkflows = async () => {
  loadingList.value = true
  try {
    const { data } = await getWorkflows()
    workflows.value = data.workflows || []
  } catch (e) { ElMessage.error('加载失败') } finally { loadingList.value = false }
}

const createNew = async () => {
  try {
    const { data } = await apiCreate({
      name: '新工作流',
      nodes: [{ id: 'start_1', type: 'start', label: '输入', position: { x: 100, y: 200 }, config: {} }],
      edges: []
    })
    editing.value = true
    currentWf.value = data
    nodes.value = data.nodes.map(n => ({ ...n, data: { label: n.label, config: n.config || {} } }))
    edges.value = data.edges
  } catch (e) { ElMessage.error('创建失败') }
}

const editWorkflow = async (wf) => {
  try {
    const { data } = await getWorkflow(wf.id || wf._id)
    editing.value = true
    currentWf.value = data
    nodes.value = (data.nodes || []).map(n => ({ id: n.id, type: n.type, position: n.position || { x: 0, y: 0 }, data: { label: n.label, config: n.config || {} } }))
    edges.value = data.edges || []
    await nextTick()
    selectedNode.value = null
  } catch (e) { ElMessage.error('加载失败') }
}

const runWf = () => {
  runTarget.value = currentWf.value
  runResult.value = null
  runInputs.value = '{\n  "input": "测试输入"\n}'
  showRunDialog.value = true
}

const handleMore = (cmd, row) => {
  if (cmd === 'log') viewRuns(row)
  else if (cmd === 'version') viewVersions(row)
  else if (cmd === 'export') doExport(row)
  else if (cmd === 'delete') delWorkflow(row)
}

const backToList = () => { editing.value = false; selectedNode.value = null; fetchWorkflows() }

const toggleStatus = async () => {
  currentWf.value.status = currentWf.value.status === 'active' ? 'draft' : 'active'
  try {
    await apiUpdate(currentWf.value.id || currentWf.value._id, { status: currentWf.value.status })
    ElMessage.success(currentWf.value.status === 'active' ? '已启用' : '已停用')
  } catch (e) { ElMessage.error('操作失败') }
}

const saveWf = async () => {
  saving.value = true
  try {
    const payload = {
      name: currentWf.value.name,
      status: currentWf.value.status,
      nodes: nodes.value.map(n => ({ id: n.id, type: n.type, label: n.data?.label || '', position: n.position, config: n.data?.config || {} })),
      edges: edges.value.map(e => ({ id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle }))
    }
    await apiUpdate(currentWf.value.id || currentWf.value._id, payload)
    ElMessage.success('保存成功')
  } catch (e) { ElMessage.error('保存失败') } finally { saving.value = false }
}

const delWorkflow = async (wf) => {
  try {
    await ElMessageBox.confirm('确定删除该工作流？', '确认')
    await apiDelete(wf.id || wf._id)
    ElMessage.success('已删除')
    fetchWorkflows()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

const runWorkflowDialog = (wf) => {
  runTarget.value = wf
  runResult.value = null
  runInputs.value = '{\n  "input": "测试输入"\n}'
  showRunDialog.value = true
}

const doRun = async () => {
  if (!runTarget.value) return
  running.value = true
  try {
    let inputs = {}
    try { inputs = JSON.parse(runInputs.value) } catch (e) { ElMessage.warning('JSON 格式错误'); running.value = false; return }
    const { data } = await apiRun(runTarget.value.id || runTarget.value._id, inputs)
    runResult.value = data
    ElMessage.success('执行完成')
  } catch (e) { ElMessage.error('执行失败') } finally { running.value = false }
}

const viewRuns = async (wf) => {
  runTarget.value = wf
  showRunsDialog.value = true
  loadingRuns.value = true
  try {
    const { data } = await getWorkflowRuns(wf.id || wf._id)
    runLogs.value = data.runs || []
  } catch (e) { ElMessage.error('加载失败') } finally { loadingRuns.value = false }
}

const onDragStart = (event, type) => {
  event.dataTransfer.setData('application/node-type', type)
  event.dataTransfer.effectAllowed = 'move'
}

const onDrop = (event) => {
  const type = event.dataTransfer.getData('application/node-type')
  if (!type) return
  const nt = nodeTypes.find(n => n.type === type)
  const id = `${type}_${Date.now().toString(36)}`
  const position = { x: event.offsetX - 60, y: event.offsetY - 25 }
  const newNode = { id, type, position, data: { label: nt.label, config: {} } }
  nodes.value = [...nodes.value, newNode]
}

const removeNode = () => {
  if (!selectedNode.value) return
  nodes.value = nodes.value.filter(n => n.id !== selectedNode.value.id)
  edges.value = edges.value.filter(e => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id)
  selectedNode.value = null
}

const nodeTypeLabels = { start: '\u8f93\u5165', llm: 'LLM', tool: '\u5de5\u5177', condition: '\u6761\u4ef6', transform: '\u8f6c\u6362', output: '\u8f93\u51fa' }

const upstreamVars = computed(() => {
  if (!selectedNode.value) return []
  const vars = []
  const id = selectedNode.value.id
  const incomingEdges = edges.value.filter(e => e.target === id)
  const upstreamIds = incomingEdges.map(e => e.source)
  if (upstreamIds.length === 0) {
    vars.push({ name: 'input', desc: '\u5de5\u4f5c\u6d41\u8f93\u5165\u53c2\u6570' })
    return vars
  }
  for (const uid of upstreamIds) {
    const node = nodes.value.find(n => n.id === uid)
    if (!node) continue
    const label = node.data?.label || nodeTypeLabels[node.type] || uid
    vars.push({ name: uid, desc: `${label} \u7684\u5b8c\u6574\u7ed3\u679c` })
    if (node.type === 'start') {
      vars.push({ name: 'input', desc: '\u7528\u6237\u8f93\u5165\u7684\u503c' })
    } else if (node.type === 'llm') {
      vars.push({ name: uid, desc: `${label} \u7684\u56de\u590d\u5185\u5bb9` })
    } else if (node.type === 'tool') {
      const tn = node.data?.config?.tool_name || ''
      if (tn === 'http') {
        vars.push({ name: uid, desc: `${label} \u7684\u8fd4\u56de\u7ed3\u679c (body/status_code)` })
      } else if (tn === 'regex') {
        vars.push({ name: uid, desc: `${label} \u7684\u5339\u914d\u7ed3\u679c (matches/count)` })
      } else if (tn === 'send_email') {
        vars.push({ name: uid, desc: `${label} \u7684\u53d1\u9001\u7ed3\u679c (result/to)` })
      } else {
        vars.push({ name: uid, desc: `${label} \u7684\u6267\u884c\u7ed3\u679c (result)` })
      }
    } else if (node.type === 'transform') {
      vars.push({ name: uid, desc: `${label} \u7684\u8f6c\u6362\u7ed3\u679c (result)` })
    }
  }
  return vars
})

const { onConnect, onNodeClick, onPaneClick, onEdgeClick } = useVueFlow()
onConnect((params) => {
  edges.value = [...edges.value, { id: `e_${params.source}_${params.target}`, source: params.source, target: params.target, sourceHandle: params.sourceHandle }]
})
onNodeClick(({ node }) => {
  selectedNode.value = node
})
onEdgeClick(({ edge }) => {
  ElMessageBox.confirm('删除这条连线？', '确认', { type: 'warning' }).then(() => {
    edges.value = edges.value.filter(e => e.id !== edge.id)
    ElMessage.success('连线已删除')
  }).catch(() => {})
})
onPaneClick(() => {
  selectedNode.value = null
})

const showImportDialog = () => {
  importMode.value = 'json'
  importJson.value = ''
  importFileName.value = ''
  importFileData.value = null
  showImportDialogFlag.value = true
}

const onImportFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  importFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => { importJson.value = ev.target.result }
  reader.readAsText(file)
}

const doImport = async () => {
  importing.value = true
  try {
    const data = JSON.parse(importJson.value)
    await apiImport(data)
    ElMessage.success('导入成功')
    showImportDialogFlag.value = false
    fetchWorkflows()
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.message || 'JSON 格式错误'))
  } finally { importing.value = false }
}

const doExport = async (wf) => {
  try {
    const { data } = await apiExport(wf.id || wf._id)
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${data.name || 'workflow'}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) { ElMessage.error('导出失败') }
}

const viewVersions = async (wf) => {
  versionTarget.value = wf
  showVersionsDialog.value = true
  loadingVersions.value = true
  try {
    const { data } = await apiGetVersions(wf.id || wf._id)
    versions.value = data.versions || []
  } catch (e) { ElMessage.error('加载失败') } finally { loadingVersions.value = false }
}

const showSaveVersionDialog = () => {
  versionComment.value = ''
  versionTarget.value = currentWf.value
  showSaveVersionFlag.value = true
}

const doSaveVersion = async () => {
  savingVersion.value = true
  try {
    await saveWf()
    const { data } = await apiSaveVersion(currentWf.value.id || currentWf.value._id, versionComment.value)
    ElMessage.success(`版本 v${data.version} 已保存`)
    showSaveVersionFlag.value = false
  } catch (e) { ElMessage.error('保存版本失败') } finally { savingVersion.value = false }
}

const doRestoreVersion = async (v) => {
  try {
    await ElMessageBox.confirm(`确定恢复到 v${v.version}？当前未保存的修改将丢失。`, '恢复版本')
    await apiRestoreVersion(versionTarget.value.id || versionTarget.value._id, v.version)
    ElMessage.success('已恢复')
    showVersionsDialog.value = false
    fetchWorkflows()
  } catch (e) { if (e !== 'cancel') ElMessage.error('恢复失败') }
}

const doExportVersion = async (v) => {
  try {
    const json = JSON.stringify({ name: v.name, description: v.description, nodes: v.nodes, edges: v.edges }, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${v.name || 'workflow'}_v${v.version}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { ElMessage.error('导出失败') }
}

const doDeleteVersion = async (v) => {
  try {
    await ElMessageBox.confirm(`确定删除版本 v${v.version}？`, '删除版本')
    await apiDeleteVersion(versionTarget.value.id || versionTarget.value._id, v.version)
    ElMessage.success('已删除')
    viewVersions(versionTarget.value)
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

onMounted(fetchWorkflows)
</script>

<style scoped>
.workflow-page { height: 100%; }
.editor-layout { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.editor-topbar { display: flex; align-items: center; padding: 8px 16px; background: #fff; border-bottom: 1px solid #ebeef5; }
.editor-body { display: flex; flex: 1; overflow: hidden; }
.node-panel { width: 160px; border-right: 1px solid #ebeef5; padding: 12px; background: #fafafa; overflow-y: auto; }
.panel-title { font-size: 13px; font-weight: 600; color: #606266; margin-bottom: 12px; }
.node-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; margin-bottom: 6px; border-radius: 6px; cursor: grab; font-size: 13px; transition: background 0.2s; }
.node-item:hover { background: #ecf5ff; }
.node-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.canvas-wrap { flex: 1; background: #f5f7fa; }
.config-panel { width: 280px; border-left: 1px solid #ebeef5; padding: 12px; overflow-y: auto; }
.custom-node { display: flex; align-items: center; gap: 6px; padding: 10px 16px; border-radius: 8px; border: 2px solid #e4e7ed; background: #fff; min-width: 100px; cursor: pointer; }
.start-node { border-color: #409eff; }
.llm-node { border-color: #67c23a; }
.tool-node { border-color: #e6a23c; }
.condition-node { border-color: #f56c6c; }
.transform-node { border-color: #909399; }
.output-node { border-color: #409eff; }
.delay-node { border-color: #f56c6c; }
.loop-node { border-color: #409eff; }
.parallel-node { border-color: #e6a23c; }
.database-node { border-color: #67c23a; }
.file-operation-node { border-color: #909399; }
.webhook-node { border-color: #409eff; }
.code-exec-node { border-color: #f56c6c; }
.image-gen-node { border-color: #e6a23c; }
.error-handler-node { border-color: #f56c6c; }
.text-split-node { border-color: #909399; }
.text-translate-node { border-color: #409eff; }
.text-summarize-node { border-color: #67c23a; }
.json-build-node { border-color: #e6a23c; }
.data-filter-node { border-color: #909399; }
.data-sort-node { border-color: #409eff; }
.switch-node { border-color: #f56c6c; }
.sub-workflow-node { border-color: #67c23a; }
.retry-node { border-color: #e6a23c; }
.notify-node { border-color: #409eff; }
.math-calc-node { border-color: #67c23a; }
.datetime-node { border-color: #409eff; }
.type-convert-node { border-color: #909399; }
.csv-parse-node { border-color: #e6a23c; }
.excel-read-node { border-color: #67c23a; }
.regex-replace-node { border-color: #f56c6c; }
.hash-encode-node { border-color: #409eff; }
.uuid-generate-node { border-color: #e6a23c; }
.text-embedding-node { border-color: #67c23a; }
.speech-to-text-node { border-color: #f56c6c; }
.text-to-speech-node { border-color: #409eff; }
.image-process-node { border-color: #e6a23c; }
.markdown-html-node { border-color: #909399; }
.websocket-connect-node { border-color: #409eff; }
.http-stream-node { border-color: #67c23a; }
.network-ping-node { border-color: #f56c6c; }
.url-shorten-node { border-color: #e6a23c; }
.qrcode-gen-node { border-color: #909399; }
.qrcode-scan-node { border-color: #409eff; }
.pdf-generate-node { border-color: #f56c6c; }
.json-diff-node { border-color: #67c23a; }
.cn-icon { font-size: 16px; }
.cn-label { font-size: 13px; font-weight: 500; color: #303133; }
:deep(.vue-flow__handle) { width: 10px; height: 10px; border-radius: 50%; background: #409eff; border: 2px solid #fff; }
:deep(.vue-flow__handle:hover) { background: #337ecc; transform: scale(1.3); }
:deep(.vue-flow__connection-path) { stroke: #409eff; stroke-width: 2; }
:deep(.vue-flow__edge-path) { stroke: #409eff; stroke-width: 2; }
:deep(.vue-flow__edge:hover .vue-flow__edge-path) { stroke: #f56c6c; stroke-width: 3; cursor: pointer; }
:deep(.vue-flow__edge.selected .vue-flow__edge-path) { stroke: #f56c6c; stroke-width: 3; }
:deep(.vue-flow__attribution) { display: none; }
.action-btns { display: flex; flex-wrap: nowrap; gap: 4px; align-items: center; }
.action-btns .el-button { margin: 0; border-radius: 6px; font-size: 12px; padding: 4px 8px; display: inline-flex; align-items: center; gap: 2px; transition: all 0.2s; white-space: nowrap; flex-shrink: 0; }
.btn-icon { font-size: 12px; }
.btn-edit { color: #409eff; border: 1px solid #b3d8ff; background: #ecf5ff; }
.btn-edit:hover { background: #409eff; color: #fff; border-color: #409eff; }
.btn-run { color: #67c23a; border: 1px solid #c2e7b0; background: #f0f9eb; }
.btn-run:hover { background: #67c23a; color: #fff; border-color: #67c23a; }
.btn-log { color: #909399; border: 1px solid #d3d4d6; background: #f4f4f5; }
.btn-log:hover { background: #909399; color: #fff; border-color: #909399; }
.btn-version { color: #e6a23c; border: 1px solid #f3d19e; background: #fdf6ec; }
.btn-version:hover { background: #e6a23c; color: #fff; border-color: #e6a23c; }
.btn-export { color: #606266; border: 1px solid #dcdfe6; background: #fff; }
.btn-export:hover { background: #606266; color: #fff; border-color: #606266; }
.btn-more { color: #606266; border: 1px solid #dcdfe6; background: #fff; }
.btn-more:hover { background: #ecf5ff; color: #409eff; border-color: #b3d8ff; }
.var-hint { background: #f0f9eb; border: 1px solid #e1f3d8; border-radius: 6px; padding: 8px 10px; margin-bottom: 12px; font-size: 12px; }
.var-hint-title { font-weight: 600; color: #67c23a; margin-bottom: 4px; }
.var-hint-tip { color: #909399; margin-bottom: 6px; }
.var-hint-tip code { background: #fff; padding: 1px 4px; border-radius: 3px; color: #e6a23c; font-size: 11px; }
.var-hint-item { display: flex; align-items: center; gap: 6px; padding: 2px 0; }
.var-hint-item code { background: #fff; padding: 1px 6px; border-radius: 3px; color: #409eff; font-size: 11px; white-space: nowrap; }
.var-hint-desc { color: #909399; font-size: 11px; }
</style>
