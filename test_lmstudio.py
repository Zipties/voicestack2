import requests
import json

# Test LM Studio endpoint
url = "http://192.168.40.69:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}
data = {
    "model": "qwen3-8b-192k-josiefied-uncensored-neo-max",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:", json.dumps(result, indent=2))
        print("✓ LM Studio endpoint is working!")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}") 