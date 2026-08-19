 import os
from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for
from google import genai


app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")

SITE_PASSWORD = os.environ.get("SITE_PASSWORD")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        if SITE_PASSWORD and password == SITE_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))

        error = "Incorrect password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    if client is None:
        return {
            "error": "Gemini API key is not configured on the server."
        }, 500

    data = request.get_json(silent=True) or {}

    old_essay = data.get("old_essay", "").strip()
    brain_dump = data.get("brain_dump", "").strip()
    prompt = data.get("prompt", "").strip()
    grading_rules = data.get("grading_rules", "").strip()

    if not brain_dump:
        return {"error": "Please provide your brain dump."}, 400

    if not prompt:
        return {"error": "Please provide the essay prompt."}, 400

    system_instruction = """
You are an expert college-essay drafting assistant.

Your job is to turn a student's raw material into a strong FIRST-DRAFT
FOUNDATION for an essay.

The student's old essay is provided as a STYLE REFERENCE. Analyze its
characteristics and write in a style that is strongly consistent with the
student's natural writing patterns.

Prioritize:
- The student's natural vocabulary
- Their sentence length and rhythm
- Their level of formality
- Their storytelling tendencies
- Their way of explaining personal experiences
- Their natural personality and perspective

Do NOT copy distinctive sentences or phrases from the old essay.
The old essay is for style analysis, not content copying.

Use the student's brain dump as the factual source material.

IMPORTANT:
- Do not invent achievements, experiences, conversations, emotions,
  motivations, or details that are not supported by the student's material.
- Do not manufacture fake stories simply to make the essay stronger.
- If a detail is unclear, write around it rather than inventing it.
- Preserve the student's actual perspective.
- Do not make the writing unnecessarily sophisticated.
- Avoid generic inspirational language and admissions clichés.
- The result should sound like a strong version of the student, not like
  a professional adult writer.

The essay prompt is the assignment you must answer.
The grading rules are constraints you must follow.

Produce only the draft itself. Do not explain your reasoning.
"""

    user_prompt = f"""
OLD ESSAY — STYLE REFERENCE:

{old_essay if old_essay else "[No old essay provided]"}


BRAIN DUMP — STUDENT'S RAW MATERIAL:

{brain_dump}


ESSAY PROMPT:

{prompt}


GRADING RULES / REQUIREMENTS:

{grading_rules if grading_rules else "[No additional grading rules provided]"}


Now create the first-draft foundation.
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

        draft = response.text

        return {"draft": draft}

    except Exception as error:
        return {
            "error": f"Gemini request failed: {str(error)}"
        }, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
