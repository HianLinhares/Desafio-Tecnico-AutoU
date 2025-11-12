from flask import Flask, render_template, request, jsonify
import re
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Configuração para produção
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'your-api-key-here')

def preprocess_text(text):
    """Pré-processamento do texto do email"""
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.lower()
    text = ' '.join(text.split())
    return text

def extract_text_from_txt(file):
    """Extrai texto de arquivos TXT"""
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        return f"Erro ao ler arquivo TXT: {str(e)}"

def classify_email(text):
    """Classifica o email usando análise de palavras-chave"""
    productive_keywords = [
        'problema', 'ajuda', 'suporte', 'erro', 'solicitação', 
        'atualização', 'status', 'urgente', 'importante', 'caso',
        'sistema', 'tecnico', 'requisição', 'dúvida', 'questão',
        'suporte', 'assistencia', 'resolver', 'conserto', 'manutenção',
        'bug', 'falha', 'cliente', 'contrato', 'projeto', 'desenvolvimento'
    ]
    
    unproductive_keywords = [
        'obrigado', 'agradeço', 'parabéns', 'feliz', 'natal', 
        'ano novo', 'cumprimentos', 'saudações', 'atenciosamente',
        'felicitações', 'agradecimentos', 'cumprimento', 'saudação',
        'festas', 'feriado', 'final de semana', 'bom dia', 'boa tarde'
    ]
    
    text_lower = text.lower()
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    if productive_count > unproductive_count:
        return "Produtivo", productive_count, unproductive_count
    elif unproductive_count > productive_count:
        return "Improdutivo", productive_count, unproductive_count
    else:
        # Análise de contexto para desempate
        if any(word in text_lower for word in ['suporte', 'problema', 'erro', 'urgente', 'cliente']):
            return "Produtivo", productive_count, unproductive_count
        else:
            return "Improdutivo", productive_count, unproductive_count

def generate_response(category, email_text, productive_count, unproductive_count):
    """Gera resposta automática baseada na categoria"""
    word_count = len(email_text.split())
    
    if category == "Produtivo":
        if productive_count >= 3:
            return "URGENTE: Nossa equipe de suporte técnico já foi acionada para resolver sua solicitação. Você receberá uma atualização em até 1 hora útil."
        elif 'status' in email_text.lower() or 'atualização' in email_text.lower():
            return "Informamos que sua solicitação está em andamento. Nossa previsão de conclusão é de 24-48 horas úteis. Agradecemos sua paciência."
        elif any(word in email_text.lower() for word in ['bug', 'erro', 'falha']):
            return "Relato de problema técnico recebido. Nossa equipe de desenvolvimento está analisando a questão e retornará com uma solução."
        else:
            responses = [
                "Agradecemos seu contato. Nossa equipe analisará sua solicitação e retornará em breve.",
                "Recebemos sua solicitação. Estamos trabalhando nela e atualizaremos você em até 24 horas.",
                "Obrigado por reportar. Nossa equipe de suporte já foi notificada e entrará em contato em breve."
            ]
            return responses[min(word_count // 50, len(responses) - 1)]
    else:
        responses = [
            "Agradecemos sua mensagem. Estamos sempre à disposição para ajudá-lo quando necessário.",
            "Obrigado pelo contato. Ficamos felizes com sua mensagem e estamos disponíveis para qualquer necessidade.",
            "Agradecemos sua mensagem. Caso precise de assistência, não hesite em nos contatar.",
            "Obrigado por compartilhar. Estamos aqui para ajudar quando precisar."
        ]
        return responses[min(word_count // 30, len(responses) - 1)]

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
            
            # Verificar tipo de arquivo (apenas TXT para simplificar)
            if file.filename.endswith('.txt'):
                email_text = extract_text_from_txt(file)
            else:
                return jsonify({'error': 'Para deploy na nuvem, use apenas arquivos .txt'}), 400
        else:
            return jsonify({'error': 'Nenhum texto ou arquivo de email fornecido'}), 400
        
        if len(email_text.strip()) < 5:
            return jsonify({'error': 'O texto do email é muito curto'}), 400
        
        # Pré-processar texto
        processed_text = preprocess_text(email_text)
        
        # Classificar email
        category, prod_count, unprod_count = classify_email(processed_text)
        
        # Gerar resposta
        response = generate_response(category, email_text, prod_count, unprod_count)
        
        # Retornar resultado
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
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

# Para produção
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)