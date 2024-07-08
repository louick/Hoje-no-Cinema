# Hoje-no-Cinema

Este projeto posta recomendações diárias de filmes no Twitter usando a API do TMDb e a API do Twitter.

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis de ambiente:

TMDB_API_KEY=your_tmdb_api_key
TMDB_IMAGE_BASE_URL=your_tmdb_image_base_url
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_CONSUMER_KEY=your_twitter_consumer_key
TWITTER_CONSUMER_SECRET=your_twitter_consumer_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

### Instalação

1. Clone o repositório.
2. Crie e ative um ambiente virtual:
   ```sh
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate  # Windows

pip install -r requirements.txt


python daily_tweet.py
