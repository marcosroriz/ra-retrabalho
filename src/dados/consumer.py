from src.config.token import config_basic
import requests

# URL da API
url = config_basic['API_URL']

# Definir os cabeçalhos, incluindo o token no campo Authorization
headers = {
    'Authorization': f'Bearer {config_basic['TOKEN']}',
    'Content-Type': 'application/json'
}

# Dados a serem enviados no corpo da requisição (substitua com seus dados)
data = {
    "DataInicial": "01/11/2024",
    "DataFinal": "05/11/2024",
    "CodEmpresa": 2,
    "CodServico": "0" 
} 

# Fazer a requisição POST
response = requests.post(url, headers=headers, json=data)

# Verificar o status da resposta
if response.status_code == 200:
    print('Requisição POST bem-sucedida!')
    print(response.json()) 
else:
    print(f'Erro {response.status_code}: {response.text}')
