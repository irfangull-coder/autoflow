"""Simple, no-API-key RAG retrieval for the AutoFlow starter.

Why no embeddings library here? So the Week-1 prototype runs on any
laptop with only Python + FastAPI. The interface is deliberately the
same as a vector-DB version will have:

    index = DocumentIndex()
    index.add_document("Return Policy", text)
    index.search("return policy kya hai?")  -> list of chunks + source

Later (Week 3-4) you can swap the scoring inside `search()` for
embeddings + ChromaDB/pgvector without changing the agents, because
they only call `search()` and read `text` + `source`.
"""
import re
from collections import Counter

# Very small stopword list for English + Roman Urdu, so common words
# like "kya", "hai", "ka" do not dominate the score.
STOPWORDS = {
    "a", "an", "the", "is", "are", "what", "how", "when", "where",
    "kya", "hai", "hain", "ka", "ki", "ke", "ko", "me", "mein",
    "par", "aur", "ye", "yeh", "mera", "meri", "mujhe", "batao",
    "bataen", "please", "kindly",
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


def chunk_text(text: str, max_words: int = 60) -> list[str]:
    """Split a document into overlapping-ish word chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


class DocumentIndex:
    def __init__(self):
        # Each chunk: {"text": ..., "source": ..., "tokens": Counter}
        self.chunks: list[dict] = []

    def add_document(self, source: str, text: str) -> int:
        added = 0
        for chunk in chunk_text(text):
            self.chunks.append(
                {"text": chunk, "source": source, "tokens": Counter(tokenize(chunk))}
            )
            added += 1
        return added

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Score chunks by token overlap with the query."""
        query_tokens = Counter(tokenize(query))
        if not query_tokens:
            return []
        scored = []
        for chunk in self.chunks:
            overlap = sum(
                min(query_tokens[t], chunk["tokens"][t]) for t in query_tokens
            )
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"text": c["text"], "source": c["source"], "score": s}
            for s, c in scored[:top_k]
        ]
