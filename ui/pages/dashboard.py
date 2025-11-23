import streamlit as st
from auth.session_manager import SessionManager


def render():
    """Render main dashboard"""
    
    user = SessionManager.get_current_user()
    
    if not user:
        st.error("Please login first")
        return
    
    # Header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(f"📈 Welcome back, @{user['x_handle']}!")
    
    with col2:
        if st.button("🚪 Logout"):
            SessionManager.logout()
            st.rerun()
    
    # User Info Card
    st.markdown("---")
    
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        if user.get('x_profile_image'):
            st.image(user['x_profile_image'], width=100)
        st.markdown(f"**@{user['x_handle']}**")
    
    with info_col2:
        st.metric("Followers", f"{user['followers_count']:,}")
    
    with info_col3:
        st.metric("Plan", user['subscription_tier'].title())
    
    st.markdown("---")
    
    # Analysis Section
    st.info("🔍 Analysis feature coming soon! Database is ready.")
    
    if st.button("🎯 Run Analysis (Coming Soon)", disabled=True):
        st.warning("Analysis engine will be built in Day 4-5")