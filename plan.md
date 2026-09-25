# Kế hoạch triển khai — RAG Pipeline (sprint 4 giờ, nhóm 4 người)

Tài liệu này giả lập nhóm đã họp, phân vai và bắt đầu code ngay. Mốc thời gian tính từ lúc `git clone` xong. Tham chiếu bắt buộc: [README.md](README.md), [docs/STEP_BY_STEP.md](docs/STEP_BY_STEP.md), [docs/MODULE_CONTRACTS.md](docs/MODULE_CONTRACTS.md), [docs/GRADING_RUBRIC.md](docs/GRADING_RUBRIC.md).

## 0. Việc phải chốt trước khi bấm giờ (5 phút, cả nhóm)

- **Chủ đề**: chọn **"Dịch vụ đại học"** (học phí, học bổng, ký túc xá, thư viện, đăng ký học phần) — nguồn dễ tìm, có PDF/DOCX chính thức từ website trường + tin/thông báo công khai. Nhóm có thể đổi chủ đề khác trong [docs/SUGGESTED_TOPICS.md](docs/SUGGESTED_TOPICS.md) nếu có sẵn nguồn quen thuộc hơn — quy tắc không đổi: ≥3 tài liệu chính sách (PDF/DOCX) + ≥5 bài viết/thông báo.
- **LLM provider**: chọn provider mà nhóm **đã có sẵn API key** ngay lúc này (OpenAI / Gemini / Anthropic) — đừng chờ xin key giữa chừng, sẽ lệch tiến độ. Điền vào `.env` (copy từ `.env.example`).
- **Embedding provider**: mặc định `sentence_transformers` (chạy local, không tốn API/quota) — giữ nguyên để tránh rủi ro rate limit trong 4 tiếng.

### ⚠️ Hai điểm vênh trong repo cần xử lý ngay (kẻo cuối giờ mới phát hiện test fail)

1. `tests/test_acceptance.py` đọc `group_project/evaluation/RESULT.md`, nhưng file có sẵn (đã có template, đang rỗng phần nội dung) lại nằm ở [reports/RESULT.md](reports/RESULT.md). Thư mục `group_project/evaluation/` hiện chỉ có `golden_dataset.json` (rỗng). → **Việc cần làm**: copy nội dung template từ `reports/RESULT.md` sang `group_project/evaluation/RESULT.md` và điền nội dung ở đó (đường dẫn mà test và acceptance criteria thực sự kiểm tra).
2. README trỏ tới `group_project/ịndividual/INDIVIDUAL_REPORT.md` (thư mục có lỗi gõ dấu, không tồn tại). File thật là [reports/INDIVIDUAL_REPORT.md](reports/INDIVIDUAL_REPORT.md). → Mỗi thành viên copy từ đường dẫn thật này, không đi tìm thư mục `ịndividual`.

Phân công: 1 bạn xử lý 2 việc trên trong 5 phút đầu (song song với phần Setup bên dưới), không cần chờ.

## 1. Phân vai trò (4 người)

| Vai trò | Phụ trách chính | File chính |
|---|---|---|
| **A — Data & Standardize** | Thu thập tài liệu, crawl tin, convert Markdown | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py` |
| **B — Indexing & Dense search** | Chunking, embedding, ChromaDB, semantic search | `src/task4_chunking_indexing.py`, `src/task5_semantic_search.py` |
| **C — Lexical & Fusion & Pipeline** | BM25, RRF, PageIndex fallback, retrieval pipeline | `src/task6_lexical_search.py`, `src/task7_reranking.py`, `src/task8_pageindex_vectorless.py`, `src/task9_retrieval_pipeline.py` |
| **D — Generation & UI** | LLM generation, citation, Streamlit chatbot | `src/task10_generation.py`, `app.py` |

Cuối buổi, **cả 4 người cùng làm evaluation** (golden dataset, RAGAS, A/B, report) vì phần này cần hiểu toàn bộ pipeline.

Nếu nhóm chỉ có 3 người: gộp vai C và D (một người vừa làm retrieval pipeline vừa làm generation, vì task10 phụ thuộc trực tiếp vào task9). Nếu có 5 người: tách riêng một bạn phụ trách Evaluation/Golden dataset xuyên suốt từ giữa buổi thay vì dồn vào cuối.

## 2. Bảng phân bổ thời gian (tổng 240 phút)

| Khối | Thời gian | Ai làm gì | Kết quả bắt buộc đạt được |
|---|---|---|---|
| **0. Setup** | 00:00–00:15 (15p) | Cả nhóm: tạo venv, `pip install -e ".[dev]"`, `playwright install chromium`, copy `.env`, chốt chủ đề & provider, phân vai, tạo nhánh git riêng mỗi người | Môi trường chạy được `pytest -q` (dù đang fail vì `NotImplementedError` — đó là baseline bình thường) |
| **1. Data collection** | 00:15–00:45 (30p) | **A**: tìm & tải PDF/DOCX, điền `ARTICLE_URLS`, chạy task1+task2. **B/C/D**: đọc kỹ `docs/MODULE_CONTRACTS.md`, code sẵn phần không phụ thuộc data (ví dụ `embed_texts`, `get_collection`, khung `rerank_rrf`) | ≥3 file trong `data/landing/legal/`, ≥5 file JSON trong `data/landing/news/` |
| **2. Standardize + Index start** | 00:45–01:15 (30p) | **A**: code & chạy task3 (Markdown hoá). **B**: code `load_documents`, `chunk_documents` trong task4 (chạy thử ngay khi task3 ra Markdown đầu tiên, không cần chờ hết) | `data/standardized/legal/*.md` ≥3, `data/standardized/news/*.md` ≥5; `chunk_documents` pass được `tests/test_contracts.py::test_chunk_documents_preserves_identity_and_metadata` |
| **3. Embedding + Dense + BM25** | 01:15–02:00 (45p) | **B**: `embed_texts`, `embed_chunks`, `get_collection`, `index_to_vectorstore` (task4) → chạy `python -m src.task4_chunking_indexing` → sau đó `semantic_search` (task5). **C**: song song code `build_bm25_index` + `lexical_search` (task6) dùng chung `CORPUS` (load lại từ Markdown hoặc import từ task4) | ChromaDB có dữ liệu tại `chroma_db/`; `semantic_search("...")` và `lexical_search("...")` chạy ra `SearchResult` hợp lệ |
| **4. RRF + Fallback + Pipeline** | 02:00–02:30 (30p) | **C**: `rerank_rrf` (task7) → `pageindex_search`/`upload_documents` (task8, bản tối giản — xem mục 4.4) → `retrieve` (task9), calibrate `SCORE_THRESHOLD` | `pytest tests/test_contracts.py -q` pass các test liên quan RRF và `retrieve` |
| **5. Generation + UI** | 02:30–03:10 (40p) | **D**: `reorder_for_llm`, `format_context`, `call_llm`, `generate_with_citation` (task10) → nối vào `app.py` (hiển thị answer + sources + retrieval method + score) | `streamlit run app.py` trả lời có citation, hiển thị nguồn |
| **6. Evaluation** | 03:10–03:40 (30p) | Cả nhóm: viết 15+ câu hỏi vào `group_project/evaluation/golden_dataset.json`, chạy RAGAS 4 metric cho Config A (dense-only) vs Config B (hybrid+RRF), điền `group_project/evaluation/RESULT.md` | `tests/test_acceptance.py` pass toàn bộ; RESULT.md không còn `TODO` |
| **7. Test, report, demo, push** | 03:40–04:00 (20p) | Cả nhóm: `pytest -q` toàn bộ, mỗi người điền `reports/<mssv>-<ten>.md`, kiểm tra không commit `.env`/cache, chuẩn bị 1 query đúng domain + 1 query ngoài domain để demo, `git push` | Repo sạch, test pass, demo sẵn sàng |

## 3. Chi tiết kỹ thuật theo từng người

### 3.1 A — Data & Standardize

**Task 1 — `src/task1_collect_legal_docs.py`**
- Sửa hàm `download_documents()`: bỏ `raise NotImplementedError`, thêm logic tải/copy file.
- Thu thập ở đâu: trang chính thức của một trường đại học cụ thể (mục "Quy chế đào tạo", "Thông báo học phí – học bổng", "Quy định ký túc xá", "Nội quy thư viện", "Hướng dẫn đăng ký học phần"). Ưu tiên file PDF/DOCX có ngày ban hành rõ ràng. Có thể tải thủ công bằng trình duyệt rồi copy vào `data/landing/legal/` — không bắt buộc dùng code tải tự động nếu trang chặn bot.
- Yêu cầu tối thiểu: ≥3 file, mỗi file >1KB (kiểm tra bởi `tests/test_acceptance.py::test_corpus_has_required_legal_documents`), đặt tên không dấu, mô tả đúng nội dung (vd. `hoc-phi-2025.pdf`, `quy-che-ky-tuc-xa.docx`).

**Task 2 — `src/task2_crawl_news.py`**
- Điền ≥5 URL công khai vào `ARTICLE_URLS` (thông báo/tin tức từ cùng chủ đề: học bổng mới, thay đổi học phí, tin thư viện, sự kiện tuyển sinh...).
- Cài đặt `crawl_article()` theo gợi ý comment sẵn trong file (dùng `crawl4ai.AsyncWebCrawler`, đã có trong `pyproject.toml`). Nếu một trang chặn crawler, đổi sang nguồn công khai khác thay vì cố vượt WAF (đúng lưu ý trong file).
- Chạy `python -m src.task2_crawl_news` → mỗi bài ra 1 file JSON tại `data/landing/news/` với đủ 4 field: `url`, `title`, `date_crawled`, `content_markdown` (bắt buộc theo `test_corpus_has_required_news_with_metadata`).

**Task 3 — `src/task3_convert_markdown.py`**
- Cài `convert_legal_docs()`: dùng `MarkItDown` (đã có trong deps) để convert từng PDF/DOCX trong `data/landing/legal/` → ghi `.md` vào `data/standardized/legal/`.
- Cài `convert_news_articles()`: đọc JSON trong `data/landing/news/`, ghép header (title/url/date) + `content_markdown` → ghi vào `data/standardized/news/`.
- Chạy lại nhiều lần không được tạo file trùng/rỗng (đúng docstring); dùng tên file ổn định theo `path.stem`.

### 3.2 B — Indexing & Dense search

**Task 4 — `src/task4_chunking_indexing.py`**
- `load_documents()`: đọc toàn bộ `.md` dưới `data/standardized/`, gán `doc_type` theo thư mục cha (`legal`/`news`), `id` = đường dẫn tương đối — dùng đúng code mẫu đã comment sẵn trong file.
- `chunk_documents(documents)`: dùng `RecursiveCharacterTextSplitter` từ `langchain-text-splitters` (đã có trong deps), `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50`. Mỗi chunk id dạng `f"{document['id']}::chunk-{index}"`, `metadata.chunk_index` tăng dần từ 0.
- `embed_texts(texts)`: dispatch theo `EMBEDDING_PROVIDER` trong `.env`. Với `sentence_transformers` (mặc định): `SentenceTransformer("BAAI/bge-m3").encode(texts).tolist()`. **Lưu ý rủi ro thời gian**: `BAAI/bge-m3` nặng (~2GB), tải lần đầu có thể mất nhiều phút — bắt đầu tải **ngay từ khối Setup** (chạy `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"` nền trong lúc cả nhóm họp phân vai). Nếu mạng quá chậm, đổi sang model nhỏ hơn (`intfloat/multilingual-e5-small`, dim 384) và cập nhật `EMBEDDING_DIM` tương ứng — nhớ ghi rõ lý do đổi trong báo cáo nhóm.
- `get_collection()`: `chromadb.PersistentClient(path=CHROMA_DIR)`, collection `metadata={"hnsw:space": "cosine"}` — dùng đúng code mẫu.
- `embed_chunks(chunks)`, `index_to_vectorstore(chunks)`: theo code mẫu comment sẵn, dùng `upsert` (không phải `add`) để chạy lại pipeline không tạo dữ liệu trùng.
- Chạy: `python -m src.task4_chunking_indexing` → in ra số chunks đã index.

**Task 5 — `src/task5_semantic_search.py`**
- Cài `semantic_search(query, top_k)`: gọi `embed_texts([query])[0]` rồi `get_collection().query(...)`, đổi cosine distance → similarity bằng `max(0.0, 1.0 - distance)`, trả `SearchResult` với `retrieval_method="dense"`, sort giảm dần theo score.
- Bắt buộc dùng chung `embed_texts` với Task 4 (không tự tạo model embedding riêng) — đây là invariant trong `MODULE_CONTRACTS.md`.

### 3.3 C — Lexical, Fusion, Fallback, Pipeline

**Task 6 — `src/task6_lexical_search.py`**
- `CORPUS`: nạp cùng danh sách chunks đã dùng ở Task 4 (import lại `load_documents` + `chunk_documents` từ `task4_chunking_indexing`, hoặc đọc trực tiếp từ ChromaDB collection để đảm bảo đồng bộ corpus).
- `build_bm25_index(corpus)`: `rank_bm25.BM25Okapi` trên `content.lower().split()`.
- `lexical_search(query, top_k)`: tính score, lấy top_k theo `np.argsort`, bỏ score ≤ 0, trả `retrieval_method="bm25"`.

**Task 7 — `src/task7_reranking.py`**
- `rerank_rrf(ranked_lists, top_k, k)`: công thức `sum(1/(k+rank))`, rank bắt đầu từ 1, chỉ fuse 1 lần trong toàn pipeline (không gọi lại RRF ở nơi khác). Copy code mẫu có sẵn trong comment, gán `retrieval_method="hybrid"`.
- Reranker nâng cao (Jina/BGE cross-encoder) là **không bắt buộc** — bỏ qua trong 4 giờ, để dành làm bonus (+3đ) nếu còn dư thời gian ở cuối.

**Task 8 — `src/task8_pageindex_vectorless.py`** (bản tối giản do giới hạn thời gian)
- Vì đây là dịch vụ ngoài cần API key riêng (`PAGEINDEX_API_KEY`) và không phải trọng số điểm chính (Retrieval pipeline & fallback chỉ 10/90 điểm), làm bản tối giản: nếu `PAGEINDEX_API_KEY` rỗng, `pageindex_search` trả `[]` ngay (không raise ra ngoài task9); nếu có key, thử gọi SDK `pageindex` (đã có trong deps) trong `try/except` và vẫn trả `[]` khi lỗi. Điều này thoả đúng rule "PageIndex/provider lỗi không được làm UI crash" và test `test_retrieve_survives_fallback_provider_error`.
- Nếu nhóm có key thật và còn thời gian, hoàn thiện `upload_documents()` để có fallback thật — ghi rõ trong README/báo cáo đây là phần đã kiểm chứng bằng key thật.

**Task 9 — `src/task9_retrieval_pipeline.py`**
- Cài `retrieve()` đúng code mẫu: `dense = semantic_search(query, top_k*2)`, `sparse = lexical_search(query, top_k*2)`, `hybrid = rerank_rrf([dense, sparse], top_k) if use_reranking else dense[:top_k]`. Fallback so sánh `dense[0]["score"]` (cosine gốc) với `score_threshold`, **không** so với RRF score.
- **Calibrate `SCORE_THRESHOLD`**: chạy thử 3–5 câu hỏi rõ ràng trong domain (nên có score dense cao) và 2–3 câu hỏi ngoài domain (vd. hỏi về thời tiết, nấu ăn — score phải thấp) để chọn giá trị threshold hợp lý (không dùng mù 0.3 mặc định nếu domain của nhóm cho ra thang điểm khác) — ghi lại kết quả calibrate này vào `RESULT.md` (dòng "Fallback threshold and calibration").

### 3.4 D — Generation & UI

**Task 10 — `src/task10_generation.py`**
- `reorder_for_llm(chunks)`: dùng đúng pattern mẫu (chunks quan trọng nhất ở đầu và cuối context để giảm "lost in the middle"), **không được mutate list gốc** (test `test_reorder_is_non_mutating_and_context_contains_source` kiểm tra điều này).
- `format_context(chunks)`: mỗi đoạn phải có `Title` và `Source` để LLM trích dẫn kiểm chứng được.
- `call_llm(system_prompt, user_message)`: dispatch theo `LLM_PROVIDER` (`openai`/`gemini`/`anthropic`), dùng đúng SDK đã có trong deps (`openai`, `google-genai`, `anthropic`) và `LLM_MODEL` từ `.env`. Bọc lỗi gọi API để không crash UI.
- `generate_with_citation(query, top_k)`: nếu `retrieve()` trả rỗng → safe refusal (`retrieval_source="none"`, không sources). Ngược lại retrieve → reorder → format context → gọi LLM → trả `GenerationResult` với `retrieval_source = chunks[0]["retrieval_method"]`.

**`app.py`**
- Thay 3 chỗ `TODO`: gọi `generate_with_citation(query, top_k)` thay vì answer giả; hiển thị `sources` (title, source, score, retrieval_method) dưới mỗi câu trả lời — có thể dùng `st.expander` per source; lưu cả `answer` và `sources` vào `st.session_state.messages` để hiển thị lại khi rerender lịch sử chat.
- Đổi tiêu đề/mô tả sidebar theo đúng chủ đề nhóm chọn (hiện đang là placeholder "Thay mô tả theo đề tài của nhóm").

### 3.5 Cả nhóm — Evaluation (khối 6, 30 phút)

- **Golden dataset**: điền `group_project/evaluation/golden_dataset.json` (hiện đang rỗng) — mảng JSON ≥15 phần tử, mỗi phần tử có `question`, `expected_answer`, `expected_context` (bắt buộc theo `tests/test_acceptance.py::test_golden_dataset_has_15_grounded_cases`). Câu hỏi nên bám corpus thật (học phí, học bổng, ký túc xá...), có cả câu dễ (trực tiếp trong 1 đoạn) và câu khó (cần tổng hợp nhiều đoạn) để evaluation có ý nghĩa.
- **4 metric**: dùng `ragas` (đã có trong deps) để tính faithfulness, answer relevance, context recall, context precision.
- **A/B comparison**: Config A = `retrieve(..., use_reranking=False)` (dense-only), Config B = `retrieve(..., use_reranking=True)` (hybrid+RRF) — giữ nguyên `top_k`, generator, evaluator, prompt giữa hai config, chỉ đổi retrieval strategy.
- Điền toàn bộ bảng trong `group_project/evaluation/RESULT.md` (không còn chữ `TODO` — kiểm tra bởi `test_evaluation_report_is_completed`): overall scores, a/b comparison, worst performers (≥3 case lỗi kèm root cause), recommendations.

## 4. Rủi ro & phương án dự phòng

| Rủi ro | Phương án |
|---|---|
| Website chặn crawler (task2) | Đổi sang nguồn công khai khác cùng chủ đề, không cố vượt WAF |
| `BAAI/bge-m3` tải chậm | Tải nền từ đầu buổi; nếu vẫn chậm, đổi `EMBEDDING_MODEL` nhỏ hơn + cập nhật `EMBEDDING_DIM` |
| Hết quota/API key LLM giữa chừng | Chuẩn bị provider dự phòng thứ 2 trong `.env`, đổi `LLM_PROVIDER` khi cần |
| PageIndex không có key hoặc SDK lỗi | Trả `[]` an toàn (xem mục 3.3) — pipeline vẫn dùng hybrid, không crash |
| Trễ tiến độ ở khối 3–4 | Cắt phần reranker nâng cao và PageIndex thật (đều là bonus/không bắt buộc), dồn thời gian cho generation + evaluation vì đây là phần chiếm điểm nhiều nhất (15đ generation, 10đ evaluation) |
| Golden dataset/RESULT.md không kịp làm kỹ | Ưu tiên đủ 15 câu + 4 metric chạy được trước, phần phân tích lỗi/root cause làm rút gọn nhưng không được để trống (test chỉ check không còn "TODO" và có đủ heading, nhưng giảng viên chấm theo chất lượng nội dung thật) |

## 5. Checklist trước khi nộp (khối 7)

```bash
pytest tests/test_contracts.py -q
pytest tests/test_acceptance.py -q
pytest -q
streamlit run app.py   # demo thủ công
```

- [ ] `data/landing/legal/` ≥3 file PDF/DOCX hợp lệ; `data/landing/news/` ≥5 JSON đủ field
- [ ] `data/standardized/legal|news/` có Markdown tương ứng, không rỗng
- [ ] `chroma_db/` có dữ liệu, `semantic_search`/`lexical_search`/`rerank_rrf`/`retrieve` chạy đúng contract
- [ ] `generate_with_citation` trả lời có citation đối chiếu được với `sources`; safe refusal khi thiếu evidence
- [ ] `app.py` hiển thị answer + sources + retrieval method + score
- [ ] `group_project/evaluation/golden_dataset.json` ≥15 câu; `group_project/evaluation/RESULT.md` hết `TODO`
- [ ] Mỗi thành viên có `reports/<mssv>-<ten>.md` điền từ template `reports/INDIVIDUAL_REPORT.md`
- [ ] Không commit `.env`, API key, hoặc cache (`chroma_db/` nên thêm vào `.gitignore` nếu chưa có — kiểm tra trước khi `git add`)
- [ ] Chuẩn bị demo: 1 query đúng domain, 1 query ngoài domain (test fallback/safe refusal), kết quả A/B
