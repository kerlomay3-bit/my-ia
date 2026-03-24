import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = "cle_fixe_pour_render_123"

# ON MET LA CLÉ ICI DIRECTEMENT POUR ÉVITER L'ERREUR RENDER
try:
    client = Groq(api_key="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")
except Exception as e:
    client = None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '<body style="background:#1e1e2e;color:white;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;"><form method="post" style="background:#2a2b32;padding:20px;border-radius:10px;"><h2>Code: 1234</h2><input type="password" name="password" style="padding:10px;"><br><br><button type="submit" style="width:100%;padding:10px;background:#10a37f;color:white;border:none;cursor:pointer;">Entrer</button></form></body>'

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'): return jsonify({"error": "Auth"}), 403
    try:
        user_text = request.form.get("message")
        user_image = request.files.get('image')
        
        content = []
        if user_text: content.append({"type": "text", "text": user_text})
        if user_image:
            b64 = base64.b64encode(user_image.read()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
        # Appel direct sans historique complexe pour tester
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": content}]
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
