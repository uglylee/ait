<template>
  <div class="workflow-page">
    <!-- 工作流列表视图 -->
    <div v-if="!editing">
      <div class="page-card">
        <div class="card-header">
          <h3>AI 工作流</h3>
          <div>
            <el-button size="small" @click="showImportDialog">导入</el-button>
            <el-button size="small" type="warning" @click="showTemplateDialog = true">模板库</el-button>
            <el-button size="small" type="success" @click="showAiDialog = true">AI创建</el-button>
            <el-button size="small" :type="batchMode ? 'danger' : ''" @click="toggleBatchMode">{{ batchMode ? '取消' : '批量操作' }}</el-button>
            <el-button v-if="batchMode" size="small" type="danger" @click="batchDelete" :disabled="selectedWorkflows.length === 0">删除({{ selectedWorkflows.length }})</el-button>
            <el-button v-if="batchMode" size="small" type="success" @click="batchExport" :disabled="selectedWorkflows.length === 0">导出({{ selectedWorkflows.length }})</el-button>
            <el-button type="primary" size="small" @click="createNew">新建工作流</el-button>
          </div>
        </div>
        <div class="card-body">
          <el-table :data="paginatedWorkflows" stripe v-loading="loadingList" @selection-change="(val) => selectedWorkflows = val">
            <el-table-column v-if="batchMode" type="selection" width="40" />
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
          <div v-if="workflows.length > pageSize" style="margin-top:12px;display:flex;justify-content:flex-end">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 15, 20, 50]"
              :total="workflows.length"
              layout="total, sizes, prev, pager, next"
              small
            />
          </div>
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
          <input v-model="nodeSearchQuery" placeholder="搜索节点..." class="node-search-input" />
          <div class="node-category-bar">
            <span v-for="cat in nodeCategories" :key="cat.value" class="node-cat-tag" :class="{ active: nodeCategory === cat.value }" @click="nodeCategory = cat.value">{{ cat.label }}</span>
          </div>
          <div class="node-list-scroll">
            <div v-for="nt in filteredNodeTypes" :key="nt.type" class="node-item" draggable="true" @dragstart="onDragStart($event, nt.type)">
              <span class="node-icon" :style="{ background: nt.color }">{{ nt.icon }}</span>
              <span>{{ nt.label }}</span>
            </div>
          </div>
        </div>
        <!-- 画布 -->
        <div class="canvas-wrap" ref="canvasRef" @drop="onDrop" @dragover.prevent>
          <VueFlow v-model:nodes="nodes" v-model:edges="edges" fit-view-on-init :default-edge-options="{ type: 'smoothstep', animated: true }" :edges-updatable="true" :edges-focusable="true" @node-click="handleNodeClick" @pane-click="handlePaneClick">
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

            <template #node-approval="nodeProps">
              <div class="custom-node approval-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">✅</span><span class="cn-label">{{ nodeProps.data?.label || '审批' }}</span></div>
            </template>
            <template #node-email_send="nodeProps">
              <div class="custom-node email-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📧</span><span class="cn-label">{{ nodeProps.data?.label || '邮件' }}</span></div>
            </template>
            <template #node-excel_write="nodeProps">
              <div class="custom-node excel-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📗</span><span class="cn-label">{{ nodeProps.data?.label || 'Excel' }}</span></div>
            </template>
            <template #node-chart_gen="nodeProps">
              <div class="custom-node chart-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📊</span><span class="cn-label">{{ nodeProps.data?.label || '图表' }}</span></div>
            </template>
            <template #node-statistics="nodeProps">
              <div class="custom-node stats-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📈</span><span class="cn-label">{{ nodeProps.data?.label || '统计' }}</span></div>
            </template>
            <template #node-calendar_event="nodeProps">
              <div class="custom-node calendar-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📅</span><span class="cn-label">{{ nodeProps.data?.label || '日历' }}</span></div>
            </template>
            <template #node-sentiment_analysis="nodeProps">
              <div class="custom-node sentiment-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">💭</span><span class="cn-label">{{ nodeProps.data?.label || '情感分析' }}</span></div>
            </template>
            <template #node-template_render="nodeProps">
              <div class="custom-node template-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📝</span><span class="cn-label">{{ nodeProps.data?.label || '模板' }}</span></div>
            </template>
            <template #node-ssh_exec="nodeProps">
              <div class="custom-node ssh-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🖥️</span><span class="cn-label">{{ nodeProps.data?.label || 'SSH' }}</span></div>
            </template>
            <template #node-log_analyze="nodeProps">
              <div class="custom-node log-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📋</span><span class="cn-label">{{ nodeProps.data?.label || '日志分析' }}</span></div>
            </template>
            <template #node-backup="nodeProps">
              <div class="custom-node backup-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">💾</span><span class="cn-label">{{ nodeProps.data?.label || '备份' }}</span></div>
            </template>
            <template #node-data_merge="nodeProps">
              <div class="custom-node merge-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔗</span><span class="cn-label">{{ nodeProps.data?.label || '数据合并' }}</span></div>
            </template>
            <template #node-deduplicate="nodeProps">
              <div class="custom-node dedup-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">✂️</span><span class="cn-label">{{ nodeProps.data?.label || '去重' }}</span></div>
            </template>
            <template #node-pivot_table="nodeProps">
              <div class="custom-node pivot-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📊</span><span class="cn-label">{{ nodeProps.data?.label || '透视表' }}</span></div>
            </template>
            <template #node-correlation="nodeProps">
              <div class="custom-node corr-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📉</span><span class="cn-label">{{ nodeProps.data?.label || '相关性' }}</span></div>
            </template>
            <template #node-docx_read="nodeProps">
              <div class="custom-node docx-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📄</span><span class="cn-label">{{ nodeProps.data?.label || 'Word读' }}</span></div>
            </template>
            <template #node-docx_write="nodeProps">
              <div class="custom-node docx-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">📝</span><span class="cn-label">{{ nodeProps.data?.label || 'Word写' }}</span></div>
            </template>
            <template #node-encrypt="nodeProps">
              <div class="custom-node encrypt-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔒</span><span class="cn-label">{{ nodeProps.data?.label || '加密' }}</span></div>
            </template>
            <template #node-jwt_generate="nodeProps">
              <div class="custom-node jwt-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">🔑</span><span class="cn-label">{{ nodeProps.data?.label || 'JWT' }}</span></div>
            </template>
            <template #node-schedule_trigger="nodeProps">
              <div class="custom-node schedule-node"><Handle type="target" :position="Position.Left" /><Handle type="source" :position="Position.Right" /><span class="cn-icon">⏰</span><span class="cn-label">{{ nodeProps.data?.label || '定时' }}</span></div>
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
              <el-form-item label="选择子工作流">
                <el-select v-model="selectedNode.data.config.workflow_id" filterable placeholder="搜索并选择工作流" style="width:100%" @focus="fetchSubWorkflows">
                  <el-option v-for="wf in availableSubWorkflows" :key="wf.id || wf._id" :label="wf.name" :value="wf.id || wf._id" />
                </el-select>
              </el-form-item>
              <el-form-item label="已选" v-if="selectedNode.data.config.workflow_id">
                <el-tag size="small" type="info">{{ getWorkflowName(selectedNode.data.config.workflow_id) }}</el-tag>
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
            <template v-if="selectedNode.type === 'approval'">
              <el-form-item label="审批超时(秒)">
                <el-input-number v-model="selectedNode.data.config.timeout" :min="10" :max="3600" style="width:100%" />
              </el-form-item>
              <el-form-item label="审批回调URL">
                <el-input v-model="selectedNode.data.config.check_url" placeholder="http://..." />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'email_send'">
              <el-form-item label="SMTP服务器">
                <el-input v-model="selectedNode.data.config.smtp_host" placeholder="smtp.qq.com" />
              </el-form-item>
              <el-form-item label="SMTP端口">
                <el-input-number v-model="selectedNode.data.config.smtp_port" :min="1" :max="65535" style="width:100%" />
              </el-form-item>
              <el-form-item label="发件人邮箱">
                <el-input v-model="selectedNode.data.config.smtp_user" placeholder="your@qq.com" />
              </el-form-item>
              <el-form-item label="授权码">
                <el-input v-model="selectedNode.data.config.smtp_pass" type="password" show-password placeholder="SMTP授权码" />
              </el-form-item>
              <el-form-item label="收件人">
                <el-input v-model="selectedNode.data.config.to_addr" placeholder="recipient@example.com" />
              </el-form-item>
              <el-form-item label="邮件主题">
                <el-input v-model="selectedNode.data.config.subject" placeholder="用 {{变量名}} 引用" />
              </el-form-item>
              <el-form-item label="邮件内容">
                <el-input v-model="selectedNode.data.config.body" type="textarea" :rows="4" placeholder="{{变量名}}" />
              </el-form-item>
              <el-form-item label="HTML格式">
                <el-switch v-model="selectedNode.data.config.is_html" />
              </el-form-item>
              <el-form-item label="附件路径">
                <el-input v-model="selectedNode.data.config.attachments" type="textarea" :rows="2" placeholder="文件路径，多个用逗号分隔&#10;支持: {{n3.path}}, {{n4.result.path}}" />
                <div style="font-size:11px;color:#909399;margin-top:4px">引用上游节点生成的文件，如 {{节点ID.path}}</div>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'excel_write'">
              <el-form-item label="文件路径">
                <el-input v-model="selectedNode.data.config.file_path" placeholder="C:\report.xlsx 或 {{变量名}}" />
              </el-form-item>
              <el-form-item label="数据源">
                <el-input v-model="selectedNode.data.config.data" type="textarea" :rows="3" placeholder="{{变量名}} 或 JSON数组" />
              </el-form-item>
              <el-form-item label="Sheet名称">
                <el-input v-model="selectedNode.data.config.sheet_name" placeholder="Sheet1" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'chart_gen'">
              <el-form-item label="数据源">
                <el-input v-model="selectedNode.data.config.data" type="textarea" :rows="3" placeholder="{{变量名}} 或 JSON数组" />
              </el-form-item>
              <el-form-item label="图表类型">
                <el-select v-model="selectedNode.data.config.chart_type" style="width:100%">
                  <el-option label="柱状图" value="bar" />
                  <el-option label="折线图" value="line" />
                  <el-option label="饼图" value="pie" />
                  <el-option label="散点图" value="scatter" />
                </el-select>
              </el-form-item>
              <el-form-item label="标题">
                <el-input v-model="selectedNode.data.config.title" placeholder="图表标题" />
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'statistics'">
              <el-form-item label="数据源">
                <el-input v-model="selectedNode.data.config.data" type="textarea" :rows="3" placeholder="{{变量名}} 或 JSON数组" />
              </el-form-item>
              <el-form-item label="字段名">
                <el-input v-model="selectedNode.data.config.field" placeholder="amount" />
              </el-form-item>
              <el-form-item label="统计操作">
                <el-select v-model="selectedNode.data.config.operation" style="width:100%">
                  <el-option label="均值 (mean)" value="mean" />
                  <el-option label="中位数 (median)" value="median" />
                  <el-option label="标准差 (stdev)" value="stdev" />
                  <el-option label="方差 (variance)" value="variance" />
                  <el-option label="最小值 (min)" value="min" />
                  <el-option label="最大值 (max)" value="max" />
                  <el-option label="求和 (sum)" value="sum" />
                  <el-option label="计数 (count)" value="count" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'calendar_event'">
              <el-form-item label="事件标题">
                <el-input v-model="selectedNode.data.config.title" placeholder="会议" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="selectedNode.data.config.description" placeholder="事件描述" />
              </el-form-item>
              <el-form-item label="开始时间">
                <el-input v-model="selectedNode.data.config.start_time" placeholder="2026-06-25 10:00" />
              </el-form-item>
              <el-form-item label="结束时间">
                <el-input v-model="selectedNode.data.config.end_time" placeholder="2026-06-25 11:00" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'sentiment_analysis'">
              <el-form-item label="文本">
                <el-input v-model="selectedNode.data.config.text" type="textarea" :rows="3" placeholder="{{变量名}}" />
              </el-form-item>
              <el-form-item label="LLM Provider">
                <el-select v-model="selectedNode.data.config.provider" style="width:100%">
                  <el-option label="agnes" value="agnes" />
                  <el-option label="deepseek" value="deepseek" />
                  <el-option label="openai" value="openai" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'template_render'">
              <el-form-item label="模板内容">
                <el-input v-model="selectedNode.data.config.template" type="textarea" :rows="5" placeholder="甲方: {{party_a}}&#10;乙方: {{party_b}}" />
              </el-form-item>
              <el-form-item label="数据 (JSON)">
                <el-input v-model="selectedNode.data.config.data" type="textarea" :rows="3" placeholder='{"party_a": "张三", "party_b": "李四"}' />
              </el-form-item>
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="可选，自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'ssh_exec'">
              <el-form-item label="主机地址">
                <el-input v-model="selectedNode.data.config.host" placeholder="192.168.1.100" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="selectedNode.data.config.port" :min="1" :max="65535" style="width:100%" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="selectedNode.data.config.username" placeholder="root" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="selectedNode.data.config.password" type="password" show-password />
              </el-form-item>
              <el-form-item label="执行命令">
                <el-input v-model="selectedNode.data.config.command" type="textarea" :rows="2" placeholder="ls -la 或 {{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'log_analyze'">
              <el-form-item label="日志文件路径">
                <el-input v-model="selectedNode.data.config.file_path" placeholder="C:\app.log 或 {{变量名}}" />
              </el-form-item>
              <el-form-item label="关键词">
                <el-input v-model="selectedNode.data.config.keyword" placeholder="ERROR" />
              </el-form-item>
              <el-form-item label="最大扫描行数">
                <el-input-number v-model="selectedNode.data.config.max_lines" :min="100" :max="100000" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'backup'">
              <el-form-item label="源路径">
                <el-input v-model="selectedNode.data.config.source" placeholder="C:\data 或 {{变量名}}" />
              </el-form-item>
              <el-form-item label="目标路径">
                <el-input v-model="selectedNode.data.config.dest" placeholder="自动生成" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'data_merge'">
              <el-form-item label="左数据变量">
                <el-input v-model="selectedNode.data.config.left_var" placeholder="left" />
              </el-form-item>
              <el-form-item label="右数据变量">
                <el-input v-model="selectedNode.data.config.right_var" placeholder="right" />
              </el-form-item>
              <el-form-item label="左键名">
                <el-input v-model="selectedNode.data.config.left_key" placeholder="id" />
              </el-form-item>
              <el-form-item label="右键名">
                <el-input v-model="selectedNode.data.config.right_key" placeholder="id" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'deduplicate'">
              <el-form-item label="数据变量">
                <el-input v-model="selectedNode.data.config.data_var" placeholder="input" />
              </el-form-item>
              <el-form-item label="去重字段">
                <el-input v-model="selectedNode.data.config.field" placeholder="留空则按整条去重" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'pivot_table'">
              <el-form-item label="数据变量">
                <el-input v-model="selectedNode.data.config.data_var" placeholder="input" />
              </el-form-item>
              <el-form-item label="分组字段">
                <el-input v-model="selectedNode.data.config.group_by" placeholder="region" />
              </el-form-item>
              <el-form-item label="聚合字段">
                <el-input v-model="selectedNode.data.config.agg_field" placeholder="amount" />
              </el-form-item>
              <el-form-item label="聚合函数">
                <el-select v-model="selectedNode.data.config.agg_func" style="width:100%">
                  <el-option label="求和 (sum)" value="sum" />
                  <el-option label="计数 (count)" value="count" />
                  <el-option label="平均值 (avg)" value="avg" />
                  <el-option label="最大值 (max)" value="max" />
                  <el-option label="最小值 (min)" value="min" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'correlation'">
              <el-form-item label="X数据变量">
                <el-input v-model="selectedNode.data.config.x_var" placeholder="x" />
              </el-form-item>
              <el-form-item label="Y数据变量">
                <el-input v-model="selectedNode.data.config.y_var" placeholder="y" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'docx_read'">
              <el-form-item label="文件路径">
                <el-input v-model="selectedNode.data.config.file_path" placeholder="C:\doc.docx 或 {{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'docx_write'">
              <el-form-item label="保存路径">
                <el-input v-model="selectedNode.data.config.save_path" placeholder="自动生成" />
              </el-form-item>
              <el-form-item label="文档标题">
                <el-input v-model="selectedNode.data.config.title" placeholder="文档标题" />
              </el-form-item>
              <el-form-item label="文档内容">
                <el-input v-model="selectedNode.data.config.content" type="textarea" :rows="5" placeholder="{{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'encrypt'">
              <el-form-item label="操作">
                <el-select v-model="selectedNode.data.config.action" style="width:100%">
                  <el-option label="加密" value="encrypt" />
                  <el-option label="解密" value="decrypt" />
                </el-select>
              </el-form-item>
              <el-form-item label="密钥">
                <el-input v-model="selectedNode.data.config.key" placeholder="留空自动生成" />
              </el-form-item>
              <el-form-item label="输入内容">
                <el-input v-model="selectedNode.data.config.text" type="textarea" :rows="3" placeholder="{{变量名}}" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'jwt_generate'">
              <el-form-item label="载荷 (JSON)">
                <el-input v-model="selectedNode.data.config.payload" type="textarea" :rows="3" placeholder='{"user_id": "1001", "role": "admin"}' />
              </el-form-item>
              <el-form-item label="密钥">
                <el-input v-model="selectedNode.data.config.secret" placeholder="your-secret-key" />
              </el-form-item>
              <el-form-item label="过期时间(分钟)">
                <el-input-number v-model="selectedNode.data.config.expire_minutes" :min="1" :max="1440" style="width:100%" />
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'schedule_trigger'">
              <el-form-item label="触发类型">
                <el-select v-model="selectedNode.data.config.schedule_type" style="width:100%">
                  <el-option label="间隔执行" value="interval" />
                  <el-option label="Cron表达式" value="cron" />
                </el-select>
              </el-form-item>
              <el-form-item label="间隔(秒)" v-if="selectedNode.data.config.schedule_type === 'interval'">
                <el-input-number v-model="selectedNode.data.config.interval" :min="1" :max="86400" style="width:100%" />
              </el-form-item>
              <el-form-item label="Cron表达式" v-if="selectedNode.data.config.schedule_type === 'cron'">
                <el-input v-model="selectedNode.data.config.cron" placeholder="0 9 * * 1-5" />
              </el-form-item>
            </template>
            <el-button type="danger" size="small" @click="removeNode" style="width:100%;margin-top:8px">删除节点</el-button>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 运行历史对话框 -->
    <el-dialog v-model="showRunsDialog" title="运行历史" width="800px">
      <div v-if="viewingRunDetail">
        <el-button size="small" @click="viewingRunDetail = null" style="margin-bottom:12px">← 返回列表</el-button>
        <div style="margin-bottom:8px">
          <el-tag :type="viewingRunDetail.status === 'completed' ? 'success' : 'danger'" size="small">{{ viewingRunDetail.status }}</el-tag>
          <span style="font-size:12px;color:#909399;margin-left:8px">{{ viewingRunDetail.created_at }}</span>
        </div>
        <div v-if="viewingRunDetail.node_results" class="node-results-tree">
          <div v-for="(res, nid) in viewingRunDetail.node_results" :key="nid" class="node-result-item">
            <div class="node-result-header">
              <span class="node-result-status" :class="getStatusClass(res)">{{ getStatusIcon(res) }}</span>
              <span class="node-result-id">{{ nid }}</span>
            </div>
            <div v-if="res && res.error" class="node-result-error">{{ res.error }}</div>
            <div v-else-if="res && res.result" class="node-result-output">{{ truncate(JSON.stringify(res.result), 300) }}</div>
          </div>
        </div>
      </div>
      <div v-else>
        <el-table :data="runLogs" v-loading="loadingRuns" size="small" max-height="400">
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="160" />
          <el-table-column label="节点数" width="80">
            <template #default="{ row }">{{ Object.keys(row.node_results || {}).length }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" link @click="viewRunDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showRunsDialog = false; viewingRunDetail = null">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 变量管理对话框 -->
    <el-dialog v-model="showVariablesDialog" title="工作流变量" width="600px">
      <div style="margin-bottom:8px;font-size:12px;color:#909399">在节点配置中用 <code>{{variables.变量名}}</code> 引用</div>
      <el-table :data="wfVariables" size="small" max-height="300">
        <el-table-column label="变量名" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" placeholder="变量名" />
          </template>
        </el-table-column>
        <el-table-column label="默认值" min-width="150">
          <template #default="{ row }">
            <el-input v-model="row.value" size="small" placeholder="默认值" />
          </template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-select v-model="row.type" size="small">
              <el-option label="字符串" value="string" />
              <el-option label="数字" value="number" />
              <el-option label="布尔" value="boolean" />
              <el-option label="JSON" value="json" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ $index }">
            <el-button size="small" type="danger" link @click="removeVariable($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" type="primary" @click="addVariable" style="margin-top:8px">+ 添加变量</el-button>
      <template #footer>
        <el-button @click="showVariablesDialog = false">取消</el-button>
        <el-button type="primary" @click="currentWf.variables = wfVariables; showVariablesDialog = false; ElMessage.success('变量已保存')">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI创建工作流对话框 -->
    <el-dialog v-model="showAiDialog" title="AI智能创建工作流" width="600px">
      <div style="margin-bottom:12px;font-size:13px;color:#606266">用自然语言描述你想要的工作流，AI会自动为你生成。</div>
      <el-input v-model="aiDescription" type="textarea" :rows="5" placeholder="例如：帮我创建一个工作流，读取CSV销售数据，过滤金额大于10000的记录，按金额排序，然后用LLM生成分析报告，最后导出为PDF" />
      <div style="margin-top:8px;font-size:12px;color:#909399">支持的节点：LLM、工具调用、条件分支、循环、数据处理、图表生成、文档导出等66种节点</div>
      <template #footer>
        <el-button @click="showAiDialog = false">取消</el-button>
        <el-button type="primary" :loading="aiGenerating" @click="generateByAI">{{ aiGenerating ? 'AI生成中...' : 'AI生成' }}</el-button>
      </template>
    </el-dialog>

    <!-- 模板库对话框 -->
    <el-dialog v-model="showTemplateDialog" title="工作流模板库" width="700px">
      <div v-for="cat in templateCategories" :key="cat.label" style="margin-bottom:16px">
        <div style="font-weight:600;margin-bottom:8px;color:#303133">{{ cat.label }}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div v-for="tpl in cat.templates" :key="tpl.name" class="template-card" @click="applyTemplate(tpl)">
            <div style="font-weight:500;font-size:13px;margin-bottom:4px">{{ tpl.name }}</div>
            <div style="font-size:11px;color:#909399">{{ tpl.desc }}</div>
            <div style="font-size:11px;color:#b0b0b0;margin-top:4px">{{ tpl.nodes }} 个节点</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTemplateDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 执行输入对话框 -->
    <el-dialog v-model="showRunDialog" title="执行工作流" width="600px">
      <el-tabs v-model="runInputMode">
        <el-tab-pane label="表单输入" name="form">
          <el-form label-position="top" size="small">
            <el-form-item label="input (工作流输入参数)">
              <el-input v-model="runFormInput" type="textarea" :rows="4" placeholder="输入内容，如文本、URL、JSON数据等" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="JSON输入" name="json">
          <el-form label-position="top" size="small">
            <el-form-item label="输入参数 (JSON)">
              <el-input v-model="runInputs" type="textarea" :rows="6" placeholder='{"input": "你的输入内容"}' />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <div v-if="runResult">
        <el-divider />
        <div style="font-size:13px;color:#606266;margin-bottom:8px">执行结果</div>
        <el-tag :type="runResult.status === 'completed' ? 'success' : 'danger'" size="small" style="margin-bottom:8px">{{ runResult.status }}</el-tag>
        <div v-if="runResult.node_results" class="node-results-tree">
          <div v-for="(res, nid) in runResult.node_results" :key="nid" class="node-result-item">
            <div class="node-result-header">
              <span class="node-result-status" :class="getStatusClass(res)">{{ getStatusIcon(res) }}</span>
              <span class="node-result-id">{{ nid }}</span>
              <span v-if="res && res.elapsed" class="node-result-time">{{ res.elapsed }}ms</span>
            </div>
            <div v-if="res && res.error" class="node-result-error">{{ res.error }}</div>
            <div v-else-if="res && res.result" class="node-result-output">{{ truncate(JSON.stringify(res.result), 200) }}</div>
          </div>
        </div>
        <pre v-else style="background:#f5f7fa;padding:12px;border-radius:6px;font-size:12px;max-height:300px;overflow:auto;white-space:pre-wrap">{{ JSON.stringify(runResult.outputs || runResult, null, 2) }}</pre>
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
const selectedWorkflows = ref([])
const batchMode = ref(false)
const currentPage = ref(1)
const pageSize = ref(15)
const paginatedWorkflows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return workflows.value.slice(start, start + pageSize.value)
})
const editing = ref(false)
const wfVariables = ref([])
const showVariablesDialog = ref(false)

const loadVariables = () => {
  wfVariables.value = currentWf.value.variables || []
}

const addVariable = () => {
  wfVariables.value.push({ name: '', value: '', type: 'string' })
}

const removeVariable = (idx) => {
  wfVariables.value.splice(idx, 1)
}
const saving = ref(false)
const currentWf = ref({ name: '', nodes: [], edges: [], status: 'draft' })
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)
const availableSubWorkflows = ref([])

const fetchSubWorkflows = async () => {
  try {
    const { data } = await getWorkflows()
    availableSubWorkflows.value = (data.workflows || []).filter(wf => {
      const wfId = wf.id || wf._id
      const currentId = currentWf.value?.id || currentWf.value?._id
      return wfId !== currentId
    })
  } catch (e) { /* ignore */ }
}

const loadingSmartConfig = ref(false)

const loadSmartConfig = async () => {
  if (!selectedNode.value || !currentWf.value) return
  loadingSmartConfig.value = true
  try {
    const resp = await fetch(`/api/v1/workflows/${currentWf.value.id || currentWf.value._id}/suggest-config/${selectedNode.value.id}`)
    const data = await resp.json()
    if (data.suggestions) {
      Object.assign(selectedNode.value.data.config, data.suggestions)
      ElMessage.success('已应用推荐配置')
    }
  } catch (e) { ElMessage.error('获取推荐失败') }
  finally { loadingSmartConfig.value = false }
}

const getWorkflowName = (wfId) => {
  const wf = availableSubWorkflows.value.find(w => (w.id || w._id) === wfId)
  return wf ? wf.name : wfId
}

const nodeSearchQuery = ref('')
const nodeCategory = ref('all')
const nodeCategories = [
  { value: 'all', label: '全部' },
  { value: 'data', label: '数据处理' },
  { value: 'ai', label: 'AI/LLM' },
  { value: 'tool', label: '工具' },
  { value: 'control', label: '控制流' },
  { value: 'office', label: '办公' },
  { value: 'devops', label: '运维' },
  { value: 'security', label: '安全' },
  { value: 'format', label: '数据格式' },
]
const nodeCategoryMap = {
  data: ['csv_parse','data_filter','data_sort','data_merge','deduplicate','pivot_table','correlation','statistics','excel_read','excel_write'],
  ai: ['llm','text_translate','text_summarize','sentiment_analysis','text_embedding','image_gen','image_process','speech_to_text','text_to_speech'],
  tool: ['tool','file_operation','webhook','code_exec','file_watcher'],
  control: ['start','output','condition','switch','loop','parallel','delay','retry','error_handler','sub_workflow','approval','schedule_trigger'],
  office: ['docx_read','docx_write','pdf_generate','template_render','chart_gen','calendar_event','email_send','notify','text_split','markdown_html'],
  devops: ['ssh_exec','log_analyze','backup','network_ping','http_stream','websocket_connect','database'],
  security: ['encrypt','jwt_generate','hash_encode','qrcode_gen','qrcode_scan','url_shorten','regex_replace'],
  format: ['json_build','json_parse','json_diff','type_convert','uuid_generate','math_calc','datetime','regex'],
}
const undoStack = ref([])
const redoStack = ref([])
const pushUndo = () => {
  undoStack.value.push(JSON.stringify({ nodes: nodes.value, edges: edges.value }))
  if (undoStack.value.length > 50) undoStack.value.shift()
  redoStack.value = []
}
const undo = () => {
  if (undoStack.value.length === 0) return
  redoStack.value.push(JSON.stringify({ nodes: nodes.value, edges: edges.value }))
  const prev = JSON.parse(undoStack.value.pop())
  nodes.value = prev.nodes
  edges.value = prev.edges
}
const redo = () => {
  if (redoStack.value.length === 0) return
  undoStack.value.push(JSON.stringify({ nodes: nodes.value, edges: edges.value }))
  const next = JSON.parse(redoStack.value.pop())
  nodes.value = next.nodes
  edges.value = next.edges
}

const filteredNodeTypes = computed(() => {
  let list = nodeTypes
  if (nodeCategory.value !== 'all') {
    const cats = nodeCategoryMap[nodeCategory.value] || []
    list = list.filter(nt => cats.includes(nt.type))
  }
  if (nodeSearchQuery.value) {
    const q = nodeSearchQuery.value.toLowerCase()
    list = list.filter(nt => nt.label.toLowerCase().includes(q) || nt.type.toLowerCase().includes(q))
  }
  return list
})

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
  { type: 'approval', label: '审批节点', icon: '✅', color: '#f0f9eb' },
  { type: 'email_send', label: '发送邮件', icon: '📧', color: '#ecf5ff' },
  { type: 'excel_write', label: 'Excel写入', icon: '📗', color: '#f0f9eb' },
  { type: 'chart_gen', label: '图表生成', icon: '📊', color: '#fdf6ec' },
  { type: 'statistics', label: '统计计算', icon: '📈', color: '#f0f9eb' },
  { type: 'calendar_event', label: '日历事件', icon: '📅', color: '#ecf5ff' },
  { type: 'sentiment_analysis', label: '情感分析', icon: '💭', color: '#fef0f0' },
  { type: 'template_render', label: '模板渲染', icon: '📝', color: '#f4f4f5' },
  { type: 'ssh_exec', label: 'SSH远程', icon: '🖥️', color: '#fef0f0' },
  { type: 'log_analyze', label: '日志分析', icon: '📋', color: '#fdf6ec' },
  { type: 'backup', label: '数据备份', icon: '💾', color: '#ecf5ff' },
  { type: 'data_merge', label: '数据合并', icon: '🔗', color: '#f4f4f5' },
  { type: 'deduplicate', label: '数据去重', icon: '✂️', color: '#fef0f0' },
  { type: 'pivot_table', label: '透视表', icon: '📊', color: '#f0f9eb' },
  { type: 'correlation', label: '相关性分析', icon: '📉', color: '#fdf6ec' },
  { type: 'docx_read', label: 'Word读取', icon: '📄', color: '#ecf5ff' },
  { type: 'docx_write', label: 'Word写入', icon: '📝', color: '#f4f4f5' },
  { type: 'encrypt', label: '加密解密', icon: '🔒', color: '#fef0f0' },
  { type: 'jwt_generate', label: 'JWT生成', icon: '🔑', color: '#fdf6ec' },
  { type: 'schedule_trigger', label: '定时触发', icon: '⏰', color: '#ecf5ff' },
]

const showRunDialog = ref(false)
const runInputMode = ref('form')
const runFormInput = ref('')
const runInputs = ref('{\n  "input": "测试输入"\n}')
const runResult = ref(null)
const running = ref(false)
const runTarget = ref(null)

const showRunsDialog = ref(false)
const runLogs = ref([])
const loadingRuns = ref(false)
const viewingRunDetail = ref(null)

const viewRuns = async (wf) => {
  showRunsDialog.value = true
  loadingRuns.value = true
  try {
    const { data } = await getWorkflowRuns(wf.id || wf._id)
    runLogs.value = data.runs || []
  } catch (e) { ElMessage.error('加载运行记录失败') }
  finally { loadingRuns.value = false }
}

const viewRunDetail = async (run) => {
  viewingRunDetail.value = run
}

const showAiDialog = ref(false)
const aiDescription = ref('')
const aiGenerating = ref(false)

const generateByAI = async () => {
  if (!aiDescription.value.trim()) return ElMessage.warning('请输入需求描述')
  aiGenerating.value = true
  try {
    const { data } = await apiPost('/workflows/ai-generate', { description: aiDescription.value })
    showAiDialog.value = false
    ElMessage.success('AI工作流已生成')
    fetchWorkflows()
  } catch (e) { ElMessage.error('生成失败: ' + (e.detail || e.message || JSON.stringify(e))) }
  finally { aiGenerating.value = false }
}

const showTemplateDialog = ref(false)
const templateCategories = [
  { label: '运维', templates: [
    { name: '系统巡检日报', desc: '执行命令+日志分析+LLM报告+PDF', nodes: 9 },
    { name: '服务健康监控', desc: 'Ping+HTTP+日志+条件+告警', nodes: 8 },
    { name: '日志智能分析', desc: '扫描+正则+统计+LLM+Word+PDF', nodes: 8 },
    { name: '自动化部署验证', desc: '进程+端口+重试+日志+LLM', nodes: 7 },
  ]},
  { label: '数据', templates: [
    { name: 'CSV数据分析', desc: '解析+过滤+排序+统计+图表', nodes: 6 },
    { name: '报表生成器', desc: '代码生成+Excel+图表+LLM', nodes: 5 },
    { name: '数据清洗管线', desc: 'HTTP+正则+条件+LLM', nodes: 6 },
    { name: '多源数据整合', desc: '合并+去重+透视+图表', nodes: 5 },
  ]},
  { label: '办公', templates: [
    { name: '周报生成器', desc: '分割+LLM润色+PDF+HTML', nodes: 7 },
    { name: '合同模板生成', desc: '模板渲染+Word+日历', nodes: 5 },
    { name: '会议纪要', desc: '分割+LLM+翻译+PDF+HTML', nodes: 6 },
    { name: '审批文档流程', desc: 'LLM+审批+Word', nodes: 4 },
  ]},
  { label: 'AI', templates: [
    { name: 'RAG知识问答', desc: '知识库+LLM+摘要+UUID+JSON', nodes: 8 },
    { name: '智能内容路由', desc: 'LLM分类+条件+专家LLM', nodes: 6 },
    { name: '客户反馈分析', desc: '情感分析+条件+LLM回复', nodes: 5 },
    { name: '多格式导出', desc: 'LLM+并行+HTML+PDF+JSON', nodes: 6 },
  ]},
]

const applyTemplate = async (tpl) => {
  const templateData = templateWorkflows[tpl.name]
  if (!templateData) { ElMessage.warning('模板暂未实现'); return }
  try {
    const { data } = await apiCreate({ name: tpl.name, description: tpl.desc, nodes: templateData.nodes, edges: templateData.edges })
    showTemplateDialog.value = false
    ElMessage.success('模板已创建: ' + tpl.name)
    fetchWorkflows()
  } catch (e) { ElMessage.error('创建失败') }
}

const templateWorkflows = {
  '系统巡检日报': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'tool', label: '磁盘空间', position: { x: 250, y: 100 }, config: { tool_name: 'run_command', input_template: 'wmic logicaldisk get size,freespace,caption /format:csv', timeout: 15 } },
      { id: 'n2', type: 'tool', label: '内存使用', position: { x: 250, y: 250 }, config: { tool_name: 'run_command', input_template: 'systeminfo | findstr /C:"Total Physical Memory"', timeout: 15 } },
      { id: 'n3', type: 'log_analyze', label: '日志分析', position: { x: 500, y: 100 }, config: { keyword: 'error', max_lines: 2000 } },
      { id: 'n4', type: 'statistics', label: '错误统计', position: { x: 500, y: 250 }, config: { data: '[{"count":3},{"count":1},{"count":5}]', 'field': 'count', 'operation': 'mean' } },
      { id: 'n5', type: 'llm', label: '生成报告', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '生成系统巡检日报:\n磁盘: {{n1.result}}\n内存: {{n2.result}}\n错误数: {{n3.count}}' } },
      { id: 'n6', type: 'pdf_generate', label: 'PDF报告', position: { x: 1000, y: 150 }, config: { input_template: '{{n5.response}}', title: 'System Check Report' } },
      { id: 'n7', type: 'backup', label: '备份日志', position: { x: 1000, y: 300 }, config: { source: './backend.log' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1200, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 's1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n3', target: 'n5' }, { id: 'e6', source: 'n4', target: 'n5' },
      { id: 'e7', source: 'n5', target: 'n6' }, { id: 'e8', source: 'n3', target: 'n7' },
      { id: 'e9', source: 'n6', target: 'e1' }, { id: 'e10', source: 'n7', target: 'e1' }
    ]
  },
  '服务健康监控': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'network_ping', label: 'Ping检测', position: { x: 250, y: 100 }, config: { input_template: '127.0.0.1', count: 3 } },
      { id: 'n2', type: 'tool', label: 'HTTP探测', position: { x: 250, y: 250 }, config: { tool_name: 'http', method: 'GET', input_template: '{{s1.input}}', timeout: 10 } },
      { id: 'n3', type: 'log_analyze', label: '日志扫描', position: { x: 250, y: 400 }, config: { keyword: 'error', max_lines: 1000 } },
      { id: 'n4', type: 'condition', label: 'HTTP正常?', position: { x: 500, y: 200 }, config: { condition: 'n2.status_code', operator: 'eq', value: '200' } },
      { id: 'n5', type: 'llm', label: '分析告警', position: { x: 750, y: 150 }, config: { provider: 'agnes', prompt: '分析服务异常:\nPing: {{n1.success}}\nHTTP: {{n2.status_code}}\n错误: {{n3.count}}' } },
      { id: 'n6', type: 'backup', label: '备份日志', position: { x: 750, y: 350 }, config: { source: './backend.log' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 's1', target: 'n2' },
      { id: 'e3', source: 's1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n4', target: 'n5', sourceHandle: 'true' },
      { id: 'e6', source: 'n3', target: 'n6' },
      { id: 'e7', source: 'n5', target: 'e1' }, { id: 'e8', source: 'n6', target: 'e1' }
    ]
  },
  'CSV数据分析': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'csv_parse', label: '解析CSV', position: { x: 250, y: 200 }, config: { delimiter: ',', has_header: true, input_template: '{{s1.input}}' } },
      { id: 'n2', type: 'data_filter', label: '过滤数据', position: { x: 500, y: 100 }, config: { data_var: 'n1.result', operator: 'gt', value: '0' } },
      { id: 'n3', type: 'statistics', label: '统计计算', position: { x: 500, y: 250 }, config: { data: '{{n1.result}}', operation: 'mean' } },
      { id: 'n4', type: 'chart_gen', label: '生成图表', position: { x: 750, y: 200 }, config: { data: '{{n1.result}}', chart_type: 'bar', title: '数据分析' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n3', target: 'n4' }, { id: 'e6', source: 'n4', target: 'e1' }
    ]
  },
  '报表生成器': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'code_exec', label: '生成数据', position: { x: 250, y: 200 }, config: { language: 'python', code: 'import json\nprint(json.dumps([{"month":"Jan","sales":100},{"month":"Feb","sales":150},{"month":"Mar","sales":200}]))', timeout: 10 } },
      { id: 'n2', type: 'excel_write', label: '写入Excel', position: { x: 500, y: 100 }, config: { data: '{{n1.result}}', sheet_name: 'Sheet1' } },
      { id: 'n3', type: 'chart_gen', label: '生成图表', position: { x: 500, y: 250 }, config: { data: '{{n1.result}}', chart_type: 'bar', title: '销售报表' } },
      { id: 'n4', type: 'llm', label: '分析报告', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '分析以下销售数据:\n{{n1.result}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n3', target: 'n4' }, { id: 'e6', source: 'n4', target: 'e1' }
    ]
  },
  '周报生成器': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'text_split', label: '拆分工作项', position: { x: 250, y: 200 }, config: { delimiter: ';', text: '{{s1.input}}' } },
      { id: 'n2', type: 'llm', label: '润色内容', position: { x: 500, y: 200 }, config: { provider: 'agnes', prompt: '将以下工作项润色为正式周报:\n{{n1.items}}' } },
      { id: 'n3', type: 'datetime', label: '当前日期', position: { x: 500, y: 350 }, config: { action: 'now', format: '%Y年第%W周' } },
      { id: 'n4', type: 'pdf_generate', label: '生成PDF', position: { x: 750, y: 150 }, config: { input_template: '周报 - {{n3.result}}\n\n{{n2.response}}', title: 'Weekly Report' } },
      { id: 'n5', type: 'markdown_html', label: '生成HTML', position: { x: 750, y: 300 }, config: { input_template: '# 周报 - {{n3.result}}\n\n{{n2.response}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 's1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n2', target: 'n5' }, { id: 'e6', source: 'n3', target: 'n4' },
      { id: 'e7', source: 'n3', target: 'n5' }, { id: 'e8', source: 'n4', target: 'e1' },
      { id: 'e9', source: 'n5', target: 'e1' }
    ]
  },
  'RAG知识问答': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'tool', label: '知识库检索', position: { x: 250, y: 200 }, config: { tool_name: 'knowledge_search', input_template: '{{s1.input}}', top_k: 5 } },
      { id: 'n2', type: 'llm', label: 'RAG回答', position: { x: 500, y: 200 }, config: { provider: 'agnes', prompt: '基于检索结果回答:\n{{n1.results}}\n问题: {{s1.input}}' } },
      { id: 'n3', type: 'text_summarize', label: '摘要', position: { x: 750, y: 100 }, config: { max_length: 200, input_template: '{{n2.response}}' } },
      { id: 'n4', type: 'uuid_generate', label: '生成ID', position: { x: 750, y: 250 }, config: {} },
      { id: 'n5', type: 'datetime', label: '时间戳', position: { x: 750, y: 380 }, config: { action: 'now' } },
      { id: 'n6', type: 'json_build', label: '构建记录', position: { x: 1000, y: 200 }, config: { fields: '{"id":"{{n4.uuid}}","question":"{{s1.input}}","answer":"{{n2.response}}","time":"{{n5.result}}"}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1200, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n6' },
      { id: 'e5', source: 'n3', target: 'n6' }, { id: 'e6', source: 'n4', target: 'n6' },
      { id: 'e7', source: 'n5', target: 'n6' }, { id: 'e8', source: 'n6', target: 'e1' }
    ]
  },
  '智能内容路由': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'llm', label: '意图识别', position: { x: 250, y: 200 }, config: { provider: 'agnes', prompt: '判断用户意图，只回答一个词：代码/翻译/写作\n用户: {{s1.input}}' } },
      { id: 'n2', type: 'switch', label: '路由分发', position: { x: 500, y: 200 }, config: { switch_var: '{{n1.response}}' } },
      { id: 'n3', type: 'llm', label: '代码专家', position: { x: 750, y: 80 }, config: { provider: 'agnes', prompt: '你是代码专家，请生成代码:\n{{s1.input}}' } },
      { id: 'n4', type: 'llm', label: '翻译专家', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '你是翻译专家，请翻译:\n{{s1.input}}' } },
      { id: 'n5', type: 'llm', label: '写作专家', position: { x: 750, y: 320 }, config: { provider: 'agnes', prompt: '你是写作专家，请写作:\n{{s1.input}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3', sourceHandle: 'case1' },
      { id: 'e4', source: 'n2', target: 'n4', sourceHandle: 'default' },
      { id: 'e5', source: 'n2', target: 'n5' },
      { id: 'e6', source: 'n3', target: 'e1' }, { id: 'e7', source: 'n4', target: 'e1' },
      { id: 'e8', source: 'n5', target: 'e1' }
    ]
  },
  '客户反馈分析': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'sentiment_analysis', label: '情感分析', position: { x: 250, y: 200 }, config: { text: '{{s1.input}}' } },
      { id: 'n2', type: 'condition', label: '是否负面?', position: { x: 500, y: 200 }, config: { condition: 'n1.score', operator: 'lt', value: '0' } },
      { id: 'n3', type: 'llm', label: '生成回复', position: { x: 750, y: 100 }, config: { provider: 'agnes', prompt: '客户反馈: {{s1.input}}\n情感: {{n1.result}}\n请生成专业回复' } },
      { id: 'n4', type: 'transform', label: '记录正面', position: { x: 750, y: 300 }, config: { expression: "'正面反馈已记录'" } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3', sourceHandle: 'true' },
      { id: 'e4', source: 'n2', target: 'n4', sourceHandle: 'false' },
      { id: 'e5', source: 'n3', target: 'e1' }, { id: 'e6', source: 'n4', target: 'e1' }
    ]
  },
  '多格式导出': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'llm', label: '生成内容', position: { x: 250, y: 200 }, config: { provider: 'agnes', prompt: '围绕以下主题生成500字文章:\n{{s1.input}}' } },
      { id: 'n2', type: 'markdown_html', label: '转HTML', position: { x: 500, y: 100 }, config: { input_template: '{{n1.response}}' } },
      { id: 'n3', type: 'pdf_generate', label: '生成PDF', position: { x: 500, y: 250 }, config: { input_template: '{{n1.response}}', title: 'AI Document' } },
      { id: 'n4', type: 'json_build', label: 'JSON输出', position: { x: 500, y: 400 }, config: { fields: '{"title":"{{s1.input}}","content":"{{n1.response}}"}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 750, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n1', target: 'n4' },
      { id: 'e5', source: 'n2', target: 'e1' }, { id: 'e6', source: 'n3', target: 'e1' },
      { id: 'e7', source: 'n4', target: 'e1' }
    ]
  },
  '日志智能分析': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'log_analyze', label: '扫描ERROR', position: { x: 250, y: 150 }, config: { keyword: 'error', max_lines: 5000 } },
      { id: 'n2', type: 'statistics', label: '错误统计', position: { x: 250, y: 350 }, config: { data: '[{"count":12},{"count":5},{"count":3}]', 'field': 'count', 'operation': 'sum' } },
      { id: 'n3', type: 'chart_gen', label: '错误图表', position: { x: 500, y: 200 }, config: { data: '[{"type":"auth","count":12},{"type":"timeout","count":5}]', chart_type: 'pie', title: 'Error Distribution' } },
      { id: 'n4', type: 'llm', label: '分析建议', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '分析日志错误:\n错误数: {{n1.count}}\n总和: {{n2.result}}' } },
      { id: 'n5', type: 'docx_write', label: 'Word报告', position: { x: 1000, y: 100 }, config: { title: 'Log Report', content: '{{n4.response}}' } },
      { id: 'n6', type: 'backup', label: '备份', position: { x: 1000, y: 300 }, config: { source: './backend.log' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1200, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n3', target: 'n4' }, { id: 'e6', source: 'n4', target: 'n5' },
      { id: 'e7', source: 'n4', target: 'n6' }, { id: 'e8', source: 'n5', target: 'e1' },
      { id: 'e9', source: 'n6', target: 'e1' }
    ]
  },
  '合同模板生成': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'template_render', label: '渲染模板', position: { x: 250, y: 200 }, config: { template: '甲方: {{party_a}}\n乙方: {{party_b}}\n金额: {{amount}}元', data: '{"party_a":"甲方","party_b":"乙方","amount":"50000"}' } },
      { id: 'n2', type: 'docx_write', label: '生成Word', position: { x: 500, y: 100 }, config: { title: '服务合同', content: '{{n1.result}}' } },
      { id: 'n3', type: 'calendar_event', label: '签约日程', position: { x: 500, y: 300 }, config: { title: '合同签约', start_time: '2026-06-25 10:00', end_time: '2026-06-25 11:00' } },
      { id: 'n4', type: 'hash_encode', label: '文档哈希', position: { x: 750, y: 200 }, config: { algorithm: 'md5', input_template: '{{n1.result}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 's1', target: 'n3' }, { id: 'e4', source: 'n1', target: 'n4' },
      { id: 'e5', source: 'n2', target: 'e1' }, { id: 'e6', source: 'n3', target: 'e1' },
      { id: 'e7', source: 'n4', target: 'e1' }
    ]
  },
  '会议纪要': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'text_split', label: '拆分议题', position: { x: 250, y: 200 }, config: { delimiter: '|', text: '{{s1.input}}' } },
      { id: 'n2', type: 'llm', label: '议题总结', position: { x: 500, y: 200 }, config: { provider: 'agnes', prompt: '总结会议议题:\n{{n1.items}}' } },
      { id: 'n3', type: 'text_translate', label: '英文翻译', position: { x: 500, y: 350 }, config: { text: '{{n2.response}}', target_lang: 'English' } },
      { id: 'n4', type: 'pdf_generate', label: 'PDF纪要', position: { x: 750, y: 150 }, config: { input_template: '{{n2.response}}', title: 'Meeting Minutes' } },
      { id: 'n5', type: 'markdown_html', label: 'HTML纪要', position: { x: 750, y: 300 }, config: { input_template: '# 会议纪要\n\n{{n2.response}}\n\n## English\n\n{{n3.result}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n4' },
      { id: 'e5', source: 'n3', target: 'n5' }, { id: 'e6', source: 'n4', target: 'n5' },
      { id: 'e7', source: 'n5', target: 'e1' }
    ]
  },
  '审批文档流程': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'llm', label: '生成方案', position: { x: 250, y: 200 }, config: { provider: 'agnes', prompt: '为以下需求生成方案:\n{{s1.input}}' } },
      { id: 'n2', type: 'approval', label: '主管审批', position: { x: 500, y: 200 }, config: { timeout: 10 } },
      { id: 'n3', type: 'docx_write', label: '生成文档', position: { x: 750, y: 200 }, config: { title: '项目方案', content: '{{n1.response}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3' }, { id: 'e4', source: 'n3', target: 'e1' }
    ]
  },
  '自动化部署验证': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'tool', label: '检查进程', position: { x: 250, y: 100 }, config: { tool_name: 'run_command', input_template: 'tasklist /fi "imagename eq python.exe" /fo csv /nh', timeout: 10 } },
      { id: 'n2', type: 'tool', label: '检查端口', position: { x: 250, y: 250 }, config: { tool_name: 'run_command', input_template: 'netstat -ano | findstr :8000', timeout: 10 } },
      { id: 'n3', type: 'log_analyze', label: '启动日志', position: { x: 500, y: 150 }, config: { keyword: 'startup', max_lines: 1000 } },
      { id: 'n4', type: 'llm', label: '部署报告', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '部署检查结果:\n进程: {{n1.result}}\n端口: {{n2.result}}\n启动日志: {{n3.result}}' } },
      { id: 'n5', type: 'hash_encode', label: '校验码', position: { x: 750, y: 350 }, config: { algorithm: 'sha256', input_template: '{{n4.response}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 's1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n3' },
      { id: 'e5', source: 'n3', target: 'n4' }, { id: 'e6', source: 'n4', target: 'n5' },
      { id: 'e7', source: 'n5', target: 'e1' }
    ]
  },
  '数据清洗管线': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'tool', label: 'HTTP抓取', position: { x: 250, y: 200 }, config: { tool_name: 'http', method: 'GET', input_template: '{{s1.input}}', timeout: 30 } },
      { id: 'n2', type: 'tool', label: '正则提取', position: { x: 500, y: 100 }, config: { tool_name: 'regex', pattern: '\\d{4}-\\d{2}-\\d{2}', input_template: '{{n1.body}}' } },
      { id: 'n3', type: 'condition', label: '有数据?', position: { x: 500, y: 300 }, config: { condition: 'n2.count', operator: 'gt', value: '0' } },
      { id: 'n4', type: 'llm', label: 'LLM分析', position: { x: 750, y: 200 }, config: { provider: 'agnes', prompt: '分析数据:\n匹配: {{n2.matches}}\n原始: {{n1.body}}' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 1000, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 'n1', target: 'n2' },
      { id: 'e3', source: 'n2', target: 'n3' }, { id: 'e4', source: 'n3', target: 'n4', sourceHandle: 'true' },
      { id: 'e5', source: 'n4', target: 'e1' }
    ]
  },
  '多源数据整合': {
    nodes: [
      { id: 's1', type: 'start', label: '输入', position: { x: 50, y: 200 }, config: {} },
      { id: 'n1', type: 'code_exec', label: '数据源A', position: { x: 200, y: 100 }, config: { language: 'python', code: 'import json\nprint(json.dumps([{"id":"P1","name":"产品A","q1":100},{"id":"P2","name":"产品B","q1":200}]))', timeout: 10 } },
      { id: 'n2', type: 'code_exec', label: '数据源B', position: { x: 200, y: 300 }, config: { language: 'python', code: 'import json\nprint(json.dumps([{"id":"P1","price":50},{"id":"P2","price":80}]))', timeout: 10 } },
      { id: 'n3', type: 'data_merge', label: '合并数据', position: { x: 450, y: 200 }, config: { left_var: 'n1.result', right_var: 'n2.result', left_key: 'id', right_key: 'id' } },
      { id: 'n4', type: 'chart_gen', label: '生成图表', position: { x: 700, y: 200 }, config: { data: '{{n3.result}}', chart_type: 'bar', title: '产品销售额' } },
      { id: 'e1', type: 'output', label: '输出', position: { x: 950, y: 200 }, config: {} }
    ],
    edges: [
      { id: 'e1', source: 's1', target: 'n1' }, { id: 'e2', source: 's1', target: 'n2' },
      { id: 'e3', source: 'n1', target: 'n3' }, { id: 'e4', source: 'n2', target: 'n3' },
      { id: 'e5', source: 'n3', target: 'n4' }, { id: 'e6', source: 'n4', target: 'e1' }
    ]
  },
}

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

// Keyboard shortcuts
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo() }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); redo() }
  })
}

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) selectedWorkflows.value = []
}

const batchDelete = async () => {
  if (selectedWorkflows.value.length === 0) return ElMessage.warning('请先选择工作流')
  try {
    await ElMessageBox.confirm(`确定删除 ${selectedWorkflows.value.length} 个工作流?`, '批量删除', { type: 'warning' })
    for (const wf of selectedWorkflows.value) {
      await apiDelete(wf.id || wf._id)
    }
    ElMessage.success('批量删除成功')
    selectedWorkflows.value = []
    batchMode.value = false
    fetchWorkflows()
  } catch (e) { if (e !== 'cancel') ElMessage.error('批量删除失败') }
}

const batchExport = async () => {
  if (selectedWorkflows.value.length === 0) return ElMessage.warning('请先选择工作流')
  const exportData = []
  for (const wf of selectedWorkflows.value) {
    try {
      const { data } = await apiExport(wf.id || wf._id)
      exportData.push(data)
    } catch (e) { /* skip */ }
  }
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflows_batch_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success(`已导出 ${exportData.length} 个工作流`)
}

const apiPost = async (url, data) => {
  const resp = await fetch(`/api/v1${url}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!resp.ok) {
    const text = await resp.text()
    try { throw JSON.parse(text) } catch { throw new Error(text || `HTTP ${resp.status}`) }
  }
  return { data: await resp.json() }
}

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

const getStatusClass = (res) => {
  if (!res) return 'pending'
  if (res.error) return 'error'
  return 'success'
}
const getStatusIcon = (res) => {
  if (!res) return '⏳'
  if (res.error) return '❌'
  return '✅'
}
const truncate = (str, len) => str && str.length > len ? str.slice(0, len) + '...' : str

const runWf = () => {
  runFormInput.value = ''
  runInputMode.value = 'form'
  runTarget.value = currentWf.value
  runResult.value = null
  runInputs.value = '{\n  "input": "测试输入"\n}'
  showRunDialog.value = true
}

const handleMore = (cmd, row) => {
  if (cmd === 'log') viewRuns(row)
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
    if (runInputMode.value === 'form') {
      inputs = { input: runFormInput.value }
    } else {
    try { inputs = JSON.parse(runInputs.value) } catch (e) { ElMessage.warning('JSON 格式错误'); running.value = false; return }
}
    const { data } = await apiRun(runTarget.value.id || runTarget.value._id, inputs)
    runResult.value = data
    ElMessage.success('执行完成')
  } catch (e) { ElMessage.error('执行失败') } finally { running.value = false }
}

const onDragStart = (event, type) => {
  event.dataTransfer.setData('application/node-type', type)
  event.dataTransfer.effectAllowed = 'move'
}

const onDrop = (event) => {
  pushUndo()
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
  const incomingEdges = edges.value.filter(e => e.target === selectedNode.value.id)
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
const handleNodeClick = ({ node }) => {
  selectedNode.value = node
}
const handlePaneClick = () => {
  selectedNode.value = null
}
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
    a.download = `${wf.name || 'workflow'}.json`
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
.node-search-input { width: 100%; padding: 6px 10px; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 12px; margin-bottom: 8px; outline: none; }
.node-search-input:focus { border-color: #409eff; }
.node-category-bar { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.node-cat-tag { padding: 2px 8px; font-size: 11px; border-radius: 10px; cursor: pointer; background: #f0f2f5; color: #606266; border: 1px solid transparent; }
.node-cat-tag.active { background: #ecf5ff; color: #409eff; border-color: #b3d8ff; }
.node-cat-tag:hover { background: #e9e9e9; }
.node-list-scroll { max-height: calc(100vh - 260px); overflow-y: auto; }
.node-results-tree { max-height: 300px; overflow-y: auto; }
.node-result-item { padding: 6px 8px; margin-bottom: 4px; border-radius: 4px; background: #fafafa; border-left: 3px solid #dcdfe6; }
.node-result-item:has(.success) { border-left-color: #67c23a; }
.node-result-item:has(.error) { border-left-color: #f56c6c; }
.node-result-header { display: flex; align-items: center; gap: 6px; font-size: 12px; }
.node-result-status { font-size: 12px; }
.node-result-id { font-weight: 500; color: #303133; }
.node-result-time { color: #909399; font-size: 11px; margin-left: auto; }
.node-result-error { color: #f56c6c; font-size: 11px; margin-top: 4px; word-break: break-all; }
.node-result-output { color: #606266; font-size: 11px; margin-top: 4px; word-break: break-all; max-height: 60px; overflow: hidden; }
.template-card { padding: 10px 12px; border: 1px solid #e4e7ed; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.template-card:hover { border-color: #409eff; background: #ecf5ff; }
</style>
