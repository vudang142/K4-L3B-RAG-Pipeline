# RAG evaluation results

## Run information

| Field                              | Value |
| ----------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | ragas 0.4.3 |
| Evaluator model                    | gemini-3.5-flash-lite (LangchainLLMWrapper qua endpoint OpenAI-compatible) |
| Generator model                    | gemini-3.5-flash-lite (`LLM_PROVIDER=gemini` trong `.env`) |
| Embedding model                    | gemini-embedding-001, 768 chiều (dùng chung `embed_texts()` của Task 4 cho cả retrieval và metric answer relevancy) |
| Corpus version/commit              | 6eed331 (3 PDF legal + 5 bài news, 429 chunks đã index trong ChromaDB) |
| Golden dataset size                | 17 câu (12 easy/medium 1-hop, 3 medium suy luận từ 1 đoạn dài, 1 hard cần gộp 4 tài liệu) |
| `top_k`                            | 5 |
| Fallback threshold and calibration | `SCORE_THRESHOLD = 0.73`, calibrate bằng 5 câu trong domain (dense score 0,779–0,878) và 3 câu ngoài domain (0,564–0,682) — xem `python -m src.task9_retrieval_pipeline`. Hai dải không chồng nhau nên chọn điểm giữa. |

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)` — chỉ dùng `semantic_search` (ChromaDB cosine).
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)` — `semantic_search` + `lexical_search` (BM25) hợp nhất bằng `rerank_rrf` (k=60).

Hai config dùng cùng golden dataset, cùng generator (`gemini-3.5-flash-lite`), cùng evaluator, cùng `SYSTEM_PROMPT`, cùng `top_k=5`; chỉ khác `use_reranking`. Script: `group_project/evaluation/run_evaluation.py`, raw output: `group_project/evaluation/results/{answers,scores}_{A,B}.json`.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.9412 |   1.0000 |   +0.0588 |
| Answer relevance  |   0.8887 |   0.9155 |   +0.0268 |
| Context recall    |   0.7843 |   0.8235 |   +0.0392 |
| Context precision |   0.5750 |   0.5784 |   +0.0034 |
| **Average**       |   0.7973 |   0.8294 |   +0.0321 |

Ngoài 4 metric, đo thêm: refusal rate (A: 1/17, B: 0/17) và latency trung bình (A: 6,17s/câu, B: 7,48s/câu — B chậm hơn vì gọi thêm BM25 + RRF).

## A/B comparison

- Cấu hình tốt hơn: **Config B (hybrid + RRF)**, thắng ở cả 4 metric, đặc biệt faithfulness đạt tuyệt đối (1.0 so với 0.9412) và không có câu nào bị từ chối trả lời (0 so với 1).
- Evidence: câu "Mô hình hồi quy trong nghiên cứu du lịch ẩm thực đường phố Hà Nội giải thích được bao nhiêu %?" — Config A có best dense score dưới 0.73 nên kích hoạt fallback, `pageindex_search` trả `[]` (chưa có `PAGEINDEX_API_KEY`), pipeline trả safe refusal → điểm 0 ở cả 4 metric. Config B: BM25 khớp từ khóa "78,6%", "hồi quy" đẩy đúng chunk-26 lên qua RRF dù dense score thấp, LLM trả lời đúng và trích dẫn `[Document 4]`.
- Trade-off về latency/cost: B chậm hơn A khoảng 1,3s/câu (embed câu hỏi 1 lần + BM25 tại chỗ + RRF, không gọi thêm LLM) — chi phí tăng không đáng kể so với mức tăng recall/faithfulness, nên đánh đổi này đáng chấp nhận cho corpus quy mô nhỏ (429 chunks) của nhóm.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Mô hình hồi quy trong nghiên cứu du lịch ẩm thực đường phố Hà Nội giải thích được bao nhiêu %? | A | 0.0 | 0.0 | 0.0 | 0.0 | retrieval (fallback) | Best dense cosine score dưới `SCORE_THRESHOLD=0.73` kích hoạt fallback; `pageindex_search` trả `[]` vì thiếu `PAGEINDEX_API_KEY` → an toàn nhưng mất hẳn câu trả lời đáng lẽ có trong corpus. Config B (hybrid) trả lời đúng cho cùng câu này. |
|   2 | Vì quảng bá là yếu tố ảnh hưởng lớn nhất, nghiên cứu kiến nghị Sở Du lịch Hà Nội làm gì? | A & B | 1.0 | 0.76–0.88 | 0.0 | 0.0 | data (PDF extraction) | PDF `MOT_SO_YEU_TO_ANH_HUONG_...pdf` có layout 2 cột; MarkItDown trích xuất xen kẽ dòng giữa 2 cột (ví dụ chunk-70 lẫn "Một là, Quảng bá..." với "Ba là, Văn hóa ẩm thực..."). LLM sinh câu trả lời đúng, nhưng context bị nhiễu chữ khiến metric context recall/precision (so khớp câu chữ với reference) chấm 0 dù nội dung đúng. |
|   3 | Bún chả được nhắc đến như thế nào trong các nguồn, và có thể ăn bún chả ở những quán nào? | A & B | 1.0 | 0.76–0.91 | 0.0 | 0.0 | retrieval (multi-hop) | Câu hỏi "hard" cần gộp thông tin từ 4 tài liệu khác nhau (2 bài báo + 1 nghiên cứu). `top_k=5` chỉ lấy được 1-2 nguồn, recall thấp so với `expected_context` liệt kê đủ 4 nguồn. Retrieval hoạt động đúng nhưng câu hỏi vượt khả năng tổng hợp của single-hop retrieval. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bật `use_reranking=True` (hybrid) làm mặc định trong `app.py`/production, không dùng dense-only | Case #1: dense-only refuse hoàn toàn một câu có đáp án rõ ràng trong corpus; hybrid trả lời đúng | Giảm refusal rate về 0, tăng average score +0.032 | Chạy lại `run_evaluation.py --configs A B` sau khi đổi default, so `refusals` trong `summary.json` |
|        2 | Sửa `convert_legal_docs()` (task3) dùng chế độ đọc PDF theo layout cột (`pdfplumber`/`PyMuPDF` với `sort=True`) thay vì MarkItDown mặc định cho các PDF khoa học nhiều cột | Case #2: nội dung đúng nhưng bị xáo trộn thứ tự dòng giữa 2 cột làm hỏng context cho cả người đọc lẫn metric | Context precision/recall cho các câu liên quan `MOT_SO_YEU_TO_...pdf` tăng từ ~0 lên gần với các case khác (~0.3–0.5) | Re-convert, re-index, chạy lại đúng 5 câu liên quan file này trong golden dataset |
|        3 | Với câu hỏi multi-hop (như case #3), tăng `top_k` hoặc thêm bước gộp theo `doc_type`/nguồn trước khi đưa vào context, thay vì lấy top-5 chunk phẳng | Case #3: 4/4 nguồn liên quan tồn tại trong corpus nhưng chỉ 1-2 lọt vào top-5 | Context recall cho câu multi-hop tăng, không ảnh hưởng câu 1-hop (giữ `top_k=5` cho câu dễ) | Thêm cờ `top_k` lớn hơn (vd 8) riêng cho câu multi-hop trong golden dataset, so sánh recall trước/sau |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | ------------------: | ---------- |
| Chưa thực hiện | — | — | — | Nhóm ưu tiên hoàn thành A/B chính (dense vs hybrid) trong thời gian sprint; PageIndex fallback thật (cần `PAGEINDEX_API_KEY`) và thử `top_k` khác nhau để lại làm bonus nếu còn thời gian. |
