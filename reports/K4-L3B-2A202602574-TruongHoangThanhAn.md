# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

#### Thông tin

- Họ và tên: Trương Hoàng Thành An
- Mã học viên: 2A202602574
- Nhóm: team số 4 — chủ đề du lịch văn hóa ẩm thực Hà Nội
- Repository/branch: [github.com/vudang142/K4-L3B-RAG-Pipeline/tree/TruongHoangThanhAn](https://github.com/vudang142/K4-L3B-RAG-Pipeline/tree/TruongHoangThanhAn)

## Phần việc đã thực hiện

| Module/deliverable             | Việc tôi trực tiếp làm                                                                                                                                                          | File/commit/PR                                                        | Trạng thái |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- | ------------ |
| Kế hoạch nhóm               | Viết plan phân vai 4 role, timeline 4 giờ, rủi ro và checklist nộp bài                                                                                                        | `plan.md` — commit `08bdd9e`                                     | Done         |
| Task 1 — Thu thập tài liệu | Cài`download_documents()`: ghi nguồn trích dẫn của 3 PDF, bỏ qua file đã có, chỉ nhận response là PDF/DOCX thật, kiểm tra ≥3 file >1KB                              | `src/task1_collect_legal_docs.py`                                   | Done         |
| Task 2 — Crawl tin            | Chạy crawl 5 URL bằng Crawl4AI (trong`.venv`), kiểm tra 5 JSON đủ 4 field                                                                                                     | `data/landing/news/*.json` — commit `1658b15`                    | Done         |
| Task 3 — Chuẩn hóa Markdown | Cài`convert_legal_docs()` (MarkItDown) và `convert_news_articles()` (header title/url/date); tên file theo `path.stem` nên chạy lại không tạo trùng                   | `src/task3_convert_markdown.py` — commit `1658b15`               | Done         |
| Task 4 — Chunking/Indexing    | Cài load/chunk/embed/upsert ChromaDB (cosine); sửa lỗi không nạp`.env` và batch + retry embedding Gemini; index 429 chunks                                                   | `src/task4_chunking_indexing.py` — commit `3729a1f`, `1658b15` | Done         |
| Task 5 — Semantic search      | Cài`semantic_search()` dùng chung `embed_texts()` với Task 4, đổi cosine distance → similarity                                                                             | `src/task5_semantic_search.py` — commit `3729a1f`                | Done         |
| Tích hợp Role C              | Review nhánh`Khánh-Linh`, chỉ lấy task6–9 (bỏ các thay đổi xóa PDF/plan.md do nhánh rẽ từ commit cũ), chạy test rồi merge vào `TruongHoangThanhAn` và `main` | commit`1658b15`                                                     | Done         |
| Task 9 — Calibrate threshold  | Thay bộ câu hỏi calibrate sai domain (đại học) bằng câu hỏi du lịch ẩm thực, đo và chọn`SCORE_THRESHOLD = 0.73`                                                     | `src/task9_retrieval_pipeline.py`                                   | Done         |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Embed bằng Gemini `gemini-embedding-001` (768 chiều), gửi theo batch 20 chunk/lần, nghỉ 2 giây giữa các batch và retry 40 giây khi gặp lỗi 429.
   **Lý do/evidence:** Gửi cả 429 chunk trong một lần gọi bị lỗi `400 at most 100 requests can be in one batch`; chia batch lớn thì vượt quota free tier (`429 RESOURCE_EXHAUSTED`, 100 request/phút). Sau khi sửa, `python -m src.task4_chunking_indexing` in `Indexed 429 chunks`. `sentence-transformers` không có trong dependency nên không dùng provider local.
   **Trade-off:** Index lại mất vài phút và phụ thuộc quota/API key Gemini. Đổi bù, nhóm không phải tải model ~2GB về máy.
2. **Quyết định:** Chọn `SCORE_THRESHOLD = 0.73` dựa trên dense cosine score, không dùng mặc định 0.3.
   **Lý do/evidence:** Chạy calibrate trên 5 câu đúng chủ đề (score 0.779–0.878) và 3 câu ngoài chủ đề (0.564–0.682). Hai dải không chồng nhau, nên lấy điểm giữa 0.73. Nếu để 0.3, fallback sẽ không bao giờ được kích hoạt. Bộ câu cũ còn xếp "Cách nấu phở bò ngon?" vào nhóm ngoài chủ đề, trong khi câu này đúng chủ đề ẩm thực của nhóm.
   **Trade-off:** Chỉ có 8 câu calibrate. Một câu đúng chủ đề nhưng hỏi về chi tiết hiếm có thể rơi dưới 0.73 và bị chuyển sang fallback.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest tests/ -q`; `python -m src.task5_semantic_search`; `python -m src.task9_retrieval_pipeline "ẩm thực Hà Nội có món gì ngon"`; calibrate bằng `python -m src.task9_retrieval_pipeline`.
- Kết quả trước/sau nếu có: trước khi sửa, `chroma_db/` không tồn tại và mọi test retrieval fail vì `NotImplementedError`. Sau khi sửa, `pytest` đạt 17/20 pass. 3 test còn fail thuộc task10 (Role D) và phần evaluation của cả nhóm.
- Lỗi đã phát hiện và cách xử lý:
  - Task 4 không gọi `load_dotenv()`, nên âm thầm dùng `sentence_transformers` (chưa cài) thay vì Gemini. Đã thêm `load_dotenv()`.
  - Nhánh `Khánh-Linh` rẽ từ commit cũ, nếu merge cả nhánh sẽ xóa 3 PDF và `plan.md`. Tôi chỉ lấy 4 file task6–9.
  - Script chạy bằng Python hệ thống báo thiếu `crawl4ai`. Chạy bằng `.venv/Scripts/python.exe` thì hết lỗi.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: chunk cố định 500 ký tự cắt ngang các bảng số liệu trong PDF nghiên cứu. Nhiều chunk chỉ còn các dòng số, không có tên cột, nên vẫn đạt dense score cao (~0.57) với cả câu "test query". Ngoài ra, khi chưa có `PAGEINDEX_API_KEY`, câu ngoài chủ đề dù dưới threshold vẫn nhận lại kết quả hybrid, nên việc từ chối trả lời phải do prompt của task10 đảm nhận.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: chunk theo cấu trúc Markdown (heading/bảng) để giữ bảng số liệu nguyên vẹn, và trả `[]` khi dense score dưới threshold mà fallback rỗng, để pipeline tự từ chối trả lời mà không phụ thuộc LLM.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Trương Hoàng Thành An
