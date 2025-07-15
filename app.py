import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# 🎯 Identifiants Free Mobile
FREE_USER_1 = "12026027"
FREE_API_1 = "MF7Qjs3C8KxKHz"
TEL_ADMIN_1 = "+33617722379"

# Deuxième numéro de notification (admin)
FREE_USER_2 = "12026027"
FREE_API_2 = "1Pat6vSRCLiSXl"
TEL_ADMIN_2 = "+33611772793"

st.set_page_config(page_title="Extranet · Réservations", page_icon="📆", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")
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

            demain = datetime.now() + timedelta(days=1)
            demain_str = demain.strftime("%Y-%m-%d")
            df_demain = df[df["date_arrivee"].dt.strftime("%Y-%m-%d") == demain_str]

            st.subheader("📆 Clients arrivant demain :")
            st.dataframe(df_demain)

            if not df_demain.empty:
                st.subheader("📨 Envoi des SMS...")

                for _, row in df_demain.iterrows():
                    msg = (
                        f"Reservation : {row['plateforme']}\n"
                        f"Client       : {row['nom_client']}\n"
                        f"Arrive le    : {row['date_arrivee'].strftime('%d/%m/%Y')}\n"
                        f"Depart le    : {row['date_depart'].strftime('%d/%m/%Y')}"
                    )

                    # Envoi au client (FREE_USER_1)
                    res1 = requests.get(
                        "https://smsapi.free-mobile.fr/sendmsg",
                        params={"user": FREE_USER_1, "pass": FREE_API_1, "msg": msg}
                    )

                    # Envoi au second numéro (FREE_USER_2)
                    res2 = requests.get(
                        "https://smsapi.free-mobile.fr/sendmsg",
                        params={"user": FREE_USER_2, "pass": FREE_API_2, "msg": msg}
                    )

                    # Affichage
                    if res1.status_code == 200 and res2.status_code == 200:
                        st.success(f"✅ SMS envoyés pour {row['nom_client']}")
                    else:
                        st.error(f"❌ Erreur pour {row['nom_client']} | Codes : {res1.status_code}, {res2.status_code}")
            else:
                st.info("✅ Aucun client n'arrive demain.")

            # 🎨 Visualisation calendrier
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
st.caption("Développé avec ❤️ par [charleytrigano](https://github.com/charleytrigano)")

