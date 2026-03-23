import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
# On définit une clé secrète fixe pour Render
app.secret_key = os.environ.get("SECRET_KEY", "ma_cle_secrete_fixe_123")

# Initialisation du client Groq
API_KEY = os.environ.get("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")
client = Groq(api_key=API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''<body style="background:#1e1e2e; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;"><form method="post" style="background:#2a2b32; padding:20px; border-radius:10px;"><h2>Connexion</h2><input type="password" name="password" style="padding:10px;"><br><br><button type="submit">Entrer</button></form></body>'''

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'): return jsonify({"error": "Session expirée"}), 403
    
    try:
        user_message = request.form.get("message")
        image = request.files.get('image')

        # Construction du contenu pour Groq (Texte + Image éventuelle)
        content = []
        if user_message:
            content.append({"type": "text", "text": user_message})
        
        if image:
            # On encode l'image en base64 pour l'envoyer au modèle Vision
            b64_img = base64.b64encode(image.read()).decode('utf-8')
            content.append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })

        # Appel au modèle Llama 3.2 Vision
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": content}],
            max_tokens=1024
        )
        
        reponse = completion.choices[0].message.content
        return jsonify({"response": reponse})
    
    except Exception as e:
        # Affiche l'erreur réelle dans les logs Render pour le débogage
        print(f"DEBUG: {str(e)}") 
        return jsonify({"error": "Erreur lors de l'appel à l'IA"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
