import os
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "une_cle_au_hasard_123")

# Récupère la clé API depuis les variables d'environnement de Render
API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Change "1234" par ton mot de passe voulu
        if request.form.get('password') == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
    return '''
    <body style="background:#343541; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <form method="post" style="background:#40414f; padding:20px; border-radius:10px;">
            <h2>Connexion IA</h2>
            <input type="password" name="password" placeholder="Mot de passe" style="padding:10px; border-radius:5px; border:none;"><br><br>
            <button type="submit" style="width:100%; padding:10px; background:#10a37f; color:white; border:none; border-radius:5px; cursor:pointer;">Entrer</button>
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
        return jsonify({"error": "Non autorisé"}), 401
    
    try:
        user_message = request.form.get("message")
        image = request.files.get('image')

        # GESTION DE LA MÉMOIRE (Stockée dans la session du navigateur)
        if 'chat_history' not in session:
            session['chat_history'] = [{"role": "system", "content": "Tu es un assistant IA intelligent."}]
        
        history = session['chat_history']

        content = []
        if user_message:
            content.append({"type": "text", "text": user_message})
        
        if image:
            # Traitement de l'image pour Groq Vision
            b64_image = base64.b64encode(image.read()).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
            })

        history.append({"role": "user", "content": content})

        # Appel au modèle VISION (Llama 3.2)
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=history,
            max_tokens=1024
        )
        
        response_text = completion.choices[0].message.content
        
        # On ajoute la réponse à l'historique
        history.append({"role": "assistant", "content": response_text})
        
        # On limite l'historique aux 15 derniers messages pour ne pas saturer la session
        session['chat_history'] = history[-15:]
        session.modified = True

        return jsonify({"response": response_text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Port dynamique pour Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
