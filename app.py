import streamlit as st
from auth.twitter_oauth import TwitterOAuth
from auth.session_manager import SessionManager
from ui.pages import home, dashboard
from db.connection import init_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="LevelX - X Growth Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database on startup
try:
    init_db()
except:
    pass

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)


def handle_oauth_callback():
    """Handle OAuth callback from X"""
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        code = query_params['code']
        state = query_params['state']
        
        logger.info(f"Handling OAuth callback with state: {state[:10]}...")
        
        # Clear query params immediately to avoid Streamlit routing warning
        st.query_params.clear()
        
        # Exchange code for token (state verification happens inside)
        oauth = TwitterOAuth()
        
        with st.spinner("Completing login..."):
            token_data = oauth.get_access_token(code, state)
            
            if not token_data:
                st.error("❌ Failed to complete login. Please try again.")
                if st.button("← Back to Home"):
                    st.rerun()
                return
            
            # Get user info
            user_data = oauth.get_user_info(token_data['access_token'])
            
            if not user_data:
                st.error("❌ Failed to get your X profile. Please try again.")
                if st.button("← Back to Home"):
                    st.rerun()
                return
            
            # Create/update user in database
            user = SessionManager.create_user(
                user_data,
                token_data['access_token'],
                token_data.get('refresh_token')
            )
            
            if user:
                # Set session
                SessionManager.set_user_session(user, user_data)
                st.success(f"✅ Welcome, @{user.x_handle}!")
                st.rerun()
            else:
                st.error("❌ Failed to create user. Please try again.")
                if st.button("← Back to Home"):
                    st.rerun()


def main():
    # Check for OAuth callback
    if 'code' in st.query_params:
        handle_oauth_callback()
        return
    
    # Route based on authentication
    if SessionManager.is_authenticated():
        dashboard.render()
    else:
        home.render()


if __name__ == "__main__":
    main()