# Lab 7 homework — 10-minute usability test

Tester (not in your team, first name only): Hưng  Date: 26/11/2026
Task you gave them: "Find out if you can register your thesis with 118 credits, and where to replace a lost student card."

Rule: do not help or explain. Watch and write down what happens.

| # | What the tester did or said | What they expected | Why the system/UI caused it | Fix idea |
|---|---|---|---|---|
| 1 | Entered both parts of the task into one chat message: `"Can I register my thesis with 118 credits, and where can I replace a lost student card?"` | Expected an answer covering both thesis eligibility (118 vs. 120 credits) and where to replace a lost student card. | Neither the welcome text nor the chat input placeholder warned users to ask one question at a time; the RAG backend (`StubLLM` + top-1 hit) returned only `S26#3` (student card replacement) and silently dropped the thesis part (see [before_combined_query.png](../docs/lab7/before_combined_query.png)). | **Implemented (H1 Fix):** Update `WELCOME`, add an always-visible caption under the title, and update the `st.chat_input` placeholder to guide users to ask **one question at a time**. |
| 2 | Looked only at the main chat pane (and tested on phone width `375x812`) without noticing the collapsed `>` sidebar toggle at the top-left. | Expected clickable example questions and the AI assistant notice to be visible directly on the first screen. | Both `"Try an example"` buttons and `"This is an AI assistant..."` lived exclusively in `st.sidebar`, which Streamlit hides by default on mobile/narrow windows (see [before_mobile.png](../docs/lab7/before_mobile.png)). | **Implemented (H1 Fix):** Surface the AI notice + one-question-at-a-time caption right under the main title and render clickable `Suggested questions:` buttons below `WELCOME` when `len(messages) == 1`. |
| 3 | Asked `"I lost my student card"` and clicked `👍` / `👎` below the answer; noticed the buttons stayed visible right after clicking and the answer omitted fee/turnaround details. | Expected `👍` / `👎` to disappear immediately once rated (and stay side-by-side on mobile), and expected complete replacement fee/duration info without room-number mismatch (`S26#3` says `I.102`, while `offices.csv` says `A.102`). | In `ui/app.py`, `st.session_state.rated.add(rid)` happens without `st.rerun()` (so buttons only vanish on the next turn) and `st.columns([1, 1, 6])` stacks on narrow viewports; `StubLLM` extracts only the first sentence of `S26#3`. | Follow-up improvements: store toast in `session_state` and call `st.rerun()` after rating so buttons hide immediately, and align `offices.csv` (`A.102`) with `S26#3` (`I.102`). |

The one change we made (commit link): https://github.com/ng-wngkh07/assistant_core_lab_group3/commit/c81b0260b1b8173da89ae6d120c064ebe1ed974f (`ui/logic.py`, `ui/app.py`)
Before / after screenshot:
- Desktop initial screen: [before_desktop.png](../docs/lab7/before_desktop.png) -> [after_desktop.png](../docs/lab7/after_desktop.png)
- Phone-width (`375x812`) initial screen: [before_mobile.png](../docs/lab7/before_mobile.png) -> [after_mobile.png](../docs/lab7/after_mobile.png)
- H1 task query (combined query dropping thesis vs. guided two-step flow): [before_combined_query.png](../docs/lab7/before_combined_query.png) -> [after_h1_flow.png](../docs/lab7/after_h1_flow.png)
