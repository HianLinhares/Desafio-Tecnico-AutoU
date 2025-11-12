from flask import Flask, render_template, request, jsonify
import re
import os
import PyPDF2
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuração da API de IA (usando Hugging Face como exemplo)
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'your-api-key-here')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

# Modelos para classificação e geração de texto
CLASSIFICATION_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
TEXT_GENERATION_MODEL = "microsoft/DialoGPT-medium"

def preprocess_text(text):
    """Pré-processamento do texto do email"""
    # Remover caracteres especiais e números
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Converter para minúsculas
    text = text.lower()
    # Remover espaços extras
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

def classify_email(text):
    """Classifica o email usando IA"""
    # Simulação de classificação (substituir por chamada real à API)
    # Em produção, usaríamos a API do Hugging Face
    
    # Palavras-chave para classificação
    productive_keywords = [
        'problema', 'ajuda', 'suporte', 'erro', 'solicitação', 
        'atualização', 'status', 'urgente', 'importante', 'caso',
        'sistema', 'tecnico', 'requisição', 'dúvida', 'questão'
    ]
    
    unproductive_keywords = [
        'obrigado', 'agradeço', 'parabéns', 'feliz', 'natal', 
        'ano novo', 'cumprimentos', 'saudações', 'atenciosamente'
    ]
    
    text_lower = text.lower()
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    # Lógica simples de classificação
    if productive_count > unproductive_count:
        return "Produtivo"
    elif unproductive_count > productive_count:
        return "Improdutivo"
    else:
        # Em caso de empate, usar análise de sentimento simulada
        if len(text.split()) > 20:  # Emails mais longos tendem a ser produtivos
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
    else:  # Improdutivo
        responses = [
            "Agradecemos sua mensagem. Estamos sempre à disposição para ajudá-lo quando necessário.",
            "Obrigado pelo contato. Ficamos felizes com sua mensagem e estamos disponíveis para qualquer necessidade.",
            "Agradecemos sua mensagem. Caso precise de assistência, não hesite em nos contatar.",
            "Obrigado por compartilhar. Estamos aqui para ajudar quando precisar."
        ]
    
    # Seleciona resposta baseada no comprimento do email
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
            
            # Verificar tipo de arquivo
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
        
        # Classificar email
        category = classify_email(processed_text)
        
        # Gerar resposta
        response = generate_response(category, email_text)
        
        # Retornar resultado
        return jsonify({
            'category': category,
            'response': response,
            'processed_text': processed_text[:200] + '...' if len(processed_text) > 200 else processed_text
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))