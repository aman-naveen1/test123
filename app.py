from datetime import date, datetime
from html import escape
import pandas as pd
import streamlit as st

from aase import robustness_report, simulate_disruption
from calendar_parser import parse_academic_calendar
from database import absence_count, init_db, load_data, recent_runs, record_absence, record_run, save_calendar, seed_from_data
from engine import gap_score, load_demo_data, repair_schedule
from ingestion import parse_timetable_file
from optimizer import optimize_timetable, optimize_whole_timetable

st.set_page_config(page_title="AASE | Timetable Management", page_icon="📅", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
:root { --navy:#0b2450; --blue:#164d9b; --ink:#172b4d; --muted:#66758b; --line:#e5ebf3; --canvas:#f6f8fc; }
html, body, [class*="css"] { color:var(--ink); font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp { background:var(--canvas) !important; color:var(--ink) !important; }
.block-container { padding:1.5rem 2rem 3rem; max-width:1560px; }
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background:#fff !important; border-right:1px solid var(--line); }
section[data-testid="stSidebar"] > div { padding-top:1rem; }
section[data-testid="stSidebar"] * { color:#526274; }
.brand { display:flex; align-items:center; gap:.75rem; padding:.35rem .45rem 1.35rem; }
.brand-mark { background:var(--navy); color:#fff; width:34px; height:34px; border-radius:10px; display:inline-flex; align-items:center; justify-content:center; font-size:1rem; }
.brand-title { color:var(--navy) !important; font-size:1rem; font-weight:800; letter-spacing:-.02em; }
.brand-subtitle { color:#8090a5 !important; font-size:.7rem; font-weight:650; text-transform:uppercase; letter-spacing:.08em; margin-top:.12rem; }
section[data-testid="stSidebar"] .stRadio label { border-radius:9px; padding:.34rem .45rem; font-size:.9rem; font-weight:650; }
section[data-testid="stSidebar"] .stRadio label:has(input:checked) { background:#edf3fc; color:var(--blue) !important; }
.sidebar-status { background:#f4f7fb; border:1px solid var(--line); border-radius:12px; padding:.75rem; margin-top:.8rem; font-size:.75rem; line-height:1.7; }
.eyebrow { color:var(--blue) !important; font-size:.72rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.4rem; }
.page-header { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin-bottom:1.25rem; }
.page-header h1 { margin:0; color:var(--navy) !important; font-size:2rem; line-height:1.15; letter-spacing:-.045em; }
.page-header p { color:var(--muted) !important; margin:.45rem 0 0; font-size:.94rem; }
.context-pill { background:#fff; border:1px solid var(--line); border-radius:10px; padding:.55rem .8rem; color:var(--muted); font-size:.78rem; font-weight:700; white-space:nowrap; }
.section-title { color:var(--navy) !important; font-size:1.14rem; font-weight:780; letter-spacing:-.02em; margin:1.75rem 0 .7rem; }
.metric-card { background:#fff; border:1px solid var(--line); color:var(--ink) !important; border-radius:14px; padding:1rem 1.1rem; min-height:104px; display:flex; flex-direction:column; justify-content:center; text-align:left; box-shadow:0 2px 8px rgba(22,45,80,.035); }
.metric-card .value,.metric-card .label { color:inherit !important; }
.metric-card .value { color:var(--navy) !important; font-size:1.8rem; font-weight:800; letter-spacing:-.05em; order:2; }
.metric-card .label { color:var(--muted) !important; font-size:.76rem; font-weight:760; letter-spacing:.03em; text-transform:uppercase; order:1; }
.timeline { border-left:2px solid #d7e3f3; margin:.35rem 0 0 .7rem; padding-left:1.35rem; }
.timetable-panel { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1.35rem 1.5rem 1.1rem; box-shadow:0 4px 14px rgba(22,45,80,.04); }
.timetable-panel-head { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; padding-bottom:1rem; border-bottom:1px solid var(--line); }
.timetable-panel-head h2 { margin:0; color:var(--navy) !important; font-size:1.28rem; letter-spacing:-.025em; }
.timetable-panel-head p { margin:.25rem 0 0; color:var(--muted) !important; font-size:.84rem; }
.schedule-badge { color:var(--blue) !important; background:#edf4ff; border-radius:99px; padding:.36rem .65rem; font-size:.73rem; font-weight:800; white-space:nowrap; }
.timeline-item { position:relative; margin:0 0 .85rem; }
.timeline-item:before { content:""; position:absolute; width:9px; height:9px; border-radius:50%; background:var(--blue); border:3px solid #eaf2ff; left:-1.72rem; top:.7rem; }
.timeline-time { color:var(--blue) !important; font-size:.78rem; font-weight:800; margin-bottom:.25rem; }
.class-card { background:#fff; border:1px solid var(--line); border-radius:11px; padding:.78rem 1rem; box-shadow:0 1px 4px rgba(22,45,80,.03); }
.class-course { font-weight:760; color:var(--navy) !important; }
.class-meta { color:var(--muted) !important; font-size:.82rem; margin-top:.16rem; }
div[data-testid="stDataFrame"], div[data-testid="stFileUploader"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }
div[data-testid="stFileUploader"] { padding:.25rem; }
button[kind="primary"] { background:var(--navy) !important; color:#fff !important; border-radius:8px !important; font-weight:700 !important; border:1px solid var(--navy) !important; }
button[kind="secondary"] { border-color:#cfd9e6 !important; border-radius:8px !important; }
div[data-baseweb="select"] > div, input { border-radius:8px !important; }
@media (max-width: 760px) { .block-container { padding:1rem; } .page-header { align-items:flex-start; flex-direction:column; } .page-header h1 { font-size:1.65rem; } }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('''<div class="brand"><span class="brand-mark">A</span><div><div class="brand-title">AASE</div><div class="brand-subtitle">Scheduling workspace</div></div></div>''', unsafe_allow_html=True)
    role = st.selectbox("View as", ["Student", "Faculty", "Administrator"], key="role_view")
    navigation = {
        "Student": ["My Timetable", "Calendar"],
        "Faculty": ["My Teaching", "Report absence"],
        "Administrator": ["Dashboard","Time Table","Teachers","Rooms","Academic Calendar","OCR Intake","Disruptions","Optimization","Reports"],
    }
    page = st.radio("Navigation", navigation[role], label_visibility="collapsed")
    st.divider()
    status_copy = {
        "Student": "<b>Student view</b><br>View your timetable<br>Check academic dates",
        "Faculty": "<b>Faculty view</b><br>Review teaching sessions<br>Report an absence",
        "Administrator": "<b>System status</b><br>● Local data connected<br>● Optimizer ready<br>● ERP / API ready",
    }
    st.markdown(f'<div class="sidebar-status">{status_copy[role]}</div>', unsafe_allow_html=True)

if "db_seeded" not in st.session_state:
    seed_from_data(load_demo_data(), source="demo", replace_classes=True)
    st.session_state["db_seeded"] = True

data = load_data()

page_descriptions = {
    "My Timetable": "Find your classes, rooms and teaching staff at a glance.",
    "Calendar": "Keep track of holidays and academic events.",
    "My Teaching": "Review today’s teaching plan and your assigned sessions.",
    "Report absence": "Let scheduling staff know when you cannot teach.",
}
st.markdown(f'''
<div class="page-header">
  <div><div class="eyebrow">{escape(role)} workspace</div><h1>{escape(page)}</h1><p>{escape(page_descriptions.get(page, "Plan, review and adapt your academic timetable from one focused workspace."))}</p></div>
  <div class="context-pill">{escape(datetime.now().strftime("%A, %d %B"))}</div>
</div>
''', unsafe_allow_html=True)

today_name = datetime.now().strftime("%A")
groups = sorted({x["group"] for x in data["classes"]}) or ["BSc-CS-3A"]
selected_group = st.selectbox("Student / Group", groups, index=0, key="selected_group")
today_classes = [x for x in data["classes"] if x["day"] == today_name and x["group"] == selected_group]
current_gap = gap_score(data["classes"], selected_group)

if page not in {"Dashboard", "My Timetable", "My Teaching", "Calendar", "Report absence"}:
    m1,m2,m3 = st.columns(3)
    for col,value,label in [(m1,current_gap,"Student Idle-Gap Score"),(m2,absence_count(),"Recorded Staff Absences"),(m3,len(data["rooms"]),"Managed Rooms")]:
        col.markdown(f'<div class="metric-card"><div class="value">{escape(str(value))}</div><div class="label">{escape(label)}</div></div>', unsafe_allow_html=True)

if page == "My Timetable":
    requested_day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].index(today_name) if today_name in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"} else 0)
    my_classes = [x for x in data["classes"] if x["day"] == requested_day and x["group"] == selected_group]
    st.markdown(f'''<div class="timetable-panel"><div class="timetable-panel-head"><div><h2>{escape(requested_day)} timetable</h2><p>Classes for {escape(selected_group)}.</p></div><div class="schedule-badge">{len(my_classes)} class(es)</div></div>''', unsafe_allow_html=True)
    if my_classes:
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        order={s:i for i,s in enumerate(["09:00-10:00","10:00-11:00","11:15-12:15","12:15-13:15","14:00-15:00","15:00-16:00"])}
        for row in sorted(my_classes,key=lambda x:order.get(x["slot"],99)):
            st.markdown(f'<div class="timeline-item"><div class="timeline-time">{escape(str(row["slot"]))}</div><div class="class-card"><div class="class-course">{escape(str(row["course"]))}</div><div class="class-meta">{escape(str(row["teacher"]))} · Room {escape(str(row["room"]))}</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info(f"No classes are scheduled for {selected_group} on {requested_day}.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Calendar":
    st.markdown('<div class="section-title">Upcoming academic dates</div>', unsafe_allow_html=True)
    if data["calendar_events"]:
        st.dataframe(pd.DataFrame(data["calendar_events"])[["date", "name", "type"]], use_container_width=True, hide_index=True)
    else:
        st.info("No academic calendar has been published yet. Check with your timetable administrator.")

elif page == "My Teaching":
    teacher_options = sorted({x["teacher"] for x in data["classes"]}) or ["No teachers found"]
    selected_teacher = st.selectbox("Faculty member", teacher_options, key="faculty_member")
    faculty_classes = [x for x in data["classes"] if x["teacher"] == selected_teacher and x["day"] == today_name]
    st.markdown(f'''<div class="timetable-panel"><div class="timetable-panel-head"><div><h2>Today’s teaching</h2><p>Sessions assigned to {escape(selected_teacher)}.</p></div><div class="schedule-badge">{len(faculty_classes)} session(s)</div></div>''', unsafe_allow_html=True)
    if faculty_classes:
        st.dataframe(pd.DataFrame(faculty_classes)[["slot", "course", "group", "room"]], use_container_width=True, hide_index=True)
    else:
        st.info(f"No teaching sessions are scheduled for {selected_teacher} today.")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Report absence":
    teacher_options = sorted({x["teacher"] for x in data["classes"]}) or ["No teachers found"]
    selected_teacher = st.selectbox("Faculty member", teacher_options, key="absence_faculty_member")
    absence_date = st.date_input("Date unavailable", value=date.today(), key="faculty_absence_date")
    reason = st.text_area("Reason (optional)", placeholder="Add a short note for the scheduling team.")
    if st.button("Submit absence report", type="primary"):
        record_absence(selected_teacher, absence_date.isoformat(), reason)
        st.success("Your absence report has been sent to the scheduling team.")

elif page == "Dashboard":
    st.markdown(f'''<div class="timetable-panel"><div class="timetable-panel-head"><div><h2>Today’s Timetable</h2><p>Your complete schedule for {escape(selected_group)}.</p></div><div class="schedule-badge">{escape(today_name)}</div></div>''', unsafe_allow_html=True)
    if today_classes:
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        order={s:i for i,s in enumerate(["09:00-10:00","10:00-11:00","11:15-12:15","12:15-13:15","14:00-15:00","15:00-16:00"])}
        for row in sorted(today_classes,key=lambda x:order.get(x["slot"],99)):
            st.markdown(f'<div class="timeline-item"><div class="timeline-time">{escape(str(row["slot"]))}</div><div class="class-card"><div class="class-course">{escape(str(row["course"]))}</div><div class="class-meta">{escape(str(row["teacher"]))} · Room {escape(str(row["room"]))} · {escape(str(row["group"]))}</div></div></div>',unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.info(f"No scheduled classes for {selected_group} today ({today_name}).")
    st.markdown('</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Managed timetable records</div>',unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(data["classes"]),use_container_width=True,hide_index=True)
    with c2:
        st.markdown('<div class="section-title">Recent AASE operations</div>',unsafe_allow_html=True)
        runs=recent_runs(6)
        if runs: st.dataframe(pd.DataFrame(runs)[["created_at","operation","status","summary"]],use_container_width=True,hide_index=True)
        else: st.info("No optimization runs yet.")

elif page == "Time Table":
    st.markdown('<div class="section-title">Timetable Intake</div>',unsafe_allow_html=True)
    st.caption("Upload PDF, CSV or Excel. CSV/XLSX/XLS are parsed directly; PDF text is extracted first and scanned PDFs can fall back to local Tesseract OCR.")
    files=st.file_uploader("Upload timetable files",type=["pdf","csv","xlsx","xls"],accept_multiple_files=True)
    use_ocr=st.checkbox("Enable Tesseract fallback for scanned PDFs",value=True)
    if files and st.button("Parse & import timetable",type="primary"):
        imported=[]
        for f in files:
            try:
                rows, source = parse_timetable_file(f,default_group=selected_group,use_ocr=use_ocr)
                imported.extend(rows)
                st.success(f"{f.name}: {len(rows)} row(s) parsed via {source}.")
            except Exception as exc: st.error(f"Could not process {f.name}: {exc}")
        if imported:
            imported_data={"classes":imported,"teachers":[],"rooms":[],"students":[{"id":selected_group,"size":0}]}
            teacher_names=sorted({x["teacher"] for x in imported if x["teacher"]!="UNKNOWN"})
            room_names=sorted({x["room"] for x in imported if x["room"]!="UNKNOWN"})
            imported_data["teachers"]=[{"name":t,"qualified_courses":sorted({x["course"] for x in imported if x["teacher"]==t}),"available_slots":{}} for t in teacher_names]
            imported_data["rooms"]=[{"name":r,"capacity":60} for r in room_names]
            seed_from_data(imported_data,source="document_import",replace_classes=True)
            st.success(f"Imported {len(imported)} timetable record(s) into SQLite.")
            st.dataframe(pd.DataFrame(imported),use_container_width=True,hide_index=True)

elif page == "Teachers":
    st.markdown('<div class="section-title">Teacher Metadata & Availability</div>',unsafe_allow_html=True)
    rows=[{"Teacher":t["name"],"Qualified courses":", ".join(t.get("qualified_courses",[])),"Available slots":sum(len(v) for v in t.get("available_slots",{}).values())} for t in data["teachers"]]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.markdown("### Record an absence")
    if data["teachers"]:
        teacher=st.selectbox("Teacher",sorted({t["name"] for t in data["teachers"]}))
        absence_date=st.date_input("Absence date",value=date.today())
        reason=st.text_input("Reason","")
        if st.button("Record absence",type="primary"):
            record_absence(teacher,absence_date.isoformat(),reason); st.success(f"Recorded {teacher} as absent on {absence_date}."); st.rerun()

elif page == "Rooms":
    st.markdown('<div class="section-title">Room Inventory</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(data["rooms"]),use_container_width=True,hide_index=True)

elif page == "Academic Calendar":
    st.markdown('<div class="section-title">Academic Calendar Intelligence</div>',unsafe_allow_html=True)
    calendar_file=st.file_uploader("Upload academic calendar",type=["pdf","csv","xlsx","xls"],key="calendar_upload")
    restricted=st.checkbox("Treat restricted holidays as blocked",value=False)
    if calendar_file and st.button("Parse & save calendar",type="primary"):
        try:
            events,warnings=parse_academic_calendar(calendar_file,use_ocr=True)
            save_calendar(events,restricted_as_holiday=restricted)
            for w in warnings: st.warning(w)
            if events:
                st.success(f"Saved {len(events)} calendar event(s) to SQLite.")
                st.dataframe(pd.DataFrame(events),use_container_width=True,hide_index=True)
            else: st.error("No calendar events were parsed, so nothing was saved.")
        except Exception as exc: st.error(f"Could not process academic calendar: {exc}")
    else: st.caption("Supported: PDF, CSV, XLSX and XLS. Scanned PDFs automatically fall back to Tesseract when needed.")

elif page == "OCR Intake":
    st.markdown('<div class="section-title">Document Intake & OCR</div>',unsafe_allow_html=True)
    st.info("AASE accepts PDF, CSV and Excel for timetable and academic-calendar intake. OCR is only needed when a PDF contains images/scans instead of selectable text.")
    st.code("PDF → text extraction → parser → SQLite\nScanned PDF → Tesseract OCR → parser → SQLite\nCSV/XLSX/XLS → pandas → normalized records → SQLite",language="text")
    st.markdown("### Tesseract configuration")
    st.write("Install Tesseract 5.x locally. If it is not on PATH, set TESSERACT_CMD to the full tesseract.exe path.")
    st.code('Windows example:\nTESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe',language="text")
    st.success("OCR is local and free; no Google Cloud account or API key is required.")

elif page == "Disruptions":
    st.markdown('<div class="section-title">Disruption Management</div>',unsafe_allow_html=True)
    disruption_type=st.radio("Failure type",["Teacher unavailable","Room unavailable"],horizontal=True)
    targets=sorted({x["teacher"] if disruption_type=="Teacher unavailable" else x["room"] for x in data["classes"]})
    target=st.selectbox("Resource",targets or ["No resources found"])
    if disruption_type == "Teacher unavailable":
        d1,d2=st.columns(2)
        with d1: disruption_day=st.selectbox("Absent day",["Monday","Tuesday","Wednesday","Thursday","Friday"],key="disruption_day")
        with d2: disruption_slot=st.selectbox("Absent slot",["09:00-10:00","10:00-11:00","11:15-12:15","12:15-13:15","14:00-15:00","15:00-16:00"],key="disruption_slot")
    else:
        disruption_day=None
        disruption_slot=None
    if st.button("Simulate disruption",type="primary"):
        result=simulate_disruption(data,disruption_type,target,day=disruption_day,slot=disruption_slot,time_limit=10); st.session_state["last_result"]=result; record_run("Disruption simulation",result.get("status","UNKNOWN"),result.get("summary",""))
    if "last_result" in st.session_state:
        result=st.session_state["last_result"]
        (st.success if result.get("status") in {"OPTIMAL","FEASIBLE"} or result.get("changed") else st.warning)(result.get("summary","Completed."))
        if result.get("schedule"): st.dataframe(pd.DataFrame(result["schedule"]),use_container_width=True,hide_index=True)
        for r in result.get("reasons",[]): st.write("• "+r)

elif page == "Optimization":
    st.markdown('<div class="section-title">AASE Optimization Engine</div>',unsafe_allow_html=True)
    operation=st.selectbox("Operation",["Optimize whole timetable","Repair one disruption","Heuristic repair","Robustness analysis"])
    teacher_names=sorted({t["name"] for t in data["teachers"]})
    absent_teacher=st.selectbox("Absent teacher",teacher_names) if teacher_names else ""
    c1,c2=st.columns(2)
    with c1: absent_day=st.selectbox("Day",["Monday","Tuesday","Wednesday","Thursday","Friday"])
    with c2: absent_slot=st.selectbox("Slot",["09:00-10:00","10:00-11:00","11:15-12:15","12:15-13:15","14:00-15:00","15:00-16:00"])
    if st.button("Run AASE",type="primary"):
        if operation=="Optimize whole timetable": result=optimize_whole_timetable(data,time_limit=15,absent_teacher=absent_teacher,absent_day=absent_day,absent_slot=absent_slot)
        elif operation=="Repair one disruption": result=optimize_timetable(data,student_id=selected_group,absent_teacher=absent_teacher,absent_day=absent_day,absent_slot=absent_slot)
        elif operation=="Heuristic repair": result=repair_schedule(data,absent_day,absent_slot,absent_teacher,selected_group)
        else:
            rb=robustness_report(data,time_limit=5); result={"status":"COMPLETE","summary":f"Tested {rb['checks']} single-resource disruptions.","reasons":[f"Recoverable: {rb['recoverable_checks']}/{rb['checks']} ({rb['robustness_percent']}%)."]}; st.session_state["robustness"]=rb
        st.session_state["last_result"]=result; record_run(operation,result.get("status","UNKNOWN"),result.get("summary",""))
    if "last_result" in st.session_state:
        result=st.session_state["last_result"]
        (st.success if result.get("status") in {"OPTIMAL","FEASIBLE","COMPLETE"} or result.get("changed") else st.warning)(result.get("summary","Operation completed."))
        if result.get("schedule"): st.dataframe(pd.DataFrame(result["schedule"]),use_container_width=True,hide_index=True)
        for r in result.get("reasons",[]): st.write("• "+r)
        rb=st.session_state.get("robustness")
        if rb: st.metric("Single-resource robustness",f"{rb['robustness_percent']}%",f"{rb['recoverable_checks']}/{rb['checks']} recoverable")

else:
    st.markdown('<div class="section-title">Reports & Audit Trail</div>',unsafe_allow_html=True)
    runs=recent_runs(50)
    if runs: st.dataframe(pd.DataFrame(runs),use_container_width=True,hide_index=True)
    else: st.info("No AASE operations have been recorded yet.")
    st.markdown("### Architecture")
    st.code("ERP/API or PDF/Tesseract → SQLite normalized data → CP-SAT optimizer → repaired timetable → dashboard",language="text")

st.divider()
st.caption("AASE is ERP-agnostic: SQLite is the local project database today; a college ERP API can become the production data source later.")
