# Individual contribution report

---

#### Thông tin

- Họ và tên: Phan Thị Khánh Linh
- Mã học viên: 2A202602310
- Nhóm: team số 4 — chủ đề du lịch văn hóa ẩm thực Hà Nội
- Repository/branch: [github.com/vudang142/K4-L3B-RAG-Pipeline/tree/Khánh-Linh](https://github.com/vudang142/K4-L3B-RAG-Pipeline/tree/Kh%C3%A1nh-Linh)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
| ------------------ | --------------------------- | -------------- | ------------ |
| Task 6 — Lexical search (BM25) | Cài `build_bm25_index`, `lexical_search`; tokenize bỏ dấu câu, cache index, lọc chunk không chứa từ khóa nào của query | `src/task6_lexical_search.py` | Done |
| Task 7 — RRF fusion | Cài `rerank_rrf`: gộp điểm theo `1/(k+rank)`, mỗi ranked list chỉ tính 1 lần cho mỗi chunk, sort ổn định | `src/task7_reranking.py` | Done |
| Task 8 — PageIndex fallback | Cài `upload_documents`, `pageindex_search`: upload PDF, lưu mapping doc_id, query có timeout, trả `[]` an toàn khi thiếu key hoặc lỗi | `src/task8_pageindex_vectorless.py` | Done |
| Task 9 — Retrieval pipeline | Cài `retrieve()`: dense + BM25 → RRF (nếu bật hybrid) → fallback PageIndex khi dense score dưới threshold | `src/task9_retrieval_pipeline.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** `lexical_search` lọc theo việc chunk có chứa ít nhất một từ khóa của query (dùng `bm25.doc_freqs`), thay vì chỉ lọc `score > 0`.
   **Lý do/evidence:** Với corpus nhỏ, BM25Okapi có thể cho IDF = 0 ở một số từ phổ biến khiến score bằng 0 dù chunk vẫn thực sự khớp từ khóa; lọc theo `score > 0` sẽ bỏ sót các chunk này.
   **Trade-off:** Cách lọc này có thể giữ lại vài chunk match yếu (chỉ trùng 1 từ không quan trọng), nhưng an toàn hơn là bỏ sót kết quả đúng.
2. **Quyết định:** RRF chỉ tính điểm một lần cho mỗi chunk trong cùng một ranked list (bỏ qua nếu chunk xuất hiện lặp).
   **Lý do/evidence:** Tránh một chunk được cộng dồn điểm nhiều lần nếu vô tình xuất hiện lặp trong list dense hoặc sparse, giữ đúng công thức RRF chuẩn.
   **Trade-off:** Không có, đây là điều kiện đúng theo định nghĩa RRF.

## Kiểm thử và kết quả

- Test đã dùng: `pytest tests/test_contracts.py -q` cho các test `test_lexical_search_returns_bm25_contract`, `test_rrf_uses_rank_deduplicates_and_marks_hybrid`, `test_retrieve_uses_dense_score_for_fallback`, `test_retrieve_fuses_once_when_dense_is_confident`, `test_retrieve_survives_fallback_provider_error`.
- Kết quả: toàn bộ test trên đều pass sau khi merge vào nhánh chính.
- Lỗi đã phát hiện và cách xử lý: PageIndex SDK chỉ nhận PDF, không nhận Markdown → giới hạn `upload_documents` chỉ upload file `.pdf` trong `data/landing/legal/`, bỏ qua `.gitkeep`. Khi thiếu `PAGEINDEX_API_KEY` hoặc SDK lỗi/timeout, `pageindex_search` trả `[]` để không làm crash `retrieve()`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: khi không có `PAGEINDEX_API_KEY`, fallback luôn trả `[]`, nên với câu hỏi có dense score thấp mà không dùng hybrid, pipeline sẽ không có cách nào trả lời được dù thông tin có thể có trong corpus.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: bổ sung một fallback đơn giản không cần API ngoài (ví dụ mở rộng BM25 với `top_k` lớn hơn) cho trường hợp chưa có `PAGEINDEX_API_KEY`.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 26/09/2026
- Tên thành viên: Phan Thị Khánh Linh
