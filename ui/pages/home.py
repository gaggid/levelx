import streamlit as st
from auth.twitter_oauth import TwitterOAuth
from auth.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


def render():
    """Render home/landing page with login"""
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 60px 0 40px 0;">
        <h1 style="font-size: 48px; font-weight: 700; margin-bottom: 20px;">
            See Exactly Why Accounts at <span style="color: #667eea;">Your Level</span> Are Growing Faster
        </h1>
        <p style="font-size: 20px; color: #a0aec0; margin: 20px 0 40px 0;">
            AI-powered X growth intelligence that compares you with similar accounts<br/>
            and tells you exactly what to copy.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔗 Connect X Account - Analyze Free", type="primary", use_container_width=True):
            initiate_oauth()
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Features Section
    st.markdown("---")
    st.markdown("### 🎯 What You'll Get")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📊 Growth Score
        Instant analysis of how fast you're growing compared to peers at your follower level.
        """)
    
    with col2:
        st.markdown("""
        #### 👥 5 Peer Matches
        AI finds accounts similar to yours that are growing faster—real accounts you can study.
        """)
    
    with col3:
        st.markdown("""
        #### 💡 Actionable Insights
        3 specific tactics your peers use that you don't—with exact steps to implement.
        """)
    
    # How It Works
    st.markdown("---")
    st.markdown("### 🚀 How It Works")
    
    steps_col1, steps_col2, steps_col3 = st.columns(3)
    
    with steps_col1:
        st.markdown("""
        **1. Connect X Account**  
        Secure OAuth login (read-only access)
        """)
    
    with steps_col2:
        st.markdown("""
        **2. AI Analyzes Your Profile**  
        We study your content, engagement, and niche
        """)
    
    with steps_col3:
        st.markdown("""
        **3. Get Your Growth Plan**  
        See peers, insights, and action items
        """)


def initiate_oauth():
    """Start OAuth flow"""
    try:
        oauth = TwitterOAuth()
        auth_url = oauth.get_authorization_url()
        
        # Redirect to X authorization
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
        st.info("Redirecting to X for authorization...")
        
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        st.error("❌ Failed to start login. Please check your X API credentials in .env file.")