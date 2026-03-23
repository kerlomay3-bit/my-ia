import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_123")

# Récupération de la clé API
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''<body style="background:#1e1e2e; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;"><form method="post"><input type="password" name="password" placeholder="Pass: 1234" style="padding:10px;"><button type="submit">Entrer</button></form></body>'''

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user_message = request.form.get("message")
        image = request.files.get('image')

        # Mémoire simple via session
        if 'history' not in session:
            session['history'] = []
        
        # Préparation du contenu du message
        content = []
        if user_message:
            content.append({"type": "text", "text": user_message})
        
        if image:
            b64 = base64.b64encode(image.read()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        if not content:
            return jsonify({"error": "Vide"}), 400

        # On ajoute le message utilisateur à l'historique
        session['history'].append({"role": "user", "content": content})

        # Appel Groq - Syntaxe Corrigée
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=session['history'],
            max_tokens=1024
        )
        
        # Extraction de la réponse (L'erreur venait souvent d'ici)
        reponse = completion.choices[0].message.content
        
        # Sauvegarde de la réponse IA dans l'historique
        session['history'].append({"role": "assistant", "content": reponse})
        
        # Limiter la mémoire pour éviter les bugs de session trop lourde
        if len(session['history']) > 10:
            session['history'] = session['history'][-10:]
            
        session.modified = True
        return jsonify({"response": reponse})
    
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}") # Visible dans les logs Render
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
