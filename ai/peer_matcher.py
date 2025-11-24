from typing import Dict, List, Optional, Tuple
from ai.claude_client import ClaudeClient, ClaudeAPIError
from data.twitter_client import TwitterAPIClient, TwitterAPIError
from data.user_profiler import UserProfiler
from db.models import PeerMatch
from db.connection import get_session
import json
import logging
import re

logger = logging.getLogger(__name__)


class PeerMatcher:
    """
    AI-powered peer account matching system
    """
    
    def __init__(self, cost_tracker=None):
        self.claude = ClaudeClient()
        self.twitter = TwitterAPIClient(cost_tracker=cost_tracker)
        self.profiler = UserProfiler(cost_tracker=cost_tracker)
        self.cost_tracker = cost_tracker
        logger.info("PeerMatcher initialized")
    
    def find_peers(
        self,
        user_profile: Dict,
        count: int = 5,
        save_to_db: bool = False,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar accounts that are growing faster
        """
        logger.info(f"Finding {count} peers for @{user_profile['handle']}")
        
        try:
            # Step 1: Search Twitter for real similar accounts
            suggested_handles = self._search_similar_accounts(user_profile, count)
            logger.info(f"Search found {len(suggested_handles)} accounts")
            
            # Step 2: Validate and fetch peer profiles
            validated_peers = self._validate_peers(suggested_handles)
            logger.info(f"Validated {len(validated_peers)} accounts")
            
            if not validated_peers:
                raise Exception("No valid peer accounts found")
            
            # Step 3: Calculate match scores
            scored_peers = self._score_peers(user_profile, validated_peers)
            
            # Step 3.5: Filter by follower range (remove outliers)
            scored_peers = self._filter_by_follower_range(user_profile, scored_peers)
            
            # Step 4: Filter for faster-growing accounts
            faster_peers = self._filter_faster_growing(user_profile, scored_peers)
            logger.info(f"Found {len(faster_peers)} faster-growing peers")
            
            # Step 5: Sort by match score and take top N
            top_peers = sorted(faster_peers, key=lambda x: x['match_score'], reverse=True)[:count]
            
            # Step 6: Save to database if requested
            if save_to_db and user_id:
                self._save_to_database(user_id, top_peers)
            
            logger.info(f"✅ Returning {len(top_peers)} peer matches")
            return top_peers
            
        except Exception as e:
            logger.error(f"Error in peer matching: {e}")
            raise
    
    def _search_similar_accounts(self, user_profile: Dict, count: int) -> List[str]:
        """
        Search Twitter for real accounts using keywords (no AI hallucination)
        """
        niche = user_profile['niche']
        followers = user_profile['basic_metrics']['followers_count']
        
        # Niche-specific search queries
        search_queries = {
            'finance': ['finance trading', 'stock market', 'investing tips'],
            'tech': ['developer programming', 'software engineer', 'tech founder'],
            'business': ['entrepreneur startup', 'founder business', 'saas'],
            'marketing': ['marketing growth', 'content strategy', 'digital marketing'],
            'ai': ['artificial intelligence', 'machine learning', 'AI developer'],
            'crypto': ['cryptocurrency', 'bitcoin ethereum', 'web3'],
        }
        
        queries = search_queries.get(niche, [niche])
        
        all_handles = []
        
        # WIDER RANGE: For small accounts, be more flexible
        if followers < 1000:
            min_followers = int(followers * 0.3)
            max_followers = int(followers * 5.0)
        else:
            min_followers = int(followers * 0.5)
            max_followers = int(followers * 2.0)
        
        logger.info(f"Searching for accounts with {min_followers:,}-{max_followers:,} followers")
        
        # Track what we're seeing
        follower_counts_seen = []
        
        # Search with multiple queries
        for query in queries:
            try:
                logger.info(f"Searching with query: '{query}'")
                users = self.twitter.search_users(query, max_results=20)
                
                logger.info(f"Search returned {len(users)} users")
                
                # Filter by follower range
                matched_in_query = 0
                for user in users:
                    user_followers = user['public_metrics']['followers_count']
                    follower_counts_seen.append(user_followers)
                    
                    if min_followers <= user_followers <= max_followers:
                        handle = user['username']
                        if handle not in all_handles:
                            all_handles.append(handle)
                            matched_in_query += 1
                            logger.info(f"  ✅ Match: @{handle} ({user_followers:,} followers)")
                            
                            if len(all_handles) >= count * 2:
                                break
                
                logger.info(f"Query '{query}' found {matched_in_query} matches in range")
                
                if len(all_handles) >= count * 2:
                    break
                    
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                continue
        
        # Show what follower counts we saw
        if follower_counts_seen:
            follower_counts_seen.sort()
            logger.info(f"📊 Follower counts seen: min={follower_counts_seen[0]:,}, max={follower_counts_seen[-1]:,}, median={follower_counts_seen[len(follower_counts_seen)//2]:,}")
        
        logger.info(f"✅ Total: Found {len(all_handles)} candidate accounts via search")
        return all_handles[:count * 2]
    
    def _validate_peers(self, handles: List[str]) -> List[Dict]:
        """
        Validate that suggested accounts exist and fetch their profiles
        """
        validated = []
        
        for handle in handles:
            try:
                # Fetch user profile
                user_data = self.twitter.get_user_by_handle(handle)
                
                # Check if account exists
                if not user_data or user_data.get('id') is None:
                    logger.warning(f"❌ Account @{handle} does not exist or is private")
                    continue
                
                # Fetch recent tweets for analysis
                tweets = self.twitter.get_user_tweets(handle, max_results=50)
                
                # Need at least some tweets to analyze
                if not tweets or len(tweets) < 5:
                    logger.warning(f"❌ @{handle} has insufficient tweets for analysis")
                    continue
                
                # Profile the account
                peer_profile = self.profiler.analyze_user(user_data, tweets)
                
                validated.append(peer_profile)
                logger.info(f"✅ Validated @{handle}")
                
            except TwitterAPIError as e:
                logger.warning(f"❌ Could not validate @{handle}: {e}")
                continue
            except Exception as e:
                logger.warning(f"❌ Error profiling @{handle}: {e}")
                continue
        
        return validated
    
    def _score_peers(self, user_profile: Dict, peers: List[Dict]) -> List[Dict]:
        """Calculate match scores for each peer"""
        scored_peers = []
        
        for peer in peers:
            score = 0.0
            reasons = []
            
            # 1. Follower count similarity (30 points max)
            user_followers = user_profile['basic_metrics']['followers_count']
            peer_followers = peer['basic_metrics']['followers_count']
            
            ratio = min(user_followers, peer_followers) / max(user_followers, peer_followers)
            follower_score = ratio * 30
            score += follower_score
            
            if ratio > 0.8:
                reasons.append(f"Similar audience size ({peer_followers:,} followers)")
            
            # 2. Niche match (30 points max)
            if user_profile['niche'] == peer['niche']:
                score += 30
                reasons.append(f"Same niche: {peer['niche']}")
            
            # 3. Content style similarity (20 points max)
            style_score = self._calculate_style_similarity(
                user_profile['content_style'],
                peer['content_style']
            )
            score += style_score
            
            if style_score > 15:
                reasons.append("Similar content style")
            
            # 4. Engagement similarity (20 points max)
            user_eng = user_profile['engagement_baseline']['engagement_rate']
            peer_eng = peer['engagement_baseline']['engagement_rate']
            
            if user_eng > 0 and peer_eng > 0:
                eng_ratio = min(user_eng, peer_eng) / max(user_eng, peer_eng)
                eng_score = eng_ratio * 20
                score += eng_score
                
                if eng_ratio > 0.7:
                    reasons.append(f"Strong engagement ({peer_eng:.1f}%)")
            
            # Add score to peer dict
            peer['match_score'] = round(score, 1)
            peer['match_reason'] = " • ".join(reasons[:3])
            
            scored_peers.append(peer)
        
        return scored_peers
    
    def _calculate_style_similarity(self, user_style: Dict, peer_style: Dict) -> float:
        """Calculate content style similarity score (0-20)"""
        score = 0.0
        
        factors = ['thread_percentage', 'media_percentage', 'link_percentage']
        
        for factor in factors:
            user_val = user_style.get(factor, 0)
            peer_val = peer_style.get(factor, 0)
            
            if user_val == 0 and peer_val == 0:
                similarity = 1.0
            else:
                diff = abs(user_val - peer_val) / 100
                similarity = 1 - min(diff, 1)
            
            score += similarity * (20 / len(factors))
        
        return score
    
    def _filter_by_follower_range(self, user_profile: Dict, peers: List[Dict]) -> List[Dict]:
        """Remove peers outside acceptable follower range"""
        user_followers = user_profile['basic_metrics']['followers_count']
        min_followers = int(user_followers * 0.5)
        max_followers = int(user_followers * 2.0)
        
        filtered = []
        for peer in peers:
            peer_followers = peer['basic_metrics']['followers_count']
            
            if min_followers <= peer_followers <= max_followers:
                filtered.append(peer)
            else:
                logger.info(f"❌ Filtered out @{peer['handle']} - {peer_followers:,} followers outside range")
        
        return filtered
    
    def _filter_faster_growing(self, user_profile: Dict, peers: List[Dict]) -> List[Dict]:
        """Filter to only accounts growing faster than user"""
        user_growth = user_profile['growth_velocity']['estimated_30d_growth']
        
        faster_peers = []
        
        for peer in peers:
            peer_growth = peer['growth_velocity']['estimated_30d_growth']
            
            if peer_growth >= user_growth * 1.1:
                peer['growth_advantage'] = f"+{peer_growth - user_growth:,} followers/month"
                faster_peers.append(peer)
            elif user_growth == 0:
                faster_peers.append(peer)
        
        # If no faster peers found, return best matches anyway
        if not faster_peers and peers:
            logger.warning("No faster-growing peers found, returning best matches anyway")
            return sorted(peers, key=lambda x: x['match_score'], reverse=True)
        
        return faster_peers
    
    def _save_to_database(self, user_id: str, peers: List[Dict]):
        """Save peer matches to database"""
        try:
            session = get_session()
            
            # Delete old matches
            session.query(PeerMatch).filter_by(user_id=user_id).delete()
            
            # Insert new matches
            for peer in peers:
                match = PeerMatch(
                    user_id=user_id,
                    peer_handle=peer['handle'],
                    peer_followers=peer['basic_metrics']['followers_count'],
                    match_score=peer['match_score'],
                    match_reason=peer.get('match_reason', '')
                )
                session.add(match)
            
            session.commit()
            session.close()
            
            logger.info(f"✅ Saved {len(peers)} peer matches to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            session.rollback()
            session.close()