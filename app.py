import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# Identifiants Free Mobile (ne pas partager publiquement)
FREE_USER = "12026027"
FREE_API = "MF7Qjs3C8KxKHz"

st.set_page_config(page_title="Extranet · Réservations", page_icon="📆", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")
st.write("Importez un fichier .csv contenant les réservations à venir.")

# Upload CSV
csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        # Lecture du fichier CSV avec séparateur ;
        df = pd.read_csv(csv_file, sep=";")

        # Nettoyage des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.success("📋 Données chargées :")
            st.dataframe(df)

            # Filtrer les clients qui arrivent demain
            demain = datetime.now() + timedelta(days=1)
            demain_str = demain.strftime("%Y-%m-%d")
            df_demain = df[df["date_arrivee"].dt.strftime("%Y-%m-%d") == demain_str]

            st.subheader("📆 Clients arrivant demain :")
            st.dataframe(df_demain)

            if not df_demain.empty:
                st.subheader("📨 Envoi des SMS en cours...")

                for _, row in df_demain.iterrows():
                    message = (
                        f"Reservation : {row['plateforme']}\n"
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
                        st.success(f"✅ SMS envoyé :\n{message}")
                    else:
                        st.error(f"❌ Erreur d'envoi pour {row['nom_client']}. Code HTTP : {response.status_code}")
            else:
                st.info("✅ Aucun client n'arrive demain.")

            # Visualisation calendrier
            st.subheader("📊 Visualisation des réservations")
            df_calendar = df.copy()
            df_calendar["nom_affiche"] = df_calendar["nom_client"] + " (" + df_calendar["plateforme"] + ")"

            fig = px.timeline(
                df_calendar,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_affiche",
                color="plateforme",
                title="Calendrier des réservations"
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : {e}")

st.markdown("---")
st.caption("Développé avec ❤️ par [charleytrigano](https://github.com/charleytrigano)")
