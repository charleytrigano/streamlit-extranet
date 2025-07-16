import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="📅 Calendrier des Réservations", layout="wide")

st.title("📅 Calendrier des Réservations Clients")

# --- Étape 1 : Import du fichier Excel ---
fichier = st.file_uploader("Importez votre fichier .xlsx", type=["xlsx"])

if fichier is not None:
    try:
        df = pd.read_excel(fichier)

        # Vérification des colonnes requises
        colonnes_attendues = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not colonnes_attendues.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(colonnes_attendues)}")
        else:
            # Nettoyage des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            # Affichage du tableau
            st.success("✅ Fichier bien importé !")
            st.dataframe(df)

            # --- Étape 2 : Préparer les données pour Gantt ---
            df["Séjour"] = df["nom_client"] + " (" + df["plateforme"] + ")"

            fig = px.timeline(
                df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="Séjour",
                color="plateforme",
                hover_data=["prix_brut", "prix_net", "charges", "%", "telephone"],
                title="Vue calendrier mensuel des séjours",
            )

            fig.update_yaxes(autorange="reversed")  # Pour afficher les dates du haut vers le bas
            fig.update_layout(height=600)

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
else:
    st.info("📂 Veuillez importer un fichier Excel pour afficher le calendrier.")




