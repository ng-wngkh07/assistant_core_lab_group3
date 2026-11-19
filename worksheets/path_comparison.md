# Lab 6 — Three assistant paths

Run `python eval/compare_paths.py` and fill in.

## 1. Baseline Measurement (20 Cases: `E01`–`E20`)

```text
path                correct  abstain ok  p50 ms  max ms
deterministic          7/20       5/5     0.0     0.4   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15
retrieval             16/20       4/5     0.0     0.1   fails: E13 E14 E15 E19
llm (stub)            16/20       4/5     0.1    11.4   fails: E13 E14 E15 E19
```

| Path | Correct /20 | Abstain correct /5 | p50 latency | Controllability (1–5) | Main failure mode |
|---|---|---|---|---|---|
| deterministic | 7/20 | 5/5 | 0.0 ms | 5 | Cannot answer any document-based policy/rule questions (`E01`, `E02`, `E05`–`E15`); only handles tools, office lookup, and abstentions. |
| retrieval | 16/20 | 4/5 | 0.0 ms | 4 | Router greedy keyword hijacking (`E13`, `E15`), BM25 lexical/paraphrase mismatch (`E14`), and false positive keyword overlap on ambiguous queries (`E19`). |
| llm (provider: stub) | 16/20 | 4/5 | 0.1 ms | 3 | Inherits upstream routing/BM25 retrieval failures (`E13`, `E14`, `E15`, `E19`) and relies on schema/grounding checks plus retrieval fallback to prevent ungrounded answers. |

## 2. Reflection — Which path would you ship for policy questions, and why? (3 sentences)

**English (3 sentences):**
1. For policy questions, we would ship the **retrieval-grounded `llm` path (with strict `parse_draft` citation validation and automatic fallback to the `retrieval` path)**, or pure `retrieval` when zero hallucination tolerance and sub-millisecond latency are prioritized.
2. This architecture combines high accuracy (16/20 on baseline, 21/25 after H1) with strict controllability by ensuring every answer cites retrieved official KB chunks (`H26`, `F26`, `S26`), abstains when `score < 2.0` or privacy guards trigger, and gracefully degrades to verbatim source quotes on provider failure.
3. Among the four failing cases (`E13`, `E14`, `E15`, `E19`), we would fix **`E15` (and `E13`) first** in `router.py`, because greedy substring matching on `"library"` and `"tuition"` hijacks valid policy queries into `Intent.OFFICE` and `Intent.FEE` before they ever reach the RAG index.

**Tiếng Việt (3 câu trả lời):**
1. Đối với các câu hỏi quy chế học vụ, nhóm chọn triển khai đường **`llm` kết hợp RAG có kiểm tra trích dẫn (`parse_draft`) và tự động fallback về `retrieval`** (hoặc dùng trực tiếp `retrieval` nếu ưu tiên độ trễ ~0.0 ms và kiểm soát tuyệt đối).
2. Lý do là đường này vừa đạt độ chính xác cao (16/20 ở baseline và 21/25 sau H1), vừa đảm bảo mọi câu trả lời đều bám sát văn bản quy chế chính thức thông qua mã nguồn trích dẫn (`source_ids`), chặn rò rỉ dữ liệu cá nhân qua `guard.py` và loại bỏ rủi ro bịa đặt (hallucination).
3. Trong 4 case bị fail (`E13`, `E14`, `E15`, `E19`), nhóm sẽ sửa **`E15` (cùng `E13`) đầu tiên** tại `router.py`, vì bộ định tuyến đang bắt từ khóa `"library"` và `"tuition"` quá tham lam khiến câu hỏi quy chế bị đẩy nhầm sang `Intent.OFFICE` và `Intent.FEE` trước khi kịp đi vào bộ truy xuất BM25.

---

## 3. Post-H1 Measurement (25 Cases: `E01`–`E25`)

```text
path                correct  abstain ok  p50 ms  max ms
deterministic          9/25       7/7     0.0     0.6   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23
retrieval             21/25       6/7     0.0     0.2   fails: E13 E14 E15 E19
llm (stub)            21/25       6/7     0.1     0.6   fails: E13 E14 E15 E19
```
