from flask import Flask, request, render_template
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()
app = Flask(__name__)

# Initialize Gemini with current models
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Current working models (July 2024)
WORKING_MODELS = [
    'gemini-1.5-flash',  # New fast model
    'gemini-1.5-pro',    # New pro model
    'gemini-pro'         # Legacy fallback
]

model = None
for model_name in WORKING_MODELS:
    try:
        model = genai.GenerativeModel(model_name)
        print(f"✅ Successfully loaded: {model_name}")
        break
    except Exception as e:
        print(f"⚠️ {model_name} failed: {str(e)}")

if not model:
    print("❌ No working models found. Available models:")
    for m in genai.list_models():
        print(f"- {m.name}")
    exit(1)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        code = request.form.get("code", "")
        bugs = []
        
        # Static analysis
        if "password =" in code.lower():
            bugs.append("Hardcoded password (Critical)")
        if "SELECT *" in code.upper() and "{" in code:
            bugs.append("Possible SQL injection (Critical)")
            
        # AI analysis with rate limiting
        ai_analysis = ""
        try:
            response = model.generate_content(
                f"""Analyze this code for security issues:
                {code}
                
                Provide concise feedback in this format:
                [Type] [Severity]: [Description]
                [Recommendation]""",
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 300
                }
            )
            ai_analysis = response.text
        except Exception as e:
            ai_analysis = f"⚠️ Analysis error: {str(e)}"
        
        return render_template("index.html",
                           code=code,
                           static_bugs=bugs,
                           ai_analysis=ai_analysis)
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)