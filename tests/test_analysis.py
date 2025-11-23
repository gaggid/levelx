import sys
sys.path.append('.')

from data.twitter_client import TwitterAPIClient
from data.user_profiler import UserProfiler
from data.cache_manager import CacheManager
import logging
import json

logging.basicConfig(level=logging.INFO)

def analyze_account(handle: str):
    """Complete analysis of an X account"""
    print(f"\n🔍 Analyzing @{handle}...\n")
    
    # Initialize components
    client = TwitterAPIClient()
    profiler = UserProfiler()
    cache = CacheManager(ttl_hours=6)
    
    # 1. Check cache first
    print("1️⃣ Checking cache...")
    cached_tweets = cache.get_cached_tweets(handle)
    
    if cached_tweets:
        print(f"   ✅ Found {len(cached_tweets)} cached tweets")
        tweets = cached_tweets
        
        # Still need to fetch user profile (it's fast)
        user = client.get_user_by_handle(handle)
    else:
        # 2. Fetch from API
        print("2️⃣ Fetching from API...")
        user = client.get_user_by_handle(handle)
        tweets = client.get_user_tweets(handle, max_results=50)
        
        # 3. Cache the results
        cache.cache_tweets(handle, tweets)
        print(f"   ✅ Cached {len(tweets)} tweets")
    
    # 4. Analyze profile
    print("\n3️⃣ Analyzing profile...")
    profile = profiler.analyze_user(user, tweets)
    
    # 5. Display results
    print("\n" + "="*60)
    print(f"📊 ANALYSIS RESULTS FOR @{handle}")
    print("="*60)
    
    print(f"\n👤 BASIC INFO:")
    print(f"   Name: {profile['name']}")
    print(f"   Followers: {profile['basic_metrics']['followers_count']:,}")
    print(f"   Following: {profile['basic_metrics']['following_count']:,}")
    print(f"   Total Tweets: {profile['basic_metrics']['tweet_count']:,}")
    
    print(f"\n🎯 NICHE: {profile['niche'].upper()}")
    
    print(f"\n📝 CONTENT STYLE:")
    style = profile['content_style']
    print(f"   Threads: {style['thread_percentage']:.1f}%")
    print(f"   Media Posts: {style['media_percentage']:.1f}%")
    print(f"   Link Posts: {style['link_percentage']:.1f}%")
    print(f"   Questions: {style['question_percentage']:.1f}%")
    print(f"   Avg Length: {style['avg_tweet_length']:.0f} chars")
    
    print(f"\n📈 ENGAGEMENT:")
    engagement = profile['engagement_baseline']
    print(f"   Avg Likes: {engagement['avg_likes']:.1f}")
    print(f"   Avg Retweets: {engagement['avg_retweets']:.1f}")
    print(f"   Avg Replies: {engagement['avg_replies']:.1f}")
    print(f"   Engagement Rate: {engagement['engagement_rate']:.2f}%")
    
    print(f"\n⏰ POSTING RHYTHM:")
    rhythm = profile['posting_rhythm']
    print(f"   Posts/Week: {rhythm['posts_per_week']:.1f}")
    print(f"   Consistency Score: {rhythm['consistency_score']}/100")
    
    print(f"\n🚀 GROWTH:")
    growth = profile['growth_velocity']
    print(f"   Estimated 30d Growth: +{growth['estimated_30d_growth']:,} followers")
    print(f"   Growth Rate: {growth['growth_rate_pct']:.2f}%")
    
    print("\n" + "="*60)
    
    # Save full analysis to JSON
    with open(f'analysis_{handle}.json', 'w') as f:
        json.dump(profile, f, indent=2, default=str)
    print(f"\n💾 Full analysis saved to: analysis_{handle}.json")


if __name__ == "__main__":
    # Test with a known account
    analyze_account("sahilbloom")
    
    # Or try with your own handle
    # analyze_account("MrGaggi")