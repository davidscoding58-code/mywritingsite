import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Collaborative Essay Framework Builder", page_icon="🤝", layout="wide")
st.title("🤝 Collaborative Essay Framework Builder")
st.write("Factor in peer review notes, counselor edits, or teacher comments to upgrade your essay foundation.")

# Sidebar Settings
with st.sidebar:
    st.header("🔑 Settings")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    st.caption("Get a free key from Google AI Studio.")
    
    st.header("🎛️ Dial In Style Parameters")
    formality_level = st.slider("Tone Formality Level:", min_value=1, max_value=5, value=3, 
                                help="1 = Casual/Conversational, 5 = Highly Academic/Traditional")
    creativity_level = st.slider("Creative Risk-Taking:", min_value=1, max_value=5, value=3, 
                                 help="1 = Safe & Structured, 5 = Artistic, Bold Metaphors & Hooks")

# Initialize session state for the draft
if "essay_draft" not in st.session_state:
    st.session_state.essay_draft = ""

# Layout Columns
col1, col2 = st.columns(2)

with col1:
    st.header("🎨 Step 1: Voice & Rules")
    style_sample = st.text_area(
        "Paste a style sample (Your preferred natural writing rhythm):", 
        height=100,
        placeholder="Paste a past writing sample that feels authentic to you..."
    )
    
    audience_guide = st.text_area(
        "Requirements & Grader Style (Target school/teacher expectations):",
        height=100,
        placeholder="Example: Ivy League app reading committee looking for intellectual curiosity."
    )
    
    st.header("🧠 Step 2: Content & Goal")
    personal_thoughts = st.text_area(
        "Brain dump your thoughts, memories, and personal experiences:", 
        height=120,
        placeholder="Unfiltered notes. What happened? What did you learn? Why does it matter?"
    )
    
    prompt_text = st.text_area(
        "Paste the official essay prompt and length constraints:", 
        height=80,
        placeholder="Example: Why do you want to attend our school? Max 250 words."
    )

    st.header("💬 Step 3: Outside Critique")
    human_feedback = st.text_area(
        "Human Feedback & Review Comments (Optional):",
        height=120,
        placeholder="Paste edits from a teacher, parent, or friend here. Example: 'Paragraph 2 is too long' or 'Focus more on the teamwork angle instead of your coding skill.'"
    )
    
    generate_btn = st.button("Pour / Refine Foundation Draft", type="primary")

with col2:
    st.header("🧱 Collaborative Foundation Canvas")
    
    # Trigger AI generation
    if generate_btn:
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif not style_sample or not personal_thoughts or not prompt_text:
            st.error("Please fill out the primary fields (Voice, Substance, and Goal) to generate or refine your text.")
        else:
            with st.spinner("Weaving your stories and peer critiques into the foundation..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # Convert sliders into text descriptions
                    formality_map = {1: "conversational, approachably raw", 2: "semi-formal", 3: "balanced and natural", 4: "polished and highly professional", 5: "deeply academic and elegant"}
                    creativity_map = {1: "safe and highly structured", 2: "standard narrative", 3: "thoughtful storytelling", 4: "bold imagery and unique thematic threads", 5: "experimental and memorable"}
                    
                    system_instruction = (
                        f"You are an elite academic writing coach. Your goal is to draft or refine a foundational essay framework. "
                        f"1. You must mimic the voice, cadence, and structure found in the 'Style Sample'.\n"
                        f"2. Calibrate the text tone to be {formality_map[formality_level]} with a {creativity_map[creativity_level]} structure.\n"
                        f"3. Strictly satisfy the target school guidelines from the 'Requirements' section.\n"
                        f"4. If 'Human Feedback & Review Comments' are provided, prioritize adjusting the text layout to directly fix those issues."
                    )
                    
                    user_content = (
                        f"USER NATURAL VOICE MODEL:\n\"\"\"{style_sample}\"\"\"\n\n"
                        f"GRADER EXPECTATIONS:\n\"\"\"{audience_guide}\"\"\"\n\n"
                        f"RAW PERSONAL EXPERIENCES:\n\"\"\"{personal_thoughts}\"\"\"\n\n"
                        f"OFFICIAL TARGET PROMPT:\n\"\"\"{prompt_text}\"\"\"\n\n"
                        f"CRITICAL HUMAN FEEDBACK TO INTEGRATE (IF ANY):\n\"\"\"{human_feedback}\"\"\""
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.55,
                        )
                    )
                    
                    st.session_state.essay_draft = response.text
                    st.success("Foundation upgraded successfully!")
                    
                except Exception as e:
                    st.error(f"Error during construction: {e}")

    # Interactive canvas
    edited_draft = st.text_area(
        "Interactive Construction Area (Tweak live here):",
        value=st.session_state.essay_draft,
        height=400,
        placeholder="Your customized framework draft will appear here. Edit it directly to perfect the piece.",
        key="editable_canvas"
    )
    
    # Real-time tracking
    word_count = len(edited_draft.split()) if edited_draft.strip() else 0
    st.caption(f"📊 **Word Count:** {word_count} words")
    
    if st.session_state.essay_draft:
        st.download_button(
            label="💾 Download Tailored Draft",
            data=edited_draft,
            file_name="tailored_essay.txt",
            mime="text/plain"
        )
