from flask import Flask, render_template, request, jsonify
import re
import os
import PyPDF2
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Tentar importar openai, se não estiver instalado, usar fallback
try:
    import openai
    openai.api_key = OPENAI_API_KEY
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI não instalada. Usando classificação por palavras-chave.")

# Configurações existentes
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'your-api-key-here')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"
CLASSIFICATION_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
TEXT_GENERATION_MODEL = "microsoft/DialoGPT-medium"

def preprocess_text(text):
    """Pré-processamento do texto do email"""
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    text = ' '.join(text.split())
    return text

def extract_text_from_pdf(pdf_file):
    """Extrai texto de arquivos PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {str(e)}"

def classify_email_with_openai(text):
    """Classifica o email usando OpenAI GPT"""
    if not OPENAI_AVAILABLE:
        return classify_email_fallback(text)
    
    try:
        # Usar requests para fazer a chamada à API da OpenAI
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
            print(f"Erro OpenAI API: {response.status_code}")
            return classify_email_fallback(text)
            
    except Exception as e:
        print(f"Erro na chamada OpenAI: {e}")
        return classify_email_fallback(text)

def classify_email_fallback(text):
    """Classificação fallback com palavras-chave"""
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
    """Gera resposta automática baseada na categoria"""
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
        # Verificar se o request tem dados
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
        
        # Pré-processar texto
        processed_text = preprocess_text(email_text)
        
        # Classificar email usando OpenAI
        category = classify_email_with_openai(processed_text)
        
        # Gerar resposta
        response = generate_response(category, email_text)
        
        # Retornar resultado
        return jsonify({
            'category': category,
            'response': response,
            'processed_text': processed_text[:200] + '...' if len(processed_text) > 200 else processed_text,
            'ai_used': OPENAI_AVAILABLE  # Indicar se usou IA real
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))