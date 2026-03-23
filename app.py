import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle_securisee_123")

# Initialisation du client Groq
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''<body style="background:#1e1e2e; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;"><form method="post" style="background:#2a2b32; padding:20px; border-radius:10px;"><h2>Accès IA</h2><input type="password" name="password" placeholder="Code: 1234" style="padding:10px; border-radius:5px; border:none;"><br><br><button type="submit" style="width:100%; background:#10a37f; color:white; border:none; padding:10px; cursor:pointer;">Entrer</button></form></body>'''

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'): return jsonify({"error": "Forbidden"}), 403
    
    try:
        user_message = request.form.get("message")
        image = request.files.get('image')

        # Initialiser l'historique si vide
        if 'history' not in session:
            session['history'] = []
        
        # On ne garde que le texte dans l'historique session (pour éviter que ça soit trop lourd)
        current_msg = {"role": "user", "content": user_message if user_message else "Image envoyée"}
        
        # Préparation de l'envoi à Groq (Texte + Image Base64)
        groq_messages = []
        # On ajoute le passé (en format simple pour Groq)
        for h in session['history']:
            groq_messages.append({"role": h["role"], "content": h["content"]})
            
        # On ajoute le message actuel
        current_content = []
        if user_message:
            current_content.append({"type": "text", "text": user_message})
        
        if image:
            b64_img = base64.b64encode(image.read()).decode('utf-8')
            current_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
        
        groq_messages.append({"role": "user", "content": current_content})

        # Appel API
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=groq_messages,
            max_tokens=1024
        )
        
        reponse = completion.choices[0].message.content
        
        # Sauvegarde dans la mémoire (texte uniquement pour la légèreté)
        session['history'].append({"role": "user", "content": user_message if user_message else ""})
        session['history'].append({"role": "assistant", "content": reponse})
        
        # On garde les 6 derniers échanges
        session['history'] = session['history'][-12:]
        session.modified = True

        return jsonify({"response": reponse})
    
    except Exception as e:
        print(f"ERREUR LOG: {str(e)}") # Vérifie tes logs Render si ça persiste
        return jsonify({"error": "Erreur serveur"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
