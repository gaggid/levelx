import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('TWITTERAPI_KEY')

print(f"🔑 API Key loaded: {api_key[:10]}..." if api_key else "❌ No API key found")
print()

# Test different endpoint formats
endpoints_to_test = [
    "https://api.twitterapi.io/v1/users/naval",
    "https://api.twitterapi.io/users/naval",
    "https://twitterapi.io/api/v1/users/naval",
]

headers = {"X-API-Key": api_key}

for endpoint in endpoints_to_test:
    print(f"Testing: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()