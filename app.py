
from __future__ import annotations

import html

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_FILE = Path(os.environ.get("SCHOOL_DATA_FILE", Path(__file__).with_name("school_data.json")))
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PALETTE = dict(bg="#0B1020", side="#111827", card="#172033", card2="#1E293B", violet="#8B5CF6",
               cyan="#06B6D4", ok="#34D399", warn="#FBBF24", err="#FB7185", text="#F8FAFC",
               muted="#94A3B8")
PAGES = ["Dashboard", "Students", "Teachers", "Grade Management", "Reports & Analytics", "About Project"]
ICONS = dict(zip(PAGES, ["▦", "🎓", "👩‍🏫", "✎", "📈", "ⓘ"]))
NEW_SUBJECT = "+ Enter a new subject…"
BANDS = ["A (90-100)", "B (80-89)", "C (70-79)", "D (60-69)", "F (below 60)"]

CSS = Template("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; }
.stApp { background: $bg; }
.stApp, .stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3,
[data-baseweb="select"] *, [data-baseweb="tab"] { color: $text; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1250px; }
[data-testid="stSidebar"] { background: $side; border-right: 1px solid #243049; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: 8px 12px; border-radius: 10px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: $card2; }
h2, h3 { font-weight: 700; letter-spacing: -0.01em; }
.brand { display:flex; gap:12px; align-items:center; padding: 6px 4px 18px; }
.brand .logo { width:42px; height:42px; border-radius:12px; display:flex; align-items:center;
  justify-content:center; font-size:22px; background: linear-gradient(135deg,$violet,$cyan); }
.brand b { font-size:1.05rem; display:block; } .brand small { color:$muted; }
.page-head { display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap;
  gap:8px; margin-bottom:1.2rem; }
.page-head h1 { font-size:2rem; font-weight:800; margin:0; letter-spacing:-0.02em; color:$text; }
.page-head p { color:$muted; margin:4px 0 0; } .page-head .date { color:$muted; font-size:.85rem;
  background:$card; border:1px solid #243049; padding:6px 12px; border-radius:999px; }
.kpi { background:$card; border:1px solid #243049; border-radius:16px; padding:18px 20px;
  box-shadow:0 4px 14px rgba(0,0,0,.25); height:100%; }
.kpi .top { display:flex; justify-content:space-between; color:$muted; font-size:.85rem; font-weight:500; }
.kpi .icon { width:34px; height:34px; border-radius:10px; display:flex; align-items:center;
  justify-content:center; background:rgba(139,92,246,.18); color:$violet; }
.kpi .val { font-size:2.3rem; font-weight:800; margin-top:6px; letter-spacing:-0.02em; }
.kpi .sub { color:$muted; font-size:.8rem; }
.panel-title { font-weight:700; font-size:1.05rem; margin:.4rem 0 .6rem; }
.notice { border-radius:12px; padding:12px 16px; margin:8px 0; border:1px solid; font-size:.92rem; }
.notice.ok { background:rgba(52,211,153,.12); border-color:$ok; color:$ok; }
.notice.warn { background:rgba(251,191,36,.12); border-color:$warn; color:$warn; }
.notice.err { background:rgba(251,113,133,.12); border-color:$err; color:$err; }
.notice.info { background:rgba(6,182,212,.12); border-color:$cyan; color:$cyan; }
.empty { text-align:center; background:$card; border:1px dashed #334155; border-radius:16px;
  padding:34px 20px; margin:8px 0 12px; } .empty .big { font-size:2rem; }
.empty b { display:block; margin:6px 0 4px; font-size:1.05rem; } .empty span { color:$muted; }
.tbl-wrap { overflow-x:auto; background:$card; border:1px solid #243049; border-radius:14px; margin-bottom:8px; }
table.tbl { width:100%; border-collapse:collapse; font-size:.9rem; }
table.tbl th { text-align:left; color:$muted; font-weight:600; padding:12px 14px; background:$card2;
  white-space:nowrap; } table.tbl td { padding:11px 14px; border-top:1px solid #243049; color:$text; }
table.tbl tr:hover td { background:rgba(139,92,246,.07); }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, textarea
  { background:$card2 !important; border-color:#334155 !important; border-radius:10px !important; }
input, textarea { color:$text !important; -webkit-text-fill-color:$text !important; }
[data-testid="stForm"] { background:$card; border:1px solid #243049; border-radius:16px; padding:20px; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [role="listbox"] { background:$card2 !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button { border-radius:10px; font-weight:600;
  border:1px solid $violet; background:transparent; color:$text; }
[data-testid="stFormSubmitButton"] > button { background:linear-gradient(135deg,$violet,#6D5BF0); }
.stButton > button:hover { background:rgba(139,92,246,.2); border-color:$cyan; color:$text; }
@media (max-width: 640px) { .page-head h1 { font-size:1.5rem; } .kpi .val { font-size:1.8rem; } }
</style>""").substitute(**PALETTE)



def to_pos_int(value: Any) -> int | None:
    """Return value as a positive integer, or None."""
    if isinstance(value, bool):
        return None
    try:
        number = float(str(value).strip())
        return int(number) if number > 0 and number == int(number) else None
    except (ValueError, OverflowError):
        return None


def clean_student(rec: Any) -> dict | None:
    if not isinstance(rec, dict):
        return None
    roll, age, name = to_pos_int(rec.get("roll_no")), to_pos_int(rec.get("age")), str(rec.get("name", "")).strip()
    if not (roll and age and name):
        return None
    grades = {}
    raw = rec.get("grades")
    for subject, mark in (raw.items() if isinstance(raw, dict) else []):
        try:
            if 0 <= float(mark) <= 100:
                grades[str(subject)] = float(mark)
        except (TypeError, ValueError):
            continue
    return {**rec, "name": name, "age": age, "email": str(rec.get("email", "")).strip(),
            "roll_no": roll, "grades": grades}


def clean_teacher(rec: Any) -> dict | None:
    if not isinstance(rec, dict):
        return None
    emp, age, name = to_pos_int(rec.get("emp_id")), to_pos_int(rec.get("age")), str(rec.get("name", "")).strip()
    subject = " ".join(str(rec.get("subject", "")).split())
    if not (emp and age and name and subject):
        return None
    return {**rec, "name": name, "age": age, "email": str(rec.get("email", "")).strip(),
            "emp_id": emp, "subject": subject}


def backup_file() -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        shutil.copy2(DATA_FILE, DATA_FILE.with_name(f"school_data.backup-{stamp}.json"))
    except OSError:
        pass


def load_data() -> tuple[dict, list[str]]:
    """Load school_data.json safely. Returns (data, notices)."""
    data: dict = {"students": [], "teachers": []}
    if not DATA_FILE.exists():
        return data, []
    try:
        text = DATA_FILE.read_text(encoding="utf-8").strip()
        parsed = json.loads(text) if text else {}
        if not isinstance(parsed, dict):
            raise ValueError("root must be an object")
    except (OSError, ValueError):
        backup_file()
        return data, ["The data file could not be read. A backup copy was kept and the app started empty."]
    notes, dropped = [], 0
    for key, cleaner, id_key in (("students", clean_student, "roll_no"), ("teachers", clean_teacher, "emp_id")):
        raw = parsed.get(key, [])
        seen: set = set()
        for rec in raw if isinstance(raw, list) else []:
            item = cleaner(rec)
            if item is None or item[id_key] in seen:
                dropped += 1
                continue
            seen.add(item[id_key])
            data[key].append(item)
    if dropped:
        backup_file()
        notes.append(f"{dropped} malformed or duplicate record(s) were ignored. The original file was backed up.")
    return data, notes


def save_data(data: dict) -> bool:
    tmp = DATA_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        tmp.replace(DATA_FILE)
        return True
    except OSError:
        return False


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def validate_person(name: str, age: Any, email: str) -> list[str]:
    errors = []
    if not name.strip():
        errors.append("Full name is required.")
    if to_pos_int(age) is None or not 3 <= to_pos_int(age) <= 100:
        errors.append("Age must be a whole number between 3 and 100.")
    if not EMAIL_RE.match(email.strip()):
        errors.append("Enter a valid email address such as name@example.com.")
    return errors


def register_student(data: dict, name: str, age: Any, email: str, roll_text: str) -> tuple[bool, str]:
    errors = validate_person(name, age, email)
    roll = to_pos_int(roll_text)
    if roll is None:
        errors.append("Roll number must be a positive whole number.")
    elif any(s["roll_no"] == roll for s in data["students"]):
        errors.append(f"Roll number {roll} is already registered.")
    if errors:
        return False, " ".join(errors)
    data["students"].append({"name": name.strip(), "age": int(age), "email": email.strip(),
                             "roll_no": roll, "grades": {}, "created_at": now_iso()})
    if not save_data(data):
        data["students"].pop()
        return False, "Could not write school_data.json. Check file permissions."
    return True, f"{name.strip()} registered with roll number {roll}."


def register_teacher(data: dict, name: str, age: Any, email: str, emp_text: str, subject: str) -> tuple[bool, str]:
    errors = validate_person(name, age, email)
    emp = to_pos_int(emp_text)
    if emp is None:
        errors.append("Employee ID must be a positive whole number.")
    elif any(t["emp_id"] == emp for t in data["teachers"]):
        errors.append(f"Employee ID {emp} is already registered.")
    if not subject.strip():
        errors.append("Subject taught is required.")
    if age is not None and to_pos_int(age) is not None and to_pos_int(age) < 18:
        errors.append("Teachers must be at least 18.")
    if errors:
        return False, " ".join(errors)
    data["teachers"].append({"name": name.strip(), "age": int(age), "email": email.strip(), "emp_id": emp,
                             "subject": canonical_subject(data, subject), "created_at": now_iso()})
    if not save_data(data):
        data["teachers"].pop()
        return False, "Could not write school_data.json. Check file permissions."
    return True, f"{name.strip()} registered to teach {data['teachers'][-1]['subject']}."


def all_subjects(data: dict) -> list[str]:
    names = {sub for s in data["students"] for sub in s["grades"]} | {t["subject"] for t in data["teachers"]}
    return sorted(names, key=str.lower)


def canonical_subject(data: dict, subject: str) -> str:
    """Reuse existing spelling so 'python' and 'Python' stay one subject."""
    cleaned = " ".join(subject.split())
    return next((s for s in all_subjects(data) if s.lower() == cleaned.lower()), cleaned)


def find_student(data: dict, roll: int) -> dict | None:
    return next((s for s in data["students"] if s["roll_no"] == roll), None)


def add_grade(data: dict, roll: int, subject: str, marks: float) -> tuple[bool, str]:
    student = find_student(data, roll)
    if student is None:
        return False, "That student could not be found."
    if not subject.strip():
        return False, "Subject is required."
    if not 0 <= marks <= 100:
        return False, "Marks must be between 0 and 100."
    subject = canonical_subject(data, subject)
    old = student["grades"].get(subject)
    student["grades"][subject] = float(marks)
    if not save_data(data):
        if old is None:
            del student["grades"][subject]
        else:
            student["grades"][subject] = old
        return False, "Could not write school_data.json. Check file permissions."
    verb = "added" if old is None else f"updated (was {old:g})"
    return True, f"{subject} mark {verb} for {student['name']}: {marks:g}."


def average(grades: dict) -> float | None:
    return sum(grades.values()) / len(grades) if grades else None


def band(mark: float) -> str:
    return BANDS[0 if mark >= 90 else 1 if mark >= 80 else 2 if mark >= 70 else 3 if mark >= 60 else 4]


def students_df(data: dict) -> pd.DataFrame:
    rows = [{"Name": s["name"], "Roll No": s["roll_no"], "Age": s["age"], "Email": s["email"],
             "Subjects": len(s["grades"]), "Average": average(s["grades"])} for s in data["students"]]
    return pd.DataFrame(rows, columns=["Name", "Roll No", "Age", "Email", "Subjects", "Average"])


def teachers_df(data: dict) -> pd.DataFrame:
    rows = [{"Name": t["name"], "Employee ID": t["emp_id"], "Age": t["age"], "Email": t["email"],
             "Subject": t["subject"]} for t in data["teachers"]]
    return pd.DataFrame(rows, columns=["Name", "Employee ID", "Age", "Email", "Subject"])


def grades_df(data: dict) -> pd.DataFrame:
    rows = [{"Student": s["name"], "Roll No": s["roll_no"], "Subject": sub, "Marks": m}
            for s in data["students"] for sub, m in s["grades"].items()]
    return pd.DataFrame(rows, columns=["Student", "Roll No", "Subject", "Marks"])


def subject_averages(gdf: pd.DataFrame) -> pd.DataFrame:
    if gdf.empty:
        return pd.DataFrame(columns=["Subject", "Average", "Students"])
    out = gdf.groupby("Subject")["Marks"].agg(Average="mean", Students="count").reset_index()
    return out.round({"Average": 1}).sort_values("Average", ascending=False)


# ------------------------------------------------------------------ UI pieces
def goto(page: str, **state: Any) -> None:
    st.session_state.page = page
    st.session_state.update(state)


def notice(kind: str, message: str) -> None:
    st.markdown(f'<div class="notice {kind}">{html.escape(message)}</div>', unsafe_allow_html=True)


def flash(kind: str, message: str) -> None:
    st.session_state.flash = (kind, message)


def page_header(title: str, subtitle: str) -> None:
    today = datetime.now().strftime("%A, %d %B %Y")
    st.markdown(f'<div class="page-head"><div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>'
                f'<div class="date">{today}</div></div>', unsafe_allow_html=True)
    for note in st.session_state.get("load_notes", []):
        notice("warn", note)
    if "flash" in st.session_state:
        notice(*st.session_state.pop("flash"))


def kpi_card(icon: str, label: str, value: str, sub: str = "") -> None:
    st.markdown(f'<div class="kpi"><div class="top"><span>{label}</span><span class="icon">{icon}</span></div>'
                f'<div class="val">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def empty_state(icon: str, title: str, text: str, button: str | None = None, page: str = "",
                **state: Any) -> None:
    st.markdown(f'<div class="empty"><div class="big">{icon}</div><b>{html.escape(title)}</b>'
                f'<span>{html.escape(text)}</span></div>', unsafe_allow_html=True)
    if button:
        st.button(button, on_click=goto, args=(page,), kwargs=state, key=f"empty_{title}_{button}")


def fmt_cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return f"{value:.1f}" if isinstance(value, float) else html.escape(str(value))


def html_table(df: pd.DataFrame) -> None:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{fmt_cell(v)}</td>" for v in row) + "</tr>"
                   for row in df.head(500).itertuples(index=False))
    st.markdown(f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def style_fig(fig, height: int = 320):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=PALETTE["text"]),
                      legend=dict(font=dict(color=PALETTE["muted"])))
    fig.update_xaxes(gridcolor="#243049", zerolinecolor="#243049")
    fig.update_yaxes(gridcolor="#243049", zerolinecolor="#243049")
    return fig


def show_chart(fig, height: int = 320) -> None:
    st.plotly_chart(style_fig(fig, height), width="stretch", config={"displayModeBar": False})


def title(text: str) -> None:
    st.markdown(f'<div class="panel-title">{text}</div>', unsafe_allow_html=True)


def subject_chart(sa: pd.DataFrame) -> None:
    fig = px.bar(sa, x="Subject", y="Average", text="Average", hover_data=["Students"],
                 color="Average", color_continuous_scale=[PALETTE["violet"], PALETTE["cyan"]])
    fig.update_traces(texttemplate="%{text:.1f}")
    fig.update_layout(yaxis_range=[0, 100], coloraxis_showscale=False)
    show_chart(fig)


def distribution_chart(gdf: pd.DataFrame) -> None:
    counts = gdf["Marks"].map(band).value_counts()
    dist = pd.DataFrame({"Band": BANDS, "Marks recorded": [int(counts.get(b, 0)) for b in BANDS]})
    colors = [PALETTE["ok"], PALETTE["cyan"], PALETTE["violet"], PALETTE["warn"], PALETTE["err"]]
    show_chart(px.bar(dist, x="Band", y="Marks recorded", color="Band", color_discrete_sequence=colors,
                      text="Marks recorded").update_layout(showlegend=False))


def comparison_chart(sdf: pd.DataFrame) -> None:
    graded = sdf.dropna(subset=["Average"]).sort_values("Average")
    fig = px.bar(graded, x="Average", y="Name", orientation="h", text="Average", hover_data=["Roll No"],
                 color_discrete_sequence=[PALETTE["violet"]])
    fig.update_traces(texttemplate="%{text:.1f}")
    fig.update_layout(xaxis_range=[0, 100], yaxis_title=None)
    show_chart(fig, max(260, 36 * len(graded) + 60))


# ----------------------------------------------------------------- pages
def page_dashboard(data: dict) -> None:
    page_header("Dashboard", "A live snapshot of your school, calculated from saved records.")
    sdf, gdf = students_df(data), grades_df(data)
    cols = st.columns(4)
    with cols[0]:
        kpi_card("🎓", "Total Students", str(len(data["students"])), "registered")
    with cols[1]:
        kpi_card("👩‍🏫", "Total Teachers", str(len(data["teachers"])), "registered")
    with cols[2]:
        kpi_card("✎", "Subjects with Grades", str(gdf["Subject"].nunique()), f"{len(gdf)} marks recorded")
    with cols[3]:
        kpi_card("★", "Overall Average", f"{gdf['Marks'].mean():.1f}" if not gdf.empty else "—",
                 "across all marks" if not gdf.empty else "no marks yet")
    st.write("")
    q = st.columns(3)
    q[0].button("＋ Register student", on_click=goto, args=("Students",), kwargs={"student_view": "Register"},
                width="stretch")
    q[1].button("＋ Register teacher", on_click=goto, args=("Teachers",), kwargs={"teacher_view": "Register"},
                width="stretch")
    q[2].button("✎ Add grades", on_click=goto, args=("Grade Management",), width="stretch")
    st.write("")
    left, right = st.columns(2)
    with left:
        title("Enrollment overview (current snapshot)")
        if not data["students"] and not data["teachers"]:
            empty_state("🏫", "Nothing registered yet", "Register your first student or teacher to begin.")
        else:
            graded = int((sdf["Subjects"] > 0).sum())
            snap = pd.DataFrame({"Group": ["Students with grades", "Students without grades", "Teachers"],
                                 "Count": [graded, len(sdf) - graded, len(data["teachers"])]})
            fig = px.pie(snap, names="Group", values="Count", hole=0.6, color="Group",
                         color_discrete_map={"Students with grades": PALETTE["violet"],
                                             "Students without grades": PALETTE["warn"],
                                             "Teachers": PALETTE["cyan"]})
            show_chart(fig)
    with right:
        title("Subject-wise average marks")
        if gdf.empty:
            empty_state("✎", "No grades recorded", "Add marks on the Grade Management page.",
                        "Add grades", "Grade Management")
        else:
            subject_chart(subject_averages(gdf))
    left, right = st.columns(2)
    with left:
        title("Grade distribution")
        if gdf.empty:
            empty_state("📊", "No distribution yet", "Charts appear once marks are recorded.")
        else:
            distribution_chart(gdf)
    with right:
        title("Student performance comparison")
        if sdf["Average"].notna().any():
            comparison_chart(sdf)
        else:
            empty_state("🎓", "No averages yet", "A student needs at least one mark to be compared.")
    title("Recent activity")
    recent = sorted([("Student", s) for s in data["students"] if s.get("created_at")] +
                    [("Teacher", t) for t in data["teachers"] if t.get("created_at")],
                    key=lambda x: x[1]["created_at"], reverse=True)[:6]
    if recent:
        html_table(pd.DataFrame([{"Type": k, "Name": r["name"], "Registered": r["created_at"].replace("T", " ")}
                                 for k, r in recent]))
    else:
        notice("info", "Registration times are saved for new records. Older records have no timestamp, "
                       "so none are shown.")


def student_register(data: dict) -> None:
    n = st.session_state.setdefault("n_student", 0)
    with st.form(f"student_form_{n}"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *", key=f"s_name_{n}")
        roll = c2.text_input("Roll number *", key=f"s_roll_{n}", help="A positive whole number")
        age = c1.number_input("Age *", 0, 120, 18, key=f"s_age_{n}")
        email = c2.text_input("Email *", key=f"s_email_{n}")
        submitted = st.form_submit_button("Register student")
    if submitted:
        ok, msg = register_student(data, name, age, email, roll)
        if ok:
            st.session_state.n_student = n + 1
            flash("ok", msg)
            st.rerun()
        notice("err", msg)


def student_directory(data: dict) -> None:
    if not data["students"]:
        return empty_state("🎓", "No students registered", "Use the Register view to add the first student.",
                           "Register a student", "Students", student_view="Register")
    sdf = students_df(data)
    c1, c2, c3 = st.columns([2, 1, 1])
    term = c1.text_input("Search by name or roll number", key="s_search")
    status = c2.selectbox("Filter", ["All students", "With grades", "Without grades"])
    sort = c3.selectbox("Sort by", ["Name", "Roll No", "Average (high to low)"])
    if term:
        t = term.strip().lower()
        sdf = sdf[sdf["Name"].str.lower().str.contains(t, regex=False) | (sdf["Roll No"].astype(str) == t)]
    if status != "All students":
        sdf = sdf[(sdf["Subjects"] > 0) == (status == "With grades")]
    if sort.startswith("Average"):
        sdf = sdf.sort_values("Average", ascending=False, na_position="last")
    else:
        sdf = sdf.sort_values(sort, key=lambda col: col.str.lower() if col.dtype == object else col)
    if sdf.empty:
        return empty_state("🔍", "No matching students", "Try a different search or clear the filter.")
    html_table(sdf)
    st.caption(f"Showing {len(sdf)} of {len(data['students'])} students")


def student_profile(data: dict) -> None:
    if not data["students"]:
        return empty_state("🎓", "No students registered", "Register a student first.",
                           "Register a student", "Students", student_view="Register")
    rolls = [s["roll_no"] for s in data["students"]]
    roll = st.selectbox("Select a student", rolls, index=None, placeholder="Choose a student…",
                        format_func=lambda r: f"{find_student(data, r)['name']} (roll {r})")
    student = find_student(data, roll) if roll is not None else None
    if student is None:
        return notice("info", "Select a student to open their profile.")
    avg = average(student["grades"])
    cols = st.columns(4)
    with cols[0]:
        kpi_card("#", "Roll number", str(student["roll_no"]), student["name"])
    with cols[1]:
        kpi_card("☺", "Age", str(student["age"]), html.escape(student["email"]))
    with cols[2]:
        kpi_card("✎", "Graded subjects", str(len(student["grades"])))
    with cols[3]:
        kpi_card("★", "Average", f"{avg:.1f}" if avg is not None else "—")
    st.write("")
    if not student["grades"]:
        return empty_state("✎", "No grades yet", f"{student['name']} has no recorded marks.",
                           "Add grades", "Grade Management")
    gdf = pd.DataFrame({"Subject": list(student["grades"]), "Marks": list(student["grades"].values())})
    left, right = st.columns([1, 1.4])
    with left:
        html_table(gdf)
    with right:
        fig = px.bar(gdf, x="Subject", y="Marks", text="Marks", color_discrete_sequence=[PALETTE["cyan"]])
        fig.update_traces(texttemplate="%{text:.1f}")
        fig.update_layout(yaxis_range=[0, 100])
        show_chart(fig, 280)


def page_students(data: dict) -> None:
    page_header("Students", "Register students, browse the directory and open profiles.")
    view = st.radio("View", ["Directory", "Register", "Profile"], key="student_view", horizontal=True,
                    label_visibility="collapsed")
    {"Directory": student_directory, "Register": student_register, "Profile": student_profile}[view](data)


def teacher_register(data: dict) -> None:
    n = st.session_state.setdefault("n_teacher", 0)
    with st.form(f"teacher_form_{n}"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *", key=f"t_name_{n}")
        emp = c2.text_input("Employee ID *", key=f"t_emp_{n}", help="A positive whole number")
        age = c1.number_input("Age *", 0, 120, 30, key=f"t_age_{n}")
        subject = c2.text_input("Subject taught *", key=f"t_sub_{n}")
        email = st.text_input("Email *", key=f"t_email_{n}")
        submitted = st.form_submit_button("Register teacher")
    if submitted:
        ok, msg = register_teacher(data, name, age, email, emp, subject)
        if ok:
            st.session_state.n_teacher = n + 1
            flash("ok", msg)
            st.rerun()
        notice("err", msg)


def teacher_directory(data: dict) -> None:
    if not data["teachers"]:
        return empty_state("👩‍🏫", "No teachers registered", "Use the Register view to add the first teacher.",
                           "Register a teacher", "Teachers", teacher_view="Register")
    tdf = teachers_df(data)
    c1, c2 = st.columns([2, 1])
    term = c1.text_input("Search by name or employee ID", key="t_search")
    subject = c2.selectbox("Subject", ["All subjects"] + sorted(tdf["Subject"].unique(), key=str.lower))
    if term:
        t = term.strip().lower()
        tdf = tdf[tdf["Name"].str.lower().str.contains(t, regex=False) | (tdf["Employee ID"].astype(str) == t)]
    if subject != "All subjects":
        tdf = tdf[tdf["Subject"] == subject]
    if tdf.empty:
        return empty_state("🔍", "No matching teachers", "Try a different search or subject.")
    html_table(tdf)
    ids = list(tdf["Employee ID"])
    emp = st.selectbox("View teacher details", ids, index=None, placeholder="Choose a teacher…",
                       format_func=lambda e: tdf.loc[tdf["Employee ID"] == e, "Name"].iloc[0])
    if emp is not None:
        t = next(t for t in data["teachers"] if t["emp_id"] == emp)
        cols = st.columns(3)
        with cols[0]:
            kpi_card("#", "Employee ID", str(t["emp_id"]), html.escape(t["name"]))
        with cols[1]:
            kpi_card("✎", "Subject", html.escape(t["subject"]), html.escape(t["email"]))
        with cols[2]:
            kpi_card("☺", "Age", str(t["age"]))


def page_teachers(data: dict) -> None:
    page_header("Teachers", "Register teachers and see who teaches each subject.")
    view = st.radio("View", ["Directory", "Register"], key="teacher_view", horizontal=True,
                    label_visibility="collapsed")
    {"Directory": teacher_directory, "Register": teacher_register}[view](data)


def page_grades(data: dict) -> None:
    page_header("Grade Management", "Add or update a student's marks (0–100).")
    if not data["students"]:
        return empty_state("🎓", "No students to grade", "Register a student before adding marks.",
                           "Register a student", "Students", student_view="Register")
    rolls = [s["roll_no"] for s in data["students"]]
    roll = st.selectbox("Student", rolls, format_func=lambda r: f"{find_student(data, r)['name']} (roll {r})")
    student = find_student(data, roll)
    choice = st.selectbox("Subject", all_subjects(data) + [NEW_SUBJECT])
    subject = st.text_input("New subject name") if choice == NEW_SUBJECT else choice
    existing = next((k for k in student["grades"] if k.lower() == " ".join(subject.split()).lower()), None)
    if subject.strip():
        notice("warn", f"This will update {existing} (current mark: {student['grades'][existing]:g})."
               if existing else f"This will add a new subject for {student['name']}: {subject.strip()}.")
    with st.form("grade_form"):
        marks = st.number_input("Marks (0–100)", 0.0, 100.0,
                                float(student["grades"][existing]) if existing else 0.0, step=0.5)
        submitted = st.form_submit_button("Update mark" if existing else "Save mark")
    if submitted:
        ok, msg = add_grade(data, roll, subject, marks)
        if ok:
            flash("ok", msg)
            st.rerun()
        notice("err", msg)
    title(f"Grades for {html.escape(student['name'])}")
    if not student["grades"]:
        return empty_state("✎", "No marks recorded", "Save the first mark above.")
    avg = average(student["grades"])
    left, right = st.columns([1, 1.4])
    with left:
        kpi_card("★", "Average", f"{avg:.1f}", f"{len(student['grades'])} subject(s)")
        st.write("")
        html_table(pd.DataFrame({"Subject": list(student["grades"]), "Marks": list(student["grades"].values())}))
    with right:
        gdf = pd.DataFrame({"Subject": list(student["grades"]), "Marks": list(student["grades"].values())})
        fig = px.bar(gdf, x="Subject", y="Marks", text="Marks", color_discrete_sequence=[PALETTE["violet"]])
        fig.update_traces(texttemplate="%{text:.1f}")
        fig.update_layout(yaxis_range=[0, 100])
        show_chart(fig, 300)


def page_reports(data: dict) -> None:
    page_header("Reports & Analytics", "Enrollment, performance and gaps in the recorded data.")
    sdf, gdf = students_df(data), grades_df(data)
    cols = st.columns(4)
    with cols[0]:
        kpi_card("🎓", "Students", str(len(sdf)))
    with cols[1]:
        kpi_card("👩‍🏫", "Teachers", str(len(data["teachers"])))
    with cols[2]:
        kpi_card("✎", "Marks recorded", str(len(gdf)))
    with cols[3]:
        kpi_card("★", "Overall average", f"{gdf['Marks'].mean():.1f}" if not gdf.empty else "—")
    st.write("")
    left, right = st.columns(2)
    with left:
        title("Subject-wise performance")
        if gdf.empty:
            empty_state("✎", "No grades recorded", "Add marks to see subject performance.",
                        "Add grades", "Grade Management")
        else:
            subject_chart(subject_averages(gdf))
    with right:
        title("Grade distribution")
        if gdf.empty:
            empty_state("📊", "No distribution yet", "Marks are grouped into bands once recorded.")
        else:
            distribution_chart(gdf)
    title("Highest-performing students")
    graded = sdf.dropna(subset=["Average"]).sort_values("Average", ascending=False)
    if len(graded) < 2:
        notice("info", "At least two students with recorded marks are needed for a meaningful ranking.")
    else:
        top = graded.head(5).reset_index(drop=True)
        top.insert(0, "Rank", top.index + 1)
        html_table(top[["Rank", "Name", "Roll No", "Subjects", "Average"]])
        st.caption("Averages are based on each student's own recorded subjects, which may differ in number.")
    title("Students without recorded grades")
    ungraded = sdf[sdf["Subjects"] == 0]
    if ungraded.empty:
        notice("ok", "Every registered student has at least one mark." if len(sdf) else "No students registered yet.")
    else:
        html_table(ungraded[["Name", "Roll No", "Email"]])
    title("Performance table")
    if gdf.empty:
        return empty_state("📋", "No performance data", "Marks will be listed here.")
    term = st.text_input("Search by student or subject", key="r_search").strip().lower()
    view = gdf if not term else gdf[gdf["Student"].str.lower().str.contains(term, regex=False)
                                    | gdf["Subject"].str.lower().str.contains(term, regex=False)]
    if view.empty:
        empty_state("🔍", "No results", "Try a different search term.")
    else:
        html_table(view)
    d1, d2 = st.columns(2)
    d1.download_button("Download students CSV", sdf.to_csv(index=False).encode("utf-8"), "students.csv",
                       "text/csv", disabled=sdf.empty, width="stretch")
    d2.download_button("Download grades CSV", gdf.to_csv(index=False).encode("utf-8"), "grades.csv",
                       "text/csv", disabled=gdf.empty, width="stretch")


def page_about(data: dict) -> None:
    page_header("About Project", "A Streamlit version of a command-line school management project.")
    st.markdown(
        "**Built with** Python, Streamlit, pandas and Plotly.\n\n"
        "**Data** lives in `school_data.json` next to `app.py` with the original schema: `students` "
        "(`name`, `age`, `email`, `roll_no`, `grades`) and `teachers` (`name`, `age`, `email`, `emp_id`, "
        "`subject`). New records also get a `created_at` time.\n\n"
        "**Limitations:** JSON storage suits a local demo. There is no file locking, so simultaneous users "
        "can overwrite each other, hosted platforms may reset the file, and there is no login.")


def main() -> None:
    st.set_page_config(page_title="School Management System", page_icon="🎓", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    if "data" not in st.session_state:
        st.session_state.data, st.session_state.load_notes = load_data()
    st.session_state.setdefault("page", "Dashboard")
    with st.sidebar:
        st.markdown('<div class="brand"><div class="logo">🎓</div><div><b>School Management</b>'
                    '<small>Administration</small></div></div>', unsafe_allow_html=True)
        st.radio("Navigate", PAGES, key="page", label_visibility="collapsed",
                 format_func=lambda p: f"{ICONS[p]}  {p}")
        st.caption("Data saved to school_data.json")
    renderers = {"Dashboard": page_dashboard, "Students": page_students, "Teachers": page_teachers,
                 "Grade Management": page_grades, "Reports & Analytics": page_reports,
                 "About Project": page_about}
    renderers[st.session_state.page](st.session_state.data)


main()