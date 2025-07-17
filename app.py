import streamlit as st
import pandas as pd
import requests
import calendar
import plotly.figure_factory as ff
from datetime import datetime, timedelta

st.set_page_config(page_title="Portail Extranet", layout="wide")

st.title("🏨 Portail Extranet")

# --- Sidebar navigation ---
page = st.sidebar.selectbox("📂 Naviguer entre les pages", ["📋 Réservations", "📩 SMS", "📅 Calendrier"])

# --- Upload fichier Excel ---
uploaded_file = st.file_uploader("Importer le fichier .xlsx des réservations", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
            st.stop()

        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")
        st.stop()

    # --- Page Réservations ---
    if page == "📋 Réservations":
        st.subheader("📋 Réservations à venir")
        st.dataframe(df.sort_values("date_arrivee"))

    # --- Page SMS ---
    elif page == "📩 SMS":
        st.subheader("📩 Envoi automatique de SMS aux clients")
        st.info("Un message est envoyé aux clients 24h avant leur arrivée.")

        # Filtrer les arrivées de demain
        demain = (datetime.today() + timedelta(days=1)).date()
        df_demain = df[df["date_arrivee"].dt.date == demain]

        if df_demain.empty:
            st.success("Aucun client attendu demain.")
        else:
            sms_log = []
            for _, row in df_demain.iterrows():
                nom = row["nom_client"]
                date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                date_depart = row["date_depart"].strftime("%d/%m/%Y")
                plateforme = row["plateforme"]
                tel = row["telephone"]

                message = (
                    f"Bonjour {nom},\n\nNous sommes heureux de vous accueillir demain à Nice.\n"
                    f"📅 Réservation via {plateforme}\n"
                    f"🛬 Arrivée : {date_arrivee}\n"
                    f"🛫 Départ : {date_depart}\n"
                    f"🚗 Un emplacement de parking est à votre disposition.\n"
                    f"Merci de nous indiquer votre heure approximative d'arrivée.\n\n"
                    f"Bon voyage et à demain !\nAnnick et Charley"
                )

                # Config SMS API Free (exemples – à adapter)
                free_users = [
                    {"user": "12026027", "api": "1Pat6vSRCLiSXl", "to": "+33611772793"},
                    {"user": "12026027", "api": "MF7Qjs3C8KxKHz", "to": "+33617722379"}
                ]

                for free in free_users:
                    params = {
                        "user": free["user"],
                        "pass": free["api"],
                        "msg": message
                    }
                    try:
                        r = requests.get("https://smsapi.free-mobile.fr/sendmsg", params=params)
                        if r.status_code == 200:
                            sms_log.append(f"✅ SMS envoyé à {free['to']} pour {nom}")
                        else:
                            sms_log.append(f"❌ Erreur pour {free['to']} - statut {r.status_code}")
                    except Exception as e:
                        sms_log.append(f"❌ Exception pour {free['to']} : {e}")

            st.write("### Résultat des envois :")
            for ligne in sms_log:
                st.write(ligne)

    # --- Page Calendrier ---
    elif page == "📅 Calendrier":
        st.subheader("📅 Calendrier des réservations")

        couleur_plateforme = {
            "Booking": "blue",
            "Airbnb": "green",
            "Autre": "orange"
        }

        df["plateforme"] = df["plateforme"].fillna("Autre")

        tasks = []
        for _, row in df.iterrows():
            task = {
                "Task": row["nom_client"],
                "Start": row["date_arrivee"],
                "Finish": row["date_depart"],
                "Resource": row["plateforme"]
            }
            tasks.append(task)

        if tasks:
            fig = ff.create_gantt(tasks, index_col="Resource", colors=couleur_plateforme,
                                  show_colorbar=True, group_tasks=True, title="Planning des séjours",
                                  showgrid_x=True, showgrid_y=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune réservation à afficher.")

else:
    st.warning("📎 Veuillez importer un fichier .xlsx avec les colonnes nécessaires.")


