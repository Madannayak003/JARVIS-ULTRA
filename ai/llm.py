import requests
from config.settings import OLLAMA_MODEL, OLLAMA_URL


def ask(prompt):

    try:

        response = requests.post(

            OLLAMA_URL,

            json={

                "model": OLLAMA_MODEL,

                "prompt": prompt,

                "stream": False

            }

        )

        response.raise_for_status()

        return response.json()["response"]

    except Exception as e:

        print(e)

        return "Sorry sir, my AI brain is offline."