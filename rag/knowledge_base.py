"""
RAG (Retrieval-Augmented Generation) Knowledge Base Module.
Indexes local technical manuals, maintenance guides, and alarm codes.
Retrieves relevant context chunks based on vector/keyword similarity.
"""

import os
import re

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")

class LocalRAGKnowledgeBase:
    def __init__(self, docs_dir=DOCS_DIR):
        self.docs_dir = docs_dir
        self.chunks = []
        self.load_documents()

    def load_documents(self):
        self.chunks = []
        if not os.path.exists(self.docs_dir):
            return

        for fname in os.listdir(self.docs_dir):
            if fname.endswith(".md") or fname.endswith(".txt"):
                path = os.path.join(self.docs_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                    
                    # Split into sections by headers or double newlines
                    sections = re.split(r'\n(?=#+ )|\n\n', text)
                    for sec in sections:
                        sec_clean = sec.strip()
                        if len(sec_clean) > 20:
                            self.chunks.append({
                                "source": fname,
                                "content": sec_clean
                            })
                except Exception:
                    pass

    def search(self, query, top_k=3):
        if not self.chunks:
            self.load_documents()
        if not self.chunks:
            return []

        q_words = set(re.findall(r'\w+', query.lower()))
        if not q_words:
            return []

        scored = []
        for chunk in self.chunks:
            content_words = set(re.findall(r'\w+', chunk["content"].lower()))
            overlap = len(q_words.intersection(content_words))
            
            # Exact phrase bonus
            bonus = 2.0 if query.lower() in chunk["content"].lower() else 0.0
            score = overlap + bonus
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]
        return results

_GLOBAL_RAG = LocalRAGKnowledgeBase()

def search_knowledge_base(query, top_k=3):
    """
    Public RAG search API. Returns formatted text excerpts from local docs.
    """
    results = _GLOBAL_RAG.search(query, top_k=top_k)
    if not results:
        return {"success": False, "excerpts": [], "context_text": ""}

    excerpts = []
    formatted = []
    for r in results:
        excerpts.append({"source": r["source"], "text": r["content"]})
        formatted.append(f"[{r['source']}]\n{r['content']}")

    return {
        "success": True,
        "excerpts": excerpts,
        "context_text": "\n\n".join(formatted)
    }
