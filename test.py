import os
import requests


def _post_chat_completion(url: str, api_key: str, model: str, prompt: str) -> tuple[int, str]:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    return response.status_code, response.text


def check_model() -> None:
    prompt = "Explain AI simply in 2 lines."

    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if fireworks_key:
        model_url = os.getenv("FIREWORKS_MODEL_URL", "https://api.fireworks.ai/inference/v1/chat/completions")
        model_name = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-8b-instruct")
        try:
            status_code, text = _post_chat_completion(model_url, fireworks_key, model_name, prompt)
            print(f"Fireworks HTTP {status_code}")
            print(text)
            return
        except requests.RequestException as exc:
            print(f"Fireworks request failed: {exc}")

    if groq_key:
        model_url = os.getenv("GROQ_MODEL_URL", "https://api.groq.com/openai/v1/chat/completions")
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        try:
            status_code, text = _post_chat_completion(model_url, groq_key, model_name, prompt)
            print(f"Groq HTTP {status_code}")
            print(text)
            return
        except requests.RequestException as exc:
            print(f"Groq request failed: {exc}")

    print("Missing FIREWORKS_API_KEY or GROQ_API_KEY. Set one and run again.")


if __name__ == "__main__":
    check_model()