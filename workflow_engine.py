import os
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class WorkflowNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str  # start, llm, tool, condition, transform, output
    label: str = ""
    config: Dict[str, Any] = {}
    position: Dict[str, float] = {"x": 0, "y": 0}


class WorkflowEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str
    target: str
    sourceHandle: Optional[str] = None


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "未命名工作流"
    description: str = ""
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class WorkflowRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: str = "running"
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    node_results: Dict[str, Any] = {}
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    finished_at: Optional[str] = None
    error: Optional[str] = None


_workflows_col = None
_runs_col = None


def _get_cols():
    global _workflows_col, _runs_col
    if _workflows_col is None:
        from pymongo import MongoClient
        MONGO_URL = os.environ.get("MONGODB_URL", "mongodb://ai_mongo:ai_mongo_2024@localhost:27017")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
        db = client["ai_framework"]
        _workflows_col = db["workflows"]
        _runs_col = db["workflow_runs"]
    return _workflows_col, _runs_col


def list_workflows() -> List[Dict]:
    col, _ = _get_cols()
    results = []
    for doc in col.find().sort("updated_at", -1):
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results


def get_workflow(workflow_id: str) -> Optional[Dict]:
    col, _ = _get_cols()
    doc = col.find_one({"_id": workflow_id})
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def create_workflow(data: dict) -> Dict:
    col, _ = _get_cols()
    wf = Workflow(**data)
    doc = wf.model_dump()
    doc["_id"] = doc.pop("id")
    col.insert_one(doc)
    doc["id"] = doc["_id"]
    return doc


def update_workflow(workflow_id: str, data: dict) -> bool:
    col, _ = _get_cols()
    data["updated_at"] = datetime.now().isoformat()
    result = col.update_one({"_id": workflow_id}, {"$set": data})
    return result.modified_count > 0


def delete_workflow(workflow_id: str) -> bool:
    col, _ = _get_cols()
    result = col.delete_one({"_id": workflow_id})
    return result.deleted_count > 0


def save_run(run: WorkflowRun):
    _, runs_col = _get_cols()
    doc = {
        "_id": run.id,
        "workflow_id": run.workflow_id,
        "status": run.status,
        "inputs": run.inputs,
        "outputs": {},
        "node_results": {},
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "error": run.error
    }
    runs_col.insert_one(doc)


def update_run(run: WorkflowRun):
    _, runs_col = _get_cols()
    data = run.model_dump()
    data.pop("id", None)
    runs_col.update_one({"_id": run.id}, {"$set": {"status": data["status"], "outputs": data["outputs"], "node_results": data["node_results"], "finished_at": data.get("finished_at"), "error": data.get("error")}})


def get_runs(workflow_id: str, limit: int = 20) -> List[Dict]:
    _, runs_col = _get_cols()
    results = []
    for doc in runs_col.find({"workflow_id": workflow_id}).sort("started_at", -1).limit(limit):
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results


def get_run(run_id: str) -> Optional[Dict]:
    _, runs_col = _get_cols()
    doc = runs_col.find_one({"_id": run_id})
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def _topological_sort(nodes: List[dict], edges: List[dict]) -> List[List[str]]:
    in_degree = {n["id"]: 0 for n in nodes}
    children = {n["id"]: [] for n in nodes}
    for e in edges:
        in_degree[e["target"]] = in_degree.get(e["target"], 0) + 1
        children[e["source"]].append(e["target"])

    levels = []
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    while queue:
        levels.append(queue[:])
        next_queue = []
        for nid in queue:
            for child in children.get(nid, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_queue.append(child)
        queue = next_queue
    return levels


def _resolve_var(name: str, context: dict) -> str:
    """从 context 中解析变量，支持 {{key}} 和 {{node_id.field}} 两种格式"""
    def _extract(val):
        if isinstance(val, dict):
            if "response" in val:
                return str(val["response"])
            if "result" in val:
                return str(val["result"])
            if "stdout" in val:
                return str(val["stdout"])
            if "output" in val:
                inner = val["output"]
                if isinstance(inner, dict) and "response" in inner:
                    return str(inner["response"])
                if isinstance(inner, dict) and "result" in inner:
                    return str(inner["result"])
                if isinstance(inner, dict) and "stdout" in inner:
                    return str(inner["stdout"])
                return json.dumps(inner, ensure_ascii=False) if not isinstance(inner, str) else inner
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, list):
            return json.dumps(val, ensure_ascii=False)
        return str(val)

    if name in context:
        return _extract(context[name])
    parts = name.split(".", 1)
    if len(parts) == 2:
        node_id, field = parts
        if node_id in context:
            val = context[node_id]
            if isinstance(val, dict) and field in val:
                return _extract(val[field])
    return "{" + name + "}"


def _replace_vars(template: str, context: dict) -> str:
    """替换模板中的 {{变量名}}，支持嵌套字段访问"""
    import re
    def _replacer(m):
        return _resolve_var(m.group(1), context)
    return re.sub(r"\{\{(.+?)\}\}", _replacer, template)


def _execute_node(node: dict, context: dict, llm_router=None) -> Any:
    ntype = node["type"]
    config = node.get("config", {})

    if ntype == "start":
        return context.get("inputs", {})

    elif ntype == "llm":
        if not llm_router:
            return {"error": "LLM router not available"}
        provider = config.get("provider", "agnes")
        prompt = config.get("prompt", "")
        messages = []
        if prompt:
            prompt = _replace_vars(prompt, context)
            messages.append({"role": "user", "content": prompt})
        else:
            user_input = context.get("input", context.get("text", ""))
            messages.append({"role": "user", "content": str(user_input)})

        import asyncio
        import threading

        result_container = [None]
        error_container = [None]

        def _run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                async def _call():
                    result = ""
                    async for chunk in llm_router.chat_stream(messages, provider=provider):
                        if chunk == "[DONE]":
                            continue
                        if chunk.startswith('{"type": "reasoning"'):
                            continue
                        result += chunk
                    return result
                result_container[0] = new_loop.run_until_complete(_call())
            except Exception as e:
                error_container[0] = str(e)
            finally:
                new_loop.close()

        t = threading.Thread(target=_run_in_thread)
        t.start()
        t.join(timeout=120)

        if error_container[0]:
            return {"error": error_container[0]}
        return {"response": result_container[0]}

    elif ntype == "tool":
        tool_name = config.get("tool_name", "")
        tool_input = config.get("input_template", "")
        tool_input = _replace_vars(tool_input, context)

        if tool_name == "ocr":
            try:
                from ocr_engine import ocr_recognize
                import base64 as b64
                ocr_source = config.get("ocr_source", "context")
                if ocr_source == "path":
                    file_path = tool_input.strip()
                    if not file_path or not os.path.exists(file_path):
                        return {"error": f"文件不存在: {file_path}"}
                    with open(file_path, "rb") as f:
                        img_bytes = f.read()
                    return ocr_recognize(img_bytes)
                elif ocr_source == "base64":
                    file_data = tool_input.strip()
                    if not file_data:
                        return {"error": "未提供 base64 图像数据"}
                    if file_data.startswith("data:"):
                        file_data = file_data.split(",", 1)[1]
                    img_bytes = b64.b64decode(file_data)
                    return ocr_recognize(img_bytes)
                else:
                    file_data = context.get("file_data") or context.get("file_base64") or context.get("image_base64", "")
                    if file_data:
                        if file_data.startswith("data:"):
                            file_data = file_data.split(",", 1)[1]
                        img_bytes = b64.b64decode(file_data)
                        return ocr_recognize(img_bytes)
                    elif tool_input:
                        if os.path.exists(tool_input):
                            with open(tool_input, "rb") as f:
                                img_bytes = f.read()
                            return ocr_recognize(img_bytes)
                        return {"error": f"文件不存在: {tool_input}"}
                    return {"error": "OCR 需要提供文件路径或 base64 图像数据"}
            except Exception as e:
                return {"error": f"OCR 失败: {str(e)}"}

        elif tool_name == "http":
            import httpx
            method = config.get("method", "GET").upper()
            url = tool_input or config.get("url", "")
            headers_str = config.get("headers", "")
            body = config.get("body", "")
            timeout_val = int(config.get("timeout", 30))

            url = _replace_vars(url, context)
            body = _replace_vars(body, context)

            headers = {}
            if headers_str:
                try:
                    headers = json.loads(headers_str) if headers_str.strip().startswith("{") else dict(
                        line.split(":", 1) for line in headers_str.strip().split("\n") if ":" in line
                    )
                except Exception:
                    headers = {}

            try:
                with httpx.Client(timeout=timeout_val, follow_redirects=True) as client:
                    kwargs = {"url": url, "headers": headers}
                    if method in ("POST", "PUT", "PATCH"):
                        if body:
                            try:
                                kwargs["json"] = json.loads(body)
                            except Exception:
                                kwargs["data"] = body
                    resp = client.request(method, **kwargs)
                    try:
                        resp_data = resp.json()
                    except Exception:
                        resp_data = resp.text
                    return {
                        "status_code": resp.status_code,
                        "headers": dict(resp.headers),
                        "body": resp_data
                    }
            except httpx.TimeoutException:
                return {"error": f"HTTP 请求超时 ({timeout_val}s)"}
            except Exception as e:
                return {"error": f"HTTP 请求失败: {str(e)}"}

        elif tool_name == "knowledge_search":
            try:
                from langchain_engine import get_rag_engine
                rag = get_rag_engine()
                top_k = int(config.get("top_k", 3))
                results = rag.search(tool_input, top_k=top_k)
                return {"results": results}
            except Exception as e:
                return {"error": str(e)}

        elif tool_name == "text_extract":
            try:
                result = tool_input[:int(config.get("max_length", 5000))]
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}

        elif tool_name == "regex":
            import re
            pattern = config.get("pattern", "")
            text = tool_input
            try:
                matches = re.findall(pattern, text)
                return {"matches": matches, "count": len(matches)}
            except re.error as e:
                return {"error": f"正则表达式错误: {str(e)}"}

        elif tool_name == "json_parse":
            try:
                data = json.loads(tool_input)
                path = config.get("path", "")
                if path:
                    for key in path.split("."):
                        if key.isdigit():
                            data = data[int(key)]
                        else:
                            data = data[key]
                return {"result": data}
            except Exception as e:
                return {"error": f"JSON 解析失败: {str(e)}"}

        elif tool_name == "run_command":
            import subprocess
            import platform
            cmd = tool_input
            if not cmd:
                return {"error": "命令为空"}
            timeout_val = int(config.get("timeout", 30))
            system = platform.system().lower()
            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout_val)
                stdout = proc.stdout
                stderr = proc.stderr
                if system == "windows":
                    for enc in ["gbk", "gb2312", "utf-8", "latin-1"]:
                        try:
                            stdout = proc.stdout.decode(enc)
                            stderr = proc.stderr.decode(enc)
                            break
                        except (UnicodeDecodeError, LookupError):
                            continue
                else:
                    stdout = proc.stdout.decode("utf-8", errors="replace")
                    stderr = proc.stderr.decode("utf-8", errors="replace")
                output = stdout[:5000]
                return {
                    "result": output,
                    "stdout": output,
                    "stderr": stderr[:2000],
                    "returncode": proc.returncode
                }
            except subprocess.TimeoutExpired:
                return {"error": f"命令执行超时 ({timeout_val}s)"}
            except Exception as e:
                return {"error": f"命令执行失败: {str(e)}"}

        elif tool_name == "open_app":
            import subprocess
            import platform
            import shutil
            app_name = tool_input.strip()
            if not app_name:
                return {"error": "应用名称为空"}
            system = platform.system().lower()
            app_map = {
                "notepad": "notepad.exe",
                "记事本": "notepad.exe",
                "calculator": "calc.exe",
                "计算器": "calc.exe",
                "paint": "mspaint.exe",
                "画图": "mspaint.exe",
                "explorer": "explorer.exe",
                "文件管理器": "explorer.exe",
                "cmd": "cmd.exe",
                "终端": "cmd.exe",
                "powershell": "powershell.exe",
                "chrome": "chrome",
                "谷歌浏览器": "chrome",
                "edge": "msedge",
                "edge浏览器": "msedge",
                "firefox": "firefox",
                "火狐": "firefox",
                "vscode": "code",
                "vs code": "code",
                "word": "winword",
                "excel": "excel",
                "ppt": "powerpnt",
                "terminal": "wt.exe",
            }
            resolved = app_map.get(app_name.lower(), app_name)
            try:
                if system == "windows":
                    if resolved.endswith(".exe"):
                        subprocess.Popen(f"start {resolved}", shell=True)
                    else:
                        try:
                            subprocess.Popen(["cmd", "/c", "start", "", resolved], shell=False)
                        except FileNotFoundError:
                            found = shutil.which(resolved)
                            if found:
                                subprocess.Popen([found], shell=False)
                            else:
                                subprocess.Popen(f"start {resolved}", shell=True)
                elif system == "darwin":
                    subprocess.Popen(["open", "-a", app_name])
                else:
                    subprocess.Popen([app_name])
                return {"result": f"已启动: {app_name}", "app": app_name, "resolved": resolved}
            except Exception as e:
                return {"error": f"启动应用失败: {str(e)}"}

        elif tool_name == "file_read":
            try:
                file_path = tool_input.strip()
                if not file_path or not os.path.exists(file_path):
                    return {"error": f"文件不存在: {file_path}"}
                encoding = config.get("encoding", "utf-8")
                max_size = int(config.get("max_size", 10000))
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read(max_size)
                return {"result": content, "path": file_path, "size": os.path.getsize(file_path)}
            except Exception as e:
                return {"error": f"读取文件失败: {str(e)}"}

        elif tool_name == "send_email":
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = config.get("smtp_host", "smtp.qq.com")
            smtp_port = int(config.get("smtp_port", 465))
            smtp_user = config.get("smtp_user", "")
            smtp_pass = config.get("smtp_pass", "")
            use_ssl = config.get("use_ssl", True)

            if not smtp_user or not smtp_pass:
                return {"error": "未配置 SMTP 账号或密码"}

            to_addr = config.get("to_addr", "")
            subject = config.get("subject", "")
            body = tool_input
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict):
                    if "result" in parsed:
                        body = str(parsed["result"])
                    elif "response" in parsed:
                        body = str(parsed["response"])
                    elif "stdout" in parsed:
                        body = str(parsed["stdout"])
            except (json.JSONDecodeError, TypeError):
                pass
            body = body.encode('utf-8', errors='replace').decode('utf-8', errors='replace')

            if not to_addr:
                return {"error": "未配置收件人"}

            to_addr = _replace_vars(to_addr, context)
            subject = _replace_vars(subject, context)

            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
                else:
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                    server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_addr.split(","), msg.as_string())
                server.quit()
                return {"result": f"邮件已发送", "to": to_addr, "subject": subject}
            except smtplib.SMTPAuthenticationError:
                return {"error": "SMTP 认证失败，请检查账号密码"}
            except smtplib.SMTPConnectError:
                return {"error": f"无法连接 SMTP 服务器 {smtp_host}:{smtp_port}"}
            except Exception as e:
                return {"error": f"发送邮件失败: {str(e)}"}

        elif tool_name == "file_write":
            try:
                file_path = config.get("file_path", "")
                file_path = _replace_vars(file_path, context)
                if not file_path:
                    return {"error": "未指定写入路径"}
                write_mode = config.get("write_mode", "overwrite")
                content = tool_input
                os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
                if write_mode == "append" and os.path.exists(file_path):
                    with open(file_path, "a", encoding="utf-8", errors="replace") as f:
                        f.write(content)
                else:
                    with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                        f.write(content)
                return {"result": f"已写入文件", "path": file_path, "size": len(content.encode("utf-8")), "mode": write_mode}
            except Exception as e:
                return {"error": f"写入文件失败: {str(e)}"}

        elif tool_name == "pdf_extract":
            try:
                pdf_path = tool_input.strip()
                if not pdf_path or not os.path.exists(pdf_path):
                    return {"error": f"PDF 文件不存在: {pdf_path}"}
                try:
                    import fitz
                    doc = fitz.open(pdf_path)
                    pages = []
                    full_text = []
                    for i, page in enumerate(doc):
                        text = page.get_text()
                        pages.append({"page": i + 1, "text": text})
                        full_text.append(text)
                    doc.close()
                    return {"result": "\n".join(full_text), "pages": pages, "total_pages": len(pages)}
                except ImportError:
                    import subprocess
                    result = subprocess.run(
                        ["python", "-m", "PyPDF2"],
                        capture_output=True, timeout=5
                    )
                    raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")
            except ImportError as e:
                return {"error": f"PDF 解析库未安装: {str(e)}。请运行: pip install PyMuPDF"}
            except Exception as e:
                return {"error": f"PDF 解析失败: {str(e)}"}

        elif tool_name == "clipboard":
            try:
                import subprocess
                platform_name = __import__("platform").system().lower()
                action = config.get("action", "paste")
                if action == "paste":
                    if platform_name == "windows":
                        result = subprocess.run(["powershell", "-command", "Get-Clipboard"],
                                               capture_output=True, timeout=5, shell=False)
                        text = result.stdout.decode("utf-8", errors="replace").strip()
                    elif platform_name == "darwin":
                        result = subprocess.run(["pbpaste"], capture_output=True, timeout=5)
                        text = result.stdout.decode("utf-8", errors="replace").strip()
                    else:
                        result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                               capture_output=True, timeout=5)
                        text = result.stdout.decode("utf-8", errors="replace").strip()
                    return {"result": text}
                elif action == "copy":
                    text = tool_input
                    if platform_name == "windows":
                        subprocess.run(["powershell", "-command", f"Set-Clipboard -Value '{text}'"],
                                       timeout=5, shell=False)
                    elif platform_name == "darwin":
                        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                        proc.communicate(text.encode("utf-8"))
                    else:
                        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                        proc.communicate(text.encode("utf-8"))
                    return {"result": "已复制到剪贴板"}
                else:
                    return {"error": f"未知剪贴板操作: {action}"}
            except Exception as e:
                return {"error": f"剪贴板操作失败: {str(e)}"}

        elif tool_name == "screenshot":
            try:
                save_path = config.get("save_path", "")
                save_path = _replace_vars(save_path, context)
                if not save_path:
                    save_path = os.path.join("generated_media", f"screenshot_{int(__import__('time').time())}.png")
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                try:
                    import pyautogui
                    img = pyautogui.screenshot()
                    img.save(save_path)
                except ImportError:
                    import subprocess
                    if __import__("platform").system().lower() == "windows":
                        ps_cmd = (
                            "Add-Type -AssemblyName System.Windows.Forms; "
                            "$screen = [System.Windows.Forms.Screen]::PrimaryScreen; "
                            "$bmp = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height); "
                            "$gfx = [System.Drawing.Graphics]::FromImage($bmp); "
                            "$gfx.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size); "
                            f"$bmp.Save('{save_path}')"
                        )
                        subprocess.run(["powershell", "-command", ps_cmd], timeout=10, shell=False)
                    else:
                        return {"error": "截图需要安装 pyautogui: pip install pyautogui"}
                return {"result": f"截图已保存", "path": save_path}
            except Exception as e:
                return {"error": f"截图失败: {str(e)}"}

    elif ntype == "condition":
        condition = config.get("condition", "true")
        try:
            condition = _replace_vars(condition, context)
            result = eval(condition)
            return {"result": bool(result), "branch": "true" if result else "false"}
        except Exception:
            return {"result": False, "branch": "false"}

    elif ntype == "transform":
        template = config.get("template", "{{input}}")
        template = _replace_vars(template, context)
        return {"result": template}

    elif ntype == "delay":
        import time
        seconds = int(config.get("seconds", 3))
        seconds = min(seconds, 60)
        time.sleep(seconds)
        return {"result": f"waited {seconds} seconds"}

    elif ntype == "loop":
        list_var = config.get("list_var", "input")
        raw = context.get(list_var, context.get("inputs", {}).get(list_var, []))
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = [raw]
        if not isinstance(raw, list):
            raw = [raw]
        return {"items": raw, "count": len(raw), "current": raw[0] if raw else None}

    elif ntype == "parallel":
        upstream_results = {}
        for k, v in context.items():
            if k not in ("inputs",) and k != node_id:
                upstream_results[k] = v
        return {"results": upstream_results, "count": len(upstream_results)}

    elif ntype == "database":
        db_type = config.get("db_type", "mongodb")
        connection_string = _replace_vars(config.get("connection_string", ""), context)
        query = _replace_vars(config.get("query", ""), context)
        if not connection_string:
            return {"error": "未配置数据库连接字符串"}
        if not query:
            return {"error": "未配置查询语句"}
        try:
            if db_type == "mongodb":
                from pymongo import MongoClient
                client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
                db_name = config.get("db_name", "test")
                coll_name = config.get("collection", "test")
                coll = client[db_name][coll_name]
                query_obj = json.loads(query) if query.strip().startswith("{") else {}
                results = list(coll.find(query_obj).limit(100))
                for r in results:
                    r["_id"] = str(r["_id"])
                return {"result": results, "count": len(results)}
            elif db_type in ("mysql", "postgresql"):
                if db_type == "mysql":
                    import pymysql
                    conn = pymysql.connect(connection_string, connect_timeout=10)
                else:
                    import psycopg2
                    conn = psycopg2.connect(connection_string, connect_timeout=10)
                cursor = conn.cursor()
                cursor.execute(query)
                if cursor.description:
                    columns = [d[0] for d in cursor.description]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return {"result": rows, "count": len(rows)}
                else:
                    conn.commit()
                    return {"result": f"affected {cursor.rowcount} rows", "count": cursor.rowcount}
            else:
                return {"error": f"不支持的数据库类型: {db_type}"}
        except Exception as e:
            return {"error": f"数据库操作失败: {str(e)}"}

    elif ntype == "file_operation":
        operation = config.get("operation", "read")
        file_path = _replace_vars(config.get("path", ""), context)
        if not file_path:
            return {"error": "未配置文件路径"}
        try:
            if operation == "read":
                encoding = config.get("encoding", "utf-8")
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read(int(config.get("max_size", 50000)))
                return {"result": content, "path": file_path, "size": os.path.getsize(file_path)}
            elif operation == "write":
                content = _replace_vars(config.get("content", ""), context)
                os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"result": "写入成功", "path": file_path}
            elif operation == "copy":
                dest = _replace_vars(config.get("dest", ""), context)
                import shutil
                shutil.copy2(file_path, dest)
                return {"result": "复制成功", "src": file_path, "dest": dest}
            elif operation == "move":
                dest = _replace_vars(config.get("dest", ""), context)
                import shutil
                shutil.move(file_path, dest)
                return {"result": "移动成功", "src": file_path, "dest": dest}
            elif operation == "delete":
                if os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                return {"result": "删除成功", "path": file_path}
            elif operation == "list":
                items = os.listdir(file_path) if os.path.isdir(file_path) else [file_path]
                return {"result": items, "count": len(items), "path": file_path}
            else:
                return {"error": f"未知操作: {operation}"}
        except Exception as e:
            return {"error": f"文件操作失败: {str(e)}"}

    elif ntype == "webhook":
        import httpx
        method = config.get("method", "GET").upper()
        url = _replace_vars(config.get("url", ""), context)
        headers_str = config.get("headers", "")
        body = _replace_vars(config.get("body", ""), context)
        timeout_val = int(config.get("timeout", 30))
        if not url:
            return {"error": "未配置 URL"}
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str) if headers_str.strip().startswith("{") else dict(
                    line.split(":", 1) for line in headers_str.strip().split("\n") if ":" in line
                )
            except Exception:
                headers = {}
        try:
            with httpx.Client(timeout=timeout_val, follow_redirects=True) as client:
                kwargs = {"url": url, "headers": headers}
                if method in ("POST", "PUT", "PATCH"):
                    if body:
                        try:
                            kwargs["json"] = json.loads(body)
                        except Exception:
                            kwargs["data"] = body
                resp = client.request(method, **kwargs)
                try:
                    resp_data = resp.json()
                except Exception:
                    resp_data = resp.text
                return {"status_code": resp.status_code, "body": resp_data, "headers": dict(resp.headers)}
        except httpx.TimeoutException:
            return {"error": f"请求超时 ({timeout_val}s)"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

    elif ntype == "code_exec":
        language = config.get("language", "python")
        code = _replace_vars(config.get("code", ""), context)
        timeout_val = int(config.get("timeout", 30))
        if not code:
            return {"error": "代码为空"}
        import subprocess
        import tempfile
        try:
            if language == "python":
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                    f.write(code)
                    tmp_path = f.name
                proc = subprocess.run(
                    ["python", tmp_path], capture_output=True, timeout=timeout_val,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
            elif language in ("javascript", "js"):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
                    f.write(code)
                    tmp_path = f.name
                proc = subprocess.run(["node", tmp_path], capture_output=True, timeout=timeout_val)
            else:
                return {"error": f"不支持的语言: {language}"}
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            stdout = proc.stdout.decode("utf-8", errors="replace")[:5000]
            stderr = proc.stderr.decode("utf-8", errors="replace")[:2000]
            return {"result": stdout, "stderr": stderr, "returncode": proc.returncode}
        except subprocess.TimeoutExpired:
            return {"error": f"代码执行超时 ({timeout_val}s)"}
        except Exception as e:
            return {"error": f"执行失败: {str(e)}"}

    elif ntype == "image_gen":
        prompt = _replace_vars(config.get("prompt", ""), context)
        if not prompt:
            return {"error": "未配置图像 Prompt"}
        import httpx as _httpx
        size = config.get("size", "1024x1024")
        try:
            from pymongo import MongoClient as _MC
            _c = _MC(os.environ.get("MONGODB_URL", "mongodb://ai_mongo:ai_mongo_2024@localhost:27017"), serverSelectionTimeoutMS=3000)
            _s = _c["ai_framework"]["settings"].find_one({"_id": "app_settings"}) or {}
            api_key = _s.get("agnes_key", "")
            base_url = _s.get("agnes_url", "https://apihub.agnes-ai.com")
            model = config.get("model") or _s.get("agnes_image_model_1", "agnes-image-2.1-flash")
            if not api_key:
                return {"error": "未配置图像生成 API Key"}
            url = f"{base_url.rstrip('/')}/v1/images/generations"
            payload = {"model": model, "prompt": prompt, "n": 1, "size": size}
            with _httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
                resp.raise_for_status()
                data = resp.json()
            import base64
            media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_media", "images")
            os.makedirs(media_dir, exist_ok=True)
            saved = []
            for i, img in enumerate(data.get("data", [])):
                b64 = img.get("b64_json")
                img_url = img.get("url")
                if b64:
                    filename = f"wf_img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
                    filepath = os.path.join(media_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(b64))
                    saved.append({"filename": filename, "path": filepath})
                elif img_url:
                    saved.append({"url": img_url})
            return {"result": saved[0] if saved else "生成完成", "images": saved}
        except Exception as e:
            return {"error": f"图像生成失败: {str(e)}"}

    elif ntype == "error_handler":
        fallback = config.get("fallback_output", "上游执行出错")
        upstream_error = None
        for k, v in context.items():
            if isinstance(v, dict) and "error" in v:
                upstream_error = v["error"]
                break
        if upstream_error:
            return {"result": fallback, "original_error": upstream_error}
        return {"result": "上游执行正常，无需处理"}

    elif ntype == "text_split":
        delimiter = config.get("delimiter", "\n")
        text = _replace_vars(config.get("text", "{{input}}"), context)
        parts = [p.strip() for p in text.split(delimiter) if p.strip()]
        return {"items": parts, "count": len(parts)}

    elif ntype == "text_translate":
        if not llm_router:
            return {"error": "LLM router not available"}
        text = _replace_vars(config.get("text", "{{input}}"), context)
        target_lang = config.get("target_lang", "英语")
        prompt = f"将以下文本翻译为{target_lang}，只输出翻译结果：\n{text}"
        import asyncio, threading
        result_container = [None]
        error_container = [None]
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _call():
                    r = ""
                    async for chunk in llm_router.chat_stream([{"role": "user", "content": prompt}], provider=config.get("provider", "agnes")):
                        if chunk == "[DONE]" or chunk.startswith('{"type": "reasoning"'):
                            continue
                        r += chunk
                    return r
                result_container[0] = loop.run_until_complete(_call())
            except Exception as e:
                error_container[0] = str(e)
            finally:
                loop.close()
        t = threading.Thread(target=_run); t.start(); t.join(timeout=120)
        if error_container[0]:
            return {"error": error_container[0]}
        return {"result": result_container[0], "source": text, "target_lang": target_lang}

    elif ntype == "text_summarize":
        if not llm_router:
            return {"error": "LLM router not available"}
        text = _replace_vars(config.get("text", "{{input}}"), context)
        max_length = config.get("max_length", 200)
        prompt = f"用中文总结以下内容，不超过{max_length}字：\n{text[:3000]}"
        import asyncio, threading
        result_container = [None]
        error_container = [None]
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _call():
                    r = ""
                    async for chunk in llm_router.chat_stream([{"role": "user", "content": prompt}], provider=config.get("provider", "agnes")):
                        if chunk == "[DONE]" or chunk.startswith('{"type": "reasoning"'):
                            continue
                        r += chunk
                    return r
                result_container[0] = loop.run_until_complete(_call())
            except Exception as e:
                error_container[0] = str(e)
            finally:
                loop.close()
        t = threading.Thread(target=_run); t.start(); t.join(timeout=120)
        if error_container[0]:
            return {"error": error_container[0]}
        return {"result": result_container[0], "original_length": len(text)}

    elif ntype == "json_build":
        fields_str = config.get("fields", "{}")
        fields_str = _replace_vars(fields_str, context)
        try:
            fields = json.loads(fields_str)
        except Exception:
            fields = {}
        key_value_pairs = config.get("key_value_pairs", "")
        if key_value_pairs:
            for line in key_value_pairs.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    v_resolved = _replace_vars(v, context)
                    try:
                        fields[k] = json.loads(v_resolved)
                    except Exception:
                        fields[k] = v_resolved
        return {"result": fields}

    elif ntype == "data_filter":
        list_var = config.get("list_var", "input")
        raw = context.get(list_var, context.get("inputs", {}).get(list_var, []))
        if isinstance(raw, str):
            try: raw = json.loads(raw)
            except: raw = [raw]
        if not isinstance(raw, list):
            raw = [raw]
        field = config.get("field", "")
        op = config.get("operator", "eq")
        value = _replace_vars(config.get("value", ""), context)
        filtered = []
        for item in raw:
            if isinstance(item, dict) and field:
                item_val = item.get(field, "")
            else:
                item_val = item
            try:
                if op == "eq" and str(item_val) == value: filtered.append(item)
                elif op == "ne" and str(item_val) != value: filtered.append(item)
                elif op == "gt" and float(item_val) > float(value): filtered.append(item)
                elif op == "lt" and float(item_val) < float(value): filtered.append(item)
                elif op == "contains" and value in str(item_val): filtered.append(item)
                elif op == "startswith" and str(item_val).startswith(value): filtered.append(item)
            except (ValueError, TypeError):
                continue
        return {"items": filtered, "count": len(filtered), "original_count": len(raw)}

    elif ntype == "data_sort":
        list_var = config.get("list_var", "input")
        raw = context.get(list_var, context.get("inputs", {}).get(list_var, []))
        if isinstance(raw, str):
            try: raw = json.loads(raw)
            except: raw = [raw]
        if not isinstance(raw, list):
            raw = [raw]
        sort_field = config.get("sort_field", "")
        reverse = config.get("reverse", False)
        if sort_field and raw and isinstance(raw[0], dict):
            sorted_list = sorted(raw, key=lambda x: x.get(sort_field, ""), reverse=reverse)
        else:
            sorted_list = sorted(raw, reverse=reverse)
        return {"items": sorted_list, "count": len(sorted_list)}

    elif ntype == "switch":
        switch_var = _replace_vars(config.get("switch_var", "{{input}}"), context)
        cases_str = config.get("cases", "")
        default_case = config.get("default_case", "default")
        matched = default_case
        for line in cases_str.strip().split("\n"):
            if ":" in line:
                case_val, case_name = line.split(":", 1)
                if case_val.strip() == str(switch_var).strip():
                    matched = case_name.strip()
                    break
        return {"result": switch_var, "matched": matched, "branch": matched}

    elif ntype == "sub_workflow":
        sub_wf_id = config.get("workflow_id", "")
        if not sub_wf_id:
            return {"error": "未配置子工作流 ID"}
        sub_inputs = {}
        inputs_str = config.get("inputs_map", "{}")
        inputs_str = _replace_vars(inputs_str, context)
        try:
            sub_inputs = json.loads(inputs_str)
        except Exception:
            sub_inputs = {"input": str(context.get("input", ""))}
        try:
            sub_run = run_workflow(sub_wf_id, inputs=sub_inputs, llm_router=llm_router)
            return {"result": sub_run.outputs, "status": sub_run.status, "workflow_id": sub_wf_id}
        except Exception as e:
            return {"error": f"子工作流执行失败: {str(e)}"}

    elif ntype == "retry":
        max_retries = int(config.get("max_retries", 3))
        delay_sec = int(config.get("delay", 2))
        import time
        last_error = None
        for attempt in range(max_retries):
            upstream_ok = True
            for k, v in context.items():
                if isinstance(v, dict) and "error" in v:
                    upstream_ok = False
                    last_error = v["error"]
                    break
            if upstream_ok:
                return {"result": "上游执行成功", "attempts": attempt + 1}
            if attempt < max_retries - 1:
                time.sleep(delay_sec)
        return {"error": f"重试{max_retries}次后仍然失败: {last_error}", "attempts": max_retries}

    elif ntype == "notify":
        notify_type = config.get("notify_type", "dingtalk")
        webhook_url = _replace_vars(config.get("webhook_url", ""), context)
        content = _replace_vars(config.get("content", "{{input}}"), context)
        title = _replace_vars(config.get("title", "工作流通知"), context)
        if not webhook_url:
            return {"error": "未配置 Webhook URL"}
        import httpx as _httpx
        try:
            if notify_type == "dingtalk":
                payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
            elif notify_type == "wecom":
                payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
            elif notify_type == "feishu":
                payload = {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}}
            else:
                payload = {"text": f"{title}\n\n{content}"}
            with _httpx.Client(timeout=10) as client:
                resp = client.post(webhook_url, json=payload)
                return {"result": f"通知已发送 ({notify_type})", "status_code": resp.status_code}
        except Exception as e:
            return {"error": f"发送通知失败: {str(e)}"}

    # ==================== 数据处理类 ====================

    elif ntype == "math_calc":
        expression = config.get("expression", "0")
        expression = _replace_vars(expression, context)
        try:
            import math
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "int": int, "float": float,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "log10": math.log10,
                "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return {"result": result, "expression": expression}
        except Exception as e:
            return {"error": f"数学计算失败: {str(e)}"}

    elif ntype == "datetime":
        action = config.get("action", "now")
        fmt = config.get("format", "%Y-%m-%d %H:%M:%S")
        import datetime as _dt
        try:
            if action == "now":
                result = _dt.datetime.now().strftime(fmt)
            elif action == "today":
                result = _dt.date.today().strftime(fmt)
            elif action == "timestamp":
                result = int(_dt.datetime.now().timestamp())
            elif action == "parse":
                text = _replace_vars(config.get("input_template", ""), context)
                result = _dt.datetime.strptime(text, fmt).isoformat()
            elif action == "add":
                text = _replace_vars(config.get("input_template", ""), context)
                days = int(config.get("days", 0))
                hours = int(config.get("hours", 0))
                minutes = int(config.get("minutes", 0))
                dt = _dt.datetime.fromisoformat(text) if text else _dt.datetime.now()
                result = (dt + _dt.timedelta(days=days, hours=hours, minutes=minutes)).strftime(fmt)
            elif action == "diff":
                text1 = _replace_vars(config.get("input_template", ""), context)
                text2 = _replace_vars(config.get("end_date", ""), context)
                dt1 = _dt.datetime.fromisoformat(text1)
                dt2 = _dt.datetime.fromisoformat(text2)
                diff = dt2 - dt1
                result = {"days": diff.days, "seconds": diff.seconds, "total_hours": diff.total_seconds() / 3600}
            else:
                result = _dt.datetime.now().strftime(fmt)
            return {"result": result, "action": action}
        except Exception as e:
            return {"error": f"日期时间操作失败: {str(e)}"}

    elif ntype == "type_convert":
        target_type = config.get("target_type", "string")
        input_val = _replace_vars(config.get("input_template", ""), context)
        try:
            if target_type == "string":
                result = str(input_val)
            elif target_type == "int":
                result = int(float(input_val))
            elif target_type == "float":
                result = float(input_val)
            elif target_type == "bool":
                result = bool(input_val) and input_val not in ("0", "false", "False", "null", "None", "")
            elif target_type == "list":
                if isinstance(input_val, str):
                    result = [x.strip() for x in input_val.split(config.get("delimiter", ","))]
                elif isinstance(input_val, list):
                    result = input_val
                else:
                    result = [input_val]
            elif target_type == "json":
                result = json.loads(input_val) if isinstance(input_val, str) else json.loads(json.dumps(input_val))
            elif target_type == "dict":
                if isinstance(input_val, str):
                    result = dict(item.split("=", 1) for item in input_val.split("\n") if "=" in item)
                elif isinstance(input_val, dict):
                    result = input_val
                else:
                    result = {"value": input_val}
            else:
                result = str(input_val)
            return {"result": result, "type": target_type}
        except Exception as e:
            return {"error": f"类型转换失败: {str(e)}"}

    elif ntype == "csv_parse":
        delimiter = config.get("delimiter", ",")
        has_header = config.get("has_header", True)
        input_val = _replace_vars(config.get("input_template", ""), context)
        try:
            import csv
            import io
            if os.path.isfile(input_val):
                with open(input_val, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            else:
                content = input_val
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter) if has_header else csv.reader(io.StringIO(content), delimiter=delimiter)
            if has_header:
                rows = [dict(row) for row in reader]
            else:
                rows = [row for row in reader]
            return {"result": rows, "count": len(rows)}
        except Exception as e:
            return {"error": f"CSV 解析失败: {str(e)}"}

    elif ntype == "excel_read":
        file_path = _replace_vars(config.get("input_template", ""), context)
        sheet_name = config.get("sheet_name", "")
        max_rows = int(config.get("max_rows", 1000))
        try:
            import openpyxl
            if not file_path or not os.path.exists(file_path):
                return {"error": f"Excel 文件不存在: {file_path}"}
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
            rows = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i >= max_rows:
                    break
                rows.append([str(cell) if cell is not None else "" for cell in row])
            wb.close()
            headers = rows[0] if rows else []
            data = [dict(zip(headers, row)) for row in rows[1:]] if headers else rows
            return {"result": data, "headers": headers, "count": len(data)}
        except ImportError:
            return {"error": "需要安装 openpyxl: pip install openpyxl"}
        except Exception as e:
            return {"error": f"Excel 读取失败: {str(e)}"}

    elif ntype == "regex_replace":
        pattern = config.get("pattern", "")
        replacement = config.get("replacement", "")
        input_val = _replace_vars(config.get("input_template", ""), context)
        try:
            import re
            result = re.sub(pattern, replacement, input_val)
            count = len(re.findall(pattern, input_val))
            return {"result": result, "count": count}
        except re.error as e:
            return {"error": f"正则表达式错误: {str(e)}"}
        except Exception as e:
            return {"error": f"正则替换失败: {str(e)}"}

    elif ntype == "hash_encode":
        algorithm = config.get("algorithm", "md5")
        encoding = config.get("encoding", "hex")
        input_val = _replace_vars(config.get("input_template", ""), context)
        try:
            import hashlib
            import base64
            data = input_val.encode("utf-8")
            if algorithm == "md5":
                h = hashlib.md5(data)
            elif algorithm == "sha1":
                h = hashlib.sha1(data)
            elif algorithm == "sha256":
                h = hashlib.sha256(data)
            elif algorithm == "sha512":
                h = hashlib.sha512(data)
            elif algorithm == "base64_encode":
                result = base64.b64encode(data).decode("utf-8")
                return {"result": result, "algorithm": algorithm}
            elif algorithm == "base64_decode":
                result = base64.b64decode(input_val).decode("utf-8", errors="replace")
                return {"result": result, "algorithm": algorithm}
            elif algorithm == "url_encode":
                from urllib.parse import quote
                result = quote(input_val)
                return {"result": result, "algorithm": algorithm}
            elif algorithm == "url_decode":
                from urllib.parse import unquote
                result = unquote(input_val)
                return {"result": result, "algorithm": algorithm}
            else:
                return {"error": f"不支持的算法: {algorithm}"}
            if encoding == "hex":
                result = h.hexdigest()
            elif encoding == "base64":
                result = base64.b64encode(h.digest()).decode("utf-8")
            else:
                result = h.hexdigest()
            return {"result": result, "algorithm": algorithm}
        except Exception as e:
            return {"error": f"哈希/编码失败: {str(e)}"}

    elif ntype == "uuid_generate":
        version = config.get("version", "4")
        count = int(config.get("count", 1))
        try:
            import uuid
            results = []
            for _ in range(min(count, 100)):
                if version == "1":
                    results.append(str(uuid.uuid1()))
                else:
                    results.append(str(uuid.uuid4()))
            return {"result": results[0] if count == 1 else results, "count": len(results)}
        except Exception as e:
            return {"error": f"UUID 生成失败: {str(e)}"}

    # ==================== AI 扩展类 ====================

    elif ntype == "text_embedding":
        input_val = _replace_vars(config.get("input_template", ""), context)
        provider = config.get("provider", "agnes")
        try:
            import httpx as _httpx
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
            if provider == "agnes":
                api_key = os.getenv("AGNES_API_KEY", "")
                base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com")
            else:
                api_key = os.getenv("OPENAI_API_KEY", "")
                base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            if not api_key:
                return {"error": "未配置 API Key"}
            model = config.get("model", "text-embedding-ada-002")
            texts = [input_val] if isinstance(input_val, str) else input_val
            with _httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{base_url}/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": model, "input": texts}
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings = [item["embedding"] for item in data["data"]]
                return {"result": embeddings[0] if len(embeddings) == 1 else embeddings, "dimensions": len(embeddings[0])}
        except Exception as e:
            return {"error": f"文本嵌入失败: {str(e)}"}

    elif ntype == "speech_to_text":
        audio_path = _replace_vars(config.get("input_template", ""), context)
        language = config.get("language", "zh")
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language=language)
            return {"result": result["text"], "language": result.get("language", language)}
        except ImportError:
            return {"error": "需要安装 openai-whisper: pip install openai-whisper"}
        except Exception as e:
            return {"error": f"语音识别失败: {str(e)}"}

    elif ntype == "text_to_speech":
        input_val = _replace_vars(config.get("input_template", ""), context)
        save_path = config.get("save_path", "")
        voice = config.get("voice", "alloy")
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
            api_key = os.getenv("OPENAI_API_KEY", "")
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            if not api_key:
                return {"error": "未配置 OPENAI_API_KEY"}
            if not save_path:
                save_path = os.path.join("generated_media", f"tts_{int(__import__('time').time())}.mp3")
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            import httpx as _httpx
            with _httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{base_url}/v1/audio/speech",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "tts-1", "input": input_val, "voice": voice}
                )
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(resp.content)
            return {"result": f"语音已生成", "path": save_path, "voice": voice}
        except Exception as e:
            return {"error": f"语音合成失败: {str(e)}"}

    elif ntype == "image_process":
        input_path = _replace_vars(config.get("input_template", ""), context)
        action = config.get("action", "resize")
        save_path = config.get("save_path", "")
        try:
            from PIL import Image
            if not input_path or not os.path.exists(input_path):
                return {"error": f"图片不存在: {input_path}"}
            img = Image.open(input_path)
            if action == "resize":
                width = int(config.get("width", 800))
                height = int(config.get("height", 600))
                img = img.resize((width, height), Image.LANCZOS)
            elif action == "crop":
                left = int(config.get("left", 0))
                top = int(config.get("top", 0))
                right = int(config.get("right", img.width))
                bottom = int(config.get("bottom", img.height))
                img = img.crop((left, top, right, bottom))
            elif action == "rotate":
                angle = int(config.get("angle", 90))
                img = img.rotate(angle, expand=True)
            elif action == "watermark":
                from PIL import ImageDraw, ImageFont
                text = config.get("text", "Watermark")
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except Exception:
                    font = ImageFont.load_default()
                draw.text((10, img.height - 50), text, fill="rgba(255,255,255,128)", font=font)
            elif action == "grayscale":
                img = img.convert("L")
            elif action == "thumbnail":
                max_size = int(config.get("max_size", 200))
                img.thumbnail((max_size, max_size), Image.LANCZOS)
            if not save_path:
                base, ext = os.path.splitext(input_path)
                save_path = f"{base}_{action}{ext}"
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            img.save(save_path)
            return {"result": f"图片已处理", "path": save_path, "action": action, "size": f"{img.width}x{img.height}"}
        except ImportError:
            return {"error": "需要安装 Pillow: pip install Pillow"}
        except Exception as e:
            return {"error": f"图片处理失败: {str(e)}"}

    elif ntype == "markdown_html":
        input_val = _replace_vars(config.get("input_template", ""), context)
        try:
            import markdown
            html = markdown.markdown(input_val, extensions=["extra", "codehilite", "tables"])
            save_path = config.get("save_path", "")
            if save_path:
                save_path = _replace_vars(save_path, context)
                os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html}</body></html>")
            return {"result": html, "path": save_path or None}
        except ImportError:
            return {"error": "需要安装 markdown: pip install markdown"}
        except Exception as e:
            return {"error": f"Markdown 转换失败: {str(e)}"}

    # ==================== 网络通信类 ====================

    elif ntype == "websocket_connect":
        url = _replace_vars(config.get("url", ""), context)
        message = _replace_vars(config.get("input_template", ""), context)
        timeout_val = int(config.get("timeout", 10))
        try:
            import websocket
            ws = websocket.create_connection(url, timeout=timeout_val)
            if message:
                ws.send(message)
            result_data = ws.recv()
            ws.close()
            return {"result": result_data, "url": url}
        except ImportError:
            return {"error": "需要安装 websocket-client: pip install websocket-client"}
        except Exception as e:
            return {"error": f"WebSocket 连接失败: {str(e)}"}

    elif ntype == "http_stream":
        url = _replace_vars(config.get("url", ""), context)
        method = config.get("method", "GET").upper()
        headers_str = config.get("headers", "")
        body = config.get("body", "")
        timeout_val = int(config.get("timeout", 30))
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str) if headers_str.strip().startswith("{") else dict(
                    line.split(":", 1) for line in headers_str.strip().split("\n") if ":" in line
                )
            except Exception:
                pass
        body = _replace_vars(body, context)
        try:
            import httpx as _httpx
            collected = []
            with _httpx.Client(timeout=timeout_val, follow_redirects=True) as client:
                kwargs = {"url": url, "headers": headers}
                if method in ("POST", "PUT", "PATCH") and body:
                    try:
                        kwargs["json"] = json.loads(body)
                    except Exception:
                        kwargs["data"] = body
                with client.stream(method, **kwargs) as resp:
                    for line in resp.iter_lines():
                        if line:
                            collected.append(line)
                            if len(collected) >= 500:
                                break
            return {"result": "\n".join(collected), "url": url, "lines": len(collected)}
        except Exception as e:
            return {"error": f"HTTP 流式请求失败: {str(e)}"}

    elif ntype == "network_ping":
        target = _replace_vars(config.get("input_template", ""), context)
        count = int(config.get("count", 4))
        timeout_val = int(config.get("timeout", 5))
        try:
            import subprocess
            param = "-n" if __import__("platform").system().lower() == "windows" else "-c"
            proc = subprocess.run(
                ["ping", param, str(min(count, 10)), "-w", str(timeout_val * 1000), target],
                capture_output=True, timeout=timeout_val * 10 + 5
            )
            output = proc.stdout
            for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
                try:
                    output = proc.stdout.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            success = proc.returncode == 0
            return {"result": output, "success": success, "target": target}
        except Exception as e:
            return {"error": f"Ping failed: {str(e)}"}

    elif ntype == "url_shorten":
        url = _replace_vars(config.get("input_template", ""), context)
        provider = config.get("provider", "tinyurl")
        try:
            import httpx as _httpx
            with _httpx.Client(timeout=10, follow_redirects=True) as client:
                if provider == "tinyurl":
                    resp = client.get(f"https://tinyurl.com/api-create.php", params={"url": url})
                    short_url = resp.text
                elif provider == "is.gd":
                    resp = client.get(f"https://is.gd/create.php", params={"format": "json", "url": url})
                    short_url = resp.json()["shorturl"]
                else:
                    return {"error": f"不支持的缩短服务: {provider}"}
            return {"result": short_url, "original": url}
        except Exception as e:
            return {"error": f"URL 缩短失败: {str(e)}"}

    # ==================== 实用工具类 ====================

    elif ntype == "qrcode_gen":
        input_val = _replace_vars(config.get("input_template", ""), context)
        save_path = config.get("save_path", "")
        size = int(config.get("size", 256))
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=max(1, size // 256), border=2)
            qr.add_data(input_val)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            if not save_path:
                save_path = os.path.join("generated_media", f"qrcode_{int(__import__('time').time())}.png")
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            img = img.resize((size, size))
            img.save(save_path)
            return {"result": f"二维码已生成", "path": save_path, "content": input_val}
        except ImportError:
            return {"error": "需要安装 qrcode: pip install qrcode[pil]"}
        except Exception as e:
            return {"error": f"二维码生成失败: {str(e)}"}

    elif ntype == "qrcode_scan":
        input_path = _replace_vars(config.get("input_template", ""), context)
        try:
            from PIL import Image
            import pyzbar.pyzbar as pyzbar
            if not input_path or not os.path.exists(input_path):
                return {"error": f"图片不存在: {input_path}"}
            img = Image.open(input_path)
            decoded = pyzbar.decode(img)
            results = [{"data": d.data.decode("utf-8", errors="replace"), "type": d.type} for d in decoded]
            return {"result": results, "count": len(results)}
        except ImportError:
            return {"error": "需要安装 pyzbar: pip install pyzbar"}
        except Exception as e:
            return {"error": f"二维码识别失败: {str(e)}"}

    elif ntype == "pdf_generate":
        input_val = _replace_vars(config.get("input_template", ""), context)
        save_path = config.get("save_path", "")
        title = config.get("title", "")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            if not save_path:
                save_path = os.path.join("generated_media", f"doc_{int(__import__('time').time())}.pdf")
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            c = canvas.Canvas(save_path, pagesize=A4)
            width, height = A4
            y = height - 50
            if title:
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, y, title)
                y -= 30
            c.setFont("Helvetica", 11)
            for line in input_val.split("\n"):
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:100])
                y -= 16
            c.save()
            return {"result": f"PDF 已生成", "path": save_path}
        except ImportError:
            return {"error": "需要安装 reportlab: pip install reportlab"}
        except Exception as e:
            return {"error": f"PDF 生成失败: {str(e)}"}

    elif ntype == "json_diff":
        input_val = _replace_vars(config.get("input_template", ""), context)
        compare_val = _replace_vars(config.get("compare_value", ""), context)
        try:
            if isinstance(input_val, str):
                data1 = json.loads(input_val)
            else:
                data1 = input_val
            if isinstance(compare_val, str):
                data2 = json.loads(compare_val)
            else:
                data2 = compare_val

            def _diff(a, b, path=""):
                differences = []
                if type(a) != type(b):
                    differences.append({"path": path or "/", "type": "type_mismatch", "a": str(type(a).__name__), "b": str(type(b).__name__)})
                    return differences
                if isinstance(a, dict):
                    for key in set(list(a.keys()) + list(b.keys())):
                        if key not in a:
                            differences.append({"path": f"{path}.{key}", "type": "added", "b": b[key]})
                        elif key not in b:
                            differences.append({"path": f"{path}.{key}", "type": "removed", "a": a[key]})
                        else:
                            differences.extend(_diff(a[key], b[key], f"{path}.{key}"))
                elif isinstance(a, list):
                    for i in range(max(len(a), len(b))):
                        if i >= len(a):
                            differences.append({"path": f"{path}[{i}]", "type": "added", "b": b[i]})
                        elif i >= len(b):
                            differences.append({"path": f"{path}[{i}]", "type": "removed", "a": a[i]})
                        else:
                            differences.extend(_diff(a[i], b[i], f"{path}[{i}]"))
                elif a != b:
                    differences.append({"path": path or "/", "type": "changed", "a": a, "b": b})
                return differences

            diffs = _diff(data1, data2)
            return {"result": diffs, "count": len(diffs), "identical": len(diffs) == 0}
        except Exception as e:
            return {"error": f"JSON 对比失败: {str(e)}"}

    elif ntype == "output":
        clean = {}
        for k, v in context.items():
            if k in ("inputs",):
                clean[k] = v
            elif isinstance(v, dict):
                try:
                    json.dumps(v)
                    clean[k] = v
                except (TypeError, ValueError):
                    clean[k] = str(v)
            else:
                clean[k] = v
        return {"output": clean}

    return {"result": "unknown node type"}


_versions_col = None


def _get_versions_col():
    global _versions_col
    if _versions_col is None:
        from pymongo import MongoClient
        MONGO_URL = os.environ.get("MONGODB_URL", "mongodb://ai_mongo:ai_mongo_2024@localhost:27017")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
        db = client["ai_framework"]
        _versions_col = db["workflow_versions"]
    return _versions_col


def export_workflow(workflow_id: str) -> Optional[Dict]:
    wf = get_workflow(workflow_id)
    if not wf:
        return None
    return {
        "name": wf.get("name", ""),
        "description": wf.get("description", ""),
        "nodes": wf.get("nodes", []),
        "edges": wf.get("edges", []),
        "exported_at": datetime.now().isoformat(),
        "version": "1.0"
    }


def import_workflow(data: dict) -> Dict:
    import_data = {
        "name": data.get("name", "导入的工作流"),
        "description": data.get("description", ""),
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
        "status": "draft"
    }
    return create_workflow(import_data)


def save_version(workflow_id: str, comment: str = "") -> Optional[Dict]:
    wf = get_workflow(workflow_id)
    if not wf:
        return None
    col = _get_versions_col()
    versions_count = col.count_documents({"workflow_id": workflow_id})
    version_doc = {
        "workflow_id": workflow_id,
        "version": versions_count + 1,
        "name": wf.get("name", ""),
        "description": wf.get("description", ""),
        "nodes": wf.get("nodes", []),
        "edges": wf.get("edges", []),
        "status": wf.get("status", "draft"),
        "comment": comment,
        "created_at": datetime.now().isoformat()
    }
    col.insert_one(version_doc)
    return {"version": version_doc["version"], "created_at": version_doc["created_at"]}


def list_versions(workflow_id: str) -> List[Dict]:
    col = _get_versions_col()
    results = []
    for doc in col.find({"workflow_id": workflow_id}).sort("version", -1):
        doc.pop("_id", None)
        results.append(doc)
    return results


def get_version(workflow_id: str, version: int) -> Optional[Dict]:
    col = _get_versions_col()
    doc = col.find_one({"workflow_id": workflow_id, "version": version})
    if doc:
        doc.pop("_id", None)
    return doc


def restore_version(workflow_id: str, version: int) -> bool:
    v = get_version(workflow_id, version)
    if not v:
        return False
    update_data = {
        "name": v.get("name", ""),
        "description": v.get("description", ""),
        "nodes": v.get("nodes", []),
        "edges": v.get("edges", []),
    }
    return update_workflow(workflow_id, update_data)


def delete_version(workflow_id: str, version: int) -> bool:
    col = _get_versions_col()
    result = col.delete_one({"workflow_id": workflow_id, "version": version})
    return result.deleted_count > 0


def run_workflow(workflow_id: str, inputs: Dict[str, Any] = None, llm_router=None) -> WorkflowRun:
    wf_data = get_workflow(workflow_id)
    if not wf_data:
        raise ValueError(f"Workflow {workflow_id} not found")

    run = WorkflowRun(workflow_id=workflow_id, inputs=inputs or {})
    save_run(run)

    nodes = wf_data.get("nodes", [])
    edges = wf_data.get("edges", [])

    if not nodes:
        run.status = "completed"
        run.finished_at = datetime.now().isoformat()
        update_run(run)
        return run

    levels = _topological_sort(nodes, edges)
    node_map = {n["id"]: n for n in nodes}
    context = {"inputs": inputs or {}}
    if isinstance(inputs, dict):
        for k, v in inputs.items():
            if k not in context:
                context[k] = v

    for level in levels:
        for node_id in level:
            node = node_map.get(node_id)
            if not node:
                continue
            try:
                result = _execute_node(node, context, llm_router)
                context[node_id] = result
                if isinstance(result, dict):
                    for k, v in result.items():
                        if k not in context:
                            context[k] = v
                run.node_results[node_id] = {"status": "completed", "result": result}
            except Exception as e:
                run.node_results[node_id] = {"status": "failed", "error": str(e)}
                run.status = "failed"
                run.error = str(e)
                run.finished_at = datetime.now().isoformat()
                update_run(run)
                return run

    clean_outputs = {}
    for k, v in context.items():
        if isinstance(v, dict):
            try:
                json.dumps(v)
                clean_outputs[k] = v
            except (TypeError, ValueError):
                clean_outputs[k] = str(v)
        elif isinstance(v, list):
            try:
                json.dumps(v)
                clean_outputs[k] = v
            except (TypeError, ValueError):
                clean_outputs[k] = str(v)
        else:
            clean_outputs[k] = v
    run.outputs = clean_outputs
    run.status = "completed"
    run.finished_at = datetime.now().isoformat()
    update_run(run)
    return run
