import sys
sys.path.append('.')

from data.twitter_client import TwitterAPIClient
import json

client = TwitterAPIClient()
tweets = client.get_user_tweets("naval", max_results=5)

print("🔍 Analyzing tweet structure:\n")

for i, tweet in enumerate(tweets[:2], 1):
    print(f"{'='*60}")
    print(f"TWEET {i}")
    print(f"{'='*60}")
    print(f"Text: {tweet.get('text')[:100]}...")
    print(f"\nEntities keys: {list(tweet.get('entities', {}).keys())}")
    print(f"Entities content: {json.dumps(tweet.get('entities', {}), indent=2)}")
    print()