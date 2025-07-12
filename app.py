import streamlit as st

st.set_page_config(page_title="Portail Extranet", layout="centered")

st.title("🌐 Portail Extranet Streamlit")
st.write("Bienvenue sur votre application extranet déployée avec Streamlit Cloud.")

nom = st.text_input("Quel est votre nom ?")
if nom:
    st.success(f"Bonjour, {nom} 👋 Bienvenue sur le portail.")

st.markdown("---")
st.caption("Développé avec ❤️ par [charleytrigano](https://github.com/charleytrigano)")
