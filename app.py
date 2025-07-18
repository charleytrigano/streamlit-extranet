import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta, date
import requests
from io import BytesIO

st.set_page_config(page_title="Extranet Réservations", layout="wide")

st.title("📅 Portail Extranet Streamlit")
st.markdown("**Bienvenue dans votre outil de gestion de réservations.**")

# --- Lecture du fichier .xlsx
uploaded_file = st.file_uploader("Importer un fichier .xlsx", type=["xlsx"])
df = pd.DataFrame()

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Nettoyage des colonnes
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                         "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(df.columns.str.strip()):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            # Conversion des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
            df["plateforme"] = df["plateforme"].astype(str).str.strip()
            df["nom_client"] = df["nom_client"].astype(str).str.strip()
            st.success("✅ Fichier chargé avec succès.")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

# --- Envoi des SMS (Free Mobile)
def envoyer_sms_free(user, api_key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={message}"
    response = requests.get(url)
    return response.status_code == 200

# --- SMS 24h avant l’arrivée
if not df.empty:
    aujourd_hui = pd.Timestamp(date.today())
    demain = aujourd_hui + pd.Timedelta(days=1)

    df_sms = df[df["date_arrivee"].dt.date == demain.date()]

    st.subheader("📩 Envoi automatique de SMS (arrivées demain)")

    if not df_sms.empty:
        for _, row in df_sms.iterrows():
            nom = row["nom_client"]
            message = f"""Bonjour {nom}, Nous sommes heureux de vous accueillir demain à Nice. 
Un emplacement de parking est à votre disposition. Merci de nous indiquer votre heure d'arrivée. 
Bon voyage et à demain ! Annick & Charley"""

            sent = envoyer_sms_free("12026027", "1Pat6vSRCLiSXl", message)
            if sent:
                st.success(f"✅ SMS envoyé à {nom}")
            else:
                st.error(f"❌ Échec de l'envoi du SMS à {nom}")
    else:
        st.info("Aucun client n’arrive demain.")

# --- 🆕 Ajouter une réservation
with st.form("ajouter_reservation"):
    st.subheader("➕ Ajouter une réservation manuellement")
    col1, col2 = st.columns(2)
    with col1:
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d’arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb"])
    with col2:
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")

    submit = st.form_submit_button("✅ Ajouter")

    if submit and nom_client:
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
        st.success(f"Réservation ajoutée pour {nom_client} ✅")

# --- 🗓️ Calendrier mensuel
if not df.empty:
    st.subheader("📆 Calendrier des réservations")

    today = date.today()
    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=today.month - 1)
    annee = st.number_input("Année", value=today.year, step=1)

    mois_index = list(calendar.month_name).index(mois)

    # Réservations du mois
    start_month = date(annee, mois_index, 1)
    end_month = start_month + pd.DateOffset(months=1) - pd.DateOffset(days=1)

    cal = calendar.Calendar()
    semaines = cal.monthdatescalendar(annee, mois_index)

    couleurs = {"Booking": "#8ecae6", "Airbnb": "#f4a261"}

    # Construction du calendrier HTML
    html = '<style>td, th {border:1px solid gray; padding:8px; text-align:center;}</style>'
    html += "<table><tr>" + "".join(f"<th>{day}</th>" for day in ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]) + "</tr>"

    for semaine in semaines:
        html += "<tr>"
        for jour in semaine:
            contenu = f"<strong>{jour.day}</strong>"
            jour_reservations = df[
                (df["date_arrivee"].dt.date <= jour) &
                (df["date_depart"].dt.date > jour)
            ]
            for _, res in jour_reservations.iterrows():
                couleur = couleurs.get(res["plateforme"], "#ccc")
                contenu += f'<div style="background:{couleur}; padding:2px; margin-top:2px; font-size:12px;">{res["nom_client"]}</div>'
            html += f"<td>{contenu}</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# --- 📥 Exportation
if not df.empty:
    def convert_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Réservations")
        return output.getvalue()

    st.download_button(
        label="💾 Télécharger les réservations",
        data=convert_to_excel(df),
        file_name="reservations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
