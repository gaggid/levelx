import streamlit as st

st.set_page_config(
    page_title="LevelX",
    page_icon="📈",
    layout="wide"
)

st.title("📈 LevelX - X Growth Intelligence")
st.write("Development environment is working!")

if st.button("Test Button"):
    st.success("✅ Streamlit is working correctly!")