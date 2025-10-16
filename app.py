# app.py
import streamlit as st
import requests
import textwrap
import json
from typing import List

# ---------- CONFIG ----------
BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")  # set in Streamlit secrets
TIMEOUT = 60  # seconds for backend calls

# ---------- HELPERS ----------
def post_json(endpoint: str, payload: dict):
    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"
    try:
        with st.spinner("Contacting backend..."):
            resp = requests.post(url, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
    except requests.RequestException as e:
        st.error(f"Backend request failed: {e}")
        return None

def show_code_with_lines(code: str, lang: str = "python"):
    # Add line numbers as simple example and display in code block
    lines = code.splitlines()
    numbered = "\n".join(f"{i+1:3d}: {line}" for i, line in enumerate(lines))
    st.code(numbered, language=lang)

def display_youtube_list(videos: List[dict]):
    for v in videos:
        title = v.get("title", "YouTube video")
        video_id = v.get("video_id") or v.get("id") or v.get("url")
        if not video_id:
            continue
        # support either a full url or just id
        if video_id.startswith("http"):
            url = video_id
        else:
            url = f"https://www.youtube.com/watch?v={video_id}"
        st.markdown(f"**{title}**")
        st.video(url)

# ---------- UI ----------
st.set_page_config(page_title="CodeExplain — AI Code Tutor", layout="wide")
st.title("CodeExplain — Generative AI Code Explainer (Streamlit Frontend)")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Your code")
    with st.form(key="code_form"):
        lang = st.selectbox("Language", ["python", "javascript", "java", "cpp", "csharp", "go"], index=0)
        expertise = st.selectbox("Your level", ["Beginner", "Intermediate", "Advanced"])
        code_area = st.text_area("Paste code here", height=300, placeholder="# paste code or upload file", key="code_area")
        uploaded = st.file_uploader("Or upload a file", type=["py", "js", "java", "cpp", "cs", "go"])
        col1, col2, col3 = st.columns(3)
        with col1:
            explain_btn = st.form_submit_button("Explain (line-by-line)")
        with col2:
            fix_btn = st.form_submit_button("Detect & Fix Errors")
        with col3:
            practice_btn = st.form_submit_button("Generate Practice Questions")
        st.form_submit_button("Clear", on_click=lambda: st.session_state.update({"code_area": ""}))

    # If uploaded file, read it
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        # put into the text area for editing
        code_area = raw
        st.success(f"Loaded {uploaded.name}")

with col_right:
    st.subheader("Options & Settings")
    safe_run = st.checkbox("Allow remote code execution (backend sandbox)", value=False)
    include_youtube = st.checkbox("Include YouTube resources", value=True)
    max_tokens = st.slider("Model tokens (backend hint)", 256, 4096, 1024)
    st.markdown("---")
    st.markdown("**Session**")
    st.write(f"Language: {lang} • Level: {expertise}")
    st.button("Save preferences (placeholder)")

# ---------- ACTIONS ----------
if explain_btn or fix_btn or practice_btn:
    if not code_area or not code_area.strip():
        st.warning("Please paste or upload some code first.")
    else:
        payload = {
            "code": code_area,
            "language": lang,
            "user_level": expertise.lower(),
            "options": {
                "safe_run": safe_run,
                "include_youtube": include_youtube,
                "max_tokens": max_tokens
            }
        }

        if explain_btn:
            result = post_json("/explain", payload)
            if result:
                st.header("Line-by-line Explanation")
                summary = result.get("summary")
                if summary:
                    st.markdown("**Summary:**")
                    st.write(summary)

                lines = result.get("lines")
                # If backend returns line-by-line list
                if lines and isinstance(lines, list):
                    # show original code at top
                    st.subheader("Original code")
                    show_code_with_lines(code_area, lang)
                    st.markdown("----")
                    # display line explanations in accordions
                    for item in lines:
                        # support either dict items or tuples
                        ln = item.get("line_number", None) or item.get("ln", None)
                        code = item.get("code", "")
                        expl = item.get("explanation", "") or item.get("explain", "")
                        header = f"Line {ln}" if ln else (code.strip()[:40] or "Line")
                        with st.expander(header):
                            st.markdown(f"```{lang}\n{code}\n```")
                            st.write(expl)
                else:
                    # fallback: show a single explanation text
                    explanation = result.get("explanation") or result.get("text")
                    st.write(explanation or "No detailed line-by-line returned.")

                # YouTube resources
                vids = result.get("related_videos") or result.get("videos")
                if include_youtube and vids:
                    st.markdown("---")
                    st.subheader("YouTube resources")
                    display_youtube_list(vids)

        if fix_btn:
            result = post_json("/fix", payload)
            if result:
                st.header("Detected Issues & Fixes")
                patches = result.get("patches", [])
                fixed_code = result.get("fixed_code")
                if patches:
                    for p in patches:
                        st.markdown(f"**Issue:** {p.get('issue','')}")
                        st.write(p.get("explanation",""))
                        if p.get("patch"):
                            st.code(p.get("patch"), language=lang)
                if fixed_code:
                    st.markdown("**Fixed code preview**")
                    st.code(fixed_code, language=lang)
                    if st.button("Apply fixed code to editor"):
                        st.session_state["code_area"] = fixed_code
                        st.experimental_rerun()

        if practice_btn:
            result = post_json("/practice", payload)
            if result:
                st.header("Personalized Practice Questions")
                questions = result.get("questions", [])
                for i, q in enumerate(questions, start=1):
                    st.markdown(f"**Q{i} — {q.get('title','Practice question')}**")
                    st.write(q.get("prompt",""))
                    st.write(f"**Difficulty:** {q.get('difficulty','medium')}")
                    if q.get("sample_solution"):
                        with st.expander("Show sample solution"):
                            st.code(q.get("sample_solution"), language=lang)

# ---------- FOOTER ----------
st.sidebar.markdown("---")
st.sidebar.markdown("Built for: Hackathon — Generative AI Code Tutor")
st.sidebar.markdown("Tips: Store backend URL in Streamlit secrets as `backend_url`.")
