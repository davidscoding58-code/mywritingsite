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

    if not prompt:
        return {"error": "Please provide the essay prompt."}, 400

    if not brain_dump:
        return {"error": "Please provide your brain dump."}, 400

    system_instruction = f"""
You are an expert essay drafting assistant.

Your job is to write a COMPLETE FIRST DRAFT of the essay from beginning to end.

Use the student's brain dump as the factual source material.

If an old essay is provided, use it only as a style reference. Analyze:
- vocabulary
- sentence rhythm
- paragraph length
- storytelling habits
- level of formality
- overall personality

Do not copy distinctive phrases or sentences from the old essay.

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

Answer the essay prompt directly.

Follow all provided requirements, including:
- word limits
- rubric expectations
- structural requirements
- formatting instructions
- content constraints

FORMALITY LEVEL: {formality}/100

Interpret formality like this:
- 0 = very casual and conversational
- 50 = natural, polished student writing
- 100 = highly formal and academic

CREATIVE RISK LEVEL: {creative_risk}/100

Interpret creative risk like this:
- 0 = conventional and safe
- 50 = moderately distinctive
- 100 = bold and highly original

Use these settings as guidance, not rigid rules.

The essay should:
- have a clear beginning, middle, and ending
- fully develop the main idea
- use concrete details when available
- connect experiences to reflection naturally
- sound personal and believable
- sound like a stronger version of the student's own writing

Avoid:
- generic motivational language
- admissions clichés
- fake-sounding sophistication
- unnecessary vocabulary inflation
- repetitive conclusions
- excessive rhetorical questions
- empty statements about growth

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
ESSAY PROMPT:

{prompt}


BRAIN DUMP:

{brain_dump}


WRITING REQUIREMENTS:

{grading_rules if grading_rules else "[No additional requirements provided]"}


OLD ESSAY — STYLE REFERENCE:

{old_essay if old_essay else "[No style reference provided]"}


ADDITIONAL INSTRUCTIONS:

{additional_instructions if additional_instructions else "[No additional instructions provided]"}


HUMAN FEEDBACK:

{human_feedback if human_feedback else "[No human feedback provided]"}


FORMALITY:

{formality}/100


CREATIVE RISK:

{creative_risk}/100


Write the complete essay now.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
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
