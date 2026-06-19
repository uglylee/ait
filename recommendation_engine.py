from typing import List, Dict
import uuid

_client = None

def _get_client():
    global _client
    if _client is None:
        from chromadb import Client
        _client = Client()
    return _client

def add_interaction(user_id: str, text: str):
    if not text or not text.strip():
        return
    client = _get_client()
    name = f"rec_{user_id.replace(' ', '_').replace('/', '_')}"
    collection = client.get_or_create_collection(name=name)
    collection.add(
        documents=[text[:2000]],
        ids=[str(uuid.uuid4())],
        metadatas=[{"user_id": user_id}]
    )

def recommend(user_id: str, top_k: int = 5) -> List[Dict]:
    client = _get_client()
    name = f"rec_{user_id.replace(' ', '_').replace('/', '_')}"
    try:
        collection = client.get_collection(name=name)
    except Exception:
        return []

    if collection.count() == 0:
        return []

    all_docs = collection.get()
    if not all_docs["documents"]:
        return []

    recent = all_docs["documents"][-10:]
    query = " ".join(recent[-3:])

    try:
        results = collection.query(query_texts=[query], n_results=min(top_k + 5, collection.count()))
    except Exception:
        return []

    kb_results = []
    try:
        from langchain_engine import get_rag_engine
        rag = get_rag_engine()
        kb_results = rag.search(query, top_k=3)
    except Exception:
        pass

    recs = []
    seen = set()
    for i, (doc, score) in enumerate(zip(
        results["documents"][0] if results["documents"] else [],
        results["distances"][0] if results["distances"] else []
    )):
        if doc in seen:
            continue
        seen.add(doc)
        recs.append({
            "id": str(i),
            "title": doc[:100],
            "type": "content",
            "full_text": doc,
            "related": [{"content": r["content"][:300], "score": round(r["score"], 2)} for r in kb_results]
        })
        if len(recs) >= top_k:
            break

    return recs
