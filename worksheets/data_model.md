# Lab 5 Data Model Design Review (Bonus H3)

**Author:** Hoàng Bách (Thành viên 4)  
**Course:** CSC10014 · Data & SQL Persistence  
**Reference Schema:** `sql/bad_schema.sql` vs Normalized 3-Table Schema (`chat_session`, `interaction`, `feedback`)

---

## 1. Context & Objective

In `sql/bad_schema.sql`, an assistant logging database was designed as a single flat table:

```sql
CREATE TABLE assistant_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    student_name TEXT,
    student_phone TEXT,
    session_id TEXT,
    full_question_text TEXT,
    answer_text TEXT,
    intent TEXT,
    topic TEXT,
    resolved TEXT,
    degraded INTEGER,
    latency_ms REAL,
    feedback_rating INTEGER,
    feedback_comment TEXT,
    created_at TEXT
);
```

While seemingly simple, this naive design introduces major security, architectural, and data integrity problems. Below are three critical problems identified in `bad_schema.sql` and how our improved architecture fixes each.

---

## 2. Three Critical Problems and Our Solutions

### Problem 1: Violation of Privacy and Data Minimization (PDPA Compliance)
* **The Flaw:** `bad_schema.sql` stores plaintext Personal Identifiable Information (PII) including `student_id`, `student_name`, `student_phone`, and raw `full_question_text` alongside raw `session_id`.
* **The Risk:** 
  - Students frequently paste personal data, credentials, or sensitive queries into chat messages. Storing raw question text and identities permanently exposes users to data breaches, identity theft, and violates Vietnam's Personal Data Protection Law (Decree 13/2023/ND-CP).
  - No feature requires knowing the real identity of the student to provide academic handbook rules or office information.
* **Our Solution:**
  - **Zero PII Storage:** Neither student names, phone numbers, nor raw prompt texts are ever stored in the database.
  - **Salted One-Way Hashing:** Session IDs are hashed via `SHA-256(salt + raw_session)[:16]`. Conversations can still be grouped into distinct sessions for analytics without reverse-engineering user identity.
  - **Intent & Topic Extraction:** We only persist categorical metadata (`intent`, `topic`, `resolved`, `latency_ms`), preserving full analytical utility while completely protecting user privacy.

---

### Problem 2: Denormalized Flat Table & Redundancy Anomalies (Violating 1NF, 2NF, 3NF)
* **The Flaw:** A single table mixes three distinct lifecycle concepts:
  1. The conversation session (`session_id`).
  2. Individual interaction turns (`request_id`, `intent`, `topic`, `latency_ms`).
  3. User feedback ratings and comments (`rating`, `comment`).
* **The Risk:**
  - **Duplication & Storage Waste:** If a student asks 10 questions in a session, their session metadata and student attributes are duplicated 10 times.
  - **Sparse / NULL Columns:** The majority of interactions do not receive feedback (~65-70%), leaving `feedback_rating` and `feedback_comment` NULL for most rows.
  - **Update Anomalies:** If a session property or feedback item needs modification, multiple rows must be synchronized, creating inconsistency if a write fails midway.
* **Our Solution:**
  - **Normalized 3-Table Relational Schema:**
    - `chat_session` (1) — represents the conversation boundary.
    - `interaction` (N) — represents each question-and-answer exchange with a foreign key to `chat_session.id`.
    - `feedback` (N) — isolated table referencing `interaction.request_id`.
  - Storage is compact, zero redundancy exists across session turns, and feedback rows only exist when feedback is actually submitted.

---

### Problem 3: Lack of Referential Integrity and Domain Validation Constraints
* **The Flaw:**
  - No Foreign Keys: Nothing guarantees that `feedback_rating` corresponds to an actual answered question. Anyone or any script could insert arbitrary rows or fabricate feedback for non-existent interactions.
  - No Domain Validation: `feedback_rating` is an unrestricted integer, allowing erroneous or malicious ratings like `100`, `-99`, or `0.5`. `resolved` is stored as arbitrary text (`"yes"`, `"true"`, `"1"`).
* **Our Solution:**
  - **Strict Foreign Keys:** `feedback.request_id` enforces a foreign key constraint referencing `interaction.request_id`. At the API and repository level, feedback submission is rejected with HTTP 404 if the interaction does not exist.
  - **Check Constraints & Enums:** SQLite constraint `CHECK (rating IN (-1, 0, 1))` ensures database-level validation so invalid ratings are physically blocked by the engine even if application validation were bypassed.
  - **Strong Typing via SQLModel:** Schema fields are strictly typed (`bool` for resolved/degraded, `float` for latency_ms, `datetime` UTC timestamps).

---

## 3. Comparison Summary Table

| Criterion | `bad_schema.sql` | Our Normalized 3-Table Schema |
| :--- | :--- | :--- |
| **Privacy / PII** | Stores name, phone, raw questions | Zero PII; salted SHA-256 session hash |
| **Normal Form** | Flat, denormalized, redundant | 3NF normalized (`chat_session`, `interaction`, `feedback`) |
| **Feedback Integrity** | Orphan feedback possible | Foreign key ensures feedback requires existing interaction |
| **Rating Validation** | Unconstrained integer | Database `CHECK (rating IN (-1, 0, 1))` |
| **Extensibility** | Hard to add new channels or rating metrics | Clean relations allow adding tables (e.g. `faq`, `channels`) without breaking schema |
