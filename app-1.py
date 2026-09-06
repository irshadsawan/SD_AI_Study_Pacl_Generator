import os
import json
import re
from typing import Optional

import streamlit as st
from groq import Groq

# ============================================================
# AI STUDY PACK GENERATOR
# Development: Google Colab
# Deployment: Streamlit
# Model/API: Groq (OpenAI-compatible client)
# ============================================================

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)

# ---------- API KEY ----------
def get_groq_api_key() -> Optional[str]:
    # Streamlit Cloud: add GROQ_API_KEY under Settings > Secrets
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")


def get_client() -> Groq:
    key = get_groq_api_key()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY was not found. Add it to Streamlit Secrets "
            "or set it as an environment variable."
        )
    return Groq(api_key=key)


# ---------- AI GENERATION ----------
def generate_study_pack(
    topic: str,
    level: str,
    subject: str,
    duration: str,
    study_hours: str,
    num_questions: int,
    include_mcqs: bool,
    include_flashcards: bool,
    include_summary: bool,
    include_study_plan: bool,
    model: str,
) -> str:
    client = get_client()

    sections = []
    if include_summary:
        sections.append("1. Clear topic summary with key concepts")
    if include_study_plan:
        sections.append("2. A practical study plan matching the requested duration and hours/day")
    if include_mcqs:
        sections.append(
            f"3. {num_questions} multiple-choice questions with 4 options each, "
            "the correct answer, and a short explanation"
        )
    if include_flashcards:
        sections.append(
            "4. Flashcards in Question → Answer format covering the most important concepts"
        )

    if not sections:
        sections = ["1. A concise but useful study guide"]

    prompt = f"""
You are an expert educational content designer.

Create a complete AI Study Pack for the following learner:

Topic: {topic}
Subject: {subject or "Not specified"}
Academic level: {level}
Available study duration: {duration}
Study time: {study_hours} hours/day

Required sections:
{chr(10).join(sections)}

Quality rules:
- Use accurate, educational language appropriate for the learner's level.
- Organize the content with clear Markdown headings.
- Explain difficult concepts in simple language.
- Do not invent references, statistics, quotations, or citations.
- Make the study plan realistic and progressive.
- For MCQs, make only one option correct and clearly mark the answer.
- Make flashcards concise enough for revision.
- End with a "Final Revision Checklist".
- If the topic is ambiguous, state the interpretation you used.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You create structured, accurate study materials.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=7000,
    )

    return response.choices[0].message.content


def clean_filename(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip())
    return text[:60] or "study_pack"


# ---------- UI ----------
st.title("📚 AI Study Pack Generator")
st.caption(
    "Generate a personalized study pack with summaries, study plans, MCQs, "
    "flashcards, and revision guidance."
)

with st.sidebar:
    st.header("⚙️ Study Settings")

    level = st.selectbox(
        "Learner Level",
        ["Beginner", "Intermediate", "Advanced", "University"],
    )

    subject = st.text_input(
        "Subject (optional)",
        placeholder="e.g. Physics, Python, Pakistan Studies",
    )

    duration = st.selectbox(
        "Study Duration",
        [
            "1 week",
            "2 weeks",
            "4 weeks",
            "6 weeks",
            "8 weeks",
            "12 weeks",
        ],
    )

    study_hours = st.selectbox(
        "Study Time per Day",
        ["30 minutes", "1 hour", "2 hours", "3 hours", "4+ hours"],
    )

    model = st.selectbox(
        "Groq Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ],
    )

    st.divider()

    include_summary = st.checkbox("📝 Summary", value=True)
    include_study_plan = st.checkbox("🗓️ Study Plan", value=True)
    include_mcqs = st.checkbox("❓ MCQs", value=True)
    include_flashcards = st.checkbox("🃏 Flashcards", value=True)

    num_questions = st.slider(
        "Number of MCQs",
        min_value=5,
        max_value=30,
        value=10,
        step=5,
    )

    st.divider()
    st.info(
        "For Streamlit Cloud, store your Groq API key as "
        "`GROQ_API_KEY` in App Settings → Secrets."
    )

topic = st.text_area(
    "🎯 Enter your study topic",
    placeholder=(
        "Example: Introduction to Machine Learning\n"
        "Example: Thermodynamics\n"
        "Example: Constitutional Development of Pakistan"
    ),
    height=120,
)

generate = st.button(
    "🚀 Generate Study Pack",
    type="primary",
    use_container_width=True,
)

if generate:
    if not topic.strip():
        st.warning("Please enter a study topic first.")
        st.stop()

    try:
        with st.spinner("🤖 Creating your personalized study pack..."):
            result = generate_study_pack(
                topic=topic.strip(),
                level=level,
                subject=subject.strip(),
                duration=duration,
                study_hours=study_hours,
                num_questions=num_questions,
                include_mcqs=include_mcqs,
                include_flashcards=include_flashcards,
                include_summary=include_summary,
                include_study_plan=include_study_plan,
                model=model,
            )

        st.session_state["study_pack"] = result
        st.session_state["study_topic"] = topic.strip()

    except Exception as e:
        error = str(e)

        if "GROQ_API_KEY" in error:
            st.error("❌ Groq API key not found.")
            st.code(
                'GROQ_API_KEY = "your_groq_api_key_here"',
                language="toml",
            )
            st.write(
                "On Streamlit Cloud: App → Settings → Secrets → "
                "add the key above."
            )
        else:
            st.error(f"❌ Generation failed: {error}")


# ---------- RESULT ----------
if "study_pack" in st.session_state:
    st.divider()
    st.subheader("📖 Your AI Study Pack")

    st.markdown(st.session_state["study_pack"])

    filename = (
        clean_filename(st.session_state.get("study_topic", "study_pack"))
        + "_study_pack.md"
    )

    st.download_button(
        "⬇️ Download Study Pack",
        data=st.session_state["study_pack"],
        file_name=filename,
        mime="text/markdown",
        use_container_width=True,
    )

    if st.button("🗑️ Clear Study Pack"):
        for key in ["study_pack", "study_topic"]:
            st.session_state.pop(key, None)
        st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("Built with Python + Groq + Streamlit | Development can be done in Google Colab")
