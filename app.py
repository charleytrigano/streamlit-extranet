import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import requests

st.set_page_config(layout="wide", page_title="Portail Extranet Streamlit")

st.title("🏨 Portail Extranet - Multi-services")

# Onglets
onglet = st.sidebar.radio("Navigation", ["📋 Réservations & SMS", "📆 Calendrier mensuel"])

# Lecture du fichier
if "df" not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # Nettoyage
        df.columns = df.columns.str.strip()
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                         "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            st.session_state.df = df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")

# Onglet 1 : Réservations et SMS
if onglet == "📋 Réservations & SMS" and st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📄 Réservations à venir")
    st.dataframe(df)

    # Envoi SMS aux clients arrivant demain
    demain = (datetime.today() + timedelta(days=1)).date()
    df_demain = df[df["date_arrivee"].dt.date == demain]

    if not df_demain.empty:
        st.subheader("📩 Envoi automatique de SMS pour demain")

        for i, row in df_demain.iterrows():
            nom = row["nom_client"]
            date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
            date_depart = row["date_depart"].strftime("%d/%m/%Y")
            plateforme = row["plateforme"]
            tel = str(row["telephone"])
            if tel.startswith("0"):
                tel = "+33" + tel[1:]
            elif tel.startswith("33"):
                tel = "+" + tel
            elif not tel.startswith("+"):
                tel = "+33" + tel

            message = f"Bonjour {nom},\n"
            message += "Nous sommes heureux de vous accueillir demain à Nice.\n"
            message += "Un emplacement de parking est à votre disposition.\n"
            message += "Merci de nous indiquer votre heure d'arrivée.\n"
            message += "Bon voyage et à demain !\nAnnick & Charley"

            try:
                user_id = "12026027"  # Remplace si besoin
                api_key = "1Pat6vSRCLiSXl"
                url = f"https://smsapi.free-mobile.fr/sendmsg?user={user_id}&pass={api_key}&msg={requests.utils.quote(message)}&to={tel}"
                response = requests.get(url)
                if response.status_code == 200:
                    st.success(f"✅ SMS envoyé à {nom} ({tel})")
                else:
                    st.error(f"❌ Échec de l'envoi à {tel}")
            except Exception as e:
                st.error(f"❌ Erreur pour {tel} : {e}")

# Onglet 2 : Calendrier mensuel
if onglet == "📆 Calendrier mensuel" and st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📅 Calendrier mensuel des réservations")

    # Choix du mois
    mois_actuel = st.session_state.get("mois_actuel", datetime.today().month)
    annee_actuelle = st.session_state.get("annee_actuelle", datetime.today().year)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Mois précédent"):
            if mois_actuel == 1:
                mois_actuel = 12
                annee_actuelle -= 1
            else:
                mois_actuel -= 1
    with col3:
        if st.button("➡️ Mois suivant"):
            if mois_actuel == 12:
                mois_actuel = 1
                annee_actuelle += 1
            else:
                mois_actuel += 1

    st.session_state.mois_actuel = mois_actuel
    st.session_state.annee_actuelle = annee_actuelle

    # Créer le calendrier
    cal = calendar.Calendar(firstweekday=0)
    jours = list(cal.itermonthdates(annee_actuelle, mois_actuel))
    data = {jour: [] for jour in jours}

    couleurs = {
        "Booking": "#f39c12",
        "Airbnb": "#e74c3c",
        "Autre": "#3498db"
    }

    for _, row in df.iterrows():
        nom = row["nom_client"]
        plate = row["plateforme"]
        arrivee = row["date_arrivee"].date()
        depart = row["date_depart"].date()
        color = couleurs.get(plate, "#95a5a6")
        jours_sejour = pd.date_range(arrivee, depart - timedelta(days=1)).date

        for jour in jours:
            if jour in jours_sejour:
                data[jour].append((nom, plate, color))

    # Affichage HTML
    semaine_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    html = f"<h4>{calendar.month_name[mois_actuel]} {annee_actuelle}</h4>"
    html += "<table style='width:100%; border-collapse:collapse;'>"
    html += "<tr>" + "".join(f"<th style='border:1px solid #ccc; padding:5px'>{j}</th>" for j in semaine_labels) + "</tr>"

    semaine = []
    for jour in jours:
        if jour.month != mois_actuel:
            semaine.append("<td style='background:#eee; padding:8px'></td>")
        else:
            contenu = f"<div style='font-size:10px;'><strong>{jour.day}</strong><br>"
            for nom, plate, color in data[jour]:
                contenu += f"<div style='background:{color}; color:white; padding:2px; margin:1px;'>{nom}</div>"
            contenu += "</div>"
            semaine.append(f"<td style='border:1px solid #ccc; vertical-align:top'>{contenu}</td>")

        if len(semaine) == 7:
            html += "<tr>" + "".join(semaine) + "</tr>"
            semaine = []

    if semaine:
        while len(semaine) < 7:
            semaine.append("<td></td>")
        html += "<tr>" + "".join(semaine) + "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Développé avec ❤️ par [charleytrigano](https://github.com/charleytrigano)")


