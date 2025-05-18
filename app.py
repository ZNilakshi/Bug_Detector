from flask import Flask, request, render_template, session
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment and configure Flask
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "dev-secret-key"

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_code(code):
    """Static analysis"""
    bugs = []
    if "password =" in code.lower():
        bugs.append("Hardcoded password (Critical)")
    if "SELECT *" in code.upper() and "{" in code:
        bugs.append("Possible SQL injection (Critical)")
    return bugs

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        code = request.form.get("code", "")
        action = request.form.get("action", "analyze")
        
        # Store in history (max 5 items)
        if 'history' not in session:
            session['history'] = []
        session['history'].insert(0, code[:100] + ("..." if len(code) > 100 else ""))
        session['history'] = session['history'][:5]
        
        # Handle different actions
        if action == "explain":
            response = model.generate_content(
                f"Explain this code in simple terms:\n\n{code}\n"
                "Focus on what it does, not security issues."
            )
            return render_template("index.html",
                               code=code,
                               ai_analysis=response.text,
                               history=session.get('history', []))
        
        elif action == "fix":
            response = model.generate_content(
                f"Fix security issues in this code:\n\n{code}\n"
                "Show both:\n1. The corrected code\n2. Brief explanations of changes"
            )
            return render_template("index.html",
                               code=code,
                               ai_analysis=response.text,
                               history=session.get('history', []))
        
        else:  # Default analysis
            bugs = analyze_code(code)
            response = model.generate_content(
                f"Analyze this code for security issues:\n\n{code}\n"
                "Format as:\n- [Type] [Severity]: [Description]\n- [Recommendation]"
            )
            return render_template("index.html",
                               code=code,
                               static_bugs=bugs,
                               ai_analysis=response.text,
                               history=session.get('history', []))
    
    return render_template("index.html",
                       history=session.get('history', []))

if __name__ == "__main__":
    app.run(debug=True)