import requests
import re
from configfile import gemini_key as api_key

# --- FIX 1: Remove custom headers (only need Content-Type for the request body)
headers = {"Content-Type": "application/json"}

# --- FIX 2: Add the API key as a query parameter in the ENDPOINT URL
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
# Note: The f-string handles injecting the api_key directly here.


def generate_with_gemini(prompt: str):
    data = {"contents": [{"parts": [{"text": f"{prompt}"}]}]}

    # The key is now in the ENDPOINT, so the request is simpler
    response = requests.post(ENDPOINT, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()

        # ... rest of your code to extract and parse the JSON ...
        gemini_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Use regex to find the content between the first [ and the last ]
        match = re.search(r"(\[.*\])", gemini_text, re.DOTALL)

        if match:
            json_string = match.group(1).strip()
        else:
            obj_match = re.search(r"(\{.*\})", gemini_text, re.DOTALL)
            if obj_match:
                json_string = obj_match.group(1).strip()
            else:
                print("Error: Could not find a JSON array or object in the response.")
                return None

        return json_string
    else:
        print("Error:", response.status_code, response.text)
        return None
