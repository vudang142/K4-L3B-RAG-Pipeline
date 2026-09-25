"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os
import sys

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()

# Giá trị cuối cùng lấy từ SCORE_THRESHOLD trong .env sau khi calibrate
# (python -m src.task9_retrieval_pipeline); 0.3 chỉ là mặc định tạm.
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or 0.3)
DEFAULT_TOP_K = 5

# Câu hỏi mẫu để calibrate threshold — thay bằng câu hỏi theo corpus của nhóm.
IN_DOMAIN_QUERIES = [
    "Học phí một tín chỉ là bao nhiêu?",
    "Điều kiện để được xét học bổng khuyến khích học tập?",
    "Sinh viên đăng ký ở ký túc xá như thế nào?",
    "Thư viện mở cửa vào những giờ nào?",
    "Thời hạn đăng ký học phần là khi nào?",
]
OUT_OF_DOMAIN_QUERIES = [
    "Thời tiết Hà Nội ngày mai thế nào?",
    "Cách nấu phở bò ngon?",
    "Giá vàng hôm nay bao nhiêu?",
]


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    if top_k <= 0:
        return []

    dense = semantic_search(query, top_k=top_k * 2)
    if use_reranking:
        sparse = lexical_search(query, top_k=top_k * 2)
        # RRF chỉ chạy đúng một lần trong toàn pipeline.
        hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    else:
        hybrid = dense[:top_k]

    # Fallback dựa trên cosine score gốc của dense search, không dùng RRF score.
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception:
            pass
    return hybrid[:top_k]


def calibrate(queries_in: list[str], queries_out: list[str]) -> None:
    """In best dense cosine score của query in/out domain để chọn threshold."""
    def best(query: str) -> float:
        dense = semantic_search(query, top_k=1)
        return dense[0]["score"] if dense else 0.0

    scores_in = [(q, best(q)) for q in queries_in]
    scores_out = [(q, best(q)) for q in queries_out]
    for label, rows in (("IN-DOMAIN", scores_in), ("OUT-OF-DOMAIN", scores_out)):
        print(f"\n{label}")
        for query, score in rows:
            print(f"  {score:.3f}  {query}")

    min_in = min(score for _, score in scores_in)
    max_out = max(score for _, score in scores_out)
    print(f"\nmin in-domain = {min_in:.3f}, max out-of-domain = {max_out:.3f}")
    if min_in > max_out:
        print(f"Suggested SCORE_THRESHOLD = {(min_in + max_out) / 2:.3f}")
    else:
        print("In/out domain scores overlap; chọn threshold thủ công và ghi lại trade-off.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for result in retrieve(" ".join(sys.argv[1:]), top_k=3):
            print(f"[{result['retrieval_method']}] {result['score']:.4f} {result['id']}")
    else:
        calibrate(IN_DOMAIN_QUERIES, OUT_OF_DOMAIN_QUERIES)
