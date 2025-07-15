import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# 🎯 Identifiants Free Mobile client
FREE_USER_CLIENT = "12026027"
FREE_API_CLIENT = "MF7Qjs3C8KxKHz"

st.set_page_config(page_title="Extranet · Réservations", page_icon="📆", layout="centered")

st.title("📩 SMS Automatique 24h avant arrivée")
st.write("Importez un fichier .csv contenant les réservations à venir.")

csv_file = st.file_uploader("Importer un fichier CSV", type=["csv"])

if csv_file is not None:
    try:
        df = pd.read_csv(csv_file, sep=";")

        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.success("📋 Données chargées :")
            st.dataframe(df)

            # 🔍 Sélection des clients arrivant demain
            demain = datetime.now() + timedelta(days=1)
            demain_str = demain.strftime("%Y-%m-%d")
            df_demain = df[df["date_arrivee"].dt.strftime("%Y-%m-%d") == demain_str]

            st.subheader("📆 Clients arrivant demain :")
            st.dataframe(df_demain)

            if not df_demain.empty:
                st.subheader("📨 Envoi des SMS clients")

                for _, row in df_demain.iterrows():
                    message = (
                        f"Bonjour {row['nom_client']}, Nous sommes heureux de vous accueillir demain à Nice. "
                        f"Un emplacement de parking est à votre disposition sur place. "
                        f"Nous vous demandons de bien vouloir nous indiquer votre heure approximative d'arrivée afin que nous puissions nous rendre disponible. "
                        f"Dans l'attente nous vous disons bon voyage et à demain. Annick et Charley"
                    )

                    response = requests.get(
                        "https://smsapi.free-mobile.fr/sendmsg",
                        params={
                            "user": FREE_USER_CLIENT,
                            "pass": FREE_API_CLIENT,
                            "msg": message
                        }
                    )

                    if response.status_code == 200:
                        st.success(f"✅ SMS envoyé à {row['nom_client']}")
                    else:
                        st.error(f"❌ Erreur pour {row['nom_client']} - Code {response.status_code}")

            else:
                st.info("✅ Aucun client n'arrive demain.")

            # 🎨 Visualisation du calendrier
            st.subheader("📊 Calendrier des réservations")
            df_calendar = df.copy()
            df_calendar["nom_affiche"] = df_calendar["nom_client"] + " (" + df_calendar["plateforme"] + ")"

            fig = px.timeline(
                df_calendar,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_affiche",
                color="plateforme",
                title="Visualisation des séjours"
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : {e}")

st.markdown("---")
st.caption("Développé avec ❤️ par Annick & Charley · [charleytrigano](https://github.com/charleytrigano)")


