import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import calendar

st.set_page_config(page_title="Portail Extranet", layout="wide")

# --------------------- CONFIGURATION SMS -----------------------
FREE_API_KEY_1 = "MF7Qjs3C8KxKHz"
FREE_USER_1 = "12026027"

FREE_API_KEY_2 = "1Pat6vSRCLiSXl"
FREE_USER_2 = "12026027"

# --------------------- TITRE -----------------------
st.title("🏨 Portail Extranet - Réservations")

# --------------------- IMPORT FICHIER -----------------------
st.subheader("📁 Importer un fichier .xlsx des réservations")
uploaded_file = st.file_uploader("Importer un fichier Excel", type=["xlsx"])

df = None
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Nettoyage et validation
        df.columns = df.columns.str.strip()
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_cols))}")
            df = None
        else:
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
            st.success("✅ Fichier importé avec succès")
            st.dataframe(df)
    except Exception as e:
        st.error(f"Erreur lors de l'importation : {e}")

# --------------------- ENVOI DE SMS -----------------------
if df is not None:
    st.subheader("📩 Envoi automatique de SMS (24h avant arrivée)")
    aujourd_hui = datetime.today().date()
    demain = aujourd_hui + timedelta(days=1)

    df_sms = df[df["date_arrivee"].dt.date == demain]

    if st.button("📲 Envoyer les SMS aux clients de demain"):
        if df_sms.empty:
            st.info("Aucun client attendu demain.")
        else:
            for _, row in df_sms.iterrows():
                nom = row["nom_client"]
                tel = row["telephone"]
                arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                depart = row["date_depart"].strftime("%d/%m/%Y")
                plateforme = row["plateforme"]

                message = (
                    f"Reservation : {plateforme}\n"
                    f"Client       : {nom}\n"
                    f"Arrivee le   : {arrivee}\n"
                    f"Depart le    : {depart}\n\n"
                    f"Bonjour {nom}, nous sommes heureux de vous accueillir demain à Nice. "
                    f"Un emplacement de parking est à votre disposition sur place. "
                    f"Merci de nous indiquer votre heure d'arrivée approximative.\n"
                    f"Bon voyage et à demain !\n"
                    f"Annick & Charley"
                )

                for user, key in [(FREE_USER_1, FREE_API_KEY_1), (FREE_USER_2, FREE_API_KEY_2)]:
                    response = requests.get(
                        "https://smsapi.free-mobile.fr/sendmsg",
                        params={"user": user, "pass": key, "msg": message},
                    )
                    if response.status_code == 200:
                        st.success(f"✅ SMS envoyé à {tel}")
                    else:
                        st.error(f"❌ Erreur d'envoi à {tel} — Code : {response.status_code}")

# --------------------- CALENDRIER -----------------------
if df is not None:
    st.subheader("🗓️ Calendrier mensuel des réservations")

    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=datetime.today().month - 1)
    annee = st.number_input("Année", value=datetime.today().year, step=1)

    # Génération du calendrier
    nb_jours = calendar.monthrange(annee, list(calendar.month_name).index(mois))[1]
    jours = [datetime(annee, list(calendar.month_name).index(mois), j).date() for j in range(1, nb_jours + 1)]

    # Préparation des données
    data = {jour: [] for jour in jours}
    couleurs = {
        "Booking": "#3498db",
        "Airbnb": "#e67e22",
        "Autre": "#95a5a6"
    }

    for _, row in df.iterrows():
        nom = row["nom_client"]
        plate = row["plateforme"]
        arrivee = row["date_arrivee"]
        depart = row["date_depart"]

        if pd.isna(arrivee) or pd.isna(depart):
            continue

        arrivee = arrivee.date()
        depart = depart.date()
        color = couleurs.get(plate, couleurs["Autre"])

        try:
            jours_sejour = pd.date_range(arrivee, depart - timedelta(days=1)).date
            for jour in jours:
                if jour in jours_sejour:
                    data[jour].append((nom, plate, color))
        except Exception as e:
            st.warning(f"Erreur de date pour {nom}")

    # Affichage
    html_calendar = "<table style='width:100%; border-collapse:collapse;'>"
    html_calendar += "<tr>" + "".join([f"<th>{j.strftime('%a %d')}</th>" for j in jours]) + "</tr>"
    html_calendar += "<tr>"

    for jour in jours:
        html_calendar += "<td style='vertical-align:top; border:1px solid #ccc; padding:5px;'>"
        for nom, plate, color in data[jour]:
            html_calendar += f"<div style='background:{color}; padding:2px; margin-bottom:2px; color:white; font-size:12px;'>{nom}</div>"
        html_calendar += "</td>"
    html_calendar += "</tr></table>"

    st.markdown(html_calendar, unsafe_allow_html=True)


