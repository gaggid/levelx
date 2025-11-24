from typing import Dict, List, Optional
from ai.claude_client import ClaudeClient, ClaudeAPIError
import json
import logging
import random

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    Generate actionable insights by comparing user with high-performing peers
    Focus: Content quality, not formatting (UI handles presentation)
    """
    
    def __init__(self, cost_tracker=None):
        self.claude = ClaudeClient()
        self.cost_tracker = cost_tracker
        
        # Try to initialize Gemini (optional fallback)
        self.gemini = None
        try:
            from ai.gemini_client import GeminiClient
            self.gemini = GeminiClient()
            logger.info("InsightsGenerator initialized with Claude + Gemini fallback")
        except Exception as e:
            logger.info("InsightsGenerator initialized with Claude only")
    
    def generate_insights(
        self,
        user_profile: Dict,
        peer_profiles: List[Dict],
        num_insights: int = 3
    ) -> Dict:
        """
        Generate actionable insights by comparing user with peers
        
        Returns:
            Dict with:
                - comparison_data: All metrics for UI to display
                - insights: List of insight objects with content
        """
        logger.info(f"Generating {num_insights} insights for @{user_profile['handle']}")
        
        try:
            # Step 1: Calculate comparison metrics
            comparison = self._calculate_comparison(user_profile, peer_profiles)
            logger.info(f"Comparison calculated: {len(comparison['gaps'])} gaps identified")
            
            # Step 2: Identify top opportunities
            opportunities = self._identify_opportunities(comparison)
            logger.info(f"Identified {len(opportunities)} opportunities")
            
            # Step 3: Generate insights with AI (multi-tier fallback)
            insights = self._generate_insights_multi_tier(
                user_profile,
                peer_profiles,
                comparison,
                opportunities,
                num_insights
            )
            
            # Step 4: Package everything for UI
            result = {
                'user': {
                    'handle': user_profile['handle'],
                    'followers': user_profile['basic_metrics']['followers_count']
                },
                'comparison_data': comparison,  # UI can display this however it wants
                'opportunities': opportunities,  # UI can show top gaps
                'insights': insights,            # AI-generated content
                'peer_profiles': [               # UI might want to show peer cards
                    {
                        'handle': p['handle'],
                        'followers': p['basic_metrics']['followers_count'],
                        'growth_rate': p['growth_velocity']['estimated_30d_growth'],
                        'posts_per_week': p['posting_rhythm']['posts_per_week'],
                        'engagement_rate': p['engagement_baseline']['engagement_rate']
                    }
                    for p in peer_profiles
                ]
            }
            
            logger.info(f"✅ Generated {len(insights)} insights with full comparison data")
            return result
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise
    
    def _calculate_comparison(self, user_profile: Dict, peer_profiles: List[Dict]) -> Dict:
        """
        Calculate comprehensive comparison metrics
        Returns clean data structure for UI rendering
        """
        # Extract user metrics
        user_metrics = {
            'posts_per_week': user_profile['posting_rhythm']['posts_per_week'],
            'consistency_score': user_profile['posting_rhythm']['consistency_score'],
            'engagement_rate': user_profile['engagement_baseline']['engagement_rate'],
            'avg_likes': user_profile['engagement_baseline']['avg_likes'],
            'thread_percentage': user_profile['content_style']['thread_percentage'],
            'media_percentage': user_profile['content_style']['media_percentage'],
            'link_percentage': user_profile['content_style']['link_percentage'],
            'question_percentage': user_profile['content_style']['question_percentage'],
            'avg_tweet_length': user_profile['content_style']['avg_tweet_length'],
            'growth_rate': user_profile['growth_velocity']['estimated_30d_growth'],
            'followers': user_profile['basic_metrics']['followers_count']
        }
        
        # Calculate peer statistics (avg, min, max, median)
        peer_metrics_list = []
        for peer in peer_profiles:
            peer_metrics_list.append({
                'posts_per_week': peer['posting_rhythm']['posts_per_week'],
                'consistency_score': peer['posting_rhythm']['consistency_score'],
                'engagement_rate': peer['engagement_baseline']['engagement_rate'],
                'avg_likes': peer['engagement_baseline']['avg_likes'],
                'thread_percentage': peer['content_style']['thread_percentage'],
                'media_percentage': peer['content_style']['media_percentage'],
                'link_percentage': peer['content_style']['link_percentage'],
                'question_percentage': peer['content_style']['question_percentage'],
                'avg_tweet_length': peer['content_style']['avg_tweet_length'],
                'growth_rate': peer['growth_velocity']['estimated_30d_growth'],
                'followers': peer['basic_metrics']['followers_count']
            })
        
        # Calculate statistics for each metric
        peer_stats = {}
        for key in user_metrics.keys():
            values = [p[key] for p in peer_metrics_list]
            values_sorted = sorted(values)
            
            peer_stats[key] = {
                'average': round(sum(values) / len(values), 2),
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'median': round(values_sorted[len(values) // 2], 2)
            }
        
        # Calculate gaps and user percentile
        gaps = {}
        for key in user_metrics:
            user_val = user_metrics[key]
            peer_avg = peer_stats[key]['average']
            gap = peer_avg - user_val
            gap_percentage = (gap / peer_avg * 100) if peer_avg != 0 else 0
            
            # Calculate percentile (where user ranks)
            all_values = [user_val] + [p[key] for p in peer_metrics_list]
            all_values_sorted = sorted(all_values)
            user_rank = all_values_sorted.index(user_val) + 1
            percentile = int((user_rank / len(all_values)) * 100)
            
            gaps[key] = {
                'user': round(user_val, 2),
                'peer_avg': peer_avg,
                'peer_min': peer_stats[key]['min'],
                'peer_max': peer_stats[key]['max'],
                'peer_median': peer_stats[key]['median'],
                'gap': round(gap, 2),
                'gap_percentage': round(gap_percentage, 1),
                'percentile': percentile,
                'user_ahead': gap < 0  # True if user is better than peers
            }
        
        return {
            'user_metrics': user_metrics,
            'peer_stats': peer_stats,
            'gaps': gaps,
            'num_peers': len(peer_profiles)
        }
    
    def _identify_opportunities(self, comparison: Dict) -> List[Dict]:
        """
        Identify top opportunities where peers significantly outperform user
        """
        gaps = comparison['gaps']
        opportunities = []
        
        # Define thresholds for significant gaps
        significant_gaps = {
            'posts_per_week': 2.0,
            'consistency_score': 20,
            'engagement_rate': 0.1,
            'thread_percentage': 10,
            'media_percentage': 15,
            'link_percentage': 20,
            'avg_tweet_length': 30
        }
        
        for metric, threshold in significant_gaps.items():
            gap_data = gaps.get(metric)
            if not gap_data:
                continue
            
            # Determine if this is an opportunity
            is_opportunity = False
            
            if metric == 'link_percentage':
                # For links, user using TOO MANY is bad
                if gap_data['gap'] < -threshold:
                    is_opportunity = True
            else:
                # For most metrics, peers being higher is an opportunity
                if gap_data['gap'] > threshold:
                    is_opportunity = True
            
            if is_opportunity:
                opportunities.append({
                    'metric': metric,
                    'metric_display_name': metric.replace('_', ' ').title(),
                    'user_value': gap_data['user'],
                    'peer_avg': gap_data['peer_avg'],
                    'peer_min': gap_data['peer_min'],
                    'peer_max': gap_data['peer_max'],
                    'gap': gap_data['gap'],
                    'gap_percentage': abs(gap_data['gap_percentage']),
                    'percentile': gap_data['percentile'],
                    'severity': self._calculate_severity(metric, gap_data['gap'], threshold)
                })
        
        # Sort by severity
        opportunities.sort(key=lambda x: x['severity'], reverse=True)
        
        return opportunities
    
    def _calculate_severity(self, metric: str, gap: float, threshold: float) -> float:
        """Calculate impact score for prioritization"""
        impact_weights = {
            'posts_per_week': 3.0,
            'consistency_score': 2.5,
            'engagement_rate': 2.0,
            'media_percentage': 1.5,
            'thread_percentage': 1.5,
            'link_percentage': 1.2,
            'avg_tweet_length': 0.8
        }
        
        weight = impact_weights.get(metric, 1.0)
        gap_ratio = abs(gap) / threshold
        
        return weight * gap_ratio
    
    def _generate_insights_multi_tier(
        self,
        user_profile: Dict,
        peer_profiles: List[Dict],
        comparison: Dict,
        opportunities: List[Dict],
        num_insights: int
    ) -> List[Dict]:
        """
        Generate insights with multi-tier fallback: Claude → Gemini → Templates
        """
        # Tier 1: Try Claude
        try:
            logger.info("Attempting insights generation with Claude...")
            insights = self._generate_insights_with_ai(
                user_profile, peer_profiles, comparison, opportunities, num_insights,
                provider='claude'
            )
            if insights and len(insights) >= num_insights:
                logger.info("✅ Claude insights generated")
                return insights
        except Exception as e:
            logger.warning(f"Claude failed: {e}")
        
        # Tier 2: Try Gemini
        if self.gemini:
            try:
                logger.info("Attempting insights generation with Gemini...")
                insights = self._generate_insights_with_ai(
                    user_profile, peer_profiles, comparison, opportunities, num_insights,
                    provider='gemini'
                )
                if insights and len(insights) >= num_insights:
                    logger.info("✅ Gemini insights generated")
                    return insights
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Tier 3: Templates
        logger.warning("⚠️ Using template-based insights")
        return self._generate_fallback_insights(opportunities, comparison, num_insights)
    
    def _generate_insights_with_ai(
        self,
        user_profile: Dict,
        peer_profiles: List[Dict],
        comparison: Dict,
        opportunities: List[Dict],
        num_insights: int,
        provider: str = 'claude'
    ) -> List[Dict]:
        """
        Generate insights using AI (Claude or Gemini)
        Focus on CONTENT not FORMAT
        """
        # Build content-focused prompt
        prompt = self._build_content_prompt(
            user_profile,
            comparison,
            opportunities,
            peer_profiles,
            num_insights
        )
        
        # System prompt focused on analysis quality
        system = """You are an expert X/Twitter growth analyst. Your job is to:

1. Identify the most impactful gaps between the user and successful peers
2. Explain WHY each gap matters for growth (use data/examples)
3. Provide ONE specific, actionable step to close the gap

Focus on substance, not style. No emojis, no formatting tricks. Just clear analysis.

For each insight, provide:
- Title: Short, descriptive (5-7 words)
- Analysis: What's the gap? Why does it matter? (2-3 sentences, use numbers)
- Action: One specific step with a target metric (1 sentence)

Example:
Title: Post More Consistently
Analysis: You post 0.7 times per week while successful peers post 10+ times weekly. This lack of frequency means the algorithm doesn't prioritize your content, and followers forget about you between posts. Peer @Example grew 120 followers/month by posting daily.
Action: Commit to 5 posts per week (one each weekday) and batch-create content on Sundays."""

        try:
            # Call appropriate AI provider
            if provider == 'claude':
                response = self.claude.complete(
                    prompt=prompt,
                    system=system,
                    temperature=0.8,  # Slightly creative but grounded
                    cost_tracker=self.cost_tracker
                )
            else:  # gemini
                full_prompt = f"{system}\n\n{prompt}"
                response = self.gemini.complete(full_prompt, temperature=0.8)
            
            # Parse into structured data
            insights = self._parse_content_insights(response)
            
            # Enrich with metrics (so UI has all data it needs)
            for i, insight in enumerate(insights):
                if i < len(opportunities):
                    opp = opportunities[i]
                    insight['metrics'] = {
                        'metric': opp['metric'],
                        'user_value': opp['user_value'],
                        'peer_avg': opp['peer_avg'],
                        'gap': opp['gap'],
                        'gap_percentage': opp['gap_percentage'],
                        'percentile': opp['percentile']
                    }
            
            return insights[:num_insights]
            
        except Exception as e:
            logger.error(f"{provider} API error: {e}")
            raise
    
    def _build_content_prompt(
        self,
        user_profile: Dict,
        comparison: Dict,
        opportunities: List[Dict],
        peer_profiles: List[Dict],
        num_insights: int
    ) -> str:
        """
        Build prompt focused on content quality, not formatting
        """
        user_handle = user_profile['handle']
        user_metrics = comparison['user_metrics']
        gaps = comparison['gaps']
        
        # Present data clearly
        metrics_summary = []
        for opp in opportunities[:num_insights + 2]:
            metric = opp['metric']
            gap_data = gaps[metric]
            
            metrics_summary.append(
                f"{opp['metric_display_name']}: "
                f"You have {gap_data['user']:.1f}, "
                f"peers average {gap_data['peer_avg']:.1f} "
                f"(you're at {gap_data['percentile']}th percentile, "
                f"gap of {abs(gap_data['gap']):.1f})"
            )
        
        metrics_text = "\n".join(metrics_summary)
        
        # Top peer examples with real data
        peer_examples = []
        for peer in peer_profiles[:3]:
            peer_examples.append(
                f"@{peer['handle']}: {peer['basic_metrics']['followers_count']:,} followers, "
                f"+{peer['growth_velocity']['estimated_30d_growth']} growth/month, "
                f"{peer['posting_rhythm']['posts_per_week']:.1f} posts/week"
            )
        peer_text = "\n".join(peer_examples)
        
        prompt = f"""Analyze @{user_handle}'s X account and generate {num_insights} growth insights.

USER: @{user_handle}
- {user_metrics['followers']} followers
- Growing at +{user_metrics['growth_rate']} followers/month
- Posts {user_metrics['posts_per_week']:.1f} times/week
- {user_metrics['engagement_rate']:.2f}% engagement rate

TOP PERFORMING PEERS (faster-growing accounts in same niche):
{peer_text}

KEY PERFORMANCE GAPS:
{metrics_text}

Generate {num_insights} insights. For each, focus on:
1. What's the specific gap (use numbers from above)
2. Why it matters for growth (reference peer success)
3. One concrete action to take (with target number)

Be specific. Use real data. Avoid generic advice like "post better content."

Generate {num_insights} insights now (Title, Analysis, Action format):"""

        return prompt
    
    def _parse_content_insights(self, response: str) -> List[Dict]:
        """
        Parse AI response into clean content structure
        Handles various response formats
        """
        insights = []
        
        # Try to identify insight blocks
        lines = response.strip().split('\n')
        
        current_insight = {}
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect field markers
            if line.lower().startswith('title:') or line.startswith('**Title'):
                if current_insight and 'title' in current_insight:
                    insights.append(current_insight)
                    current_insight = {}
                
                title = line.split(':', 1)[-1].strip().strip('*').strip()
                current_insight['title'] = title
                current_field = 'title'
                
            elif line.lower().startswith('analysis:') or line.startswith('**Analysis'):
                current_field = 'analysis'
                analysis_text = line.split(':', 1)[-1].strip()
                current_insight['analysis'] = analysis_text
                
            elif line.lower().startswith('action:') or line.startswith('**Action'):
                current_field = 'action'
                action_text = line.split(':', 1)[-1].strip()
                current_insight['action'] = action_text
                
            elif line.startswith(('1.', '2.', '3.', '###', '##')):
                # Numbered or markdown header - treat as new insight
                if current_insight and 'title' in current_insight:
                    insights.append(current_insight)
                    current_insight = {}
                
                title = line.lstrip('#').lstrip('1234567890.').strip()
                current_insight['title'] = title
                current_field = 'title'
                
            else:
                # Continue current field
                if current_field == 'title':
                    if 'title' not in current_insight:
                        current_insight['title'] = line
                elif current_field == 'analysis':
                    if 'analysis' in current_insight:
                        current_insight['analysis'] += ' ' + line
                    else:
                        current_insight['analysis'] = line
                elif current_field == 'action':
                    if 'action' in current_insight:
                        current_insight['action'] += ' ' + line
                    else:
                        current_insight['action'] = line
        
        # Add last insight
        if current_insight and 'title' in current_insight:
            insights.append(current_insight)
        
        # Clean up insights
        for insight in insights:
            for key in ['title', 'analysis', 'action']:
                if key in insight:
                    # Remove extra whitespace, stars, etc.
                    insight[key] = insight[key].strip('*').strip()
        
        return insights
    
    def _generate_fallback_insights(
        self,
        opportunities: List[Dict],
        comparison: Dict,
        num_insights: int
    ) -> List[Dict]:
        """
        Template-based insights (when AI fails)
        """
        logger.warning("Using template fallback")
        
        user_metrics = comparison['user_metrics']
        peer_stats = comparison['peer_stats']
        
        insights = []
        
        # Templates focused on content
        templates = {
            'posts_per_week': {
                'title': 'Increase Posting Frequency',
                'analysis': f"You post {user_metrics['posts_per_week']:.1f} times per week while successful peers average {peer_stats['posts_per_week']['average']:.1f} posts weekly. Low posting frequency means the algorithm doesn't prioritize your content and followers lose awareness of your account. Regular posting is the #1 driver of growth.",
                'action': f"Post {max(3, int(peer_stats['posts_per_week']['average'] * 0.7))} times per week consistently. Use a scheduling tool to batch-create content."
            },
            'consistency_score': {
                'title': 'Build Posting Consistency',
                'analysis': f"Your consistency score is {user_metrics['consistency_score']}/100 compared to peer average of {peer_stats['consistency_score']['average']}/100. Inconsistent posting signals to both the algorithm and your audience that you're not a reliable creator, reducing reach and engagement.",
                'action': "Post at the same time each day (e.g., 9 AM) for 30 days. Set calendar reminders to build the habit."
            },
            'media_percentage': {
                'title': 'Add More Visual Content',
                'analysis': f"Only {user_metrics['media_percentage']:.0f}% of your posts include visuals while peers use media in {peer_stats['media_percentage']['average']:.0f}% of their posts. Tweets with images or videos get 3x more engagement than text-only posts and perform better in the algorithm.",
                'action': f"Add visuals to at least {int(peer_stats['media_percentage']['average'] * 0.7)}% of posts. Use screenshots, charts, or Canva templates."
            },
            'thread_percentage': {
                'title': 'Create More Thread Content',
                'analysis': f"You write threads {user_metrics['thread_percentage']:.0f}% of the time while successful peers do {peer_stats['thread_percentage']['average']:.0f}%. Threads allow for deeper storytelling, keep readers engaged longer, and demonstrate subject matter expertise.",
                'action': "Write 2 threads per week on your core topics. Aim for 5-8 tweets per thread with clear narrative flow."
            },
            'link_percentage': {
                'title': 'Reduce Link-Heavy Content',
                'analysis': f"You include links in {user_metrics['link_percentage']:.0f}% of posts while peers average {peer_stats['link_percentage']['average']:.0f}%. X's algorithm deprioritizes link posts because they drive traffic away from the platform. Text-only content gets 2-3x more reach.",
                'action': f"Reduce to {int(peer_stats['link_percentage']['average'])}% link posts. Share the insight in the main tweet and put the source link in a reply."
            },
            'engagement_rate': {
                'title': 'Improve Engagement Rate',
                'analysis': f"Your {user_metrics['engagement_rate']:.2f}% engagement rate trails the {peer_stats['engagement_rate']['average']:.2f}% peer average. Higher engagement signals content quality to the algorithm, leading to more reach and faster follower growth.",
                'action': "End posts with questions, reply to every comment within 1 hour, and engage with others' content for 15 minutes before posting your own."
            }
        }
        
        for opp in opportunities[:num_insights]:
            metric = opp['metric']
            if metric in templates:
                template = templates[metric]
                
                insights.append({
                    'title': template['title'],
                    'analysis': template['analysis'],
                    'action': template['action'],
                    'metrics': {
                        'metric': metric,
                        'user_value': opp['user_value'],
                        'peer_avg': opp['peer_avg'],
                        'gap': opp['gap'],
                        'gap_percentage': opp['gap_percentage'],
                        'percentile': opp['percentile']
                    }
                })
        
        return insights[:num_insights]


# Test function
# Test function
def test_insights_generator():
    """Test insights generation with sample data"""
    
    # Sample user profile (you)
    user_profile = {
        'handle': 'MrGaggi',
        'basic_metrics': {
            'followers_count': 661,
            'following_count': 938
        },
        'niche': 'finance',
        'posting_rhythm': {
            'posts_per_week': 0.7,
            'consistency_score': 10
        },
        'content_style': {
            'thread_percentage': 10.0,
            'media_percentage': 0.0,
            'link_percentage': 75.0,
            'question_percentage': 5.0,
            'avg_tweet_length': 150
        },
        'engagement_baseline': {
            'engagement_rate': 0.09,
            'avg_likes': 0.4
        },
        'growth_velocity': {
            'estimated_30d_growth': 5
        }
    }
    
    # Sample peer profiles
    peer_profiles = [
        {
            'handle': 'Stocks_Cg',
            'basic_metrics': {'followers_count': 2225},
            'niche': 'finance',
            'posting_rhythm': {'posts_per_week': 9.7, 'consistency_score': 80},
            'content_style': {
                'thread_percentage': 15.0,
                'media_percentage': 20.0,
                'link_percentage': 30.0,
                'question_percentage': 10.0,
                'avg_tweet_length': 180
            },
            'engagement_baseline': {'engagement_rate': 0.14, 'avg_likes': 3.1},
            'growth_velocity': {'estimated_30d_growth': 105}
        },
        {
            'handle': 'PHI_StockMarket',
            'basic_metrics': {'followers_count': 2587},
            'niche': 'finance',
            'posting_rhythm': {'posts_per_week': 17.5, 'consistency_score': 100},
            'content_style': {
                'thread_percentage': 20.0,
                'media_percentage': 25.0,
                'link_percentage': 35.0,
                'question_percentage': 15.0,
                'avg_tweet_length': 200
            },
            'engagement_baseline': {'engagement_rate': 0.18, 'avg_likes': 4.6},
            'growth_velocity': {'estimated_30d_growth': 123}
        }
    ]
    
    # Generate insights
    generator = InsightsGenerator()
    
    print("\n🧪 Testing Insights Generator\n")
    print("="*60)
    
    # NEW: Handle the Dict return structure
    result = generator.generate_insights(user_profile, peer_profiles, num_insights=3)
    
    # Extract insights from result
    insights = result['insights']
    comparison = result['comparison_data']
    opportunities = result['opportunities']
    
    print(f"\n📊 COMPARISON SUMMARY:")
    print(f"   User: @{result['user']['handle']} ({result['user']['followers']} followers)")
    print(f"   Peers analyzed: {comparison['num_peers']}")
    print(f"   Opportunities identified: {len(opportunities)}")
    print()
    
    # Show top gaps
    print("🎯 TOP PERFORMANCE GAPS:")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"   {i}. {opp['metric_display_name']}: "
              f"You={opp['user_value']:.1f}, "
              f"Peers={opp['peer_avg']:.1f}, "
              f"Gap={abs(opp['gap']):.1f} "
              f"({opp['percentile']}th percentile)")
    print()
    
    # Show insights
    print(f"✅ Generated {len(insights)} insights:\n")
    print("="*60)
    
    for i, insight in enumerate(insights, 1):
        print(f"\n💡 INSIGHT #{i}: {insight['title']}")
        print(f"\n📊 Analysis:")
        print(f"   {insight['analysis']}")
        print(f"\n✅ Action:")
        print(f"   {insight['action']}")
        
        # Show metrics if available
        if 'metrics' in insight:
            m = insight['metrics']
            print(f"\n📈 Metrics:")
            print(f"   You: {m['user_value']:.1f}")
            print(f"   Peers: {m['peer_avg']:.1f}")
            print(f"   Gap: {m['gap']:.1f} ({m['gap_percentage']:.0f}% behind)")
            print(f"   Your Rank: {m['percentile']}th percentile")
        
        print()
    
    print("="*60)
    print("✅ Test complete!")
    
    # Return result for inspection
    return result


if __name__ == "__main__":
    test_insights_generator()