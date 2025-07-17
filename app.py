import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import datetime
import requests
import os

st.set_page_config(layout="wide")

# ---- PARAMÈTRES SMS (à adapter selon tes clés Free Mobile) ----
FREE_USER_1 = "12026027"
FREE_API_KEY_1 = "MF7Qjs3C8KxKHz"
FREE_USER_2 = "12026027"
FREE_API_KEY_2 = "1Pat6vSRCLiSXl"
sms_log = []

def envoyer_sms(message):
    for user, key in [(FREE_USER_1, FREE_API_KEY_1), (FREE_USER_2, FREE_API_KEY_2)]:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={requests.utils.quote(message)}"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                sms_log.append(f"✅ SMS envoyé à l'utilisateur {user}")
            else:
                sms_log.append(f"❌ Échec de l'envoi pour {user} (code {r.status_code})")
        except Exception as e:
            sms_log.append(f"❌ Erreur pour {user} : {e}")

# ---- CHARGEMENT DU FICHIER XLSX ----
st.sidebar.title("📂 Importer les réservations")
xlsx_file = st.sidebar.file_uploader("Charger un fichier .xlsx", type=["xlsx"])

if xlsx_file:
    try:
        df = pd.read_excel(xlsx_file)
        required_columns = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_columns.issubset(set(df.columns.str.strip())):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_columns))}")
            st.stop()

        df.columns = df.columns.str.strip()
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "📅 Calendrier", "➕ Nouvelle réservation", "📨 Journal des SMS"])

        # ---- ONGLET RÉSERVATIONS ----
        if onglet == "📋 Réservations":
            st.title("📋 Tableau des Réservations")
            st.dataframe(df)

        # ---- ONGLET CALENDRIER ----
        elif onglet == "📅 Calendrier":
            st.title("📅 Vue Calendrier Mensuelle")

            df_events = []
            platform_colors = {
                "Airbnb": "rgb(255, 150, 150)",
                "Booking": "rgb(150, 200, 255)",
                "Autre": "rgb(200, 255, 200)"
            }

            for _, row in df.iterrows():
                if pd.notnull(row["date_arrivee"]) and pd.notnull(row["date_depart"]):
                    debut = row["date_arrivee"]
                    fin = row["date_depart"]
                    label = row["nom_client"]
                    couleur = platform_colors.get(str(row["plateforme"]), "gray")
                    df_events.append(dict(Task=label, Start=debut, Finish=fin, Resource=str(row["plateforme"])))

            if df_events:
                fig = ff.create_gantt(df_events, index_col="Resource", show_colorbar=True, group_tasks=True, title="Calendrier des réservations")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée valide pour le calendrier.")

        # ---- ONGLET NOUVELLE RÉSERVATION ----
        elif onglet == "➕ Nouvelle réservation":
            st.title("➕ Ajouter une Réservation")

            with st.form("formulaire"):
                nom_client = st.text_input("Nom du client")
                telephone = st.text_input("Téléphone (format international, ex : +33612345678)")
                plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
                date_arrivee = st.date_input("Date d'arrivée")
                date_depart = st.date_input("Date de départ")
                prix_brut = st.text_input("Prix brut")
                prix_net = st.text_input("Prix net")
                charges = st.text_input("Charges")
                pourcentage = st.text_input("%")
                submitted = st.form_submit_button("✅ Ajouter")

            if submitted:
                if nom_client and plateforme and telephone and date_arrivee and date_depart:
                    nouvelle_reservation = {
                        "nom_client": nom_client,
                        "date_arrivee": pd.to_datetime(date_arrivee),
                        "date_depart": pd.to_datetime(date_depart),
                        "plateforme": plateforme,
                        "telephone": telephone,
                        "prix_brut": prix_brut,
                        "prix_net": prix_net,
                        "charges": charges,
                        "%": pourcentage
                    }
                    df = pd.concat([df, pd.DataFrame([nouvelle_reservation])], ignore_index=True)
                    st.success("✅ Réservation ajoutée !")
                else:
                    st.error("❌ Merci de remplir tous les champs obligatoires.")

        # ---- ONGLET JOURNAL SMS ----
        elif onglet == "📨 Journal des SMS":
            st.title("📨 Journal des SMS envoyés")
            if sms_log:
                for ligne in sms_log:
                    st.write(ligne)
            else:
                st.info("Aucun SMS envoyé pour le moment.")

        # ---- ENVOI SMS AUTOMATIQUE POUR LES CLIENTS ARRIVANT DEMAIN ----
        demain = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
        clients_demain = df[df["date_arrivee"] == demain]

        for _, row in clients_demain.iterrows():
            message = (
                f"Bonjour {row['nom_client']},\n"
                "Nous sommes heureux de vous accueillir demain à Nice.\n"
                "Un emplacement de parking est à votre disposition.\n"
                "Merci d'indiquer votre heure approximative d'arrivée.\n"
                "Bon voyage et à demain !\n"
                "Annick & Charley"
            )
            envoyer_sms(message)

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")


