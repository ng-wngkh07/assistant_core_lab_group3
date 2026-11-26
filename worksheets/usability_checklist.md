# Lab 7 — Usability checklist (tick before your user test)

- [x] The first screen says what the assistant can do, with example questions
- [x] Empty or too-long input shows a friendly message (not a crash)
- [x] While waiting, the user sees "Thinking…"
- [x] Every answer from documents shows its sources
- [x] "I don't know" answers tell the user who can help (escalation)
- [x] If the backend is down, the page says so clearly
- [x] Each answer has 👍 / 👎, and clicking gives a "thanks" message
- [x] The page says it is an AI assistant
- [x] Text is readable (size, contrast); buttons have clear labels
- [x] Works on a phone-width window

## 2-minute Hallway Test (Part E)

- **Classmate from another group (first name) & date**: Hưng — 26/11/2026
- **Browser check notes (`http://localhost:8501`, tested at `1280x800` and `375x812`)**:
  - Validation verified: `"   "` shows `Please type a question.`; >2000 chars shows `Your question is too long (max 2000 characters).`
  - Document answers show `Sources: H26#5.3 — 5.3 Thesis registration` / `Sources: S26#3 — 3 Student card replacement`; unanswerable queries (`"What is the cafeteria menu today?"`) escalate with info note `I could not find this in the official documents. A staff member can help: Training Office, room I.101.`
  - Backend-down state verified with API stopped: shows red error banner `The assistant backend is not reachable. Start it with: uvicorn assistant_api.main:create_app --factory` (see [evidence_backend_down.png](../docs/lab7/evidence_backend_down.png)).
  - Feedback buttons verified: `👍` shows toast `Thanks for your feedback!`; `👎` shows toast `Thanks — we will look at this answer.` (see [evidence_escalation_feedback.png](../docs/lab7/evidence_escalation_feedback.png)).
- **1 surprising thing noticed**:
  - On a phone-width window (`375x812`), Streamlit collapses the sidebar behind the top-left `>` button, which originally hid **both** all `"Try an example"` buttons and the `"This is an AI assistant..."` notice from mobile users (see [before_mobile.png](../docs/lab7/before_mobile.png)). In addition, `👍` / `👎` buttons stay visible for one render pass immediately after clicking (only disappearing on the next Streamlit rerun) and stack vertically on mobile, and `"What is the wifi password for building B?"` matched `S26#2` (IT password reset) instead of escalating.
