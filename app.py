import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import requests
import os
from dotenv import load_dotenv

# 🔐 Charger les variables d’environnement
load_dotenv()
FREE_USER = os.getenv("FREE_USER")
FREE_API = os.getenv("FREE_API")
DESTINATAIRE_SMS = "+33617722379"  # Numéro autorisé (Free)

st.set_page_config(page_title="📅 Extranet Réservations", layout="wide")
st.title("🏨 Récupération des réservations & 📩 SMS automatiques")

st.markdown("Importez un fichier `.csv` avec les colonnes : `nom_client`, `date_arrivee`, `date_depart`, `plateforme`, `telephone`")

csv_file = st.file_uploader("📁 Importer le fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        df = pd.read_csv(csv_file, sep=";")

        # Dates au bon format
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        # Vérification des colonnes
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"Le fichier doit contenir les colonnes suivantes : {', '.join(required_cols)}")
        else:
            st.success("✅ Données importées")
            st.dataframe(df)

            # 🟦 Calendrier visuel
            st.subheader("📅 Vue calendrier des séjours")
            df_events = df.copy()
            df_events["label"] = df_events["nom_client"] + " (" + df_events["plateforme"] + ")"

            fig = px.timeline(df_events, x_start="date_arrivee", x_end="date_depart", y="label", color="plateforme")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # 🔔 Filtrage des clients arrivant demain
            demain = datetime.date.today() + datetime.timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain]

            if not df_demain.empty:
                st.warning(f"📨 {len(df_demain)} client(s) arrivent demain ({demain})")

                if st.button("📤 Envoyer les SMS Free Mobile"):
                    for _, row in df_demain.iterrows():
                        message = (f"Reservation : {row['plateforme']}\n"
    f"Client       : {row['nom_client']}\n"
    f"Arrive le    : {row['date_arrivee'].strftime('%d/%m/%Y')}\n"
    f"Depart le    : {row['date_depart'].strftime('%d/%m/%Y')}"
)

                        response = requests.get(
                            "https://smsapi.free-mobile.fr/sendmsg",
                            params={
                                "user": FREE_USER,
                                "pass": FREE_API,
                                "msg": message
                            }
                        )
                        if response.status_code == 200:
                            st.success(f"✅ SMS envoyé : {message}")
                        else:
                            st.error(f"❌ Erreur d'envoi pour {row['nom_client']}. Code HTTP : {response.status_code}")
            else:
                st.info("📭 Aucun client prévu demain.")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
