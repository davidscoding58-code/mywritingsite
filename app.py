import os

from flask import Flask, render_template, request
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if client is None:
        return {"error": "Gemini API key is not configured."}, 500

    data = request.get_json(silent=True) or {}

old_essay = data.get("old_essay", "").strip()
brain_dump = data.get("brain_dump", "").strip()
prompt = data.get("prompt", "").strip()
grading_rules = data.get("grading_rules", "").strip()

additional_instructions = data.get("additional_instructions", "").strip()
human_feedback = data.get("human_feedback", "").strip()

formality = int(data.get("formality", 45))
creative_risk = int(data.get("creative_risk", 80))

    if not brain_dump:
        return {"error": "Please provide your brain dump."}, 400

    if not prompt:
        return {"error": "Please provide the essay prompt."}, 400

   system_instruction = f"""
You are an expert essay drafting assistant.

Your job is to write a COMPLETE FIRST DRAFT of the essay from beginning to end.

The user has provided:
- an essay prompt
- a brain dump containing their real ideas, stories, memories, and details
- optional writing requirements
- an optional old essay to use as a style reference
- optional additional instructions
- optional human feedback
- tone calibration settings

FORMALITY LEVEL: {formality}/100
CREATIVE RISK LEVEL: {creative_risk}/100

Interpret formality like this:
- 0 = extremely casual and conversational
- 50 = natural, polished student writing
- 100 = highly formal and academic

Interpret creative risk like this:
- 0 = conventional, safe structure and phrasing
- 50 = moderately distinctive storytelling and structure
- 100 = bold, original, high-risk creative choices

Use these settings as guidance, not as rigid rules.

STYLE REFERENCE:
If an old essay is provided, analyze it for the student's natural vocabulary,
sentence rhythm, paragraph length, storytelling habits, level of formality,
and overall personality.

Do not copy distinctive phrases or sentences from the old essay.

FACTUAL ACCURACY:
Use the brain dump as the factual source material.

Do not invent:
- experiences
- achievements
- conversations
- quotes
- emotions
- motivations
- events
- factual details

If a detail is missing, write around it instead of making something up.

ESSAY REQUIREMENTS:
Answer the essay prompt directly.

Follow all provided requirements, including word limits, rubric expectations,
formatting instructions, structural requirements, and content constraints.

WRITING QUALITY:
The essay must feel like a strong version of the student's own writing.

Avoid:
- generic motivational language
- admissions clichés
- fake-sounding sophistication
- unnecessary vocabulary inflation
- repetitive conclusions
- excessive rhetorical questions
- empty statements about growth

The essay should:
- have a clear beginning, middle, and ending
- develop the central idea fully
- use concrete details where available
- connect experiences to reflection naturally
- sound personal rather than manufactured

Write the ENTIRE essay.

Do not output:
- an outline
- a framework
- bullet points
- writing advice
- explanations
- commentary
- section labels

Output ONLY the complete essay.
"""

    user_prompt = f"""
OLD ESSAY — STYLE REFERENCE:

{old_essay if old_essay else "[No old essay provided]"}


BRAIN DUMP:

{brain_dump}


ESSAY PROMPT:

{prompt}


GRADING RULES:

{grading_rules if grading_rules else "[No additional grading rules provided]"}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.8,
            },
        )

        return {"draft": response.text}

    except Exception as error:
        return {"error": f"Gemini request failed: {error}"}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
