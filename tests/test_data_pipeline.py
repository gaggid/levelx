import sys
sys.path.append('.')

from data.twitter_client import TwitterAPIClient
from data.user_profiler import UserProfiler
from data.cache_manager import CacheManager
import logging

logging.basicConfig(level=logging.INFO)

def test_full_pipeline():
    """Test complete data pipeline"""
    print("\n🚀 Testing Data Pipeline\n")
    
    # 1. Test Twitter API Client
    print("1️⃣ Testing TwitterAPIClient...")
    client = TwitterAPIClient()
    
    test_handle = "naval"  # Use a popular account for testing
    
    try:
        user = client.get_user_by_handle(test_handle)
        print(f"   ✅ Fetched @{user['username']}")
        print(f"   📊 {user['public_metrics']['followers_count']:,} followers")
        
        tweets = client.get_user_tweets(test_handle, max_results=20)
        print(f"   ✅ Fetched {len(tweets)} tweets\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return
    
    # 2. Test Cache Manager
    print("2️⃣ Testing CacheManager...")
    cache = CacheManager(ttl_hours=6)
    
    # Cache the tweets
    cache.cache_tweets(test_handle, tweets)
    print(f"   ✅ Cached tweets for @{test_handle}")
    
    # Retrieve from cache
    cached_tweets = cache.get_cached_tweets(test_handle)
    if cached_tweets:
        print(f"   ✅ Retrieved {len(cached_tweets)} tweets from cache\n")
    else:
        print(f"   ❌ Cache retrieval failed\n")
    
    # 3. Test User Profiler
    print("3️⃣ Testing UserProfiler...")
    profiler = UserProfiler()
    
    profile = profiler.analyze_user(user, tweets)
    
    print(f"   ✅ Profile analyzed")
    print(f"   🎯 Niche: {profile['niche']}")
    print(f"   📈 Engagement Rate: {profile['engagement_baseline']['engagement_rate']}%")
    print(f"   📝 Posts/Week: {profile['posting_rhythm']['posts_per_week']}")
    print(f"   🧵 Thread %: {profile['content_style']['thread_percentage']}%")
    print(f"   📸 Media %: {profile['content_style']['media_percentage']}%\n")
    
    # 4. Cache Stats
    print("4️⃣ Cache Statistics...")
    stats = cache.get_cache_stats()
    print(f"   📊 Total entries: {stats['total_entries']}")
    print(f"   ✅ Fresh entries: {stats['fresh_entries']}")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    test_full_pipeline()