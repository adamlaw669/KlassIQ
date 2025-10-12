import requests
import os

# Supported local languages
LANGUAGES = ["English", "Hausa", "Yoruba", "Igbo"]

TRANSLATE_API = "https://translation.googleapis.com/language/translate/v2"
API_KEY = os.getenv("GOOGLE_TRANSLATE_KEY")  # optional

def translate_text(content, target_lang):
    """Translate entire JSON structure recursively to target_lang."""
    if target_lang == "English" or not API_KEY:
        return content  # no translation needed or no key

    # Define language map
    lang_code = {
        "Hausa": "ha",
        "Yoruba": "yo",
        "Igbo": "ig"
    }.get(target_lang, "en")

    def translate_string(text):
        payload = {"q": text, "target": lang_code, "format": "text", "key": API_KEY}
        try:
            res = requests.post(TRANSLATE_API, params=payload)
            res.raise_for_status()
            data = res.json()
            return data["data"]["translations"][0]["translatedText"]
        except Exception:
            return text

    def recurse(obj):
        if isinstance(obj, str):
            return translate_string(obj)
        elif isinstance(obj, list):
            return [recurse(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: recurse(v) for k, v in obj.items()}
        else:
            return obj

    return recurse(content)
