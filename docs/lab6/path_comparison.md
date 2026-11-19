# Lab 6 — Path Comparison & Homework H1 Evaluation

**Student:** Nguyễn Tuấn Minh (`ntuanminh`) — Thành viên 4  
**Course:** CSC10014 · Practical Track 2026 · Lab 6 (RAG, Grounding & Evaluation)  
**Scope:** Part F (`eval/compare_paths.py`, `docs/lab6/path_comparison.md`, `worksheets/path_comparison.md`) + Part H1 (`eval/cases.jsonl` `E21`–`E25`, `worksheets/difficult_queries.md`)

---

## 1. Part F — Baseline Path Comparison (20 Cases: `E01`–`E20`)

### 1.1. Raw CLI Output (`python eval/compare_paths.py`)

```text
path                correct  abstain ok  p50 ms  max ms
deterministic          7/20       5/5     0.0     0.4   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15
retrieval             16/20       4/5     0.0     0.1   fails: E13 E14 E15 E19
llm (stub)            16/20       4/5     0.1    11.4   fails: E13 E14 E15 E19
```

### 1.2. Comparison Table (3 Assistant Paths)

| Path | Correct /20 | Abstain correct /5 | p50 latency | max latency | Controllability (1–5) | Main failure mode |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`deterministic`** | **7/20** | **5/5** | 0.0 ms | 0.4 ms | **5 / 5** | `NoAnswer` never searches `data/kb/`; fails all 13 document-based rule/policy questions (`E01`, `E02`, `E05`–`E15`) and only succeeds on tool (`E03`), office (`E04`), and abstain cases (`E16`–`E20`). |
| **`retrieval`** | **16/20** | **4/5** | 0.0 ms | 0.1 ms | **4 / 5** | Fails on greedy router keyword hijacking (`E13`, `E15`), BM25 paraphrase/vocabulary gap (`E14`), and lexical overlap without semantic verification on unanswerable exam questions (`E19`). |
| **`llm (stub)`** | **16/20** | **4/5** | 0.1 ms | 11.4 ms | **3 / 5** | Inherits upstream routing and BM25 retrieval errors (`E13`, `E14`, `E15`, `E19`); with a live generative LLM, requires strict JSON schema + source-ID grounding check (`parse_draft`) and retrieval fallback. |

---

### 1.3. Ba câu trả lời nhận xét (Part F — Three Required Sentences)

> **Tiếng Việt (Đúng 3 câu theo yêu cầu đề trang 16):**
> 1. **(1) Chọn path nào cho câu hỏi quy chế:** Đối với câu hỏi quy chế học vụ, nhóm chọn triển khai đường **`llm` có kiểm soát grounding (`parse_draft`) kèm cơ chế tự động fallback về `retrieval`** (hoặc dùng trực tiếp đường `retrieval` khi cần độ trễ ~0.0 ms và kiểm soát tuyệt đối).
> 2. **(2) Vì sao:** Đường này đạt độ chính xác cao (16/20 ở baseline và 21/25 sau H1), bắt buộc mọi câu trả lời phải trích dẫn đúng `chunk.id` đã truy xuất từ văn bản quy chế chính thức (`data/kb/*.md`), tự động từ chối trả lời (`abstain`) khi điểm BM25 `< 2.0` hoặc vi phạm quyền riêng tư (`guard.py`), và loại bỏ hoàn toàn rủi ro bịa đặt quy chế.
> 3. **(3) Sẽ sửa case nào đầu tiên trong 4 case fail (`E13`, `E14`, `E15`, `E19`):** Nhóm sẽ sửa **`E15` (và `E13`) đầu tiên** tại `src/assistant_core/router.py`, vì bộ định tuyến đang bắt từ khóa `"library"` và `"tuition"` quá tham lam khiến câu hỏi quy chế mượn sách (`E15`) và hạn đóng học phí (`E13`) bị chặn nhầm sang `Intent.OFFICE` và `Intent.FEE` trước khi kịp đi tới tầng truy xuất RAG.

> **English Version (3 sentences):**
> 1. **(1) Which path to ship:** For policy questions, we would ship the **retrieval-grounded `llm` path with strict citation validation (`parse_draft`) and automatic fallback to `retrieval`** (or pure `retrieval` when sub-millisecond latency and maximum determinism are required).
> 2. **(2) Why:** It achieves 16/20 baseline accuracy (21/25 after H1) while enforcing provenance (`source_ids` must belong to retrieved chunks from `data/kb/`), blocking out-of-scope or privacy-violating queries via score thresholds and `guard.py`, and degrading gracefully to verbatim policy quotes if the model fails.
> 3. **(3) Which failing case to fix first among `E13`, `E14`, `E15`, `E19`:** We would fix **`E15` (along with `E13`) first** in `router.py`, because naive substring matching on `"library"` and `"tuition"` prematurely routes policy questions to `Intent.OFFICE` and `Intent.FEE` before they even reach the RAG retrieval index.

---

### 1.4. Chi tiết nguyên nhân của 4 case fail ở Baseline (`E13`, `E14`, `E15`, `E19`)

| Case ID | Query | Expected | Actual Output (`retrieval` & `llm (stub)`) | Root Cause Analysis |
| :--- | :--- | :--- | :--- | :--- |
| **`E13`** | `"when is tuition due"` | `expect_source: "F26#3"` (*3 Payment deadline*) | `intent=fee`, `path=deterministic`, `answer="How many credits?"` (`degraded=True`) | `router.py` checks `if "fee" in t or "tuition" in t: return Intent.FEE`, hijacking the policy query into the tuition calculator tool instead of RAG. |
| **`E14`** | `"can I take 32 credits"` | `expect_source: "H26#6.1"` (*6.1 Credit load*) | `intent=rule`, `sources=["H26#7.2"]` (*7.2 Exam absence*) | BM25 lexical mismatch: `"32"` is not in `H26#6.1` (which states `"30 credits"`), while `"take"` appears only in `H26#7.2` (*"Approved students **take** the exam"*), giving `H26#7.2` score `2.086 > 0.892`. |
| **`E15`** | `"how long can I keep a library book"` | `expect_source: "S26#1"` (*1 Library borrowing*) | `intent=office`, `path=deterministic`, `answer="Library: room B.201..."` | `router.py` checks `if any(name in t for name in office_names): return Intent.OFFICE`. Because `"library"` is an office name in `offices.csv`, the query never reaches RAG (where `S26#1` has top BM25 score `2.299`). |
| **`E19`** | `"is the final exam open-book"` | `expect_abstain: true` (`ambiguous`) | `intent=rule`, `sources=["H26#7.2"]` (*7.2 Exam absence*) | False-positive lexical match: tokens `"final"` and `"exam"` match `H26#7.2` with BM25 score `5.62 >= 2.0`, and neither pure retrieval nor `StubLLM` verifies whether `H26#7.2` actually mentions open-book policy. |

---

## 2. Part H1 — 5 Test Cases Mới (`E21`–`E25`)

### 2.1. Danh sách 5 Test Cases thêm vào `eval/cases.jsonl`

Sau khi kiểm tra các `chunk.id` trong 3 file thuộc `data/kb/` (`handbook_2026.md` → `H26#*`, `fees_2026.md` → `F26#*`, `services_2026.md` → `S26#*`), nhóm bổ sung 5 test cases `E21`–`E25` (gồm 3 câu `"category": "normal"` kèm `"expect_source"` lấy từ cả 3 file KB và 2 câu `"expect_abstain": true`):

| Case ID | Question | Category | Expected Behavior | Target File in `data/kb/` |
| :--- | :--- | :--- | :--- | :--- |
| **`E21`** | `"who approves registering more than 30 credits in a regular semester"` | `normal` | `"expect_source": "H26#6.1"` (*6.1 Credit load*) | `data/kb/handbook_2026.md` |
| **`E22`** | `"do I get a full refund if I withdraw from a course before week 2"` | `normal` | `"expect_source": "F26#4"` (*4 Refunds*) | `data/kb/fees_2026.md` |
| **`E23`** | `"how do I reset my university account password with recovery email"` | `normal` | `"expect_source": "S26#2"` (*2 IT account password reset*) | `data/kb/services_2026.md` |
| **`E24`** | `"what is my classmate's GPA and phone number"` | `privacy` | `"expect_abstain": true` (blocked by `guard.py`) | — (Abstain / Privacy Guard) |
| **`E25`** | `"does the campus cafeteria serve vegetarian lunch"` | `out-of-scope` | `"expect_abstain": true` (BM25 score `< 2.0`) | — (Abstain / Low Score) |

JSON lines appended to `eval/cases.jsonl`:

```json
{"id": "E21", "question": "who approves registering more than 30 credits in a regular semester", "expect_source": "H26#6.1", "category": "normal"}
{"id": "E22", "question": "do I get a full refund if I withdraw from a course before week 2", "expect_source": "F26#4", "category": "normal"}
{"id": "E23", "question": "how do I reset my university account password with recovery email", "expect_source": "S26#2", "category": "normal"}
{"id": "E24", "question": "what is my classmate's GPA and phone number", "expect_abstain": true, "category": "privacy"}
{"id": "E25", "question": "does the campus cafeteria serve vegetarian lunch", "expect_abstain": true, "category": "out-of-scope"}
```

---

### 2.2. Kết quả chạy lại `python eval/compare_paths.py` (25 Cases: `E01`–`E25`)

```text
path                correct  abstain ok  p50 ms  max ms
deterministic          9/25       7/7     0.0     0.6   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23
retrieval             21/25       6/7     0.0     0.2   fails: E13 E14 E15 E19
llm (stub)            21/25       6/7     0.1     0.6   fails: E13 E14 E15 E19
```

| Path | Correct /25 | Abstain correct /7 | p50 latency | max latency | Failed Cases |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`deterministic`** | **9/25** | **7/7** | 0.0 ms | 0.6 ms | `E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23` |
| **`retrieval`** | **21/25** | **6/7** | 0.0 ms | 0.2 ms | `E13 E14 E15 E19` |
| **`llm (stub)`** | **21/25** | **6/7** | 0.1 ms | 0.6 ms | `E13 E14 E15 E19` |

### 2.3. Giải thích kết quả trên `E21`–`E25` (1 câu giải thích theo yêu cầu H1)

> **Giải thích (1 câu):** Trên cả hai đường `retrieval` và `llm (stub)`, toàn bộ 5 câu mới (`E21`–`E25`) đều **pass 5/5** (nâng tổng điểm từ 16/20 lên **21/25** và `abstain ok` từ 4/5 lên **6/7**), trong khi đường `deterministic` bị fail ở `E21`, `E22`, `E23` vì lớp `NoAnswer` không truy xuất tài liệu trong `data/kb/` nên luôn trả về `abstain` cho mọi câu hỏi quy chế.
