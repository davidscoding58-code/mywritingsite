import os
from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "temporary-secret")

SITE_PASSWORD = os.environ.get("SITE_PASSWORD")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


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
        return {"error": "Gemini API key is not configured."}, 500

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

Use the old essay only as a style reference. Do not copy distinctive
sentences or phrases from it.

Use the brain dump as the factual source material.

Answer the essay prompt directly and follow the grading rules.

Do not invent experiences, achievements, conversations, emotions, or details.

Write naturally and preserve the student's personality, vocabulary,
sentence rhythm, and level of sophistication.

Avoid generic admissions clichés and unnecessarily sophisticated language.

Create a strong first-draft foundation that the student can edit.

Output only the draft.
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
