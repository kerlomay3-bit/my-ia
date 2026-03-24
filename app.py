import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = "cle_de_test_123"

# Connexion directe à Groq
client = Groq(api_key="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")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '<body style="background:#1e1e2e;color:white;display:flex;justify-content:center;align-items:center;height:100vh;"><form method="post"><h2>Code: 1234</h2><input type="password" name="password"><button type="submit">Entrer</button></form></body>'

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

        # Préparation du contenu
        message_content = []
        if user_text:
            message_content.append({"type": "text", "text": user_text})
        
        if user_image:
            # On lit l'image et on l'encode
            image_data = base64.b64encode(user_image.read()).decode('utf-8')
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })

        # Appel Groq (Modèle Vision)
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": message_content}]
        )
        
        # Récupération de la réponse
        return jsonify({"response": completion.choices[0].message.content})
    
    except Exception as e:
        print(f"CRASH LOG: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
