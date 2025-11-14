from flask import Flask, render_template, request, jsonify
import re
import os
import PyPDF2
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import nltk
import ssl


try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords') 
except LookupError:
    nltk.download('stopwords', quiet=True)

load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


try:
    import openai

    if hasattr(openai, 'OpenAI'):
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        print("OpenAI configurada com sucesso (versão nova)")
    else:

        openai.api_key = OPENAI_API_KEY
        OPENAI_AVAILABLE = True
        print("OpenAI configurada com sucesso (versão antiga)")
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI não instalada. Usando classificação por palavras-chave.")


HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'your-api-key-here')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"
CLASSIFICATION_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
TEXT_GENERATION_MODEL = "microsoft/DialoGPT-medium"

def preprocess_text(text):

    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    text = ' '.join(text.split())
    return text

def extract_text_from_pdf(pdf_file):
  
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {str(e)}"

def classify_email_with_openai(text):
  
    if not OPENAI_AVAILABLE:
        return classify_email_fallback(text)
    
    try:
  
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": """Classifique o email como EXATAMENTE 'Produtivo' ou 'Improdutivo'. 
                    Produtivo: solicitações, problemas, questões de trabalho, suporte técnico.
                    Improdutivo: cumprimentos, agradecimentos, mensagens sociais.
                    Responda apenas com uma palavra: 'Produtivo' ou 'Improdutivo'."""
                },
                {
                    "role": "user",
                    "content": f"Classifique este email: {text[:1000]}"
                }
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            category = result['choices'][0]['message']['content'].strip()
            
            if "Produtivo" in category:
                return "Produtivo"
            elif "Improdutivo" in category:
                return "Improdutivo"
            else:
                return classify_email_fallback(text)
        else:
            print(f"Erro OpenAI API: {response.status_code} - {response.text}")
            return classify_email_fallback(text)
            
    except Exception as e:
        print(f"Erro na chamada OpenAI: {e}")
        return classify_email_fallback(text)

def classify_email_fallback(text):
 
    productive_keywords = [
        'problema', 'ajuda', 'suporte', 'erro', 'solicitação', 
        'atualização', 'status', 'urgente', 'importante', 'caso',
        'sistema', 'tecnico', 'requisição', 'dúvida', 'questão',
        'relatório', 'projeto', 'reunião', 'prazo', 'entregável'
    ]
    
    unproductive_keywords = [
        'obrigado', 'agradeço', 'parabéns', 'feliz', 'natal', 
        'ano novo', 'cumprimentos', 'saudações', 'atenciosamente',
        'bom fim de semana', 'abraço', 'abs', 'cumprimentos'
    ]
    
    text_lower = text.lower()
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    if productive_count > unproductive_count:
        return "Produtivo"
    elif unproductive_count > productive_count:
        return "Improdutivo"
    else:
        if len(text.split()) > 20:
            return "Produtivo"
        else:
            return "Improdutivo"

def generate_response(category, email_text):
  
    if category == "Produtivo":
        responses = [
            "Agradecemos seu contato. Nossa equipe analisará sua solicitação e retornará em breve.",
            "Recebemos sua solicitação. Estamos trabalhando nela e atualizaremos você em até 24 horas.",
            "Obrigado por reportar. Nossa equipe de suporte já foi notificada e entrará em contato em breve.",
            "Confirmamos o recebimento de sua requisição. Você receberá uma atualização em breve."
        ]
    else:
        responses = [
            "Agradecemos sua mensagem. Estamos sempre à disposição para ajudá-lo quando necessário.",
            "Obrigado pelo contato. Ficamos felizes com sua mensagem e estamos disponíveis para qualquer necessidade.",
            "Agradecemos sua mensagem. Caso precise de assistência, não hesite em nos contatar.",
            "Obrigado por compartilhar. Estamos aqui para ajudar quando precisar."
        ]
    
    word_count = len(email_text.split())
    if word_count < 50:
        return responses[0]
    elif word_count < 100:
        return responses[1]
    elif word_count < 200:
        return responses[2]
    else:
        return responses[3]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_email_route():
    try:
     
        if 'email_text' in request.form and request.form['email_text'].strip():
            email_text = request.form['email_text']
        elif 'email_file' in request.files:
            file = request.files['email_file']
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            if file.filename.endswith('.txt'):
                email_text = file.read().decode('utf-8')
            elif file.filename.endswith('.pdf'):
                email_text = extract_text_from_pdf(file)
            else:
                return jsonify({'error': 'Formato de arquivo não suportado. Use .txt ou .pdf'}), 400
        else:
            return jsonify({'error': 'Nenhum texto ou arquivo de email fornecido'}), 400
        
     
        processed_text = preprocess_text(email_text)
        
      
        category = classify_email_with_openai(processed_text)
        
   
        response = generate_response(category, email_text)
        
   
        return jsonify({
            'category': category,
            'response': response,
            'processed_text': processed_text[:200] + '...' if len(processed_text) > 200 else processed_text,
            'ai_used': OPENAI_AVAILABLE  # Indicar se usou IA real
        })
    
    except Exception as e:
        print(f"Erro no processamento: {str(e)}")
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

@app.route('/health')
def health_check():
 
    return jsonify({
        'status': 'online', 
        'timestamp': datetime.now().isoformat(),
        'openai_available': OPENAI_AVAILABLE,
        'platform': 'railway'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)