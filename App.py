# App.py
import streamlit as st
import json
import random
import time
from pathlib import Path
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Learning Hub", page_icon="📘", layout="centered")

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
SCORES_FILE = BASE_DIR / "scores.json"
ADMIN_PASSWORD = "admin123"  # change this to something you prefer

# -------------------------
# HELPERS: file IO
# -------------------------
def read_json(path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except json.JSONDecodeError:
        return []
    return []

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Ensure files exist
if not QUESTIONS_FILE.exists():
    write_json(QUESTIONS_FILE, [])
if not SCORES_FILE.exists():
    write_json(SCORES_FILE, [])

# -------------------------
# LOAD DATA
# -------------------------
all_questions = read_json(QUESTIONS_FILE)  # list of dicts
all_scores = read_json(SCORES_FILE)        # list of dicts

# -------------------------
# SESSION STATE INIT
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "questions" not in st.session_state:
    st.session_state.questions = []

if "index" not in st.session_state:
    st.session_state.index = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "username" not in st.session_state:
    st.session_state.username = ""

if "subject" not in st.session_state:
    st.session_state.subject = "All"

if "level" not in st.session_state:
    st.session_state.level = "All"

if "time_limit" not in st.session_state:
    st.session_state.time_limit = 30  # default seconds per question

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "timed_out" not in st.session_state:
    st.session_state.timed_out = False

if "admin" not in st.session_state:
    st.session_state.admin = False

if "editing" not in st.session_state:
    st.session_state.editing = None  # index of question in questions.json being edited

# -------------------------
# UI: Sidebar - global controls
# -------------------------
st.sidebar.title("Settings & Controls")
st.sidebar.write("Configure session")

# Username
st.session_state.username = st.sidebar.text_input("Your name (optional)", value=st.session_state.username)

# Subject and Level selectors (populate from questions)
available_subjects = sorted({q.get("subject","General") for q in all_questions})
available_levels = sorted({q.get("level","General") for q in all_questions})

subject_options = ["All"] + available_subjects
level_options = ["All"] + available_levels

st.session_state.subject = st.sidebar.selectbox("Subject", subject_options, index=subject_options.index(st.session_state.subject) if st.session_state.subject in subject_options else 0)
st.session_state.level = st.sidebar.selectbox("Level", level_options, index=level_options.index(st.session_state.level) if st.session_state.level in level_options else 0)

# Time limit per question
st.session_state.time_limit = st.sidebar.number_input("Time limit (seconds) per question", min_value=5, max_value=600, value=st.session_state.time_limit, step=5)

# Buttons
if st.sidebar.button("Start Quiz"):
    # filter & load questions based on subject & level
    filtered = [q for q in all_questions if (st.session_state.subject == "All" or q.get("subject","General")==st.session_state.subject) and (st.session_state.level == "All" or q.get("level","General")==st.session_state.level)]
    if not filtered:
        st.sidebar.error("No questions found for the selected subject/level.")
    else:
        random.shuffle(filtered)
        st.session_state.questions = filtered
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.start_time = time.time()
        st.session_state.timed_out = False
        st.session_state.page = "quiz"
        st.experimental_rerun()

if st.sidebar.button("Go to Admin"):
    st.session_state.page = "admin"
    st.experimental_rerun()

if st.sidebar.button("Home"):
    st.session_state.page = "home"
    st.experimental_rerun()

# -------------------------
# Helper for saving score
# -------------------------
def save_score(username, score, total, subject, level):
    entry = {
        "username": username or "Anonymous",
        "score": score,
        "total": total,
        "subject": subject,
        "level": level,
        "timestamp": datetime.now().isoformat()
    }
    scores = read_json(SCORES_FILE)
    scores.append(entry)
    write_json(SCORES_FILE, scores)

# -------------------------
# PAGES
# -------------------------
def page_home():
    st.title("📘 BECE / SHS / JHS Learning Hub")
    st.write("Use the sidebar to select subject/level and start the quiz. You can also upload or manage questions in Admin.")
    st.markdown("**How to use**:\n\n1. Pick subject and level (or leave as All).\n2. Set time per question.\n3. Click **Start Quiz**.\n4. Answer each question and click Submit.\n\nYou can add questions via Admin or upload a JSON file of questions.")

    st.header("Sample Questions Preview")
    if not all_questions:
        st.info("No questions found. Use Admin to add questions or upload a questions.json file.")
    else:
        preview = all_questions[:6]
        for i, q in enumerate(preview, start=1):
            subj = q.get("subject","General")
            lvl = q.get("level","General")
            st.write(f"**{i}. [{subj} - {lvl}]** {q.get('question','')}")
            opts = q.get("options",[])
            st.write(" - " + " | ".join(opts))
    # Leaderboard
    st.header("Leaderboard (Top scores)")
    scores = read_json(SCORES_FILE)
    if scores:
        sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)
        top = sorted_scores[:10]
        for i, s in enumerate(top, start=1):
            st.write(f"{i}. {s['username']} — {s['score']}/{s['total']} — {s['subject']} {s['level']} — {s['timestamp']}")
    else:
        st.info("No scores yet.")

def page_quiz():
    if not st.session_state.questions:
        st.error("No active quiz. Start from the sidebar.")
        return

    total = len(st.session_state.questions)
    idx = st.session_state.index
    if idx >= total:
        # quiz finished
        st.success("🎉 Quiz complete!")
        st.write(f"Name: **{st.session_state.username or 'Anonymous'}**")
        st.write(f"Score: **{st.session_state.score} / {total}**")
        save_score(st.session_state.username, st.session_state.score, total, st.session_state.subject, st.session_state.level)
        st.download_button("Download your score (JSON)", json.dumps(read_json(SCORES_FILE), indent=2), file_name="scores.json")
        if st.button("Restart quiz"):
            st.session_state.index = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.session_state.questions = random.sample(st.session_state.questions, k=len(st.session_state.questions))
            st.session_state.page = "quiz"
            st.experimental_rerun()
        if st.button("Back to Home"):
            st.session_state.page = "home"
            st.experimental_rerun()
        return

    q = st.session_state.questions[idx]
    st.header(f"Question {idx+1} / {total}")
    st.subheader(q.get("question","No question text"))
    if q.get("image"):
        st.image(q.get("image"))

    # start timer for this question if not set
    if st.session_state.start_time is None or st.session_state.get("q_index") != idx:
        st.session_state.start_time = time.time()
        st.session_state.q_index = idx
        st.session_state.timed_out = False

    elapsed = time.time() - st.session_state.start_time
    remaining = int(st.session_state.time_limit - elapsed)
    if remaining <= 0:
        st.session_state.timed_out = True
        remaining = 0

    # show timer
    timer_col1, timer_col2 = st.columns([2,6])
    with timer_col1:
        st.write("⏱ Time left:")
        st.metric("", f"{remaining} s")
    with timer_col2:
        st.progress(max(0, (st.session_state.time_limit - remaining) / st.session_state.time_limit))

    # options
    options = q.get("options", [])
    if not options:
        st.error("This question has no options.")
        return

    # radio for answer
    selected = st.radio("Choose your answer:", options, key=f"answer_{idx}")

    # Submit logic
    if st.button("Submit"):
        if st.session_state.timed_out:
            st.warning("Time is up for this question! Answer not accepted.")
            # mark as incorrect and move on
            st.session_state.index += 1
            st.experimental_rerun()
        else:
            correct = q.get("answer")
            explanation = q.get("explanation", "")
            if selected == correct:
                st.success("Correct ✔")
                st.session_state.score += 1
            else:
                st.error(f"Wrong ✖. Correct answer is: **{correct}**")
            if explanation:
                st.info(f"Explanation: {explanation}")
            # move to next question
            st.session_state.index += 1
            # reset timer for next question
            st.session_state.start_time = time.time()
            st.experimental_rerun()

    # allow skip (counts as wrong)
    if st.button("Skip"):
        st.session_state.index += 1
        st.session_state.start_time = time.time()
        st.experimental_rerun()

    st.write("---")
    st.write(f"Subject: **{q.get('subject','General')}**  •  Level: **{q.get('level','General')}**")

def page_admin():
    st.title("🔧 Admin Panel")
    # login
    if not st.session_state.admin:
        pw = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.success("Admin mode enabled.")
                st.experimental_rerun()
            else:
                st.error("Wrong password.")
        st.stop()

    # admin actions
    st.success("Admin access granted.")
    st.write("You can add, edit, delete, import, or export questions here.")

    # Upload questions (JSON)
    st.subheader("Import questions (upload JSON)")
    uploaded = st.file_uploader("Upload a questions.json file (must be a JSON array of questions)", type=["json"])
    if uploaded is not None:
        try:
            uploaded_data = json.load(uploaded)
            if isinstance(uploaded_data, list):
                # option: merge or replace
                if st.button("Replace existing questions with uploaded file"):
                    write_json(QUESTIONS_FILE, uploaded_data)
                    st.success("Questions replaced. Reloading data.")
                    st.experimental_rerun()
                if st.button("Merge uploaded questions into existing file"):
                    existing = read_json(QUESTIONS_FILE)
                    existing.extend(uploaded_data)
                    write_json(QUESTIONS_FILE, existing)
                    st.success("Questions merged.")
                    st.experimental_rerun()
            else:
                st.error("Uploaded file must be a JSON array.")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    st.subheader("Add a new question")
    with st.form("add_q_form"):
        q_text = st.text_area("Question text")
        opts_raw = st.text_input("Comma-separated options (order matters)", help="Example: 12, 24, 36, 48")
        answer = st.text_input("Correct answer (must match one option exactly)")
        explanation = st.text_area("Explanation (optional)")
        subject = st.text_input("Subject (e.g. Math, English)", value="General")
        level = st.text_input("Level (e.g. JHS1, SHS2)", value="General")
        submitted = st.form_submit_button("Add Question")
        if submitted:
            options = [o.strip() for o in opts_raw.split(",") if o.strip()]
            if not q_text or not options or answer.strip() not in options:
                st.error("Please provide question text, options and ensure the correct answer matches one option exactly.")
            else:
                existing = read_json(QUESTIONS_FILE)
                new_q = {
                    "question": q_text,
                    "options": options,
                    "answer": answer.strip(),
                    "explanation": explanation,
                    "subject": subject or "General",
                    "level": level or "General"
                }
                existing.append(new_q)
                write_json(QUESTIONS_FILE, existing)
                st.success("Question added.")
                st.experimental_rerun()

    st.subheader("Existing questions (edit / delete)")
    questions = read_json(QUESTIONS_FILE)
    for i, q in enumerate(questions):
        with st.expander(f"{i+1}. {q.get('question')[:80]}..."):
            st.write("Options:", q.get("options"))
            st.write("Answer:", q.get("answer"))
            st.write("Subject:", q.get("subject","General"), "Level:", q.get("level","General"))
            col1, col2 = st.columns(2)
            if col1.button(f"Edit##{i}"):
                st.session_state.editing = i
                st.experimental_rerun()
            if col2.button(f"Delete##{i}"):
                if st.confirm(f"Delete question {i+1}?"):
                    questions.pop(i)
                    write_json(QUESTIONS_FILE, questions)
                    st.success("Deleted.")
                    st.experimental_rerun()

    # edit mode
    if st.session_state.editing is not None:
        i = st.session_state.editing
        if i < 0 or i >= len(questions):
            st.error("Invalid index.")
            st.session_state.editing = None
        else:
            q = questions[i]
            st.subheader(f"Editing question {i+1}")
            with st.form(f"edit_form_{i}"):
                q_text = st.text_area("Question text", value=q.get("question",""))
                opts_raw = st.text_input("Comma-separated options", value=", ".join(q.get("options",[])))
                answer = st.text_input("Correct answer", value=q.get("answer",""))
                explanation = st.text_area("Explanation", value=q.get("explanation",""))
                subject = st.text_input("Subject", value=q.get("subject","General"))
                level = st.text_input("Level", value=q.get("level","General"))
                saved = st.form_submit_button("Save changes")
                if saved:
                    options = [o.strip() for o in opts_raw.split(",") if o.strip()]
                    if not q_text or not options or answer.strip() not in options:
                        st.error("Please ensure question, options and answer are valid.")
                    else:
                        questions[i] = {
                            "question": q_text,
                            "options": options,
                            "answer": answer.strip(),
                            "explanation": explanation,
                            "subject": subject or "General",
                            "level": level or "General"
                        }
                        write_json(QUESTIONS_FILE, questions)
                        st.success("Saved changes.")
                        st.session_state.editing = None
                        st.experimental_rerun()
            if st.button("Cancel edit"):
                st.session_state.editing = None
                st.experimental_rerun()

    # Export data
    st.subheader("Export")
    st.download_button("Download questions.json", json.dumps(read_json(QUESTIONS_FILE), indent=2, ensure_ascii=False), file_name="questions.json")
    st.download_button("Download scores.json", json.dumps(read_json(SCORES_FILE), indent=2, ensure_ascii=False), file_name="scores.json")

    if st.button("Logout Admin"):
        st.session_state.admin = False
        st.experimental_rerun()

# -------------------------
# Router
# -------------------------
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "quiz":
    page_quiz()
elif st.session_state.page == "admin":
    page_admin()
else:
    page_home()
