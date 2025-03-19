import requests
import json
import logging

# ----------------------- Parameter Configuration -----------------------
API_KEY = "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"             # Replace with your actual API key
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-3.5-turbo"                    # You can change to any supported model
SITE_URL = "https://your-site.example.com"      # Optional: your website URL for leaderboard rankings
SITE_NAME = "YourSiteName"                        # Optional: your site’s name
DEBUG = True                                      # Set to True to enable debug logging

# ----------------------- Logging Configuration -------------------------
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ----------------------- Error Code Mapping ----------------------------
ERROR_CODES = {
    400: "Bad Request: Invalid/missing parameters or CORS issue.",
    401: "Invalid credentials: API key disabled/invalid or OAuth expired.",
    402: "Insufficient credits: Add more credits and retry.",
    403: "Content flagged: Input was moderated.",
    408: "Request timed out.",
    429: "Rate limit reached: Slow down your requests.",
    502: "Model error: Chosen model is down or response is invalid.",
    503: "Model unavailable: No provider meets your routing requirements."
}

# ----------------------- API Communication Function -----------------------
def call_openrouter_api(request_payload: dict) -> dict:
    """
    Sends a POST request to the OpenRouter API with the given JSON payload.
    This version uses default mode (i.e. no structured or formatted JSON enforcement).
    
    Args:
        request_payload (dict): JSON payload including at least a "messages" key.
                                If "model" is missing, the default MODEL is added.
    
    Returns:
        dict: The JSON response from the API or an error object.
    """
    # Prepare HTTP headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    if SITE_URL:
        headers["HTTP-Referer"] = SITE_URL
    if SITE_NAME:
        headers["X-Title"] = SITE_NAME

    # Ensure a model is specified
    if "model" not in request_payload:
        request_payload["model"] = MODEL

    logging.debug("Payload keys: %s", list(request_payload.keys()))

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(request_payload))
        logging.debug("HTTP status code received: %s", response.status_code)
    except requests.exceptions.RequestException as req_err:
        logging.error("Network error occurred: %s", str(req_err))
        return {"error": {"code": None, "message": "Network error occurred", "metadata": str(req_err)}}

    # If HTTP response status code is not 200, handle as an error
    if response.status_code != 200:
        try:
            error_json = response.json()
            err_msg = error_json.get("error", {}).get("message", ERROR_CODES.get(response.status_code, "Unknown HTTP error"))
        except json.JSONDecodeError:
            err_msg = ERROR_CODES.get(response.status_code, "Unknown HTTP error")
            print("Response text (non-JSON):", response.text)
        logging.error("HTTP error %s: %s", response.status_code, err_msg)
        return {"error": {"code": response.status_code, "message": err_msg}}

    try:
        response_json = response.json()
    except json.JSONDecodeError as json_err:
        logging.error("Invalid JSON in response: %s", str(json_err))
        print("Full invalid response text:")
        print(response.text)
        return {
            "error": {
                "code": None,
                "message": "Invalid JSON response",
                "metadata": {"error": str(json_err), "response": response.text}
            }
        }

    # Check if the API returned an error inside the JSON body
    if "error" in response_json:
        error_info = response_json["error"]
        err_code = error_info.get("code", "Unknown")
        err_message = error_info.get("message", "No message provided")
        logging.error("API returned error code %s: %s", err_code, err_message)
        return {"error": {"code": err_code, "message": err_message}}

    # Debug: print a summary of the first message (if present)
    if "choices" in response_json and response_json["choices"]:
        first_choice = response_json["choices"][0]
        if "message" in first_choice:
            content = first_choice["message"].get("content", "")
            summary = content[:100] + "..." if len(content) > 100 else content
            logging.debug("First response message summary: %s", summary)

    return response_json

# ----------------------- Example Usage -----------------------
if __name__ == "__main__":
    # Example payload using default mode (without specifying a response_format)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "What is the meaning of life?"
            }
        ]
    }

    logging.debug("Starting API call with default payload...")
    result = call_openrouter_api(payload)

    if "error" in result:
        print("Error:", result["error"]["message"])
    else:
        # Extract and print a summary of the API response (first 100 characters)
        message = result.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        summary = content[:100] + "..." if len(content) > 100 else content
        print("API Response Summary:", summary)