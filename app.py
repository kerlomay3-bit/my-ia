import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
# Une clé secrète pour que les sessions Flask fonctionnent
app.secret_key = "une_cle_secrete_pour_ton_ia_123"

# Ta clé API Groq directement dans le code
API_KEY = "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"
client = Groq(api_key=API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Mot de passe par défaut : 1234
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''
    <body style="background:#1e1e2e; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <form method="post" style="background:#2a2b32; padding:30px; border-radius:15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
            <h2 style="margin-top:0;">Accès IA Perso</h2>
            <input type="password" name="password" placeholder="Mot de passe" style="padding:12px; border-radius:5px; border:none; width:200px;"><br><br>
            <button type="submit" style="width:100%; background:#10a37f; color:white; border:none; padding:12px; border-radius:5px; cursor:pointer; font-weight:bold;">Entrer</button>
        </form>
    </body>
    '''

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('logged_in'):
        return jsonify({"error": "Session expirée"}), 403
    
    try:
        user_message = request.form.get("message")
        image = request.files.get('image')

        # Initialiser l'historique si nouveau chat
        if 'history' not in session:
            session['history'] = []
        
        # Préparation du contenu actuel (Texte + Image)
        current_content = []
        if user_message:
            current_content.append({"type": "text", "text": user_message})
        
        if image:
            b64_img = base64.b64encode(image.read()).decode('utf-8')
            current_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })

        if not current_content:
            return jsonify({"error": "Message vide"}), 400

        # On construit les messages pour Groq (Historique + Message Actuel)
        # Note : On ne stocke que le texte dans l'historique session pour éviter le bug des 4Ko
        groq_messages = []
        for h in session['history']:
            groq_messages.append({"role": h["role"], "content": h["content"]})
        
        groq_messages.append({"role": "user", "content": current_content})

        # Appel à Groq Vision
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=groq_messages,
            max_tokens=1024
        )
        
        reponse = completion.choices[0].message.content
        
        # On sauvegarde le texte dans l'historique session (pour la mémoire)
        session['history'].append({"role": "user", "content": user_message if user_message else ""})
        session['history'].append({"role": "assistant", "content": reponse})
        
        # On limite l'historique aux 8 derniers messages
        session['history'] = session['history'][-8:]
        session.modified = True

        return jsonify({"response": reponse})
    
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Utilisation du port dynamique pour Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
