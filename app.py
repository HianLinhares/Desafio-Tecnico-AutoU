from flask import Flask, render_template, request, jsonify
import re
import os

app = Flask(__name__)

def preprocess_text(text):
    """Pré-processamento do texto do email"""
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    return ' '.join(text.split())

def classify_email(text):
    """Classifica o email usando análise de palavras-chave"""
    productive_keywords = [
        'problema', 'ajuda', 'suporte', 'erro', 'solicitação', 
        'atualização', 'status', 'urgente', 'importante', 'caso',
        'sistema', 'tecnico', 'requisição', 'dúvida', 'questão',
        'suporte', 'assistencia', 'resolver', 'conserto', 'manutenção'
    ]
    
    unproductive_keywords = [
        'obrigado', 'agradeço', 'parabéns', 'feliz', 'natal', 
        'ano novo', 'cumprimentos', 'saudações', 'atenciosamente',
        'felicitações', 'agradecimentos', 'cumprimento', 'saudação'
    ]
    
    text_lower = text.lower()
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    if productive_count > unproductive_count:
        return "Produtivo", productive_count, unproductive_count
    else:
        return "Improdutivo", productive_count, unproductive_count

def generate_response(category):
    """Gera resposta automática baseada na categoria"""
    if category == "Produtivo":
        return "Agradecemos seu contato. Nossa equipe analisará sua solicitação e retornará em breve."
    else:
        return "Agradecemos sua mensagem. Estamos sempre à disposição para ajudá-lo quando necessário."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    try:
        # Pegar texto do email
        email_text = request.form.get('email_text', '')
        
        if not email_text.strip():
            return jsonify({'error': 'Por favor, insira um texto de email'}), 400
        
        # Processar e classificar
        processed_text = preprocess_text(email_text)
        category, prod_count, unprod_count = classify_email(processed_text)
        response = generate_response(category)
        
        return jsonify({
            'category': category,
            'response': response,
            'processed_text': processed_text[:200] + '...' if len(processed_text) > 200 else processed_text,
            'stats': {
                'productive_keywords': prod_count,
                'unproductive_keywords': unprod_count,
                'word_count': len(email_text.split())
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)