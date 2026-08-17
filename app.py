import re
import streamlit as st
import importlib.util
import streamlit as st

st.write("google:", importlib.util.find_spec("google"))
st.write("google.genai:", importlib.util.find_spec("google.genai"))
st.write("google.generativeai:", importlib.util.find_spec("google.generativeai"))
from google.genai import types

st.set_page_config(
    page_title="Collaborative Essay Framework Builder",
    page_icon="🤝",
    layout="wide",
)

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "style_sample": "",
    "requirements": "",
    "personal_thoughts": "",
    "essay_prompt": "",
    "human_feedback": "",
    "draft_text": "",
    "tone_formality": 3,
    "creative_risk": 3,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def word_count(text):
    return len(re.findall(r"\S+", text.strip())) if text.strip() else 0


def get_secret_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def build_system_instruction(
    style_sample,
    requirements,
    personal_thoughts,
    essay_prompt,
    human_feedback,
    tone_formality,
    creative_risk,
):

    tone_descriptions = {
        1: "Casual and conversational. Use natural speech and avoid unnecessary formality.",
        2: "Mostly conversational with moderate polish.",
        3: "Balanced and polished while maintaining a natural student voice.",
        4: "Formal and sophisticated without sounding artificial.",
        5: "Highly academic and traditional, using sophisticated language where appropriate.",
    }

    creativity_descriptions = {
        1: "Safe and structured. Prioritize clarity and conventional organization.",
        2: "Moderately creative with occasional distinctive phrasing.",
        3: "Balanced creativity. Use memorable language when it serves the story.",
        4: "Bold and expressive. Use distinctive imagery when appropriate.",
        5: "Highly artistic and bold. Allow unusual imagery and metaphors when they genuinely strengthen the essay.",
    }

    return f"""
You are an elite college-application writing coach and structural editor.

Your task is to create a strong FOUNDATION DRAFT for a college application essay.
The student will personally edit, rewrite, and polish the result.

VOICE:
Study the Style Sample carefully. Match its underlying cadence, sentence rhythm,
vocabulary, directness, and personality. Do not copy its specific wording.

REQUIREMENTS:
Follow the target school's requirements, grader expectations, and other
instructions provided by the student.

PERSONAL MATERIAL:
Use the student's actual memories, experiences, opinions, observations, and stories.
NEVER invent achievements, events, relationships, dialogue, locations, or factual
details that the student did not provide.

PROMPT:
The Official Essay Prompt is authoritative. Directly answer the actual question
and respect the specified word count.

HUMAN FEEDBACK:
If Human Feedback is provided, prioritize applying it to the revision unless it
conflicts with the official prompt or factual information.

TONE FORMALITY:
Level {tone_formality}/5
{tone_descriptions[tone_formality]}

CREATIVE RISK:
Level {creative_risk}/5
{creativity_descriptions[creative_risk]}

AVOID GENERIC AI WRITING.

Do not use cliché phrases such as:
- "From a young age..."
- "This experience taught me..."
- "Throughout my journey..."
- "Little did I know..."
- "I have always been passionate about..."
- "It shaped me into the person I am today..."
- generic claims about resilience
- generic claims about leadership
- generic claims about perseverance
- empty moral lessons

Do not make the essay sound like marketing copy or a professional novelist wrote it.

Prioritize specificity, authenticity, strong structure, meaningful reflection,
and a natural student voice.

The result should be a real foundation draft, NOT:
- an outline
- bullet points
- writing advice
- commentary
- an explanation

Return ONLY the foundation draft.

========================
STYLE SAMPLE
========================
{style_sample}

========================
REQUIREMENTS & GRADER STYLE
========================
{requirements}

========================
PERSONAL THOUGHTS & EXPERIENCES
========================
{personal_thoughts}

========================
OFFICIAL ESSAY PROMPT
========================
{essay_prompt}

========================
HUMAN FEEDBACK & REVIEW COMMENTS
========================
{human_feedback if human_feedback.strip() else "No human feedback provided."}
"""


def generate_draft(api_key):

    client = genai.Client(api_key=api_key)

    system_instruction = build_system_instruction(
        st.session_state.style_sample,
        st.session_state.requirements,
        st.session_state.personal_thoughts,
        st.session_state.essay_prompt,
        st.session_state.human_feedback,
        st.session_state.tone_formality,
        st.session_state.creative_risk,
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="""
Create the strongest possible foundation draft using all of the provided
information.

Write the actual essay.

Do not invent factual details.

Return only the draft.
""",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text.strip()


# ============================================================
# HEADER
# ============================================================

st.title("🤝 Collaborative Essay Framework Builder")

st.caption(
    "Build the structural foundation with AI, then edit and polish it yourself."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="Paste your Gemini API key",
        help="Your API key is not stored in the application code.",
    )

    secret_key = get_secret_key()

    effective_key = api_key.strip() or secret_key.strip()

    if secret_key:
        st.success("Gemini API key loaded from Streamlit Secrets.")

    st.divider()

    st.subheader("Style Tuning")

    st.session_state.tone_formality = st.slider(
        "Tone Formality Level",
        min_value=1,
        max_value=5,
        value=st.session_state.tone_formality,
        help="1 = Casual/Conversational, 5 = Highly Academic/Traditional",
    )

    st.session_state.creative_risk = st.slider(
        "Creative Risk-Taking",
        min_value=1,
        max_value=5,
        value=st.session_state.creative_risk,
        help="1 = Safe & Structured, 5 = Artistic/Bold Metaphors",
    )


# ============================================================
# TWO-COLUMN WORKSPACE
# ============================================================

left, right = st.columns(2, gap="large")


# ============================================================
# LEFT COLUMN
# ============================================================

with left:

    st.header("📝 My Inputs")

    st.session_state.style_sample = st.text_area(
        "1. Style Sample",
        value=st.session_state.style_sample,
        height=180,
        placeholder=(
            "Paste a past writing sample showing your natural rhythm, "
            "vocabulary, sentence structure, and personality."
        ),
    )

    st.session_state.requirements = st.text_area(
        "2. Requirements & Grader Style",
        value=st.session_state.requirements,
        height=160,
        placeholder=(
            "Target school, teacher expectations, grading criteria, "
            "required themes, things to avoid, etc."
        ),
    )

    st.session_state.personal_thoughts = st.text_area(
        "3. Personal Thoughts & Experiences",
        value=st.session_state.personal_thoughts,
        height=220,
        placeholder=(
            "Dump your memories, stories, opinions, experiences, "
            "specific moments, observations, and thoughts here."
        ),
    )

    st.session_state.essay_prompt = st.text_area(
        "4. Official Essay Prompt",
        value=st.session_state.essay_prompt,
        height=150,
        placeholder=(
            "Paste the exact college application question and word limit."
        ),
    )

    st.session_state.human_feedback = st.text_area(
        "5. Human Feedback & Review Comments",
        value=st.session_state.human_feedback,
        height=160,
        placeholder=(
            "Optional feedback from a parent, teacher, counselor, "
            "or peer reviewer."
        ),
    )

    if st.button(
        "🚀 Pour / Refine Foundation Draft",
        type="primary",
        use_container_width=True,
    ):

        if not effective_key:
            st.error(
                "Enter your Gemini API key in the sidebar or add "
                "GEMINI_API_KEY to Streamlit Secrets."
            )

        elif not st.session_state.essay_prompt.strip():
            st.error("Enter the official essay prompt.")

        elif not st.session_state.personal_thoughts.strip():
            st.error("Enter your personal thoughts and experiences.")

        else:

            with st.spinner("Building your foundation draft..."):

                try:

                    st.session_state.draft_text = generate_draft(
                        effective_key
                    )

                    st.success("Foundation draft created.")

                except Exception as e:

                    st.error(f"Gemini error: {e}")


# ============================================================
# RIGHT COLUMN
# ============================================================

with right:

    st.header("✍️ My Editing Workspace")

    st.text_area(
        "Foundation Draft",
        key="draft_text",
        height=650,
        placeholder=(
            "Your foundation draft will appear here. "
            "Edit anything you want."
        ),
        label_visibility="collapsed",
    )

    st.metric(
        "Word Count",
        word_count(st.session_state.draft_text),
    )

    st.download_button(
        "⬇️ Download Draft as .txt",
        data=st.session_state.draft_text,
        file_name="essay_foundation_draft.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=not bool(st.session_state.draft_text.strip()),
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI builds the foundation. You control the final essay."
)
