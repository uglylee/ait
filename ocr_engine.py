import io
import os
import numpy as np
from PIL import Image

_reader = None

def get_ocr_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return _reader

def ocr_recognize(file_bytes: bytes) -> dict:
    reader = get_ocr_reader()
    image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
    img_array = np.array(image)
    results = reader.readtext(img_array)

    texts = [r[1] for r in results]
    confidences = [r[2] for r in results]

    full_text = "\n".join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    return {
        "text": full_text,
        "confidence": round(avg_confidence, 2),
        "format": "plain_text",
        "details": [{"text": r[1], "confidence": round(r[2], 2)} for r in results]
    }

def ai_enhance(raw_text: str) -> str:
    if not raw_text.strip():
        return ""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    api_key = os.getenv("AGNES_API_KEY", "")
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com")
    model = os.getenv("AGNES_MODEL", "agnes-2.0-flash")
    if not api_key:
        return raw_text

    prompt = f"""你是一个文字识别后处理助手。请对以下OCR识别结果进行增强处理：
1. 修正明显的识别错误（错别字、标点错误）
2. 合理分段和排版
3. 保持原文意思不变，不要添加额外内容
4. 如果是表格，用Markdown表格格式整理

OCR原始识别结果：
{raw_text}

增强后的结果："""

    import httpx
    try:
        with httpx.Client(timeout=30.0) as resp:
            r = resp.post(
                f"{base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024}
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return raw_text
