
import os
from flask import Flask, request, jsonify, send_from_directory
import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Rota para servir o arquivo index.html
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Rota que vai receber a imagem e fazer a chamada segura para a API do OpenRouter
@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Pega a chave da API do ambiente, de forma segura
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Erro: Chave da API não encontrada no servidor.")
        return jsonify({"error": "A chave da API não foi encontrada no servidor. Verifique seu arquivo .env"}), 500

    # 2. Pega os dados da imagem enviados pelo frontend
    data = request.json
    print(f"Dados recebidos do frontend: {data}") # Log para depuração
    if not data:
        print("Erro: Dados JSON vazios ou ausentes na requisição.")
        return jsonify({"error": "Requisição inválida: dados JSON vazios ou ausentes."}), 400
    if 'image' not in data:
        print("Erro: Chave 'image' não encontrada nos dados recebidos.")
        return jsonify({"error": "Requisição inválida: chave 'image' não encontrada nos dados."}), 400

    base64_image = data['image']
    print(f"Tamanho da imagem base64 recebida: {len(base64_image)} bytes") # Log para depuração

    # 3. Prepara a requisição para a API do OpenRouter
    # O prompt agora inclui a imagem como parte do conteúdo
    prompt_text = """Analise a imagem do alimento e forneça uma resposta em JSON. As chaves devem ser: "descricao", "ingredientes", "modoDePreparo", "tabelaNutricional", "historia". Os valores devem ser strings formatadas em HTML (use <ul>, <li>, <p>, <strong>). A tabela nutricional deve ser uma string HTML simples."""

    payload = {
        "model": "google/gemini-2.5-flash-image-preview:free", # Modelo especificado pelo usuário
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": base64_image}}
                ]
            }
        ]
    }

    api_url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:5000/", # Pode ser o URL do seu site em produção
        "X-Title": "Leitor de Comida", # Título do seu aplicativo
        "Content-Type": "application/json"
    }

    print(f"Enviando payload para OpenRouter: {payload}") # Log para depuração
    print(f"Headers para OpenRouter: {headers}") # Log para depuração

    # 4. Envia a requisição para o OpenRouter e retorna a resposta para o frontend
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Lança um erro para respostas com status ruim (4xx ou 5xx)
        # Retorna diretamente o JSON da resposta do OpenRouter para o frontend
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao contatar a API do OpenRouter: {e}")
        if response is not None:
            print(f"Status da resposta da API: {response.status_code}")
            print(f"Corpo da resposta da API: {response.text}")
            return jsonify({"error": f"Erro ao se comunicar com a API do OpenRouter: {e}. Status: {response.status_code}. Resposta: {response.text}"}), 500
        return jsonify({"error": f"Erro ao se comunicar com a API do OpenRouter: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
