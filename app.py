import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📅 Calendrier des Réservations", layout="wide")

st.title("🏨 Calendrier des Réservations")
st.markdown("Importez un fichier **CSV** avec les colonnes : `nom_client`, `date_arrivee`, `date_depart`, `plateforme`")

uploaded_file = st.file_uploader("📁 Importer le fichier CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, sep=";")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes suivantes : {', '.join(required_cols)}")
        else:
            # Conversion des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            st.success("✅ Fichier importé avec succès")
            st.dataframe(df)

            # Création du calendrier
            fig = px.timeline(
                df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_client",
                color="plateforme",
                title="Vue calendrier des séjours",
                labels={"nom_client": "Client", "plateforme": "Plateforme"}
            )

            fig.update_yaxes(autorange="reversed")  # Clients dans l'ordre
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")
else:
    st.info("📤 Veuillez importer un fichier CSV pour afficher les réservations.")
