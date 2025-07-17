import streamlit as st
import pandas as pd
import datetime
import plotly.figure_factory as ff
import requests

st.set_page_config(page_title="Extranet Streamlit", layout="wide")

# Onglets de navigation
page = st.sidebar.radio("📁 Navigation", ["📋 Tableau des réservations", "📅 Planning", "📩 SMS automatique"])

st.title("🏨 Portail Extranet Streamlit")

# ----------- Fichier requis -----------
uploaded_file = st.sidebar.file_uploader("📤 Importer le fichier Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Nettoyage des colonnes
        df.columns = df.columns.str.strip()

        # Conversion des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        # Ajouter un jour à la date de départ pour l'affichage
        df["date_depart"] = df["date_depart"] + pd.Timedelta(days=1)

        # Colonnes attendues
        colonnes_requises = {
            "nom_client", "date_arrivee", "date_depart",
            "plateforme", "telephone",
            "prix_brut", "prix_net", "charges", "%"
        }

        if not colonnes_requises.issubset(set(df.columns)):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(colonnes_requises)}")
        else:
            st.success("✅ Fichier importé avec succès !")

            # ---------------------- PAGE 1 : TABLEAU ----------------------
            if page == "📋 Tableau des réservations":
                st.subheader("📋 Liste des réservations")
                st.dataframe(df)

            # ---------------------- PAGE 2 : PLANNING ----------------------
            elif page == "📅 Planning":
                st.subheader("📅 Calendrier des réservations")
                couleur_plateforme = {
                    "Airbnb": "#FF5A5F",
                    "Booking": "#003580",
                    "Abritel": "#7B42F6",
                    "Autre": "#00BFFF"
                }

                # Création du Gantt Chart
                tasks = []
                for _, row in df.iterrows():
                    task = {
                        "Task": row["nom_client"],
                        "Start": row["date_arrivee"],
                        "Finish": row["date_depart"],
                        "Resource": row["plateforme"]
                    }
                    tasks.append(task)

                fig = ff.create_gantt(
                    tasks,
                    index_col="Resource",
                    colors=couleur_plateforme,
                    show_colorbar=True,
                    group_tasks=True,
                    showgrid_x=True,
                    showgrid_y=True,
                    title="📆 Planning mensuel des séjours",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

            # ---------------------- PAGE 3 : ENVOI SMS ----------------------
            elif page == "📩 SMS automatique":
                st.subheader("📩 Envoi automatique de SMS la veille de l'arrivée")

                # Calcul des clients à prévenir
                demain = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
                df["date_arrivee_date"] = df["date_arrivee"].dt.date
                df_demain = df[df["date_arrivee_date"] == demain]

                if df_demain.empty:
                    st.info("Aucun client prévu demain.")
                else:
                    st.write(f"📨 Clients à prévenir pour le {demain.strftime('%d/%m/%Y')} :")
                    st.dataframe(df_demain[["nom_client", "date_arrivee", "date_depart", "telephone", "plateforme"]])

                    # Détails Free API
                    free_users = [
                        {
                            "user": "12026027",
                            "key": "1Pat6vSRCLiSXl",
                            "telephone": "+33617722379"
                        },
                        {
                            "user": "12026027",
                            "key": "1Pat6vSRCLiSXl",
                            "telephone": "+33611772793"
                        }
                    ]

                    # Message personnalisé pour chaque client
                    for _, row in df_demain.iterrows():
                        message = (
                            f"Bonjour {row['nom_client']},\n"
                            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                            f"Un emplacement de parking est à votre disposition sur place.\n"
                            f"Merci de nous indiquer votre heure d'arrivée pour que nous puissions nous rendre disponibles.\n"
                            f"Bon voyage et à demain !\n"
                            f"Annick & Charley"
                        )

                        for user in free_users:
                            url = f"https://smsapi.free-mobile.fr/sendmsg?user={user['user']}&pass={user['key']}&msg={requests.utils.quote(message)}"
                            response = requests.get(url)

                            if response.status_code == 200:
                                st.success(f"✅ SMS envoyé à {user['telephone']} pour {row['nom_client']}")
                            else:
                                st.error(f"❌ Erreur pour {user['telephone']} ({row['nom_client']}) - code {response.status_code}")

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier : {e}")
else:
    st.info("📂 Veuillez importer un fichier Excel (.xlsx) contenant les réservations.")
