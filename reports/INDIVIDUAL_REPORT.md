# Individual contribution report

---

## Thông tin

- **Họ và tên:** Vũ Hải Đăng
- **Mã học viên:** 2A202602821
- **Nhóm:** K4-L3B
- **Repository/branch:** https://github.com/vudang142/K4-L3B-RAG-Pipeline

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1: Thu thập tài liệu pháp lý | Thiết kế SOURCES dict, implement download + validate PDF/DOCX | `src/task1_collect_legal_docs.py` | Done |
| Task 2: Crawl tin tức | Implement crawl_single() với Crawl4AI, crawl_all() | `src/task2_crawl_news.py` | Done |
| Task 3: Convert Markdown | Convert legal + news bằng MarkItDown, giữ metadata | `src/task3_convert_markdown.py` | Done |


---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chọn hybrid RRF làm retrieval mặc định
   - **Lý do/evidence:** A/B test cho thấy Config B thắng ở cả 4 metrics, đặc biệt faithfulness đạt 1.0 so với 0.94 của dense-only
   - **Trade-off:** Latency tăng ~1.3s/câu nhưng recall/faithfulness cải thiện đáng kể

2. **Quyết định:** Dùng `SCORE_THRESHOLD = 0.73` cho fallback
   - **Lý do/evidence:** Calibrate với 5 câu in-domain (0.779-0.878) và 3 câu out-domain (0.564-0.682), hai dải không overlap
   - **Trade-off:** Threshold phụ thuộc corpus, cần re-calibrate nếu đổi dataset

---

## Kiểm thử và kết quả

- **Test đã dùng:**
  - `pytest tests/test_contracts.py -q` - verify contracts ✓
  - A/B evaluation trên 17 câu golden dataset

- **Kết quả A/B:**
  | Metric | Config A (dense) | Config B (hybrid+RRF) | Delta |
  |--------|-----------------|----------------------|-------|
  | Faithfulness | 0.9412 | **1.0000** | +0.0588 |
  | Answer relevance | 0.8887 | **0.9155** | +0.0268 |
  | Context recall | 0.7843 | **0.8235** | +0.0392 |
  | Average | 0.7973 | **0.8294** | +0.0321 |

- **Lỗi đã phát hiện:**
  - PDF 2 cột: MarkItDown trích xuất xen kẽ dòng → cần dùng pdfplumber với sort=True
  - Câu hard (multi-hop): top_k=5 không đủ → cần tăng top_k hoặc chunk theo document

---

## Điều còn hạn chế

- **Hạn chế:** PageIndex fallback chưa test thực tế (cần PAGEINDEX_API_KEY)
- **Nếu có thêm thời gian:** Sửa PDF extraction dùng layout-aware reader, thử conversation memory cho follow-up questions

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 2026-09-25
- **Tên thành viên:** Vũ Hải Đăng
