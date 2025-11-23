import streamlit as st
from db.connection import init_db, test_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="LevelX",
    page_icon="📈",
    layout="wide"
)

st.title("📈 LevelX - X Growth Intelligence")
st.write("Development environment - Day 2")

# Test database connection
st.subheader("Database Connection Test")

if st.button("Test Database Connection"):
    with st.spinner("Connecting to database..."):
        if test_connection():
            st.success("✅ Database connection successful!")
        else:
            st.error("❌ Database connection failed. Check your .env file.")

if st.button("Initialize Database Tables"):
    with st.spinner("Creating tables..."):
        try:
            init_db()
            st.success("✅ Database tables created successfully!")
            st.info("Check your Supabase dashboard > Table Editor to see the tables.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")