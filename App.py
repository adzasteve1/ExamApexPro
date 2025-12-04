import streamlit as st
import json
from typing import Any

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data
def load_questions(path="questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_subjective_answer(ans: Any) -> str:
    """Return a readable string for answer which may be str/list/dict."""
    if isinstance(ans, str):
        return ans
    if isinstance(ans, list):
        return "\n".join(str(x) for x in ans)
    if isinstance(ans, dict):
        lines = []
        for k, v in ans.items():
            lines.append(f"{k}:")
            if isinstance(v, dict):
                for kk, vv in v.items():
                    lines.append(f"  - {kk}: {vv}")
            elif isinstance(v, list):
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"  - {v}")
        return "\n".join(lines)
    return str(ans)

def get_subjects_levels(questions):
    subjects = sorted({q.get("subject", "Unknown") for q in questions})
    levels = sorted({q.get("level", "Unknown") for q in questions})
    return subjects, levels

# -----------------------------
# Load data & init session
# -----------------------------
questions = load_questions()

if "q_index" not in st.session_state:
    st.session_state.q_index = 0

# permanent saved answers (only saved when user navigates or submits)
# keys: int(question index in filtered list) -> string answer
if "answers" not in st.session_state:
    st.session_state.answers = {}

# temporary widget values for the currently-displayed question
if "temp_answers" not in st.session_state:
    st.session_state.temp_answers = {}

if "filtered" not in st.session_state:
    st.session_state.filtered = []  # filtered questions for selected subject+level

# UI: title
st.set_page_config(page_title="Smart Quiz App", layout="centered")
st.title("📘 Smart Quiz App — One Question at a Time")

# -----------------------------
# Sidebar: select subject & level
# -----------------------------
subjects, levels = get_subjects_levels(questions)

sel_subject = st.selectbox("Subject", ["-- Select --"] + subjects)
sel_level = st.selectbox("Level", ["-- Select --"] + levels)

# When selection changes, filter and reset index/answers/temp
if sel_subject != "-- Select --" and sel_level != "-- Select --":
    # If different from current filtered selection, reset
    current_first = st.session_state.filtered[0] if st.session_state.filtered else None
    if (not st.session_state.filtered) or current_first.get("subject") != sel_subject or current_first.get("level") != sel_level:
        st.session_state.filtered = [q for q in questions if q.get("subject") == sel_subject and q.get("level") == sel_level]
        st.session_state.q_index = 0
        st.session_state.answers = {}
        st.session_state.temp_answers = {}

# If nothing filtered, show message and stop rendering quiz
if not st.session_state.filtered:
    st.info("Choose a Subject and Level to load questions.")
    st.stop()

filtered = st.session_state.filtered
total = len(filtered)

# -----------------------------
# Save current widget value (called before navigation or on submit)
# -----------------------------
def save_current_temp():
    """Save current temp widget into answers dict (only if user actually chose an option or typed)."""
    q_idx = st.session_state.q_index
    q = filtered[q_idx]

    key_temp = f"temp_{q_idx}"
    # If user hasn't interacted, temp may not exist. Use .get
    temp_val = st.session_state.temp_answers.get(key_temp, None)

    # For objective questions, the placeholder value is "-- Select --" (we don't save that)
    if "options" in q and q.get("options"):
        if temp_val and temp_val != "-- Select --":
            st.session_state.answers[q_idx] = temp_val
        else:
            # If placeholder or None, ensure we don't save an empty answer
            if q_idx in st.session_state.answers:
                # don't erase previously saved answer on a navigation unless user deliberately changed to placeholder
                pass
    else:
        # subjective: save whatever (even empty string counts as attempted if non-empty)
        if temp_val is not None:
            # store string (strip trailing/leading whitespace)
            st.session_state.answers[q_idx] = str(temp_val).strip()

# -----------------------------
# Navigation callbacks
# -----------------------------
def go_next():
    save_current_temp()
    if st.session_state.q_index < total - 1:
        st.session_state.q_index += 1

def go_prev():
    save_current_temp()
    if st.session_state.q_index > 0:
        st.session_state.q_index -= 1

# -----------------------------
# Render current question
# -----------------------------
q_index = st.session_state.q_index
q = filtered[q_index]

st.progress((q_index + 1) / total)
st.markdown(f"### Question {q_index + 1} of {total}")
st.write(q.get("question", ""))

# Determine widget key and current temp value
temp_key = f"temp_{q_index}"
# initialize temp value from saved answers if exists and temp not set yet
if temp_key not in st.session_state.temp_answers:
    # fill temp from saved answers if present
    if q_index in st.session_state.answers:
        st.session_state.temp_answers[temp_key] = st.session_state.answers[q_index]
    else:
        # default placeholder for objective or empty string for subjective
        if q.get("options"):
            st.session_state.temp_answers[temp_key] = "-- Select --"
        else:
            st.session_state.temp_answers[temp_key] = st.session_state.answers.get(q_index, "")

# Render input but bind to temp_answers (we only permanently save on nav/submit)
if q.get("options"):
    # insert placeholder at front
    options_with_placeholder = ["-- Select --"] + list(q["options"])
    # compute index for the radio display
    current_temp = st.session_state.temp_answers.get(temp_key, "-- Select --")
    try:
        selected_idx = options_with_placeholder.index(current_temp)
    except ValueError:
        selected_idx = 0
    # show radio; using key ensures Streamlit stores widget state under that key
    val = st.radio("Choose an option:", options_with_placeholder, index=selected_idx, key=temp_key)
    # keep temp in session_state.temp_answers updated automatically (st actually writes to key)
    st.session_state.temp_answers[temp_key] = val

else:
    # subjective
    val = st.text_area("Type your answer here:", value=st.session_state.temp_answers[temp_key], key=temp_key, height=140)
    st.session_state.temp_answers[temp_key] = val

# Explanation toggle (optional)
if q.get("explanation"):
    if st.checkbox("Show question explanation (optional)", key=f"exp_{q_index}"):
        st.info(q.get("explanation"))

# Navigation buttons (use callbacks so clicks persist across reruns)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.button("⬅️ Previous", on_click=go_prev, disabled=(q_index == 0))
with col2:
    st.button("Next ➡️", on_click=go_next, disabled=(q_index == total - 1))
with col3:
    # Save current temp then compute results
    def submit_quiz():
        # save current temp
        save_current_temp()
        # Build results and show in a new streamlit element by setting a flag in session_state
        st.session_state.show_results = True

    st.button("✅ Submit Quiz", on_click=submit_quiz)

st.markdown("---")
# -----------------------------
# Show results if requested
# -----------------------------
if st.session_state.get("show_results", False):
    # Ensure current temp saved before computing
    save_current_temp()

    # Build attempted indexes (only those with a non-empty saved answer)
    attempted = []
    for idx, _ in enumerate(filtered):
        if idx in st.session_state.answers:
            ans = st.session_state.answers[idx]
            if str(ans).strip() != "":
                attempted.append(idx)

    # Compute score and results list
    score = 0
    results = []
    for idx in attempted:
        ques = filtered[idx]
        user_ans = st.session_state.answers.get(idx, "")
        correct = ques.get("answer", None)
        explanation = ques.get("explanation", "")

        if ques.get("options"):  # objective
            is_correct = (user_ans == correct)
            if is_correct:
                score += 1
            results.append({
                "index": idx,
                "question": ques.get("question"),
                "type": "objective",
                "your_answer": user_ans,
                "correct_answer": correct,
                "explanation": explanation,
                "is_correct": is_correct
            })
        else:  # subjective
            results.append({
                "index": idx,
                "question": ques.get("question"),
                "type": "subjective",
                "your_answer": user_ans,
                "correct_answer": format_subjective_answer(correct) if correct is not None else "No model answer",
                "explanation": explanation
            })

    st.header("📊 Quiz Results (attempted questions only)")
    st.subheader(f"Score (objective): {score} / {sum(1 for r in results if r['type']=='objective')}")
    st.write(f"Total attempted questions: {len(results)}")

    for i, r in enumerate(results, start=1):
        st.markdown(f"### Q{i}. {r['question']}")
        if r["type"] == "objective":
            status = "✅ Correct" if r["is_correct"] else "❌ Incorrect"
            st.markdown(f"- **Your answer:** {r['your_answer']} — {status}")
            st.markdown(f"- **Correct answer:** {r['correct_answer']}")
            if r.get("explanation"):
                st.info(f"Explanation: {r['explanation']}")
        else:
            st.markdown(f"- **Your answer:** {r['your_answer']}")
            st.markdown(f"- **Model answer:**\n{r['correct_answer']}")
            if r.get("explanation"):
                st.info(f"Explanation: {r['explanation']}")
        st.markdown("---")

    # Buttons after results: restart or change subject/level
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🔄 Restart same quiz"):
            st.session_state.q_index = 0
            st.session_state.answers = {}
            st.session_state.temp_answers = {}
            st.session_state.show_results = False
            st.experimental_rerun()
    with rc2:
        if st.button("🔙 Change Subject/Level"):
            st.session_state.filtered = []
            st.session_state.q_index = 0
            st.session_state.answers = {}
            st.session_state.temp_answers = {}
            st.session_state.show_results = False
            st.experimental_rerun()


