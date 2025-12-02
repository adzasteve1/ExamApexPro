# app.py -- Modern Learning App (Option B with Subjective "Show Answer" button)
import streamlit as st
import json
import random
from pathlib import Path
from datetime import datetime

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Learning Hub — Modern", page_icon="📘", layout="centered")

BASE_DIR = Path(__file__).parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
SCORES_FILE = BASE_DIR / "scores.json"
ADMIN_PASSWORD = "admin123"  # change this if you want

# -------------------------
# Helpers: JSON IO & flatten
# -------------------------
def read_json(path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return []
    return []

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def flatten_questions(raw):
    out = []
    if not isinstance(raw, list):
        return out
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        if "questions" in entry and isinstance(entry["questions"], list):
            for q in entry["questions"]:
                if isinstance(q, dict) and q.get("question"):
                    out.append(normalize_question(q))
        if "theory" in entry and isinstance(entry["theory"], list):
            for q in entry["theory"]:
                if isinstance(q, dict) and q.get("question"):
                    out.append(normalize_question(q))
        if "question" in entry and ("options" in entry or "answer" in entry):
            out.append(normalize_question(entry))
    return out

def normalize_question(q):
    normalized = {}
    normalized["question"] = q.get("question", "").strip()
    opts = q.get("options")
    if isinstance(opts, list):
        normalized["options"] = [str(o) for o in opts]
    elif isinstance(opts, str):
        normalized["options"] = [o.strip() for o in opts.split(",") if o.strip()]
    else:
        normalized["options"] = []
    normalized["answer"] = q.get("answer", "")
    normalized["explanation"] = q.get("explanation", "")
    normalized["subject"] = q.get("subject", "General")
    normalized["level"] = q.get("level", "General")
    normalized["image"] = q.get("image") if q.get("image") else None
    return normalized

# Ensure files exist
if not QUESTIONS_FILE.exists():
    write_json(QUESTIONS_FILE, [])
if not SCORES_FILE.exists():
    write_json(SCORES_FILE, [])

raw_data = read_json(QUESTIONS_FILE)
ALL_QUESTIONS = flatten_questions(raw_data)
ALL_SCORES = read_json(SCORES_FILE)

# -------------------------
# Session State init
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "quiz"
for k, v in {
    "questions": [],
    "index": 0,
    "score": 0,
    "username": "",
    "subject": "All",
    "level": "All",
    "started": False,
    "show_feedback": False,
    "last_selected": None,
    "prev_subject": None,
    "prev_level": None,
    "admin": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------
# Sidebar (filters + nav)
# -------------------------
st.sidebar.title("Controls")
st.session_state.username = st.sidebar.text_input("Your name (optional)", value=st.session_state.username)

subjects = ["All"] + sorted({q.get("subject", "General") for q in ALL_QUESTIONS})
levels = ["All"] + sorted({q.get("level", "General") for q in ALL_QUESTIONS})

st.session_state.subject = st.sidebar.selectbox(
    "Subject", subjects,
    index=subjects.index(st.session_state.subject) if st.session_state.subject in subjects else 0
)
st.session_state.level = st.sidebar.selectbox(
    "Level", levels,
    index=levels.index(st.session_state.level) if st.session_state.level in levels else 0
)

if st.sidebar.button("Home"):
    st.session_state.page = "home"
if st.sidebar.button("Admin"):
    st.session_state.page = "admin"
if st.sidebar.button("Restart Quiz"):
    st.session_state.started = False
    st.session_state.questions = []
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.show_feedback = False
    st.session_state.last_selected = None
    st.session_state.page = "quiz"

# -------------------------
# Quiz loader
# -------------------------
def load_questions_for_session():
    filtered = [
        q for q in ALL_QUESTIONS
        if (st.session_state.subject == "All" or q.get("subject", "General") == st.session_state.subject)
        and (st.session_state.level == "All" or q.get("level", "General") == st.session_state.level)
    ]
    filtered = [q for q in filtered if q.get("question")]
    if not filtered:
        st.session_state.questions = []
        st.session_state.started = False
        return
    random.shuffle(filtered)
    st.session_state.questions = filtered
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.started = True
    st.session_state.show_feedback = False
    st.session_state.last_selected = None

if (st.session_state.prev_subject != st.session_state.subject) or (st.session_state.prev_level != st.session_state.level) or (not st.session_state.started):
    st.session_state.prev_subject = st.session_state.subject
    st.session_state.prev_level = st.session_state.level
    load_questions_for_session()

# -------------------------
# Helper: save score
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
# Pages
# -------------------------
def page_home():
    st.title("📘 Learning Hub — Home")
    st.write("This is the modern learning interface. The quiz starts automatically on open (one question at a time). Use the sidebar to change subject/level or restart.")
    st.write("")
    st.header("All questions (preview)")
    if not ALL_QUESTIONS:
        st.info("No questions found. Upload via Admin.")
    else:
        for i, q in enumerate(ALL_QUESTIONS, start=1):
            with st.expander(f"{i}. [{q.get('subject')} - {q.get('level')}] {q.get('question')[:120]}"):
                if q.get("options"):
                    st.write("Options:", " | ".join(q.get("options")))
                st.write("Answer:", q.get("answer") if q.get("answer") else "(subjective/theory)")
                if q.get("explanation"):
                    st.info("Explanation: " + str(q.get("explanation")))
    st.header("Leaderboard (Top 5)")
    scores = read_json(SCORES_FILE)
    if scores:
        top = sorted(scores, key=lambda s: s.get("score", 0), reverse=True)[:5]
        for i, s in enumerate(top, start=1):
            st.write(f"{i}. {s.get('username','Anonymous')} — {s.get('score')}/{s.get('total')} — {s.get('subject')} {s.get('level')}")
    else:
        st.info("No scores yet.")

def page_quiz():
    st.title("📘 Learning Hub — Quiz")
    if not st.session_state.questions:
        st.warning("No questions available for this subject/level. Use the sidebar to select a different filter or add questions in Admin.")
        return

    total = len(st.session_state.questions)
    idx = st.session_state.index
    q = st.session_state.questions[idx]

    st.markdown(f"**Question {idx+1} of {total}** — *{q.get('subject','General')} / {q.get('level','General')}*")
    st.write("")
    st.subheader(q.get("question"))

    if q.get("image"):
        st.image(q.get("image"))

    options = q.get("options") or []

    # -------------------------
    # MCQ Input
    # -------------------------
    if options:
        if not st.session_state.show_feedback:
            choice = st.radio("", options, key=f"choice_{idx}")
            st.session_state.last_selected = choice
            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("Submit", use_container_width=True):
                    st.session_state.show_feedback = True
                    correct = q.get("answer")
                    sel = st.session_state.last_selected
                    st.session_state._last_result = (str(sel).strip() == str(correct).strip())
            with c2:
                if st.button("Skip", use_container_width=True):
                    st.session_state.index = (st.session_state.index + 1) % len(st.session_state.questions)
                    st.session_state.show_feedback = False
                    st.session_state.last_selected = None
                    return
        else:
            res = st.session_state.get("_last_result", None)
            correct = q.get("answer")
            explanation = q.get("explanation")
            if res:
                st.success("✅ Correct")
                st.session_state.score += 1
            else:
                st.error(f"❌ Wrong — correct answer: **{correct}**")
            if explanation:
                st.info(f"💡 Explanation: {explanation}")
            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("Next", use_container_width=True):
                    st.session_state.index += 1
                    st.session_state.show_feedback = False
                    st.session_state.last_selected = None
                    return
            with c2:
                if st.button("Finish Quiz", use_container_width=True):
                    st.session_state.index = len(st.session_state.questions)
                    st.session_state.show_feedback = False
                    return

    # -------------------------
    # Subjective Input
    # -------------------------
    else:
        choice = st.text_input("", key=f"input_{idx}", placeholder="Type your answer here...")
        st.session_state.last_selected = choice
        if not st.session_state.show_feedback:
            if st.button("Show Answer", key=f"show_{idx}"):
                st.session_state.show_feedback = True
        else:
            correct = q.get("answer")
            explanation = q.get("explanation")
            st.info("Answer revealed (subjective):")
            if isinstance(correct, (dict, list)):
                st.json(correct)
            else:
                st.write(str(correct))
            if explanation:
                st.info(f"💡 Explanation: {explanation}")
            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("Next", use_container_width=True):
                    st.session_state.index += 1
                    st.session_state.show_feedback = False
                    st.session_state.last_selected = None
                    return
            with c2:
                if st.button("Finish Quiz", use_container_width=True):
                    st.session_state.index = len(st.session_state.questions)
                    st.session_state.show_feedback = False
                    return

    # -------------------------
    # End of quiz
    # -------------------------
    if st.session_state.index >= total:
        st.success("🎉 Quiz complete!")
        st.write(f"**Name:** {st.session_state.username or 'Anonymous'}")
        st.write(f"**Score:** {st.session_state.score} / {total}")
        save_score(st.session_state.username, st.session_state.score, total, st.session_state.subject, st.session_state.level)
        st.download_button("Download scores (JSON)", json.dumps(read_json(SCORES_FILE), indent=2), file_name="scores.json")
        if st.button("Restart", use_container_width=True):
            load_questions_for_session()
            return

def page_admin():
    st.title("🔧 Admin")
    if not st.session_state.admin:
        pw = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.success("Admin enabled")
            else:
                st.error("Wrong password")
        return

    st.success("Admin mode active")
    st.write("Upload a `questions.json` (list) or add questions below.")

    uploaded = st.file_uploader("Upload questions.json", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            if isinstance(data, list):
                if st.button("Replace questions with uploaded file"):
                    write_json(QUESTIONS_FILE, data)
                    st.success("Replaced questions file. Please restart the app (F5) or press Restart Quiz in sidebar.")
                if st.button("Merge uploaded questions into existing"):
                    existing = read_json(QUESTIONS_FILE)
                    existing.extend(data)
                    write_json(QUESTIONS_FILE, existing)
                    st.success("Merged uploaded questions.")
            else:
                st.error("Uploaded file must be a JSON list.")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    st.subheader("Add a new question (quick)")
    with st.form("add_q"):
        q_text = st.text_area("Question")
        opts = st.text_input("Comma-separated options (leave blank for subjective)")
        ans = st.text_input("Correct answer (for MCQ ensure it matches one option)")
        expl = st.text_area("Explanation (optional)")
        subj = st.text_input("Subject", value="General")
        lvl = st.text_input("Level", value="General")
        added = st.form_submit_button("Add question")
        if added:
            options = [o.strip() for o in opts.split(",")] if opts else []
            new_q = {
                "question": q_text,
                "options": options,
                "answer": ans,
                "explanation": expl,
                "subject": subj or "General",
                "level": lvl or "General"
            }
            existing = read_json(QUESTIONS_FILE)
            existing.append(new_q)
            write_json(QUESTIONS_FILE, existing)
            st.success("Saved. Press Restart Quiz in sidebar to load new questions.")

    st.subheader("Export")
    if st.button("Download questions.json"):
        st.download_button("questions.json", json.dumps(read_json(QUESTIONS_FILE), indent=2, ensure_ascii=False))

    if st.button("Logout Admin"):
        st.session_state.admin = False
        st.session_state.page = "home"

# -------------------------
# Router
# -------------------------
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "quiz":
    if st.session_state.index >= len(st.session_state.questions):
        page_quiz()
    else:
        page_quiz()
elif st.session_state.page == "admin":
    page_admin()
else:
    page_quiz()
