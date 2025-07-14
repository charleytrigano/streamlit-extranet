import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📅 Calendrier Réservations", layout="centered")
st.title("🏨 Visualisation des réservations 📅")

# Upload du fichier CSV
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lecture du CSV avec ; comme séparateur
        df = pd.read_csv(csv_file, sep=";", on_bad_lines='skip', engine='python')
        
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.success("✅ Fichier chargé avec succès")
            st.dataframe(df)

            # Convertir les dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors='coerce')
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors='coerce')

            # Supprimer les lignes avec dates invalides
            df.dropna(subset=["date_arrivee", "date_depart"], inplace=True)

            # Créer une timeline
            fig = px.timeline(
                df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_client",
                color="plateforme",
                title="🗓️ Réservations par client",
            )
            fig.update_yaxes(autorange="reversed")  # pour inverser l'ordre des noms
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
else:
    st.info("📂 Importez un fichier .csv avec les colonnes : nom_client, date_arrivee, date_depart, plateforme")
