import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import random

st.set_page_config(page_title="Extranet Streamlit", layout="wide")

# Navigation
page = st.sidebar.radio("Navigation", ["📩 Réservations", "📅 Planning"])

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
            # Nettoyage des colonnes
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
            df["nom_client"] = df["nom_client"].astype(str)
            df["plateforme"] = df["plateforme"].astype(str).str.strip()

            if page == "📩 Réservations":
                st.subheader("📤 Envoi automatique de SMS (Free Mobile)")
                st.dataframe(df)

                # SMS Free API config
                FREE_API_USER_1 = "12026027"
                FREE_API_KEY_1 = "1Pat6vSRCLiSXl"
                NUM_1 = "+33617722379"

                FREE_API_USER_2 = "12026027"
                FREE_API_KEY_2 = "MF7Qjs3C8KxKHz"
                NUM_2 = "+33611772793"

                # Envoi des SMS pour les arrivées de demain
                demain = (datetime.now() + timedelta(days=1)).date()
                df_demain = df[df["date_arrivee"].dt.date == demain]

                if not df_demain.empty:
                    for _, row in df_demain.iterrows():
                        nom = row["nom_client"]
                        plateforme = row["plateforme"]
                        date_dep = row["date_depart"].strftime("%d/%m/%Y")

                        message = (
                            f"Bonjour {nom},\n"
                            f"Nous sommes heureux de vous accueillir demain à Nice via {plateforme}.\n"
                            f"Un parking est à votre disposition sur place.\n"
                            f"Merci de nous indiquer votre heure d'arrivée.\n"
                            f"Bon voyage et à demain !\n"
                            f"Annick & Charley"
                        )

                        url1 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_API_USER_1}&pass={FREE_API_KEY_1}&msg={requests.utils.quote(message)}"
                        url2 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_API_USER_2}&pass={FREE_API_KEY_2}&msg={requests.utils.quote(message)}"

                        r1 = requests.get(url1)
                        r2 = requests.get(url2)

                        if r1.status_code == 200:
                            st.success(f"✅ SMS envoyé à {nom} ({NUM_1})")
                        else:
                            st.error(f"❌ Erreur SMS vers {NUM_1}")

                        if r2.status_code == 200:
                            st.success(f"✅ SMS envoyé à {nom} ({NUM_2})")
                        else:
                            st.error(f"❌ Erreur SMS vers {NUM_2}")
                else:
                    st.info("Aucune réservation prévue pour demain.")

            elif page == "📅 Planning":
                st.subheader("📅 Calendrier des réservations (Gantt)")

                # Tâches pour Gantt
                tasks = []
                unique_platforms = df["plateforme"].unique()

                # Générer une couleur aléatoire par plateforme si non définie
                plateforme_colors = {}
                base_colors = {
                    "Airbnb": "rgb(255,90,95)",
                    "Booking": "rgb(0,53,128)",
                    "Abritel": "rgb(123,66,246)"
                }

                for plat in unique_platforms:
                    if plat in base_colors:
                        plateforme_colors[plat] = base_colors[plat]
                    else:
                        r = random.randint(0, 255)
                        g = random.randint(0, 255)
                        b = random.randint(0, 255)
                        plateforme_colors[plat] = f"rgb({r},{g},{b})"

                for _, row in df.iterrows():
                    tasks.append(dict(
                        Task=row["plateforme"],
                        Start=str(row["date_arrivee"].date()),
                        Finish=str(row["date_depart"].date()),
                        Resource=row["nom_client"]
                    ))

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
                        colors=plateforme_colors
                    )
                    fig.update_layout(title="📆 Planning des réservations", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur lors de la génération du calendrier : {e}")

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")
else:
    st.info("📤 Veuillez importer un fichier .xlsx à gauche.")


