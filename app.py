import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import os

st.set_page_config(page_title="Extranet Streamlit", layout="wide")

# Navigation
page = st.sidebar.radio("Navigation", ["📋 Réservations", "📅 Planning"])

st.title("🏨 Portail Extranet Streamlit")

# Téléversement unique du fichier
uploaded_file = st.sidebar.file_uploader("📂 Importer le fichier Excel", type=["xlsx"], key="main_upload")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        required_cols = {
            "nom_client", "date_arrivee", "date_depart", "plateforme",
            "telephone", "prix_brut", "prix_net", "charges", "%"
        }

        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_cols))}")
        else:
            # Nettoyage des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
            df["nom_client"] = df["nom_client"].astype(str)
            df["plateforme"] = df["plateforme"].astype(str)

            if page == "📋 Réservations":
                st.subheader("📩 Envoi automatique de SMS aux clients")
                st.success("✅ Données chargées avec succès !")
                st.dataframe(df)

                # SMS Free API config
                FREE_API_USER_1 = "12026027"
                FREE_API_KEY_1 = "1Pat6vSRCLiSXl"
                NUM_1 = "+33617722379"

                FREE_API_USER_2 = "12026027"
                FREE_API_KEY_2 = "MF7Qjs3C8KxKHz"
                NUM_2 = "+33611772793"

                # Envoi des SMS aux clients arrivant demain
                demain = (datetime.now() + timedelta(days=1)).date()
                df_demain = df[df["date_arrivee"].dt.date == demain]

                if not df_demain.empty:
                    st.subheader("📤 SMS envoyés (Free Mobile)")
                    for _, row in df_demain.iterrows():
                        nom = row["nom_client"]
                        msg = (
                            f"Bonjour {nom},\n"
                            "Nous sommes heureux de vous accueillir demain à Nice.\n"
                            "Un emplacement de parking est à votre disposition sur place.\n"
                            "Merci de nous indiquer votre heure d'arrivée.\n"
                            "Bon voyage et à demain !\n"
                            "Annick & Charley"
                        )
                        # Envoi à NUM_1
                        url1 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_API_USER_1}&pass={FREE_API_KEY_1}&msg={requests.utils.quote(msg)}"
                        r1 = requests.get(url1)
                        if r1.status_code == 200:
                            st.success(f"✅ SMS envoyé à {nom} ({NUM_1})")
                        else:
                            st.error(f"❌ Erreur pour {NUM_1}")

                        # Envoi à NUM_2
                        url2 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_API_USER_2}&pass={FREE_API_KEY_2}&msg={requests.utils.quote(msg)}"
                        r2 = requests.get(url2)
                        if r2.status_code == 200:
                            st.success(f"✅ SMS envoyé à {nom} ({NUM_2})")
                        else:
                            st.error(f"❌ Erreur pour {NUM_2}")
                else:
                    st.info("Aucune réservation prévue pour demain.")

            elif page == "📅 Planning":
                st.subheader("📆 Calendrier des réservations")

                # Créer les tâches Gantt
                tasks = []
                for _, row in df.iterrows():
                    client = row["nom_client"]
                    start = row["date_arrivee"]
                    end = row["date_depart"]
                    plate = row["plateforme"]

                    tasks.append(dict(
                        Task=plate,
                        Start=str(start.date()),
                        Finish=str(end.date()),
                        Resource=client
                    ))

                # Couleurs RGB
                couleur_plateforme = {
                    "Airbnb": "rgb(255,90,95)",
                    "Booking": "rgb(0,53,128)",
                    "Abritel": "rgb(123,66,246)",
                    "Autre": "rgb(0,191,255)"
                }

                try:
                    fig = ff.create_gantt(
                        tasks,
                        index_col="Task",
                        show_colorbar=True,
                        group_tasks=True,
                        showgrid_x=True,
                        showgrid_y=True,
                        bar_width=0.3,
                        height=600,
                        colors=couleur_plateforme
                    )
                    fig.update_layout(
                        title="📅 Planning mensuel",
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur lors de la génération du calendrier : {e}")

    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
else:
    st.info("📤 Veuillez importer un fichier .xlsx dans la barre latérale.")


