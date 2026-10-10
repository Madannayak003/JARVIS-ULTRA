from config.environment import get_env


CLIENT_ID = get_env("SPOTIFY_CLIENT_ID")

CLIENT_SECRET = get_env("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = get_env(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback",
)
