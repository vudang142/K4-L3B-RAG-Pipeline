"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re


CORPUS: list[dict] = []

# Cache (corpus object, bm25 index) để không build lại index cho mỗi query.
_INDEX_CACHE: tuple[list[dict], object] | None = None


def tokenize(text: str) -> list[str]:
    """Lowercase và tách theo ký tự chữ/số (Unicode), bỏ dấu câu."""
    return re.findall(r"\w+", text.lower())


def load_corpus() -> list[dict]:
    """Nạp đúng danh sách chunks mà Task 4 index vào ChromaDB.

    Dùng lại load_documents + chunk_documents nên chunk id trùng khớp với
    dense search, giúp RRF gộp được cùng một chunk từ hai retriever.
    """
    from .task4_chunking_indexing import chunk_documents, load_documents

    return chunk_documents(load_documents())


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    return BM25Okapi([tokenize(item["content"]) for item in corpus])


def _get_index():
    global CORPUS, _INDEX_CACHE
    if not CORPUS:
        CORPUS = load_corpus()
    if not CORPUS:
        return None
    if _INDEX_CACHE is None or _INDEX_CACHE[0] is not CORPUS:
        _INDEX_CACHE = (CORPUS, build_bm25_index(CORPUS))
    return _INDEX_CACHE[1]


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    import numpy as np

    query_tokens = tokenize(query)
    if top_k <= 0 or not query_tokens:
        return []
    bm25 = _get_index()
    if bm25 is None:
        return []

    scores = bm25.get_scores(query_tokens)
    token_set = set(query_tokens)
    results = []
    # Sort ổn định trên -scores để giữ thứ tự corpus khi bằng điểm.
    for index in np.argsort(-scores, kind="stable"):
        # Bỏ chunk không chứa từ nào của query. Không lọc theo score > 0 vì
        # với corpus nhỏ, IDF của BM25Okapi có thể bằng 0 dù chunk vẫn khớp.
        if token_set.isdisjoint(bm25.doc_freqs[index]):
            continue
        item = CORPUS[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) == top_k:
            break
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
