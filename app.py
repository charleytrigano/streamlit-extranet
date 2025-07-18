import streamlit as st
import pandas as pd
import datetime
import calendar
import requests
from io import BytesIO

# Configuration Streamlit
st.set_page_config(page_title="Portail Extranet", layout="wide")

# Constantes
FREE_USER_1 = "12026027"
FREE_API_KEY_1 = "MF7Qjs3C8KxKHz"
FREE_USER_2 = "12026027"
FREE_API_KEY_2 = "1Pat6vSRCLiSXl"
NUMERO_ADMIN_1 = "+33617722379"
NUMERO_ADMIN_2 = "+33611772793"

PLATFORM_COLORS = {
    "Airbnb": "#FF5A5F",
    "Booking": "#003580",
    "Autre": "#FFA500"
}

# Fonction : Envoi de SMS via Free Mobile
def send_sms_free(user, key, msg):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={msg}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        return False

# Fonction : Générer le calendrier mensuel visuel
def render_calendar(df, year, month):
    cal = calendar.Calendar()
    month_days = cal.itermonthdates(year, month)
    weeks = []
    for week in calendar.monthcalendar(year, month):
        weeks.append(week)

    plateforme_colors = PLATFORM_COLORS
    data_by_date = {}

    for _, row in df.iterrows():
        start = row["date_arrivee"].date()
        end = row["date_depart"].date()
        for single_date in pd.date_range(start, end - datetime.timedelta(days=1)):
            data_by_date.setdefault(single_date.date(), []).append((row["nom_client"], row["plateforme"]))

    # Affichage du calendrier
    st.markdown(f"### 📅 Calendrier des réservations – {calendar.month_name[month]} {year}")
    table = ""
    table += "<table style='width:100%; border-collapse: collapse;'>"
    table += "<tr>" + "".join(f"<th style='border: 1px solid #ccc; padding: 5px;'>{day}</th>" for day in ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]) + "</tr>"

    for week in weeks:
        table += "<tr>"
        for day in week:
            if day == 0:
                table += "<td style='border: 1px solid #ccc; padding: 10px; height: 80px;'></td>"
                continue

            current_date = datetime.date(year, month, day)
            if current_date in data_by_date:
                cell_content = f"<strong>{day}</strong><br/>"
                for nom, plateforme in data_by_date[current_date]:
                    color = plateforme_colors.get(plateforme, "#ccc")
                    cell_content += f"<div style='background-color:{color}; color:white; padding:2px; margin:2px; border-radius:4px; font-size:12px'>{nom}</div>"
            else:
                cell_content = f"<strong>{day}</strong><br/>"

            table += f"<td style='border: 1px solid #ccc; vertical-align: top; padding: 5px; height: 80px;'>{cell_content}</td>"
        table += "</tr>"
    table += "</table>"
    st.markdown(table, unsafe_allow_html=True)

# Onglets
tabs = st.tabs(["📋 Tableau des réservations", "🗓️ Calendrier", "➕ Nouvelle réservation"])

# 1. Onglet Tableau des réservations
with tabs[0]:
    st.header("📋 Gestion des réservations")
    uploaded_file = st.file_uploader("Importer un fichier .xlsx", type="xlsx")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()
            required_columns = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}

            if not required_columns.issubset(set(df.columns)):
                st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_columns)}")
            else:
                df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
                df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

                st.success("✅ Données chargées avec succès.")
                st.dataframe(df)

                # SMS aux clients arrivant demain
                demain = datetime.date.today() + datetime.timedelta(days=1)
                df_demain = df[df["date_arrivee"].dt.date == demain]

                for _, row in df_demain.iterrows():
                    nom = row["nom_client"]
                    msg = f"Bonjour {nom}, Nous sommes heureux de vous accueillir demain à Nice.\nUn parking est à votre disposition. Merci de nous indiquer votre heure d'arrivée.\nBon voyage et à demain !\nAnnick & Charley"
                    num = row["telephone"]
                    send_sms_free(FREE_USER_1, FREE_API_KEY_1, msg)
                    send_sms_free(FREE_USER_2, FREE_API_KEY_2, msg)
        except Exception as e:
            st.error(f"Erreur lors du traitement du fichier : {e}")

# 2. Onglet Calendrier
with tabs[1]:
    st.header("🗓️ Visualisation mensuelle")
    if uploaded_file:
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        today = datetime.date.today()
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Mois", range(1, 13), index=today.month - 1)
        with col2:
            year = st.selectbox("Année", range(today.year - 1, today.year + 2), index=1)

        try:
            render_calendar(df, year, month)
        except Exception as e:
            st.error(f"Erreur lors de la génération du calendrier : {e}")
    else:
        st.warning("📂 Veuillez importer un fichier pour afficher le calendrier.")

# 3. Onglet Nouvelle Réservation
with tabs[2]:
    st.header("➕ Ajouter une nouvelle réservation")

    with st.form("add_resa"):
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée", min_value=datetime.date.today())
        date_depart = st.date_input("Date de départ", min_value=date_arrivee + datetime.timedelta(days=1))
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")
        submit = st.form_submit_button("Ajouter")

        if submit:
            try:
                new_row = pd.DataFrame([{
                    "nom_client": nom_client,
                    "date_arrivee": pd.to_datetime(date_arrivee),
                    "date_depart": pd.to_datetime(date_depart),
                    "plateforme": plateforme,
                    "telephone": telephone,
                    "prix_brut": prix_brut,
                    "prix_net": prix_net,
                    "charges": charges,
                    "%": pourcentage
                }])

                df = pd.concat([df, new_row], ignore_index=True)
                st.success("✅ Réservation ajoutée.")

                towrite = BytesIO()
                df.to_excel(towrite, index=False)
                towrite.seek(0)
                st.download_button("📥 Télécharger le fichier mis à jour", towrite, file_name="reservations_mise_a_jour.xlsx")
            except Exception as e:
                st.error(f"Erreur : {e}")
