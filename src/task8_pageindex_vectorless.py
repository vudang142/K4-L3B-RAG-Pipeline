"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.

Bản tối giản: SDK PageIndex chỉ nhận PDF, nên chỉ upload các PDF gốc trong
data/landing/legal/. Không có API key hoặc chưa upload -> pageindex_search
trả [] để Task 9 dùng hybrid results.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
ROOT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT_DIR / "data" / "standardized"
LANDING_LEGAL_DIR = ROOT_DIR / "data" / "landing" / "legal"
# Mapping source -> doc_id; đã có trong .gitignore.
DOC_IDS_PATH = ROOT_DIR / "pageindex_doc_ids.json"

# Tổng thời gian tối đa cho một lần fallback (giây). SDK không đặt timeout
# cho HTTP request nên toàn bộ lời gọi được chạy trong thread có timeout.
PAGEINDEX_TIMEOUT = 30
POLL_INTERVAL = 1.0


def _load_doc_ids() -> dict[str, str]:
    if not DOC_IDS_PATH.exists():
        return {}
    try:
        return json.loads(DOC_IDS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_doc_ids(doc_ids: dict[str, str]) -> None:
    DOC_IDS_PATH.write_text(
        json.dumps(doc_ids, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY is empty; skip upload (fallback disabled).")
        return

    from pageindex import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    doc_ids = _load_doc_ids()
    for path in sorted(LANDING_LEGAL_DIR.iterdir()):
        if path.suffix.lower() != ".pdf":
            if path.name != ".gitkeep":
                print(f"Skip {path.name}: PageIndex SDK only accepts PDF")
            continue
        if path.name in doc_ids:
            print(f"Already uploaded {path.name}: {doc_ids[path.name]}")
            continue
        response = client.submit_document(str(path))
        doc_ids[path.name] = response["doc_id"]
        # Lưu sau mỗi file để lần chạy lại không upload trùng khi lỗi giữa chừng.
        _save_doc_ids(doc_ids)
        print(f"Uploaded {path.name}: {response['doc_id']}")


def _node_content(node: dict) -> str:
    contents = node.get("relevant_contents") or []
    parts = [
        item.get("relevant_content", "") if isinstance(item, dict) else str(item)
        for item in contents
    ]
    text = "\n".join(part for part in parts if part)
    return text or node.get("text") or node.get("content") or ""


def _search(query: str, top_k: int, doc_ids: dict[str, str]) -> list[dict]:
    from pageindex import PageIndexClient

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    deadline = time.monotonic() + PAGEINDEX_TIMEOUT

    # Gửi query cho mọi document trước, rồi poll song song để giảm độ trễ.
    pending: dict[str, str] = {}
    for source, doc_id in doc_ids.items():
        try:
            pending[source] = client.submit_query(doc_id, query)["retrieval_id"]
        except Exception:
            continue  # document chưa sẵn sàng hoặc lỗi riêng lẻ

    nodes_by_source: dict[str, list[dict]] = {}
    while pending and time.monotonic() < deadline:
        for source, retrieval_id in list(pending.items()):
            try:
                response = client.get_retrieval(retrieval_id)
            except Exception:
                pending.pop(source)
                continue
            status = response.get("status")
            if status == "completed":
                nodes_by_source[source] = response.get("retrieved_nodes") or []
                pending.pop(source)
            elif status == "failed":
                pending.pop(source)
        if pending:
            time.sleep(POLL_INTERVAL)

    # API không trả score: gán 1/rank theo thứ hạng node trong từng document.
    results = []
    seen: set[str] = set()
    for source in doc_ids:
        for rank, node in enumerate(nodes_by_source.get(source, []), 1):
            content = _node_content(node)
            item_id = f"pageindex::{source}::{node.get('node_id') or rank}"
            if not content.strip() or item_id in seen:
                continue
            seen.add(item_id)
            results.append({
                "id": item_id,
                "content": content,
                "score": 1.0 / rank,
                "metadata": {
                    "source": source,
                    "title": node.get("title") or Path(source).stem,
                    "doc_type": "legal",
                    "url": None,
                    "chunk_index": rank - 1,
                },
                "retrieval_method": "pageindex",
            })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not PAGEINDEX_API_KEY or top_k <= 0:
        return []
    doc_ids = _load_doc_ids()
    if not doc_ids:
        return []

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_search, query, top_k, doc_ids)
        return future.result(timeout=PAGEINDEX_TIMEOUT + 5)
    except Exception:
        # Lỗi mạng/SDK/timeout không được làm crash pipeline hay UI.
        return []
    finally:
        executor.shutdown(wait=False)


if __name__ == "__main__":
    upload_documents()
