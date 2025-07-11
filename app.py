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

def clean_markdown(text):
    """Remove markdown formatting from text"""
    return text.replace('**', '').replace('*', '').replace('`', '')

def extract_fixed_code(response_text):
    """More robust code extraction"""
    text = response_text.strip()
    
    # Case 1: Already clean code
    if not text.startswith('```') and '\n' in text:
        return text
        
    # Case 2: Markdown code block
    if '```' in text:
        parts = text.split('```')
        if len(parts) > 1:
            code_block = parts[1].strip()
            if code_block.startswith('python'):
                return '\n'.join(code_block.split('\n')[1:])
            return code_block
            
    return text  # fallback # Return None if no code block found

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        code = request.form.get("code", "")
        action = request.form.get("action", "analyze_explain")
        
        # Store history (same as before)
        if 'history' not in session:
            session['history'] = []
        session['history'].insert(0, code[:100] + ("..." if len(code) > 100 else ""))
        session['history'] = session['history'][:5]
        
        if action == "fix":
            response = model.generate_content(
            f"""STRICTLY FOLLOW THESE INSTRUCTIONS:
        1. Provide ONLY the complete rewritten/fixed code
        2. DO NOT include any analysis, explanations, or markdown formatting
        3. Ensure the code is production-ready with all security fixes

        Problematic code to fix:
        {code}"""
        )
            # More aggressive code extraction
            fixed_code = response.text.strip()
            if fixed_code.startswith("```") and fixed_code.endswith("```"):
                fixed_code = fixed_code[fixed_code.find('\n')+1:-3].strip()
                
            return render_template("index.html",
                               code=code,
                               fixed_code=fixed_code,
                               history=session.get('history', []))
        
        else:  # Analysis
            response = model.generate_content(
                f"""STRICT INSTRUCTIONS FOR ANALYSIS:
                You are a code analyzer. ONLY provide analysis text.
                DO NOT include any code solutions or examples.
                STRUCTURE OUTPUT AS:
                
                CODE PURPOSE: [1-2 sentences]
                
                SECURITY ISSUES:
                - [Issue 1]
                - [Issue 2]
                
                CODE QUALITY:
                - [Observation 1]
                - [Observation 2]
                
                IMPROVEMENTS:
                - [Suggestion 1]
                - [Suggestion 2]
                
                Analyze this code (NO CODE OUTPUT ALLOWED):
                {code}"""
            )
            return render_template("index.html",
                               code=code,
                               ai_analysis=response.text,
                               history=session.get('history', []))
    
    return render_template("index.html",
                       history=session.get('history', []))

if __name__ == "__main__":
    app.run(debug=True)