import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import tweepy
import time
import textwrap
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket
from urllib3.connection import HTTPConnection

# Configurar opções de socket
HTTPConnection.default_socket_options = (
    HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
        (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
        (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
    ]
)

# Função para fazer requisições HTTP com retry
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Adicionar cabeçalho User-Agent
def get_with_user_agent(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    return requests_retry_session().get(url, headers=headers)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Chaves da API do TMDb
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_IMAGE_BASE_URL = os.getenv('TMDB_IMAGE_BASE_URL')
TMDB_MOVIE_URL = "https://www.themoviedb.org/movie/"

# Chaves da API do Twitter
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Autenticar com a API do Twitter usando o Client da API v2
client_v2 = tweepy.Client(bearer_token=BEARER_TOKEN, 
                          consumer_key=CONSUMER_KEY, 
                          consumer_secret=CONSUMER_SECRET, 
                          access_token=ACCESS_TOKEN, 
                          access_token_secret=ACCESS_TOKEN_SECRET)

# Autenticar com a API do Twitter usando o API da API v1.1
auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
client_v1 = tweepy.API(auth)

def get_movies_released_on_day(api_key, year):
    today = datetime.now().strftime(f'{year}-%m-%d')
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={api_key}&primary_release_date.gte={today}&primary_release_date.lte={today}&language=pt-BR'
    response = get_with_user_agent(url)
    if response.status_code != 200:
        return {}
    return response.json()

def get_best_movie_of_decade(api_key, start_year, end_year, min_votes=10):
    today = datetime.now().strftime('%m-%d')
    best_movie = None
    for year in range(start_year, end_year + 1):
        url = f'https://api.themoviedb.org/3/discover/movie?api_key={api_key}&primary_release_date.gte={year}-{today}&primary_release_date.lte={year}-{today}&language=pt-BR'
        response = get_with_user_agent(url)
        if response.status_code != 200:
            continue
        movies = response.json().get('results', [])
        for movie in movies:
            if movie.get('vote_count', 0) >= min_votes:
                if not best_movie or movie.get('vote_average', 0) > best_movie.get('vote_average', 0):
                    best_movie = movie
    return best_movie

def get_movie_details(api_key, movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=pt-BR&append_to_response=credits'
    response = get_with_user_agent(url)
    if response.status_code != 200:
        return {}
    return response.json()

def download_image(image_path):
    url = f"{TMDB_IMAGE_BASE_URL}{image_path}"
    response = get_with_user_agent(url)
    if response.status_code == 200:
        with open("temp.jpg", 'wb') as file:
            for chunk in response:
                file.write(chunk)
        return "temp.jpg"
    return None

def create_tweet_content(movie):
    title = movie['title']
    release_date = datetime.strptime(movie['release_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    overview = movie['overview']
    vote_average = movie['vote_average']
    directors = [crew['name'] for crew in movie['credits']['crew'] if crew['job'] == 'Director']
    writers = [crew['name'] for crew in movie['credits']['crew'] if crew['job'] == 'Writer']
    countries = [country['name'] for country in movie['production_countries']]
    genres = [genre['name'] for genre in movie['genres']]
    movie_url = f"{TMDB_MOVIE_URL}{movie['id']}"

    tweet = (
        f"🎬 {title}\n"
        f"📅 Data de Lançamento: {release_date}\n"
        f"⭐ Avaliação: {vote_average}\n"
        f"🎥 Diretor(es): {', '.join(directors)}\n"
        f"✍️ Roteirista(s): {', '.join(writers)}\n"
        f"🌍 País(es) de Origem: {', '.join(countries)}\n"
        f"🎭 Gênero(s): {', '.join(genres)}\n\n"
        f"{overview}\n\n"
        f"🔗 {movie_url}\n#Lançamento #Filmes"
    )
    
    # Truncar o tweet se exceder 280 caracteres
    if len(tweet) > 280:
        tweet = textwrap.shorten(tweet, width=280, placeholder="...")
    return tweet

def post_to_twitter(client_v1, client_v2, message, image_path):
    try:
        # Fazer upload da imagem
        if image_path:
            media = client_v1.media_upload(image_path)
            # Postar o tweet com o texto e a imagem
            response = client_v2.create_tweet(text=message, media_ids=[media.media_id])
        else:
            response = client_v2.create_tweet(text=message)
        print("Tweet postado com sucesso.")
    except tweepy.TweepyException as e:
        print(f"Erro ao postar tweet: {e}")
        if '429' in str(e):
            print("Rate limit atingido. Aguardando antes de tentar novamente.")
            reset_time = int(e.response.headers.get('x-rate-limit-reset', time.time() + 15 * 60))
            sleep_time = max(0, reset_time - time.time())
            print(f"Aguardando {sleep_time / 60:.2f} minutos para reset do rate limit.")
            time.sleep(sleep_time)
            post_to_twitter(client_v1, client_v2, message, image_path)
        elif '403' in str(e):
            print("Limite diário de tweets atingido.")
        elif 'RemoteDisconnected' in str(e):
            print("Conexão remota foi fechada sem resposta. Aguardando e tentando novamente.")
            time.sleep(60)  # Espera de 1 minuto antes de tentar novamente
            post_to_twitter(client_v1, client_v2, message, image_path)

def main():
    decades = [(1920, 1929), (1930, 1939), (1940, 1949), (1950, 1959),
               (1960, 1969), (1970, 1979), (1980, 1989), (1990, 1999),
               (2000, 2009), (2010, 2019), (2020, 2029)]
    
    for start_year, end_year in decades:
        print(f"Processando década {start_year} - {end_year}")
        top_movie = get_best_movie_of_decade(TMDB_API_KEY, start_year, end_year)
        
        if not top_movie:
            print(f"Nenhum filme foi lançado entre {start_year} e {end_year} neste dia.")
            continue
        
        # Obter detalhes adicionais do filme
        movie_details = get_movie_details(TMDB_API_KEY, top_movie['id'])
        top_movie.update(movie_details)
        
        # Criar e postar o tweet
        tweet = create_tweet_content(top_movie)
        image_path = download_image(top_movie['poster_path']) if 'poster_path' in top_movie else None
        post_to_twitter(client_v1, client_v2, tweet, image_path)
        print(f"Tweetado: {tweet}")
        time.sleep(200)

if __name__ == '__main__':
    main()
