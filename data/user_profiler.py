from typing import Dict, List
import re
from collections import Counter
from datetime import datetime
import logging
from ai.claude_client import ClaudeClient, ClaudeAPIError

logger = logging.getLogger(__name__)


class UserProfiler:
    """
    Analyzes user profiles and tweets to extract insights
    """
    
    def __init__(self, cost_tracker=None):
        """Initialize profiler with AI client"""
        try:
            self.claude = ClaudeClient()
            self.cost_tracker = cost_tracker
            logger.info("UserProfiler initialized with AI niche detection")
        except Exception as e:
            logger.warning(f"Could not initialize Claude client: {e}. Will use keyword fallback.")
            self.claude = None
            self.cost_tracker = cost_tracker
    
    def analyze_user(self, user_data: Dict, tweets: List[Dict]) -> Dict:
        """
        Generate comprehensive user profile
        
        Args:
            user_data: User profile from X API
            tweets: List of recent tweets
        
        Returns:
            Dict with analysis results
        """
        logger.info(f"Analyzing user @{user_data.get('username', 'unknown')}")
        
        profile = {
            'handle': user_data.get('username'),
            'user_id': user_data.get('id'),
            'name': user_data.get('name'),
            'bio': user_data.get('description', ''),
            'profile_image': user_data.get('profile_image_url'),
            'basic_metrics': self._extract_basic_metrics(user_data),
            'niche': self._detect_niche(user_data, tweets),
            'content_style': self._analyze_content_style(tweets),
            'posting_rhythm': self._analyze_posting_rhythm(tweets),
            'engagement_baseline': self._calculate_engagement(tweets, user_data),
            'growth_velocity': self._estimate_growth(user_data, tweets)
        }
        
        logger.info(f"Analysis complete for @{profile['handle']} - Niche: {profile['niche']}")
        return profile
    
    def _extract_basic_metrics(self, user_data: Dict) -> Dict:
        """Extract basic account metrics"""
        metrics = user_data.get('public_metrics', {})
        
        return {
            'followers_count': metrics.get('followers_count', 0),
            'following_count': metrics.get('following_count', 0),
            'tweet_count': metrics.get('tweet_count', 0),
            'listed_count': metrics.get('listed_count', 0),
            'follower_following_ratio': self._calculate_ff_ratio(
                metrics.get('followers_count', 0),
                metrics.get('following_count', 0)
            )
        }
    
    def _calculate_ff_ratio(self, followers: int, following: int) -> float:
        """Calculate follower/following ratio"""
        if following == 0:
            return float(followers)
        return round(followers / following, 2)
    
    def _detect_niche(self, user_data: Dict, tweets: List[Dict]) -> str:
        """
        Detect user's niche using AI (with keyword fallback)
        """
        # Try AI detection first if available
        if self.claude:
            try:
                niche = self._detect_niche_with_ai(user_data, tweets)
                logger.info(f"AI detected niche: {niche}")
                return niche
            except Exception as e:
                logger.warning(f"AI niche detection failed: {e}, falling back to keywords")
        
        # Fallback to keyword-based detection
        return self._detect_niche_keywords(user_data, tweets)
    
    def _detect_niche_with_ai(self, user_data: Dict, tweets: List[Dict]) -> str:
        """
        Use Claude to detect niche accurately
        """
        bio = user_data.get('description', '')
        
        # Get sample of recent tweet text
        tweet_samples = []
        for tweet in tweets[:10]:
            text = tweet.get('text', '')
            if text:
                tweet_samples.append(text[:100])
        
        tweet_text = ' '.join(tweet_samples)
        
        prompt = f"""Analyze this X/Twitter account and determine their primary niche/topic.

    **Bio:** {bio[:300]}

    **Recent tweets:** {tweet_text[:600]}

    **Available niches:** tech, business, marketing, design, writing, productivity, finance, crypto, ai, health, education, entertainment, sports, other

    Return ONLY ONE word from the list above. No explanation, just the niche word."""

        system = "You are a content classification expert. Analyze the account and return only the single best-matching niche category from the provided list."
        
        try:
            response = self.claude.complete(
                prompt=prompt,
                system=system,
                temperature=0,
                cost_tracker=self.cost_tracker
            )
            
            # Extract and validate niche
            niche = response.strip().lower()
            
            valid_niches = [
                'tech', 'business', 'marketing', 'design', 'writing',
                'productivity', 'finance', 'crypto', 'ai', 'health',
                'education', 'entertainment', 'sports', 'other'
            ]
            
            if niche in valid_niches:
                return niche
            
            # If response contains one of the valid niches, extract it
            for valid in valid_niches:
                if valid in niche:
                    return valid
            
            logger.warning(f"AI returned invalid niche: {niche}")
            return 'other'
            
        except ClaudeAPIError as e:
            logger.error(f"Claude API error in niche detection: {e}")
            raise
    
    def _detect_niche_keywords(self, user_data: Dict, tweets: List[Dict]) -> str:
        """
        Fallback: Detect user's niche from bio and tweets using keywords
        """
        bio = user_data.get('description', '').lower()
        tweet_text = ' '.join([t.get('text', '').lower() for t in tweets[:20]])
        
        combined_text = f"{bio} {tweet_text}"
        
        # Enhanced keywords
        niche_keywords = {
            'tech': ['developer', 'programming', 'software', 'engineer', 'code', 'tech', 'ai', 'ml', 'data', 'startup', 'openai', 'anthropic'],
            'business': ['entrepreneur', 'founder', 'startup', 'business', 'ceo', 'saas', 'growth', 'revenue', 'ycombinator', 'y combinator'],
            'marketing': ['marketing', 'seo', 'content', 'copywriting', 'branding', 'ads', 'funnel', 'conversion'],
            'design': ['designer', 'ui', 'ux', 'figma', 'graphic', 'brand', 'creative', 'design'],
            'writing': ['writer', 'author', 'writing', 'book', 'newsletter', 'blog', 'content', 'storytelling'],
            'productivity': ['productivity', 'habits', 'efficiency', 'time management', 'gtd', 'focus'],
            'finance': ['finance', 'investing', 'stocks', 'trading', 'wealth', 'money', 'portfolio'],
            'crypto': ['crypto', 'bitcoin', 'ethereum', 'blockchain', 'web3', 'defi', 'nft'],
            'health': ['fitness', 'health', 'nutrition', 'wellness', 'workout', 'diet', 'exercise'],
            'education': ['education', 'learning', 'teacher', 'course', 'teaching', 'student', 'knowledge']
        }
        
        # Score each niche
        niche_scores = {}
        for niche, keywords in niche_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            niche_scores[niche] = score
        
        # Get top niche
        if max(niche_scores.values()) > 0:
            detected_niche = max(niche_scores, key=niche_scores.get)
            logger.info(f"Keyword detected niche: {detected_niche} (score: {niche_scores[detected_niche]})")
            return detected_niche
        
        logger.warning("Could not detect niche, defaulting to 'other'")
        return 'other'
    
    def _analyze_content_style(self, tweets: List[Dict]) -> Dict:
        """
        Analyze tweet composition and style
        """
        if not tweets:
            return self._empty_content_style()
        
        total = len(tweets)
        
        # Count different content types
        thread_count = 0
        media_count = 0
        link_count = 0
        question_count = 0
        
        for tweet in tweets:
            text = tweet.get('text', '')
            entities = tweet.get('entities', {})
            
            # Detect threads
            if self._is_thread_starter(text):
                thread_count += 1
            
            # Detect media (check both entities and tweet-level fields)
            if self._has_media(tweet, entities):
                media_count += 1
            
            # Detect links
            if self._has_link(entities):
                link_count += 1
            
            # Detect questions
            if '?' in text:
                question_count += 1
        
        # Calculate average lengths
        lengths = [len(t.get('text', '')) for t in tweets]
        avg_length = sum(lengths) / total if total > 0 else 0
        
        style = {
            'thread_percentage': round((thread_count / total) * 100, 1),
            'media_percentage': round((media_count / total) * 100, 1),
            'link_percentage': round((link_count / total) * 100, 1),
            'question_percentage': round((question_count / total) * 100, 1),
            'avg_tweet_length': round(avg_length, 0),
            'content_mix': {
                'threads': thread_count,
                'media_posts': media_count,
                'link_posts': link_count,
                'questions': question_count
            }
        }
        
        logger.info(f"Content style: {thread_count} threads, {media_count} media, {link_count} links")
        return style
    
    def _is_thread_starter(self, text: str) -> bool:
        """Check if tweet is a thread starter"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Common thread patterns
        patterns = [
            r'^\d+[/\\]',           # "1/" or "1\"
            r'^\d+\)',              # "1)"
            r'thread[:\s]',         # "Thread:" or "Thread "
            r'🧵',                  # Thread emoji
            r'👇',                  # Down arrow
            r'a thread',            # "A thread"
        ]
        
        return any(re.search(pattern, text_lower) for pattern in patterns)
    
    def _has_media(self, tweet: Dict, entities: Dict) -> bool:
        """Check if tweet has media (images, videos, GIFs)"""
        # Check entities for media
        if 'media' in entities and entities['media']:
            return True
        
        # Check tweet-level media field (some APIs include it here)
        if 'media' in tweet and tweet['media']:
            return True
        
        # Check for extended entities
        if 'extended_entities' in tweet and 'media' in tweet.get('extended_entities', {}):
            return True
        
        return False
    
    def _has_link(self, entities: Dict) -> bool:
        """Check if tweet has external link"""
        if not entities or 'urls' not in entities:
            return False
        
        urls = entities.get('urls', [])
        if not urls:
            return False
        
        # Filter out X/Twitter links (these are usually for quoted tweets)
        external_urls = [
            u for u in urls 
            if u.get('expanded_url') and 
            'twitter.com' not in u.get('expanded_url', '') and
            'x.com' not in u.get('expanded_url', '')
        ]
        
        return len(external_urls) > 0
    
    def _analyze_posting_rhythm(self, tweets: List[Dict]) -> Dict:
        """
        Analyze posting frequency and timing
        """
        if not tweets:
            return {'posts_per_week': 0, 'consistency_score': 0, 'date_range_days': 0, 'total_analyzed': 0}
        
        # Parse dates - handle multiple date formats
        dates = []
        for tweet in tweets:
            created_at = tweet.get('created_at')
            if not created_at:
                continue
            
            try:
                date = None
                
                # FIXED: Check Twitter format FIRST (has spaces)
                # Format 1: Twitter format "Sat Nov 22 02:46:05 +0000 2025"
                if created_at.count(' ') >= 5:
                    try:
                        date = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    except ValueError:
                        pass
                
                # Format 2: ISO format with Z
                if not date and ('Z' in created_at or 'T' in created_at):
                    try:
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # Format 3: Simple ISO fallback
                if not date:
                    try:
                        date = datetime.fromisoformat(created_at)
                    except ValueError:
                        pass
                
                if date:
                    dates.append(date)
                    
            except Exception as e:
                logger.debug(f"Could not parse date '{created_at}': {e}")
                continue
        
        if len(dates) < 2:
            logger.warning(f"Not enough valid dates parsed: {len(dates)} from {len(tweets)} tweets")
            return {
                'posts_per_week': 0, 
                'consistency_score': 0,
                'date_range_days': 0,
                'total_analyzed': len(tweets)
            }
        
        # Calculate date range
        dates_sorted = sorted(dates)
        date_range = (dates_sorted[-1] - dates_sorted[0]).days
        
        if date_range == 0:
            # All tweets on same day
            posts_per_week = len(tweets)
        else:
            posts_per_week = round((len(tweets) / date_range) * 7, 1)
        
        # Consistency score (simplified)
        # 7+ posts/week = 100, linear scale below that
        consistency_score = min(100, int((posts_per_week / 7) * 100))
        
        logger.info(f"Posting rhythm: {posts_per_week} posts/week over {date_range} days ({len(dates)} tweets)")
        
        return {
            'posts_per_week': posts_per_week,
            'consistency_score': consistency_score,
            'date_range_days': date_range,
            'total_analyzed': len(tweets)
        }
    
    def _calculate_engagement(self, tweets: List[Dict], user_data: Dict) -> Dict:
        """
        Calculate average engagement metrics
        """
        if not tweets:
            return self._empty_engagement()
        
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        
        for tweet in tweets:
            metrics = tweet.get('public_metrics', {})
            total_likes += metrics.get('like_count', 0)
            total_retweets += metrics.get('retweet_count', 0)
            total_replies += metrics.get('reply_count', 0)
        
        count = len(tweets)
        followers = user_data.get('public_metrics', {}).get('followers_count', 1)
        
        avg_likes = total_likes / count
        avg_retweets = total_retweets / count
        avg_replies = total_replies / count
        
        # Engagement rate = (total engagements) / (followers * tweet count) * 100
        total_engagements = total_likes + total_retweets + total_replies
        engagement_rate = (total_engagements / followers / count) * 100 if followers > 0 else 0
        
        return {
            'avg_likes': round(avg_likes, 1),
            'avg_retweets': round(avg_retweets, 1),
            'avg_replies': round(avg_replies, 1),
            'engagement_rate': round(engagement_rate, 2),
            'total_engagements': total_engagements,
            'engagement_per_tweet': round(total_engagements / count, 1)
        }
    
    def _estimate_growth(self, user_data: Dict, tweets: List[Dict]) -> Dict:
        """
        Estimate growth velocity
        """
        metrics = user_data.get('public_metrics', {})
        followers = metrics.get('followers_count', 0)
        tweet_count = metrics.get('tweet_count', 0)
        
        # Estimate based on activity level
        if tweet_count > 0 and followers > 0:
            rhythm = self._analyze_posting_rhythm(tweets)
            posts_per_week = rhythm.get('posts_per_week', 0)
            
            # More active accounts grow faster (heuristic)
            if posts_per_week >= 7:
                growth_rate = 0.05  # 5%
            elif posts_per_week >= 3:
                growth_rate = 0.03  # 3%
            else:
                growth_rate = 0.01  # 1%
            
            estimated_30d_growth = int(followers * growth_rate)
        else:
            estimated_30d_growth = 0
            growth_rate = 0
        
        return {
            'estimated_30d_growth': estimated_30d_growth,
            'growth_rate_pct': round((growth_rate * 100) if growth_rate else 0, 2)
        }
    
    def _empty_content_style(self) -> Dict:
        """Return empty content style dict"""
        return {
            'thread_percentage': 0,
            'media_percentage': 0,
            'link_percentage': 0,
            'question_percentage': 0,
            'avg_tweet_length': 0,
            'content_mix': {
                'threads': 0,
                'media_posts': 0,
                'link_posts': 0,
                'questions': 0
            }
        }
    
    def _empty_engagement(self) -> Dict:
        """Return empty engagement dict"""
        return {
            'avg_likes': 0,
            'avg_retweets': 0,
            'avg_replies': 0,
            'engagement_rate': 0,
            'total_engagements': 0,
            'engagement_per_tweet': 0
        }


# Test function
def test_profiler():
    """Test the user profiler with sample data"""
    sample_user = {
        'username': 'testuser',
        'id': '12345',
        'name': 'Test User',
        'description': 'Software developer building AI products',
        'public_metrics': {
            'followers_count': 5000,
            'following_count': 500,
            'tweet_count': 1200
        }
    }
    
    sample_tweets = [
        {
            'text': '1/ Here\'s a thread about Python...',
            'created_at': '2024-01-15T10:30:00Z',
            'public_metrics': {'like_count': 50, 'retweet_count': 10, 'reply_count': 5},
            'entities': {'urls': [{'expanded_url': 'https://example.com'}]}
        },
        {
            'text': 'Just shipped a new feature!',
            'created_at': '2024-01-14T14:20:00Z',
            'public_metrics': {'like_count': 30, 'retweet_count': 5, 'reply_count': 2},
            'entities': {}
        },
    ]
    
    profiler = UserProfiler()
    profile = profiler.analyze_user(sample_user, sample_tweets)
    
    print("✅ Profile analysis complete!")
    print(f"   Niche: {profile['niche']}")
    print(f"   Engagement Rate: {profile['engagement_baseline']['engagement_rate']}%")
    print(f"   Posts/Week: {profile['posting_rhythm']['posts_per_week']}")
    print(f"   Threads: {profile['content_style']['thread_percentage']}%")


if __name__ == "__main__":
    test_profiler()