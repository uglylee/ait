"""
LangChain 集成模块
提供 LLM包装、Memory、Chains、RAG、Agents、Tools 等完整功能
"""

import os
import json
from typing import List, Dict, Optional, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool

# ============ 1. LLM 包装器 ============

class UniversalChatLLM:
    """通用 LLM 包装器，支持所有已配置的提供商"""

    def __init__(self, provider: str = "deepseek", model: str = None, temperature: float = 0.7, max_tokens: int = 2048):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _get_provider_config(self):
        from llm_config import llm_router
        router = llm_router
        if self.provider not in router.providers:
            raise ValueError(f"Provider {self.provider} not available")
        p = router.providers[self.provider]
        return {
            "api_key": p.api_key,
            "base_url": p.base_url,
            "model": self.model or p.default_model
        }

    def invoke(self, messages: List, **kwargs) -> str:
        """同步调用"""
        import httpx
        config = self._get_provider_config()
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{config['base_url']}/v1/chat/completions",
                headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                json={"model": config["model"], "messages": formatted_messages, "temperature": self.temperature, "max_tokens": self.max_tokens}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def ainvoke(self, messages: List, **kwargs) -> str:
        """异步调用"""
        import httpx
        config = self._get_provider_config()
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{config['base_url']}/v1/chat/completions",
                headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                json={"model": config["model"], "messages": formatted_messages, "temperature": self.temperature, "max_tokens": self.max_tokens}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


# ============ 2. 对话记忆 ============

class ConversationMemory:
    """对话记忆管理"""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history

    def load_history(self, messages: List[Dict]) -> List:
        """从数据库消息加载历史"""
        history = []
        recent = messages[-self.max_history:] if len(messages) > self.max_history else messages
        for msg in recent:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))
        return history

    def build_messages(self, system_prompt: str, history: List, user_input: str) -> List:
        """构建完整消息列表"""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.extend(history)
        messages.append(HumanMessage(content=user_input))
        return messages


# ============ 3. 提示词模板 ============

class PromptTemplates:
    """常用提示词模板"""

    CHAT = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    RAG = ChatPromptTemplate.from_messages([
        ("system", "你是一个智能助手。根据以下上下文回答用户的问题。如果上下文中没有相关信息，请说明。\n\n上下文：\n{context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    SUMMARIZE = ChatPromptTemplate.from_messages([
        ("system", "请对以下内容进行总结，输出简洁的摘要。"),
        ("human", "{text}")
    ])

    TRANSLATE = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业翻译助手。将以下文本翻译成{target_language}。"),
        ("human", "{text}")
    ])

    CODE_REVIEW = ChatPromptTemplate.from_messages([
        ("system", "你是一个资深代码审查专家。分析以下代码，指出问题并给出改进建议。"),
        ("human", "{code}")
    ])

    @staticmethod
    def create_custom(template: str) -> ChatPromptTemplate:
        """创建自定义模板"""
        return ChatPromptTemplate.from_template(template)


# ============ 4. 链 (Chains) ============

class Chains:
    """常用链"""

    @staticmethod
    def simple_chat(llm, system_prompt: str = "你是一个有帮助的助手"):
        """简单对话链"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        return prompt | llm | StrOutputParser()

    @staticmethod
    def rag_chain(llm):
        """RAG 检索增强链"""
        prompt = PromptTemplates.RAG
        return prompt | llm | StrOutputParser()

    @staticmethod
    def summarize_chain(llm):
        """摘要链"""
        prompt = PromptTemplates.SUMMARIZE
        return prompt | llm | StrOutputParser()

    @staticmethod
    def sequential_chains(llm, prompts: List[str]):
        """顺序链 - 多步处理"""
        chain = RunnablePassthrough()
        for p in prompts:
            template = ChatPromptTemplate.from_template(p)
            chain = chain | template | llm | StrOutputParser()
        return chain


# ============ 5. RAG 检索增强生成 ============

class RAGManager:
    """RAG 管理器"""

    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embeddings = None

    def init_embeddings(self):
        """初始化嵌入模型"""
        if self.embeddings is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def init_vectorstore(self, collection_name: str = "default"):
        """初始化向量数据库"""
        import chromadb
        from langchain_community.vectorstores import Chroma
        self.init_embeddings()
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = Chroma(
            client=self.chroma_client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
        return self.collection

    def add_documents(self, texts: List[str], metadatas: List[Dict] = None, collection_name: str = "default"):
        """添加文档"""
        self.init_vectorstore(collection_name)
        from langchain_core.documents import Document
        docs = [Document(page_content=t, metadata=metadatas[i] if metadatas else {}) for i, t in enumerate(texts)]
        self.collection.add_documents(docs)
        return len(docs)

    def add_text(self, text: str, chunk_size: int = 500, overlap: int = 50, collection_name: str = "default"):
        """添加长文本（自动分割）"""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = splitter.split_text(text)
        return self.add_documents(chunks, collection_name=collection_name)

    def search(self, query: str, k: int = 5, collection_name: str = "default"):
        """检索相似文档"""
        self.init_vectorstore(collection_name)
        results = self.collection.similarity_search_with_score(query, k=k)
        return [{"content": doc.page_content, "score": float(score), "metadata": doc.metadata} for doc, score in results]

    def as_retriever(self, k: int = 4):
        """转换为 LangChain retriever"""
        self.init_vectorstore()
        return self.collection.as_retriever(search_kwargs={"k": k})

    def delete_collection(self, collection_name: str = "default"):
        """删除集合"""
        if self.chroma_client:
            self.chroma_client.delete_collection(collection_name)


# ============ 6. 工具 ============

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入: 数学表达式字符串，如 '2 + 3 * 4'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def python_repl(code: str) -> str:
    """执行 Python 代码。输入: Python 代码字符串"""
    import io
    import contextlib
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {"__builtins__": __builtins__})
        return output.getvalue() or "代码执行成功（无输出）"
    except Exception as e:
        return f"执行错误: {str(e)}"

@tool
def web_search(query: str) -> str:
    """搜索网络信息（模拟）。输入: 搜索关键词"""
    return f"搜索结果: 关于 '{query}' 的信息需要网络连接才能获取。"

@tool
def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def word_count(text: str) -> str:
    """统计文本字数"""
    return f"字数: {len(text)}"

TOOLS = [calculator, python_repl, web_search, get_current_time, word_count]


# ============ 7. Agent ============

class SimpleAgent:
    """简单 Agent（基于规则的工具调用）"""

    def __init__(self, llm, tools: List = None, system_prompt: str = None):
        self.llm = llm
        self.tools = {t.name: t for t in (tools or TOOLS)}
        self.system_prompt = system_prompt or "你是一个有帮助的AI助手，可以使用工具来完成任务。"

    def _parse_tool_call(self, text: str):
        """解析工具调用"""
        import re
        pattern = r'(\w+)\((.*?)\)'
        matches = re.findall(pattern, text)
        for name, args_str in matches:
            if name in self.tools:
                args = args_str.strip().strip('"').strip("'")
                return name, args
        return None, None

    def invoke(self, query: str, history: List = None) -> str:
        """执行 Agent"""
        tool_list = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        system = f"""{self.system_prompt}

你可以使用以下工具：
{tool_list}

如果需要使用工具，在回复中包含: TOOL_CALL: 工具名(参数)
如果不需要工具，直接回答问题。"""

        messages = [SystemMessage(content=system)]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=query))

        response = self.llm.invoke(messages)
        tool_name, tool_args = self._parse_tool_call(response)

        if tool_name and tool_name in self.tools:
            tool_result = self.tools[tool_name].invoke(tool_args)
            follow_up = [SystemMessage(content=f"工具 {tool_name} 返回: {tool_result}\n请基于这个结果回答用户的问题。")]
            messages.append(AIMessage(content=response))
            messages.extend(follow_up)
            final_response = self.llm.invoke(messages)
            return final_response

        return response


# ============ 8. 文档加载器 ============

class DocumentLoaders:
    """文档加载器"""

    @staticmethod
    def from_text(text: str) -> List[Dict]:
        return [{"content": text, "metadata": {"source": "text"}}]

    @staticmethod
    def from_file(file_path: str) -> List[Dict]:
        """加载文件"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return DocumentLoaders._load_pdf(file_path)
        elif ext in ['.txt', '.md', '.py', '.js', '.json']:
            return DocumentLoaders._load_text(file_path)
        elif ext in ['.csv']:
            return DocumentLoaders._load_csv(file_path)
        return [{"content": f"不支持的文件格式: {ext}", "metadata": {"source": file_path}}]

    @staticmethod
    def _load_text(file_path: str) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [{"content": content, "metadata": {"source": file_path, "type": "text"}}]

    @staticmethod
    def _load_pdf(file_path: str) -> List[Dict]:
        try:
            import PyPDF2
            docs = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    docs.append({"content": page.extract_text(), "metadata": {"source": file_path, "page": i}})
            return docs
        except ImportError:
            return [{"content": "需要安装 PyPDF2: pip install PyPDF2", "metadata": {"source": file_path}}]

    @staticmethod
    def _load_csv(file_path: str) -> List[Dict]:
        import csv
        docs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                docs.append({"content": " | ".join(row), "metadata": {"source": file_path, "row": i}})
        return docs


# ============ 全局实例 ============

rag_manager = RAGManager()
