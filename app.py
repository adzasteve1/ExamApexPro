import streamlit as st
import json
import random
from typing import Any
import datetime

# =========================
# PWA CONFIG INJECTION
# =========================
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#0d6efd">

<!-- iOS support -->
<link rel="apple-touch-icon" href="/static/icons/icon-152.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Exam Master App">

<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js')
    .then(reg => console.log("Service worker registered:", reg))
    .catch(err => console.log("Service worker error:", err));
}
</script>
""", unsafe_allow_html=True)

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Smart Quiz App", layout="centered")

# -----------------------------
# Persistent Share / Add to Home Screen Banner
# -----------------------------
if "banner_shown" not in st.session_state:
    st.session_state.banner_shown = False

if not st.session_state.banner_shown:
    with st.expander("📌 Quick Access & Share Tips", expanded=True):
        st.markdown("""
**Add to Home Screen (Shortcut):**  
- **Android:** Tap browser menu → **Add to Home screen**  
- **iOS (Safari):** Tap **Share → Add to Home Screen**  

**Share App with friends:**  
- Tap **Copy App Link** button below to copy the app URL and send it.
""")
        if st.button("📋 Copy App Link"):
            st.write("Copy this link manually: `https://examapexpro.streamlit.app`")
    st.session_state.banner_shown = True

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data
def load_questions(path="questions.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_subjective_answer(ans: Any) -> str:
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
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "temp_answers" not in st.session_state:
    st.session_state.temp_answers = {}
if "filtered" not in st.session_state:
    st.session_state.filtered = []
if "mode" not in st.session_state:
    st.session_state.mode = "menu"  # menu, practice, exam_of_day, mock_exam

# -----------------------------
# Utility Functions
# -----------------------------
def reset_quiz(filtered_questions):
    st.session_state.filtered = filtered_questions
    st.session_state.q_index = 0
    st.session_state.answers = {}
    st.session_state.temp_answers = {}
    st.session_state.show_results = False

def pick_mock_exam(q_list, count):
    if len(q_list) < count:
        count = len(q_list)
    return random.sample(q_list, count)

def get_daily_exam():
    today = datetime.date.today().strftime("%Y-%m-%d")
    random.seed(today)
    return pick_mock_exam(questions, 20)

def save_current_temp():
    q_idx = st.session_state.q_index
    q = st.session_state.filtered[q_idx]
    key_temp = f"temp_{q_idx}"
    temp_val = st.session_state.temp_answers.get(key_temp, None)

    if "options" in q and q.get("options"):
        if temp_val and temp_val != "-- Select --":
            st.session_state.answers[q_idx] = temp_val
    else:
        if temp_val is not None:
            st.session_state.answers[q_idx] = str(temp_val).strip()

def go_next():
    save_current_temp()
    if st.session_state.q_index < len(st.session_state.filtered) - 1:
        st.session_state.q_index += 1

def go_prev():
    save_current_temp()
    if st.session_state.q_index > 0:
        st.session_state.q_index -= 1

# -----------------------------
# UI: Mode Selection Menu
# -----------------------------
st.title("📘 Exam Master Prep")

if st.session_state.mode == "menu":
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📚 Practice Mode"):
            st.session_state.mode = "practice"
    with col2:
        if st.button("⏳ Exam of the Day"):
            filtered_questions = get_daily_exam()
            if not filtered_questions:
                st.error("🚫 No questions available for today's exam.")
            else:
                reset_quiz(filtered_questions)
                st.session_state.mode = "exam"
    with col3:
        if st.button("📝 Mock Exam Generator"):
            st.session_state.mode = "mock"
    st.stop()

# -----------------------------
# Practice Mode
# -----------------------------
if st.session_state.mode == "practice":
    st.header("📚 Practice Mode")
    subjects, levels = get_subjects_levels(questions)
    sel_subject = st.selectbox("Select Subject", ["-- Select --"] + subjects)
    sel_level = st.selectbox("Select Level", ["-- Select --"] + levels)

    if st.button("Load Questions"):
        if sel_subject == "-- Select --" or sel_level == "-- Select --":
            st.error("🚫 Please select both Subject and Level.")
        else:
            filtered_questions = [q for q in questions if q.get("subject") == sel_subject and q.get("level") == sel_level]
            if not filtered_questions:
                st.error("🚫 No questions found for this subject and level.")
            else:
                reset_quiz(filtered_questions)
                st.session_state.mode = "exam"

    if st.button("Back to Menu"):
        st.session_state.mode = "menu"
    st.stop()

# -----------------------------
# Mock Exam Generator
# -----------------------------
if st.session_state.mode == "mock":
    st.header("📝 Mock Exam Generator")
    subjects, levels = get_subjects_levels(questions)
    sel_subject = st.selectbox("Select Subject", ["-- Select --"] + subjects)
    sel_level = st.selectbox("Select Level", ["-- Select --"] + levels)
    count = st.slider("Number of Questions", 10, 60, 20)

    if st.button("Generate Mock Exam"):
        if sel_subject == "-- Select --" or sel_level == "-- Select --":
            st.error("🚫 Please select both Subject and Level.")
        else:
            base = [q for q in questions if q.get("subject") == sel_subject and q.get("level") == sel_level]
            if not base:
                st.error("🚫 No questions available for this selection.")
            else:
                filtered_questions = pick_mock_exam(base, count)
                reset_quiz(filtered_questions)
                st.session_state.mode = "exam"

    if st.button("Back to Menu"):
        st.session_state.mode = "menu"
    st.stop()

# -----------------------------
# Exam Display
# -----------------------------
filtered = st.session_state.filtered
if not filtered:
    st.info("No questions loaded. Go back to Menu and select a mode.")
    st.stop()

total = len(filtered)
q_index = st.session_state.q_index
q = filtered[q_index]

st.progress((q_index + 1) / total)
st.markdown(f"### Question {q_index + 1} of {total}")
st.write(q.get("question", ""))

temp_key = f"temp_{q_index}"
if temp_key not in st.session_state.temp_answers:
    if q_index in st.session_state.answers:
        st.session_state.temp_answers[temp_key] = st.session_state.answers[q_index]
    else:
        if q.get("options"):
            st.session_state.temp_answers[temp_key] = "-- Select --"
        else:
            st.session_state.temp_answers[temp_key] = st.session_state.answers.get(q_index, "")

# -----------------------------
# Objective / Subjective Inputs
# -----------------------------
if q.get("options"):
    options_with_placeholder = ["-- Select --"] + list(q["options"])
    current_temp = st.session_state.temp_answers.get(temp_key, "-- Select --")
    try:
        selected_idx = options_with_placeholder.index(current_temp)
    except ValueError:
        selected_idx = 0
    val = st.radio("Choose an option:", options_with_placeholder, index=selected_idx, key=temp_key)
    st.session_state.temp_answers[temp_key] = val
else:
    val = st.text_area("Type your answer here:", value=st.session_state.temp_answers[temp_key], key=temp_key)
    st.session_state.temp_answers[temp_key] = val

# Explanation toggle
if q.get("explanation"):
    if st.checkbox("Show question explanation (optional)", key=f"exp_{q_index}"):
        st.info(q.get("explanation"))

# -----------------------------
# Navigation Buttons
# -----------------------------
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.button("⬅️ Previous", on_click=go_prev, disabled=(q_index == 0))
with col2:
    st.button("Next ➡️", on_click=go_next, disabled=(q_index == total - 1))
with col3:
    def submit_quiz():
        save_current_temp()
        st.session_state.show_results = True
    st.button("✅ Submit Quiz", on_click=submit_quiz)

st.markdown("---")

# -----------------------------
# Show Results
# -----------------------------
if st.session_state.get("show_results", False):
    save_current_temp()
    attempted = [idx for idx, _ in enumerate(filtered) if idx in st.session_state.answers and str(st.session_state.answers[idx]).strip() != ""]
    score = 0
    results = []
    for idx in attempted:
        ques = filtered[idx]
        user_ans = st.session_state.answers.get(idx, "")
        correct = ques.get("answer", None)
        explanation = ques.get("explanation", "")
        if ques.get("options"):
            is_correct = (user_ans == correct)
            if is_correct:
                score += 1
            results.append({"index": idx, "question": ques.get("question"), "type": "objective",
                            "your_answer": user_ans, "correct_answer": correct, "explanation": explanation, "is_correct": is_correct})
        else:
            results.append({"index": idx, "question": ques.get("question"), "type": "subjective",
                            "your_answer": user_ans, "correct_answer": format_subjective_answer(correct) if correct else "No model answer",
                            "explanation": explanation})

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

    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🔄 Restart same quiz"):
            reset_quiz(st.session_state.filtered)
    with rc2:
        if st.button("🔙 Change Subject/Level"):
            st.session_state.filtered = []
            st.session_state.q_index = 0
            st.session_state.answers = {}
            st.session_state.temp_answers = {}
            st.session_state.show_results = False
            st.session_state.mode = "menu"
