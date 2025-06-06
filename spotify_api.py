
# spotify_api.py
import requests
import base64
import time
from dotenv import load_dotenv
import os


load_dotenv()  # Carga variables desde .env
# Llena con tus propias claves desde Spotify Developer Dashboard

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"

class SpotifyAPI:
    def __init__(self):
        self.access_token = None
        self.token_expiration = 0

    def _get_token(self):
        auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {b64_auth_str}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            self.token_expiration = time.time() + token_info["expires_in"]
        else:
            raise Exception("Error al obtener el token de Spotify")

    def _ensure_token(self):
        if not self.access_token or time.time() > self.token_expiration:
            self._get_token()

    def buscar_uri(self, consulta):
        self._ensure_token()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": consulta, "type": "track", "limit": 1}
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        if response.status_code == 200:
            results = response.json()
            items = results.get("tracks", {}).get("items", [])
            if items:
                return items[0]["uri"]  # Devuelve la URI interna Spotify

        return None
