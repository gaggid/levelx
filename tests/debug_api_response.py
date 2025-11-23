import sys
sys.path.append('.')

import requests
from config.settings import settings
import json
import time

def debug_raw_api():
    """Check raw API response"""
    
    api_key = settings.TWITTERAPI_KEY
    handle = "naval"
    
    print(f"\n🔍 Testing TwitterAPI.io with @{handle}\n")
    
    # Test 1: User Info
    print("="*60)
    print("TEST 1: User Info Endpoint")
    print("="*60)
    
    url1 = "https://api.twitterapi.io/twitter/user/info"
    headers = {"X-API-Key": api_key}
    params1 = {"userName": handle}
    
    response1 = requests.get(url1, headers=headers, params=params1)
    print(f"Status: {response1.status_code}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"Response keys: {list(data1.keys())}")
        if 'data' in data1:
            user = data1['data']
            print(f"User name: {user.get('name')}")
            print(f"Followers: {user.get('followers'):,}")
            print(f"✅ User endpoint working!")
    else:
        print(f"❌ Error: {response1.text}")
    
    print("\n" + "="*60)
    print("TEST 2: Last Tweets Endpoint")
    print("="*60)
    
    time.sleep(5)  # Rate limit
    
    url2 = "https://api.twitterapi.io/twitter/user/last_tweets"
    params2 = {"userName": handle, "count": 20}
    
    response2 = requests.get(url2, headers=headers, params=params2)
    print(f"Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"\nResponse keys: {list(data2.keys())}")
        
        if 'tweets' in data2:
            tweets = data2['tweets']
            print(f"Total tweets returned: {len(tweets)}")
            
            if tweets:
                print(f"\n📝 First tweet analysis:")
                first = tweets[0]
                print(f"   Type: {first.get('type')}")
                print(f"   ID: {first.get('id')}")
                print(f"   Text: {first.get('text', 'N/A')[:100]}...")
                print(f"   Is Reply: {first.get('isReply')}")
                print(f"   Has retweeted_tweet: {'retweeted_tweet' in first}")
                print(f"   Like Count: {first.get('likeCount')}")
                print(f"   Created At: {first.get('createdAt')}")
                
                print(f"\n📊 Tweet type breakdown:")
                types = {}
                replies = 0
                retweets = 0
                
                for tweet in tweets:
                    tweet_type = tweet.get('type', 'unknown')
                    types[tweet_type] = types.get(tweet_type, 0) + 1
                    
                    if tweet.get('isReply'):
                        replies += 1
                    if 'retweeted_tweet' in tweet or tweet_type == 'retweet':
                        retweets += 1
                
                print(f"   Types: {types}")
                print(f"   Replies: {replies}")
                print(f"   Retweets: {retweets}")
                print(f"   Original tweets: {len(tweets) - replies - retweets}")
                
                print(f"\n📄 Full first tweet structure:")
                print(json.dumps(first, indent=2)[:1000] + "...")
                
            else:
                print("❌ No tweets in response!")
        else:
            print(f"❌ No 'tweets' key in response!")
            print(f"Response: {json.dumps(data2, indent=2)[:500]}")
    else:
        print(f"❌ Error: {response2.text}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    debug_raw_api()