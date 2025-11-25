import requests
import re
from configfile import gemini_key as api_key

headers = {"Content-Type": "application/json", "X-goog-api-key": f"{api_key}"}
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def generate_with_gemini(prompt: str):
    data = {"contents": [{"parts": [{"text": f"{prompt}"}]}]}

    response = requests.post(ENDPOINT, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()

        # --- THE FIX IS HERE ---
        gemini_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Use regex to find the content between the first [ and the last ]
        # The 's' flag makes '.' match newlines
        match = re.search(r"(\[.*\])", gemini_text, re.DOTALL)

        if match:
            # Extracted string is the first group matched by the regex
            json_string = match.group(1).strip()
        else:
            # Fallback if the regex fails (maybe it returned a JSON object {})
            # Try to match a JSON object {} just in case
            obj_match = re.search(r"(\{.*\})", gemini_text, re.DOTALL)
            if obj_match:
                json_string = obj_match.group(1).strip()
            else:
                # If no JSON structure is found, raise an error or return the raw text
                print("Error: Could not find a JSON array or object in the response.")
                return None

        # Return the clean JSON string, ready for json.loads()
        return json_string
    else:
        print("Error:", response.status_code, response.text)
        return None
