import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

st.set_page_config(page_title="📅 Calendrier des Réservations", layout="wide")
st.title("📅 Calendrier Google-like des réservations")

# Importer fichier CSV
csv_file = st.file_uploader("📁 Importer un fichier CSV", type=["csv"])
if csv_file is not None:
    try:
        df = pd.read_csv(csv_file, sep=";")  # Si ton fichier utilise des ;
    except:
        df = pd.read_csv(csv_file)

    # Vérifier les colonnes
    required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme"}
    if not required_cols.issubset(df.columns):
        st.error(f"Le fichier doit contenir les colonnes : {required_cols}")
    else:
        # Convertir les dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"])
        df["date_depart"] = pd.to_datetime(df["date_depart"])

        # Créer les événements du calendrier
        events = []
        for _, row in df.iterrows():
            couleur = "#1E90FF" if row["plateforme"].lower() == "airbnb" else "#32CD32"
            events.append({
                "title": f"{row['nom_client']} ({row['plateforme']})",
                "start": row["date_arrivee"].strftime("%Y-%m-%d"),
                "end": (row["date_depart"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "color": couleur
            })

        # Options du calendrier
        options = {
            "initialView": "dayGridMonth",
            "locale": "fr",
            "height": 700
        }

        st.markdown("### 🗓️ Vue calendrier")
        calendar(events=events, options=options)

        st.markdown("### 📋 Données chargées")
        st.dataframe(df)
